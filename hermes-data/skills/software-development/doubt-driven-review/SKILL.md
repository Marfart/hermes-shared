---
name: doubt-driven-review
description: "Subjects every non-trivial decision to fresh-context adversarial review before it stands. Use when correctness matters more than speed, when working in unfamiliar code, when stakes are high, or when a confident output would be cheaper to verify now than debug later."
version: 1.0.0
author: Hermes Agent (adapted from addyosmani/agent-skills)
license: MIT
metadata:
  hermes:
    tags: [review, quality, verification, adversarial, doubt]
    related_skills: [writing-plans, subagent-driven-development, test-driven-development]
---

# Doubt-Driven Review

## Overview

A confident answer is not a correct one. Long sessions accumulate context that quietly turns assumptions into "facts" without anyone noticing. Doubt-driven review is the discipline of materializing a fresh-context reviewer — biased to **disprove**, not approve — before any non-trivial output stands.

This is NOT a post-hoc review. This is an in-flight posture: non-trivial decisions get cross-examined while course-correction is still cheap.

## When to Use

A decision is **non-trivial** when at least ONE of these is true:

- It introduces or modifies branching logic
- It crosses a module or service boundary
- It asserts a property the type system cannot verify (thread safety, idempotence, ordering, invariants)
- Its correctness depends on context the future reader cannot see
- Its blast radius is irreversible (production deploy, data migration, public API change)
- It involves analysis, conclusions, or claims that will be delivered to a user

Apply the skill when:
- About to make an architectural decision under uncertainty
- About to commit non-trivial code
- About to claim a non-obvious fact ("this is safe", "this scales", "this matches the spec")
- Working in code or analysis you don't fully understand
- Producing a daily briefing, research report, or any output where accuracy matters
- After 3+ failed fix attempts

**When NOT to use:**
- Mechanical operations (renaming, formatting, file moves)
- Following a clear, unambiguous user instruction
- Reading or summarizing existing code
- One-line changes with obvious correctness
- Pure tooling operations (running tests, listing files)
- The user has explicitly asked for speed over verification

<HARD-GATE>
If you've tried 3+ times to fix something and failed, you MUST apply doubt-driven review before trying again. The 4th attempt without fresh-context review is wasted effort.
</HARD-GATE>

## The 5-Step Doubt Cycle

```
DOUBT CYCLE:
- [ ] Step 1: CLAIM — wrote the claim + why-it-matters
- [ ] Step 2: EXTRACT — isolated artifact + contract, stripped reasoning
- [ ] Step 3: DOUBT — invoked fresh-context reviewer with adversarial prompt
- [ ] Step 4: RECONCILE — classified every finding against the artifact text
- [ ] Step 5: STOP — met stop condition (trivial findings, 3 cycles, or user override)
```

### Step 1: CLAIM — Surface What Stands

Name the decision in 2-3 lines:

```
CLAIM: "The new caching layer is thread-safe under the
        read-heavy workload described in the spec."
WHY THIS MATTERS: a race here corrupts user data and is
                  hard to detect in QA.
```

If you can't write the claim that compactly, you have a vibe, not a decision. Surface it before scrutinizing it.

### Step 2: EXTRACT — Smallest Reviewable Unit

A fresh-context reviewer needs the **artifact** and the **contract**, not the journey.

- Code: the diff or the function — not the whole file
- Decision: the proposal in 3-5 sentences plus the constraints it has to satisfy
- Analysis: the conclusion plus the data it's based on

**Strip reasoning.** The reviewer must reach their own conclusion. If you hand them yours, they'll anchor on it.

### Step 3: DOUBT — Fresh-Context Adversarial Review

Use `delegate_task` to spawn a fresh subagent with NO session context:

```
delegate_task(
    goal="You are an adversarial reviewer. Your job is to DISPROVE the following claim, not approve it. Find every flaw, gap, and unsupported assumption.",
    context="CLAIM: [the claim]\n\nARTIFACT: [the extracted code/decision]\n\nCONTRACT: [what it must satisfy]\n\nFind: (1) logical gaps, (2) missing error handling, (3) assumptions that could be wrong, (4) edge cases not covered, (5) any reason this might fail.",
    toolsets=["terminal", "file"]
)
```

The reviewer must be biased to **disprove**, not approve. "Looks good" is not an acceptable review.

