# Playwright MCP 读取 WhatsApp 消息（2026-06-17 验证）

## 架构要点

Playwright MCP（`mcp_playwright_browser_*` 工具）**创建自己的独立浏览器会话**，不连接已有的 CDP 端口（如 9223）。这意味着：

- 即使 CDP 端口 9223 的 Chrome 没开，Playwright MCP 也能自己启动浏览器
- Playwright MCP 的浏览器和 CDP 端口的 Chrome 是**两个独立的实例**
- 登录状态不共享（Playwright MCP 需要自己的 WhatsApp 登录 session）
- 如果 CDP 端口的 Chrome 已经登录了 WhatsApp，Playwright MCP 的浏览器**不会自动继承**登录状态

## 完整工作流

### 1. 启动 Chrome（如果 CDP 端口没开）

```bash
# 启动带 CDP 端口的 Chrome（whatsapp-bulk profile）
"/c/Program Files/Google/Chrome/Application/chrome.exe" \
  --remote-debugging-port=9223 \
  --user-data-dir="$APPDATA/hermes/chrome-profiles/whatsapp-bulk" \
  --new-window "https://web.whatsapp.com"
```

### 2. 用 Playwright MCP 导航到 WhatsApp Web

```javascript
await page.goto('https://web.whatsapp.com');
```

### 3. 等待加载完成

```javascript
await new Promise(f => setTimeout(f, 8000)); // 等8秒加载
```

### 4. 读取聊天列表

`mcp_playwright_browser_snapshot()` 返回完整的聊天列表，包含：

- 每个聊天的联系人名、最后消息预览、时间
- 未读消息数（如 `"2条未读消息"`）
- 置顶标记（`"已置顶的聊天"`）
- 静音标记（`"已静音的聊天"`）
- 星标标记（`"已加星标的聊天"`）
- 已读/已送达状态
- 表情反应（如 `"对以下消息留下了心情 👍"`）

### 5. 点击进入特定聊天

```javascript
// 用文本匹配点击
await page.locator('text="Arnold Chimambo"').click();
```

### 6. 读取完整聊天历史

`mcp_playwright_browser_snapshot(full=true)` 返回该聊天的完整消息历史，包含：

- **每条消息的发送者**（`"你："` 或 `"联系人名："`）
- **时间戳**（如 `16:41`, `昨天`, `星期一`）
- **已读/已送达状态**（`"已读"` + `wds-ic-read` 图标）
- **引用消息**（`"引用的消息"` 按钮 + 被引用的原文）
- **图片/影音内容**（`"打开图片"` 按钮 + `"转发影音内容"`）
- **长消息截断**（`"查看更多"` 按钮表示消息被截断）
- **系统提示**（如 `"在手机上使用 WhatsApp 可查看2026年3月19日之前的较早消息。"`）

### 7. 消息结构示例

```
昨天
  Arnold Chimambo： Noted thanks 16:41
  你： 打开图片 17:34 已读
  你： My boss would like to ask if this type of enclosure is acceptable for you? 17:35 已读
  Arnold Chimambo： Yes 17:35
  你： Ok,thank you! 17:37 已读
今天
  Arnold Chimambo： Morning 13:46
  Arnold Chimambo： Did you confirm about the payment issue 13:46
  你： Morning 14:13 已读
  你： We are still awaiting the final confirmation... 14:13 已读
  Arnold Chimambo： Ok noted 14:30
  你： Hello, thank you so much for your patience... 20:18 已读
  Arnold Chimambo： Please find our detailed responses... 21:25
  你： 引用的消息 Thank you for your reply ！ 22:01 已读
  你： Hello, our boss would like to confirm... 22:45 已送达
```

## 关键发现

1. **Playwright MCP 浏览器 ≠ CDP 端口浏览器** — 它们是独立的。如果 CDP 端口的 Chrome 已经登录了 WhatsApp，Playwright MCP 的浏览器可能还需要重新扫码。

2. **长消息自动截断** — WhatsApp Web 在 snapshot 中会截断长消息，显示 `"查看更多"` 按钮。要获取完整内容，需要点击该按钮。

3. **引用消息可展开** — `"引用的消息"` 按钮包含被引用消息的完整内容，在 snapshot 中可见。

4. **图片消息** — 显示为 `"打开图片"` 按钮，无法直接读取图片内容（需要 vision 分析）。

5. **时间分组** — 消息按 `昨天` / `今天` / `星期X` 分组，方便定位。

6. **表情反应** — 显示为 `"对以下消息留下了心情 🙏"` 格式。

## 与 CDP 脚本发送的配合

- **读取消息**：用 Playwright MCP（本方法）
- **发送消息**：用 `whatsapp_bulk_sender_cdp.mjs`（CDP 端口 9223 脚本）
- 两者使用不同的浏览器实例，互不干扰
- 读取后如需回复，用 CDP 脚本或手动在 Playwright MCP 浏览器中操作
