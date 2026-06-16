<!-- SKILL.md -->
---
name: playwright-advanced
description: "Playwright 高级模式 — 反检测、网络拦截、CDP连接、多页面并发、PDF生成、视觉对比"
version: 1.0.0
author: agent (小马)
---

# Playwright 高级模式

## 核心要点

### 1. 反检测技术
- **playwright-stealth** 包自动打补丁（webdriver/plugins/chrome）
- `add_init_script()` 在页面加载前注入 JS 补丁
- `--disable-blink-features=AutomationControlled` 启动参数
- 手动设置 `user_agent` / `viewport` / `locale` / `timezone_id` / `geolocation`
- 检测网址: `https://bot.sannysoft.com`

### 2. 网络拦截
- `page.route("**/*", handler)` 拦截所有请求
- `route.abort()` 阻止图片/字体（节省带宽）
- `route.fulfill()` 返回 Mock 数据（无需后端）
- `route.continue_(headers=new_headers)` 修改请求头
- `page.on("console")` 捕获浏览器 console 消息

### 3. CDP 连接
- `chromium.connect_over_cdp("http://127.0.0.1:9223")` 连接已有 Chrome
- 共享登录态/Cookie/Session
- 不关浏览器（用户还在用）
- 端口 9223=WhatsApp 发送, 9226=富通搜索

### 4. 多页面并发
- `asyncio.gather(*tasks)` 并行 N 个页面
- 页面池（3-5个页面共享 context/Cookie）
- `new_context()` 每次独立 Cookie jar

### 5. 截图 & PDF
- `full_page=True` 全页截图
- `clip={"x","y","width","height"}` 裁剪截图
- `page.pdf(format="A4")` 通过 Playwright 生成 PDF
- 视觉对比：MD5 哈希检测变化，PIL + numpy 像素级差异

## 脚本清单

| # | 文件 | 核心内容 | 状态 |
|---|------|---------|------|
| 1 | `01_stealth_anti_detection.py` | Stealth + 反检测补丁 | ✅ |
| 2 | `02_network_intercept.py` | 路由拦截 + Mock + Console 捕获 | ✅ |
| 3 | `03_cdp_multi_page.py` | CDP 连接 + 并行抓取 + 页面池 | ✅ |
| 4 | `04_screenshot_pdf.py` | 截图技术 + PDF 生成 + 视觉对比 | ✅ |

## 依赖
```
playwright >= 1.59
playwright-stealth >= 2.0
pillow              # 可选：视觉对比
numpy               # 可选：像素级对比
```