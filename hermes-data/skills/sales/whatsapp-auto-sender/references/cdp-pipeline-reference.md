# Playwright CDP WhatsApp Pipeline — Pipeline Architecture Reference

## Full Data Chain

```
Excel / Search Results (raw leads)
  ↓
iiot_search_enriched_<date>.json          ← crawl_buyer_leads.mjs 或 build_enriched_for_whatsapp.py
  ↓
whatsapp_priority_queue_<date>.json       ← build_whatsapp_queue.mjs (filter WhatsApp-only, sort by fitScore)
  ↓
whatsapp_messages_<date>.json             ← render_whatsapp_messages.mjs (4 styles × variations)
  ↓
whatsapp_bulk_send_results_<date>.json    ← whatsapp_bulk_sender_cdp.mjs (Playwright CDP send)
```

## error 类型与处理

| 错误 | 原因 | 处理方式 |
|------|------|----------|
| `net::ERR_ABORTED` | WhatsApp Web 页面跳转到 send URL 时被自身中断（导航竞争） | 脚本跳过该条目继续下一个；可重试该条 |
| `locator.waitFor: Timeout Nms exceeded. Call log: waiting for locator('button[aria-label="发送"]...'` | 号码未注册 WhatsApp / 页面没加载完 send button | 自动跳过（标记未注册），继续下一个 |
| `Cannot find page with WhatsApp` | CDP 连接时 WhatsApp 页面未打开 | 先打开 web.whatsapp.com |

## Chrome CDP 架构

```
Chrome Instance (persistent, started at boot or manually)
  ├── remote-debugging-port=9223
  ├── user-data-dir=%LOCALAPPDATA%\hermes\chrome-profiles\whatsapp-bulk
  └── → web.whatsapp.com (1 page only, kept open)

Playwright CDP Client (node whatsapp_bulk_sender_cdp.mjs)
  ├── chromium.connectOverCDP('http://127.0.0.1:9223')
  ├── pickPage() → find or create WhatsApp page
  ├── ensureLoggedIn() → check for QR code / link device
  ├── for each lead:
  │     ├── page.goto(sendUrl) → open chat with pre-filled message
  │     ├── waitForComposer() → wait for input or send button
  │     ├── clickSend() → click send or press Enter
  │     └── sleep(delayMs)
  └── write results JSON
```

## send URL 格式

```
https://web.whatsapp.com/send?phone=<digits_only>&text=<urlencoded_message>
```

Phone: digits only (no +, no spaces, no dashes)。
Example: `+27 82 363 7667` → `27823637667`

## 发送器参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--mode` | prepare | `send`=实际发送, `prepare`=只打开聊天不点发送 |
| `--queue` | messages JSON path | 消息文件路径 |
| `--limit` | 0 (不限) | 本次发送条数上限 |
| `--start-index` | 0 | 从第几条开始（0-indexed） |
| `--delay-ms` | 2500 | 每条后等待毫秒 |
| `--headless` | 可见窗口 | 设为 headless 模式 |
| `--allow-resend` | false | 跳过查重，允许再次发送已发号码 |

## Playwright send button 优先级检测策略

```javascript
const sendCandidates = [
  page.getByRole("button", { name: "发送", exact: true }),
  page.getByRole("button", { name: "Send", exact: true }),
  page.locator('span[data-icon="send"]').locator(".."),
  page.locator('button[aria-label="发送"]'),
  page.locator('button[aria-label="Send"]'),
];
// 以上都失败则按 Enter
```

## Pre-send Duplicate Audit

**Version added:** v3 (2026-06-02)
**Registry file:** `C:\Users\Admin\AppData\Local\hermes\memories\buyer-development\whatsapp_sent_registry.json`

### How it works

1. `whatsapp_bulk_sender_cdp.mjs` → `loadSentRegistry()` 启动时自动扫描所有历史 `whatsapp_bulk_send_results_*.json`
2. 按 `normalizePhone(whatsapp_number)` 建立唯一键注册表
3. 只索引 `status === "sent"` 的条目（error/prepared 不算）
4. 注册表字段：
   ```json
   {
     "27823637667": {
       "phone": "27823637667",
       "first_sent_at": "2026-06-02-02-07-17",
       "last_sent_at": "2026-06-02-02-08-57",
       "names": ["Agora Automation (Pty)Ltd"],
       "variants": ["scada_plc-v1-3-1-2-2-3-2"],
       "files": ["whatsapp_bulk_send_results_2026-06-02-02-07-17.json"],
       "send_count": 2
     }
   }
   ```
5. 发送循环中：`if (!options.allowResend && normalizedPhone && sentRegistry[normalizedPhone])` → `skipped_already_sent`，跳过
6. 发送成功后即时更新注册表中的 `last_sent_at` / `send_count` / `names` / `variants`
7. 写结果文件后再写回注册表文件持久化

