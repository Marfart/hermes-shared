# Unified Build Pattern for Small Horse Daily HTML

## Overview

The recommended approach for generating the daily HTML is a single `execute_code` call that:
1. Defines all content as structured data arrays
2. Loads/downloads images via a shared `img()` function
3. Generates cards and detail pages via loops
4. Runs verification checks before writing the file

This avoids the complexity of maintaining a separate build script file and ensures consistency across all sections.

## Data Structure Pattern

Every section uses the same data structure:

```python
section_stories = [
    {
        "id": "unique_id",           # Must be unique across ALL sections
        "img": "img_key",            # Must be unique across ALL sections
        "tag": "显示标签",            # e.g. "AI·开源", "生命科学"
        "tc": "tag-orange",          # CSS class: tag-red/purple/blue/green/orange/cyan/pink/gold
        "title": "标题",
        "src": "L1 - Source1/Source2",
        "text": "卡片摘要（~120字）",
        "detail": [                  # Optional — if absent, no detail page
            {"title": "章节标题", "content": "章节内容（3-5句）"},
            {"title": "小马解读", "content": "深度分析..."},
            {"title": "推演链", "content": "A→B→C→D..."},
            {"title": "追踪信号", "content": "①... ②..."}
        ]
    }
]
```

## Image Loading

```python
B = {}  # global cache: key -> data URI

def img(key):
    """Return data URI. Tries local files first, then picsum fallback."""
    if key in B:
        return B[key]
    # Try local files in images/ and root
    for ext in ['.jpg', '.jpeg', '.png', '.webp']:
        for base in [os.path.join(WORK, 'images'), WORK]:
            fpath = os.path.join(base, key + ext)
            if os.path.exists(fpath):
                with open(fpath, 'rb') as f:
                    raw = f.read()
                if len(raw) > 1000:  # skip failed downloads (263 bytes)
                    break
        else:
            continue
        break
    else:
        # picsum fallback
        url = f"https://picsum.photos/seed/{key}/1200/675"
        raw = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': '...'}), timeout=15).read()
    
    # Determine MIME from magic bytes
    # Resize to >=1200px wide if smaller
    # Encode as base64 data URI
    B[key] = f"data:{mime};base64,{b64}"
    return B[key]
```

## Card Generation

```python
def build_card(item):
    text_short = item["text"][:120] + "…" if len(item["text"]) > 120 else item["text"]
    return f'''
<div class="sec-card" onclick="showDetail('{item["id"]}')">
  <div class="sec-card-img"><img src="{img(item["img"])}" alt="{item["title"]}"></div>
  <div class="sec-card-body">
    <span class="tag {item["tc"]}">{item["tag"]}</span>
    <h3 class="sec-card-title">{item["title"]}</h3>
    <p class="sec-card-src">{item.get("src","")}</p>
    <p class="sec-card-text">{text_short}</p>
  </div>
</div>'''
```

## Detail Page Generation

```python
def build_detail(item):
    if "detail" not in item or not item["detail"]:
        return ""
    sections = ""
    for s in item["detail"]:
        sections += f'<h3 style="...">{s["title"]}</h3>\n'
        sections += f'<p style="margin-top:16px;line-height:1.7">{s["content"]}</p>\n'
    return f'''
<div class="detail-page" id="detail-{item["id"]}" style="display:none">
  <div class="detail-hero">...hero image + title + tag...</div>
  <div class="detail-body">
    <button onclick="hideDetail('{item["id"]}')">← 返回</button>
    {sections}
  </div>
</div>'''
```

## Assembly Pattern

```python
# 1. Define all section data arrays
stories = [...]
science_stories = [...]
economy_stories = [...]
politics_stories = [...]
space_stories = [...]
life_stories = [...]
fund_stories = [...]
culture_jazz = [...]
culture_games = [...]
culture_anime = [...]
risk_items = [...]

# 2. Pre-load all images
all_img_keys = [...]  # collect from all data arrays
for k in all_img_keys:
    img(k)

# 3. Build cards and details via loops
all_cards = {}
all_details = ""
for sec_name, items in [("stories", stories), ("science", science_stories), ...]:
    cards = ""
    for item in items:
        cards += build_card(item)
        all_details += build_detail(item)
    all_cards[sec_name] = cards

# 4. Build culture cards separately (use build_cult_card for different styling)
culture_cards = ""
for c in culture_jazz + culture_games + culture_anime:
    culture_cards += build_cult_card(c)
    all_details += build_detail(c)

# 5. Build hero, market table, risk HTML
# 6. Assemble full HTML string
# 7. Write file
```

