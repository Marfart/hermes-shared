# Google Custom Search API for LinkedIn Company Discovery

## Setup (free, 100 queries/day)

1. Go to https://developers.google.com/custom-search/v1/overview
2. Click "Get a Key" → Create new project → Get API key
3. Go to https://programmablesearchengine.google.com/ → Create
   - Sites to search: `linkedin.com/company/*`
   - Get Search Engine ID (cx)

## Install
```bash
pip install google-api-python-client
```

## Usage
```python
from googleapiclient.discovery import build

API_KEY = "your_key_here"
CX = "your_search_engine_id_here"

service = build("customsearch", "v1", developerKey=API_KEY)

# Search LinkedIn company pages
result = service.cse().list(
    q='"system integrator" "South Africa"',
    cx=CX,
    num=10,
).execute()

for item in result.get("items", []):
    print(item["title"], item["link"], item.get("snippet", "")[:100])
```

## Query Patterns for B2B Lead Generation

| Target | Query Pattern |
|--------|---------------|
| System integrators by country | `site:linkedin.com/company "system integrator" "South Africa"` |
| PLC/SCADA companies | `site:linkedin.com/company PLC OR SCADA OR "industrial automation"` |
| IIoT companies | `site:linkedin.com/company IIoT OR "industrial IoT" OR "edge computing"` |
| Energy monitoring | `site:linkedin.com/company "solar" OR "energy monitoring" OR "utility automation"` |
| African market | `site:linkedin.com/company "South Africa" OR "Kenya" OR "Nigeria" industrial automation` |

## Limitations
- 100 free queries/day (each query returns up to 10 results)
- Only finds company LinkedIn pages (not employee profiles)
- LinkedIn restricts what non-logged-in users can see
- For deeper data (employee contacts, posts), you need LinkedIn login + browser automation

## Alternatives if free tier not enough
- SerpApi: 100 free queries/month, then $50/mo for 5,000
- Apify LinkedIn Scraper: $5 free credit/mo on signup