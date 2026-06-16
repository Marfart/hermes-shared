---
name: self-maintenance
description: "Autonomous daily health checks, version updates, system audit, and industry research. Pattern for cron-driven agent self-improvement and maintenance routines."
version: 2.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
trigger: "cron job or user request for daily self-update / health check / system audit"
metadata:
  hermes:
    tags: [self-maintenance, health-check, version-update, skills-audit, industry-research, cron, daily-update]
    related_skills: [hermes-agent, subagent-driven-development, blogwatcher, writing-plans]
---

# Self-Maintenance

Autonomous agent maintenance routine — checks version/updates, audits skills and tools, gathers industry intelligence, and applies proactive improvements. Designed for cron-driven or ad-hoc execution.

## When to Use

- **Cron-based daily self-update** — scheduled job that repeats daily
- **On-demand health audit** — user asks "how is Hermes doing?" or "check for updates"
- **Pre-task warm-up** — before starting a large project, verify the toolchain is current
- **Post-update verification** — after `hermes update`, confirm everything still works

## The Workflow

### Phase 1: Version & Update Check

```bash
# Check current version
hermes --version

# Check health
hermes doctor
hermes doctor --fix              # Auto-fix config migration, version bumps, etc.

# For git-based installs, check pending commits
cd ~/AppData/Local/hermes/hermes-agent
git fetch --tags                 # ⚠️ REQUIRED before checking commit count!
git fetch origin                 # Fresh remote refs — without this, hermes --version
                                 # may report "N commits behind" based on stale data
git log --oneline -10 HEAD..origin/main
```

**⚠️ Always `git fetch` first.** `hermes --version` reports "N commits behind" using
whatever remote refs the local clone has cached. If you haven't fetched recently,
the count may be wildly inflated (e.g. "325 commits behind" when the real count is 17).
Run `git fetch origin` before checking delta, then compare with `git log --oneline HEAD..origin/main`.

# Safe update (fast-forward only)
git pull --ff-only
```

**⚠️ Windows CRLF noise:** On Windows (git-bash/MSYS), git may mark every file as modified
due to LF→CRLF line-ending conversion. Before pulling, check if the diff is whitespace-only:
```bash
git diff --ignore-cr-at-eol --stat   # empty = only CRLF noise
git diff -w --stat                    # empty = only whitespace changes
```
If ALL changes are whitespace-only (the git diff -w output shows 0 changed files), use `git stash` to
clear the noise, pull, then `git stash drop`:
```bash
git stash && git pull --ff-only && git stash drop
```

**Key facts:**
- Version string lives in `hermes_cli/__init__.py: __version__`
- `hermes --version` shows version + number of commits behind origin
- `hermes doctor` checks config validity, dependencies, and auth status
- `hermes update` is the end-user CLI command (internally does git pull)

### Phase 2: Skills & Tools Audit

```bash
# List installed skills with status
hermes skills list

# Browse hub for available official skills
hermes skills browse

# Check for and apply skill updates
hermes skills check              # Shows which skills have updates available
hermes skills update             # Updates all outdated skills (non-interactive)

# After update: re-verify installed skills
hermes skills list

# List enabled toolsets
hermes tools list

# Quick config health check
hermes config check

