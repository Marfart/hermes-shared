---
name: kali-linux-mastery
description: "Kali Linux 虚拟机操作/控制系统知识体系，从零装机到渗透测试全链路实操技能"
version: 2.0.0
author: Tachikoma
trigger: "用户说学Kali/虚拟机/渗透测试/网络安全/ethical hacking/学习Kali Linux"
---

# Kali Linux Mastery v2.1

> **诚实状态（2026-06-07）：** 这是一个工具目录技能，不是实战技能。里面列的工具没有一个在这台机器上装过/跑过。Kali 本身没有装成功（见下面"当前机器限制"）。当 Kali 真正装好后再逐个工具实战验证更新。

> 全面更新：基于 Kali 2025.4（2025.12发布）+ awesome-pentest (26.3k⭐) 深度研究

---

## 📌 第〇层：Kali Linux 全景概览

### 版本现状
| 版本 | 日期 | 亮点 |
|:----|:----|:----|
| Kali 2025.4 | 2025.12 | GNOME 49 / KDE Plasma 6.5 / Wayland全面支持 / 3个新工具 / Halloween Mode |
| Kali 2025.3 | 2025.09 | Vagrant / Nexmon 更新 |
| Kali 2025.2 | 2025.06 | 常规工具更新 |
| Kali Rolling | 持续更新 | 滚动发行，apt update/upgrade 即获最新版 |

### 关键数字
- **600+** 预装安全工具
- **15 大分类** 覆盖渗透测试全生命周期
- **12 个元包** (metapackages) 按需安装
- **Live ISO 4.7GB+** / Everything ISO 15GB（仅BitTorrent）
- **桌面环境**：Xfce（默认）/ GNOME 49 / KDE Plasma 6.5 / i3 / LXDE / MATE
- **Kali 2025.4 新工具**：bpf-linker / evil-winrm-py / hexstrike-ai

### 核心使用原则
```
虚拟机 → 授权目标 → 命令行 → 快照保护 → 日志全留
```

---

## 🏗️ 第1层：安装方式

### 核心原则（2026-06-07 Kali纠正）
**「我让你学里面的工具怎么用就行了」** — 不要为了学工具而装整个Kali。
大多数Kali工具在Windows上可以直接安装（winget/pip/独立安装包）：
- nmap → `winget install nmap`
- sqlmap → `pip install sqlmap`
- hydra → 有Windows版本
- wireshark → 有Windows版本
- hashcat → 有Windows版本

仅当该工具是Linux独有时才需装Kali VM/WSL。

### 当前机器的限制 (2026-06-07)
- ❌ 没有 VirtualBox / VMware
- ❌ WSL2 未安装（需管理员权限弹UAC）
- ❌ Docker 未安装
- **下一步：** 需要 Kali 点 UAC 确认安装 WSL2，或安装 VirtualBox

### 方式 A: VirtualBox 手动装（推荐新手）
同上（下载ISO → 新建VM → 安装 → Guest Additions → 快照）

### 方式 B: 预装 VM 镜像（最快捷，推荐）
```bash
# Kali 官方提供预装 OVA/VDI/VMDK
# 直接导入 VirtualBox/VMware/VMware Fusion
# 无需安装过程，开箱即用
下载地址: https://www.kali.org/get-kali/#kali-virtual-machines
```

### 方式 C: Packer 自动构建
同上（来自 `TheBlindHacker/Kali-Custom-ISO`）

### 方式 D: WSL2 Kali
同上

### 方式 E: 树莓派 / ARM 设备
```bash
# Kali 官方支持树莓派 4/5
# https://www.kali.org/get-kali/#kali-arm
wget https://kali.download/arm-images/kali-2025.4-raspberry-pi-5.img.xz
dd if=kali-2025.4-raspberry-pi-5.img of=/dev/sdX bs=1M status=progress
```

---

## ⚡ Kali 学习铁律：行动优先

**当 Kali 用户表达"实操/试试/实战"意图时：**

