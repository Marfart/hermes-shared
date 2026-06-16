---
name: whatsapp-auto-sender
description: "BLIIoT WhatsApp 自动发送开发信 — Selenium + WhatsApp Web，自动读Excel客户名单发个性化开发信，防封号延迟+断点续传"
version: 3.0.0
author: Tachikoma
platforms: [windows]
trigger: "用户要自动批量发WhatsApp消息 / 发开发信 / 客户outreach"
metadata:
  description: "BLIIoT WhatsApp 自动发送开发信 — Selenium + WhatsApp Web，自动读Excel客户名单发个性化开发信，防封号延迟+断点续传"
  tags: ["whatsapp", "outreach", "sales", "automation", "selenium", "b2b"]
  related_skills: ["industrial-lead-mining", "workspace-document-retrieval", "bliiot-email-marketing", "bliiot-agent-orchestrator"]
---

# WhatsApp Auto Sender v3 — 小马自动发信

## 概述

**两种管道，按需选择：**

| 特点 | 管道 A: Playwright CDP (新) | 管道 B: Selenium (旧) |
|------|---------------------------|---------------------|
| 底层 | Playwright + Chrome CDP | Selenium WebDriver |
| 数据源 | Hermes JSON 管道（enriched→queue→messages→send） | Excel 直接 + progress.json 续传 |
| 消息个性化 | 4种style × 9段结构(含greeting+company_pitch) × 多变体组合，自动拼装 | 11种关键词模板匹配 |
| 场景 | 从 crawl_buyer_leads 管道的标准 enriched JSON 发货 | 从 BLIIoT_Customer_Leads_v2.xlsx 直接发送 |
| 首次配置 | Chrome CDP 端口 9223（已有） | 需扫 QR 码首次登录 |
| 未注册号码 | 自动 error 标记并跳过 | `not_found` 标记跳过 |
| 高级反检测 | nodriver (0.50.3) + scrapling (0.4.8) 已安装待集成 | 无 |

**共同前提：** WhatsApp Web 必须在 Chrome 的 Default profile 上登录过（QR扫描一次永效）。

---

### 🆕 高级反检测工具（2026-06-04 已安装）

为绕过 Cloudflare Turnstile（富通搜索痛点）和 Google 反爬（Maps 痛点），已安装两个2026年最新 stealth 浏览器库：

| 库 | 版本 | 核心技术 | 解决什么问题 |
|:---|:----|:---------|:------------|
| **nodriver** | 0.50.3 | undetected-chromedriver 继任者，纯 CDP 驱动，全通过 Cloudflare | 替代 Selenium，性能快 5-10x |
| **scrapling** | 0.4.8 | patchright 底层 + browserforge 指纹 + 自动 Cloudflare Turnstile 破解 | 一行 `solve_cloudflare=True` 绕过富通 |

**安装路径:** Hermes venv (`%LOCALAPPDATA%/hermes/hermes-agent/venv/`)

详情见 `references/nodriver-scrapling-research.md`。

---

## 管道 A: Playwright CDP 管道（推荐新批次）

### 完整数据链

```
BLIIoT_Customer_Leads_v2.xlsx                        ← 原始客户名单
  → python build_enriched_0602.py                     ← 转为 enriched JSON 格式
    → node build_whatsapp_queue.mjs                   ← 建优先级队列
      → node render_whatsapp_messages.mjs             ← 渲染个性化消息
        → node whatsapp_bulk_sender_cdp.mjs --mode send  ← 逐个发送
```

### 文件位置

```
Hermes scripts:
  C:\Users\Admin\AppData\Local\hermes\scripts\buyer-development\
  ├── crawl_buyer_leads.mjs           # 从 Join 搜索结果爬官网/邮箱/WhatsApp/LinkedIn
  ├── build_whatsapp_queue.mjs        # 从 enriched JSON 筛选有 WhatsApp 的客户建队列
  ├── render_whatsapp_messages.mjs    # 4种style × 多变体组合生成个性化消息
  ├── whatsapp_bulk_sender_cdp.mjs    # Playwright CDP 发送器（核心）
  └── whatsapp_web_sender.js          # 辅助函数库（encodeMessage / buildSendUrl / openChat 等）

发信格式：
  C:\Users\Admin\AppData\Local\hermes\memories\buyer-development\
  ├── iiot_search_enriched_2026-06-0X.json         ← 增强分析结果（含电话/邮箱/LinkedIn/WhatsApp/推荐产品）
  ├── whatsapp_priority_queue_2026-06-0X.json       ← 优先队列（只含有 WhatsApp 号码的客户）
  ├── whatsapp_messages_2026-06-0X.json             ← 渲染完成的个性化消息
  └── whatsapp_bulk_send_results_2026-06-0X-XX-XX-XX.json  ← 发送结果
```

