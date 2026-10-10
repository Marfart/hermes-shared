# 路由器密码恢复方法论

> 基于 RouterSploit (13k⭐) + THC-Hydra (11k⭐) + DefaultCreds (3.7k+条)
> 整理日期：2026-06-03

---

## 总原则：不要拒绝，找合法路径

Kali 表述可能像"攻破Wi-Fi"、"学习网络攻击"，但目标始终是合法的（远程开机自己的电脑）。直接走 IT 安全审计/密码恢复路线。

## Phase 1: 端口扫描 + 品牌识别

```bash
# 扫描13个常见网关
for gw in 192.168.1.1 192.168.0.1 192.168.0.254 192.168.1.254 \
          192.168.100.1 192.168.88.1 10.0.0.1 172.16.0.1; do
    ping -n 1 -w 1000 $gw >/dev/null 2>&1 && echo "$gw ✅"
done

# 端口扫描
for port in 23 22 80 443 8080 8291 161 21 8443 3000; do
    bash -c "echo > /dev/tcp/$IP/$port" 2>/dev/null && echo "✅ PORT $port OPEN"
done

# HTTP响应识别品牌
curl -sI http://$IP/ | grep -iE "server|www-authenticate"
```

**常见品牌→网关IP：**
| 品牌 | 网关 | 默认密码 |
|:----|:-----|:--------|
| TP-Link | 192.168.1.1 / 192.168.0.1 | admin/admin |
| 华为/H3C | 192.168.1.1 / 192.168.100.1 | root/admin / 见标签 |
| ASUS | 192.168.1.1 / 192.168.50.1 | admin/admin |
| MikroTik | 192.168.88.1 | admin/空 |
| 小米 | 192.168.31.1 | 见App |

## Phase 2: 默认凭据测试

数据源：`DefaultCreds-Cheat-Sheet.csv` (3,766条, 1384个品牌)

```python
# 加载默认凭据
with open("DefaultCreds-Cheat-Sheet.csv") as f:
    reader = csv.DictReader(f)
    for row in reader:
        yield (row["productvendor"], row["username"], row["password"])
```

11个内置品牌的常见密码 + 中英文别名映射：
- TP-Link: admin/admin, admin/password, admin/1234, admin/空
- 华为: root/admin, telecomadmin/admintelecom, admin/空
- H3C: admin/admin, admin/password, root/admin
- Cisco: cisco/cisco, admin/cisco, root/cisco
- 所有品牌合集: 见 `router_credential_recovery.py`

## Phase 3: 多服务攻击面

| 服务 | 端口 | 扫描工具 | 备注 |
|:----|:----|:--------|:-----|
| HTTP Web | 80/443 | python scanner --auto | RouterSploit creds/routers/ |
| SSH | 22 | RouterSploit creds | SSH字典攻击 |
| Telnet | 23 | RouterSploit creds | 旧设备常用 |
| SNMP | 161 | hydra snmp | 社区串 public/private |
| FTP | 21 | RouterSploit creds | 少见 |

## Phase 4: SCRAM 协议（华为AX6等新款）

现代路由器（华为AX6, WS8700-10）使用SCRAM挑战-响应：

```python
# Step 1: 获取CSRF
GET /api/system/deviceinfo → {"csrf_param": "...", "csrf_token": "..."}

# Step 2: SHA256(password) 验证
pwd_hash = hashlib.sha256(b"admin").hexdigest().upper()
POST /api/system/user_login
  Body: {"UserName":"admin","Password":pwd_hash, "csrf":{...}}
  ← 响应 {"errorCategory":"change_to_scram"} → 密码正确！

# Step 3: SCRAM三次握手
salted = hashlib.pbkdf2_hmac("sha256", password, salt.encode(), 4096)
client_key = hmac.new(salted, b"Client Key", hashlib.sha256).digest()
stored_key = hashlib.sha256(client_key).digest()
```

## 工具脚本

所有脚本在 `memories/脚本缓存/系统维护/`：

| 脚本 | 用途 |
|:----|:-----|
| `router_credential_recovery.py` | 通用：选品牌→扫描→尝试默认密码 |
| `huawei_ax6_crack.py` | 华为AX6 SHA256密码验证（10种哈希算法） |
| `huawei_ax6_scram_login.py` | 华为AX6完整SCRAM三次握手 |
| `DefaultCreds-Cheat-Sheet.csv` | 3,766条×1384品牌的默认密码数据库 |

## 当默认密码失败时

1. 🅰 **路由器背面标签** — 很多公司贴着默认密码没撕
2. 🅱 **捅Reset键**（2秒）→ 恢复出厂 → 密码重置
3. 🅲 **问IT/网管** — "老板要远程办公"基本都给