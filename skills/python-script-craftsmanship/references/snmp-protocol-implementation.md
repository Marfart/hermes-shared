# SNMP Protocol Implementation with pysnmp 7.x

实战记录：从零构建 SNMP Agent + Manager，踩遍 pysnmp 的坑后的经验总结。

## 架构

```
Manager (udp client)  ── SNMP GET/GETNEXT/SET ──→  Agent (udp server)
  161/UDP                                        161/UDP
  snmp_manager.py                                snmp_agent.py
```

## pysnmp 7.x 核心 API

```python
from pysnmp.proto import api
pMod = api.PROTOCOL_MODULES[api.SNMP_VERSION_1]  # SNMPv1

# 创建 PDU — 必须用这些工厂方法，不是直接 univ.Sequence()！
req_pdu = pMod.GetRequestPDU()       # 0xA0
next_pdu = pMod.GetNextRequestPDU()  # 0xA1
rsp_pdu = pMod.GetResponsePDU()      # 0xA2
set_pdu = pMod.SetRequestPDU()       # 0xA3

# 设置 PDU 字段
pMod.apiPDU.set_defaults(pdu)
pMod.apiPDU.set_request_id(pdu, 12345)
pMod.apiPDU.set_error_status(pdu, 0)
pMod.apiPDU.set_error_index(pdu, 0)
pMod.apiPDU.set_varbinds(pdu, (("1.3.6.1.2.1.1.1.0", pMod.Null("")),))

# 读取 PDU 字段
req_id = pMod.apiPDU.get_request_id(pdu)
err = pMod.apiPDU.get_error_status(pdu)
vbs = pMod.apiPDU.get_varbinds(pdu)
for name_str, val in vbs:
    oid = tuple(int(x) for x in name_str.split("."))

# 构建消息
msg = pMod.Message()
pMod.apiMessage.set_defaults(msg)
pMod.apiMessage.set_version(msg, 0)     # SNMPv1
pMod.apiMessage.set_community(msg, b"public")
pMod.apiMessage.set_pdu(msg, pdu)

# 编码/解码
data = encoder.encode(msg)                       # bytes → wire
decoded, rest = decoder.decode(data, asn1Spec=pMod.Message())
```

## 🚨 关键陷阱

### 陷阱1：PDU 必须用 context-specific tags

SNMP 的 BER 编码要求 PDU 使用隐式 context-specific tags：

| PDU 类型 | Tag | 含义 |
|----------|:---:|:----:|
| GetRequest | 0xA0 | context [0] |
| GetNextRequest | 0xA1 | context [1] |
| GetResponse | 0xA2 | context [2] |
| SetRequest | 0xA3 | context [3] |
| GetBulkRequest | 0xA5 | context [5] |

用 `univ.Sequence()` 构造的 PDU 会用 universal tag 0x30，SNMP Agent 不会识别它。
**必须用 `pMod.GetRequestPDU()` 等工厂方法**来获得正确 tagged 的 PDU。

### 陷阱2：pyasn1 `Tag.getTagId()` → `Tag.tagId`

pysnmp 7.x 依赖的 pyasn1 新版中，Tag 对象的 `getTagId()` 方法已被移除，改用属性 `tagId`：

```python
# ❌ 旧版
pdu.getTagSet()[0].getTagId()
# ✅ 新版 
pdu.getTagSet()[0].tagId
```

### 陷阱3：`set_varbinds` 接受字符串 OID，不是元组

`apiPDU.set_varbinds()` 的第一个参数是 OID 字符串，不是元组：
```python
# ✅ 正确
pMod.apiPDU.set_varbinds(pdu, (("1.3.6.1.2.1.1.1.0", value),))
# ❌ 错误
pMod.apiPDU.set_varbinds(pdu, (((1,3,6,1,2,1,1,1,0), value),))
```

### 陷阱4：`get_varbinds` 返回 (str_oid, val) 元组列表

返回值的 OID 是点分字符串，需要手动转元组：
```python
vbs = pMod.apiPDU.get_varbinds(rsp_pdu)
for name_str, val in vbs:
    oid = tuple(int(x) for x in name_str.split('.'))
```

## 协议调试方法论（layer-by-layer isolation）

当基于 pysnmp 的 Agent/Manager 建好却不响应时，不要盲目改代码。逐层验证：

### Layer 0：运输层（UDP works?）

用最简单的 echo server 验证 asyncio UDP 能否正常工作：