## Verification (MUST run after generation)

```python
import re
from collections import Counter

# 1. onclick vs detail-page matching
onclick_ids = set(re.findall(r"showDetail\('([^']+)'\)", html))
detail_ids = set(re.findall(r'id="detail-([^"]+)"', html))
assert not (onclick_ids - detail_ids), f"Missing detail pages: {onclick_ids - detail_ids}"

# 2. img key uniqueness
refs = re.findall(r'"img":\s*"(\w+)"', html)
c = Counter(refs)
dupes = {k: v for k, v in c.items() if v > 1}
assert not dupes, f"DUPLICATE IMG KEYS: {dupes}"

# 3. MD5 image content uniqueness
import hashlib, base64
b64_images = re.findall(r'data:image/[^;]+;base64,([^"\'\\]+)', html)
seen = {}
for b64 in b64_images:
    raw = base64.b64decode(b64)
    h = hashlib.md5(raw).hexdigest()
    assert h not in seen, f"DUPLICATE MD5: {h}"
    seen[h] = True
```

## Section Order in HTML

```
nav: 🔥核心 🔬科研 📈经济 🛡️政治 🚀太空 🎨文化 🧬生命 📈基金 ⚠️风险
hero → #core → #science → #economy → #politics → #space → #life → #culture → #funds → #risk → detail_pages → footer
```

## ⚠️ F-string CSS Brace Conflict (Known Pitfall)

When embedding CSS inside Python f-strings, curly braces `{` and `}` from CSS rules conflict with f-string interpolation syntax. **This WILL cause SyntaxError.**

### Workaround A: String concatenation (for execute_code)
```python
# ❌ WON'T WORK — CSS curly braces break f-string
html = f'''<style>...nav a:hover{color:#fff}...</style>'''

# ✅ WORKS — build HTML via string concatenation
html = '<style>\n'
html += 'nav a:hover{color:#fff}\n'
html += '</style>\n'
# Then use .join() or explicit + for dynamic parts
```

### Workaround B: Write build script to .py file (RECOMMENDED for complex HTML)
For daily briefs with many sections (15+ cards), write the build logic to a standalone Python file and `python build_brief.py` via terminal.

**Build script pattern (avoiding f-strings entirely):**
```python
# Use string concatenation with + and .join()
src = img(s["img"])
body = ''.join([
    '<div class="sec-card">',
    '<img src="', src, '" alt="...">',
    '<h3>', s["title"], '</h3>',
    '</div>'
])

# Use .format() for simple templates
# Never use f-strings that contain CSS or JS
```

**Verification:**
```python
import re
onclick_ids = set(re.findall(r"showDetail\('([^']+)'\)", html))
detail_ids = set(re.findall(r'id="detail-([^"]+)"', html))
assert not (onclick_ids - detail_ids)
```

## HTTP Server Zombie Cleanup (Before starting)
Port 8899 is often left occupied by crashed HTTP servers. Clean before starting:
```bash
# Kill all processes on port 8899
for pid in $(netstat -ano | grep 8899 | awk '{print $5}' | grep -E '^[0-9]+$' | sort -u); do
  taskkill //F //PID $pid 2>/dev/null
done
sleep 2
# Start fresh
cd /c/Users/Admin/Desktop/Working/Hermes && python -m http.server 8899 --bind 0.0.0.0
```

## Full Build Flow (proven in production)
1. `execute_code` block for image download + data definitions
2. Write build script to `.py` file (avoids f-string issues with HTML/CSS)
3. Run `python build_brief.py` via terminal
4. Start HTTP server → verify 200
5. Start Cloudflare Tunnel → wait 15s → verify 200 via tunnel
6. Log the tunnel URL for user delivery

## Key Constraints

- Every `"img"` key must be unique across ALL sections (one section = one exclusive key)
- Every `"id"` must be unique across ALL sections
- Every section must have cards with the same interactive pattern (click → detail page)
- Economy section must have depth analysis cards + market table, never just a table
- Life science section must have科普 (what is X?) + 小马解读 (why important?)
- Fund section must have 推荐理由 + 深度分析 + 风险提示 + 配置建议 (仓位%)
- Culture section must have detailed artist background + sound description (metaphors) + recommended tracks
