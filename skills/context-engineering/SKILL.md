---
name: context-engineering
description: "Optimizes agent context setup. Use when starting a new session, when agent output quality degrades, when switching between tasks, or when you need to configure rules files and context for a project."
version: 1.0.0
author: Hermes Agent (adapted from addyosmani/agent-skills)
license: MIT
metadata:
  hermes:
    tags: [context, quality, agent-optimization, rules, configuration]
    related_skills: [doubt-driven-review, writing-plans]
---

# Context Engineering

## Overview

Feed agents the right information at the right time. Context is the single biggest lever for agent output quality — too little and the agent hallucinates, too much and it loses focus. Context engineering is the practice of deliberately curating what the agent sees, when it sees it, and how it's structured.

## When to Use

- Starting a new coding session or project
- Agent output quality is declining (wrong patterns, hallucinated APIs, ignoring conventions)
- Switching between different parts of a codebase
- Setting up a new project for AI-assisted development
- The agent is not following project conventions
- Before dispatching delegate_task subagents (they have zero context)

<HARD-GATE>
Before dispatching any delegate_task, you MUST provide context using the 5-layer hierarchy. Subagents with zero context = guaranteed poor output.
</HARD-GATE>

## The 5-Layer Context Hierarchy

Structure context from most persistent to most transient:

```
┌─────────────────────────────────────┐
│  1. Rules Files (CLAUDE.md, etc.)   │ ← Always loaded, project-wide
├─────────────────────────────────────┤
│  2. Spec / Architecture Docs        │ ← Loaded per feature/session
├─────────────────────────────────────┤
│  3. Relevant Source Files            │ ← Loaded per task
├─────────────────────────────────────┤
│  4. Error Output / Test Results      │ ← Loaded per iteration
├─────────────────────────────────────┤
│  5. Conversation History             │ ← Accumulates, compacts
└─────────────────────────────────────┘
```

### Level 1: Rules Files (Always Loaded)

For Hermes, this is the skill system. Skills are loaded on-demand but some are critical enough to always load first:
- For coding tasks: `writing-plans`, `test-driven-development`, `systematic-debugging`
- For analysis tasks: `doubt-driven-review`, context of what the user cares about

### Level 2: Spec / Architecture Docs (Per Feature)

Before implementing, load:
- Design documents (in `docs/` or similar)
- Architecture decision records
- API specifications
- Data models

### Level 3: Relevant Source Files (Per Task)

Only load what the task needs:
- Files being modified
- Files that import/depend on the modified files
- Test files for the modified files
- Configuration files relevant to the change

**Do NOT load the entire codebase.** Use `search_files` to find relevant files, then `read_file` only what's needed.

### Level 4: Error Output / Test Results (Per Iteration)

When debugging:
- The exact error message
- Stack trace
- Test output showing the failure
- Recent git changes that might have caused it

### Level 5: Conversation History (Compacts)

Long conversations lose focus. Periodically:
- Summarize what was decided
- Drop exploration paths that didn't pan out
- Keep only the current task context fresh

## Context for delegate_task Subagents

Subagents have ZERO session context. You must provide everything they need in the `context` parameter:

```python
delegate_task(
    goal="Fix the authentication bug in user_login.py",
    context="""
    Project: MyWebApp (Python 3.11, FastAPI, PostgreSQL)
    Bug: Users with special characters in passwords get 500 errors
    Root cause (from investigation): password hashing in auth/utils.py
      doesn't handle Unicode correctly
    
    Relevant files:
    - src/auth/utils.py (password hashing - THE BUG IS HERE)
    - src/auth/routes.py (login endpoint)
    - tests/test_auth.py (existing tests, all passing)
    
    Test command: pytest tests/test_auth.py -v
    Run command: uvicorn src.main:app --reload
    
    Conventions:
    - Use pytest for testing
    - All functions need type hints
    - Error responses use JSON format: {"error": "message"}
    """,
    toolsets=["terminal", "file"]
)
```

**Bad context** (subagent will fail):
```
context="Fix the login bug"  # Which bug? Which file? What project?
```

**Good context** (subagent can work independently):
```
context="Bug: [exact error]. File: [path]. Test: [command]. Convention: [rule]."
```

## Token Budget Management

Every context injection costs tokens. Budget them wisely:

| Context Layer | Token Cost | When to Load |
|---|---|---|
| Level 1: Rules | High (one-time) | Session start |
| Level 2: Specs | Medium | Per feature |
| Level 3: Source | Variable | Per task, only needed files |
| Level 4: Errors | Low | Per debug iteration |
| Level 5: History | High (grows) | Compact periodically |

**Rules of thumb:**
1. Don't load a skill "just in case" — load when >1% relevant (superpowers rule)
2. Don't read entire files when you need one function — use `search_files` + `read_file` with offset
3. Don't carry forward context from abandoned approaches — summarize and move on
4. For subagents: provide exactly what they need, nothing more, nothing less

## Progressive Disclosure Pattern

Instead of loading everything upfront, load context progressively:

1. **Start:** Load only Level 1 (rules/skills) and the task description
2. **Explore:** Use `search_files` to find relevant files, `read_file` to read only needed sections
3. **Deepen:** Load Level 3-4 only for the specific task at hand
4. **Refresh:** After completing a task, drop its context before starting the next one

This prevents the "lost in context" problem where an agent has so much information it can't focus.

## Anti-Rationalization 表

| 借口 | 真相 |
|------|------|
| "我需要把整个代码库都读一遍" | 你需要的是相关文件，不是整个代码库。用search_files精准定位。 |
| "context越多越好" | 过多context = 失去焦点 = 幻觉。精准比全面重要。 |
| "子agent可以自己探索" | 子agent没有session context。不给context = 让它瞎猜。 |
| "这个信息可能有用" | "可能有用" = 大概率没用。只给确定需要的。 |
| "我记住上下文了" | 长对话会丢失上下文。显式地重新加载关键信息。 |
| "skill反正会被自动加载" | 自动加载是按触发条件的。>1%相关时才加载，不是无脑全载。 |
| "探索够了，开始干活" | 探索不够 = 猜测。先读关键文件再动手。 |

## Verification

- [ ] Only relevant skills loaded (checked skill list, >1% relevant)
- [ ] Only needed source files in context (used search_files, not read entire repo)
- [ ] Subagents received complete context (goal, files, commands, conventions)
- [ ] Context refreshed after task switch (dropped old task context)
- [ ] Long conversation compacted (summarized decisions, dropped dead ends)

## Cross-References

- **Context Budget Auditing (ECC)**: This skill covers what to load; ECC's Context Budget Auditor covers how much it costs. Use both: this skill for what context to provide, ECC's auditor for measuring whether your total context stack is bloated.
- **Instinct-Based Learning (ECC)**: Instincts with low confidence (<0.5) should NOT be loaded into context. They stay project-scoped until promoted to global via observation in 2+ projects.
- **HARD-GATE (superpowers)**: HARD-GATE ensures steps aren't skipped; context-engineering ensures the right information is present for each step. They work together — one prevents process gaps, the other prevents information gaps.
- See `autonomous-learning/references/agent-skills-ecosystem.md` for the full 4-project study.