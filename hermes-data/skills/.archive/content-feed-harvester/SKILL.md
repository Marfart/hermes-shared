---
name: content-feed-harvester
description: "RSS/Atom feed harvesting with deduplication, negative keyword filtering, and cron-based agent-mode delivery. Supports 40+ curated sources across AI research, frontier science, gaming/anime, jazz/music, finance, policy, space, and culture. Delivers Chinese global intelligence briefs twice daily (7am/7pm)."
tags:
  - rss
  - feed
  - content-aggregation
  - cron
  - chinese-briefing
  - global-intelligence
  - jazz
  - ai-research
  - science
  - deduplication
  - 5-layer-architecture
version: 8.0.0
---

# Content Feed Harvester v8 — Global Intelligence System

A reusable global intelligence system collecting from 40+ RSS/Atom feeds, reading articles, and delivering **Chinese conversational briefs** via cron. Runs **twice daily (7am/7pm)** in agent mode.

## ⚠️ MODE DECISION

| Mode | Cost | When | Output |
|------|------|------|--------|
| **Agent mode (LLM)** | ~10-15k tokens/run | This user (Kali) | Chinese conversational intelligence briefing |
| **no_agent (script)** | Zero tokens | Headline-only users | Title dumps only |

**For this user (Kali): ALWAYS use Agent mode.** She explicitly rejected headline/title-only output.

## 🧠 User Preferences

### Output format (most-corrected rules)
- ✅ **Chinese conversational paragraphs** — explain what happened in natural Chinese
- ✅ **生动活泼** — lively/cute tone (塔奇克马/小马 style), with kaomoji (๑>ᴗ<๑)
- ✅ **Deep read first** — READ every article. Kali said: "你先去至少看20min的信息源再发"
- ✅ **ALL categories every tick** — "是都要发，每个里面抽两个你觉得最有意思的"
- ✅ **Cross-domain connection** — connect AI↔bio, energy↔geopolitics, regulation↔capital flows
- ❌ No bare English title dumps
- ❌ No headline-only bullets without explanation
- ❌ No URL links in output
- ❌ Don't skip categories (previous bug: 文化与审美太少)

### Item selection quality
- **Gaming** — pick REAL releases/announcements/trailers. Skip: guides, roster updates, patch notes, cosmetics, sales deals
- **Anime** — pick actual new seasons/premieres/casts. Skip: Pokémon game DLC, manga chapter endings, merchandise
- **Music** — pick new album releases/singles/tours. Skip: legal cases, industry politics, personal drama

### Music taste hierarchy
1. 🥇 **Jazz** — favorite. Free jazz, avant-garde, spiritual, soul jazz. Always include genre+background+sound description
2. Trip-hop (吹泡)
3. Ethereal wave (仙音)
4. Darkwave (暗潮)
5. Shoegaze / Dream pop (盯鞋)

## 🌐 5-Layer Source Architecture

Every source classified by layer. Default priority L1 > L2 > L3 > L4 > L5.

| Layer | Name | Examples |
|:-----:|------|----------|
| L1 | 原始发布层 | arXiv, Nature, Cell, Fed, CISA, EC, IPCC, WHO, NVIDIA blog, Studio blogs |
| L2 | 专家解释层 | MIT Tech Review, Quanta, Aeon, IEEE Spectrum, think tanks |
| L3 | 聚合发现层 | Hacker News, GitHub Trending |
| L4 | 实时信号层 | Markets, prices, social media, satellite data |
| L5 | 媒体报道层 | Bloomberg, MarketWatch (RSS used as L1 for headlines) |

## 📋 Assessment Criteria (100 points)

| Criterion | Score | Question |
|-----------|:-----:|----------|
| 源头性 Source originality | 20 | L1 first-hand? |
| 新颖性 Novelty | 20 | New info? |
| 影响力 Impact | 20 | Changes tech/capital/policy/society? |
| 稀缺性 Scarcity | 15 | Most people missing it? |
| 可验证性 Verifiability | 10 | Data/paper/official backing? |
| 时间敏感性 Time sensitivity | 10 | Needs immediate attention? |
| 跨领域价值 Cross-domain value | 5 | Connects multiple domains? |