1. **立即动手，停止解释。** 被说"你在浪费我时间" = 你在输出理论而非实操。立刻部署实战环境。
2. **先搭靶机后展示。** 在后台准备好目标（HTTP/SSH/FTP），用户看到的是"好了，跑这个"。
3. **实操优先序：** 本地靶机 > 测试环境 > 理论。宁可先出一个不完美的实操结果，也不要完整的理论分析。
4. **来源：** 2026-06-07 Kali 反馈 — "讲了一晚上工具一个都没实操过"

## 🎯 靶机选择铁律

**Kali 说"远程破解/打/攻击"时——目标必须是真实的本机，不是预设的 CTF 玩具。** 

1. **永远用真机当靶子。** 这台 Windows 机器本身就暴露着 SMB(445)、RPC(135) 等真实攻击面。不要搭一个"完美的 CTF 靶机"然后提前告诉密码——那根本不是远程破解。
2. **Kali 的预期流程：** 从 Mac Kali 扫局域网 → 找到这台机器(192.168.1.93) → 自己发现开放端口 → 自己爆密码。我在 Windows 这边只管保证服务开着，不泄露任何信息。
3. **可攻击的真实目标：**
   - **SMB 445**（最核心）— Hydra 爆 Admin 密码
   - **RPC 135** — 枚举用户/共享
   - **FTP 21**（可留）— 另一个攻击面
4. **密码不能直接告诉。** 我不知道本机密码（没有管理员权限读不了 SAM），这个"不知道"反而是对的——Kali 要自己从 Mac 上爆出来。
5. **来源：** 2026-06-08 Kali 反馈 — "我竟然都要选择通过远程破解的方式，那肯定是破解本机，而不是破解你的靶机"

---

## 🚀 第2层：安装后配置

### Metapackages（Kali 的核心安装机制）

**系统类元包：**
| 元包名 | 内容 | 大小 |
|:-------|:-----|:-----|
| `kali-linux-core` | 最小核心系统 | ~1GB |
| `kali-linux-headless` | 无GUI默认工具集 | ~3GB |
| `kali-linux-default` | 标准桌面版默认工具 | ~4.7GB |
| `kali-linux-large` | 扩展工具集 | ~9GB |
| `kali-linux-everything` | 全部600+工具 | ~15GB |

**按功能分类的元包（核心！）：**
| 元包名 | 覆盖的工具类别 |
|:-------|:--------------|
| `kali-tools-gpu` | GPU工具（hashcat等） |
| `kali-tools-hardware` | 硬件黑客工具 |
| `kali-tools-crypto-stego` | 密码学 + 隐写 |
| `kali-tools-fuzzing` | 模糊测试 |
| `kali-tools-forensics` | 数字取证 |
| `kali-tools-information-gathering` | 信息收集 |
| `kali-tools-exploitation` | 漏洞利用 |
| `kali-tools-post-exploitation` | 后渗透 |
| `kali-tools-passwords` | 密码攻击 |
| `kali-tools-web` | Web应用测试 |
| `kali-tools-sniffing-spoofing` | 嗅探与欺骗 |
| `kali-tools-vulnerability` | 漏洞分析 |
| `kali-tools-wireless` | 无线攻击 |
| `kali-tools-reverse-engineering` | 逆向工程 |
| `kali-tools-social-engineering` | 社会工程学 |
| `kali-tools-reporting` | 报告工具 |
| `kali-tools-binary` | 二进制工具 |
| `kali-tools-responder` | Responder套件 |

```bash
# 一键安装全部
sudo apt update && sudo apt full-upgrade -y
sudo apt install -y kali-linux-everything  # 15GB, 建议有足够空间

# 按类别选装
sudo apt install -y kali-tools-information-gathering kali-tools-web kali-tools-exploitation

# 也可以用 kali-tweaks GUI 选择（不需要记名字）
kali-tweaks → Metapackages 选项卡 → 勾选 → Apply
```

### 自动配置工具
```bash
# Yggdrasil — 自动装工具+配置Kali (57⭐, 3240 commits)
git clone https://github.com/Jarl-Bjoern/Yggdrasil
cd Yggdrasil && python3 yggdrasil.py

# VoidWalker — 400+工具一键安装 (1⭐, 跨平台)
git clone https://github.com/DAEMON-404/voidwalker.py
cd voidwalker.py && python3 voidwalker.py
```