# Session store statistics
hermes sessions stats
```

**What to check:**
- All expected skills are enabled (not disabled)
- No skills have warnings or dependency issues
- Core toolsets are enabled (web, browser, terminal, file, code_execution, memory, delegation, cronjob)
- Gate log at `~/.hermes/logs/gateway.log` for errors if gateway is running

**⚠️ Skills update behavior (v0.15.x):**
- Every updated skill goes through **quarantine → security scan → install** process
- **DANGEROUS verdict** skills (even builtins) still install successfully if source is trusted
- Skills that are **already up-to-date** are silently skipped (no output)
- **Name collisions** (multiple skills share the same name from different sources):
  - `hermes skills update` will print a table of all candidates
  - You must use the **full identifier** (e.g. `skills-sh/steipete/clawdis/notion`) to resolve
  - For the `notion` skill specifically, there are two community versions from skills.sh — neither is the built-in one
- After updates, verify with `hermes skills list` that nothing was accidentally removed

### Phase 3: Autonomous Topic Learning (Trends & Ecosystem Survey)

When the user triggers a learning task (search trends → audit local tools → record findings), follow this pattern:

**Step 1 — Search Trends:**
1. Try `ddgs` CLI first (`command -v ddgs` to check). On cloud/VPS IPs, DuckDuckGo often returns empty.
2. If `ddgs` returns empty (output is `""` with exit code 0), fall back to `web_search` built-in tool — it tolerates cloud IPs better.
3. For each topic, run 3 queries with different angles (e.g. "best MCP servers 2026", "new AI agent tools 2026", "awesome MCP servers github"). Multiple angles compensate for individual query limitations.
4. Use `mcp_fetch_fetch` or web_extract for content extraction from key pages (GitHub repos, blogs). If the extract backend is limited (ddgs-only), use browser tools as fallback.

**Step 2 — Audit Local Inventory:**
1. `skills_list()` to enumerate all skills with categories and count
2. Check what skill categories exist — note overlaps and gaps
3. Compare findings against what's already available locally

**Step 3 — Record Findings:**
1. Try `memory(action='add', ...)` to persist durable learnings for other sessions
2. ⚠️ **CRITICAL: memory may be disabled in cron environments.** Check for `"Memory is not available"` error.
3. **If memory is unavailable**, save findings to a dated file in `Working/` as an alternative:
   ```bash
   Working/hermes-learning-YYYY-MM-DD.md
   ```
4. Content to record: ecosystem state, tool versions, category-level insights (not session-specific task details)

**Pitfalls:**
- **Multiple search engines for resilience**: ddgs → web_search → browser. Never rely on one.
- **Memory disabled in cron**: Always check the return value of `memory()`. If it errors, write a file instead — never silently drop learnings.
- **Subagent news fabrication**: Do NOT delegate trend research to subagents. They generate convincing fake headlines. Gather primary sources directly.
- **Don't capture environment-dependent failures** (missing binaries, cloud IP blocks, transient rate limits) as durable memory — these are situational, not rules.

### Phase 4: Industry Research (Legacy — merged into Phase 3 above)

For news and industry research (when specifically asked for news/headlines rather than general ecosystem survey), use direct API calls from the parent agent:

```bash
# Google News RSS for AI/tech headlines
curl -s "https://news.google.com/rss/search?q=AI+agent+LLM&hl=en-US&gl=US&ceid=US:en"

