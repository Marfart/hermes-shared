---
name: web-scraping
description: "Web scraping and anti-detection toolkit: Scrapling, nodriver, stealth bypass, search engine scraping, LinkedIn data extraction"
category: data-science
triggers:
  - "scrape"
  - "crawl"
  - "anti-detect"
  - "bypass cloudflare"
  - "linkedin scraper"
  - "google search scraper"
  - "web data extraction"
---

# Web Scraping & Anti-Detection Toolkit (v2)

## Tool Stack (installed)

| Tool | Version | Stars | Purpose | Install |
|------|---------|-------|---------|---------|
| [Scrapling](https://github.com/D4Vinci/Scrapling) | 0.4.8 | 20k⭐ | Adaptive parser + stealth fetcher + **Cloudflare Turnstile auto-solver** | `pip install scrapling[all]` |
| [nodriver](https://github.com/ultrafunkamsterdam/nodriver) | 0.50.3 | 4.3k⭐ | Successor to undetected-chromedriver, pure CDP, **#1 stealth in 2026 benchmark** | `pip install nodriver` |
| [CloakBrowser](https://github.com/CloakHQ/cloakbrowser) | NEW | — | **Source-level Chromium patching** — C++ layer fingerprint modification, reCAPTCHA v3 score 0.9 | `git clone` + auto-download pre-built binary |
| [undetected-chromedriver](https://github.com/ultrafunkamsterdam/undetected-chromedriver) | 3.5.5 | 10k⭐ | Patched ChromeDriver anti-detection (nodriver predecessor) | `pip install undetected-chromedriver` |
| [curl-cffi](https://github.com/yifeikong/curl_cffi) | — | 3k⭐ | TLS fingerprint impersonation | `pip install curl-cffi` |
| [patchright](https://github.com/naim-prog/patchright) | — | — | Playwright fork with built-in stealth patches (used by Scrapling internally) | `pip install patchright` + `patchright install` |

## Three-Layer Fetch Strategy

### Layer 1: Scrapling Fetcher (fast, ~90% websites)
```python
from scrapling.fetchers import Fetcher
p = Fetcher.get('https://target.com')
title = p.css('title::text').get()
emails = p.css('a[href^=mailto]::attr(href)').getall()
```

### Layer 2: Scrapling StealthyFetcher (Cloudflare bypass)
```python
from scrapling.fetchers import StealthyFetcher
p = StealthyFetcher.fetch('https://target.com', headless=True, solve_cloudflare=True)
```
Requires Playwright browsers: `patchright install`

### Layer 3: nodriver (undetected browser, CDP direct)
```python
import nodriver
browser = await nodriver.start(headless=False)
tab = await browser.get('https://target.com')
text = await tab.evaluate('document.body.innerText')
```

## Anti-Detection Deep Dive (Source Code Analysis)

### nodriver 0.50.3 — Pure CDP Stealth

Core principle: bypass chromedriver detection entirely by using CDP directly — no chromedriver binary process exists.

| Anti-detection technique | Implementation | Effectiveness |
|:------------------------|:---------------|:--------------|
| **No chromedriver** | Connects to Chrome via WebSocket CDP directly. `navigator.webdriver` returns `undefined` natively. | Bypasses #1 detector — most WAFs check chromedriver fingerprint first |
| **16 stealth startup flags** | `--no-first-run`, `--no-service-autorun`, `--no-default-browser-check`, `--homepage=about:blank`, `--no-pings`, `--password-store=basic`, `--disable-infobars`, `--disable-breakpad`, `--disable-dev-shm-usage`, `--disable-session-crashed-bubble`, `--disable-search-engine-choice-screen` | Eliminates all standard automation traces |
| **Temp user profile** | Each run creates a fresh `mkdtemp` profile dir with random prefix `uc_` | No cached fingerprints across sessions |
| **Async CDP transport** | WebSocket-based via `websockets>=14`, non-blocking, event-driven | 5-10x faster than Selenium |
| **Expert mode** | `--disable-site-isolation-trials` + open shadow DOM | Useful for crawling shadow-root content |
| **Real mouse dispatch** | Uses `cdp.input_.dispatch_mouse_event` with realistic coordinates | Bypasses event-based bot detection |
| **CDP connect over network** | `remote-debugging-host` + `remote-debugging-port` over network | Can attach to already-running Chrome instances |

Source architecture (`nodriver/core/config.py`):
```python
class Config:
    _default_browser_args = [
        "--remote-allow-origins=*", "--no-first-run",
        "--no-service-autorun", "--no-default-browser-check",
        "--homepage=about:blank", "--no-pings",
        "--password-store=basic", "--disable-infobars",
        "--disable-breakpad", "--disable-dev-shm-usage",
        "--disable-session-crashed-bubble",
        "--disable-search-engine-choice-screen",
    ]
```
`start()` signature: `async def start(config=None, *, user_data_dir=None, headless=False, browser_executable_path=None, browser_args=None, sandbox=True, lang="en-US", host=None, port=None, expert=None, **kwargs) -> Browser`

### scrapling 0.4.8 — Adaptive Stealth Engine (Source Code Analysis)

Three-layer adaptive architecture (`scrapling/fetchers/`):
```
requests.py     → Fetcher / AsyncFetcher       (Layer 1: curl_cffi + browserforge headers)
chrome.py       → DynamicFetcher / DynamicSession (Layer 2: Playwright standard)
stealth_chrome.py → StealthyFetcher             (Layer 3: patchright + Cloudflare solver)
```

#### Layer 1: Fetcher (curl_cffi + browserforge)
- Uses `curl_cffi` for TLS fingerprint impersonation
- **browserforge** generates matching Chrome 147 headers (User-Agent, Sec-CH-UA, Accept, etc.)
- Headers match current OS (auto-detected), device type (desktop)
- Fastest, works for ~90% of sites without JS rendering

#### Layer 2: DynamicFetcher (Playwright)
- Full Playwright rendering for JavaScript-heavy pages
- No stealth patches — falls through to Layer 3 when blocked

#### Layer 3: StealthyFetcher — The Heavy Lifter 🔥
Built on **patchright** (Playwright fork with built-in stealth).

| Technique | Implementation | Source Evidence |
|:----------|:---------------|:----------------|
| **patchright browser engine** | Playwright fork with Chromium source-level stealth patches | `from patchright.sync_api import sync_playwright` |
| **Cloudflare Turnstile auto-solver** | Detects challenge type → locates iframe → simulates mouse click at `(x+26, y+27)` with 100-200ms delay → waits → recursive retry | `_cloudflare_solver()` method, `_CF_PATTERN__ = re.compile(r"^https?://challenges\.cloudflare\.com/cdn-cgi/challenge-platform/.*")` |
| **browserforge fingerprint engine** | Generates genuine Chrome 147 headers matching current OS | `from browserforge.headers import HeaderGenerator; Browser(name="chrome", min_version=147, max_version=147)` |
| **Canvas noise** | Adds random noise to canvas operations | `hide_canvas` parameter |
| **WebRTC leak prevention** | Forces WebRTC to respect proxy settings | `block_webrtc` parameter |
| **DNS-over-HTTPS** | Routes DNS through Cloudflare DoH | `dns_over_https` parameter |
| **Google referer** | Automatically sets Google referer header (google_search=True by default) | `google_search=True` |
| **CDP connect to existing browser** | Attach to running Chrome via CDP URL | `cdp_url` parameter |
| **Real Chrome mode** | Launches real installed Chrome instead of Chromium binary | `real_chrome=True` |
| **Ad/tracker blocking** | Blocks ~3,500 known ad/tracking domains | `block_ads=True` + `ad_domains.py` |
| **Resource blocking** | Drops font/image/media/beacon/stylesheet requests | `disable_resources=True` |
| **Proxy rotation** | Rotates proxy per request; auto-detects proxy errors | `proxy_rotator` parameter |

**Cloudflare solving flow (source-precise):**
1. `_detect_cloudflare(content)` → returns type: `"non-interactive"`, `"interactive"`, or `"embedded"`
2. **non-interactive**: Just wait for "Just a moment..." to disappear
3. **interactive/embedded**: Find iframe matching `challenges.cloudflare.com/cdn-cgi/challenge-platform/` → get bounding box → `mouse.click(x+26..28, y+25..27, delay=100..200)` → wait for networkidle → check → recursive retry (up to 100 attempts × 100ms = 10s total)

### CloakBrowser — The New Frontier (2026)

Source-level Chromium patching — not JS injection, not Playwright patches. Modifies C++ fingerprint surfaces before compilation:
- WebGL renderer string → spoofed at C++ level
- Canvas fingerprint → patched in Chromium source
- `navigator` properties → hardcoded in browser binary

2026 benchmark: reCAPTCHA v3 score **0.9** (vs nodriver 0.3-0.7, undetected-chromedriver 0.3-0.5)

**Note:** Pre-built binaries only for Linux x64 and macOS arm64. Windows not yet supported.
Repos: `CloakHQ/cloakbrowser` + `CloakHQ/chromium-stealth-builds`

## Pipeline-Specific Applications (BLIIT context)

### Pipeline 1: JoinF (富通) Search — Cloudflare Bypass
Replace current Selenium + CDP approach:
```python
from scrapling.fetchers import StealthyFetcher
p = StealthyFetcher.fetch(
    'https://data.joinf.com/api/bs/searchBusiness',
    headless=True,
    solve_cloudflare=True,
    real_chrome=True,
)
```
Existing pain: Cloudflare Turnstile requires manual handling
Fix: `solve_cloudflare=True` auto-detects type + simulates click + waits

### Pipeline 2: WhatsApp Web Sending
Use nodriver to connect to existing CDP session:
```python
import nodriver
# Attach to running Chrome with WhatsApp Web already authenticated
browser = await nodriver.start(
    user_data_dir="C:/path/to/ChromeProfile",
    headless=False,
)
```
Faster than Selenium, no chromedriver detection risk.

### Pipeline 3: Google Maps Customer Search
Use scrapling with `real_chrome=True` to avoid Google detection:
```python
from scrapling.fetchers import StealthyFetcher
p = StealthyFetcher.fetch(
    'https://www.google.com/maps/search/industrial+automation+South+Africa',
    headless=False,
    real_chrome=True,
    solve_cloudflare=True,
    page_action=lambda page: page.wait_for_selector('[role="feed"]'),
)
```

## Anti-Detection Principles

1. **CDP direct communication** — nodriver talks CDP directly, no chromedriver binary leak
2. **Fresh browser profile each run** — nodriver creates temp profile, cleans up on exit
3. **Disable isolation features** — `--disable-features=IsolateOrigins,site-per-process`
4. **Simulate real mouse** — nodriver uses CDP `dispatch_mouse_event` with realistic coordinates
5. **Residential proxies** — datacenter IPs will fail even with stealth (nodriver docs warn this)
6. **Use patchright, not Playwright** — Scrapling uses patchright internally; when building custom browser code, import from patchright not playwright
7. **solve_cloudflare=True is always worth trying** — even if unsure whether the site has Cloudflare, the overhead is minimal

## Pitfalls

- ❌ Google HTML scraper libraries break frequently (Google changes CSS class names)
- ❌ undetected-chromedriver is slow on Windows (downloads chromedriver each startup)
- ❌ `pip install "scrapling[fetchers]"` downloads Playwright (~36MB) — use `scrapling[all]` if also want CLI
- ❌ curl_cffi impersonate strings are version-specific (use `impersonate='chrome'` not `'chrome130'`)
- ❌ nodriver core.py is a namespace package — always import from `nodriver` top level
- ❌ nodriver v0.50.3 **cannot** attach to already-running CDP sessions (e.g. WhatsApp's 9223). Use Playwright's `connect_over_cdp` for that scenario
- ❌ Scrapling StealthyFetcher configure() only accepts parser keywords
- ❌ CloakBrowser Windows support is missing — don't attempt on this machine

## Key Learnings from GitHub Top Projects

10 patterns extracted from geekcomputers/Python (35.1k⭐), DhanushNehru/Python-Scripts, avinashkranjan/Amazing-Python-Scripts:

1. **Cross-platform check**: `os.name == "posix"` vs `"nt"` for ping/commands
2. **JSON config-driven**: Separate rules from code (arrangeit.py pattern)
3. **Environment variable config**: `os.getenv("my_config")` for paths
4. **Schedule-based watchdog**: `import schedule; sc.every(50).seconds.do(job)`
5. **Admin privilege elevation**: `ctypes.windll.shell32.IsUserAnAdmin()`
6. **subprocess.call return codes**: Simple ping/health checks
7. **Popen+communicate**: When output capture needed
8. **EAFP exception scanning**: try/except for port scanning
9. **Dict + zip formatted output**: Cleaner than many print() calls
10. **Thread for GUI**: `Thread(target=download).start()` prevents UI freeze
