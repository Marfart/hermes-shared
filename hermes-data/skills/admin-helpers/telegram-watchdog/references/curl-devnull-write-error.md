# curl `-o /dev/null` Write Error on Windows git-bash

## 现象

看门狗 v8 的 `diag_layer5_target` 永远报告 `cmd=curl code=23`，即使 HTTP 响应是 200。

## 根因

`curl -s --connect-timeout 5 -o /dev/null -w "%{http_code}" https://www.baidu.com`

在 Windows 的 git-bash 环境中：
- `/dev/null` 是 MSYS 模拟的伪设备，不是真正的 Windows 空设备
- curl（Windows 原生 exe）写入它时返回 **exit code 23（Write error）**
- HTTP 请求本身成功（stdout 输出 "200"），但 SubprocessRunner 看到 returncode≠0 就抛异常

## 验证步骤

```bash
# ❌ git-bash 下 buggy
$ python -c "
import subprocess
r = subprocess.run(['curl', '-s', '--connect-timeout', '5', '-o', '/dev/null', '-w', '%{http_code}', 'https://www.baidu.com'], capture_output=True, text=True, timeout=10)
print('stdout:', repr(r.stdout), 'rc:', r.returncode)
"
stdout: '200' rc: 23

# ✅ 用 NUL 修复后
$ python -c "
import subprocess
r = subprocess.run(['curl', '-s', '--connect-timeout', '5', '-o', 'NUL', '-w', '%{http_code}', 'https://www.baidu.com'], capture_output=True, text=True, timeout=10)
print('stdout:', repr(r.stdout), 'rc:', r.returncode)
"
stdout: '200' rc: 0
```

## 影响范围

看门狗日志中所有 `❌ TARGET | cmd=curl code=23:` 条目都是虚假告警。网络实际上是通的。

## 修复

```diff
- ["curl", "-s", "--connect-timeout", "5", "-o", "/dev/null", "-w", "%{http_code}", cfg.api_test_url],
+ ["curl", "-s", "--connect-timeout", "5", "-o", "NUL", "-w", "%{http_code}", cfg.api_test_url],
```

## 连带问题

`pip list --outdated` 在 cron no_agent 环境下常超时（15s 不够），导致 SSL 诊断层也被跳过。应改为：
- 直接 `curl -sI --connect-timeout 5` 到 https 目标检查 TLS 握手
- 或 Python sockets 层 TLS 协商（更快、纯 stdlib、不依赖 pip/PyPI）

## 发现时间

2026-06-04，Kali 发现"又断了"，调查发现网络一切正常，看门狗自己的诊断把自己骗了。