# Hacker News for tech community stories
curl -s "https://hn.algolia.com/api/v1/search?query=AI+agent&tags=story&hitsPerPage=10"
```

**⚠️ CRITICAL PITFALL: Subagent news fabrication**

When using `delegate_task` to research news, **subagents can generate convincing fake news**. In one session, a subagent produced fabricated headlines about "Claude 4.5 Turbo", "OpenAI Operator", and "Nvidia NeMo 3.0" — all plausible-sounding but completely invented.

**Never accept subagent research output at face value.** Always:
1. Use `web_search` or `curl` directly for the parent agent to gather primary sources
2. Extract real headlines from Google News RSS, HN Algolia API, or other structured feeds
3. Verify any subagent's claimed news stories against actual search results
4. Cross-reference with multiple sources before reporting

**Preferred approach:** Do news research in the parent agent (not via delegate_task) using `web_search` and direct API calls. Use delegate_task for code generation, data processing, and analysis — tasks where output can be verified by inspection.

### Phase 5: Plugin & Cyberware Audit (Edgerunners Upgrade)

Plugins are the "cyberware" of the agent — they directly expand tool capabilities. List all plugins and identify unenabled ones that fill gaps:

```bash
hermes plugins                   # List all plugins and their status
```

**Checklist — enable free plugins that improve daily use:**
- [ ] **Web search**: Enable `web/ddgs` (free DuckDuckGo) and `web/brave_free` (2k queries/mo free) if search is blocked by CAPTCHAs
- [ ] **Image gen**: Enable `image_gen/fal` (Flux models), `image_gen/krea`, `image_gen/openai`, `image_gen/xai` — user may ask for images
- [ ] **Video gen**: Enable `video_gen/fal` (Veo 3.1, Kling) — user may ask for videos
- [ ] **Observability**: Enable `observability/langfuse` if debugging agent behavior

**Note:** Plugins take effect on the **next session** (`/reset` or new `hermes` invocation).

### Phase 6: External Trends — New Skill Sources & Ecosystem Discovery

Check if new skill collections have appeared since last audit:

- GitHub repos with SKILL.md files that could be adapted via `external-skill-adaptation`
- New taps available via `hermes skills tap add <repo>`
- Community hubs (ClawHub, LobeHub, Browse-sh) indexed in the skills hub

**Extended ecosystem discovery (beyond skills hub):**
- **Computer-Use Drivers**: Check [trycua/cua](https://github.com/trycua/cua) for new releases (`cua-driver check-update`). This is a cross-platform background computer-use agent (MIT). On Windows, check `cua-driver doctor` for health status.
- **Hermes Plugins**: Run `hermes plugins` — these are "cyberware" that extend tool capabilities directly. Key plugins to check:
  - `rtk-hermes` — terminal output compression (60-90% token savings)
  - `Mnemosyne` — local SQLite+sqlite-vec memory
  - `disk-cleanup` — ephemeral file tracking
  - `web/ddgs` / `web/brave_free` — free search backends
- **Community Skill Indexes**:
  - [Hermes Atlas](https://hermesatlas.com) — 123+ tools across 12 categories
  - [ZeroPointRepo/awesome-hermes-skills](https://github.com/ZeroPointRepo/awesome-hermes-skills) — 85 built-in + 78 community
  - [HermesHub](https://hermeshub.xyz) — security-scanned registry

### Phase 7: Proactive Improvements

After gathering information, apply improvements:

- **Code update:** `git pull --ff-only` if updates are available
- **Skill update:** `skill_manage(action='patch')` any skill with missing steps or outdated instructions
- **Memory update:** `memory()` to persist durable facts discovered during the check
- **Config check:** `hermes config check` to verify config integrity
- **External tool updates:** Check for Cua Driver updates: `cua-driver check-update --no-cache` / `cua-driver update --apply`
  - ⚠️ **`cua-driver update --apply` Windows failure modes:**
    1. `Could not reach GitHub` — transient; retry or verify with `check-update --no-cache --json`
    2. `detected legacy install layout (v0.2.13 or earlier)` — built-in update can't handle migration, exit=1 but misdiagnosed as network error
  - 🔧 **Recovery:** PowerShell install script handles migrations correctly:
    ```powershell
    powershell.exe -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; irm https://raw.githubusercontent.com/trycua/cua/main/libs/cua-driver/scripts/install.ps1 | iex}"
    ```
  - After upgrade, verify: `cua-driver --version && cua-driver doctor`
- **Auto Curator:** v0.15.0+ has an autonomous background Curator that grades, prunes, and consolidates the skill library. Periodically check if it ran (session log / cron output). It is built-in — no install needed.

### Phase 7a: Gateway Process Health — Multi-Layer Watchdog Architecture (CRITICAL)

The Gateway process (`hermes gateway run`) is the single point of failure for message delivery, cron scheduling, and platform connectivity. A **multi-layer** watchdog architecture is essential because cron-based watchdogs share fate with the gateway:

⚠️ **Discord resource trap:** If Discord fails repeatedly (e.g., `discord connect timed out after 30s`), the gateway retries indefinitely with exponential backoff. Each attempt is 30s of blocked resources, and after the first 10 failures the gap stabilizes at 300s. **Remove Discord from `platforms` config (`enabled: false`) if not used** — it burns ~13.5 minutes of pointless connection time per day.

⚠️ **Proxy dependency:** In environments where all platform traffic goes through a local proxy (127.0.0.1:7897 Vortex/Clash), the proxy's health is a critical dependency. Proxy port being LISTENING does NOT mean it's forwarding. See `telegram-watchdog` skill's `references/vortex-proxy-disconnect-pattern.md` for the full analysis.

```
Layer 1: Windows Task Scheduler fallback     ← Independent of Hermes entirely
Layer 2: Hermes cron watchdog (script)       ← Dies when gateway dies (CRITICAL FLAW)
Layer 3: Hermes internal retry logic         ← Built into gateway run loop
```

#### Why Layer 1 is essential (Layer 2's fatal flaw)

Hermes cron (Layer 2) runs **inside** the gateway process. If the gateway crashes, the cron scheduler crashes too — the watchdog job that should detect the crash will never fire. This is a fundamental single-point-of-failure: **the watchdog shares the fate of what it monitors.**

**The fix:** A platform-level process monitor that does not depend on Hermes at all.

#### Layer 1: Windows Task Scheduler Fallback Watchdog

**Installation** (from git-bash or cmd):
```cmd
schtasks /CREATE /TN HermesGatewayFallbackWatchdog /SC MINUTE /MO 3 /TR "C:\path\to\watchdog.bat" /F
```

The `.bat` wrapper is mandatory because `.py` file association might point to PyCharm:
```bat
@echo off
"%~dp0..\hermes-agent\venv\Scripts\python.exe" "%~dp0gateway_watchdog_fallback.py"
```

**Watchdog script logic** (`gateway_watchdog_fallback.py`):
1. Read `gateway_state.json` for PID
2. Use `tasklist /FI "PID eq X" /NH` to verify PID is really alive (not just stale state file text)
3. If PID is alive → silent exit (0 output, 0 return code)
4. If PID is dead → kill residual gateway processes → restart via `hermes gateway run` with `subprocess.CREATE_NO_WINDOW`
5. Update `gateway_state.json` with new PID so subsequent checks use the correct PID

**Pitfalls:**
- `.py` file association may point to IDE (PyCharm) not Python → use `.bat` wrapper with explicit venv python.exe
- Chinese Windows locale: `schtasks`/`tasklist` output is GBK-encoded → decode with `(stdout or b"").decode("gbk", errors="replace")`
- `subprocess.run(capture_output=True, text=True)` triggers `UnicodeDecodeError` on GBK output → use `capture_output=True` (bytes) and decode manually
- Paths with spaces in `/TR` argument need careful quoting → `.bat` wrapper avoids this entirely
- The fallback script must NOT depend on Hermes libraries or imports

**Verification:**
```cmd
schtasks /QUERY /TN HermesGatewayFallbackWatchdog /FO LIST /V
```

#### Layer 2: Cron-Based Script Watchdog (Complementary)

The existing `no_agent=True` script cron (e.g. `smart_watchdog_v8.py` — the current active version) remains useful for:
- Detecting platform-level issues (SSL cert expiry, DNS failures, network problems)
- Correlating multiple signals (log scanning + network check + state file)
- Delivering detailed recovery reports to the user
- 10-minute cooldown deduplication

**Critical limitation:** Layer 2 only fires when the gateway is already alive (because cron runs inside the gateway). Its true value is diagnosing WHY a platform disconnected (SSL, DNS, rate-limit), not detecting a dead gateway. Must pair with Layer 1.

#### Silent Script Design — no_agent=True Golden Rules

**Rule 1: Silence is the default.** A `no_agent=True` script's stdout IS the message delivered to the user. Every print() is an intrusion. Design the script so that 99% of runs produce zero output.

**Rule 2: Only report repairs and restarts.** Routine diagnostics (ping OK, DNS resolves, SSL cert valid) are background noise — the user doesn't care. Only print when the script actually DID something (ran a repair command, restarted gateway). Use a flag pattern:
```python
needs_report = bool(ctx.repair_actions) or ctx.should_restart
if needs_report:
    print(...)