### 5 步完整管道

#### 1️⃣ 从 Excel 构建 enriched JSON

当你有新客户名单需要发信时，先建 enriched 格式：

```bash
python "C:\Users\Admin\AppData\Local\hermes\memories\buyer-development\build_enriched_0602.py"
```

输出到 `iiot_search_enriched_2026-06-0X.json`，包含 name, country, domain, whatsappNumbers, whatsappUrls, linkedinUrls, inferredNeeds, recommendedProducts。

**排除已有客户：** 脚本中 `if 'EXISTING' in category or 'ZODSAT' in ...` 自动跳过已有客户。

#### 2️⃣ 建 WhatsApp 优先队列

```bash
node "C:\Users\Admin\AppData\Local\hermes\scripts\buyer-development\build_whatsapp_queue.mjs" \
  "C:\Users\Admin\AppData\Local\hermes\memories\buyer-development\iiot_search_enriched_2026-06-0X.json" \
  "C:\Users\Admin\AppData\Local\hermes\memories\buyer-development"
```

输出 `whatsapp_priority_queue_2026-06-0X.json`（仅含 WhatsApp 号码的客户，按 fitScore 排序）。

#### 3️⃣ 渲染个性消息（v3 — 礼貌商务版）

```bash
node "C:\Users\Admin\AppData\Local\hermes\scripts\buyer-development\render_whatsapp_messages.mjs"
```

**消息结构（9段固定顺序）：**
```
① greeting      — 礼貌开头（"Hope you are having a wonderful day." 等5种变体）
② intro         — 自我介绍（"Hi, this is Kali from BLIIOT." 等5种）
③ company_pitch — BLIIOT公司介绍 ← 按领域差异化，4种说法
④ observation   — 客户行业观察（按style切）
⑤ offer         — 产品匹配推荐
⑥ value         — 价值说明
⑦ cta           — 行动号召
⑧ link          — 官网链接：https://bliiot.com/
⑨ close         — 收尾目录询问
```

**产品名标准化**（raw product name → clean readable shorthand）：
- `BLIIOT gateways/routers (R40, BA/BE/BL gateway series)` → `industrial gateways and routers`
- `ARMxy edge computers/controllers` → `ARM edge controllers`
- `Remote IO / RTU / data acquisition modules` → `remote I/O and data acquisition devices`
- 多个产品用 `together with` 连接（自然商务语气）

**greeting 5种变体：**
```
0: "Hope you are having a wonderful day."
1: "Hope you are having a great day."
2: "Wishing you a pleasant day."
3: "Hope your day is going well."
4: "Hope you are enjoying a good day."
```

输出 `whatsapp_messages_2026-06-0X.json`，每条消息含：
- `style_id`: scada_plc / system_integrator / energy_monitoring / generic_iiot
- `variant_id`: 追踪具体用了哪些变体组合
- `variant_parts`: 各组件用到的索引
- `message`: 完整9段消息文本

#### 4️⃣ 发送（自动查重 + 号码检测跳过）

先确认 Chrome CDP 端口 9223 活着（默认跑着）：

```bash
# 发送前10个（自动跳过已发号码）
node whatsapp_bulk_sender_cdp.mjs --mode send --limit 10 --delay-ms 3000

# 从第11个开始发剩余
node whatsapp_bulk_sender_cdp.mjs --mode send --start-index 10 --limit 99 --delay-ms 3500

# 强制重发（覆盖查重，少用）
node whatsapp_bulk_sender_cdp.mjs --mode send --limit 5 --allow-resend
```

**默认行为：自动查重！**
- 脚本运行时自动扫描所有历史 `whatsapp_bulk_send_results_*.json`
- 建立 `whatsapp_sent_registry.json`（按 whatsapp_number 索引的已发送注册表）
- 命中注册表的号码标记为 `skipped_already_sent`，跳过不发送
- 注册表文件：`C:\Users\Admin\AppData\Local\hermes\memories\buyer-development\whatsapp_sent_registry.json`

**要重发已发号码 → 加 `--allow-resend`**

**未注册 WhatsApp 的号码自动跳过** — 脚本检测不到 send button 时报 error 继续下一个。

#### 5️⃣ 检查结果

```bash
# 看最新的结果文件
cat "C:\Users\Admin\AppData\Local\hermes\memories\buyer-development\whatsapp_bulk_send_results_2026-06-02-*.json"
```

### CDP 架构要点

| 组件 | 值 |
|------|----|
| CDP 端口 | `9223`（Chrome 持续开着） |
| Chrome 路径 | `C:\Program Files\Google\Chrome\Application\chrome.exe` |
| User data 目录 | `%LOCALAPPDATA%\hermes\chrome-profiles\whatsapp-bulk` |
| WhatsApp 状态检测 | 检查 body text 是否含 `链接设备 / link with phone number / 扫码 / qr code` |
| 发送按钮检测 | 5 种备选策略：`button[aria-label="发送/Send"]` → `span[data-icon="send"]` → `Enter`键 |

