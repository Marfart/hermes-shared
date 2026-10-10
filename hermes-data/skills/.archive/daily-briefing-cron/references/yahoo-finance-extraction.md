# Yahoo Finance Data Extraction for Daily Briefings

Quick reference for extracting US market data from Yahoo Finance pages during the daily briefing cron job.

## S&P 500 (`^GSPC`) → `https://finance.yahoo.com/quote/%5EGSPC/`

**Loads cleanly** — no alert overlay.

### What's visible in the snapshot:
- **Price**: `7,553.68` + `-56.10` + `(-0.74%)` + `"At close: 4:46:01 PM EDT"`
- **Previous Close**: `7,609.78`
- **Open**: `7,605.31`
- **Volume**: `3,413,910,000`
- **Day's Range**: `7,551.22 - 7,605.35`
- **52 Week Range**: `5,921.20 - 7,620.90`
- **Avg. Volume**: `5,512,416,507`
- **Heatmap**: Top components by daily % — e.g. NVDA -3.62%, AAPL -1.57%, MSFT -3.17%, AMD +4.02%, MU +1.45%

### Extraction via browser_console
```javascript
// Gets the structured data at a glance
JSON.stringify({
  price: document.querySelector('[class*="price"]')?.textContent,
  prevClose: [...document.querySelectorAll('li')]
    .find(l => l.textContent.includes('Previous Close'))
    ?.textContent?.replace('Previous Close', '')?.trim()
});
```

## Dow Jones Industrial Average (`^DJI`) → `https://finance.yahoo.com/quote/%5EDJI/`

**Loads cleanly** — no alert overlay.

### What's visible in the snapshot:
- **Price**: `50,687.07` + `-620.72` + `(-1.21%)` + `"At close: 4:46:33 PM EDT"`
- **Previous Close**: `51,307.79`
- **Open**: `51,220.92`
- **Volume**: `546,852,298`
- **Day's Range**: `50,687.07 - 51,220.92`
- **52 Week Range**: `41,981.14 - 51,369.61`
- **Heatmap**: Dow components — e.g. IBM -7.17%, CRM -5.09%, HD +0.47%

## NASDAQ Composite (`^IXIC`) → `https://finance.yahoo.com/quote/%5EIXIC/`

**⚠️ Alert overlay blocks first load**. The page shows only:
```
- alertdialog
  - button "Close" [ref=e1]
  - heading "..."
```

**Workaround**: Call `browser_click(@e1)` to dismiss the dialog, then `browser_snapshot()` to see the real data.

## Yahoo Finance Homepage → `https://finance.yahoo.com/`

Shows the **futures ticker bar** at the top:
| Item | Example data |
|------|-------------|
| S&P Futures | `7,545.00` `-26.75 -0.35%` |
| Dow Futures | `50,822.00` `+19.00 +0.04%` |
| Nasdaq Futures | `30,487.50` `-145.75 -0.48%` |
| Russell 2000 Futures | `2,899.30` `+3.90 +0.13%` |
| VIX | `16.06` `+0.29 +1.84%` |
| Gold | `4,475.10` `+8.20 +0.18%` |
| Bitcoin USD | `63,121.66` `-3,711.17 -5.55%` |
| Brent Crude Oil | `97.15` `-0.66 -0.67%` |

## Data flow for cron (08:30 CST)

| What we need | Where to get it | Status |
|---|---|---|
| A-share prev close | `quote.eastmoney.com/` (snapshot) | ✅ Previous day's close |
| US market close | Yahoo Finance `^GSPC` / `^DJI` | ✅ Previous day's close (US-format dates) |
| US futures (current) | Yahoo Finance homepage ticker | ✅ Real-time pre-market |
| HK/Hang Seng | `web_search` fallback | ✅ Previous day |
| Hot news | `wallstreetcn.com/` | ✅ Current day |

## Key insight from live sessions

**If you need US closing data** (not just futures), Yahoo Finance is more reliable than trying to get it from eastmoney's delayed US pages. The heatmap feature also gives you stock-level granularity that eastmoney doesn't offer in its first snapshot.

**Note on data delay**: Yahoo Finance labels its data as "Delayed Quote" — typically ~15 minutes for US indices. For "previous close" context at 08:30 CST, this is perfectly fine since the US market closed 6+ hours ago.