```

**Rule 3: 10-minute cooldown for cycling issues.** If the same problem triggers repairs every cycle (e.g., Discord keeps retrying → heartbeat timeout → restart loop), the user gets bombarded. Save the last-report timestamp to a file and skip if < 600s old:
```python
cooldown_file = Path(...)
now = time.time()
last = float(cooldown_file.read_text()) if cooldown_file.exists() else 0
if now - last > 600:  # 10 min
    cooldown_file.write_text(str(now))
    print(...)
```

**Rule 4: `deliver: local` for routine monitoring.** Unless the cron job is specifically an alert-notification system, set `deliver: local`. This means the script saves its state to the local SQLite/cache but never bothers the user. Only alert-grade monitors (gateway dead, irreversible error) should use `deliver: telegram`.

**Rule 5: Watch for stale heartbeat traps.** The gateway_state.json `updated_at` timestamp can go stale if one platform (e.g. Discord) keeps retrying — the gateway is alive and working but the heartbeat stops updating. If your script's heartbeat timeout is too short (300s), it'll falsely detect the gateway as "frozen" and trigger a restart loop. Set heartbeat timeout to at least 1800s (30 minutes) to avoid this, or better: check platform-level "connected" state (telegram/weixin) instead of global heartbeat.

#### Layer 3: Gateway Internal Logic

The gateway's `run()` loop includes `restart_on_failure=True` (configurable) and reconnection backoff. This handles transient disconnections without any external intervention. The external watchdogs only kick in when internal retries have exhausted or the process itself crashed.

#### Recovery Flow (End-to-End)

```
Gateway process dies (PID 25880 disappears)
  ↓ (within 3 min)
Layer 1: Windows Task Scheduler watchdogs fires
  ↓
Reads stale gateway_state.json → tasklist confirms PID gone → triggers restart
  ↓
Kill residual gateways → Start new gateway (hermes gateway run)
  ↓
