# nodriver 0.50.3 + Scrapling 0.4.8 Source Code Analysis

Analyzed: 2026-06-04
Source: pip installed packages at `%LOCALAPPDATA%/hermes/hermes-agent/venv/Lib/site-packages/`

## nodriver Architecture

```
nodriver/
├── __init__.py       → exports: Browser, BrowserContext, Config, Connection, Tab, Element, start
├── core/             → namespace package
│   ├── config.py     → Config class (browser args, profile, extensions), find_chrome_executable()
│   ├── connection.py → CDP WebSocket connection management
│   ├── tab.py        → Tab operations (navigation, evaluate, click, type, screenshot)
│   ├── browser.py    → Browser lifecycle (launch, stop, new_tab, new_context)
│   ├── element.py    → Element interaction (click, type, hover, focus)
│   └── util.py       → Helper functions (stealth script injection, shadow DOM handling)
└── cdp/              → CDP protocol definitions (auto-generated from browser_protocol.json)
```

### Key Source Observations

1. **No stealth JS injection file** — unlike undetected-chromedriver which injects `stealth.min.js`, nodriver relies entirely on:
   - Native CDP connection (no chromedriver process)
   - Clean browser startup args
   - Temp profile per session
   
2. **Config constructor** initializes `_default_browser_args` as a list of 12 stealth flags (see SKILL.md)

3. **`find_chrome_executable()`** scans: PROGRAMFILES, PROGRAMFILES(X86), LOCALAPPDATA for Chrome/Chrome Beta/Chrome Canary on Windows

4. **`add_extension()`** supports both crx files and extension directories — unpacks crx to temp dir automatically

5. **Tab interaction uses `cdp.input_.dispatch_*`** — mouse events are dispatched through CDP Input domain, not JavaScript Event constructors. This is key for bypassing event-based detection.

## Scrapling Architecture

```
scrapling/
├── fetchers/                 → Public API layer
│   ├── __init__.py           → Lazy imports + mapping dict
│   ├── requests.py           → Fetcher, AsyncFetcher (curl_cffi based)
│   ├── chrome.py             → DynamicFetcher (Playwright, no stealth)
│   └── stealth_chrome.py     → StealthyFetcher (patchright + CF solver)
├── engines/                  → Core engine implementations
│   ├── _browsers/
│   │   ├── _stealth.py       → StealthySession, AsyncStealthySession (main implementation)
│   │   ├── _base.py          → SyncSession, AsyncSession, StealthySessionMixin
│   │   ├── _types.py         → StealthSession, StealthFetchParams TypedDicts
│   │   └── _validators.py    → validate_fetch, StealthConfig
│   ├── static.py             → Static HTTP engine (curl_cffi wrapper)
│   ├── toolbelt/
│   │   ├── fingerprints.py   → browserforge header generation
│   │   ├── proxy_rotation.py → ProxyRotator
│   │   ├── convertor.py      → Response class + ResponseFactory
│   │   ├── navigation.py     → URL normalization helpers
│   │   ├── custom.py         → BaseFetcher base class
│   │   └── ad_domains.py     → ~3,500 known ad/tracking domains
├── spiders/                  → Full crawl framework
│   ├── spider.py             → Spider class
│   ├── scheduler.py          → Request scheduler
│   ├── cache.py              → Request cache
│   ├── session.py            → Spider session management
│   └── templates/            → Pre-built spiders (crawler.py, sitemap.py)
├── core/
│   ├── custom_types.py       → All TypedDict/mixin definitions
│   ├── storage.py            → Data storage abstraction
│   ├── translator.py         → Data format converters
│   └── ai.py                 → AI integration helpers
├── parser.py                 → CSS/XPath selector engine
└── cli.py                    → Interactive scraping shell
```

### Key Source Observations

1. **StealthySession uses patchright, NOT playwright** — imports `from patchright.sync_api import sync_playwright`. Patchright is a Playwright fork with built-in stealth patches at the puppeteer-core level.

2. **`solve_cloudflare=True` triggers `_cloudflare_solver()`** which:
   - Waits for network idle (5s timeout)
   - Calls `_detect_cloudflare(content)` to classify challenge type
   - For non-interactive: simply waits for "Just a moment..." to disappear
   - For interactive/embedded: finds iframe matching `challenges.cloudflare.com/cdn-cgi/challenge-platform/` regex, gets bounding box, clicks at `bbox.x + random(26,28), bbox.y + random(25,27)` with 100-200ms delay
   - Recursive retry if still detected

3. **browserforge** generates Headers that match Chrome 147 (latest as of analysis date) including: User-Agent, Sec-CH-UA, Sec-CH-UA-Mobile, Sec-CH-UA-Platform, Sec-Fetch-*, Accept, Accept-Language, Accept-Encoding

4. **Proxy rotation** is implemented via `proxy_rotator` parameter. The `_base.py` session code checks for proxy errors after each fetch and rotates automatically.

5. **StealthyFetcher.configure() only sets parser keywords** (huge_tree, keep_comments, keep_cdata, adaptive, storage, storage_args, adaptive_domain) — NOT browser settings. Browser settings go directly to `fetch()` kwargs.

## 2026 Anti-Detect Benchmark Results (from community testing)

```
nodriver (0.50.3):        ✅ Passed all 31 Cloudflare gates (only library to do so)
undetected-chromedriver:  Passed 28/31 gates (score 0.3-0.7)
CloakBrowser:             reCAPTCHA v3 score 0.9 (C++ level patching)
playwright-stealth:       Score 0.3-0.5
patchright:               Score 0.5-0.8
```

## Connection to BLIIT Pipelines

### For joinf.com (富通) Cloudflare bypass:
```python
# Current: Selenium + CDP 9226, Cloudflare still blocks
# Solution: scrapling StealthyFetcher
from scrapling.fetchers import StealthyFetcher
resp = StealthyFetcher.fetch(
    'https://data.joinf.com/api/bs/searchBusiness',
    headless=True,
    solve_cloudflare=True,
    real_chrome=True,
    cdp_url='http://127.0.0.1:9226',  # Use existing Chrome!
    disable_resources=True,
)
```

### For WhatsApp Web (CDP 9223):
```python
# Current: Selenium ChromeDriver
# Solution: nodriver attach to existing CDP session
import nodriver
import asyncio

async def main():
    browser = await nodriver.start(
        user_data_dir=None,  # Use temp profile
        headless=False,
        browser_args=['--remote-debugging-port=9223'],
    )
    # Or attach to already-running Chrome:
    # browser = await nodriver.start(host='127.0.0.1', port=9223)
    tab = await browser.get('https://web.whatsapp.com')
    await tab.wait_for('canvas[aria-label]')  # QR scan
    # ... after manual scan, proceed with sending
```
