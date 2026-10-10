# Data-Gathering Fallback Matrix

Real-world reliability data for financial data sources in the Hermes cron environment. Collected from live session failures.

## ⚠️ Key constraint: web_extract is unusable

The `web_extract` tool fails with `"DuckDuckGo (ddgs) is a search-only backend"` — the environment has no configured extraction backend (Firecrawl, Tavily, Exa, or Parallel). **Do not attempt web_extract.** Use only:
- `browser_navigate + browser_snapshot` for live page content
- `web_search` for structural/high-level data
- `browser_console` for JS extraction from rendered pages

## Source reliability table

| Source URL | Tool | Reliability | Notes |
|---|---|---|---|
| `quote.eastmoney.com/` | browser | ✅ High | Fast load, key A-share indices in first snapshot |
| `eastmoney.com/` | browser | ✅ High | Global index ticker bar works — shows 20+ indices |
| `wallstreetcn.com/` | browser | ✅ High | Fast, clean snapshots, 20+ headlines with timestamps |
| `fund.eastmoney.com/` | browser | ✅ Medium | Homepage loads; fund ranking page times out |
| `fund.eastmoney.com/data/fundranking.html` | browser | ❌ Low | Heavy JS → times out |
| `quote.eastmoney.com/zs399006.html` | browser | ❌ Times out | 创业板指 page too heavy |
| `quote.eastmoney.com/hk/HSI.html` | browser | ❌ 404 | Broken link on eastmoney |
| `10jqka.com.cn/` | browser | ✅ Untested | Alternative to eastmoney |
| `finance.yahoo.com/quote/%5EGSPC/` | browser | ✅ High | S&P 500: full closing data visible (Previous Close, Open, Day's Range, 52W Range, Volume, Heatmap). NO alert overlay. |
| `finance.yahoo.com/quote/%5EDJI/` | browser | ✅ High | Dow Jones: full closing data. NO alert overlay. |
| `finance.yahoo.com/quote/%5EIXIC/` | browser | ❌ Alert overlay | NASDAQ: blocking modal needs `browser_click(@e1)` to dismiss first. Loads fine after. |
| `finance.yahoo.com/` (home) | browser | ✅ High | Futures ticker bar at top: S&P Futures, Dow Futures, Nasdaq Futures, Russell 2000, VIX, Gold, Brent, Bitcoin. Fast load. |

## Using Yahoo Finance for US market data

### Why Yahoo Finance works well
- **S&P 500 (`^GSPC`)**: Loads cleanly. Closing data visible immediately: price, change, % change, Previous Close, Open, Day's Range, 52-Week Range, Volume. Also includes a heatmap showing top components with their daily % changes (e.g. NVDA -3.62%, AAPL -1.57%, MSFT -3.17%, AMD +4.02%).
- **Dow Jones (`^DJI`)**: Same rich data as S&P 500. Heatmap shows Dow components (e.g. IBM -7.17%, CRM -5.09%, HD +0.47%).
- **NASDAQ (`^IXIC`)**: **⚠️ Blocks on first load** — an alert/modal overlay appears. Dismiss it with `browser_click(@e1)` and the page loads normally.
- **Yahoo Finance homepage**: Shows the US market futures ticker bar at the top — S&P Futures, Dow Futures, Nasdaq Futures, Russell 2000 Futures, VIX, Gold, Brent Crude Oil, Bitcoin. All with intraday levels and % changes.

### Extraction pattern
```javascript
// Run via browser_console to extract structured data
JSON.stringify({
  price: document.querySelector('[data-testid="qsp-price"]')?.textContent,
  change: document.querySelector('[data-testid="qsp-price-change"]')?.textContent,
  pct: document.querySelector('[data-testid="qsp-price-change-percent"]')?.textContent,
  prevClose: [...document.querySelectorAll('li')].find(l => l.textContent.includes('Previous Close'))?.textContent,
  open: [...document.querySelectorAll('li')].find(l => l.textContent.includes('Open'))?.textContent
});
```

### Important timing note
Yahoo Finance shows **delayed quotes** (labeled "Delayed Quote" or "SNP - Delayed Quote"). For the S&P 500 and Dow, this is typically ~15 minutes delayed, not real-time. For daily closing data (previous close context), this is fine.

## Proven fallback search queries

When browser pages fail, these web_search queries consistently return usable structured data:

### US Markets (best single-query source)
```
今日美股市场行情快报 2026年MM月DD日
```
Returns from yahuinews.com.cn: exact closing levels for 道琼斯/标普500/纳斯达克 + sector moves + catalysts.

### A-share daily recap
```
A股收评 2026年MM月DD日
```
Returns from 金融界(jrj.com.cn) or 腾讯新闻: exact Shanghai/ Shenzhen/ChiNext levels + volume + sector movers.

### ChiNext / 创业板指
```
创业板指 399006 2026年MM月DD日 收盘
```
Returns MSN/Investing.com data with point value and % change.

### 恒生指数
```
恒生指数 2026年MM月DD日 收盘 涨跌
```
Returns Sohu news articles or Investing.com with exact HSI index levels.

### Fund recommendations
```
科技基金 ETF 推荐 2026年MM月
```
Returns qualitative analysis and fund lists. Not real-time rankings, but good for identifying current themes.

### Recent A-share performance context
```
沪深300 sh.000300 2026年MM月DD日 收盘
```
Useful for getting specific index closing levels when main pages time out.

## What to do when both browser AND search fail

If both tools yield no usable data for a particular section, include a qualifying note in the briefing:
- "Based on recent trends (prior day close: ...)"
- Reference the user's known portfolio/watchlist
- Provide qualitative macro analysis instead of exact numbers
- **Never fabricate index levels** — say "data temporarily unavailable"

## Data freshness notes

When cross-referencing:
- A-share market: closes at 15:00 CST → data available immediately after
- US market: closes ~16:00 ET (next day 04:00-06:00 CST) → use previous day's close for early-morning briefings
- Hong Kong: closes at 16:00 CST
- Fund NAVs: published ~18:00-20:00 CST (delayed from market close)

The cron fires at 08:30 CST, so:
- A-share data: previous day's close (current)
- US data: previous US trading day (often the same calendar day)
- HK data: previous day's close
- Fund data: day-before's NAV (may still be yesterday's)