Update gateway_state.json with new PID → Gateway reconnects (Telegram+Weixin)
  ↓ (within 2 min)
Layer 2: Smart Watchdog v6 fires via cron (now running in new gateway)
  ↓
Detects platforms recovered → sends "all clear" via Weixin/Telegram
```

#### Applicability Beyond Gateway

This multi-layer pattern applies to any critical daemon monitored by Hermes cron:
- **Live sync daemon** (`hermes_live_sync.py`): If gateway dies, the 5-min cron check dies too → sync stops silently. Consider parallel Windows Task Scheduler check.
- **Cua Driver**: Less critical (doesn't affect message delivery), but same principle.

### Phase 7b: Cross-Directory Backup Sync — Real-Time Watchdog (Preferred)

When Hermes home (`%LOCALAPPDATA%/hermes/`) needs to be backed up to a cloud-synced directory (Google Drive, Dropbox, etc.), use a **watchdog-based real-time sync daemon** rather than cron-based polling:

**Architecture (real-time):**
```
Hermes home (source)                    Backup dir (destination)
%LOCALAPPDATA%/hermes/    ──watchdog──▶  Desktop/Working/Hermes/
  ↑ watchdog.FileSystemEventHandler         ↑ Google Drive cloud backup
  ↑ create/modify/delete ⚡ <1s
```

**Upgrade path from cron-sync (Phase 7b below):**
When user says "不能同步更新吗?" ("can't this sync in real-time?"), that's a signal to upgrade from cron-based polling to watchdog-based real-time. Don't explain why the cron approach is adequate — just do the upgrade.

**Key design decisions (real-time):**
- **Python `watchdog` library** — OS-level file event notifications vs polling
- **Md5 dedup** — skip copy when content hasn't changed (prevents redundant I/O on save-triggered events)
- **500ms debounce** — coalesce rapid write bursts (save → auto-save → temp-file patterns)
- **PID file guard** — prevent duplicate daemon instances
- **Crash recovery** — cron job (every 5min) checks PID, restarts if dead

**Installation:**
```bash
pip install watchdog
python %LOCALAPPDATA%/hermes/scripts/hermes_live_sync.py
# Add to Windows Startup folder for auto-start
```

**Exclusion list:**
- `state.db`, `state.db-wal`, `state.db-shm` (session DB, multi-GB — too large for cloud sync)
- `logs/` (rotating, multi-GB)
- `cache/`, `image_cache/`, `audio_cache/` (ephemeral, regenerable)
- `hermes-agent/` source code (git-managed)
- `sessions/` (transcript history, large)
- `venv/`, `.venv/`, `node_modules/` (reproducible via pip install)

**Reference:** Full setup details in the `hermes-state-backup` skill (devops category). The live sync daemon, startup autostart, and crash recovery cron are documented there with exact file paths and Windows compatibility notes.

**⚠️ Windows pitfalls specific to live-sync:**
- `os.kill(pid, 0)` crashes with `SystemError` on git-bash Python — use `tasklist` instead
- Chinese locale output (`ping`, `ipconfig`, `tasklist`) is GBK-encoded — `.decode("gbk", errors="replace")`
- PID files survive reboot — startup script handles orphan PIDs by checking process existence

### Phase 7c: Cross-Directory Backup Sync — Cron-Based (Legacy)

When Hermes home (`%LOCALAPPDATA%/hermes/`) needs to be backed up to a cloud-synced directory (Google Drive, Dropbox, etc.), deploy an **md5-based incremental sync**:

**Architecture:**
```
Hermes home (source)                          Backup dir (destination)
%LOCALAPPDATA%/hermes/    ──cron──▶    Desktop/Working/Hermes/
  ├─ config.yaml / .env / auth.json      synced to cloud drive
  ├─ skills/                             synced
  ├─ scripts/                            synced (excl. __pycache__)
  ├─ memories/                           synced
  ├─ cron/                               synced
  └─ weixin/                             synced
  (logs/, state.db, cache/, sessions/ → SKIPPED — too large)
