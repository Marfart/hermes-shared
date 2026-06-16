# LinkedIn X-ray Lead Generation (No Login)

## What Works (tested 2026-06-04)

| Method | Works? | Gets you |
|--------|--------|----------|
| web_search("site:linkedin.com/in ...") | YES | Name, job title, company name, LinkedIn URL |
| Company website crawl | YES | Emails, phone numbers from /contact /about pages |
| DuckDuckGo HTML scraping | NO | Returns HTTP 202, blocks direct scraping |
| Scrapling StealthyFetcher | NO | Times out on Google |

## Pipeline

```
Step 1: Search LinkedIn via web_search tool
  web_search("site:linkedin.com/in SCADA South Africa system integrator")
  -> Returns: profile URLs, titles, descriptions

Step 2: Extract company name from results
  - From /company/COMPANY_NAME in URL
  - From "at COMPANY_NAME" in title text

Step 3: Find official website
  web_search('"COMPANY_NAME" official website')
  -> Pick the first non-LinkedIn, non-social-media result

Step 4: Crawl for contact info (httpx or curl)
  Try: /contact, /contact-us, /about, /about-us
  -> Extract: email (regex), phone numbers (regex)

Step 5: WhatsApp detection
  Phone starting with +27 (SA), +234 (Nigeria), +254 (Kenya), +263 (Zimbabwe)
  -> Mark as WhatsApp-enabled
```

## What CANNOT Be Done Without Login

- LinkedIn Contact Info section (emails/phones) is never public
- LinkedIn API requires OAuth + approved app
- No open-source tool can extract LinkedIn emails without a logged-in session

## GitHub Projects Found (all need login)

| Project | Stars | Notes |
|---------|-------|-------|
| eliasbiondo/linkedin-mcp-server | ~100 | MCP server, needs LinkedIn session cookie |
| stickerdaniel/linkedin-mcp-server | ~200 | MCP server, uses Selenium with your account |
| initstring/linkedin2username | 1.2k | Needs LinkedIn account |
| Apify LinkedIn Profile Scraper | service | Paid API ($4/1k profiles), no login |
| exa-py (exa.ai) | API | Paid AI search API |

## Recommended Alternative

JoinF API (data.joinf.com) already gives company name + phone numbers directly without any workaround. Use LinkedIn X-ray only when JoinF coverage is insufficient for a specific market.