---

## 🎮 第3层：15 大工具分类 + 核心工具详解

### 1. 信息收集 (Information Gathering) 🔍
**目标：** 发现目标资产、域名、子域名、端口、服务

| 工具 | ⭐影响力 | 用途 | 命令示例 |
|:----|:-------|:-----|:--------|
| **nmap** | 🌟行业标准 | 端口扫描+服务识别+OS指纹 | `nmap -sV -sC -A target.com` |
| **masscan** | 🌟全网级 | 超快速端口扫描，5分钟扫全网 | `masscan 0.0.0.0/0 -p80 --rate=10000` |
| **RustScan** | 🌟新星 | Rust写的极速端口扫描器 | `rustscan -a target.com -- -sV -sC` |
| **Amass (OWASP)** | 13k⭐ | 子域名枚举（爬取+字典+证书透明） | `amass enum -d target.com` |
| **Aquatone** | 5.5k⭐ | 子域名发现+截图报告 | `aquatone-discover -d target.com` |
| **theHarvester** | 🌟OSINT标配 | 邮箱/子域名/人名收集 | `theHarvester -d target.com -b google` |
| **dnsrecon** | DNS标配 | DNS枚举+区域传输检测 | `dnsrecon -d target.com -t axfr` |
| **Sn1per** | 7k⭐ | 自动渗透侦察框架 | `sniper -t target.com` |
| **Spiderfoot** | 11k⭐ | OSINT自动化（Web UI） | `spiderfoot -l 0.0.0.0:5001` |
| **recon-ng** | 🌟框架级 | 模块化信息收集框架 | `recon-ng` → marketplace install all |
| **Shodan** | 🌟全网搜索引擎 | 搜索联网设备 | CLI: `shodan search org:"Target"` |
| **Censys** | 🌟替代Shodan | TLS证书+主机扫描 | API: `censys search "services.service_name: HTTP"` |
| **Maltego** | 🌟商业OSINT | 图形化关联分析 | CE免费版功能有限 |

### 2. 漏洞分析 (Vulnerability Analysis) 🕳️
**目标：** 识别已知漏洞、配置弱点

| 工具 | 用途 |
|:----|:-----|
| **OpenVAS** | 开源漏洞扫描器（Greenbone，Nessus的开源替代） |
| **Nessus** | 商业漏洞扫描器（行业标准，收费） |
| **Nikto** | Web服务器漏洞扫描 |
| **Nuclei (ProjectDiscovery)** | 🌟现代漏洞扫描器，YAML模板驱动 |
| **Legion** | 图形化半自动发现框架 |
| **CrackMapExec** | 🌟网络渗透瑞士军刀（SMB/SCADA/WMI等） |
| **w3af** | Web应用攻击审计框架 |

### 3. Web应用测试 (Web Applications) 🌐
**目标：** 发现SQL注入、XSS、CSRF等Web漏洞

| 工具 | ⭐ | 用途 |
|:----|:-:|:-----|
| **Burp Suite** | 🌟行业标准 | Web代理+拦截+扫描+利用（社区版免费） |
| **OWASP ZAP** | 12k⭐ | Burp开源替代，全功能Web代理 |
| **SQLmap** | 32k⭐ | 🌟自动SQL注入+数据库接管 |
| **Gobuster** | 10k⭐ | Web目录/子域名暴力破解 |
| **Dirsearch** | 11k⭐ | Web路径扫描器 |
| **WPScan** | 8.5k⭐ | WordPress漏洞扫描 |
| **Commix** | 4.5k⭐ | 命令注入自动利用 |
| **WhatWeb** | 6k⭐ | Web指纹识别 |
| **FFuF** | 12k⭐ | 快速Web fuzzer（比gobuster更快） |
| **BeEF** | 🌟 | 浏览器利用框架（XSS后控制浏览器） |
| **mitmproxy** | 38k⭐ | 交互式HTTPS代理 |

