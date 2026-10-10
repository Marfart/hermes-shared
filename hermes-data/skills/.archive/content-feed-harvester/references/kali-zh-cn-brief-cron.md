# Kali's Chinese Briefing Cron — v8 (2026-06-10) 全球情报系统升级版

## CRITICAL Session Correction (2026-06-10) — PRE-FLIGHT PROTOCOL

### Rule 1: 30-Minute Prep Before Every Briefing

Kali said: "以后发这个给我之前自己先去至少看20min的信息源再发"

Cron now triggers 30 min early: `30 6,18 * * *` (6:30/18:30, deliver ~7:00/19:00)

Step 0 — Notify Kali: "每次开始之前要给我说" — Send a Telegram message: "小马开始30分钟前沿情报思考和探索了！"

Step 1 — Deep Reading (20 min): Run harvester, read EVERY article, focus on under-covered areas (culture, UN OCHA, gaming)

Step 2 — Think & Connect (10 min): Record in Obsidian Vault. Score items. Cross-domain connect.

Step 3 — Deliver: Complete briefing at 7:00/19:00.

### Rule 2: Never Just List Country Names

UN OCHA/geopolitical entries MUST include what happened, key numbers, why it matters. Never just: "UN OCHA: 黎巴嫩、巴勒斯坦、刚果、乌克兰" without explanation.

### Rule 3: Culture Section Must Be Rich

Kali: "明显有些系列的没有发完，文化与审美太少了" — cover ALL sub-sections every time.

## Schedule
`30 6,18 * * *` — 6:30 and 18:30 for 30-min prep, deliver ~7:00 and ~19:00.

## Complete Briefing Format (7 sections, ALL must be delivered — previous bug: 文化与审美太少)

```
# Hermes 全球前沿情报简报
日期：xxxx年x月x日

## 1️⃣ 今日最高优先级信号 (3-5条最重要的)
每条：领域 | 发生了什么 | 为什么重要 | 置信度(高/中/低)

## 2️⃣ 科研与AI前沿 (L1层重点)
🧠 Google AI / NVIDIA / HuggingFace / VentureBeat / TechCrunch
📄 arXiv AI/ML/NLP/CV/安全/量子 — 挑亮点论文
🔬 Nature / Cell / Lancet / PNAS / NEJM — 挑突破性研究

## 3️⃣ 经济/金融/监管
🏛️ 美联储 / ECB / IMF  
💰 Bloomberg / MarketWatch (CPI、利率、货币政策)

## 4️⃣ 政治/政策/安全
🌍 IPCC / UN OCHA / EU / CISA  
🛡️ 网络漏洞/安全信号

## 5️⃣ 太空探索
🌌 NASA / Space.com / SpaceNews

## 6️⃣ 文化与审美（之前发太少，已修正——要完整覆盖）
🎮 游戏：只挑NEW RELEASES/测评/大新闻。Skip指南/补丁/皮肤
🌸 动漫：只挑新番/续作/PV/放送日期
🎷 爵士（重点！Kali最爱！音乐人背景+类型+听感）
🎵 音乐（新专辑/新歌/巡演）
📖 Aeon / TED / Quanta深度思想

## 7️⃣ 风险监控 & 早期信号
```

## Selection Quality Rules

- **Gaming** — real game releases/announcements/trailers only. No: guides, roster updates, patch notes, cosmetics, sales deals
- **Anime** — new seasons/premieres/casts only. No: Pokémon game DLC, manga chapter endings, merchandise
- **Music** — new album releases/singles/tours only. No: legal cases, industry politics, personal drama

## Music Taste Hierarchy (encoded in skill)
1. 🥇 JAZZ — favorite. Free jazz, avant-garde, spiritual, soul jazz. Must include genre+background+听感
2. Trip-hop (吹泡)
3. Ethereal wave (仙音)
4. Darkwave (暗潮)
5. Shoegaze/Dream pop (盯鞋)

## V8 Source Architecture (40+ sources, verified working)

### 🧠 AI Research & Lab Updates
- blog.google/technology/ai/rss/ — Google AI/DeepMind
- venturebeat.com/category/ai/feed/ — VentureBeat AI
- techcrunch.com/feed/ — TechCrunch
- thenextweb.com/rss/index.xml — TNW
- blogs.nvidia.com/feed/ — NVIDIA ✅ NEW
- huggingface.co/blog/feed.xml — HuggingFace ✅ NEW (797 items!)

### 📄 arXiv Multi-Layer Papers
- arxiv.org/rss/cs.AI / cs.LG / cs.CL / cs.CV / cs.CR
- arxiv.org/rss/quant-ph / astro-ph / q-fin / stat.ML / econ

### 🔬 Frontier Science
- MIT Tech AI, MIT Tech, ScienceDaily, Quanta, New Scientist
- Nature, PNAS, Cell ✅ NEW, Lancet ✅ NEW, NEJM ✅ NEW
- arXiv Physics, IEEE Spectrum

### 🌌 Space
- NASA, Space.com, SpaceNews

### 🌍 Policy/Climate/Security (NEW category)
- IPCC ✅, UN OCHA ✅, EU Commission ✅, CISA ✅
- WHO ✅, NOAA ✅, Federal Register ✅
- Fed speeches ✅, ECB ✅

### L3 Aggregation (NEW)
- Hacker News (hnrss.org/frontpage) ✅ — high-signal community
- Cloudflare blog ✅

### 🎨 Culture (NEW)
- Aeon.co ✅ — philosophy/culture
- TED Talks ✅

### 🎮 Game / 🌸 Anime / 🎷 Jazz / 🎵 Music
- Eurogamer, ANN, Free Jazz Collective, Stereogum

### 💰 Finance
- Fed press, IMF, Bloomberg, MarketWatch, ECB

### ⚡ General Tech
- Ars Technica

### Dead/Blocked (do not use)
- OpenAI blog/rss: 403 Cloudflare
- DeepMind discover blog: 404 → use blog.google/technology/ai/rss/
- Meta AI blog: 404
- WIRED AI tag: HTML not RSS
- Phys.org: timeout
- Fierce Biotech: 403

## Output Quality Rules (corrections consolidated)

- ❌ No bare headlines or title dumps — Kali: "不要发个标题给我"
- ❌ No "可能很重要" without explaining WHY
- ❌ Don't skip any category — ALL must be covered every tick ("是都要发")
- ❌ Don't just focus on tech — include political, economic, energy, demographic, military
- ❌ Gaming/Anime/Music — pick actual WORKS, not guides/controversies
- ✅ Chinese conversational storytelling (可爱活泼, with kaomoji)
- ✅ Explain "what happened + why it matters"
- ✅ Include artist/genre context for jazz
- ✅ Deep read articles before writing (20+ min rule)
- ✅ No URL links in output — pure storytelling

## Scoring System (for internal evaluation)
0-100: Source originality(20) + Novelty(20) + Impact(20) + Scarcity(15) + Verifiability(10) + Time sensitivity(10) + Cross-domain value(5)
- 90-100: 必须立即关注
- 80-89: 高价值信号
- 70-79: 值得跟踪
- 60-69: 背景信息
- <60: 忽略 (unless linked to long-term theme)

## Verification
```bash
rm "/c/Users/Admin/AppData/Local/hermes/scripts/feed_status.json"
timeout 60 python "/c/Users/Admin/AppData/Local/hermes/scripts/content_feed_harvester.py"
```