---

## 管道 B: Selenium 批量（旧，适合零散发送）

### 位置与用法

```
C:\Users\Admin\AppData\Local\hermes\memories\脚本缓存\whatsapp_bot\
├── whatsapp_bot.py              # 主脚本 — 批量发送
├── test_send_one.py             # 单条测试脚本
├── test_send_one_v2.py          # 增强测试版
├── test_bot.py                  # 调试版
└── launch_whatsapp.py           # 启动器
```

### 发送

```bash
cd "C:\Users\Admin\AppData\Local\hermes\memories\脚本缓存\whatsapp_bot"
python whatsapp_bot.py            # 开始发送（从断点继续）
python whatsapp_bot.py status     # 查看发送进度/历史
python whatsapp_bot.py reset      # 重置发送记录
python whatsapp_bot.py help       # 帮助
```

### 测试 vs 批量流程

```
测试模式（test_send_one.py）：
  发1条 → 你自己在浏览器里确认消息是否到达 → 没问题 → 跑批量

批量模式（whatsapp_bot.py）：
  读progress.json跳过已发 → 逐个发剩余客户 → 2-5分钟随机延迟
```

## 模板匹配规则（11种）

脚本用关键词模糊匹配，按顺序检查：

| 关键词匹配 | 发送的模板内容重点 |
|-----------|------------------|
| System Integrator / Automation Company | ARMxy+IOy灵活组合，IoT网关，BLIoTLink协议转换 |
| Machine Builder / Machine / Machinery / Robot / AGV | EdgePLC CODESYS+EtherCAT，ARMxy BL450 AI NPU |
| Building Automation / Home Automation / BACnet / HVAC | BA116+BA190 BACnet方案 |
| Automation Giant / Rockwell | 与Rockwell PLC互补，OPC UA桥接 |
| Energy / Solar / Power / Substation / Grid / SmartGrid | BE116 IEC104/IEC61850，BE190 IO模块，EMS/BMS |
| Distribution / Distributor / Supplier | 代理合作，全线产品，技术培训，利润空间 |
| Electrical Engineer / Engineering Solution / Control System | 远程IO扩展，BL330入门级($100)，R40双SIM路由 |
| Process Automation | BL191 OPC UA直连SCADA，宽温-45~80°C |
| Software / IT / Tech | OEM合作，ARMxy Ubuntu/Docker/Python二次开发 |
| Equipment Supplier | 补充现有产线，全线代理解方案 |
| Existing / EXISTING | 已有客户模板 —— 新产品线拓展 |

**未匹配上的 → 使用通用模板，含公司简介+产品概述+非洲SmartGrid案例**

## 防封号策略

| 措施 | 值 |
|-----|----|
| 每条发送间隔 | **2-5分钟** 随机（`random.randint(120, 300)`秒） |
| 每会话上限 | 30条（常量 `MAX_SEND_PER_SESSION`） |
| 发送时间建议 | 不超过20-30条/天 |
| 先测后发 | 建议先发5条测试 |

## 断点续传机制

- `progress.json` 记录已发送的 `sent_indices`（Excel行号列表）
- 启动时检查进度 → 跳过已发 → 从剩余第一条继续
- `send_log.json` 逐条记录，保留最近200条

## 首次使用步骤

1. 关掉本地已经打开的 Chrome（或确保不会冲突）
2. 运行脚本 → 自动打开 Chrome → 加载 WhatsApp Web
3. **首次扫 QR 码** → session 自动保存到 Chrome user-data 目录
4. 以后不再需要扫码

## Pitfalls

- ⚠️ WhatsApp Web 要求 **真实浏览器窗口**（headless 模式不可用）
- ⚠️ 长时间闲置后 WhatsApp Web 自动 logout → 需重新扫 QR
- ⚠️ **QR码提取方法（新版WhatsApp Web 2026-06验证）** — 新版WhatsApp Web的QR码是SVG而非canvas/img。提取方法：
  1. **Playwright MCP 元素截图（最简单）**：`page.locator('[data-ref]').screenshot({path: 'qr.png'})` — 直接截QR码区域
  2. **SVG→Canvas→PNG**：`document.querySelector('[data-ref] svg')` → XMLSerializer序列化 → Blob URL → Image加载 → Canvas绘制（可放大4-6x） → `canvas.toDataURL('image/png')`
  3. **注意**：`img[alt*="QR"]` 选择器在新版可能无效，QR码不在`<img>`标签里，而是内嵌SVG。`document.querySelector('canvas')` 在QR码首次渲染后可能被回收（hasCanvas从true变false）
  4. **Playwright连接方式**：用CDP连接已有Chrome（`browser_navigate`到web.whatsapp.com），或者直接用`mcp_playwright_browser_navigate` + `browser_snapshot`查看页面状态
