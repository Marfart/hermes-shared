---
name: bliiot-customer-acquisition
version: 3.0.0
description: B2B customer acquisition workflow for BLIIoT — Google Maps + company web crawling, LinkedIn alternatives via Google Dorking, Scrapling anti-CF bypass, pipeline commander orchestration with health checks/checkpoints/retries. Zero LinkedIn automation, 100% legal Route A method.
category: data-science
tags: [bliiot, customer-acquisition, web-scraping, anti-detection, pipeline-orchestration, scrapling, google-maps, whatsapp-outreach]
related_skills: [whatsapp-auto-sender, bliiot-b2b-directory-promotion]
---

# BLIIoT Customer Acquisition v2.0

## When to load this skill

- User asks to "find customers", "develop clients", "get leads", "find emails/phones/WhatsApp"
- User asks to "expand to [region/country]" with industrial automation products
- User asks to scrape Google Maps / company websites / LinkedIn for contacts
- User needs anti-bot bypass (Cloudflare), proxy rotation, or stealth browser automation
- User wants to run the full pipeline (search → enrich → queue → messages → send) in one command
- User asks about LinkedIn scraping feasibility

## Key Insight: LinkedIn scraping reality

**LinkedIn is NOT scrapable without login.** It uses:
- Cloudflare Turnstile (hard-block for headless)
- Bot Detection (mouse trajectory, scroll speed analysis)
- Rate limiting (fast account suspension)
- Legal risk (hiQ Labs vs LinkedIn: still litigating, LinkedIn keeps blocking)

**DO NOT** try to automate LinkedIn login or scrape LinkedIn profiles. Both LinkedIn ToS and legal precedent make this high-risk.

## Strategy: Four Tiers of Customer Discovery

### Tier 1 ✅ Google Maps (existing, proven)
Opened directly in the user's local browser via `browser_navigate`:
```
https://www.google.com/maps/search/<keyword>+<country>
```
Returns company name, phone (WhatsApp-enabled in Africa), website, rating. Already working in production.

### Tier 2 🔥 Google Dorking for LinkedIn (recommended alternative)
LinkedIn company pages ARE indexed by Google. Search instead of scraping:
```
site:linkedin.com/company "industrial automation" "South Africa"
site:linkedin.com/company "system integrator" "Nigeria"
```
Then use `web_extract` on the company's own website (found from LinkedIn page or Google search) to get emails/phones. This is 100% legal — Google search results are public, and company websites are public.

### Tier 3 🚀 Scrapling StealthyFetcher for anti-CF bypass
For websites blocked by Cloudflare, use Scrapling (20k⭐, D4Vinci/Scrapling):
```python
pip install scrapling[all]
scrapling install  # downloads browser + system deps
```
```python
from scrapling.fetchers import StealthyFetcher
p = StealthyFetcher.fetch(url, headless=True, solve_cloudflare=True)
emails = p.find_by_text(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', regex=True)
```
Scrapling bypasses Cloudflare Turnstile out of the box, spoofs browser fingerprint, and supports adaptive element relocation.

### Tier 4 🎯 Search Engine Lead Mining (multi-country, per-session)
For finding system integrators when Google Maps doesn't show enough results, or for large-scale multi-country campaigns. **Best for industrial automation / PLC / SCADA / energy companies.**

**Approach:** Use `web_search` (Hermes search tool, backed by DuckDuckGo) with carefully crafted multi-category queries per country, then grab contact info from company websites and business directories via `mcp_fetch_fetch` or `web_extract`.

**Step 1 — Multi-query per country (3-4 search rounds per country):**
```python
queries = [
    '"system integrator" "{country}" PLC SCADA automation company contact',
    '"industrial automation" "{country}" PLC SCADA IIoT company email',
    '"{country}" system integrator automation company contact email address',
    '"system integrator" "{country}" "industrial" email OR contact',
]
```

**Target countries for BLIIOT:** South Africa (P0), Nigeria (P0), Kenya (P1), Zimbabwe (P1)

**Step 2 — Extract contacts from search results:**
- Direct search hits often show phone/email in snippet (e.g. EngNet, AfricaBizInfo directories)
- Company URLs found in results → fetch via `mcp_fetch_fetch` homepage + /contact page
- If fetch fails (timeout/blocked), search `"{company_name}" contact email phone` to find directory pages
- For South African companies: EngNet (www.engnet.co.za) and African Advice directories are rich sources of email/phone

