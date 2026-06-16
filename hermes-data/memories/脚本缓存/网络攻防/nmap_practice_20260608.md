# 🎯 Nmap实战报告 — 2026-06-08

## 环境
本机: 192.168.1.93 (Dell, Biostar H510MHP)
网关: 192.168.1.1 (88:81:B9:4F:12:C2)
子网: 192.168.1.0/24

## 主机发现 (-sn)
- 扫描范围: 192.168.1.1-254
- 活主机: **88台**
- 扫描耗时: 8.92秒

## 关键发现

### 1️⃣ 网关路由器 (192.168.1.1)
| 端口 | 服务 | 备注 |
|------|------|------|
| 53/tcp | DNS | |
| 80/tcp | HTTP | Web管理界面 |
| 443/tcp | HTTPS | 安全Web管理 |
- MAC: 88:81:B9:4F:12:C2
- HTTP响应头: 含X-Frame-Options/XSS-Protection/CSP → 现代路由器固件

### 2️⃣ MSI主机 (192.168.1.114) ⚠️ 最脆弱
**操作系统: Windows Server 2008 R2 - 2012（已停止支持！）**
| 端口 | 服务 | 版本 | 风险 |
|------|------|------|------|
| 80/tcp | HTTP | IIS 7.5 | 🔴 旧版 |
| 135/tcp | MSRPC | Windows RPC | 🟡 |
| 139/tcp | NetBIOS | SMB over NetBIOS | 🟡 |
| 445/tcp | SMB | Server 2008 R2 | 🔴 **高危！EternalBlue可能有效** |
| 1433/tcp | **MS SQL** | SQL Server 2008 R2 | 🔴 **EOL！已知漏洞** |
| 3389/tcp | RDP | Windows RDP | 🟡 对外开放 |
| 8443/tcp | HTTPS | **Apache (VisualSVN Server)** | 🔴 **源码仓库！** |
| 8020/tcp | HTTP | Microsoft HTTPAPI | 🟡 |
- 大量82xx-83xx端口开放（未知服务）
- VisualSVN Server需认证（401 Unauthorized）

### 3️⃣ Intel主机 (192.168.1.115)
| 端口 | 服务 | 备注 |
|------|------|------|
| 135/tcp | MSRPC | Windows RPC |
| 139/tcp | NetBIOS | |
| 445/tcp | SMB | Windows 7-10, WorkGroup |
- 主机名: XTZJ-20241223OU

### 4️⃣ Colorful主机 (192.168.1.51)
- Windows OS
- 开放: 135, 139, 445

### 5️⃣ 虚拟机
| IP | 类型 | MAC厂商 |
|---|------|---------|
| 192.168.1.41 | VirtualBox | Oracle |
| 192.168.1.124 | VMware | VMware |
| 192.168.1.223 | VMware | VMware |
| 192.168.1.230 | VMware | VMware |
| 192.168.1.235 | VirtualBox | Oracle |

## Nmap关键命令备忘

```bash
# 主机发现（快速）
nmap -sn 192.168.1.0/24

# 端口扫描+版本检测+OS检测
nmap -sV -O -T4 目标IP

# 全端口扫描（65535个端口）
nmap -p- -T4 --min-rate=5000 目标IP

# NSE漏洞脚本
nmap --script vuln 目标IP

# SMB信息收集
nmap --script smb-os-discovery 目标IP

# 仅扫描常见端口
nmap -p 22,80,443,135,139,445,3389,8080,8443 目标IP

# 指定速率扫描
nmap -T4 --min-rate=10000 目标IP
```
