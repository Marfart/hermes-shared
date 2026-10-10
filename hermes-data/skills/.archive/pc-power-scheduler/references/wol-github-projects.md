# WOL (Wake-on-LAN) GitHub 开源工具清单

> 整理日期：2026-06-03 | 用途：路由器 WOL 方案实施参考

---

## 🌟 Web 面板型（推荐）

| # | 项目 | ⭐ | 技术栈 | 说明 |
|:-|:----|:-:|:------|:-----|
| 1 | **[sameerdhoot/wolweb](https://github.com/sameerdhoot/wolweb)** | **426⭐** | Go + Bootstrap + Docker | **最推荐！** Docker 30秒部署，Web界面管理多台设备，REST API，支持CRUD设备管理。可跑在树莓派/NAS/路由器上 |
| 2 | **[elModo7/WakeOnLAN-Web-API](https://github.com/elModo7/WakeOnLAN-Web-API)** | 7⭐ | Java Spring Boot | 完整Web面板 + REST API，带认证登录，支持远程关机（需配套Remote-Shutdown-API），Docker部署，HTTPS |

## 🔧 路由器固件专用型

| # | 项目 | 适用固件 | 说明 |
|:-|:------|:--------|:-----|
| 3 | **[austinbutler/openwrt-wol-cli](https://github.com/austinbutler/openwrt-wol-cli)** | OpenWRT | 纯Shell脚本，一行命令唤醒设备。基于 `uci` 读取DHCP静态绑定MAC，用 `etherwake` 发包 |
| 4 | **[tspizzy/DDWRT_WOL](https://github.com/tspizzy/DDWRT_WOL)** | DD-WRT | Python脚本，通过SSH登录DD-WRT路由器发送WOL魔法包，支持远程外网唤醒，双击运行 |
| 5 | **[maxalov/mikrotik-wol-api](https://github.com/maxalov/mikrotik-wol-api)** | MikroTik | Python + `librouteros`，通过RouterOS API远程发WOL命令 |

## 🔌 ESP32 硬件方案

| # | 项目 | 接入方式 | 说明 |
|:-|:------|:--------|:-----|
| 6 | **[ETeissonniere/esp32-wol](https://github.com/ETeissonniere/esp32-wol)** | ESP32-S3 ETH + WiFi | 插网线到电脑 + WiFi联网 → HTTP API发魔法包。解决WiFi电脑无法WOL的问题 |
| 7 | **[yusufcirak/WakeOnLan](https://github.com/yusufcirak/WakeOnLan)** | ESP32 + Web | ESP32 + 完整的Web界面远程唤醒系统 |
| 8 | **[filipporaciti/esp32-WOL](https://github.com/filipporaciti/esp32-WOL)** | ESP32 + RainMaker | 支持 Google Home / Alexa 语音唤醒 |
| 9 | **[memst/wol_esp](https://github.com/memst/wol_esp)** | ESP32 WiFi | 纯WiFi ESP32，绕过不支持WOL转发的路由器 |

## 🐍 Python/CLI 工具

| # | 项目 | 安装方式 | 说明 |
|:-|:------|:--------|:-----|
| 10 | **[bentasker/Wake-On-Lan-Python](https://github.com/bentasker/Wake-On-Lan-Python)** | 单文件 | 纯Python 3脚本，一行命令发魔法包，自动检测子网广播地址 |
| 11 | **[crowdrender/wakeonlan](https://github.com/crowdrender/wakeonlan)** | `pip install wakeonlan` | CL工具，支持广播IP+端口指定 |
| 12 | **[sciguy14/Remote-Wake-Sleep-On-LAN-Server](https://github.com/sciguy14/Remote-Wake-Sleep-On-LAN-Server)** | Python Flask | 树莓派做低功耗WOL服务器，带Web界面+REST API，支持远程睡眠 |

## 📚 文档/参考

| # | 项目 | ⭐ | 说明 |
|:-|:------|:-:|:-----|
| 13 | **[moonlight-stream/moonlight-docs WOL指南](https://github.com/moonlight-stream/moonlight-docs/wiki/WOL-(Wake-On-LAN))** | **1.5k⭐** | 最完整的WOL配置Wiki！涵盖BIOS/Windows/Linux/远程WOL(VPN/端口转发/WOL容器) |
| 14 | **[cyraxjoe/awake](https://github.com/cyraxjoe/awake)** | - | 轻量WOL Python库，可嵌入其他项目 |

## 🔐 路由器安全测试/密码恢复工具

| # | 项目 | ⭐ | 说明 |
|:-|:------|:-:|:-----|
| 15 | **[threat9/routersploit](https://github.com/threat9/routersploit)** | **13k⭐** | 嵌入式设备利用框架。700+模块，含华为/TPlink/Cisco等55+品牌的路由器凭证测试（SSH/Telnet/FTP/HTTP），支持autopwn一键扫描 |
| 16 | **[vanhauser-thc/thc-hydra](https://github.com/vanhauser-thc/thc-hydra)** | **11k⭐** | 业界标准网络认证爆破工具。`http-post-form` 模块支持自定义Web表单登录爆破，`-d` 调试模式可看HTTP响应检查失败条件 |
| 17 | **[ihebski/DefaultCreds-cheat-sheet](https://github.com/ihebski/DefaultCreds-cheat-sheet)** | **2k⭐** | 3,766条默认凭据，覆盖1,384个品牌。CSV格式，是router_credential_recovery.py的数据源 |
| 18 | **[danielmiessler/SecLists](https://github.com/danielmiessler/SecLists)** | **62k⭐** | 业界最大安全测试字典集（密码/用户/路径/CVE），`Passwords/Default-Credentials/default-passwords.txt` 含3万+默认密码 |

### 学习要点

**RouterSploit 目录结构：**
```
routersploit/modules/creds/routers/
├── huawei/   → ftp/ssh/telnet 默认凭据
├── tplink/
├── cisco/
├── asus/     → 含23个品牌子目录
└── ... 共700+模块
```

**多服务攻击面策略：**
1. 先扫开放端口（HTTP 80 + SSH 22 + Telnet 23）
2. 对每个服务分别用默认凭据字典攻击
3. 如果HTTP防护严格（SCRAM），尝试SSH/Telnet可能更简单

```
方案1：端口转发（最简单）
  外网 → 路由器UDP 9 → 电脑（需公网IP+ARP静态绑定）

方案2：中继服务器（最通用）
  外网 → VPN/隧道 → 内网中继 → WOL魔法包（不需公网IP）

方案3：VPN（最安全）
  外网 → VPN连入内网 → 发WOL包（不暴露端口）

方案4：ESP32硬件（WiFi电脑必备）
  外网 → WiFi的ESP32 → 以太网线连电脑 → 魔法包（解决WiFi无法WOL）
```

Moonlight文档推荐顺序：
1. **VPN服务器** — 最安全，需要一台24h设备
2. **路由器端口转发** — 最简单，需公网IP+DDNS
3. **Tailscale/ZeroTier** — 零配置VPN，可WOL
4. **Home Assistant WOL** — 已有HA的优先
  
---

> 小马搜遍GitHub，最实用的是 **[wolweb](https://github.com/sameerdhoot/wolweb)** (426⭐) — Go语言写的Web WOL面板，Docker 30秒就搭好，手机浏览器就能点开机