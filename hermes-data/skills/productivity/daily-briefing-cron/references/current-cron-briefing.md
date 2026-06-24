# Current Daily Briefing Cron Job

This is the live cron job for Kali's daily financial briefing. Refer to this when modifying or troubleshooting.

## Job Details

- **Job ID**: `01837ee19638`
- **Name**: 每日财经简报+基金推荐+财经问答
- **Schedule**: `30 8 * * 1-5` (Mon-Fri 8:30 AM Beijing time)
- **Delivery**: `telegram`
- **State**: active
- **Model**: `deepseek-v4-flash` via `ollama-cloud`
- **Mode**: **agent** (no_agent=false) — AI searches data, analyzes, generates PDF

## Current Workflow (Agent Mode)

1. **Discover** — web_search for today's A-share market, global markets, news, funds
2. **Collect** — browser to authoritative sources for real-time data:
   - 东方财富行情中心: https://quote.eastmoney.com/
   - 华尔街见闻: https://wallstreetcn.com/
   - Yahoo Finance US indices: https://finance.yahoo.com/quote/%5EGSPC/
3. **Analyze** — Cross-reference data, identify causal links, build thesis
4. **Generate PDF** — fpdf2, 6-8 pages, Chinese font (msyh.ttc or china-ss)
5. **Save** — `C:\Users\Admin\Desktop\XiaoMa_Financial_Daily_YYYYMMDD.pdf`
6. **Deliver** — telegram (auto-delivers PDF file)

## Prompt Structure

```
Generate today's XiaoMa Financial Daily PDF:
1. web_search for A-share indices, market news, fund recommendations
2. web_search for global markets (US/HK/oil/FX)
3. Cross-reference and analyze
4. Generate 6-8 page PDF with fpdf2
5. Save to Desktop as XiaoMa_Financial_Daily_YYYYMMDD.pdf
```

## Page Structure (current)

| Page | Section | Content |
|------|---------|---------|
| Cover | — | XiaoMa Financial Daily + date + issue # |
| 1 | 全球大盘纵览 | A-share + US + HK + FX + Oil + Commodities |
| 2 | 热点板块与全球要闻 | Top movers + global headlines + risk monitor |
| 3 | 策略分析 | Core/Satellite/Defensive framework + valuation |
| 4 | 基金推荐与数据分析 | Recommended fund + 4-dimension analysis |
| 5-6 | 投资小课堂 | 6 quiz questions with full explanations |
| 7 | 今日总结 | Summary table + next issue preview |

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

### What went well (2026-05-29 session)
- `quote.eastmoney.com/` — fast load, A-share indices visible immediately
- `wallstreetcn.com/` — stable, clean snapshots, 20+ headlines with timestamps
- Yahoo Finance S&P 500 (`^GSPC`) and Dow (`^DJI`) — clean load, full data
- Yahoo Finance homepage — US futures ticker bar

### What failed (and how to work around)
- **NASDAQ `^IXIC` on Yahoo Finance** → alert overlay on first load. Fix: `browser_click(@e1)` to dismiss.
- `fund.eastmoney.com/data/fundranking.html` → times out. Use homepage or web_search.

## Key User Preferences

- **Delivery format**: PDF document (not inline text). User rejected long WeChat messages.
- **Filename**: `XiaoMa_Financial_Daily_YYYYMMDD.pdf` on Desktop (date suffix for agent mode)
- **Model**: `deepseek-v4-flash` / `ollama-cloud` for cron (cold-start sessions timeout with slow models)
- Only weekdays (Mon-Fri) — no weekends
- Fund rec is **mandatory**, not optional — must include risk disclaimer
- Quiz must be **investment-practical**, not general finance
- Real-time data via browser (not web_search alone)
- Chinese language throughout
- **Delivery**: telegram (agent mode) or local (script mode)
- See `references/yahoo-finance-extraction.md` for US market extraction guide

## Mode Switch History

| Date | Change | Reason |
|------|--------|--------|
| 2026-05-29 | Created no_agent script mode | Zero-token automated delivery |
| 2026-06-05 | Changed deliver to telegram (still script) | User wanted auto-delivery |
| 2026-06-24 | **Switched to agent mode** | User said "重启小马财经日报" — wanted AI analysis |
