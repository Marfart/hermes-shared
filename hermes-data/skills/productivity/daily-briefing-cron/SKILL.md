---
name: daily-briefing-cron
description: Set up daily cron jobs that deliver structured briefings with news, analysis, and educational content to the user via WeChat
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [windows, linux, macos]
metadata:
  hermes:
    tags: [cron, briefing, finance, education, daily-report, wechat]
    related_skills: [cronjob]
---

# Daily Cron Briefing Skill

Set up and maintain **daily scheduled briefings** delivered via WeChat (or other platforms), with multiple content sections including news, analysis, and educational components.

## When to use

- User asks to receive daily news/information at a fixed time
- User wants learning or quizzing built into a daily briefing
- User wants periodic market/finance/investment updates
- User asks about "what can you do on a schedule"

## Key architecture

A cron-driven briefing is built from **two layers**:

1. **Cron job** (via `cronjob` tool) — the runtime scheduler
2. **Optionally: a supporting skill** — reusable format/prompt patterns

## Cron job creation guide

### Schedule syntax (common patterns)

| Intent | Cron expression |
|--------|----------------|
| Weekdays 8:30 AM | `30 8 * * 1-5` |
| Every day 8:30 AM | `30 8 * * *` |
| Mon-Fri 7:00 PM | `0 19 * * 1-5` |
| Every Monday 9:00 AM | `0 9 * * 1` |

**Important**: `1-5` = Monday to Friday (1=Monday, 5=Friday). Saturday=6, Sunday=0 or 7.

### Delivery target

- Omit `deliver` parameter → auto-delivers to the current conversation (WeChat/Telegram/etc.)
- Set explicitly only when user asks to send somewhere else

### Prompt structure

A good briefing prompt has **discover → collect → format → bonus** flow:

```
## Step 1: Discover
Use web_search with Chinese-language queries to find today's content
(e.g. "今日财经新闻 早报", "今日基金推荐 热门基金")

## Step 2: Collect
Open browser to authoritative sources for detail:
- Source 1 (URL)
- Source 2 (URL)

## Step 3: Format the briefing
Output sections with emoji headers:
1. 📊 **Market Overview**
2. 📰 **Top News** — 3-5 bullet items
3. 🔥 **Hot Topic** — 1-2 current focus areas

## Step 4: Core analysis — Fund/Asset recommendation (if applicable)

When the briefing includes investment picks, use this detailed format:

💎 **今日推荐基金**
**基金名称：** [code + name, e.g. 110011 易方达中小盘混合]
**推荐理由：**
- [Reason based on today's market hotspots]
- [Reason based on recent performance / policy tailwinds]
- [Risk disclaimer]

**分析要点：**
- Current valuation level (overvalued / undervalued / fair)
- Recent performance trend
- Does the portfolio's holdings align with today's market focus?

**CRITICAL**: Every fund recommendation MUST include a risk disclaimer. Never present picks as guaranteed. Base recommendations on real-time market data obtained via browser navigation to financial sites (东方财富, 天天基金网, 华尔街见闻), NOT on stale web_search results alone.

## Step 5: Educational section (investment-focused quiz)

The quiz MUST be about **practical investing skills**, not general finance trivia. Rotate through these topics daily:

| Day | Topic |
|-----|-------|
| Mon | Fund basics (index vs ETF vs active managed) |
| Tue | Investment strategy (DCA, grid trading, value investing) |
| Wed | Risk management (position sizing, stop-loss, diversification) |
| Thu | Valuation metrics (PE, PB, ROE, dividend yield) |
| Fri | Asset allocation (stock/bond balance, rebalancing) |
| Sat | Technical analysis basics (candlesticks, MA, MACD) — only if weekend enabled |
| Sun | Behavioral finance (FOMO, anchoring, loss aversion) — only if weekend enabled |

Format:

🧠 **今日投资小课堂**

📌 **知识点：** [One-line summary of the core concept]

**题目：** [Question]
A. [Option]
B. [Option]
C. [Option]
D. [Option]

**正确答案：** [Letter]
**解析：** [Detailed explanation — why right answers are right, why wrong ones are wrong, and real-world investing application]

**💡 今日投资金句：** [One memorable investing quote or principle]
```

## Session 2026-05-29 corrections (consolidated)

### Global sources are REQUIRED, not optional

