---
name: human-like-behavior
version: 1.0.0
description: 像人一样操作——所有行为必须模仿人类的随机性和节奏，禁止机器人式高频操作
tags: [behavior, anti-bot, delay, randomization, core-rule]
---

# 像人一样操作 🧸

## 操作铁律

### WhatsApp 读消息必做步骤
1. 打开对话后，**必须先滚到最顶部**（scrollTop=0），等3秒加载
2. 从第一条消息开始逐条往下读
3. 用JS提取所有消息文本：`document.querySelectorAll('[data-pre-rendered] span')` 或手动滚动+snapshot
4. 特别注意：聊天列表预览只显示最后一条，**不代表整段对话**
5. 整理出完整需求清单后再行动
6. 绝不能只看最后一条"You are welcome"就觉得读完了

### ⚠️ 工具选择铁则：WhatsApp 只能用 CDP，不能用 Playwright

**❌ 绝对禁止用 Playwright MCP（`mcp_playwright_browser_*`）操作 WhatsApp Web**
- Playwright 启动的是**全新浏览器实例**，跟本机已登录的 Chrome 完全隔离
- WhatsApp 很容易检测到 Playwright 的自动化特征（不同的指纹、无登录态、需要重新扫码）
- 每次都要重新登录 WhatsApp Web，极不方便
- 容易被平台封号

**✅ 必须用 Hermes 原生浏览器工具（`browser_navigate`、`browser_click`、`browser_snapshot`、`browser_scroll`、`browser_type`）通过 CDP 9223 端口**
- 直接连接到本机已登录好 WhatsApp Web 的 Chrome
- 共享本机浏览器的登录态、Cookie、指纹
- WhatsApp 看到的是正常浏览器操作，不会被检测为自动化
- 操作之间加随机延迟（2-8秒）模仿人类

**Playwright 的适用场景（非 WhatsApp）：**
- 需要独立浏览器环境的测试/调试
- 需要截图/PDF生成的场景
- 访问需要 JS 渲染但不想污染本机浏览器的页面
- 日报图片爬取（og:image 提取）

**所有操作——无论是直接操作浏览器/终端，还是脚本里的自动化行为——都必须模仿人类的节奏和随机性。**

这不是可选建议，是强制行为准则。

## 为什么

机器人式操作的特征：
- 工具调用之间零延迟，biubiubiu连发
- 浏览器操作连续快速点击
- 脚本一秒发十条消息
- 所有操作间隔完全一致
- 思考→操作之间没有自然停顿

这些行为模式：
1. 容易被反爬/风控系统检测
2. 容易被平台封号（WhatsApp/LinkedIn等）
3. 不自然，一看就不是人在操作
4. Kali明确纠正过多次

## 具体规则

### 1. 直接操作（浏览器/终端/工具调用）

- 工具调用之间加 **2-8秒随机延迟**（`random.uniform(2, 8)`）
- 不能连续快速点击，每次点击前有自然间隔
- 思考→操作之间有自然停顿（先想一下再动手）
- 读到信息后不要秒回，像人一样先消化一下
- 打字速度不均匀，有时快有时慢

### 2. 脚本中的自动化行为

- 请求间隔：`random.uniform(3, 10)` 秒（不同请求不同间隔）
- 批量操作：每5-10个操作加一个更长休息 `random.uniform(15, 45)` 秒
- 发送消息：每条之间 `random.uniform(45, 90)` 秒（WhatsApp等敏感平台更长）
- 批次间休息：每发5条消息休息 `random.uniform(120, 300)` 秒
- 每日上限：WhatsApp 50条，邮件 50封

### 3. 浏览器操作

- 页面加载后等待 `random.uniform(1, 3)` 秒再操作
- 点击前鼠标先移动（Playwright的hover）
- 滚动速度不均匀，有时快滚有时慢滚
- 不要在页面加载完0.1秒就找到精确元素并点击
- 偶尔"犹豫"一下（random chance 10%加2-5秒额外延迟）

### 4. 打字/输入

- 使用 `slowly=true` 或逐字符输入 + 随机间隔
- 打字速度模拟：每字符 `random.uniform(0.03, 0.15)` 秒
- 偶尔打错再删除重打（极低概率，<2%）

### 5. 思考节奏

- 收到消息后不要秒回，先"想一想"（1-5秒）
- 长回复分段发送（像人打字一样逐步出现）
- 不要一口气列出10个工具调用然后同时发出去
- 有时候先说一句话，过几秒再说下一句

## 代码模板

### Python 脚本随机延迟

```python
import random
import time

def human_delay(min_s=2, max_s=8):
    """像人一样的随机延迟"""
    time.sleep(random.uniform(min_s, max_s))

def batch_human_delay(item_count, batch_size=5):
    """批量操作间的人类节奏"""
    for i in range(item_count):
        # 单次操作间隔
        time.sleep(random.uniform(3, 10))
        # 每5个操作加一个长休息
        if (i + 1) % batch_size == 0:
            time.sleep(random.uniform(30, 120))
```

### JavaScript/Node 脚本随机延迟

```javascript
const humanDelay = (minMs = 2000, maxMs = 8000) =>
  new Promise(r => setTimeout(r, Math.random() * (maxMs - minMs) + minMs));

const batchWithDelay = async (items, fn, batchSize = 5) => {
  for (let i = 0; i < items.length; i++) {
    await fn(items[i]);
    await humanDelay(3000, 10000);
    if ((i + 1) % batchSize === 0) {
      await humanDelay(30000, 120000); // 长休息
    }
  }
};
```

## 反面教材（❌ 禁止这样做）

- 0.1秒内连发5个工具调用
- WhatsApp脚本每条消息间隔0.5秒
- 浏览器页面加载完0.01秒就点击按钮
- 所有操作间隔精确到毫秒（一模一样）
- 脚本里写死 `time.sleep(1)` 无变化

## 检查清单

每次写脚本或直接操作前问自己：

- [ ] 操作之间有随机延迟吗？
- [ ] 延迟时长有变化吗（不是固定值）？
- [ ] 批量操作有长休息吗？
- [ ] 浏览器操作像人在用吗？
- [ ] 发消息节奏像人在打字吗？

## 来源

Kali多次纠正：
1. "你搞得行为不要像机器人那样很快的去操作，你要像人一样，要模仿人随机性延迟性"
2. "像人一样，不只是一个提醒，是让你必须要去改进你的一个行为模式"
3. "无论是你的脚本还是说你是怎么样操作的，你必须要像人一样"
4. WhatsApp开发信脚本必须加随机延迟（2-5分钟间隔）防封号