```

**Key design decisions:**
- **md5 hash comparison** — only copy files whose content changed (not mtime), state file tracks hashes
- **no_agent=True** — cron runs script directly, zero LLM tokens consumed
- **Silent on no-change** — only stdout on actual sync activity; nothing to say = nothing sent
- **Startup sync** — Windows Startup folder `.cmd` wrapper for first-boot sync
- **Cleanup old files** — remove destination files that no longer exist in source

**Exclusion list:**
- `state.db`, `state.db-wal`, `state.db-shm` (session DB, multi-GB — too large for cloud sync)
- `logs/` (rotating, multi-GB)
- `cache/`, `image_cache/`, `audio_cache/` (ephemeral, regenerable)
- `hermes-agent/` source code (git-managed)
- `sessions/` (transcript history, large)
- `venv/`, `.venv/`, `node_modules/` (reproducible via pip install)

**Reference:** `scripts/hermes_sync.py` — the canonical sync script. On first deploy, edit the exclusion set to match environment.

**Cron config template:**
```
action=create  schedule='every 3m'  no_agent=True
script=hermes_sync.py  deliver=local  name="Hermes cloud backup sync"
```

### Phase 8: Report Generation

Compile findings into a structured report:

```
## 📅 Self-Maintenance Report — YYYY-MM-DD

### 🔄 Version Status
- Current: Hermes Agent vX.Y.Z
- Updates: [applied | pending | up-to-date]

### 📚 Skills & Tools
- Skills: N installed (X builtin, Y local, Z hub), all healthy
- Tools: Critical tools [OK | issues]

### 📰 Industry Highlights
- Top 3-5 stories with brief summaries

### 🔧 Improvements Applied
- [List any updates, patches, or config changes]

### 💡 Key Learnings
- [Notable findings from the session]
```

## Pitfalls

### Config Migration: `doctor --fix` vs `config migrate`

Both commands exist and both update config version, but they have different
scopes:

| Command | What it does | Best for |
|---------|-------------|----------|
| `hermes doctor --fix` | Runs full health check + auto-fixes config version, missing dirs, file issues | First-run after update |
| `hermes config migrate` | Only migrates config key schema (v25→v26, etc.) + prints available env vars | Quick version bump |

**`doctor --fix` is preferred** — it handles everything at once and is
safe to run in a cron job. However, be aware that `doctor` also tries API
connectivity checks (26 in parallel), so it takes ~15-30s depending on
network.

**After `doctor --fix`:** the config version is upgraded, but `doctor`
still shows "Config version up to date (v26)" afterward — the upgrade
is silent with no explicit success message body. Verify by checking the
"Config version" line in the output after re-running.

### Subagent News Fabrication
**The most dangerous pitfall in self-maintenance.** When you delegate news research to a subagent, it can return completely fabricated headlines that sound credible (citing fake sources, dates, and details). The subagent has no access to your tools to verify — it generates what you asked for from its training data.

**Protection:**
- Do news research directly in the parent agent using `web_search` or structured API calls
- Use delegate_task for coding, analysis, and file operations — tasks where the output can be verified against existing files
- If you must delegate research, independently verify each claimed fact with a real search

### Version Detection Confusion
- `hermes --version` reads from the installed Python package, not git HEAD
- After `git pull`, the version string may still show as "behind" if the pip package wasn't reinstalled
- The real test: `git log --oneline HEAD` vs `git log --oneline origin/main`
### Skills Hub Scale Overwhelm

- The skills hub has 1120+ skills across 2 sources (84 official, 1000+ community)
- Don't try to read them all — use targeted searches for specific capabilities
- Official optional skills are curated by Nous Research and carry the highest trust

### `hermes skills browse` Times Out in Cron/Headless

`hermes skills browse` uses an interactive curses/TUI picker. When running as
a cron job (non-TTY), the command hangs until the timeout kills it.
**Do not use `hermes skills browse` from a cron job.** Use `web_search`
with targeted queries instead to discover new skills — the skills hub index
is mirrored on skills.sh which search engines index.

### `hermes skills check` Limit

`hermes skills check` compares local skill versions against the hub. However,
it does NOT auto-update — it only shows which skills need updating. You must
run `hermes skills update` separately to apply the updates. Skills with
name collisions (same name from different hub sources) are deferred with
a table of identifiers and must be resolved manually with the full identifier.

### Security Scan Noise in Skills Update

During `hermes skills update`, every skill goes through quarantine → security scan.
**DANGEROUS/CRITICAL verdicts are normal for official/builtin skills.** The scanner
flags things like `pip install ...` (supply_chain), `sudo ...` (privilege_escalation),
and GitHub token references (exfiltration) as high-risk — but these are expected
content patterns, not actual malware. The scan outputs are safe to ignore when
the source is trusted (official/builtin/local). The update continues regardless
of the verdict when the source is trusted.

**The only verdicts that should concern you:**
- Community source + DANGEROUS = investigate before installing
- Unknown source + any non-SAFE verdict = skip
- SAFE = no action needed regardless of source

### Non-interactive Skill Install
- When running as a cron job, use `--yes` / `-y` flag with `hermes skills install` to skip the confirmation prompt
- Without `-y`, the install blocks waiting for interactive input and may fail silently in non-TTY mode
- Example: `hermes skills install official/research/duckduckgo-search -y`

## Zero-Token Cron Operations

**User mandate: ALL cron jobs must be `no_agent=True` — zero LLM token consumption.** Cront-driven recurring tasks that do reasoning (checking, summarizing, filtering) must be migrated to pure scripts. A cron that consumes tokens for every tick is wasteful regardless of the model used.

### Conversion Pattern: LLM → Script

When converting an LLM-driven cron (`no_agent=False`, skills+prompt based) to a script (`no_agent=True`, `script=<file>`), follow this approach:

**1. Script requirements:**
- Self-contained Python script (stdlib + common libs like `reportlab` only — no Hermes imports)
- Silent on success/up-to-date (empty stdout = nothing sent = perfect)
- Only `print()` on real findings — that's what cron delivers
- 15-30s timeout per API call, one retry, fail silent

**2. Implement 3 cron categories:**

| Old approach | Script replacement | Output rule |
|---|---|---|
| LLM searches web for news | Direct API calls (GitHub API, EastMoney API) | New/changed data only |
| LLM reads files / audits | Python file ops (os.walk, re, sqlite3) | Problems only |
| LLM generates complex output | `reportlab` / `fpdf2` for PDF generation | Successful path printed |

**3. Delivery platform precedence:**
- All cron jobs deliver to **telegram** (user preference, 2026-06-05)
- `deliver: local` for silent maintenance-only crons
- WeChat had rate limits (iLink: rate limited) — Telegram is the stable channel
- When converting, update `deliver` field on every affected job in one batch

**4. Example: Version checker (self_update_checker.py):**
```python
# Check GitHub API, silent if current
def main():
    local = get_local_version()
    gh_ver, body = check_github()
    if local and gh_ver and gh_ver != local and gh_ver > local:
        print(f"📦 New version: v{local} → v{gh_ver}")
        # body printed too
    # else: silent
