---
name: playwright-advanced
description: "Playwright 高级模式 — 反检测/网络拦截/CDP连接/多页面并发/PDF生成/视觉对比"
version: 1.0.0
author: agent
---

# Playwright 高级模式

当需要用 Playwright 做反检测抓取、网络拦截、CDP连接已有Chrome、多页面并发、PDF生成时加载此技能。

## 脚本位置
`memories/脚本缓存/playwright_advanced/`

> ⚡ `executable_path` 指向已有 chromium-1223（CDN 下载通过代理可能超时，见 `references/playwright-chromium-install-windows.md`）

## 1. 反检测 (01_stealth_anti_detection.py)

### 首选方案（推荐）：playwright-stealth 插件
```python
pip install playwright-stealth
```

```python
from playwright_stealth import stealth_async, stealth_sync

# async API
await stealth_async(page)
# sync API
stealth_sync(page)
```

`playwright-stealth` 自动处理：删除 `navigator.webdriver`、替换 HeadlessChrome User-Agent、修复 WebGL/Canvas 指纹泄漏等。比手动 JS 补丁更全。

### 备用方案：手动 JS 补丁
```python
# 启动参数关键
args=["--disable-blink-features=AutomationControlled"]

# init_script 在导航前注入 JS 补丁
await context.add_init_script("""
    Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
    window.chrome = {runtime: {}, loadTimes: function() {}, ...};
""")

# 手动指纹设置
context = await browser.new_context(
    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) ...",
    locale="en-US", timezone_id="America/New_York",
    geolocation={"latitude": 40.7128, "longitude": -74.0060},
)
```

## 2. 网络拦截 (02_network_intercept.py)
- `page.route("**/*", handler)` — 拦截当前页所有请求
- `browser_context.route("**/*", handler)` — 拦截整个 context（弹窗、新tab也生效）
- `route.abort("blockedbyclient")` — 阻止资源
- `route.fulfill(status=200, body=json.dumps(mock_data))` — Mock API
- `route.continue_(headers=new_headers)` — 修改请求头
- `page.on("console", handler)` — 捕获 console 消息

### 按资源类型拦截
```python
await page.route("**/*", lambda route: (
    route.abort() if route.request().resource_type == "image"
    else route.continue_()
))
```

### Glob URL 模式
- `*` — 匹配除 `/` 外任意字符
- `**` — 匹配任意字符含 `/`
- `{png,jpg,jpeg}` — 多选项匹配
- 例: `**/*.{png,jpg,jpeg,gif}` 匹配所有图片

### Mock API 响应
```python
await page.route("**/api/data", lambda route: route.fulfill(
    status=200,
    content_type="application/json",
    body='{"result": "mocked"}'
))
```

### 等待特定网络响应
```python
response = await page.wait_for_response("**/api/data")
# 或使用 predicate
response = await page.wait_for_response(
    lambda resp: "token" in resp.url
)
```

### 网络事件监听
```python
page.on("request", lambda req: print(">>", req.method, req.url))
page.on("response", lambda res: print("<<", res.status, res.url))
page.on("requestfinished", lambda req: print("done", req.url))
```

### WebSocket 监控
```python
page.on("websocket", lambda ws: print(f"WebSocket: {ws.url}"))
ws.on("framesent", lambda f: print(f">>> {f.payload}"))
ws.on("framereceived", lambda f: print(f"<<< {f.payload}"))
```

## 3. CDP 连接 (03_cdp_multi_page.py)
- `chromium.connect_over_cdp("http://127.0.0.1:9223")` — 连已有Chrome
- 共享 Cookie/登录态
- `asyncio.gather()` — 多页面并行

## 4. 截图/PDF (04_screenshot_pdf.py)
- `page.screenshot(full_page=True)` — 全页截图
- `page.pdf(format="A4")` — Playwright 生成 PDF
- MD5哈希或PIL+numpy像素级差异对比