---
name: security-audit
description: Trail of Bits security audit workflow — FP-Check verification, Sharp Edges API analysis, Phase-Gated pipeline, supply chain risk assessment. Designed for code security auditing with zero false positive tolerance.
version: 1.0.0
source: trailofbits/skills (~15K stars, 74 skills, 41 plugins)
---

# Security Audit Skill

Trail of Bits security audit methodology — battle-tested on Uniswap, OpenZeppelin, and hundreds of audits.

## When to Use

- Code security auditing (any language)
- API security review (crypto, auth, config)
- False positive verification ("is this bug real?")
- Supply chain dependency risk assessment
- Differential security review (PRs, commits, diffs)

## When NOT to Use

- General code review for style/performance (use code-review-and-quality)
- Feature development or refactoring
- Non-security bug hunting

## HARD-GATE

Before starting any security audit, ALL of these must be true:

1. **Threat model defined** — Who is the attacker? What privilege level? What can they already do?
2. **Scope specified** — Which files/modules/functions are in scope? Which are out?
3. **Bug class identified** — Is this buffer overflow, injection, crypto, logic, or race condition?
4. **FP tolerance defined** — Is this a quick scan (higher FP OK) or formal audit (zero FP tolerance)?
5. **Evidence standard set** — What counts as proof? Data flow trace? Exploit PoC? Both?

STOP if any gate condition is unmet. Do not proceed with "I'll figure it out as I go."

## Anti-Rationalization Table

Every excuse below has been observed in real LLM security audits. Reject them.

| Excuse | Why It's Wrong | Required Action |
|--------|---------------|-----------------|
| "This pattern looks dangerous, so it's a vulnerability" | 模式识别不是分析 | Complete data flow tracing before any conclusion |
| "Skipping verification for efficiency" | 没有部分分析 | Execute ALL steps per the chosen verification path |
| "The code looks unsafe, reporting without tracing" | 看起来不安全的代码可能有上游验证 | Trace complete path from source to sink |
| "Similar code was vulnerable elsewhere" | 每个上下文有不同的验证和防护 | Verify this specific instance independently |
| "This is clearly critical" | LLM倾向看到bug并过高评级 | Complete devil's advocate review; prove with evidence |
| "Small PR, quick review" | Heartbleed就2行 | Classify by RISK, not size |
| "It's documented" | 开发者不看文档 | Make secure choice the default |
| "Advanced users need flexibility" | 灵活性=陷阱 | Provide safe high-level APIs; hide primitives |
| "Nobody would actually do that" | 开发者什么都会做 | Assume maximum developer confusion |
| "It's just a config option" | 配置就是代码 | Validate configs; reject dangerous combinations |
| "We need backwards compatibility" | 不安全默认不能兼容 | Deprecate loudly; force migration |
| "Background spawns parallelize workers" | 它们不会，浪费cache | Use foreground spawns only |
| "Zero findings — skip judging" | 永远跑judge pipeline | Run dedup-judge and fp-judge even on empty |

## Core Methodologies

### 1. FP-Check: False Positive Verification

**Two verification paths:**

**Standard Path** (use when ALL hold):
- Single component, no cross-module interaction
- Well-understood bug class (buffer overflow, SQL injection, XSS)
- Straightforward data flow from source to sink
- No concurrency or async in trigger

**Deep Path** (use when ANY hold):
- Ambiguous claim interpretable multiple ways
- Cross-component bug path (3+ modules)
- Race conditions, TOCTOU, concurrency
- Logic bugs without clear spec
- Standard verification was inconclusive

**FP-Check Steps:**
1. **Step 0: Restate** — Restate the claim precisely. Half of FPs collapse here.
2. **Trace data flow** — Source → every intermediate → sink
3. **Check upstream validation** — Does something sanitize/validate before this point?
4. **Devil's advocate** — Why might this NOT be a vulnerability?
5. **Render verdict** — TRUE_POSITIVE / LIKELY_TP / UNVERIFIABLE / LIKELY_FP / FALSE_POSITIVE

### 2. Sharp Edges: API Security Analysis

**Six categories of API footguns:**

| Category | Detection Pattern | Severity |
|----------|------------------|----------|
| Algorithm Selection | `algorithm=`, `mode=`, `cipher=` parameters | Critical |
| Dangerous Defaults | `SECRET \|\| "default"`, `timeout=0`, `AUTH=False` | Critical |
| Primitive vs Semantic | Raw bytes APIs, `encrypt(bytes)` | High |
| Error Handling | `except Exception: pass`, `catch {}` | Medium |
| Configuration Landmines | `CORS="*"`, `DEBUG=True`, `SECURE=False` | High |
| Crypto API Ergonomics | Low-level `AES.new()`, hardcoded IV/nonce | High |

**Pit of Success principle**: Secure usage should be the path of least resistance.

### 3. Phase-Gated Audit Pipeline

For formal security audits (c-review style):

| Phase | Name | Must Complete Before |
|-------|------|---------------------|
| 0 | Parameter Collection | — (always enterable) |
| 1 | Prerequisites | Phase 0 |
| 2 | Output Directory | Phase 1 |
| 3 | Codebase Context | Phase 2 |
| 4 | Build Run Plan | Phase 3 |
| 5 | Create Tasks | Phase 4 |
| 6 | Spawn Workers | Phase 5 |
| 7 | Wait & Classify | Phase 6 |
| 8 | Judge Pipeline | Phase 7 |

**No phase can be skipped.** Each requires evidence from the previous phase.

### 4. Supply Chain Risk Assessment

Six risk criteria for dependency evaluation:
- **Single maintainer** — Can be bribed/phished; left-pad incident
- **Unmaintained** — Vulnerabilities won't be patched
- **Low popularity** — Fewer eyes on the code
- **High-risk features** — FFI, deserialization, third-party code execution
- **Past CVEs** — Historical vulnerability count relative to popularity
- **No security contact** — Discovered vulnerabilities can't be reported safely

### 5. Variant Analysis

After finding one vulnerability, search for similar instances:
1. Create exact match pattern (matches ONLY original)
2. Identify abstraction points (keep specific vs. can abstract)
3. Iteratively generalize ONE element at a time
4. Stop when false positive rate exceeds ~50%
5. Triage results: confidence × exploitability = priority

## References

- trailofbits/skills GitHub repository (74 skills, 41 plugins)
- FP-Check dual-path verification methodology
- Sharp Edges 6-category API analysis
- c-review 9-phase pipeline with 3-layer agent architecture
- Supply chain risk 6-criteria assessment