```

**5. Example: Python-based news scraper (financial_daily.py):**
- Direct API calls to EastMoney / TianTian Fund for indices + fund NAV
- `reportlab` with embedded Chinese font (msyh TTF) to produce PDF on desktop
- Only the PDF path + size is printed — no flood of raw data
- Non-trading hours = graceful degredation (silent with brief note)

**6. Example: GitHub trending checker (evolution_checker.py):**
- GitHub search API for recent repos sorted by stars
- Caches last-seen results in JSON file; only prints NEW items since last check
- Field filter: name, stars, description, URL — enough to decide if interesting

**7. Example: Wiki lint (wiki_lint.py):**
- Pure file operations: os.walk + re + structural analysis
- Detects: missing frontmatter, orphan pages, broken [[links]]
- Reports only when issues found — zero output = clean wiki

### Cron-to-Script Transition Checklist

- [ ] Write standalone Python script (no Hermes imports, no tool calls)
- [ ] Test: run once from terminal to confirm stdout/stderr behavior
- [ ] Place in `~/AppData/Local/hermes/scripts/`
- [ ] Update cron: `no_agent=True, script=<name>.py, prompt="brief description"`
- [ ] Update delivery to Telegram (or user's preferred channel)
- [ ] Remove from cron: old skills list, model/provider overrides
- [ ] Tell user: "[script_name] is now zero-token"

## Verification

After completing a self-maintenance cycle, verify:
- [ ] `hermes --version` shows no pending commits (or explain why)
- [ ] `hermes doctor` passes all checks
- [ ] `hermes skills list` shows expected skills enabled
- [ ] Critical tools are operational (web, terminal, file, memory)
- [ ] News research is from primary sources, not subagent fabrications
- [ ] Any applied patches or updates are documented

## Reference Files

Load these when you need deeper detail:

- **`references/gateway-fallback-watchdog.md`** — Full reference implementation of the Windows Task Scheduler fallback watchdog for gateway process health. Covers the multi-layer watchdog architecture (Layer 1: OS-level schtasks, Layer 2: Hermes cron, Layer 3: internal retry), PID liveness checking via tasklist, GBK locale decoding for Chinese Windows, and the clean restart procedure. Load this when diagnosing "why didn't the watchdog restart the gateway" or setting up any platform-level process monitoring that must outlive the gateway process.
- **`references/subagent-news-fabrication.md`** — Full transcript of a subagent news fabrication incident with detection method and prevention patterns. Load this when setting up a new self-maintenance cron job or whenever you're delegating research to subagents.
- **`references/cron-finance-briefing-errors.md`** — Record of the daily finance briefing cron errors (Codex TTFB timeout + Weixin rate limiting). Load this when troubleshooting or reconfiguring the finance briefing cron.
- **`references/cron-burst-coordination.md`** — iLink rate limit root cause analysis from cron burst overlap, plus the cloud-drive backup sync architecture and exclusion decisions. Load this when diagnosing Weixin delivery failures or deploying the hermes_sync.py script.
- **`references/cron-environment-pitfalls.md`** — Comprehensive catalog of Windows cron environment edge cases: Chinese path encoding failure, `$env:LOCALAPPDATA` empty in clean environment, `tasklist.exe` locale-dependent output, PowerShell `Start-Process` POSIX path resolution, and the recommended pure-Python migration pattern. Load this when any `no_agent=True` cron job exits with code 1 but runs fine from terminal.
- **`references/discord-heartbeat-stale-trap.md`** — Root cause analysis of the Discord retry → heartbeat stale → watchdog restart loop. Covers the detection pattern, four fixes applied (heartbeat timeout, silent script design, cooldown, deliver=local), and the chain of events. Load this when a watchdog keeps restarting the gateway and spamming the user.
- **`references/ai-ecosystem-landscape-2026-06.md`** — Condensed knowledge bank of AI ecosystem state as of June 2026: MCP protocol governance & scale, top 15 MCP servers, AI agent framework comparison (LangGraph/CrewAI/AutoGen/OpenAI Agents SDK/Google ADK), CLI agent landscape (Gemini CLI/Claude Code/Codex CLI), and Hermes-relevant observations. Load this when starting an ecosystem survey to avoid re-searching established facts.
- **`references/debugging-stuck-hermes-processes.md`** — How to find, diagnose, and resolve multiple/stuck Hermes processes on Windows. Detecting orphaned console sessions, distinguishing "waiting for input" from "actually stuck," and four approaches (SendKeys, WM_CHAR, AttachConsole+WriteConsoleInputW, taskkill) with their reliability limits and the critical `$pid`-is-a-reserved-variable PowerShell pitfall. Load this when the user reports "另一个 Hermes 卡机了" or you need to check for zombie Hermes instances.
- **`references/skills-update-name-collision-resolution.md`** — How to resolve name collisions when `hermes skills update` finds multiple skills with the same name from different hub sources. Covers the `notion` collision example, lockfile inspection, and re-installation with full identifiers.
- **`references/zero-token-scripts-catalog.md`** — Catalog of all 9 no_agent=True production scripts on this system: schedule, source, output rule, and dependencies for each. Load this when setting up a new cron or converting an LLM-driven cron to no_agent.
- **`references/version-check-stale-remote.md`** — Why `hermes --version` can report wildly inflated "N commits behind" counts due to stale git remote refs, and the always-fetch-first discipline to avoid false positives.

## Reference

### Hermes Version Detection Flow
```
hermes --version
  → reads hermes_cli/__init__.py: __version__ (e.g. "0.14.0")
  → checks git for commits behind origin/main
  → reports "Update available: N commits behind — run 'hermes update'"

Version file: hermes_cli/__init__.py (__version__ = "0.14.0")
Git tracking:  ~/AppData/Local/hermes/hermes-agent/
```

### Skills Count Breakdown
- Builtin skills: ~77 (shipped with Hermes)
- Local skills: varies (agent-created, editable)
- Hub skills: 1120+ total (84 official optional + community)
- Configurable per-platform via `hermes skills config`

### AI News Sources (Verified)
| Source | URL Pattern | Notes |
|--------|-------------|-------|
| Google News RSS | `news.google.com/rss/search?q=...` | Structured feed, easy to parse |
| Hacker News API | `hn.algolia.com/api/v1/search` | Tech-focused, developer community |
| NVIDIA Blog | `blogs.nvidia.com` | AI hardware + framework news |
| Goldman Sachs | `goldmansachs.com/insights` | AI economics / market analysis |
| Microsoft Security | `microsoft.com/security` | AI security research |
| IBM Research | `ibm.com/think` | Enterprise AI / observability |
