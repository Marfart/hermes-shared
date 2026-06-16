# og:image Extraction via Playwright

## Why Playwright over curl/urllib

Many news sites (ESPN, Bloomberg, TheStreet, MyAnimeList) block direct HTTP requests with:
- SSL handshake timeouts (ESPN)
- 403 Forbidden (Bloomberg, TheStreet)
- 404 on direct image URLs (Wikipedia thumbnails)
- Redirect to login pages

Playwright's browser engine bypasses all of these because it looks like a real user.

## Extraction Pattern

```python
# Step 1: Navigate to the article page
await page.goto(url, wait_until='domcontentloaded')

# Step 2: Extract og:image URL
og_image = await page.evaluate('''
    () => {
        const meta = document.querySelector('meta[property="og:image"]');
        return meta ? meta.content : null;
    }
''')

# Step 3: Fallback to twitter:image if og:image missing
if not og_image:
    og_image = await page.evaluate('''
        () => {
            const meta = document.querySelector('meta[name="twitter:image"]');
            return meta ? meta.content : null;
        }
    ''')

# Step 4: Download the image (use curl --noproxy to bypass proxy)
import subprocess
subprocess.run(['curl', '--noproxy', '*', '-s', '-o', '/tmp/img.jpg', og_image])
```

## Known Working Sites

| Site | og:image Reliability | Notes |
|------|---------------------|-------|
| Apple Newsroom | ✅ Always present | 1200x630, clean |
| Euronews | ✅ Always present | 1200x675 |
| TheStreet | ✅ Present | Large image, good quality |
| ESPN | ✅ Present (via Playwright) | SSL timeout on direct curl |
| MyAnimeList | ⚠️ Returns icon | Must extract actual anime image from page DOM, not og:image |
| Wikipedia | ❌ Unreliable | Thumbnail URLs are fragile, use picsum fallback |
| Bloomberg | ❌ 403 | Use Playwright to bypass |
| The Guardian | ✅ Present | Good quality |

## Fallback Chain

1. Playwright → evaluate og:image → download with curl --noproxy
2. If Playwright unavailable: curl --noproxy to article URL, regex extract og:image
3. If no og:image found: picsum.photos with semantic seed
4. Never use a random/generic image as fallback