**Step 3 — Score and output:**
- ★★★★★ = PLC/SCADA/IIoT all match BLIIOT portfolio → HIGH priority
- ★★★★☆ = SCADA/HMI/IIoT partial match → MEDIUM-HIGH
- ★★★☆☆ = Different specialty but uses IIoT/gateways → MEDIUM
- Output to Excel with: Country column color-coded, WhatsApp column green, priority column color-coded

**Proven query patterns (from 2026-06-04 session, 15 leads across 3 countries generated):**
```
# South Africa
"South Africa" "system integrator" PLC SCADA IIoT industrial automation contact
"South Africa" industrial automation system integrator company contact
"South Africa" PLC SCADA system integrator companies list contact email

# Nigeria
Nigeria SCADA PLC system integrator industrial automation company contact email
"system integrator" Nigeria IIoT remote monitoring energy automation company email
Nigeria industrial automation company PLC SCADA IIoT Lagos email contact info

# East Africa
Kenya Tanzania industrial automation PLC SCADA system integrator company contact email
"East Africa" "system integrator" PLC SCADA industrial automation Kenya Tanzania Uganda email
```

**Step 4 — Fill gaps for companies without direct email:**
- Search `"{company_name}" contact email phone`
- Search `"{company_name}" LinkedIn` for description/sector (public page, no login)
- For South African companies: check engnet.co.za supplier pages (rich directory data)
- If all searches return no email, note 'N/A' in the sheet and still score the lead

**Score output structure (Excel):**
| Column | Content | Formatting |
|--------|---------|------------|
| # | Row number | |
| Country | Country name | Color-coded per country |
| Company Name | Full name | |
| Specialty | Services/products | |
| Email | Direct contact email | Red if N/A |
| Phone | Phone number | |
| WhatsApp | Yes/No | Green highlight |
| Website | URL | |
| Address | Physical address | |
| Product Match | Stars + description | Bold+green if ★★★★★ |
| Priority | HIGH/MEDIUM/LOW | Green/yellow/red |
| Notes | Key details, contact person | |

**Common pitfalls:**
- ❌ Bing/Brave/Google cache of LinkedIn pages do NOT store email/phone — those fields are login-walled even from crawlers
- ❌ `web_extract` via ddgs backend fails — use `mcp_fetch_fetch` with proper URL instead
- ❌ `browser_navigate` may timeout on South African/African websites (slow hosting) — fall back to `mcp_fetch_fetch` and `web_search`
- ❌ Don't expect to find email for every company — some have only contact forms. These are still valid leads for calling/WhatsApp

## Pipeline Commander Architecture (NEW)

All 16 scripts in `C:\Users\Admin\AppData\Local\hermes\scripts\buyer-development\` are orchestrated by `pipeline_commander.mjs`:

```
node pipeline_commander.mjs --help
  --pipeline joinf        # 富通管道 (fetch → enrich → queue → followup → messages)
  --pipeline google-maps  # Google Maps管道
  --check                 # 🔍 全身体检 (scripts/ports/output dir)
  --status                # 📊 查看运行状态和历史
  --resume send           # 🔄 断点续跑发送
  --all                   # 🔥 全自动一条龙