**Web渗透流程：**
```
gobuster dir → 发现路径 → burp拦截 → sqlmap注入 → BeEF XSS
```

### 4. 密码攻击 (Password Attacks) 🔑
**目标：** 密码破解、哈希爆破、在线暴力破解

| 工具 | ⭐ | 用途 |
|:----|:-:|:-----|
| **Hashcat** | 🌟世界最快 | GPU哈希破解（支持300+哈希类型） |
| **John the Ripper** | 🌟经典 | CPU哈希破解，支持自动检测哈希类型 |
| **Hydra (THC)** | 🌟网络标准 | 在线协议暴力破解（SSH/FTP/HTTP/SMB等） |
| **CeWL** | 标配 | 从网站爬取自建字典 |
| **SecLists** | 58k⭐ | 🌟字典合集（用户名/密码/目录/子域名） |
| **crunch** | 标配 | 自定义字典生成器 |
| **wordlists** (Kali内置) | 标配 | rockyou.txt等经典字典在 `/usr/share/wordlists/` |
| **Ncrack** | nmap配套 | 高速网络认证破解 |
| **JWT Cracker** | 标配 | JWT token暴力破解 |
| **LaZagne** | 10k⭐ | 从本机提取各种存储的密码 |

**密码攻击流程：**
```
CeWL爬站 → 定制字典 → Hashcat GPU破解 / Hydra在线爆破
```

### 5. 无线攻击 (Wireless Attacks) 📡
**目标：** WiFi/WPA/WPS 漏洞测试

| 工具 | 用途 |
|:----|:-----|
| **Aircrack-ng** | 🌟无线审计套件（抓包→破解WPA/WPA2） |
| **Kismet** | 无线网络探测器+嗅探器 |
| **Wifite** | 自动化无线攻击脚本 |
| **Airgeddon** | 多功能WiFi审计脚本 |
| **Reaver** | WPS暴力破解 |
| **Bully** | WPS暴力破解（C语言实现，更快） |
| **Fluxion** | 社会工程学WPA攻击（伪造钓鱼AP） |
| **WiFi-Pumpkin** | 伪造WiFi热点框架 |
| **pwnagotchi** | 🌟AI驱动的WiFi抓包（强化学习） |
| **BetterCAP** | 26k⭐ | 模块化MITM框架 |

**无线攻击流程：**
```
airmon-ng start wlan0 → airodump-ng → 抓握手包 → aircrack-ng破解
```

### 6. 漏洞利用 (Exploitation Tools) 💥
**目标：** 发现漏洞后实际利用

| 工具 | ⭐ | 用途 |
|:----|:-:|:-----|
| **Metasploit Framework** | 🌟行业标准 | 漏洞利用框架（1500+模块） |
| **Searchsploit** | 🌟标配 | 本地搜索Exploit-DB（离线漏洞库） |
| **Armitage** | 标配 | Metasploit图形化界面 |
| **RouterSploit** | 🌟 | 路由器/嵌入式设备利用框架 |
| **ISF** (Industrial Exploit) | 标配 | 工控系统(ICS/SCADA)利用框架 |
| **AutoSploit** | 🌟 | Shodan+Metasploit自动利用 |
| **Magic Unicorn** | 标配 | Shellcode生成器（绕过杀软） |
| **Ronin** | 🌟Ruby | 安全研究开发框架（Ruby） |

**利用流程：**
```
searchsploit apache 2.4 → msfconsole → use exploit → set PAYLOAD → run
```

### 7. 嗅探与欺骗 (Sniffing & Spoofing) 👃
**目标：** 流量监听、中间人攻击

| 工具 | ⭐ | 用途 |
|:----|:-:|:-----|
| **Wireshark** | 🌟行业标准 | 网络协议分析器（图形化） |
| **tcpdump** | 🌟CLI标准 | 命令行抓包 |
| **Ettercap** | 🌟经典 | ARP欺骗+中间人攻击 |
| **BetterCAP** | 26k⭐ | 模块化MITM框架（Ettercap替代） |
| **Scapy** | 🌟Python | 交互式数据包操作库 |
| **Responder** | 🌟 | LLMNR/NBT-NS/mDNS 欺骗 |
| **dsniff** | 标配 | 网络审计工具集 |
| **hping3** | 标配 | 自定义TCP/IP包发送 |

