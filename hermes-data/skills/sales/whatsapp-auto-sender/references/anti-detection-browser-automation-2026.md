# 反检测浏览器自动化技术 — 2026 年最新方案

2026-06-04 从 GitHub 研究 nodriver (0.50.3) 和 scrapling (0.4.8) 源码后总结。

## 检测层级

反检测系统（Cloudflare Turnstile / DataDome / Imperva / reCAPTCHA v3）按以下维度评分：

| 检测点 | 检测内容 | 传统方案弱点 |
|:-------|:---------|:------------|
| `navigator.webdriver` | Selenium/Playwright 标记 | chromedriver 会设 `true` |
| Chrome 启动参数 | `--headless`, `--enable-automation` | 启动痕迹泄漏 |
| 浏览器指纹 | Canvas/WebGL/Fonts/WebRTC | 每次访问指纹不同 |
| 行为模式 | 鼠标轨迹、点击间隔、滚动模式 | Selenium 太"机械" |
| IP/ASN 信誉 | 数据中心 IP、代理 IP | 容易被标记 |
| TLS 握手 | JA3 指纹 | curl/requests 的 TLS 栈和浏览器不一样 |

## 方案对比

| 方案 | 原理 | Cloudflare 通过率 | 适用场景 |
|:-----|:-----|:----------------:|:---------|
| **Selenium + undetected-chromedriver** | JS patch 隐藏 webdriver | ~60% | 入门 |
| **nodriver (0.50.3)** | 纯 CDP 驱动，无 chromedriver 进程 | **2026 benchmark 唯一全通过** | Python 原生浏览器自动化 |
| **scrapling (0.4.8)** | patchright(Playwright stealth fork) + Cloudflare 自动破解 | ~90% | 爬虫/数据采集 |
| **CloakBrowser** | C++ 源码级改指纹，编译 Chromium 二进制 | **~95%+** | 最高级反检测 |

## nodriver (0.50.3)

已安装（`pip install nodriver`）。

**核心优势：**
- 无 chromedriver 进程 → `navigator.webdriver` 返回 `undefined`
- 16 个隐身启动参数（`--no-first-run`, `--disable-infobars` 等）
- 每次临时 User Data Dir，指纹无残留
- 全 async CDP 通信，性能比 Selenium 快 5-10 倍

**基本用法：**
```python
import asyncio
import nodriver as nd

async def main():
    browser = await nd.start()  # 最佳实践默认配置
    tab = await browser.get("https://example.com")
    text = await tab.text()
    print(text)

asyncio.run(main())
```

**连接到已有 CDP 端口（用于 WhatsApp 现有浏览器）：**
```python
# 连接到已有的 Chrome CDP（端口 9223）
browser = await nd.start(
    host="127.0.0.1",
    port=9223,
    sandbox=False,
)
```

## scrapling (0.4.8)

已安装（`pip install scrapling`）。

**核心优势：**
- **`solve_cloudflare=True`** — 自动检测 Turnstile 类型 → 模拟鼠标点击 → 等待 → 递归重试
- **browserforge** 指纹引擎 — 自动生成和 Chrome 147 完全匹配的 headers/UA
- **自适应**：Fetcher(基础) → DynamicFetcher(Playwright) → StealthyFetcher(patchright)
- Canvas 噪声、WebRTC 防泄漏、DNS-over-HTTPS、Google referer

**一键解决 Cloudflare：**
```python
from scrapling import StealthyFetcher

# 自动破解 Cloudflare Turnstile
resp = StealthyFetcher.fetch(
    "https://target.com",
    headless=True,
    solve_cloudflare=True,      # ← 自动破解
    real_chrome=True,            # 使用本机已安装的 Chrome
    hide_canvas=True,            # Canvas 指纹噪声
    block_webrtc=True,           # 防止 IP 泄漏
)
print(resp.text[:500])
```

## 对我们管道的改进

| 管道 | 当前方案 | 改进方案 | 效果 |
|:-----|:---------|:---------|:-----|
| 富通搜索 (joinf.com) | CDP 9226 + Selenium | **scrapling StealthyFetcher(solve_cloudflare=True)** | 不再被 Cloudflare 拦截 |
| Google Maps 爬客户 | CDP 9226 + 手动交互 | **nodriver 连接到 9226** | 更快的页面交互 |
| WhatsApp 发送 | CDP 9223 + Selenium | **nodriver 连接到 9223** | 异步加速，不抢前台 |

## 参考

- https://github.com/ultrafunkamsterdam/nodriver — nodriver (ucd 继任者)
- https://github.com/D4Vinci/Scrapling — 自适应爬虫框架
- https://github.com/CloakHQ/cloakbrowser — 源码级隐身 Chromium