### Step 4: RECONCILE — Classify Every Finding

For each finding from the reviewer:

| Finding Type | Action |
|---|---|
| **Confirmed flaw** | Fix immediately, then re-doubt the fix |
| **Valid concern, not a flaw** | Document as known risk, add defensive check |
| **Misunderstanding** | Clarify the contract, re-extract if needed |
| **Nit/style preference** | Note but don't block |
| **Reviewer wrong** | Explain why, but stay humble — you might be the one who's wrong |

### Step 5: STOP — When to Stop Doubting

Stop after any of:
- All findings are nits or misunderstandings (trivial)
- 3 full doubt cycles completed without blocking flaws
- User explicitly says "ship it" or "stop reviewing"
- Time pressure is real and genuine (not self-imposed)

## Anti-Rationalization 表

| 借口 | 真相 |
|------|------|
| "我检查过了，应该没问题" | 自己检查自己的逻辑 = 没检查。fresh-context reviewer才能发现你的盲点。 |
| "这个太简单不需要review" | 简单决策里的bug最难发现——因为你不觉得需要检查。 |
| "没时间review了" | 没时间review = 有时间debug。review比debug快10倍。 |
| "我对这块很熟悉" | 熟悉 = 盲点最多。Dunning-Kruger效应。 |
| "reviewer可能看不懂" | 那你的代码/决策就太复杂了。简化到reviewer能看懂。 |
| "3次都失败了，再试一次" | 3次失败 = 假设错误。停下来用doubt cycle重新分析。 |
| "这只是个小改动" | 小改动引入的bug最多——因为你不觉得需要检查。 |
| "用户等着呢" | 用户等bugfix比等review更久。 |

## Use with Hermes delegate_task

When using doubt-driven review with Hermes subagents:

1. **Main agent** identifies the claim (Step 1) and extracts the artifact (Step 2)
2. **Spawn a fresh `delegate_task`** with the adversarial prompt (Step 3)
3. **Main agent** reconciles findings (Step 4)
4. **If blocking flaws found**, fix and re-doubt from Step 1

The key insight: **fresh context = no anchoring bias**. The reviewer hasn't seen your reasoning, so they can't anchor on your conclusions.

## Model Tiering for Review

Use the strongest available model for the adversarial reviewer — you want maximum skepticism and reasoning power:

| Role | Model Tier | Why |
|------|-----------|-----|
| Claim author (you) | Standard | You already have full context |
| Adversarial reviewer | **Strongest** | Needs to find flaws you can't see — requires deepest reasoning |
| Reconciliation (you) | Standard | Structured comparison, no deep reasoning needed |

```python
# Adversarial reviewer — use the strongest model
delegate_task(
    goal="You are an adversarial reviewer...",
    model={"model": "deepseek-v4-flash"},  # Strongest available
    ...
)
```

## Verification

After completing the doubt cycle:
- [ ] Claim was named explicitly in 2-3 lines
- [ ] Artifact was extracted (code diff, decision proposal, analysis conclusion)
- [ ] Fresh-context reviewer was invoked via delegate_task
- [ ] Every finding was classified (confirmed flaw / valid concern / misunderstanding / nit / reviewer wrong)
- [ ] All confirmed flaws were fixed
- [ ] Stop condition was met (trivial findings / 3 cycles / user override)

Can't check all boxes? You skipped doubt-driven review. Do it again.

## Cross-References

- **FP-Check (Trail of Bits security-audit skill)**: Similar adversarial verification but specifically for security findings. doubt-driven-review is general-purpose; FP-Check is domain-specific for vulnerability claims.
- **Instinct-Based Learning (ECC/everything-claude-code skill)**: When instinct confidence is low (<0.5), doubt-driven-review is the appropriate tool for fresh-context verification before promoting the pattern.
- **HARD-GATE (superpowers)**: HARD-GATE prevents skipping steps; doubt-driven-review prevents accepting claims without evidence. They complement each other — use HARD-GATE to ensure process, use doubt-driven-review to ensure correctness.
- See `autonomous-learning/references/agent-skills-ecosystem.md` for the full 4-project comparison study (superpowers 224K⭐ + agent-skills 54K⭐ + trailofbits 15K⭐ + ECC 82K⭐).