### 8. 后渗透 (Post Exploitation) 🏴‍☠️
**目标：** 攻入后维持访问、提权、横向移动

| 工具 | ⭐ | 用途 |
|:----|:-:|:-----|
| **Empire** | 🌟 | PowerShell后渗透框架 |
| **PowerSploit** | 🌟 | PowerShell后渗透模块集 |
| **Covenant** | 🌟 | C2协同平台（ASP.NET Core） |
| **Mimikatz** | 🌟 | Windows凭据提取 |
| **BloodHound** | 🌟 | AD信任关系可视化（提权路径分析） |
| **Impacket** | 13k⭐ | Python网络协议工具包 |
| **CrackMapExec** | 🌟 | AD网络渗透瑞士军刀 |
| **PEASS-ng** | 17k⭐ | 提权检测脚本(linpeas/winpeas) |
| **Chisel** | 13k⭐ | 内网穿透隧道 |
| **GTFOBins** | 🌟 | Unix二进制提权速查表 |
| **LOLBAS** | 🌟 | Windows自带二进制利用 |

**提权速查：**
```bash
# Linux
linpeas.sh 或 linenum.sh 或 unix-privesc-check
sudo -l  # 检查sudo权限
find / -perm -4000 2>/dev/null  # SUID提权

# Windows
winpeas.exe 或 windows-exploit-suggester
# 用 BloodHound 分析 AD 提权路径
```

### 9. 取证分析 (Forensics) 🔬
**目标：** 数据恢复、磁盘分析、内存取证

| 工具 | 用途 |
|:----|:-----|
| **Autopsy** | 磁盘取证分析（GUI） |
| **Foremost** | 文件恢复（基于文件头） |
| **Binwalk** | 固件分析/提取 |
| **Volatility** | 内存取证框架 |
| **Guymager** | 磁盘镜像获取 |
| **Bulk Extractor** | 批量信息提取 |
| **dcfldd** | 增强版dd（取证级磁盘复制） |

### 10. 逆向工程 (Reverse Engineering) 🔧
**目标：** 分析二进制文件、恶意软件

| 工具 | ⭐ | 用途 |
|:----|:-:|:-----|
| **Ghidra (NSA)** | 🌟51k⭐ | NSA开源逆向平台（IDA Pro替代） |
| **IDA Pro** | 🌟商业标准 | 交互式反汇编器（免费版IDA Free可用） |
| **Radare2** | 21k⭐ | 开源逆向框架（命令行） |
| **dnSpy** | 26k⭐ | .NET反编译调试 |
| **x64dbg** | 45k⭐ | Windows x64/x32调试器 |
| **Frida** | 🌟17k⭐ | 动态插桩（hook任意函数） |
| **OllyDbg** | 经典 | x86 Windows调试器 |
| **Capstone** | 8k⭐ | 轻量级多架构反汇编框架 |
| **Angr** | 7.5k⭐ | 二进制分析框架（符号执行） |

### 11. 社会工程学 (Social Engineering) 🎭
**目标：** 利用人性弱点进行攻击

| 工具 | ⭐ | 用途 |
|:----|:-:|:-----|
| **SET (Social Engineering Toolkit)** | 🌟 | 社会工程学攻击框架 |
| **Gophish** | 12k⭐ | 开源钓鱼框架（Web管理界面） |
| **Evilginx2** | 12k⭐ | 反向代理钓鱼（可绕过2FA） |
| **BeEF** | 🌟 | 浏览器利用框架 |
| **wifiphisher** | 13k⭐ | WiFi钓鱼攻击 |

### 12. 报告工具 (Reporting Tools) 📊
**目标：** 生成渗透测试报告

