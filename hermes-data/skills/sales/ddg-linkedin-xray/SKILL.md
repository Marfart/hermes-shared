---
name: ddg-linkedin-xray
description: 不登录LinkedIn，通过搜索引掣 X-Ray 技术批量获取客户LinkedIn公开资料（姓名/职位/公司/地点）
---

# DDG LinkedIn X-Ray — Lead Sourcing Without Login

## Overview

Acquire LinkedIn profile data (name, title, company, location, profile URL) **without logging in**, using X-Ray search queries on search engines that still index LinkedIn public profiles.

**Primary working path**: `site:linkedin.com/in/` + keywords on DuckDuckGo.  
**Dead ends documented**: see `references/approaches-tested.md` to avoid re-testing.

## When to use

- You need a quick batch of prospects by role/industry/region
- You want to bypass LinkedIn's search caps and login wall
- You're sourcing B2B leads (system integrators, automation engineers, etc.)
- Budget is zero (no API keys, no SaaS subscriptions)

## How it works

LinkedIn blocked Google indexing of `/in/` pages in Jan 2024. DuckDuckGo (and to a lesser extent Brave/Bing) still returns public-profile metdata in search results: **name, job title, company, location, connections count, and headline snippet** — enough for initial lead qualification.

## Queries to use

Run 6-8 varied queries, each using `site:linkedin.com/in/` + relevant keywords.

### BLIIOT-targeted queries (verified working)

```
site:linkedin.com/in/ "system integrator" "South Africa"
site:linkedin.com/in/ "PLC" "SCADA" "South Africa"
site:linkedin.com/in/ "IIoT" Africa engineer
site:linkedin.com/in/ "industrial automation" Kenya Nigeria
site:linkedin.com/in/ "automation" "Africa" director
site:linkedin.com/in/ "RTU" "SCADA" Africa
site:linkedin.com/in/ "remote monitoring" Africa SCADA
site:linkedin.com/in/ "control systems" "Africa" engineer
```

**Yield**: ~60-80 unique profiles from 8 queries (~2.5 minutes runtime).  
**Geographic skew**: ~40% South Africa, ~10% Kenya, ~8% Nigeria, rest pan-Africa.

### Africa sourcing templates

| Focus | Example query |
|---|---|
| System integrators | `site:linkedin.com/in/ "system integrator" Africa industrial automation` |
| PLC/SCADA engineers | `site:linkedin.com/in/ "PLC" "SCADA" Africa automation` |
| IIoT specialists | `site:linkedin.com/in/ "IIoT" Africa engineer` |
| Energy monitoring | `site:linkedin.com/in/ "solar" "Africa" engineer automation` |
| Mining automation | `site:linkedin.com/in/ "mining" "automation" South Africa` |
| Country-specific | `site:linkedin.com/in/ "industrial automation" Nigeria` |

### Global template

| Focus | Example query |
|---|---|
| Broad | `site:linkedin.com/in/ "VP" OR "Director" "industrial automation"` |
| Role-specific | `site:linkedin.com/in/ "head of" OR "manager" "IoT"` |
| Company-targeted | `site:linkedin.com/in/ ("Rockwell" OR "Siemens") AND "sales"` |

## Running the scraper

### Method A — execute_code (recommended, no memory issues)

```python
from hermes_tools import web_search
import time, re

queries = [
    'site:linkedin.com/in/ "system integrator" "South Africa"',
    'site:linkedin.com/in/ "PLC" "SCADA" "South Africa"',
    # ... add more
]

all_leads, seen_urls = [], set()
for q in queries:
    r = web_search(query=q, limit=10)
    items = r.get('data', {}).get('web', []) if isinstance(r, dict) else []
    for item in items:
        url = item.get('url','')
        if 'linkedin.com/in/' not in url or url in seen_urls: continue
        seen_urls.add(url)
        # parse title -> name, job, company
        all_leads.append({...})
    time.sleep(1.5)
```

Output as JSON → convert to Excel with openpyxl.

### Method B — standalone script

```bash
python memories/脚本缓存/客户挖掘/ddg_linkedin_xray.py \
  --template bliiot_targets --limit 150
```

### Output format

Excel at `Desktop/Working/linkedin_xray_MMDD_HHMM.xlsx` with columns:
- Full Name, Job Title, Company, Country (emoji flag), Profile URL, Source Query, Description snippet

## Output processing (next steps)

1. Export results to Excel
2. For each company, run `web_search` to find official website
3. Use domain → Hunter.io / RocketReach for email discovery
4. Feed into email-marketing or whatsapp pipeline
5. Track in customer analysis pipeline

## Title parsing rules

LinkedIn search result titles follow patterns:
- `Name - Job Title - Company | LinkedIn` → name, job, company all clear
- `Name - Job Title at Company | LinkedIn` → split "at" in job field
- `Name - Company | LinkedIn` → job empty, company set
- `Name | LinkedIn` → only name

Parse with regex: strip ` | LinkedIn` suffix, split by ` - `, handle `job at company` sub-pattern.

## Constraints & pitfalls

- **Do NOT attempt to visit the profile URL** — LinkedIn authwall redirects to login. All usable data is in the search result snippet.
- **Do NOT use Bing** — Cloudflare Turnstile blocks automated queries.
- **Do NOT use Google** — LinkedIn's 2024 `robots.txt` change removed most `/in/` pages from index.
- **Do NOT use Google Cache** — returns Google's own captcha wall.
- **Do NOT use Brave Search API** — low yield, requires API key.
- **Title crowding** — DDG sometimes concatenates adjacent results into one title (e.g. "John Doe | LinkedInJane Smith"). The first name before the boundary is correct; discard garbage.
- **Country detection** — heuristic-based (city/country keywords in description). ~30% will be "unspecified" if no Africa keyword matched.
- **Rate limit** — DuckDuckGo tolerates ~1 query per 1.5s. No higher frequency tested.
- **Data volatility** — search results change daily. The same query on different days returns different profiles.

## Lead enrichment (post-sourcing)

After collecting leads, see `references/lead-enrichment.md` for the **company → website → email → CEO** pipeline including search strategies, success rates, parsing rules, and fallback approaches when web search returns nothing.

## Related skills

- `bliiot-email-marketing` — email outreach after lead enrichment
- `bliiot-agent-orchestrator` — multi-role pipeline orchestrator  
- `bliiot-customer-analysis` — data analysis pipeline for enriched leads