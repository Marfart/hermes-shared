# Zero-Token Script Catalog

All scripts under `~/AppData/Local/hermes/scripts/` designed for `no_agent=True` cron jobs. Silent on no-change, output-only on findings.

## 1. `self_update_checker.py` — Hermes Version Check
- **Schedule:** daily 12:00
- **Source:** GitHub API (`NousResearch/hermes-agent/releases/latest`)
- **Output:** Only when new version found
- **Dependencies:** stdlib (urllib, json, re)

## 2. `self_learning_kickstart.py` — 24h Self-Learning System (v3)
- **Schedule:** every 30 min (30 * * * *)
- **Source:** DDGS (duckduckgo-search) for web results
- **Output:** Learning report with search results per 3 pillars
- **Side effects:** Appends to knowledge files + writes Obsidian notes
- **Dependencies:** `ddgs` (pip), stdlib
- **Runtime:** ~10-15s per tick
- **Key constraint:** Must complete in < 20s. Uses single DDGS session, no URL extraction.

## 3. `financial_daily.py` — Daily Finance Report (PDF)
- **Schedule:** weekdays 08:30
- **Sources:** EastMoney API (indices + NAV) + EastMoney news
- **Output:** `Desktop/XiaoMa_Financial_Daily_YYYYMMDD.pdf` via reportlab
- **Dependencies:** `reportlab` + msyh TTF font (Windows Fonts)
- **Output on success:** Path + file size
- **Graceful degredation:** Non-trading hours → brief note, no crash

## 4. `wiki_lint.py` — Wiki Structure Audit
- **Schedule:** weekly Monday 06:00
- **Source:** `~/Desktop/Working/wiki/pages/`
- **Checks:** Frontmatter completeness, orphan pages, broken [[wiki-links]]
- **Output:** Only on issues found
- **Dependencies:** stdlib

## 5. `smart_watchdog_v8.py` — Platform Connectivity Watchdog
- **Schedule:** every 2 min
- **Checks:** Gateway heartbeat, SSL/TLS, proxy health (end-to-end HTTPS through 127.0.0.1:7897), user idle detection
- **Architecture:** Middleware chain pattern (MiddlewareBase protocol + ChainBuilder)
- **Error classification:** ExceptionTree (TransientError / NeedsUserAction / RepairFailed)
- **Persistence:** SQLite `.watchdog_v8.db` for dedup + alert history
- **Output:** Only on connectivity loss or recovery
- **Note:** The 10-min cooldown prevents alert storms on the same issue

## 6. `guard_monitor.sh` + `guard_monitor.ps1` — Desktop Watchdog
- **Schedule:** every 2 min
- **Arm/disarm protocol:** `guard_state.json` `armed: true/false`
- **7 detection types:** reboot, logon, screen unlock, USB, RDP, remote software, wake-from-sleep
- **PowerShell** (called from bash wrapper)
- See `devops/desktop-watchdog` skill for full details

## 7. `idle_killer.py` — Process Idle Terminator
- **Schedule:** every 5 min
- **Kills:** Processes with 2h+ user inactivity
- **Whitelist:** `hermes.exe`, `codex.exe`
- **State:** `idle_killer_state.json`

## 8. `check_live_sync_alive.sh` — Sync Daemon Heartbeat
- **Schedule:** every 5 min
- **Check:** PID existence via `tasklist`
- **Action:** Restarts Hermes live sync daemon if dead

## 9. `buyer-development-watcher/watch_files.py` — File Change Watcher
- **Schedule:** every 5 min
- **Watches:** `scripts/buyer-development/` directory for file changes
- **Silent:** Only reports on changes

## 10. `sync_learning_to_obsidian.py` — Self-Learning → Obsidian Backup Sync
- **Schedule:** every 15 min
- **Source:** `memories/自学习系统/知识库/`
- **Destination:** Obsidian Vault `01-学习笔记/自学习系统/{pillar}/`
- **Output:** Only on changes detected
- **Dependencies:** stdlib

## Cron Registration Template
```bash
hermes cron create \
  --name "descriptive name" \
  --schedule "every 2m" / "0 10 * * *" \
  --no-agent \
  --script script_name.py \
  --deliver telegram
```

## Agent-mode cron failure pattern
**Symptom:** cron output file is 0 bytes. `last_status: ok`. User receives nothing.
**Root cause:** Agent-mode cron (`no_agent=false`, the default) starts a full LLM conversation inside the scheduler. If the model times out, tool iterations exhaust, or the gateway is under load, the agent produces empty output. The scheduler records `ok` because the script itself ran.
**Fix:** Always use `no_agent=true` for any cron that must deliver reliably. The script must do all work (search + file ops + output) in under 20 seconds.