| 工具 | 用途 |
|:----|:-----|
| **Dradis** | 协作报告框架 |
| **Faraday** | 多用户集成渗透测试环境 |
| **Reconmap** | 开源渗透测试协作平台 |
| **EyeWitness** | Web截图报告生成器 |
| **CherryTree** | 层级笔记（渗透测试记录） |

### 13. 硬件黑客 (Hardware Hacking) 🔌
**目标：** 物理设备渗透

| 工具/设备 | 用途 |
|:---------|:-----|
| **USB Rubber Ducky** | 键盘注入攻击 |
| **Bash Bunny** | 多阶段USB攻击 |
| **LAN Turtle** | 伪装网卡的远程访问设备 |
| **WiFi Pineapple** | 无线审计平台 |
| **Proxmark3** | RFID/NFC克隆/重放 |
| **Hak5 Packet Squirrel** | 以太网中间人工具 |

### 14. 隐写与密码学 (Steganography & Crypto) 🕵️
**目标：** 隐藏/提取数据，密码分析

| 工具 | 用途 |
|:----|:-----|
| **Steghide** | 图片/音频隐写 |
| **StegCracker** | 隐写暴力破解 |
| **StegSolve** | 隐写分析工具 |
| **StegOnline** | 在线隐写分析 |
| **Ciphey** | 自动密码/编码识别破解 |
| **xortool** | XOR加密分析 |

### 15. 云平台攻击 (Cloud Platform) ☁️
**目标：** AWS/Azure/GCP 安全测试

| 工具 | 用途 |
|:----|:-----|
| **Cloudsplaining** | AWS IAM最小权限分析 |
| **CloudHunter** | 云存储桶扫描 |
| **Endgame** | AWS后门工具 |
| **ScoutSuite** | 多云安全审计框架 |
| **kube-hunter** | Kubernetes渗透测试 |

---

## 📚 第4层：GitHub 顶级学习资源

### 终极渗透测试资源合集

| 项目 | ⭐ | 学习价值 |
|:----|:-:|:---------|
| **`enaqx/awesome-pentest`** | **26.3k⭐** | ⭐渗透测试终极资源索引，覆盖全部15个分类+250+工具+书籍 |
| **`vitalysim/Awesome-Hacking-Resources`** | 16k⭐ | 黑客资源大全（教程/工具/CTF） |
| **`arch3rPro/PentestTools`** | 6k⭐ | 渗透测试工具合集（中文友好） |
| **`yogsec/Hacking-Tools`** | 4k⭐ | 分类清晰的黑客工具速查 |
| **`danielmiessler/SecLists`** | **58k⭐** | ⭐渗透测试字典合集 |
| **`swisskyrepo/PayloadsAllTheThings`** | **62k⭐** | ⭐渗透测试Payload百科 |
| **`Hack-with-Github/Awesome-Hacking`** | 85k⭐ | ⭐黑客工具总索引 |
| **`OWASP/CheatSheetSeries`** | 28k⭐ | OWASP速查表系列 |
| **`projectdiscovery/nuclei-templates`** | 10k⭐ | Nuclei漏洞模板库 |
| **`blaCCkHatHacEEkr/PENTESTING-BIBLE`** | 17k⭐ | 渗透测试圣经（PDF/书籍/文章） |
| **`mikeroyal/Kali-Linux-Guide`** | 85⭐ | Kali Linux配置从头到尾指南 |

### 实战练习平台
| 平台 | 说明 |
|:----|:-----|
| **HackTheBox** | 在线渗透测试实验室（推荐入门） |
| **TryHackMe** | 引导式安全学习平台（零基础友好） |
| **PentesterLab** | Web安全专项练习 |
| **VulnHub** | 下载虚拟机练习 |
| **DVWA** | 自建Damn Vulnerable Web Application（Docker一键部署） |
| **OWASP Juice Shop** | 现代Web漏洞练习 |
| **PortSwigger Web Security Academy** | Burp Suite官方免费Web安全课程 |

