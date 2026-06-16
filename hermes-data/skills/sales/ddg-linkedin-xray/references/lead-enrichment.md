# Lead Enrichment (X-Ray → Contact Info Pipeline)

After sourcing LinkedIn profile data via X-Ray search, the next step is enriching each company with **website, email, phone, and decision-maker name**. This guide documents patterns, success rates, and known dead ends.

## Pipeline Overview

```
Raw leads (name, job, company, location)
    → Clean company names (remove junk)
    → Find company website (web search)
    → Find company email + phone (web search)
    → Find CEO/decision maker (web search)
    → Try direct website scrape for contact info
    → Try person-specific search for email
    → Export enriched_leads.xlsx
```

## Company Name Cleaning

Raw "company" from X-Ray titles is often polluted with concatenated adjacent results (DDG artifact). Extract from multiple signals in priority order:

1. **Description field** — Look for `Experience: CompanyName` pattern
2. **Job title** — `"Job at Company"` or `"Job @ Company"` pattern
3. **Raw field** — Strip LinkedIn noise: `re.sub(r'\s*\|\s*LinkedIn.*', '', raw)`, remove trailing `...`
4. **URL slug** — Less reliable but sometimes contains company hint

**Junk to discard**: `Automation`, `Vice President`, `Remote`, `Energy`, `Ease`, `Dongf`, `Junior Electrical Control`, `4B Systems and`, any single-word generic terms, strings < 3 chars.

**Good companies found this session**: Omniflex, Rand Water, Schneider Electric, Anglo American, Chevron, Alstom, KHS, Jendamark Automation, Rockwell Automation, AUTOMATED SYSTEM WORKS, Chilltemp Automation, A2Z Automation, Aveng Manufacturing.

## Enrichment Search Strategy

For each company, run 3 sequential searches (1.5s pause between each):

### Search 1: Company website
```
web_search(query=f'"{company}" official website', limit=5)
```
Look for first non-social-media URL that contains the company name or is an obvious corporate domain. Skip: linkedin.com, facebook, twitter, instagram, wikipedia, youtube, github.

### Search 2: Email + CEO + phone
```
web_search(query=f'"{company}" email contact', limit=5)
```
Extract:
- **Email**: `r'([\w.+-]+@(?:[^.]+\.)+(?:com|co\.za|co\.ke|co\.ng|org|net))'` — skip gmail/yahoo/hotmail/outlook
- **Phone**: SA format `\+27[\s-]?\d[\d\s-]{6,12}`, Nigeria `\+234...`, Kenya `\+254...`
- **CEO**: `(?:CEO|Managing Director|Founder|President|Director)\s*[:\-–\s]*\s*([A-Z][a-z]+(?:\s[A-Z][a-z]+){1,2})`

### Search 3: Person-specific (fallback if no email)
```
web_search(query=f'"{contact_name}" "{company}" email', limit=3)
```
Sometimes the contact person's email is indexed separately even when the company's generic email isn't.

## Success Rates (from this session)

| Signal | Success Rate | Notes |
|---|---|---|
| Company website | ~80% | Most real companies have indexed websites |
| Email address | ~15% | Small-medium companies rarely have email indexed |
| Phone number | ~5% | SA mobile numbers rarely in search snippets |
| CEO name | ~10% | Only when CEO is mentioned in a directory |

**Why so low?** DuckDuckGo search results are limited; they return snippets from pages, not full page contents. A proper email finder (Hunter.io, RocketReach) would get much higher yields.

## When Direct Search Fails (the other ~85%)

For companies where web search found no email, try these fallback approaches **outside Hermes**:

| Approach | Tool | Best For |
|---|---|---|
| Domain email search | Hunter.io (free 25/mo) | Any company with a website |
| LinkedIn company page | Copy-paste | Finding "Contact us" section |
| Google Maps | Maps listing often has phone | Local businesses |
| Company website Contact page | Manual browser visit | Finding contact forms |
| WhoIs domain lookup | whois.com | Getting admin email |
| RocketReach/Lusha | Freemium APIs | Large companies |

The 9 companies this session that returned nothing (Letek Industrial Automation, UltraSec Fencing, etc.) are typically small South African firms with thin web presence. They're best approached via the employee's LinkedIn profile directly.

## Output Format

Final Excel has two sheets:

**Sheet 1: Enriched Leads** — one row per person
- Company, Contact Name, Job Title, Country, Website, Email, Phone, LinkedIn URL, Status

**Sheet 2: Company Summary** — one row per company
- Company, Website, Email, Phone, CEO, Status (✅Email / 🌐Website / 🔍Manual)

## Constraints

- **No email scraping from LinkedIn profiles themselves** — authwall prevents access
- **Do NOT visit LinkedIn profile URLs programmatically** — always authwall redirect
- **DDG search is rate-limited** — ~1 query per 1.5s max, slower = better results
- **African company data is sparse** in web indexes compared to US/Europe
- **Phone numbers** — SA format `+27 XX XXX XXXX`, always ask "Is this WhatsApp?" before outreach