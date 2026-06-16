# 图片下载参考 — Small Horse Daily

## 🚨 铁律（Kali 2026-06-13纠正，违反会被严厉批评）

1. **每张配图必须是新闻源的真实 og:image。零容忍 picsum/photos 风景图/通用图。**
2. **先爬图，后写稿。** 只有爬到了真实 og:image 的新闻才能入选日报。有多少张真实图就写多少条新闻，宁缺毋滥。
3. **每张图 MD5 内容必须唯一。** 不同板块不能共用同一张图（卡片和详情页同条目可以用同一张，这是正常）。
4. **每期的所有图片 key 必须全新。** 不能复用任何历史期数的 img key。

## ✅ 正确工作流（经过实战验证）

### 第1步：找到真实的新闻文章URL

通过 web_search 或 Google News 找到有真实新闻文章的URL。不要依赖AI生成的内容描述——必须打开真文章。

### 第2步：用 Playwright MCP 提取 og:image

```text
# 在 Hermes 会话中操作：
mcp_playwright_browser_navigate(url="https://具体的新闻文章URL")

# 注意：URL 必须是完整的文章页（不是列表页/首页）
# 如果返回404/error → 换一个URL
# 如果返回"Checking your connection"（Cloudflare保护）→ 换一个源

mcp_playwright_browser_evaluate(function="() => { 
  const m = document.querySelector('meta[property=\"og:image\"]'); 
  const m2 = document.querySelector('meta[property=\"og:image:secure_url\"]'); 
  const m3 = document.querySelector('meta[name=\"twitter:image\"]'); 
  return (m && m.content) || (m2 && m2.content) || (m3 && m3.content) || ''; 
}")
```

### 第3步：下载并缓存图片

拿到 og:image URL 后，用 urllib.request 下载（必须加 Mozilla UA header）：
```python
import urllib.request, io, base64
from PIL import Image

req = urllib.request.Request(img_url, headers={
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
})
resp = urllib.request.urlopen(req, timeout=20)
img_data = resp.read()
img = Image.open(io.BytesIO(img_data))
if img.mode in ('P', 'RGBA', 'LA'):
    img = img.convert('RGB')
if img.width < 1200:
    ratio = 1200 / img.width
    img = img.resize((1200, int(img.height * ratio)), Image.LANCZOS)
buf = io.BytesIO()
img.save(buf, format='JPEG', quality=85, optimize=True)
b64 = base64.b64encode(buf.getvalue()).decode()
```

### 第4步：只有拿到图了，才能写内容

如果某条新闻爬不到 og:image：
- ❌ **不要用 picsum.photos 语义 seed（这会被Kali严厉批评）**
- ❌ **不要用 Wikipedia SVG/PNG（404/400）**
- ❌ **不要用任何风景图/通用图替代**
- ✅ **放弃这条新闻，换一条能爬到图的新新闻**

## 🔬 已知成功率经过实测的源

| 源 | 方法 | 实测结果 |
|----|------|---------|
| **BBC Sport** (bbc.com/sport/) | Playwright navigate → evaluate `og:image` | ✅ 100% reliable，高清图片 |
| **BBC News** (bbc.com/news/) | Playwright navigate → evaluate `og:image` | ✅ 100% reliable，高清图片 |
| **Apple Newsroom** (apple.com/newsroom/) | Playwright navigate → evaluate `og:image` | ✅ 高清1200x630 |
| **The Verge** (theverge.com) | Playwright navigate → evaluate `og:image` | ✅ 高清图片 |
| **Reuters** (reuters.com) | Playwright navigate → evaluate `og:image:secure_url` | ✅ 注意URL带auth参数，直接下载即可 |
| **MyAnimeList** | Playwright navigate → evaluate 拿 `.seasonal-anime img` src | ✅ WebP/webp格式，需要convert('RGB') |
| **Goldmine Magazine** | Playwright navigate → evaluate `og:image` | ✅ 专辑封面高清图 |
| **WIRED** | Playwright navigate → evaluate `og:image` | ✅ 可靠 |

## ❌ 已知不可靠的源（避免使用）

| 源 | 原因 |
|----|------|
| **ESPN** | SSL handshake timeout（中国网络） |
| **Bloomberg** | 403 Forbidden |
| **Wikipedia** | 图片URL404/400（CDN限制） |
| **phys.org** | Cloudflare challenge |
| **Al Jazeera** | 404（URL不稳定） |
| **CNN** | Error page（中国网络被墙） |

## 🔄 备用方案：当主源不可用时

如果上述可靠源都找不到合适新闻的图，可以用 **web_search** 找同样话题但来自可靠源的报道。
比如BBC、The Verge、TechCrunch通常会报道同样的世界事件。

## 压缩参数（固定）

```python
# 最小宽度: 1200px
# 格式: JPEG
# 质量: 85
# 优化: True
# PAL/RGBA/LA模式要先convert('RGB')
```

## 去重验证（构建后必须执行）

```python
import hashlib, json, base64
with open('images/news_b64_v7_real_optimized.json') as f:
    B = json.load(f)
hash_to_keys = {}
for k, v in B.items():
    raw = base64.b64decode(v) if isinstance(v, str) else v
    h = hashlib.md5(raw if isinstance(raw, bytes) else raw.encode()).hexdigest()
    hash_to_keys.setdefault(h, []).append(k)
for h, keys in hash_to_keys.items():
    if len(keys) > 1:
        print(f'❌ 内容重复: {keys}')
```

## 缓存文件

- 路径: `~/Desktop/Working/Hermes/images/news_b64_v7_real_optimized.json`
- 每次日报必须用全新的 img key，不能复用历史上的任何 key
- 新图直接 append 到现有JSON中（JSON会增长，不会丢失旧图——img key做隔离）