**Thresholds**: 90-100=立即关注 / 80-89=高价值 / 70-79=跟踪 / 60-69=背景 / <60=忽略

## 📡 40+ Source Architecture (v8)

### 🧠 AI Research & Lab Updates (L1)
- blog.google/technology/ai/rss/ — Google AI/DeepMind
- venturebeat.com/category/ai/feed/ — VentureBeat AI
- techcrunch.com/feed/ — TechCrunch startups
- thenextweb.com/rss/index.xml — TNW tech analysis
- blogs.nvidia.com/feed/ — NVIDIA official
- huggingface.co/blog/feed.xml — HuggingFace (797 items!)
- w3.org/blog/news/feed/ — W3C standards

### 📄 arXiv Multi-Layer Papers (L1)
- cs.AI / cs.LG / cs.CL / cs.CV / cs.CR
- quant-ph / astro-ph / q-fin / stat.ML / econ

### 🔬 Frontier Science (L1+L2)
- MIT Tech Review (AI + general)
- ScienceDaily, Quanta Magazine, New Scientist
- Nature, Cell, Lancet, NEJM, PNAS (top journals)
- arXiv Physics, IEEE Spectrum

### 🌌 Space (L1)
- NASA, Space.com, SpaceNews

### 🌍 Policy/Climate/Security (L1 — NEW in v8)
- IPCC, UN OCHA, EU Commission, CISA
- WHO, NOAA, Federal Register
- Federal Reserve (speeches + papers), ECB

### 🔍 L3 Aggregation (NEW in v8)
- Hacker News frontpage (hnrss.org)
- Cloudflare blog

### 🎨 Culture (NEW in v8)
- Aeon.co — philosophy/culture/ideas
- TED Talks blog

### 🎮 Game / 🌸 Anime / 🎷 Jazz / 🎵 Music
- Eurogamer (games), ANN (anime), Free Jazz Collective, Stereogum

### 💰 Finance
- Fed press, IMF, Bloomberg, MarketWatch

### ⚡ General Tech
- Ars Technica

### Dead/Blocked (tested — do not use)
| Source | Reason |
|--------|--------|
| OpenAI blog/rss | 403 Cloudflare |
| DeepMind discover blog | 404 → use blog.google/technology/ai/rss/ |
| Meta AI blog | 404 |
| WIRED AI tag | HTML, not RSS |
| Phys.org | timeout |
| Fierce Biotech | 403 |
| bioRxiv | 403 |

## 📋 Briefing Format (ALL 7 sections — never skip)

```
# Hermes 全球前沿情报简报 🐴✨
日期：xxxx年x月x日

## 1️⃣ 今日最高优先级信号 (3-5条最重要的)
每条：领域 | 发生了什么 | 为什么重要 | 置信度

## 2️⃣ 科研与AI前沿
🧠 Google AI / NVIDIA / HuggingFace / VentureBeat / TechCrunch
📄 arXiv AI/ML/NLP/CV/安全/量子 — 挑亮点论文
🔬 Nature / Cell / Lancet / PNAS / NEJM — 突破性研究

## 3️⃣ 经济/金融/监管
🏛️ 美联储 / ECB / IMF
💰 Bloomberg / MarketWatch

## 4️⃣ 政治/政策/安全
🌍 IPCC / UN OCHA / EU / CISA
🛡️ 网络漏洞/安全信号

## 5️⃣ 太空探索
🌌 NASA / Space.com / SpaceNews

## 6️⃣ 文化与审美
🎮 游戏 — 只挑新作公布
🌸 动漫 — 新番/续作
🎷 爵士（重点！Kali最爱！音乐人背景+类型+听感）
🎵 音乐 — 新专辑/新歌
📖 Aeon / TED Quanta深度思想

## 7️⃣ 风险监控 & 早期信号
```

## ⏰ Pre-Flight Protocol (CRITICAL — added 2026-06-10)

This is the **most-corrected workflow rule**. Kali explicitly set this sequence.

### The 30-Minute Rule

> **7:00 briefing** → start prep at **6:30** | **19:00 briefing** → start prep at **18:30**

