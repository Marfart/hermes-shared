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

## 回复风格铁律（Kali多次强调）

**直接给结论，不要冗长解释。** 读者已知上下文时一句话完事。

❌ 禁止行为：
- 解释为什么要这样做（"因为……所以……"）
- 重复客户已知的信息
- 工具调用失败时详细描述每一步尝试过程
- "首先……其次……最后……"式列举

✅ 正确行为：
- 一句话结论
- 可选方案用表格对比
- 只说对客户有用的信息
- 出错时一句话说明问题+解决方案

**铁律来源：**
- 客户说"以后这种可以选的就直接给我说可以！！我还以为不可以"
- 客户说"直接给我说那些型号不需要价格"
- 客户说"都给你说了全部权限，你办不成？" — 表明她期望我能解决而非解释为何做不到

## CDP 连接本机Chrome的完整工作流（Windows）

### ⚠️ 关键区别：用户需要"看到"页面时

**Hermes的 `browser_navigate` 用的是 Browserbase 云服务器，不会出现在用户屏幕上！**

当任务需要用户看到内容（扫码登录、视觉验证等）→ 必须用本机Chrome CDP。
后台自动化脚本、爬虫、不需要用户肉眼看到的 → 可以用Hermes Browserbase。

### 问题场景
Hermes 浏览器工具 + Playwright MCP 都连不上本机已登录的 Chrome，因为 CDP 远程调试端口未开。

### 解决步骤（agent可自动执行）

```bash
# Step 1: 杀掉所有chrome进程
taskkill //F //IM chrome.exe

# Step 2: 删除Singleton锁（关键！否则Chrome忽略--remote-debugging-port）
rm -f "/c/Users/Admin/AppData/Local/Google/Chrome/User Data/SingletonLock"
rm -f "/c/Users/Admin/AppData/Local/Google/Chrome/User Data/SingletonSocket"
rm -f "/c/Users/Admin/AppData/Local/Google/Chrome/User Data/SingletonCookie"

# Step 3: 用PowerShell启动（cmd.exe start 和 terminal后台 & 都不能正确传递参数）
powershell.exe -Command 'Start-Process "C:\Program Files\Google\Chrome\Application\chrome.exe" -ArgumentList "--remote-debugging-port=9223","--user-data-dir=C:\Users\Admin\AppData\Local\Google\Chrome\User Data","https://web.whatsapp.com"'
```

### 验证
```bash
sleep 6
netstat -ano | grep 9223
# 或
curl -s http://127.0.0.1:9223/json/version
```

### 启动失败排查
| 症状 | 原因 | 解决 |
|------|------|------|
| curl exit code 7 | Chrome起的快但端口未开 | 等几秒重试 |
| netstat无9223 | `cmd.exe start` 和 terminal `&` 不能传递--remote-debugging-port | 改用PowerShell Start-Process |
| Chrome起来但无9223 | SingletonLock未删，profile被占 | 删除Singleton锁文件 |

### 常见失败模式（均已验证）
- ❌ Hermes browser_navigate 访问whatsapp.com → 超时（Vortex代理墙了WhatsApp）
- ❌ Hermes browser_navigate 访问whatsapp.com → 页面在云端服务器，用户看不到！扫不了码
- ❌ Playwright MCP连接 → 全新实例，需重新登WhatsApp
- ❌ `cmd.exe start "" "chrome.exe" --remote-debugging-port=9223` → 参数不传递
- ❌ terminal background `&` → 被Hermes拦截报错
- ❌ 截图 → 黑色（页面没加载出来）
- ❌ CDP端口不通时放弃修复，转用Hermes浏览器+让用户扫云端二维码 → **零容忍！用户根本看不到云端页面**
- ✅ PowerShell Start-Process + 删除SingletonLock → 端口必然监听
- ✅ CDP不通时 → 自动执行修复流程（kill→delete Singleton→PowerShell restart）→ 不需要用户介入

### ⚠️ 行为铁律：CDP 不通时必须自动修复，绝不能让用户扫云端二维码