This user explicitly rejected a China-only data set (frustration: "你的来源不够好，全球知名的财经要收集"). Every edition MUST include:
- **Cover page**: list BOTH global and Chinese data sources
- **Section 1 heading**: "全球大盘纵览" (not just "大盘概览"), covering:
  - A-share indices (Shanghai/Shenzhen/ChiNext/Beijing 50)
  - US indices (S&P 500 / Nasdaq / Dow — noting all-time highs)
  - Hong Kong / HSI + southbound capital flows
  - Crude oil (WTI) + macro driver analysis
  - FX (USD/CNY)
  - Commodities (gold, copper, aluminum, agriculture)
  - Cross-market linkages
- **Section 2**: Global news must include at least 3 non-China items (e.g. US GDP, US-Iran talks, Snowflake earnings, European politics)

### Fund recommendation section is MANDATORY, not optional

This user explicitly noticed its absence (frustration: "每日最推荐基金以及原因数据分析这一个板块没做"). The section structure:

**Section 4 — 基金推荐与数据分析** (inserted between Strategy and Quiz):

```
📌 Cover box with fund name + code + type + performance stats
   Font: 12pt bold, orange border, inside a rect(12, y, 186, 38)

✅ 逻辑一：与今日最强板块高度吻合
   [Explain why fund's holdings match today's top sector]

✅ 逻辑二：全球宏观环境持续利好
   [2-3 macro/policy/geopolitical drivers supporting the sector]

✅ 逻辑三：基金经理业绩验证
   [Recent performance data + why the fund manager's timing was good]

📊 行业数据分析
   - 供给端: supply constraints, capacity limits
   - 库存端: inventory trends, exchange stock levels
   - 需求端: downstream demand drivers
   - 成本端: raw material cost dynamics

📈 估值分析
   [Sector PE range, historical percentile, forward outlook]

⚠️ 风险提示
   [Volatility warning, potential reversal catalysts, position-sizing advice]

免责声明
```

### Font size correction (user: "文件中文字可以大一点")

- Cover title: 32pt bold
- Section headings: 16pt bold
- Sub-headings: 11pt bold
- Body text: **9pt** (was 8pt — user said too small)
- Quiz explanations: 8pt
- Footer/disclaimer: 7pt

### Layout overflow fix (user: "有些超出页面了")

The recurring `multi_cell` overflow in the quiz options section is caused by passing a hardcoded width (e.g. `W-8`) when the current x position makes the remaining space narrower than that value. The SAFE pattern:

```python
self.set_x(left_margin + indent)
self.multi_cell(0, h, txt)  # Always w=0 after resetting x
```

`multi_cell(0, ...)` auto-calculates remaining width from current x to right margin. This is 100% reliable. Hardcoded widths like `W-8` or `W-6` WILL overflow when the x position changes.

### Wake-up Cron Pattern (Wake the Agent, Not the User)

**Core architecture**: The wake-up cron's ONLY job is to send a signal to the messaging platform. The agent (小马) is **passive** — it cannot "see" cron output, cannot receive messages from other sessions, and cannot wake itself up. The user must interact with the chat for the agent session to activate.

**The correct flow**:

```
cron (no_agent) → sends 🌅/🌆 to Telegram → user sees it → user replies (1 char) → agent wakes → does 35min work → delivers result
```

**Key principles:**
- **Cron is NOT "the agent on the computer"** — cron launches an independent session with no memory of ongoing conversations. It cannot message the current agent session.
- **The agent is passive** — only user messages wake it. No system notification, no Windows popup, no console output can wake it.
- **The user's cost is ~0.5 seconds** — reply with one emoji/character to trigger the agent.
- **The agent (当前会话的小马) does ALL the real work** — deep reading, note-taking, cross-domain thinking, and output generation.
- **Exception**: For financial briefings, the cron itself can run in agent mode (`no_agent=false`) that generates and delivers the PDF directly. This is preferred when the user wants the briefing without user interaction.

### Wake-up script template (no_agent=True)

The `print("🌅")` approach only works when `deliver=telegram` — Hermes gateway reads stdout and delivers it. But this session revealed a better approach: **use Telegram Bot API directly**, so the script works independently and can be tested/debugged without the cron delivery layer.

The deployed script lives at `scripts/wake_up_xiaoma.py` under this skill. Key pattern:

```python
# Read credentials from .env
TELEGRAM_BOT_TOKEN=...   # from ~/AppData/Local/hermes/.env
TELEGRAM_HOME_CHANNEL=... # from ~/AppData/Local/hermes/.env

# Send via Telegram Bot API
url = f"https://api.telegram.org/bot{token}/sendMessage"
data = urllib.parse.urlencode({'chat_id': chat_id, 'text': "🌅"}).encode()
req = urllib.request.Request(url, data=data, method='POST')
resp = urllib.request.urlopen(req, timeout=10)
```

**Always use `deliver=local`** with Bot API scripts — delivery to Telegram happens inside the script itself, not via cron's delivery channel. This avoids double-delivery.

### Cron creation
```bash
cronjob(action='create', name='🌅 叫醒小马（早6:25/晚18:25）',
        schedule='25 6,18 * * *', deliver='local',
        no_agent=True, script='scripts/wake_up_xiaoma.py')
```

### Do NOT do:
- ❌ Don't send a long message — user doesn't need instructions
- ❌ Don't try to make the cron do the briefing (cron agent briefings were deleted — quality was poor, lacked context)
- ❌ Don't create Windows notification scripts to "wake the agent" — the agent cannot see system notifications
- ❌ Don't set deliver=telegram with Bot API scripts — this causes double-delivery (Bot sends it, then cron's deliver sends it again). Always use `deliver=local` with Bot API scripts since the script handles sending itself.
- ❌ Don't claim the agent can "wake itself up" or "remind itself" — the agent is PASSIVE and ONLY wakes on user messages. Any design that avoids user interaction is impossible with current Hermes architecture.

## Linked files

{{skill_dir contents:}}
- `scripts/wake_up_xiaoma.py` — deployed wake-up script using Telegram Bot API

## Delivery method: MEDIA only, no URLs

User explicitly rejected file-sharing URLs (frustration: "你给我的链接有问题", "不要"). The only approved delivery method:

```python
send_message(target="weixin", message="📄 小马财经日报...\n\nMEDIA:C:\\Users\\Admin\\Desktop\\小马财经日报.pdf")
```

The PDF arrives as a native file download on WeChat. Do NOT use tmpfiles.org, file.io, transfer.sh, or any other file-sharing service.

### Filename rule

The file must be named exactly `小马财经日报.pdf` on the Desktop. No date suffix, no English prefix. If the file is locked (PermissionError from a previous run still being cached), write to a temp path first and copy afterward:

```python
import tempfile, shutil
tmp = tempfile.mktemp(suffix='.pdf')
pdf.output(tmp)
shutil.copy(tmp, "C:/Users/Admin/Desktop/小马财经日报.pdf")
```

### Updated page structure (8 pages)

| Page | Section | Content |
|------|---------|---------|
| Cover | — | Title, date, issue #, data sources (global + Chinese) |
| 1 | 全球大盘纵览 | A-share + US + HK + FX + Oil + Commodities |
| 2 | 热点板块与全球要闻 | Top 3 movers + 6-8 global headlines + risk monitor |
| 3 | 策略与基金分析 | Core+Satellite, valuation, watchlist |
| 4 | 基金推荐与数据分析 | One recommended fund + supply/demand/inventory/cost analysis |
| 5 | 投资小课堂 | 6 quiz questions with full explanations |
| 6 | 今日总结 | Summary table + next issue preview |

## PDF Generation (preferred delivery format)

This user strongly prefers receiving the daily briefing as a **PDF document** rather than a long WeChat text message. See `references/pdf-generation-technique.md` for the full technique.

Two canonical scripts (use v2 for new reports, v1 for backward compatibility):

**v2 (recommended) — includes global sources, larger fonts, richer content:**
```bash
python "/c/Users/Admin/AppData/Local/hermes/memories/脚本缓存/admin助手/gen_finance_v2.py"
```

**v1 — simpler version (use as fallback):**
```bash
python "/c/Users/Admin/AppData/Local/hermes/memories/脚本缓存/admin助手/gen_cn_finance_pdf.py"
```

Both scripts output to `C:/Users/Admin/Desktop/小马财经日报.pdf`. Then deliver via WeChat:

```python
send_message(target="weixin", message="📄 小马财经日报...\n\nMEDIA:C:/Users/Admin/Desktop/小马财经日报.pdf")
```

The PDF arrives as a native file download on WeChat. When PDF generation is interrupted mid-session (e.g. user asks to re-issue a failed cron briefing), run the script instead of writing the content inline. Both scripts produce a 7-page document with all sections.

## Agent-mode vs Script-mode Workflow Decision (2026-06-24)

The financial briefing cron has two valid operating modes. Choose based on user request:

### Agent Mode (current as of 2026-06-24)
- `no_agent: false` — AI session runs the full briefing
- AI does: web_search → browser data gathering → analysis → PDF generation → deliver
- **When to use**: User explicitly asks to "restart" or "reboot" the briefing, wants fresh AI analysis
- **Model**: `deepseek-v4-flash` via `ollama-cloud` (fast cold start)
- **Deliver**: `telegram` (or `weixin` depending on user's preferred platform)
- **Advantage**: Real-time analysis, contextual reasoning, can adapt to breaking news
- **Disadvantage**: Consumes tokens, slightly slower than script

### Script Mode (legacy)
- `no_agent: true` + `script: financial_daily.py`
- Fixed Python script generates PDF from hardcoded data sources
- **When to use**: User wants zero-token automated delivery with predictable format
- **Deliver**: `local` (saves to desktop, user picks up manually)
- **Advantage**: Zero tokens, runs every time regardless of model availability
- **Disadvantage**: Stale data, no analysis, no adaptation to market events

### Switching from Script to Agent Mode
```
cronjob(action='update', job_id='01837ee19638',
  no_agent=false,
  model={'model': 'deepseek-v4-flash', 'provider': 'ollama-cloud'},
  deliver='telegram',
  prompt='Generate today\'s financial briefing PDF...')
```

### Switching from Agent to Script Mode
```
cronjob(action='update', job_id='01837ee19638',
  no_agent=true,
  script='financial_daily.py',
  deliver='local')
```

## Cron failure recovery workflow

When a cron briefing job errors and the user asks you to re-deliver:

1. **Inspect failure**: `hermes cron list` shows `last_status` and `last_delivery_error`.
2. **Common failure #1 — Model TTFB timeout**: Cron jobs run COLD (no prompt cache). Models like `gpt-5.4` (Codex) can timeout waiting ≥12s for first bytes. Fix: `cronjob(action='update', job_id='...', model={'model': 'deepseek-v4-flash', 'provider': 'ollama-cloud'})`.
3. **Common failure #2 — Platform rate limit**: WeChat sendmessage rate cap. Retry with `MEDIA:` delivery (sends as file, different API path) or wait for next tick.
4. **Re-generate**: Gather data manually (web_search + browser), run the PDF script, send the file. Don't just report the error — fix AND re-deliver.
5. **Record the fix**: Save the model/provider change to memory.

## User preference patterns (important)

When building briefings for this user (Kali / 卡莉), apply these defaults:

- **Delivery format**: PDF is strongly preferred over long WeChat text messages. The user explicitly rejected verbose multi-section chat output (frustration signal: "感觉字太多了"). Generate a compact PDF document and send the file via WeChat using `MEDIA:` prefix in send_message. Do NOT use file-sharing URL services (tmpfiles, file.io, etc.) — the user rejected these ("你的链接有问题", "不要"). Always send the file directly via MEDIA delivery.
- **Brand name**: The daily report is called **"小马财经日报"**, with NO date suffix or English prefix in the filename. Output path MUST be `C:/Users/Admin/Desktop/小马财经日报.pdf`. The file will appear in WeChat as a downloadable PDF attachment.
- **Analysis-first, not data-dump**: The user explicitly corrected "你要分析再发出来，而不是说直接就拿过来". Do NOT just paste raw search results or a list of numbers. Cross-reference data from multiple sources (both global AND Chinese), identify causal links (why did X move? what's the macro driver?), provide a reasoned thesis, and explain your thinking. Each section should include a brief analysis paragraph — not just bullet points. Global sources REQUIRED: Bloomberg, Reuters, CNBC, WSJ, FT, Yahoo Finance.
- **PDF font size**: Body text 9pt. The previous 8pt was too small. Section headings 16pt, cover title 32pt. Content has room to fill the page — don't squeeze to fit on fewer pages.
- **Global + China perspective**: The user rejected a China-only data set ("你的来源不够好，全球知名的财经要收集"). Every edition MUST include: A-share indices, US indices (S&P/Nasdaq/Dow), Hong Kong/HSI, oil, FX, and commodities. Section heading is "全球大盘纵览" not just "大盘概览".
- **Multiple quiz questions**: The user explicitly asked for more quiz content ("再加一些财经题目一起"). When including an education section, provide 5-6 questions spanning different weekly topics (rebalancing, DCA, PE ratios, stop-loss, behavioral finance, asset allocation), not just one. Each question follows the same format: scenario + 4 options + detailed explanation.
- **Delivery**: Weixin/WeChat, sending the PDF file natively (MEDIA:path). Do NOT attempt to upload to file-sharing sites; it won't work reliably from this environment.
- **Language**: Full Chinese (中文) for both chat communication AND in the PDF document. Register a Unicode font (Windows: `C:\Windows\Fonts\msyh.ttc` or `simsun.ttc`) via `fpdf2`'s `add_font(name, '', path, uni=True)` to render CJK characters. The default Helvetica/Courier/Times fonts do NOT support Chinese — you MUST register and use a Chinese font explicitly. See `references/pdf-generation-technique.md`.
- **Weekends off**: Briefings only on Mon-Fri unless user specifies otherwise
- **Education should be practical**: When quizzes are included, tie them to real investing skills. Rotate topics daily. **Never use general finance trivia questions.**
- **Strategy recommendation over fund pick**: Frame the analysis section as "Recommended Approach" with core/satellite/defensive tiers and market context, rather than picking a single specific fund.
- **Real-time data via browser + web_search**: Gather data from multiple sources (web_search for headlines/titles, browser_navigate to financial sites for live index values). Cross-reference before presenting. Use Chinese-language queries for Chinese data, English queries for global data.
- **Tone**: Professional, analytical, concise. Use moderate emoji for legibility (📊📰🔥💰🧠) but keep the report text-driven.
- **Data freshness**: Always note the date. If real-time data isn't available, explain the limitation.

## Data Source Navigation Guide

Use these specific URLs and extraction patterns for reliable real-time data collection. Browser navigation is preferred over web_search for live index/fund data.

> ⚠️ **web_extract is UNAVAILABLE** in this environment (returns "DuckDuckGo is a search-only backend"). Do not attempt it. Stick to `browser_navigate + browser_snapshot` for live content and `web_search` as fallback.
>
> See `references/data-gathering-fallbacks.md` for the complete real-world failure matrix and proven alternatives.

### A-share indices (WORKING)
**URL**: `https://quote.eastmoney.com/`
**Reliability**: ✅ **High** — fast load, data visible in first snapshot
**Extraction**: The page renders key index data near the top. Look for `上证：4075.10 ↑17.36 0.43%` pattern under "全球股市". Format: `上证：[value] [↑/↓][change] [pct%]`. Trading volume and advance/decline counts are in the same line.

**Fallback if page too heavy**: `web_search` with `"A股收评 YYYY年MM月DD日"` — 金融界(jrj.com.cn.cn) or 腾讯新闻 have clean daily recaps.

### Global indices — eastmoney homepage (WORKING)
**URL**: `https://www.eastmoney.com/`
**Reliability**: ✅ **High**
**Extraction**: Global index ticker bar shows all key indices: 恒生, 日经225, 道琼斯, 纳斯达克, 德国DAX30, 法国CAC40, 英国富时100. Format: `指数名 [value] [↑/↓][change] [pct%]`.

### Individual index pages (TIMEOUT-PRONE — avoid)
URLs that reliably **timeout or 404**:
- `https://quote.eastmoney.com/zs399006.html` (创业板指) → ❌ times out
- `https://quote.eastmoney.com/hk/HSI.html` → ❌ 404
- `https://fund.eastmoney.com/data/fundranking.html` → ❌ times out

**Use web_search fallback instead** (see `references/data-gathering-fallbacks.md`).

### US market data — Yahoo Finance (RECOMMENDED)
Yahoo Finance is a **reliable, fast source** for US market closing data. Three key URLs:

| Index | URL | Notes |
|-------|-----|-------|
| S&P 500 | `https://finance.yahoo.com/quote/%5EGSPC/` | ✅ Loads cleanly no overlay. Shows close, change, prev close, range, volume, heatmap. |
| Dow Jones | `https://finance.yahoo.com/quote/%5EDJI/` | ✅ Same clean load. Shows Dow components with daily % changes. |
| NASDAQ | `https://finance.yahoo.com/quote/%5EIXIC/` | ⚠️ **Alert overlay blocks first load** — must dismiss via `browser_click(@e1)` first. Works fine after. |

**Yahoo Finance homepage** (`https://finance.yahoo.com/`) also shows the US futures ticker bar (S&P Futures, Dow Futures, Nasdaq Futures, VIX, Gold, Brent, Bitcoin) — fast, no overlay.

**Extraction tip**: Use `browser_console(expression='...')` to extract structured data from Yahoo Finance pages. See `references/data-gathering-fallbacks.md` for the extraction JS snippet.

### Fund rankings (TIMEOUT-PRONE)
**URL**: `https://fund.eastmoney.com/data/fundranking.html`
**Reliability**: ❌ **Low** — heavy JS, frequently times out
**Fallback**: `web_search` with targeted queries, or navigate to `https://fund.eastmoney.com/` homepage (lighter, shows featured fund cards).

### Headline news
**URL**: `https://wallstreetcn.com/`
**Reliability**: ✅ **High** — fast load, 20+ headlines with author/timestamp
**No login required**.

### Global market summary (web_search fallback)
When browser index pages fail, use web_search with:
- **US markets**: `"今日美股市场行情快报 YYYY年MM月DD日"` (reliably returns structured summary with all 3 index levels)
- **A-share recap**: `"A股收评 YYYY年MM月DD日"`
- **创业板**: `"创业板指 今日行情 YYYY年MM月DD日 收盘"`
- **恒生**: `"恒生指数 YYYY年MM月DD日 收盘 涨跌"`
- **Fund data**: `"科技基金 ETF 推荐 YYYY年MM月"`

### Fallback news source
**URL**: `https://www.eastmoney.com/` (homepage)
**Reliability**: ✅ **High**

## Pitfalls

- **Model choice for cron**: Cron jobs run in cold-start sessions — NO prompt cache, NO warm model context. Models like `gpt-5.4` (Codex) can TTFB-timeout in this environment because the cron runner waits only 12s for first bytes. Always use fast-start models like DeepSeek-V4-Flash for cron jobs. The cron `model` override on creation or update is the right fix path.
- **PDF layout overflow**: fpdf2's `multi_cell(w=0, h, txt)` uses the REMAINING width from current x position to right margin. After a `cell()` call (which advances x), the remaining space shrinks. If you pass a hardcoded width like `multi_cell(W-6, ...)` when current x=16 and usable width=190, the actual remaining space is only 174 — the hardcoded 184 will OVERFLOW the right margin. Always pass `w=0` after resetting x with `set_x(margin + indent)`, OR check the remaining width with `self.w - self.x - self.r_margin` before choosing a value. The safe pattern: `self.set_x(left + indent); self.multi_cell(0, h, txt)`.
- **File locked when re-running**: If the PDF output file is still open in the WeChat preview or any app, `pdf.output(path)` raises `PermissionError: [Errno 13] Permission denied`. Close the file on the receiving end first, or write to a temp filename and copy afterward.
- **Overly verbose prompts**: Keep cron prompts focused. Each section should have clear constraints — how many items, what format.
- **No fallback**: Always include fallback instructions for when web searches return nothing useful (e.g., "based on recent known macro context").
- **No risk disclaimer**: Fund/stock recommendations MUST include risk warnings. Never present picks as guaranteed.
- **Weekend delivery**: User may not want weekend delivery. Ask or default to weekdays.
- **Quiz disconnected from briefing**: The quiz should relate to the day's content or theme, not be random.
- **Search queries in wrong language**: Chinese users need Chinese search terms for Chinese market data.
- **Using web_search alone for financial data**: `web_search` returns only snippets, not real-time index levels, fund rankings, or price data. For financial briefings, use browser_navigate to actual market sites. The user tested both approaches and chose browser for real-time accuracy.
- **Quiz too general**: The user explicitly rejected general finance questions. Every quiz must teach a practical investing skill — fund mechanics, valuation, risk, strategy, allocation, or behavioral finance. Rotate topics daily.
- **No fund recommendation**: Don't just report news. The user wants actionable analysis — pick the most relevant fund and explain why. This is a core section, not optional.
- **Yahoo Finance NASDAQ page alert overlay**: The `^IXIC` page on Yahoo Finance triggers a modal/dialog box on first load. If you navigate there and see only an alert dialog, click its close button with `browser_click(@e1)` to dismiss it and access the data. The S&P 500 (`^GSPC`) and Dow (`^DJI`) pages do NOT have this issue.
- **eastmoney global quote cross-linking**: Different eastmoney pages (homepage, quote page, SPY page) may show slightly different sets of global indices. The SPY/US stock page at `quote.eastmoney.com/us/SPY.html` has a different "全球股市" ticker set than the main `quote.eastmoney.com/` page. If a specific index is missing from one, check another eastmoney page rather than giving up.