The cron job triggers at `30 6,18 * * *` (6:30/18:30) — 30 minutes BEFORE the delivery time. Use the full 30 minutes.

### Step 0: Notify Kali on Start

**MANDATORY** — Kali said: "每次开始之前要给我说"

Send a Telegram message immediately when prep starts:
```
🐴✨ 小马开始30分钟前沿情报思考和探索了！今晚/今早的全球动态我挖深一点～ (18:30-19:00 / 06:30-07:00)
```

### Step 1: Deep Reading (first ~20 minutes)

1. Run `python /c/Users/Admin/AppData/Local/hermes/scripts/content_feed_harvester.py`
2. Read EVERY article — don't just scan titles
3. Focus on historically under-covered areas:
   - **Geopolitics/humanitarian** (UN OCHA, etc.) — NEVER just list country names. Each needs: what happened, what caused it, numbers, why it matters.
   - **Culture & ideas** (Aeon, TED, HN) — Kali said culture was too thin last time
   - **Gaming** — real announcements/releases, not guides
4. Take at least 20 minutes. Don't cut the time short.

### Step 2: Think & Connect (next ~10 minutes)

1. Record thinking in **Obsidian Vault** (C:\Users\Admin\Documents\Obsidian Vault\)
2. For each item: what changed? who benefits? who loses? what does it mean?
3. Cross-domain: AI↔regulation, energy↔geopolitics, finance↔policy
4. Score items using the 100-point system
5. Identify inflection points — not noise, not headline-chasing

### Step 3: Deliver at 7:00 / 19:00

Output complete briefing. Every section substantive — never just list topics or country names.

## 🕐 Schedule

**`30 6,18 * * *`** — Trigger at 6:30/18:30 for 30-minute prep, output around 7:00/19:00.
Time gating in script: silent during 1:00-6:59.

## 🔧 Script Architecture

Location: `scripts/content_feed_harvester.py`

Key components:
- **SOURCES list** — flat list of (url, is_atom, status_key, emoji, label) tuples
- **fetch_one_source(url, is_atom)** — curl-based with 8s connect / 15s max timeout
- **diff_new(items, seen_urls)** — dedup against JSON status file (last 50 URLs/source)
- **ThreadPoolExecutor(max_workers=5)** — parallel fetch (proxy limit)
- **Output loop** — iterates EVERY source, picks 1-2 items each
- **NEGATIVE_KEYWORDS** — politics/violence filter (CN + EN)

## ⚙️ Cron Setup

```yaml
cron:
  action: update
  job_id: e045b13a7ef3
  schedule: "0 7,19 * * *"
  name: Hourly Content Feed
  script: content_feed_harvester.py
  no_agent: false
  deliver: telegram
  enabled_toolsets: [web, terminal, file]
```

## 🔍 Feed Format Quirks

See `references/feed-format-quirks.md` for full details. Key points:
- **CDATA titles** — Atom feeds: regex, not ET
- **Atom link offset** — first 2 links are feed-level
- **Blogger RSS** — Free Jazz uses `<item>` in `<channel>` with HTML in `<description>`
- **arXiv RSS** — huge feeds (100-800KB), very reliable (200)

## 🪟 Windows Proxy Pitfalls

- Max 5 parallel curl calls (Vortex proxy overload)
- Test new sources one at a time
- Use `--noproxy "*"` to bypass for testing
- `-o NUL` instead of `-o /dev/null` (exit code 23 on Windows)

## 📚 Linked Files

- `references/kali-zh-cn-brief-cron.md` — Full cron prompt + v8 source table + format spec
- `references/feed-format-quirks.md` — CDATA, Atom offset, Blogger RSS, dead feed detection
- `references/kali-intelligence-framework.md` — Complete 5-layer architecture + scoring system
- `scripts/content_feed_harvester.py` — Production script (v8, 40+ sources)

## ✅ Verification

```bash
rm "/c/Users/Admin/AppData/Local/hermes/scripts/feed_status.json"
timeout 60 python "/c/Users/Admin/AppData/Local/hermes/scripts/content_feed_harvester.py"
```