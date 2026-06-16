# Nodriver + Scrapling 研究笔记

## 发现时间：2026-06-04

## 背景
BLIIOT 客户开发管道频繁被 Cloudflare / 反检测拦（富通搜索、Google Maps）。现有方案是 Selenium + CDP，存在检测率高、性能慢的问题。

## 核心发现

### nodriver (v0.50.3)
undetected-chromedriver 的继任者。2026 年 browser benchmark **唯一全通过 Cloudflare** 的 Python 库。

**反检测技术：**
- 无 chromedriver 进程 → `navigator.webdriver` 永远 undefined
- 16 个隐身启动参数（`--no-first-run`, `--disable-breakpad` 等）
- 临时用户目录（每次 `mkdtemp`）
- 全异步 CDP 通信，比 Selenium 快 5-10x
- 支持 `cdp_url` 参数 → 可连接到已有的 Chrome CDP 实例

**关键 API：**
```python
import nodriver as nd

# 最简单的用法
browser = await nd.start()
tab = await browser.get("https://example.com")
text = await tab.text()
await tab.scroll_down(500)

# 连接到已有 CDP（如 WhatsApp 的 9223 端口）
config = nd.Config()
config.host = "127.0.0.1"
config.port = 9223
# 注意：nodriver 当前版本不支持直接 attach 到已运行的 CDP
# 替代：用 playwright 的 connect_over_cdp
```

### scrapling (v0.4.8)
自适应爬虫框架。三层自动降级架构：Fetcher(基础请求) → DynamicFetcher(Playwright) → StealthyFetcher(patchright)。

**核心反检测技术：**
- **patchright 底层**：Playwright 的 stealth fork，浏览器引擎层改指纹（不是 JS 注入），比 undetected-chromedriver 更深层
- **Cloudflare Turnstile 自动破解**：检测 iframe 类型 → 模拟鼠标点击 → 等待网络空闲 → 递归重试
- **browserforge 指纹生成**：真实指纹引擎，自动匹配 Chrome 版本 + 当前 OS + 浏览器类型
- **Canvas 噪声**：随机噪声防 Canvas 指纹
- **WebRTC 防泄漏**：强制 WebRTC 走代理
- **DNS-over-HTTPS**：防 DNS 泄漏

**关键 API：**
```python
from scrapling import StealthyFetcher

# 一行搞定 Cloudflare（当前管道的痛点）
resp = StealthyFetcher.fetch(
    "https://data.joinf.com/api/bs/searchBusiness",
    solve_cloudflare=True,
    headless=True,
    real_chrome=True,  # 用本机 Chrome
)

# 带 page_action 的自定义自动化
resp = StealthyFetcher.fetch(
    "https://example.com",
    page_action=lambda page: page.click("#submit"),
    headless=False,
)
```

## 对现有管道的改进价值

| 管道 | 当前方案 | 痛点 | 可用改进 |
|:----|:---------|:-----|:---------|
| 富通搜索 (joinf.com) | Selenium + CDP 9226 | Cloudflare Turnstile 频拦 | scrapling `solve_cloudflare=True` |
| WhatsApp 发送 | Playwright CDP 9223 | 无 | nodriver 性能提升 5-10x |
| Google Maps 客户 | Selenium | Google 反爬检测 | scrapling `real_chrome=True` + patchright |

## 安装命令
```bash
pip install nodriver
pip install scrapling
# 两者都已安装在 Hermes venv 中
```

## 关键限制
- nodriver 当前版本（0.50.3）不支持通过 CDP URL 连接到已有浏览器实例 → WhatsApp 场景仍需用 Playwright
- scrapling 的 `solve_cloudflare=True` 需要 patchright 底层（已自带），但需要 Chromium 浏览器
- Windows 上 `real_chrome=True` 会自动检测本机 Chrome
