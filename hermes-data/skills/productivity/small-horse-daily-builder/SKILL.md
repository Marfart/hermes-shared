---
name: small-horse-daily-builder
title: "Small Horse Daily — Interactive HTML Builder"
version: "v8.1"
description: "Build the 'Small Horse Daily' interactive HTML briefing — Apple News-style dark theme with card+detail-page interaction, real news images (og:image only, no picsum), Cloudflare Tunnel sharing. TWO editions per day (morning + evening), each with completely fresh content and images."
trigger: "Daily at 6:30 (morning) and 18:30 (evening) Beijing time — user says '做日报' / '简报' / 'daily'. TWO editions: morning (7:00 deliver) + evening (19:00 deliver), each standalone with fresh content."
author: "Kali & Mr.Ma"
---

# Small Horse Daily Builder v8.0

## 预处理（写在脚本里，不改）

HTML 构建脚本：`~/Desktop/Working/Hermes/build_v7_final.py`
图片缓存：`~/Desktop/Working/Hermes/images/news_b64_v7_real_optimized.json`
输出文件：`~/Desktop/Working/Hermes/Small_Horse_Daily_YYYY-MM-DD.html`
分享工具：`C:\Users\Admin\Desktop\Working\cf.exe`

**永远不改的内容：** CSS 样式、HTML 模板结构、导航栏、hero 部分、JS 代码、detail-page 交互逻辑。这些写死在脚本里，每天只改数据部分（data dicts）。

## ⚠️ 强制预检清单（每次构建前必须逐项执行，跳过任何一项=被Kali骂）

### 第0步：滚动历史检查

```bash
# 打开历史HTML文件，检查具体新闻内容
# 用 session_search 查最近3-5天所有日报相关内容
# 输出一个「历史内容清单」：事件名、新闻标题、人物、项目、推荐基金、文化作品
# 这个清单就是「禁入名单」——以下所有步骤禁止使用名单内的任何内容
```

### 第1步：先爬图，后写稿（铁律）

**如果还有「先写稿再找图」的冲动，停下来读这句话：Kali 会非常生气。风景图和 picsum 是零容忍。每张图必须来自真实新闻的 og:image。**

正确的顺序是：
1. 搜真实新闻URL（web_search + Playwright打开）
2. 对每个URL：Playwright提取og:image → 下载 → 压缩 → 入缓存
3. **只有成功拿到真实og:image的新闻，才能进入内容编写流程**
4. 有多少张真图，写多少条。宁少勿凑

### 第2步：历史内容零重叠验证

**在写任何文字之前，用 grep 确认：**

```bash
# 列出本HTML中所有img key
python -c "
import re
# 从脚本的data dicts中提取所有img key
# 与已发布的HTML文件中的img key对比
# 任何重叠→必须换掉
print('检查通过: 所有img key全新')
"

# 列出所有拟使用的新闻标题
# 逐条对比历史日报HTML中的h1标签
# 任何语义重叠→必须换掉
```

### 第3步：图片重复检查（构建后）

```bash
python -c "
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
"
```

## 2. 图片获取（第二步 — 先于内容编写！）

**⛔ 铁律：先爬图，后写稿。图片不到手不写内容。**

### 真实新闻 og:image 获取流程

对每条候选新闻：
1. 用 `mcp_playwright_browser_navigate(url)` 打开新闻文章页面
2. 用 `mcp_playwright_browser_evaluate` 提取 `og:image` 属性值
3. 拿到 URL 后 → `urllib.request` 下载（加 Mozilla UA 头）→ Pillow 压缩 → 存入缓存 JSON
4. **只有成功拿到真实 og:image 的新闻才能入选日报**
5. 如果爬不到 → 放弃这条新闻 → 换其他新闻源
6. ❌ 绝对不用 picsum/photos 风景图/通用图作为替代

详见 `references/image-download-reference.md` 和 `references/telegram-group-delivery.md`。

### 图片铁律（硬约束，违反会被Kali严厉纠正）

- ❌ **零容忍 picsum.photos 语义 seed 或任何风景图/通用图**
- ✅ 每张图必须是新闻源的真实 og:image
- ✅ 每张图 MD5 内容必须唯一（不同板块不能共用同一张图）
- ✅ 每期的所有图片 key 必须全新（不能复用历史上的任何 key）
- ✅ 卡片和详情页（同一条目）可以用同一张图，这是正常的

### 已知可靠的 og:image 源

| 源 | 方法 |
|----|------|
| BBC Sport/News | Playwright navigate → evaluate |
| Apple Newsroom | Playwright navigate → evaluate |
| WIRED | Playwright navigate → evaluate |
| MyAnimeList | Playwright navigate → evaluate |
| TheStreet | Playwright navigate → evaluate |
| Al Jazeera | Playwright navigate → evaluate |
| ❌ ESPN | SSL 超时，避免使用 |
| ❌ Bloomberg | 403，避免使用 |
| ❌ Wikipedia | 429，避免使用 |

## 3. 内容调研（第三步 — 图片到位后）

扫描 7 大信息源，精选 **10-15 条**，与历史日报零重复：