```

The commander incorporates patterns learned from three 35k+⭐ GitHub projects (geekcomputers/Python, DhanushNehru/Python-Scripts, Amazing-Python-Scripts):
- ✅ JSON configuration-driven (`pipeline_config.json` centralizes all params)
- ✅ Health check on startup (check scripts exist, Chrome ports alive, disk space)
- ✅ Retry with exponential backoff (2 retries per step)
- ✅ Checkpoint system (each step saves state, `--resume` picks up from failure)
- ✅ Timestamped output files (no overwrites)
- ✅ Unified logging with emoji indicators

### pipeline_config.json structure
```json
{
  "paths": { "scripts_dir", "output_dir", "node_path" },
  "chrome_ports": { "joinf_search": 9226, "whatsapp_send": 9223 },
  "pipeline_steps": {
    "joinf": { "keywords": [...], "send_limit": 50, ... },
    "google_maps": { "target_markets": [...], ... }
  },
  "whatsapp_send": { "default_delay_ms": 2500, "max_retries": 2 }
}
```

**Never hardcode paths/ports/keywords in scripts** — they all go in `pipeline_config.json`.

## Scrapling Quick Reference

From the 2026 web scraping ecosystem research:

| Tool | Stars | Use Case |
|------|-------|----------|
| **Scrapling** | 20k⭐ | Adaptive scraping, auto-repositioning elements, CF bypass, proxy rotation |
| **undetected-chromedriver** | 10k⭐ | Selenium patched to pass bot detection (Imperva/DataDome) |
| **Crawl4AI** | 50k⭐ | LLM-friendly crawler, markdown output, async |
| **Firecrawl** | 70k⭐ | Turn websites into LLM-ready markdown |
| **ScrapeGraphAI** | 18k⭐ | Describe what you want in plain English, AI extracts data |
| **curl_cffi** | 3k⭐ | TLS fingerprint impersonation (Chrome/Firefox) |

Scrapling is the top pick for anti-detection scraping because it bundles everything in one `pip install`:
- `StealthyFetcher` — headless browser with spoofed fingerprints
- `AsyncStealthySession` — concurrent requests with browser tab pool
- `solve_cloudflare=True` — auto-solves Turnstile
- `adaptive=True` — elements re-found if website changes CSS
- Built-in proxy rotation, MCP server, CLI shell

## Workflow Steps

### Step 1: Market Selection
Target priority: South Africa (P0), Nigeria (P0), Kenya (P1), Zimbabwe (P1 with ZODSAT tie-in)

### Step 2: Google Maps Search
Use `browser_navigate` with keyword+country. Keyword ideas:
- `industrial automation`, `system integrator`, `PLC SCADA`, `IIoT`
- `solar energy monitoring`, `power substation automation`
- `building automation`, `remote monitoring solutions`

### Step 3: Extract + Crawl
- Get company name, phone, website from Maps
- Use `web_search` to find official website if not shown
- Use `web_extract` on homepage + /contact for emails
- **NEW: If Cloudflare blocks, fall back to Scrapling StealthyFetcher**

### Step 4: Score & Output
- Score by product match keywords → recommend specific BLIIOT products
- Output to `C:\Users\Admin\Desktop\Working\BLIIoT_Customer_Leads_Master.xlsx`
- Green highlight for phone-found (WhatsApp reachable)

### Step 5: WhatsApp Outreach
Use the `whatsapp-auto-sender` skill or the CDP-based `whatsapp_bulk_sender_cdp.mjs` for sending.

For message templates, see `references/whatsapp-outreach-scripts.md` (11 categories: SCADA/PLC, System Integrator, Energy/Solar, Building Automation, etc.)

## Important Rules

- **NEVER** crawl LinkedIn directly — account bans + legal risk
- Use Google Dorking (`site:linkedin.com/company`) as the read-only alternative
- African phone numbers (+27/+234/+254/+263) are WhatsApp-enabled
- All parameter config goes in `pipeline_config.json`, not hardcoded in scripts
- Run `node pipeline_commander.mjs --check` before starting a big pipeline run
- Run `node pipeline_commander.mjs --status` to check if pipeline left checkpoint from last time
- Timestamps in output files use `YYYY-MM-DD` format consistently
- Never use bare `try/except` — use Scrapling's retry or the commander's retry engine

## Pitfalls

- ❌ Google Maps shows only ~7 results per query. Vary keywords for coverage
- ❌ `web_extract` may timeout on slow sites — skip, don't hammer retries
- ❌ Cloudflare is the #1 blocker for company websites. Don't fight it with requests/curl — use Scrapling StealthyFetcher or skip
- ❌ LinkedIn clicking/scrolling automation = instant rate limit + account review
- ❌ Scrapling's `scrapling install` downloads full browser — takes time. Run once, don't reinstall
- ❌ The pipeline commander's retry pattern retries 2x with backoff. If it fails 3 times, the issue is likely not transient — check the specific script's error output
- ❌ When Claude Code or Gemini subagent is also running, Chrome CDP ports (9223/9226) may conflict — check with `--check` first

## Related Files

- `references/lead-builder-script.md` — Master lead builder Python class
- `references/web-scraping-ecosystem-2026.md` — Full scraping tool ecosystem research
- `references/africa-lead-examples-2026-06-04.md` — Concrete session example (15 leads, 3 countries, query patterns, contact sources, scoring rubric, tech notes)
- Scripts at `C:\Users\Admin\AppData\Local\hermes\scripts\buyer-development\`
- Config at `C:\Users\Admin\AppData\Local\hermes\scripts\buyer-development\pipeline_config.json`