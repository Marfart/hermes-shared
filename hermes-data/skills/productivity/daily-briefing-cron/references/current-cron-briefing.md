# Current Daily Briefing Cron Job

This is the live cron job for Kali's daily financial briefing. Refer to this when modifying or troubleshooting.

## Job Details

- **Job ID**: `01837ee19638`
- **Name**: 每日财经简报+基金推荐+财经问答
- **Schedule**: `30 8 * * 1-5` (Mon-Fri 8:30 AM Beijing time)
- **Delivery**: WeChat (auto)
- **State**: active
- **Model**: default (provider pinned at creation)

## Prompt Structure (5 steps)

1. **Discover** — web_search for today's news, markets, funds (Chinese queries)
2. **Collect** — **browser** to authoritative sources for real-time data:
   - 东方财富行情中心: https://quote.eastmoney.com/
   - 华尔街见闻: https://wallstreetcn.com/
   - 天天基金网热门排行: https://fund.eastmoney.com/
   - Yahoo Finance US indices: https://finance.yahoo.com/quote/%5EGSPC/
3. **Format** — Market overview (📊) + top news (📰) + hot topics (🔥)
4. **Fund recommendation** (💎) — Today's best pick with analysis:
   - Fund name + code
   - 3 reasons based on today's market/policy/valuation
   - Risk disclaimer ⚠️
   - Valuation level, performance trend, portfolio alignment
5. **Investment quiz** (🧠) — Multiple choice, rotating topics:
   - Mon: Fund basics | Tue: Strategy | Wed: Risk mgmt
   - Thu: Valuation | Fri: Asset allocation
   - Includes: topic label, question + 4 choices, correct answer + explanation, 投资金句

## Known data-gathering failure modes

### Browser timeouts on specific pages
- `zs399006.html` (创业板指) → consistently times out. Use web_search fallback instead.
- `data/fundranking.html` (基金排行) → heavy JS, times out. Use `fund.eastmoney.com/` homepage or web_search.
- `hk/HSI.html` (恒生指数) → 404 / dead link. Use web_search for HSI data.

### web_extract is completely unavailable
The `web_extract` tool fails with "DuckDuckGo is a search-only backend". **Never attempt web_extract**.

### Best fallback query per data gap
- **US markets**: `"今日美股市场行情快报 2026年MM月DD日"`
- **A-share recap**: `"A股收评 2026年MM月DD日"` → 金融界/腾讯新闻 with exact levels
- **创业板**: `"创业板指 399006 2026年MM月DD日 收盘"`
- **恒生**: `"恒生指数 2026年MM月DD日 收盘 涨跌"`
- **Funds**: `"科技基金 ETF 推荐 2026年MM月"`

### What went well
- `quote.eastmoney.com/` — fast load, A-share indices visible immediately
- `wallstreetcn.com/` — stable, clean snapshots, 20+ headlines with timestamps
- `web_search` for A-share/US recap queries — returns exact structured data
- **NEW: Yahoo Finance S&P 500 (`^GSPC`)** — full closing data + heatmap + component % changes. Clean load, no overlay.
- **NEW: Yahoo Finance Dow (`^DJI`)** — same rich data. Clean load, no overlay.
- **NEW: Yahoo Finance homepage** — US futures ticker bar (S&P Futures -0.35%, Dow Futures +0.03%, Nasdaq Futures -0.48%, VIX 16.06 +1.84%, Gold $4,475, Brent $97.15, Bitcoin $63,121 -5.55%)
- **NEW: eastmoney SPY page** (`quote.eastmoney.com/us/SPY.html`) — shows a different set of global indices than the main quote page, useful for cross-referencing

### What failed (and how to work around)
- **NASDAQ `^IXIC` on Yahoo Finance** → alert overlay blocking the page on first load. Fix: `browser_click(@e1)` to dismiss the modal.
- `fund.eastmoney.com/data/fundranking.html` → times out (expected, JS-heavy). Use homepage or web_search instead.

### Cross-referencing strategy
When browser returns partial data and web_search fills gaps, cross-reference to ensure date/point alignment:
- A-share close: from `quote.eastmoney.com/` snapshot
- US close: from Yahoo Finance (`^GSPC` / `^DJI`)
- HK close: from Sohu article via web_search
- 创业板: filled from web_search (browser failed)
- Fund rec: qualitative analysis based on market trends + sector focus

## Key User Preferences

- **Delivery format**: PDF document (not inline text). User rejected long WeChat messages.
- **Filename**: `小马财经日报.pdf` on Desktop (no date suffix, no English prefix)
- **Model**: Prefer `deepseek-v4-flash` / `ollama-cloud` for cron (cold-start sessions timeout with slow models)
- Only weekdays (Mon-Fri) — no weekends
- Fund rec is **mandatory**, not optional — must include risk disclaimer
- Quiz must be **investment-practical**, not general finance
- Real-time data via browser (not web_search alone)
- Chinese language throughout
- WeChat delivery (auto)
- See `references/yahoo-finance-extraction.md` for US market extraction guide