```python
import asyncio
class EchoProto(asyncio.DatagramProtocol):
    def connection_made(self, transport):
        self.transport = transport
        print("Server listening", flush=True)
    def datagram_received(self, data, addr):
        print(f"Got: {data}", flush=True)
        self.transport.sendto(b"ECHO:" + data, addr)

async def test():
    loop = asyncio.get_running_loop()
    transport, _ = await loop.create_datagram_endpoint(
        EchoProto, local_addr=("127.0.0.1", 1162))
    # 同时发一条测试
    class Client(asyncio.DatagramProtocol):
        def connection_made(self, tr):
            tr.sendto(b"HELLO", ("127.0.0.1", 1162))
        def datagram_received(self, data, addr):
            print(f"Client got: {data}", flush=True)
            loop.stop()
    _, _ = await loop.create_datagram_endpoint(
        Client, remote_addr=("127.0.0.1", 1162))

asyncio.run(test())
# → Server listening, Got: b'HELLO', Client got: b'ECHO:HELLO'
```

如果这步不通 → 问题在 asyncio UDP 本身（端口占用、防火墙、Windows sock 限制）
如果这步通但 SNMP 不通 → 问题在协议编码层

### Layer 1：编码/解码层（BER works?）

用 raw socket（非 asyncio）发一个手动构造的 SNMP 包，看 Agent 能不能解码：

```python
import socket
from pyasn1.codec.ber import encoder
from pysnmp.proto import api

pMod = api.PROTOCOL_MODULES[api.SNMP_VERSION_1]
pdu = pMod.GetRequestPDU()
pMod.apiPDU.set_defaults(pdu)
pMod.apiPDU.set_varbinds(pdu, (("1.3.6.1.2.1.1.1.0", pMod.Null("")),))

msg = pMod.Message()
pMod.apiMessage.set_defaults(msg)
pMod.apiMessage.set_community(msg, b"public")
pMod.apiMessage.set_pdu(msg, pdu)

data = encoder.encode(msg)
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.settimeout(3)
sock.sendto(data, ("127.0.0.1", 1161))
resp, addr = sock.recvfrom(65535)
print(f"Got {len(resp)} byte response")
```

### Layer 2：Agent 内部处理（Handler logic works?）

在 Agent 的 `handle()` 方法中加日志，看请求走到哪一步崩溃：

```python
def datagram_received(self, data, addr):
    import traceback, sys
    try:
        print(f"[DEBUG] Got {len(data)} bytes from {addr}", flush=True)
        response = self.handle(data)
        ...
    except Exception as e:
        traceback.print_exc(file=sys.stdout)
        sys.stdout.flush()
```

用 `> agent.log 2>&1` 重定向输出到文件，而非依赖 background 工具的 output_preview。

### Layer 3：验证 Agent 对外可见（netstat）

```bash
netstat -ano | grep 1161
# → UDP 127.0.0.1:1161  *:*  PID
```

如果 Agent 进程在跑但端口没出现 → 进程在 import 阶段就崩溃了（看 stderr）。

## 常见调试现象速查

| 现象 | 根因 | 排查方向 |
|:-----|:-----|:---------|
| Manager timeout, Agent log 空 | Agent 在 import 阶段就崩了 | 用 `python -c "import ..."` 单独测导入 |
| Agent 收到请求但无响应 | BER 编码错误（tag 不对） | 检查 `getTagId()` vs `tagId`，检查 PDU 是否用工厂方法 |
| Agent 响应但 Manager timeout | Manager 解码失败 | 检查 Manager 的 `decoder.decode(data, asn1Spec=...)` |
| 同步 socket 有响应但 asyncio 没有 | asyncio event loop 问题 | 检查 Agent 是否用 `run_coroutine_threadsafe` |
| 后台进程跑着但 log 文件空 | Python stdout 缓冲 | 加 `-u` 参数，或 `> file 2>&1` 重定向 |

## Shell 脚本路径注意事项（Windows + git-bash）

- 中文目录名在 git-bash 的 `cd` 命令中会失败（`没有那个文件或目录`）
- 用英文路径 `scripts_cache/` 替代中文 `脚本缓存/`
- `write_file` 创建的路径用正斜杠 `C:/Users/...` 或双反斜杠 `C:\\Users\\...`
- 后台进程输出重定向到 log 文件 (`> file.log 2>&1`) 比依赖 process().output_preview 可靠

## 完整 SNMP 学习脚本

位置：`scripts_cache/snmp_lab/`
- `snmp_agent.py` — SNMP Agent 模拟器（38 OIDs，支持 GET/GETNEXT/SET）
- `snmp_manager.py` — SNMP Manager CLI（get/walk/set/discover）

使用方式：
```bash
# 终端1：启动 Agent
cd /c/Users/Admin/AppData/Local/hermes/memories/scripts_cache/snmp_lab
python snmp_agent.py --port 1161 --community public

# 终端2：查询
python snmp_manager.py --port 1161 get 1.3.6.1.2.1.1.1.0
python snmp_manager.py --port 1161 walk 1.3.6.1.2.1.1
python snmp_manager.py --port 1161 discover
```