- ⚠️ 号码必须是国际格式（带 + 号前缀 + 国家码）
- ⚠️ 号码不在 WhatsApp 上 → 脚本 `TimeoutException` 检测不到联系人 → 自动标记为 `not_found` 并跳过
- ⚠️ 已经发过的号码默认被 `whatsapp_sent_registry.json` 挡住 → 不要怀疑是脚本 bug；要重发加 `--allow-resend`
- ⚠️ rebuild 队列和消息后 `whatsapp_messages_2026-06-01.json` 会被覆盖（同一天的文件名相同），不影响已发送注册表（按号码查重）
- ⚠️ `terminal` 或 `read_file` 显示的号码有 `****` 是终端的隐私保护功能，真实数据完整无误
- ⚠️ `render_whatsapp_messages.mjs` v3 输出的消息不再包含原始产品括号参数名（如 `(R40, BA/BE/BL gateway series)`），改用了标准化简写
- ⚠️ v3 消息 greeting 通过独立 seed 派生，`variant_id` 不体现 greeting/company_pitch 的索引；要追溯完整变体需看 `whatsapp_messages` 文件里的完整消息文本
- ⚠️ `progress.json` 不要手动修改，用 `reset` 命令重置
- ⚠️ 首次运行前确保 Chrome 没有正在打开的 profile 冲突

## ChromeDriver 启动故障诊断

最常遇到的启动失败：`DevToolsActivePort file doesn't exist` 或 `cannot connect to chrome at 127.0.0.1:9222`。

### 诊断流程

```
故障现象                                    → 检查                          → 对策
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DevToolsActivePort 不存在                    → Chrome 是否已在后台运行?        → 先杀掉旧 Chrome
                                              (tasklist | grep chrome)
cannot connect to chrome at 127.0.0.1:9222  → 9222 端口是否已监听?           → Chrome 启动时加 --remote
                                              (netstat -ano | grep 9222)       -debugging-port=9222
session not created                          → Chromedriver 版本 vs            → 更新 chromedriver 或
                                               Chrome 版本是否匹配?             用 Selenium Manager
```

### 启动 Chrome（远程调试模式）

先在终端手动启动 Chrome + 远程调试端口，确认端口监听成功后再跑脚本：

```bash
# 1. 杀掉所有旧 Chrome
taskkill /F /IM chrome.exe

# 2. 启动带调试端口的 Chrome
start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" ^
  --remote-debugging-port=9222 ^
  --user-data-dir="C:\Users\Admin\AppData\Local\Google\Chrome\User Data" ^
  --profile-directory=Default ^
  --new-window "https://web.whatsapp.com"

# 3. 确认端口已监听
sleep 3 && netstat -ano | grep 9222
```

### Chromedriver 位置

```bash
# Chromedriver 在 Selenium 缓存中
ls /c/Users/Admin/.cache/selenium/chromedriver/win64/
# 当前版本: 148.0.7778.178 (2026-06-01)

# 查看 Chrome 版本:
"C:/Program Files/Google/Chrome/Application/chrome.exe" --version
```

### 已知问题（本机环境）

| 问题 | 说明 |
|------|------|
| 旧 Chrome 残留进程 | Windows 上 Chrome 常有多达 10-20 个后台进程（`--enable-automation` flag），不杀光无法启动新实例 |
| Chromedriver 内置 Chrome 启动 | Selenium 4.44.0 的 chromedriver 尝试内置启动 Chrome 但 DevTools 端口不可达 |
| 解决方法 | 用 `debuggerAddress` 连接已有 Chrome 实例，而非让 chromedriver 自己起 Chrome |

### 最稳健的 Python 启动方式

```python
import subprocess
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# 1. 杀旧 Chrome
subprocess.run("taskkill /F /IM chrome.exe 2>nul", shell=True)

# 2. 启动远程调试 Chrome
chrome_proc = subprocess.Popen([
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "--remote-debugging-port=9222",
    "--user-data-dir=C:\Users\Admin\AppData\Local\Google\Chrome\User Data",
    "--profile-directory=Default",
    "https://web.whatsapp.com"
])

# 3. 等待 Chrome 启动
time.sleep(3)

# 4. 通过调试端口连接
opts = Options()
opts.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
driver = webdriver.Chrome(options=opts)
```

### 首次扫码登录

- 脚本首次运行会打开 WhatsApp Web → 显示二维码
- **用手机 WhatsApp → ⋮ 右上角菜单 → 已链接的设备 → 扫描**
- 登录成功后 profile 自动保存到 `Chrome User Data\Default`，下次不用再扫
- 超时等待：首次 30s 检测，若未登录再等 120s