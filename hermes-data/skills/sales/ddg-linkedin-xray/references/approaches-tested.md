# Approaches Tested: LinkedIn Data Collection Without Login

Tested 2026-06-04. Current status as of this date. Search engines change their
indexing policies over time — re-test periodically.

## 🟢 Works — DuckDuckGo X-Ray

- **Tool**: `web_search` (Hermes built-in) or DDG direct
- **Query format**: `site:linkedin.com/in/ "keyword" target_region`
- **What you get**: name, job title, company, location, connections count, headline snippet
- **Yield**: ~60-80 unique / 8 queries / 2.5 min
- **Blocked?** No captcha, no rate-limit observed at 1.5s intervals
- **Note**: data comes from search results, NOT from visiting the profile page
- **Status**: ✅ **PRIMARY PATH**

## 🔴 Dead End — Direct Profile Visit

- **Test**: `curl` + browser (Playwright) to `https://za.linkedin.com/in/rochelle-vivian-goagoses-09a801130`
- **Result**: LinkedIn authwall — immediately redirects to `https://www.linkedin.com/authwall?...&sessionRedirect=...`
- **HTML payload**: empty shell with only JS redirect code. Zero profile data.
- **Alternatives tried**: different country domains (za.linkedin.com, ke.linkedin.com), desktop User-Agent strings, Playwright headless
- **Status**: ❌ **BLOCKED** — server-side authwall, no bypass

## 🔴 Dead End — Google X-Ray

- **Query**: `site:linkedin.com/in/ "PLC" "SCADA" "South Africa"`
- **Result**: LinkedIn disallowed Google indexing of `/in/` in robots.txt (Jan 2024). Google shows zero or near-zero LinkedIn profile results.
- **Reference**: https://booleanstrings.com/2024/01/22/linkedin-x-ray-workaround/
- **Note**: Even pages that were indexed pre-2024 are being slowly purged.
- **Status**: ❌ **DEAD** — LinkedIn actively blocked Google crawler

## 🔴 Dead End — Google Cache

- **Test**: `https://webcache.googleusercontent.com/search?q=cache:https://za.linkedin.com/in/profile`
- **Result**: Redirects to `https://www.google.com/sorry/index?...` (Google captcha wall)
- **Status**: ❌ **BLOCKED** — trigger Google's automated abuse detection

## 🔴 Dead End — Bing X-Ray

- **Test**: `curl` and browser to `https://www.bing.com/search?q=site:linkedin.com/in/+PLC+SCADA`
- **Result**: Cloudflare Turnstile challenge page (captcha). Even with Playwright browser, CF Turnstile fires and blocks search results.
- **Console evidence**: `Failed to load resource: the server responded with a status of 401` from Turnstile challenge platform
- **Status**: ❌ **BLOCKED** — Cloudflare Turnstile

## 🟡 Caveated — Brave X-Ray

- **Test**: Not directly tested (API key required for Brave Search API)
- **Note**: Brave Search still indexes LinkedIn profiles in its own crawler, independent of Google/Bing. May work with their free API tier (2,000 queries/month).
- **Status**: 🟡 **UNTESTED** but theoretically viable

## 🟡 Caveated — Third-Party APIs (Proxycurl / Apify)

- **Proxycurl** — https://nubelaco.github.io/proxycurl-py-linkedin-profile-scraper/
  - Pulls public LinkedIn data without login. Legal per HiQ vs LinkedIn ruling.
  - Free tier: 100 requests/month. Paid: ~$0.001/profile.
  - GitHub repos: `nubelaco/proxycurl-py-linkedin-profile-scraper` (Python SDK)
- **Apify** — https://apify.com/unseenuser/linkedin-profile
  - "LinkedIn Bulk Profile Scraper with No Cookies Required"
  - Uses Apify's proxy infrastructure. Free credits available.
- **Status**: 🟢 **WORKS** but requires API signup and has usage costs

## 🟡 Caveated — People Search Aggregators

These sites already aggregate LinkedIn data and expose it through their own search:

| Platform | Free tier | Data available |
|---|---|---|
| RocketReach | 5/mo | email, phone, LI profile |
| Lusha | 50/mo | email, phone, LI profile |
| Apollo.io | credits | 270M+ contacts, email |
| Hunter.io | 25/mo | domain→email, LI→email |
| SignalHire | 5/mo | LI profile data |

These don't scrape LI directly — they use their own databases built from public
sources. Useful for email enrichment after you have company names.

## Summary Decision Tree

```
Need LinkedIn leads without login?
├── Have a profile URL → ✗ CANNOT scrape it directly (authwall)
├── Need a batch by keyword/location
│   ├── Try DDG X-Ray first → 🟢 60-80 leads in 2.5 min
│   ├── Need more volume → use Proxycurl API (paid)
│   └── Need emails too → Apollo.io / RocketReach
└── Need to verify: bypass Google/Bing attempts → ❌ blocked
```