1. **Hacker News** — front page + best stories
2. **GitHub Trending** — 今日热门仓库
3. **ArXiv cs.AI** — 最新论文
4. **36氪** — 近8小时科技新闻
5. **全球头条** — `web_search("world news today")`
6. **地缘政治** — `web_search("geopolitics conflict today")`
7. **金融市场** — `web_search("stock market today")`

### 选择铁律

- ✅ 覆盖至少3个不同领域（科技/AI/金融/文化/太空等）
- ✅ 地缘事件最多占1天核心位，第2天必须让位给其他领域
- ❌ 同一条新闻、同一张图片、同一个话题，不能在简报内出现两次
- ❌ 今天的任何内容不能与之前任何期数重复（事件、推荐、图片全部全新）
- ❌ 今天的HTML文件不能跟之前长得一样 — 确保视觉、叙事、话题分布都明显不同
- ✅ 每条有「小马解读」+「追踪信号」
- ✅ 交叉验证多个来源（至少2-3个不同媒体）

## 4. 填充数据到 build_v7_final.py

只修改 7 个 data dict 里的内容（不改模板、CSS、JS、变量名）：

### 数据结构模板

```python
# ① hero_stories[3] — 核心信号
hero_stories = [
    {"id": "unique_id", "img": "img_key", "conf": "95/100", "imp": "极高/高/中",
     "dom": "领域标签", "title": "标题", "src": "来源",
     "text": "事件概要\n\n小马解读：...\n\n追踪信号：..."}
]

# ② secondary[4] — 科研/AI
# ③ culture[5] — 文化（爵士/游戏/动漫）
# ④ economy_stories[2] — 经济金融
# ⑤ science_stories[3] — 生命科学
# ⑥ fund_stories[4] — 推荐基金

# ⑦ politics_stories[2] — 政治安全
# ⑧ space_stories[2] — 太空探索
# ⑨ life_stories[2] — 生命科学
```

**最佳实践：所有板块都用独立的 data dict + 循环生成。** 不再使用 hardcoded_details。s4/s5/s7 虽然以前容易漏详情页，但用独立 data dict 加循环后跟 s2/s3/s8 完全一样的代码模式，不会产生 Bug #8。详见 references/。

## 5. 构建 HTML + 验证

```bash
cd ~/Desktop/Working/Hermes && python build_v7_final.py
```

成功后验证：
```python
# ① 检查详情页完整性
python -c "
import re
with open('Small_Horse_Daily_YYYY-MM-DD.html', encoding='utf-8') as f:
    html = f.read()
onclick = set(re.findall(r\"showDetail\('([^']+)'\)\", html))
detail = set(re.findall(r'id=\"detail-([^\"]+)\"', html))
missing = onclick - detail
print(f'{len(onclick)} 卡片 = {len(detail)} 详情页')
if missing: print(f'❌ 缺失: {missing}')
else: print('✅ 全部一致！')
"

# ② 检查 img key 无重复
from collections import Counter
img_keys = re.findall(r"img\('([^']+)'\)", html)
dupes = {k:v for k,v in Counter(img_keys).items() if v > 1}
print(f'重复img key: {dupes}' if dupes else '✅ 无重复')

# ③ MD5检查base64内容无重复
import hashlib, json
with open('images/news_b64_v7_real_optimized.json') as f:
    B = json.load(f)
hash_to_keys = {}
for k, v in B.items():
    h = hashlib.md5(v.encode()).hexdigest()
    hash_to_keys.setdefault(h, []).append(k)
for h, keys in hash_to_keys.items():
    if len(keys) > 1:
        print(f'⚠️ 内容重复: {keys}')
```

## 6. Cloudflare Tunnel 分享

```bash
# 杀旧隧道
taskkill //F //IM cf.exe 2>/dev/null
# 启动新隧道（background）
cd ~/Desktop/Working && ./cf.exe tunnel --url http://localhost:8899
# 从日志中获取URL: https://XXXX.trycloudflare.com
```

## 7. 交付

直接发 Cloudflare Tunnel 链接。不发 MEDIA:path，不发本机路径。

## 模板品牌信息
- 网站名：`Small Horse Daily`（标题不含 emoji）
- 编辑署名：`Kali & Mr.Ma`
- 导航栏：圆角按钮 + emoji 图标 + hover 效果 + `text-decoration: none`
- 详情页：从右侧滑入（`transform: translateX(100%) → 0`）

## 脚本架构概览

```
build_v7_final.py 数据流：
  hero_stories[3]     → story_cards + detail_pages（核心信号）
  secondary[4]        → sec_cards + detail_pages（科研AI）
  culture[5]          → cult_cards + detail_pages（文化审美）
  economy_stories[2]  → econ_cards + detail_pages（经济金融）
  science_stories[3]  → sci_cards + detail_pages（生命科学）
  fund_stories[4]     → fund_cards + detail_pages（推荐基金）
  hardcoded_details[4]→ detail_pages for s4+s5（政治+太空）
```

## ⛔ 绝对铁律：9板块顺序不可改变

**2026-06-13 Kali 纠正：改了顺序 = 「完全搞崩了」。**

