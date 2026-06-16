# AI Ecosystem Landscape — June 2026

Captured during autonomous learning session 2026-06-05. This is a durable reference for future trend-survey and ecosystem-audit cron jobs.

## MCP Protocol Status

- **Governance**: Donated to Linux Foundation's Agentic AI Foundation (AAIF) in Dec 2025. Co-founded by Anthropic, OpenAI, Google, Microsoft, AWS, Block.
- **Scale**: 97M+ monthly SDK downloads, 10,000-12,000 public MCP servers, 300+ MCP clients, 1B+ monthly tool calls via Claude alone.
- **Transport**: SSE deprecated. New standard = Streamable HTTP (remote/production) + stdio (local dev).
- **Auth**: OAuth 2.1 with incremental scope consent added April 2026.
- **Security**: OWASP MCP Top 10 published early 2026. Top risks: Prompt Injection (#1), Tool Poisoning (#2), NeighborJack (#3 — servers binding to 0.0.0.0 instead of 127.0.0.1).
- **MCP vs A2A**: MCP = agent-to-tool (vertical). A2A = agent-to-agent (horizontal). Complementary. IBM's ACP merged into A2A Aug 2025. Both under Linux Foundation AAIF.

## Top MCP Servers (2026)

From Taskade's April 2026 ranking (tested against Claude Desktop, Cursor, Windsurf):

| Rank | Server | Category | Key Tools |
|------|--------|----------|-----------|
| 1 | Taskade MCP | Productivity | 33 tools, OAuth, project/agent/automation |
| 2 | Notion MCP | Knowledge | pages, databases, blocks |
| 3 | Linear MCP | Engineering | issues, cycles, projects |
| 4 | Exa MCP | Search | web search, semantic, content extraction |
| 5 | Brave Search MCP | Search | web/news/images, privacy-first, 2k/mo free |
| 6 | Perplexity MCP | Research | synthesized answers with citations |
| 7 | GitHub MCP | Code | PR, issues, code search, secret scanning |
| 8 | Playwright MCP | Browser | browser automation (#1 global search volume) |

## AI Agent Frameworks (2026)

### CLI/ Terminal Agents (New Gen)
- **Google Gemini CLI** — 105k⭐, Apache 2.0, free 60req/min/1k/day, 1M context, MCP support. Released Apr 2026.
- **Claude Code** — Anthropic official CLI. 80.9% SWE-bench. Agent Teams feature.
- **OpenAI Codex CLI** — OpenAI terminal agent. Multi-agent.
- **Aider / Cline / RooCode / Kilo Code** — OSS alternatives, BYOK.
- **Caliber** — fingerprints projects, generates/syncs AI agent configs (CLAUDE.md, .cursor/rules/).

### Agent Frameworks (class-level comparison)

| Framework | Lang | Orchestration | Multi-Agent | Best for |
|-----------|------|---------------|-------------|----------|
| LangGraph | Py/TS | Graph-based | Yes | Production agent workflows |
| CrewAI | Py | Role-based | Yes | Task-oriented agent teams (60%+ Fortune 500) |
| AutoGen | Py | Role-based | Yes | Conversational multi-agent systems |
| OpenAI Agents SDK | Py | Graph-based | Yes | Hosted agent apps (new 2026) |
| Google ADK | Py | — | Yes | Gemini-native orchestration |
| Pydantic AI | Py | Type-safe | Partial | Production Pythonic API |
| DSPy | Py | Programmatic | No | Programming-not-prompting optimization |
| Haystack | Py | Pipeline | Moderate | Production RAG / search |
| Semantic Kernel | C#/Py/Java | Planner | Moderate | Enterprise / Azure |
| Mastra | TS | — | Yes | TypeScript-first, observational memory |
| LlamaIndex | Py | Retrieval | Limited | Knowledge-heavy agents |
| smolagents | Py | Minimalist | Limited | Lightweight experiments |

### Multi-Agent Orchestration (specialized)
- **AutoGen** — Microsoft. Conversation-based.
- **MetaGPT** — Software company simulation (PM/architect/engineer roles).
- **Miyabi** — TS. Issue-Driven Dev. 7 coding + 14 business agents. MCP 172+ tools.
- **Bernstein** — Deterministic orchestrator. Parallel coding agents + test-driven verification. Zero LLM tokens on coordination.
- **MagiC** — Go/Py. "Kubernetes for AI agents." Routing, cost control, DAG, circuit breaker.
- **DeerFlow** — ByteDance. #1 GitHub Trending Feb 2026. 25k+ stars.
- **AXME** — Py/TS/Go/Java/.NET. Durable coordination, crash recovery, human approval gates.

## awesome-ai-agents-2026

GitHub: caramaschiHG/awesome-ai-agents-2026
- 340+ resources, 20+ categories, monthly updates
- Categories: coding agents, frameworks, browser/desktop agents, voice, creative AI, task/workflow, CRM, data/research, local/self-hosted, multi-agent platforms, protocols, observability/eval, safety, governance (NEW), cybersecurity, healthcare, learning resources

## Hermes-Relevant Observations

- **fastmcp** skill can build MCP servers → could wrap Exa/Brave Search as a native tool
- **native-mcp** skill already connects MCP servers → can register any of the top 15 MCP servers
- **duckduckgo-search** works in non-cloud environments but blocked from cloud VPS IPs
- Gemini CLI is a viable delegate_task alternative to Claude Code (free tier is generous)
- OWASP MCP Top 10 scanning could be a useful new skill
