---
name: language-tutoring
description: "Teach languages (English, Chinese, etc.) to a direct, impatient user — bilingual approach, no preliminary questions, file-based materials, session continuity."
version: 1.0.0
author: Hermes Agent
tags: [teaching, tutoring, english, ielts, language-learning, bilingual]
---

# Language Tutoring (语言辅导)

## When to Load
- User asks to learn/practice a language (English, Chinese, etc.)
- User mentions IELTS, TOEFL, or exam prep
- User asks "teach me X" or "let's study X"

## Core Rules

### 0. Research & curate before teaching
- Before writing any lesson content, search the web and GitHub for current information
- Web search: structure, formats, question types of the topic
- GitHub search: open-source projects, tools, study resources (rank by stars/relevance)
- Curate results into a ranked list, then present the most useful ones
- Only after research is done, begin teaching

### 1. NEVER ask preliminary questions — just START teaching
- Do NOT use `clarify` to ask "what level", "what topic", "how do you want to learn"
- User said "等一下，你在工作什么，我什么都没说" when asked — they want action, not questions
- Pick something useful and just go. If you must gauge level, give a sample and let them react.
- Exception: only ask if the user is mid-conversation and offers a specific request

### 2. Be direct and concise — no unnecessary detours
- Do NOT spawn subagents for calculations, research, or analysis without explicit request
- Do NOT calculate file sizes, character counts, or estimates unless user asks
- State the answer first, then optionally explain. NOT explain-first.
- If user says "暂停" / "stop" / "不用" — stop immediately, do not finish the thought

### 3. Bilingual (EN + CN) by default
- Present new vocabulary with a clean EN ↔ CN table
- Key explanations in both languages
- When user asks a technical question about how something works, answer in Chinese with English keywords/vocabulary as a learning bonus

### 4. File-based learning materials for large content
- IELTS exercises, vocabulary lists, and large materials → store as files on disk, NOT in memory
- Use `search_files` + `read_file` for on-demand retrieval instead of memory injection
- CO-LOCATE with co-learning-mode vault: store under `C:\\Users\\Admin\\Documents\\Obsidian Vault\\01-学习笔记\\英语IELTS\\`
- Use the learn_noter.py CLI tool for creating/appending structured notes:
  ```
  python "C:\\Users\\Admin\\AppData\\Local\\hermes\\scripts\\learn_noter.py" create <分类> <标题> <内容>
  python "C:\\Users\\Admin\\AppData\\Local\\hermes\\scripts\\learn_noter.py" append <分类> <标题> <新内容>
  ```
- Category=英语IELTS for English/IELTS content

### 5. Session continuity
- Use `session_search` to recall what was taught in previous sessions
- Progress is auto-tracked via learn_noter.py and Obsidian vault
- At start of a tutoring session: session_search first, then check Obsidian vault for existing notes

### 6. Memory usage
- MEMORY.md: store user identity, name, core preferences about directness/style — NOT lesson content
- USER.md: store who the user is, communication style, frustrations
- Lesson details, vocabulary logs → file on disk, not memory

## Pitfalls to Avoid
- ❌ Asking "how do you want to learn" — just start
- ❌ Going on subagent/research tangents without user asking
- ❌ Over-explaining ("let me check if", "let me calculate") — user wants direct answers
- ❌ Writing lesson content into memory (fills up, competes with conversation context)
- ❌ Ignoring "stop/暂停/不用 — continue explaining anyway

## IELTS Resource Skills (8 sub-skills, 70+ projects)

When Kali asks to collect/learn IELTS or English resources, these skills contain the curated project lists:
1. `ielts-english-learning-resources` — 综合指南+雅思专项+Anki+语法 (35+ projects)
2. `ielts-writing-evaluation-tools` — AI写作评分 (6 projects)
3. `english-listening-reading-tools` — 听力播客+阅读理解 (8 projects)
4. `english-pronunciation-speaking-tools` — 发音AI+口语训练 (7+ projects)
5. `ielts-vocabulary-wordlists` — 词频表+词汇数据 (5+ projects)
6. `ielts-study-plan-resources` — 备考计划+时间线 (5+ projects)
7. `english-collocation-grammar-tools` — 搭配+语法检查 (6+ projects)
8. `ielts-exam-simulator-tools` — 全真模拟+机考 (8 projects)

Full consolidated inventory: see `references/ielts-project-inventory.md`

## Research Workflow for Resource Collection
When asked to "collect as many X resources/skills as possible":
1. **Multi-keyword web search** — at least 8 different query angles (e.g. "IELTS preparation github", "awesome english learning", "vocabulary spaced repetition", "IELTS speaking AI", "grammar checker writing", "listening podcast transcript", "reading comprehension", "collocation dictionary")
2. **GitHub repo search** — use `mcp_github_search_repositories` with multiple queries to get star counts
3. **Star lookup** — batch `curl -s api.github.com/repos/OWNER/REPO | python -c "import sys,json;d=json.load(sys.stdin);print(d['stargazers_count'])"` for quick star counts
4. **Categorize** — group by function (comprehensive/vocab/writing/listening/speaking/grammar/simulator/plan)
5. **Format as skill** — each category = one SKILL.md with project table (name/⭐/description/use-case)
6. **Install locally** — copy to `$LOCALAPPDATA/hermes/skills/teaching/<skill-name>/`
7. **Push to shared repo** — if collaborating with another agent, push to `Marfart/hermes-shared`
8. **Update chat log** — notify collaborator via `聊天记录.md`

### Key: Kali wants "技能越多越好" — maximize breadth, not depth of a single skill
- Split into multiple narrow skills by function rather than one monolithic file
- Each skill = one functional category with project table
- Prioritize ⭐ count for ranking, but include low-star projects if they fill a gap

## Verification
- After each lesson, ensure notes were saved via learn_noter.py in the Obsidian vault under `01-学习笔记/英语IELTS/`
- Any vocabulary list should be appended to the main lesson note, not stored separately
