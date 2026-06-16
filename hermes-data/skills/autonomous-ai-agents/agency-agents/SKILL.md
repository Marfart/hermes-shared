---
name: agency-agents
title: "The Agency: AI Agent Persona System"
version: "1.0"
description: "Deep understanding of msitarzewski/agency-agents (113k⭐) — 270+ AI agent personas across 16 divisions, 12-tool cross-platform agent system. Key insight: persona-driven agents (Identity+Mission+Workflow) vs. Hermes' skill-only approach."
source: "https://github.com/msitarzewski/agency-agents"
---

# The Agency: AI Agent Persona System

## What It Is

A collection of **270+ AI agent personalities** organized into 16 divisions (engineering, security, sales, design, etc.). Each agent has a YAML frontmatter + Markdown body with identity, mission, workflow, and communication style. Supports 12+ AI tools (Claude Code, Copilot, Gemini CLI, Cursor, Codex, etc.)

## Core Data Model

```
┌─ YAML Frontmatter ─────────────────────────┐
│ name: Frontend Developer                    │
│ description: Expert frontend developer...   │
│ color: cyan                                 │
│ emoji: 🖥️                                  │
│ vibe: Builds responsive, accessible...      │
└─────────────────────────────────────────────┘
┌─ Markdown Body ─────────────────────────────┐
│ ## 🧠 Your Identity & Memory                │
│   Role, Personality, Memory, Experience     │
│ ## 🎯 Your Core Mission                     │
│   Domain expertise areas                    │
│ ## 🚨 Critical Rules You Must Follow        │
│   Non-negotiable constraints                │
│ ## 📋 Your Core Capabilities                │
│   Tools, frameworks, patterns               │
│ ## 🔄 Your Workflow Process                 │
│   Step-by-step execution guide              │
│ ## 💭 Your Communication Style              │
│   Tone, framing, language preferences       │
│ ## 🎯 Your Success Metrics                  │
│   Measurable outcomes                       │
└─────────────────────────────────────────────┘
```

## Architecture (from reading 6/16 divisions = 114 agent files)

| Component | What it does |
|-----------|-------------|
| `agents/<division>/<division>-<slug>.md` | Single source of truth (Markdown) |
| `scripts/convert.sh` | Converts source → 12 tool formats |
| `scripts/install.sh` | Places files in tool config directories |
| `integrations/<tool>/` | Pre-converted files for each tool |

**Key insight:** The `convert.sh` + `install.sh` pipeline is the architectural core — ONE source file, MANY tool targets.

## How It Differs from Hermes Skills

| Aspect | Hermes Skills | The Agency |
|--------|--------------|------------|
| Focus | **Function** (what to do) | **Persona** (who to be) |
| Unit | SKILL.md with steps | Agent.md with identity+workflow |
| Activation | Auto-loaded by context | Explicit mode switch ("activate Frontend Developer") |
| Personality | None (neutral) | Emoji + vibe + style + emoji |
| Cross-tool | Hermes-only | 12 different AI tools |

## Key Takeaways for Our Work

1. Our Hermes skills already match the "functional" layer — we have ~100 skills covering diverse domains
2. We lack the **persona layer** — adding Identity/Rules/CommunicationStyle to key skills would make them more effective
3. The convert.sh multi-target pattern is excellent — one skill definition can target Hermes + Codex + Gemini
4. The naming convention (`division-agent-name.md`) enables autocomplete/discovery without directory traversal

## Verification

Script at: `memories/脚本缓存/verify_agency_v2.py`

Parsed 114 agent files from 6 divisions:
- Identity section: 83/114 (72%)
- Mission section: 75/114 (65%)
- Workflow section: 66/114 (57%)
- Rules section: 78/114 (68%)
- Style section: 80/114 (70%)
- Metrics section: 68/114 (59%)
- Avg body length: 15,877 chars

## References

- Repo: https://github.com/msitarzewski/agency-agents
- Clone: `~/Desktop/Working/agency-agents/`