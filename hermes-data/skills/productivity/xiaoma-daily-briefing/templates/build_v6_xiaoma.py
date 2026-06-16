#!/usr/bin/env python3
"""Build v6.0 小马日报 - App-style interactive HTML with rich detail pages

Key v6 features vs v5:
- Brand: 「小马日报 🐴✨」(not "Hermes Intelligence")
- Credit: 「编辑：Kali & 小马」 in Hero + Footer
- Morning/Evening distinction: 小马早报 🌅 / 小马晚报 🌙
- Rich detail pages: 3-4 sections per story (事件概要 + 小马解读 + 推演链 + 追踪信号)
- ALL sections have depth content (not just news): 科研→科普+趋势, 文化→感受+审美, 太空→科普+商业逻辑
- Secondary + Culture cards also have expanded detail_content (150+ chars)
- Images: 100% unique, MD5-verified, no duplicates. Use picsum.photos/seed/UNIQUE_KEY as fallback
- Image cache: news_b64_v6.json (NOT v5)

CRITICAL RULES:
1. Every image must be unique - verify with MD5 after generation
2. Every section must have depth (not just news): 小马解读/小马觉得/小马感受/小马科普
3. Zero content duplication across the entire briefing

Usage:
1. Download unique images for each topic (picsum.photos/seed/TOPIC/800/600 as fallback)
2. Save to news_b64_v6.json (key -> base64)
3. MD5 verify all images are unique before proceeding
4. Edit stories[], secondary[], culture[] with today's content
5. Set edition = "早报" or "晚报"
6. Run: python build_v6_xiaoma.py
7. Output: ~/Desktop/Working/Hermes/小马日报_YYYY-MM-DD.html

Image uniqueness verification (MUST run after generating):
```python
import hashlib, base64
with open('news_b64_v6.json') as f:
    B = json.load(f)
seen = {}
for name, b64 in B.items():
    raw = base64.b64decode(b64)
    h = hashlib.md5(raw).hexdigest()
    if h in seen:
        print(f"⚠️ DUPLICATE: {name} = {seen[h]}")
    else:
        seen[h] = name
print(f"Images: {len(B)} total, {len(seen)} unique")
# If any duplicates found, replace with different picsum seed immediately
```

Requirements: Python 3.7+ (no external deps)
"""

import json, os, hashlib, base64
from datetime import datetime

# === CONFIG ===
EDITION = "早报"  # Change to "晚报" for evening
DATE_STR = datetime.now().strftime("%Y-%m-%d")
DATE_CN = datetime.now().strftime("%Y年%m月%d日")

b64_path = os.path.expanduser("~/Desktop/Working/Hermes/images/news_b64_v6.json")
with open(b64_path, 'r') as f:
    B = json.load(f)

# === VERIFY IMAGE UNIQUENESS (CRITICAL - Kali's #1 complaint) ===
seen = {}
duplicates = []
for name, b64 in B.items():
    raw = base64.b64decode(b64)
    h = hashlib.md5(raw).hexdigest()
    if h in seen:
        duplicates.append(f"{name} = {seen[h]}")
    else:
        seen[h] = name
if duplicates:
    print(f"⚠️ DUPLICATE IMAGES FOUND ({len(duplicates)}):")
    for d in duplicates:
        print(f"  {d}")
    print("FIX THESE BEFORE GENERATING HTML!")
else:
    print(f"✅ All {len(B)} images verified unique")

def img(name):
    return B.get(name, B.get('hero_banner', ''))

# === DATA STRUCTURES ===
# Each story: id, img, tags, tc, title, sub, src, conf, imp, dom, risk, rc,
#   card_excerpt, sections: [{h, cls?, label?, t}]

stories = [
    # FILL IN TODAY'S STORIES
    # EVERY story must have sections with depth content:
    # - 事件概要 (plain section)
    # - 小马解读 (blue insight box)
    # - 逻辑推演 (orange insight box)
    # - 追踪信号 (blue insight box, for top stories)
]

secondary = [
    # EVERY secondary story must have "text" field with 150+ chars of
    # 小马觉得/解读 content, NOT just a one-line summary
]

culture = [
    # EVERY culture item must have "detail" field with 200+ chars containing:
    # - 小马感受 (personal reaction)
    # - 推荐曲目/推荐理由 (for music)
    # - 趋势判断 (for games/tech)
    # - 科普段落 (for science)
]

# === HTML GENERATION ===
# Copy the full HTML template from the production build_v6_xiaoma.py
# Key CSS: dark theme, Apple-style cards, detail-page slide-in, insight boxes
# Key JS: showDetail(id) / hideDetail(id) for card→detail page transitions

output = os.path.expanduser(f"~/Desktop/Working/Hermes/小马日报_{DATE_STR}.html")
# ... (full HTML generation code here - copy from production script)

print(f"HTML saved: {output}")
print(f"Size: {os.path.getsize(output)/1024/1024:.1f}MB")