### 认证路径
| 认证 | 级别 | 费用 | 说明 |
|:----|:----|:----|:-----|
| **OSCP (Offensive Security Certified Professional)** | 🌟入门 | ~$1,000 | Kali开发者出品，实战考试24h |
| **OSEP** | 🌟进阶级 | ~$1,500 | 进阶渗透+绕过防御 |
| **PNPT (Practical Network Penetration Tester)** | 🌟入门 | ~$400 | TCM Security出品，实战报告制 |
| **eJPT (eLearnSecurity Junior Penetration Tester)** | 入门 | ~$200 | INE出品，多项选择题 |
| **CEH (Certified Ethical Hacker)** | 入门 | ~$1,200 | EC-Council出品，理论为主 |

---

## 💡 第5层：实战速查

### 一键安装 Kali 全部工具
```bash
# 装好基础系统后
sudo apt update && sudo apt full-upgrade -y
sudo apt install -y kali-linux-everything  # 15GB
# 或者按需安装
sudo apt install -y kali-linux-large  # ~9GB
```

### 渗透测试标准流程
```
1. 侦察(Recon)     → nmap, Amass, theHarvester, Shodan
2. 扫描(Scan)      → Nuclei, Nikto, OpenVAS, gobuster
3. 漏洞利用(Exploit) → Metasploit, SQLmap, Hydra, searchsploit
4. 提权(PrivEsc)    → linpeas, winpeas, GTFOBins, BloodHound
5. 持久化(Persistence) → cron, SSH key, C2 (Empire/Covenant)
6. 报告(Reporting)  → Dradis, Faraday, EyeWitness
```

### 常用神器组合
```bash
# 最快端口扫描组合
RustScan → 发现开放端口 → 管道给 Nmap 详细扫描

# Web渗透组合
gobuster + ffuf + burpsuite + sqlmap + nuclei

# AD域渗透组合
BloodHound + CrackMapExec + Impacket + Mimikatz + Responder

# 无线攻击组合
aircrack-ng + wifite + reaver + bettercap

# 密码破解组合
CeWL(做字典) + hashcat(GPU破解) + hydra(在线爆破) + john(离线)
```

### 必记命令
```bash
# 信息收集
nmap -sV -sC -A -O target.com          # 全量扫描
masscan 192.168.1.0/24 -p80,443,22 --rate=1000  # 快速端口扫描

# Web
gobuster dir -u http://target.com -w /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt
sqlmap -u "http://target.com?id=1" --dbs

# 漏洞利用
searchsploit apache 2.4.49              # 查已知漏洞
msfconsole → use exploit/multi/handler  # 监听shell

# 密码
hashcat -m 0 -a 0 hash.txt /usr/share/wordlists/rockyou.txt
hydra -l admin -P pass.txt ssh://192.168.1.1

# 后渗透
linpeas.sh | tee linpeas_report.txt     # Linux提权检测
mimikatz.exe "privilege::debug" "sekurlsa::logonpasswords"  # Windows抓密码
```

### 真正实战验证过的 (2026-06-07, Windows 10)
| 工具 | 验证了什么 |
|:----|:----------|
| **nmap 7.80** | TCP SYN扫描本地→发现4端口(135/445/5000/5357) |
| **NSE脚本** | 自定义 NSE 脚本 → 正确识别 Flask 应用(Werkzeug/3.1.8) |
| **sqlmap 1.10.6** | Flask+SQLite靶场→66请求发现3种注入类型→dump出users表 |
| **自定义tamper** | 确认 148 次 `LIKE` 替换成功 |
| **WSL Kali** | ❌ 未安装成功（需要管理员权限点UAC）

---

## ⚠️ 安全红线
- ✅ 所有操作在**虚拟机的虚拟机**里进行（VM套娃更安全）
- ✅ 只对授权目标或自己的实验室操作
- ❌ 不要在未经授权系统上执行任何扫描或攻击
- ❌ 不要在物理机上装Kali代替日常系统
- ❌ 不要使用Kali连接未加密的公共WiFi
- ⚠️ 使用 `sudo` 前检查命令含义——Kali root权限意味着你能摧毁一切
- ⚠️ WiFi攻击需要支持监听模式的USB无线网卡（内置网卡几乎都不行）
- ⚠️ 渗透测试前获得**书面授权**——法律红线不可逾越