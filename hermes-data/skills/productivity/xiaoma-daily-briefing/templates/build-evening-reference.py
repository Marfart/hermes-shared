"""
Small Horse Daily Build Script — Evening Edition Reference
Session: 2026-06-13 18:25 (晚报)

This build script demonstrates the proven production flow:
1. String concatenation (not f-strings) to avoid CSS brace conflicts
2. Image loading via execute_code first, then build.py via terminal
3. All verification passes before delivery

Directory: C:/Users/Admin/Desktop/Working/Hermes/
Output: Small_Horse_Daily_YYYY-MM-DD_evening.html
"""
import json, base64, hashlib, re

# === IMAGE LOADING ===
# Images pre-loaded via execute_code → saved to JSON cache
# Then loaded in build script:
cache_path = "C:/Users/Admin/Desktop/Working/Hermes/images/news_b64_evening_jun13.json"
with open(cache_path) as f:
    B = json.load(f)

def img(key):
    b = B.get(key)
    if not b:
        return ""
    raw = base64.b64decode(b)
    # WebP detection via magic bytes
    if raw[:4] == b'RIFF' and raw[8:12] == b'WEBP':
        return "data:image/webp;base64," + b
    return "data:image/jpeg;base64," + b

# === DATA STRUCTURE (same across all sections) ===
stories = [
    {
        "id": "unique_id",       # must be globally unique
        "img": "img_key",        # must be globally unique
        "tag": "标签文字",
        "tc": "tag-class",       # tag-red/purple/blue/orange/cyan/green/pink/gold
        "title": "标题",
        "src": "L1 - Source/Source",
        "text": ["段落1...", "段落2...", "▸ 推演链...", "小马解读..."]
    }
]

# === CARD GENERATION (string concat — NO f-strings with CSS) ===
def make_card(s):
    src = img(s["img"])
    paras = ''.join('<p style="margin-top:16px">' + p + '</p>' for p in s["text"])
    card = ''.join([
        '<div class="sec-card" onclick="showDetail(\'', s["id"], '\')">',
        '<div class="card-img"><img src="', src, '" alt="', s["title"], '"></div>',
        '<div class="card-body">',
        '<span class="tag ', s["tc"], '">', s["tag"], '</span>',
        '<h3>', s["title"], '</h3>',
        '<p class="src">', s["src"], '</p>',
        '<p class="summary">', s["text"][0][:120], '…</p>',
        '</div></div>'
    ])
    detail = ''.join([
        '<div id="detail-', s["id"], '" class="detail-page">',
        '<div class="detail-hero"><img src="', src, '" alt="', s["title"], '"></div>',
        '<div class="detail-body">',
        '<span class="tag ', s["tc"], '">', s["tag"], '</span>',
        '<h2>', s["title"], '</h2>',
        '<p class="src">', s["src"], '</p>',
        paras,
        '<button class="close-btn" onclick="hideDetail(\'', s["id"], '\')">关闭 ✕</button>',
        '</div></div>'
    ])
    return card, detail

# === VERIFICATION (MUST RUN BEFORE DELIVERY) ===
# 1. onclick counts must match detail-page counts
onclick_ids = set(re.findall(r"showDetail\('([^']+)'\)", html))
detail_ids = set(re.findall(r'id="detail-([^"]+)"', html))
assert not (onclick_ids - detail_ids), f"Missing: {onclick_ids - detail_ids}"

# 2. Section order must be s1→s2→s3→s4→s5→s6→s7→s8→s9
sections = re.findall(r'id="s(\d)"', html)
assert sections == ['1','2','3','4','5','6','7','8','9']

# 3. Image content uniqueness (MD5)
seen = {}
for name, b64 in B.items():
    raw = base64.b64decode(b64)
    h = hashlib.md5(raw).hexdigest()
    assert h not in seen, f"Duplicate: {name} = {seen[h]}"
    seen[h] = name