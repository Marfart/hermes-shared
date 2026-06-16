# Web Scraping Ecosystem 2026 — Research Notes

> Compiled 2026-06-03 from awesome-web-scraping-2026 and repository deep-dives.

## The Stack

```
┌─────────────────────────────────────────────────┐
│                 AI-Powered Layer                │
│  Crawl4AI(50k⭐) Firecrawl(70k⭐) ScrapeGraphAI │
│  Describe → get structured data. No selectors.  │
├─────────────────────────────────────────────────┤
│              Anti-Detection Layer               │
│  Scrapling(20k⭐) undetected-chromedriver(10k⭐) │
│  curl_cffi(3k⭐) puppeteer-extra-stealth(12k⭐)  │
│  Camoufox(5k⭐) playwright-stealth(1k⭐)         │
├─────────────────────────────────────────────────┤
│            Browser Automation Layer             │
│  Playwright(68k⭐) Puppeteer(89k⭐) Selenium(31k)│
│  Crawlee Python(5k⭐) Playwright Python(12k⭐)   │
├─────────────────────────────────────────────────┤
│          HTTP Client / Parser Layer             │
│  httpx(13k⭐) curl_cffi requests-html(13k⭐)     │
│  Scrapling parser (2ms parsing 5000 elements)   │
├─────────────────────────────────────────────────┤
│            Anti-Scraping Defenses               │
│  Cloudflare Turnstile ← hardest to bypass       │
│  DataDome / Imperva / Distill Network           │
│  Browser fingerprinting + behavior analysis     │
│  Rate limiting / IP reputation scoring          │
└─────────────────────────────────────────────────┘
```

## Anti-Detection Bypass Matrix

| Protection | Requests/curl | Playwright | UC-Driver | Scrapling | Scrapling+Proxy |
|-----------|:---:|:---:|:---:|:---:|:---:|
| Simple rate limit | ✅ | ✅ | ✅ | ✅ | ✅ |
| User-agent check | ✅ | ✅ | ✅ | ✅ | ✅ |
| JS challenge | ❌ | ✅ | ✅ | ✅ | ✅ |
| Cloudflare Turnstile | ❌ | ❌ | ~50% | ✅ | ✅✅ |
| DataDome | ❌ | ❌ | ~60% | ~70% | ✅(with HyperSolutions) |
| Browser fingerprint | ❌ | 🟡 (detectable) | ✅ | ✅ | ✅ |
| IP reputation | ❌ | ❌ | ❌ | ❌ | ✅ (needs residential proxy) |

## Scrapling (20k⭐) — The Recommended Anti-Detection Library

**Install:** `pip install "scrapling[all]" && scrapling install`

### Key Classes

| Class | Purpose |
|-------|---------|
| `Fetcher` | Sync HTTP with TLS impersonation |
| `AsyncFetcher` | Async HTTP version |
| `StealthyFetcher` | Headless browser with fingerprint spoofing + CF bypass |
| `DynamicFetcher` | Full browser with JS execution |
| `AsyncStealthySession` | Concurrency via browser tab pool (`max_pages=N`) |
| `Selector` | Standalone parser for pre-fetched HTML |
| `Spider` | Full crawl framework with pause/resume |

### Common Patterns

```python
# Pattern 1: Stealth page fetch with Cloudflare bypass
p = StealthyFetcher.fetch(url, headless=True, solve_cloudflare=True, network_idle=True)
emails = p.find_by_text(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', regex=True)

# Pattern 2: Async batch with browser pool
async with AsyncStealthySession(max_pages=4) as session:
    tasks = [session.fetch(u) for u in urls]
    results = await asyncio.gather(*tasks)

# Pattern 3: Adaptive parsing (survives CSS changes)
page = StealthyFetcher.fetch(url, headless=True)
products = page.css('.product', auto_save=True)   # learn current structure
products = page.css('.product', adaptive=True)     # re-find if page changed

# Pattern 4: Spider with proxy rotation
class MySpider(Spider):
    name = "demo"
    start_urls = ["https://example.com/"]
    proxy_config = {"rotation": "round-robin", "list": [...]}

# Pattern 5: CLI one-liner (no coding)
scrapling extract stealthy-fetch 'https://nopecha.com/demo/cloudflare' data.md
```

## LinkedIn Data: What's Possible Without Login

| Data Point | Without Login | With Login (scraping) | Official API |
|-----------|:---:|:---:|:---:|
| Company page | 🟡 Limited (Google-cached) | ✅ Full | ✅ (restricted) |
| Employee names | ❌ | ✅ | ❌ |
| Contact emails | ❌ | 🟡 (can extract) | ❌ |
| Job listings | ✅ Public (Google indexed) | ✅ | ✅ |
| Company description | ✅ Public | ✅ | ✅ |
| Industry/category | ✅ Public | ✅ | ✅ |

**Best approach:** Google Dorking (`site:linkedin.com/company "keyword" "country"`) then visit the company's OWN website for email/phone.

## Proxy Services Comparison

| Service | Residential IPs | Price Starts | Free Tier |
|---------|----------------|-------------|-----------|
| Bright Data | 72M+ | Enterprise | Trial |
| Oxylabs | 100M+ | Enterprise | Trial |
| IPRoyal | ~ | $1.75/GB | — |
| Evomi | 195+ countries | $0.49/GB | — |
| BirdProxies | 195+ countries | Competitive | — |

## CAPTCHA Solving

| Service | Price per 1000 | Type |
|---------|---------------|------|
| 2Captcha | $1-3 | Human-powered |
| Anti-Captcha | $1-2 | Human-powered |
| CapSolver | $0.80 | AI-powered |
| HyperSolutions | API | Enterprise anti-bot tokens (Akamai/DataDome/Kasada) |

## Related Repositories

- `D4Vinci/Scrapling` (20k⭐) — Full-stack anti-detection scraping
- `ultrafunkamsterdam/undetected-chromedriver` (10k⭐) — Selenium patcher
- `ScrapeGraphAI/Scrapegraph-ai` (18k⭐) — AI-powered, describe-and-extract
- `unclecode/crawl4ai` (50k⭐) — LLM-friendly markdown crawler
- `apify/crawlee` (15k⭐ JS / 5k⭐ Python) — Production scraping framework
- `spinov001-art/awesome-web-scraping-2026` — Comprehensive tool index