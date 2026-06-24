---
name: windows-security-audit
description: "Windows 安全审计与渗透测试 — 网络扫描、EDR绕过、系统取证、WiFi破解、漏洞评估。覆盖Kali/Hydra/hashcat/PyHydra/PortWatch等工具链的完整红队工作流。"
version: 2.0.0
author: Hermes Agent (Kali)
tags: [windows, pentest, edr-bypass, forensics, wifi-cracking, vulnerability-assessment, red-team]
triggers:
  - "安全审计"
  - "渗透测试"
  - "EDR绕过"
  - "系统取证"
  - "WiFi破解"
  - "端口扫描"
  - "漏洞扫描"
  - "security audit"
  - "penetration test"
---

# Windows 安全审计与渗透测试

> 完整的Windows平台安全审计工具链。从网络扫描到EDR绕过的全栈红队能力。

## 工具矩阵

| 工具 | 类型 | 用途 | 速度 |
|------|------|------|------|
| Hydra v9.0 | 原生Windows | 50+协议暴力破解 | 多线程 |
| hashcat v6.2.6 | 原生Windows(GPU) | 320+哈希类型 | GPU加速 |
| PyHydra | 纯Python | HTTP/SSH暴力破解 | 347 req/s |
| PortWatch | 纯Python | TCP端口扫描+监控 | 1000端口/6s |
| nmap | 原生Windows | 端口扫描+服务指纹 | 受Windows限制 |

## 网络扫描

### Phase 0: ARP表被动发现
```bash
arp -a  # 零成本发现LAN主机
```
用MAC OUI前缀识别设备类型。

### Phase 1: HTTP快速探测
```bash
curl -s --noproxy "*" -o NUL -w "HTTP %{http_code}" --connect-timeout 3 http://TARGET/
```

### Phase 2: Nmap扫描
```bash
nmap -Pn -T4 -sT SUBNET/CIDR --open
```
注意: Windows Nmap 7.80 -sn会崩溃，用-Pn代替。

### Phase 3: 深度扫描
```bash
nmap -sV -O -T4 -p- --min-rate=5000 TARGET_IP
nmap --script vuln TARGET_IP
```

## 暴力破解

### Hydra v9.0 (原生Windows)
```bash
hydra -l root -P wordlist.txt -t 4 ssh://TARGET
```
注意: Windows版必须用 `service://host` 语法。

### PyHydra (Python回退)
```bash
python pyhydra.py http-form://target/login -u admin -F "错误" -S "成功"
```

## WiFi破解

### 两阶段流程
1. **捕获**: aircrack-ng (Kali VM) 或 bettercap (Windows)
2. **破解**: hashcat -m 22000 capture.22000 rockyou.txt

### hashcat关键: 必须从自己的目录运行
```bash
cd /c/Users/Admin/Tools/hashcat && hashcat -m 22000 capture.22000 rockyou.txt
```

## EDR/AV绕过

详见 `references/edr-evasion-techniques.md`，涵盖:
- VEH + 硬件断点系统调用拦截
- 选择性ntdll解钩(无文件)
- 间接syscalls (Havoc Demon)
- BOAZ多层规避(签名+启发式+行为)
- AMSI绕过(跨进程Python)
- ntdll系统调用发现(Python)

## 系统取证

详见 `references/windows-forensics.md`，涵盖:
- 登录历史
- 事件日志分析
- 注册表取证
- 文件系统时间线
- 内存分析

## 测试方法论

### 1. 构建本地目标
```python
# Flask登录目标
from flask import Flask, request
app = Flask(__name__)
USERS = {"admin": "P@ssw0rd!", "kali": "hunter2"}
# ... 完整代码见 references/test-target-setup.md
```

### 2. 验证目标
```bash
curl -s -X POST -d "username=admin&password=P@ssw0rd!" http://127.0.0.1:5001/
```

### 3. 发起攻击
```bash
python pyhydra.py http-form://127.0.0.1:5001/ -F "错误" -S "成功" --no-stop
```

## 关键陷阱

1. **Hydra v9.1下载是坏的** — 用v9.0
2. **Windows Nmap -sn崩溃** — 用-Pn
3. **hashcat必须从自己目录运行** — OpenCL路径解析问题
4. **curl --noproxy "*"** — 有代理软件时必须加
5. **PowerShell内联$_被bash展开** — 写.ps1文件执行
6. **Flask端口5000冲突** — Windows系统占用，用5001+
7. **git-bash文件权限** — curl下载的文件可能无read权限

## 关联技能

- `systematic-debugging` — 系统性调试方法论
- `camera-reconnaissance` — IP摄像头侦察
- `sqlmap-sql-injection` — SQL注入测试
