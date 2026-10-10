# Feed Format Quirks — Field Notes

## CDATA titles in Atom (The Verge)
`<title type="html"><![CDATA[Title here]]></title>` — ElementTree `.text` returns `None` for CDATA.
**Fix:** Use regex: `re.findall(r'<title[^>]*><!\[CDATA\[([^\]]+)\]\]></title>', content)`

## Atom link index offset
First 2 `<link>` elements are feed-level (home page + self-reference). Entry links start at index 2.
```python
feed_link_count = 2
for i, t in enumerate(titles):
    link = links[i + feed_link_count] if i + feed_link_count < len(links) else ''
```

## Blogger RSS (Free Jazz Collective)
- Uses `<item>` inside `<channel>` (standard RSS 2.0)
- Full article HTML is in `<description>` — must clean with `re.sub(r'<[^>]+>', ' ', desc)`
- Tags are `<category>` elements with `domain="http://www.blogger.com/atom/ns#"` — these cover genres like "Avant-garde jazz", "Solo Sax", "Piano Trio", "Free fusion", "Nu Jazz", "Doom jazz"
- Contains media: `<media:thumbnail>` and `<media:content>` for cover art
- Very reliable Blogger platform — returns stable content

## arXiv RSS
- Huge feeds: 100-800KB, 30-100+ items per tick
- Contains `<description>` with full abstract text
- CS.AI = AI papers, CS.LG = ML papers, CS.CV = Computer vision, CS.CL = NLP
- Physics is massive (~334KB) — broadest scope
- Very reliable — always returns 200

## Nature RSS
**Dead.** Returns empty content (0 items) consistently. The `nature.com/nature.rss` URL redirects but produces no parseable items. May need authentication or have changed feed format. Do not use.

## PNAS RSS
Works well — returns ~30-40 current articles. Standard RSS 2.0 format.

## Bloomberg RSS
- Feed works (returns RSS items)
- Individual article pages return **403** when fetched by agents (anti-bot protection)
- Cron agent should skip article reading gracefully for Bloomberg links — report title-level summary only

## MarketWatch RSS
- Feed works
- Individual article pages blocked by **robots.txt** (`User-agent: * Disallow: /`)
- Cron agent should skip gracefully

## Google AI Blog (blog.google/technology/ai/rss/)
- This is the CORRECT feed URL for DeepMind/Google AI updates
- NOT deepmind.google/discover/blog/rss.xml (returns 404)
- Content is a mix of: AI model releases, product features, research announcements
- May include non-AI articles (thrifting tips, shopping features) — agent should filter

## The Next Web (TNW)
URL: `thenextweb.com/rss/index.xml` → redirects to `thenextweb.com/feed`
Returns 200 consistently. Good depth articles on tech trends.

## VentureBeat AI
URL: `venturebeat.com/category/ai/feed/`
Good mix of: AI startup funding, enterprise AI deployment, industry analysis.

## IEEE Spectrum
URL: `feeds.feedburner.com/IeeeSpectrum`
Engineering-focused. Includes career advice articles alongside tech reporting — agent should filter.

## ScienceDaily
URL: `sciencedaily.com/rss/all.xml`
Aggregates press releases from 100+ research institutions. Very high volume (~60 items/tick).
Broad scope: biology, health, physics, environment, tech.

## New Scientist
URL: `newscientist.com/feed/home/`
100 items/tick. Covers science news + quirky finds. Good for "wow" headlines.

## Quanta Magazine
URL: `quantamagazine.org/feed/`
Deep science reporting (math, physics, computer science, biology).
Lower volume (~5 items/tick) but highest quality per article.

## NASA RSS
URL: `nasa.gov/rss/dyn/breaking_news.rss`
Official NASA press releases. Standard RSS 2.0.

## Space.com
URL: `space.com/feeds/all`
Space exploration news. Standard RSS 2.0.

## SpaceNews
URL: `spacenews.com/feed/`
Space industry + policy. Standard RSS 2.0.

## Dead Feeds (2026-06-10 test)
| Feed | Problem |
|------|---------|
| openai.com/blog/rss/ | 403 Cloudflare |
| deepmind.google/discover/blog/rss.xml | 404 (moved to blog.google/...) |
| research.google/blog/rss.xml | 404 |
| ai.meta.com/blog/rss.xml | 404 |
| wired.com/tag/artificial-intelligence/feed/ | Returns HTML not RSS |
| phys.org/rss-feed/technology/technology.xml | 000 timeout |
| rss.sciam.com/ScientificAmerican-Global | 000 timeout |
| fiercebiotech.com/rss/biotech.xml | 403 |
| biorxiv.org/rss | 403 |
| plos.org/rss/?feed=plosbiology | 404 |
| daily.bandcamp.com/feed | 404 |
| pitchfork.com/rss/reviews/albums/ | 404 (returns HTML) |
| myanimelist.net/rss/news.xml | Returns HTML not RSS |