每次需要读WhatsApp/CDP操作前，按此顺序检查：
1. `curl -s http://localhost:9223/json/version` → 有响应则CDP正常，直接用
2. 无响应 → **立即自动执行上面的解决步骤**（kill Chrome + 删除Singleton + PowerShell重启）
3. 重启后验证端口 → 通了再操作WhatsApp
4. 整个过程**不需要用户介入**，agent全权完成

**绝不做的行为：**
- ❌ 看到CDP不通 → 转头用Hermes browser Navigate → "帮你截个图扫码吧"
- ❌ 说"先这样不行，我再想别的办法"而不是直接修复
- ❌ 让用户来解决Chrome启动问题

### WhatsApp 登录方式选择

WhatsApp Web 有两种登录方式：

1. **QR 码登录**（默认方式）— 手机WhatsApp扫码
2. **电话号码登录** — WhatsApp发6位验证码到手机

**什么时候用电话号码登录：**
- 二维码扫不进去（截图模糊、Playwright截图看不到二维码等）
- 手机摄像头故障
- 用户明确说"登不了了"

**电话号码登录操作步骤（Playwright MCP 实测验证 2026-06-29）：**

前提：Playwright MCP启动的是全新浏览器实例，无登录态，只能用电话号码登录。

1. `mcp_playwright_browser_navigate("https://web.whatsapp.com")`
2. 等待 8-10 秒让页面加载完整（QR码渲染需要时间）
3. `mcp_playwright_browser_snapshot()` 确认页面有"使用电话号码登录"按钮
4. `mcp_playwright_browser_click(element="使用电话号码登录按钮", target="<ref>")` — 切换到号码表单
5. 国家默认是阿曼(+968)，需要选择正确国家：
   - `mcp_playwright_browser_click(element="国家选择按钮", target="<按钮ref>")` 打开下拉列表
   - 在搜索框输入国家名（如"中国"）：`mcp_playwright_browser_fill_form(fields=[{"name":"搜索国家","target":"<搜索框ref>","type":"textbox","value":"中国"}])`
   - 等待2秒让筛选结果渲染
   - `mcp_playwright_browser_click(element="中国选项", target="<列表ref>")`
6. 输入电话号码（不含国家码）：`mcp_playwright_browser_type(element="电话号码输入框", target="<ref>", text="18111156001")`
7. `mcp_playwright_browser_click(element="下一步按钮", target="<ref>")`
8. 页面显示验证码分组（如 TZXH-FKRB），告知用户在手机上操作：
   - 打开手机WhatsApp → Android: 菜单 / iPhone: 设置
   - 已关联的设备 → 关联设备
   - 点"改用电话号码关联" → 输入验证码
9. 等待用户确认登录成功后继续操作

**⚠️ 关键注意事项：**
- Playwright MCP截图用户看不到 → 用 mcp_playwright_browser_take_screenshot 然后 MEDIA:path 发给用户
- console 经常返回null → 不要依赖 evaluate 获取页面数据，用 snapshot + text 提取
- 电话号码登录在 Playwright 中仍需用户在手机上操作验证码 → 不是全自动的
- CDP本机Chrome方案 > Playwright方案（共享登录态、无需重登）

### 特殊说明
- Playwright MCP 的 `connect_over_cdp("http://127.0.0.1:9223")` 也可以连，但MCP本身有超时问题
- 推荐用Hermes原生 `browser_navigate` 直接操作，不需要Playwright

## 来源

Kali多次纠正：
1. "你搞得行为不要像机器人那样很快的去操作，你要像人一样，要模仿人随机性延迟性"
2. "像人一样，不只是一个提醒，是让你必须要去改进你的一个行为模式"
3. "无论是你的脚本还是说你是怎么样操作的，你必须要像人一样"
4. WhatsApp开发信脚本必须加随机延迟（2-5分钟间隔）防封号
5. "直接给我说那些型号不需要价格"
6. "以后这种可以选的就直接给我说可以！！我还以为不可以"