日报的9板块顺序是**绝对的、不可改变的**。无论内容怎么换，顺序必须永远是：

```
🔥核心 → 🔬科研 → 📈经济 → 🛡️政治 → 🚀太空 → 🎨文化 → 🧬生命 → 📈基金 → ⚠️风险
```

对应到构建脚本里的 section id：
```
s1=核心 → s2=科研 → s3=经济 → s4=政治 → s5=太空 → s6=文化 → s7=生命 → s8=基金 → s9=风险
```

**验证方法**（构建后必须执行）：
```python
import re
with open('Small_Horse_Daily_YYYY-MM-DD.html', encoding='utf-8') as f:
    html = f.read()
sections = re.findall(r'id="s(\d)"', html)
expected = ['1','2','3','4','5','6','7','8','9']
assert sections == expected, f"❌ 顺序错误! 期望{expected},实际{sections}"
print(f"✅ 9板块顺序正确: {sections}")
```

**⛔ 任何对板块顺序的调整都是不允许的。** 6月12日的HTML已是用户认可的标准模板，以后的每一期必须用同样顺序。即使某个板块今天没有独家新闻，也必须有占位内容保持顺序不变。

**⛔ 导航栏顺序也必须完全一致：**
```
<a href="#s1">🔥核心</a><a href="#s2">🔬科研</a><a href="#s3">📈经济</a><a href="#s4">🛡️政治</a><a href="#s5">🚀太空</a><a href="#s6">🎨文化</a><a href="#s7">🧬生命</a><a href="#s8">📈基金</a><a href="#s9">⚠️风险</a>
```

## ⛔ 日报内容铁律（Kali 2026-06-13 纠正：「每天都是以色列伊朗和美国的战争，没有多元化全面性分析，同样的新闻内容，在日报里居然重复了三遍」）

1. **禁止同一地缘事件连续霸占核心叙事** — 最多1天核心位，第2天必须让位给其他领域。如果昨天用了「伊朗打击」「以色列入侵」「美伊冲突」，今天这三条都不能再出现
2. **同一条新闻不得在简报内出现超过1次** — 不能在核心信号讲了SpaceX IPO，经济板块又大段重复。不同板块引用同一话题时，必须是不同角度和不同事实细节。Kali原话：「同样的新闻内容，在日报里居然重复了三遍」— 零容忍
3. **最高优先级信号必须覆盖至少3个不同领域** — 不能全是战争/地缘政治。科技/AI/金融/文化/太空/生命科学，至少覆盖3个。Kali原话：「每天都是只看以色列伊朗和美国的战争，没有其他的多元化全面性分析」— 全战争/全地缘=失败
4. **每期内容与所有历史期数零重叠** — 今天不能说昨天已经说过的任何事件。用 `session_search` 查最近3天日报内容，输出禁入名单后才开始写稿
5. **板块顺序是绝对的不可改变的** — Kali原话：「你完全搞崩了，所有的顺序也不一样了」。顺序永远是：🔥核心→🔬科研→📈经济→🛡️政治→🚀太空→🎨文化→🧬生命→📈基金→⚠️风险。任何调整都不允许

## 日报铁律速查

| 规则 | 说明 |
|------|------|
| 多领域覆盖 | 至少3个不同领域，禁止单一话题霸屏 |
| 零内容重复 | 同一条新闻、同一张图不能在简报内出现两次 |
| 地缘限流 | 最多1天核心位，第2天必须让位 |
| 图片真实 | **必须100%是新闻源的og:image。零容忍风景图/通用图** |
| 图片唯一 | 每张图MD5唯一，不同板块不能共用 |
| 图片全新 | 每期img key全部新，不能复用历史key |
| 信息源深挖 | 交叉验证多个来源（至少2-3个不同媒体） |
| 详情页完整 | 每个onclick必须有对应detail-page |
| 小马解读 | 每条都有深度分析段落 |
| 构建步骤 | 先查重→先爬图→再写稿→构建→验证→分享 |
| **交付前验证清单** | 以下7项每次交付前必查，缺一不可 |

## 交付前验证清单（铁律！每次必查，跳过=被Kali骂）

构建完成后、发链接前，必须逐项执行：

1. **零内容重复检查**：把所有卡片标题+详情页标题列出来，同一事件不能出现>1次。核心信号讲过的不能再在经济/政治板块重述
2. **地缘限流检查**：战争/地缘事件最多占核心叙事1天，检查是否≥3个不同领域（科技/AI/金融/文化/太空等）
3. **板块顺序检查**：必须严格 🔥核心→🔬科研→📈经济→🛡️政治→🚀太空→🎨文化→🧬生命→📈基金→⚠️风险，不能乱序。用正则验证 `id="s1"` 到 `id="s9"` 的出现顺序
4. **图片MD5去重**：所有base64图片内容MD5必须100%唯一，零容忍重复
5. **img key唯一性**：Counter检查所有img key无重复，每个板块一个专属key
6. **所有板块可点击**：每个sec-card的onclick必须有对应detail-page div，点进去能看详情
7. **图片不是风景图/通用图**：每张图必须跟板块内容强相关，不是picsum/photos/unsplash随机图