### New sender parameter

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--allow-resend` | false | 覆盖查重，允许给已发号码再发一次 |

## 消息渲染样式库（4 种 style × 多变体，v3 升级版）

### v3 核心变更

1. **新增 `greeting` 组件** — 每条消息以礼貌开头开头（如 "Hope you are having a wonderful day."）
2. **新增 `company_pitch` 组件** — 每个 style 独立介绍 BLIIOT 做什么，4种说法
3. **消息结构变为 9 段固定顺序**：greeting → intro → company_pitch → observation → offer → value → cta → link → close
4. **产品名标准化** — 不再贴原始品牌名+括号技术参数，改用自然语言缩写

### 产品名标准化规则

| 原始产品名 | 标准化后 |
|-----------|---------|
| `BLIIOT gateways/routers (R40, BA/BE/BL gateway series)` | `industrial gateways and routers` |
| `ARMxy edge computers/controllers` | `ARM edge controllers` |
| `Remote IO / RTU / data acquisition modules` | `remote I/O and data acquisition devices` |

标准化函数（`shortProductText`）：先按正则匹配替换，再去掉 `BLIIOT` 前缀和括号内容，`[...new Set()]` 去重后用 `together with` 连接

### greeting 变体（5种）

```javascript
greeting: [
  "Hope you are having a wonderful day.",
  "Hope you are having a great day.",
  "Wishing you a pleasant day.",
  "Hope your day is going well.",
  "Hope you are enjoying a good day.",
]
```

### company_pitch 示例（scada_plc style）

```javascript
company_pitch: [
  "BLIIOT is a supplier of industrial IoT hardware, focusing on industrial gateways, edge controllers, and remote data acquisition devices for automation projects.",
  "BLIIOT mainly provides industrial gateways, ARM edge controllers, and remote I/O products for PLC, SCADA, and industrial communication applications.",
  "Our company focuses on industrial IoT connectivity products, especially gateways, edge controllers, and field data acquisition devices used in automation systems.",
  "BLIIOT is a manufacturer of industrial communication and IIoT hardware, with product lines for gateways, edge controllers, and remote monitoring devices.",
]
```

### 完整消息示例

```
# scada_plc style, queue_id=1, Agora Automation
"Hope you are having a wonderful day. Hello, this is Kali from BLIIOT.
Our company focuses on industrial IoT connectivity products, especially gateways,
edge controllers, and field data acquisition devices used in automation systems.
It looks like your projects involve PLC connectivity and industrial protocol conversion
/ automation gateway and edge integration. Our industrial gateways and routers together
with ARM edge controllers are often used in PLC, SCADA, and industrial communication
projects. They are suitable for projects that need protocol conversion, remote access,
and reliable field data collection. If you have a current requirement, I would be glad
to suggest matching models for your application. If helpful, you can first review our
website here: https://bliiot.com/ Let me know if you would like a quick catalog."
```

### 4 种 style 的 company_pitch 差异（v3 新增）

| Style | company_pitch 重点 |
|-------|-------------------|
| scada_plc | 强调 PLC/SCADA 通信应用，工业网关+ARM边缘控制器+远程IO |
| system_integrator | 强调集成项目，设备联网+协议转换+远程监控 |
| energy_monitoring | 强调远程监控、公用事业数据传输、分布式设备接入 |
| generic_iiot | 最通用，工业 IoT 连接硬件、协议转换、边缘接入 |

### variant_id 生成逻辑（不变）

```
variant_id = `${styleId}-v${introIndex}-${observationIndex}-${offerIndex}-${valueIndex}-${ctaIndex}-${linkIndex}-${closeIndex}`
```

但 v3 新增了 greeting 和 company_pitch 组件（在 `variant_parts` 中不追踪，通过 seed 确定性选择）。

### variant_id 在 v3 中的含义变化

v3 的 variant_id 仍使用原来的 7 个索引（intro/observation/offer/value/cta/link/close），greeting 和 company_pitch 通过独立的 seed 派生 `pickIndex(width, seed, 19, 6)` 和 `pickIndex(width, seed, 17, 5)` 确定，不在 variant_id 中体现。

## 消息渲染变体追溯

### variant_parts 字段结构

追踪每条消息实际使用了哪些变体组件索引，方便后续分析哪种组合回复率更高：

```json
"variant_parts": {
  "intro": 1,          // shared: "Hello, this is Kali from BLIIOT."
  "observation": 3,   // style-specific: "It looks like your projects involve..."
  "offer": 1,         // style-specific
  "value": 2,         // style-specific
  "cta": 2,           // style-specific
  "link": 3,          // shared: "If helpful, you can first review our website..."
  "close": 2          // shared: "Let me know if you would like a quick catalog."
}
```

变体选择的 seed = `lead.queue_id`（保证同一个客户每次渲染得到相同变体组合）。

## 看门狗（自动监控文件变化）

脚本: `scripts/buyer-development-watcher/watch_files.py`
Cron: `every 5m`, no_agent=true
监控: 12个文件（6 data + 5 scripts + 动态结果）
行为: 无变化静默，有变化输出简报

## 终端号码遮盖（⚠️ 开发中常见困惑）

Excel 里存的号码是完整的（如 `+27 82 363 7667`），但**终端输出**和 `read_file` 工具会**自动遮盖中间数字**为 `****`（如 `+278****7667`）作为隐私保护。

**真实号码没有问题！** 验证方法：
```python
>>> phone = '+27 82 363 7667'
>>> phone.replace(' ', '')
'+2783637667'  # 不是 +278****7667!
```

不影响发送流程——`whatsapp_bulk_sender_cdp.mjs` 中的 `normalizePhone()` 函数正确去掉空格后使用完整号码。

- ZODSAT Zimbabwe → 已有客户（正在做变压器防盗项目），跳过群发，单独跟进
- Powertel Zimbabwe → 已有合作伙伴（电信+SmartGrid），跳过群发
- 标记 "EXISTING CUSTOMER" 或 "EXISTING PARTNER" 的 → 跳过