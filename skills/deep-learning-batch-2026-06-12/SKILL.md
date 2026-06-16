---
name: deep-learning-batch-2026-06-12
title: "Batch Deep Learning — 5 Projects (June 12, 2026)"
version: "1.0"
description: "Deep research results from 5 major open-source projects. Each project was cloned, source code read, architecture understood, and key design decisions extracted."
---

# Batch Deep Learning: 5 Projects (June 12, 2026)

---

## ② pm-skills (16.8k⭐) — PM Skills Marketplace

**Claude Code plugin for product management**

### Architecture
- **9 plugins**, 68 skills, 42 chained commands
- Each plugin = `commands/` + `skills/` directory with Claude-format Markdown files
- Installed via `claude plugin marketplace add phuryn/pm-skills`

### Key Pattern: Command Chaining
`/discover` chains 4 skills: `brainstorm-ideas → identify-assumptions → prioritize-assumptions → brainstorm-experiments`

Skills = building blocks (YAML frontmatter + markdown body). Commands = orchestration layer that chains skills.

### Skill Format
```yaml
---
name: analyze-feature-requests
description: "..."
---
## Analyze Feature Requests
### Context
### Domain Context  
### Instructions
```

### Our Takeaway
The **command chaining** pattern is better than our single-file skills. A command can orchestrate multiple skills into a workflow. We could add a commands/ directory to our skills with "/command-name" type dispatchers.

---

## ③ DiffusionGemma (26B-A4B, 2026-06-10) — Google DeepMind

**First open-source diffusion text model (Apache 2.0)**

### What It Does
Replaces autoregressive token prediction with **discrete diffusion**: generates 256-token blocks in parallel. Bidirectional context allows self-correction during generation.

### Architecture
- Built on Gemma 4 MoE backbone: 26B total / 3.8B active params
- 256K context window
- Multimodal: text + image + video (thinking enabled)
- **4x faster** than comparable autoregressive models on high-end GPUs (NVIDIA RTX)

### The Hackable Adapter
Released alongside the model: `gemma/diffusion/hackable_diffusion_adapter/` — a modular JAX toolbox for fine-tuning the diffusion process on structured tasks (e.g., Sudoku solving demo).

### Our Takeaway
This is a **paradigm shift** in text generation. Whole-block parallel generation means the TTFT bottleneck is fundamentally different. For multi-turn agent contexts like ours, this could be revolutionary — prefill time drops dramatically. Available via Unsloth Studio for local inference (18GB RAM minimum).

---

## ④ LMCache (8.5k⭐) — KV Cache Management Layer

**Turns KV cache from temporary state into reusable, persistent knowledge**

### Architecture (v1 multiprocess)
```
┌─ LMCache Daemon ──────────────────┐
│  cache_controller / cache_engine  │
│  storage_backend (tiered)         │
│     ├─ GPU memory (L0)            │
│     ├─ CPU memory (L1)            │
│     ├─ Local SSD (L2)             │
│     └─ Remote / S3 (L3)           │
│  serde (serialization)            │
│  integration → vLLM / SGLang      │
└───────────────────────────────────┘
```

### Key Features
- **Vendor-neutral**: works with vLLM, SGLang, TensorRT-LLM
- **Tiered storage**: GPU → CPU → SSD → S3, KV cache survives engine crashes
- **Cross-session reuse**: cache persists across conversations, not just requests
- **CacheBlend**: non-prefix KV reuse — reuses cached blocks at *any* position, not just prefix
- **PD Disaggregation**: KV transfer between prefill/decode workers over NVLink/RDMA/TCP
- **Observability**: Kubernetes metrics + KV-cache-specific metrics (prefix hits, lifecycle)
- **Multi-node P2P**: shares KV cache across machines

### Our Takeaway
For Hermes running locally with long multi-turn sessions, LMCache could dramatically reduce response time. Every repeated prompt prefix (system prompt) would be cached and reused. The cross-session persistence is the game-changer: cache today's conversation and reuse tomorrow.

---

## ⑤ MasterDnsVPN (5.9k⭐) — DNS Tunnel VPN

**Battle-tested during Iran's 88-day total internet blackout**

### Architecture
Go implementation, 2 components:
- **Server**: receives DNS queries, decodes encapsulated TCP traffic
- **Client**: local SOCKS5 proxy, encapsulate TCP → DNS

### Protocol Design
| Layer | Technology |
|-------|-----------|
| Transport | Custom protocol + ARQ (retransmission) |
| Encryption | AES/ChaCha20/XOR (configurable) |
| Encoding | DNS-compatible (base32/base36/raw base64) |
| Overhead | **5-7 bytes** per packet (vs DNSTT's 59B) |
| Resolver | Multi-resolver + health checks + failover |
| Performance | **9x faster than DNSTT, 3.6x faster than SlipStream** |

### Core Innovation
1. **Custom ARQ protocol**: lightweight retransmission with minimal overhead (5-7B vs DNSTT's 59B)
2. **Multi-resolver with health checks**: sends duplicate packets through multiple DNS resolvers, drops unhealthy ones automatically
3. **MTU discovery**: detects working path MTU to prevent fragmentation
4. **Packed control blocks**: groups ACK/control traffic to reduce DNS query count
5. **Built-in local DNS caching**: reduces latency and limits DNS hijacking

### Our Takeaway
Brilliant engineering under extreme constraints. The multi-path + ARQ + minimal-overhead design is a masterclass in working with the worst network conditions. The DNS encoding trick (wrapping TCP inside DNS queries with 5-7B overhead) is particularly clever.

---

## ⑥ Tolaria (15.6k⭐) — Markdown Knowledge Base Desktop App

**Open-source alternative to Obsidian, AI-first design**

### Tech Stack
- **Desktop**: Tauri (Rust backend)
- **Frontend**: React + TypeScript + Vite
- **Storage**: Plain Markdown + YAML frontmatter, Git-backed
- **Localization**: lara-cli (18 languages including zh-CN)

### AI Integration Architecture
```
┌─ Tolaria Desktop ─────────────────────┐
│  Vault (Markdown files + Git repo)    │
│  AGENTS.md — agent entry point         │
│  CLAUDE.md — Claude Code setup         │
│  GEMINI.md — Gemini CLI setup          │
│  MCP Server ──────────────────────┐    │
│    ├─ vault tools (search, read)  │    │
│    ├─ ws-bridge (WebSocket API)   │    │
│    └─ tool-service (tool defs)    │    │
└─────────────────────────────────────┘──┘
```

### Key Design Decisions
1. **Files-first**: Notes = plain Markdown. No export needed. No proprietary formats.
2. **Git-first**: Every vault is a git repo. Full version history. Any git remote.
3. **AI-first**: AGENTS.md + MCP server + Claude/Gemini/Codex CLI integration
4. **Types as lenses**: YAML frontmatter types = navigation aids, not validation schemas
5. **No lock-in**: Stop using Tolaria → you keep all your files

### AGENTS.md Pattern (the best part)
Tolaria's AGENTS.md is the most sophisticated one I've seen — it's a **full development process document** covering:
- CodeScene health gates (mandatory before/after scores)
- TDD (Red→Green→Refactor)
- Locale translation (lara-cli)
- PostHog analytics events
- E2E QA with Playwright
- Native app QA with osascript
- Commit frequency (every 20-30 min)
- Pre-push hooks

### Our Takeaway
Tolaria's AGENTS.md is the gold standard for how AI assistants should be guided in a codebase. The **CodeScene health gate** pattern (before/after score capture) is something we could adopt for our own code quality. The MCP server for vault access is also interesting — we could build something similar for our Obsidian vault.