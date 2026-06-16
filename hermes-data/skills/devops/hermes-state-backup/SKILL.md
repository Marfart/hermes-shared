---
name: hermes-state-backup
description: "Cross-directory real-time sync of Hermes state to a Google Drive backup folder — watchdog-based live sync daemon, startup autostart, crash recovery cron. Keeps skills/, scripts/, memories/, config.yaml, auth.json synced to Desktop/Working/Hermes/ for cloud persistence."
version: 1.0.0
author: Tachikoma
platforms: [windows]
---

# Hermes State Backup & Sync

实时同步 Hermes 核心状态到桌面备份目录（Google Drive 持久化链路）。

## Architecture

```
%LOCALAPPDATA%/hermes/     ──实时同步(毫秒级)──▶   Desktop/Working/Hermes/
    ↑ watchdog 监听文件系统                           ↑ Google Drive 自动备份云端
    ↑ 创建/修改/删除/移动均瞬间同步
```

**为什么不直接写到桌面？** Hermes 代码大量硬编码 `%LOCALAPPDATA%/hermes/` 路径，修改源位置会破坏很多内部路径。同步是更安全的方案。

## Sibling: LLM Wiki (`Desktop/Working/wiki/`)

The LLM Wiki (Karpathy-style knowledge base) lives at `Desktop/Working/wiki/` — a **sibling** of the Hermes backup target, not inside it. It auto-syncs to Google Drive because `Working/` is the Drive-watched root. No separate live-sync daemon needed for wiki pages.

**Env var set in `.env`:**
```bash
WIKI_PATH="C:/Users/Admin/Desktop/Working/wiki"
```
When resuming a session, always orient via SCHEMA.md → index.md → log.md before writing new pages (see `research/llm-wiki` skill).

**Cron lint:** Every Monday 6:00 (job_id=`366f34e9bf5e`) — checks orphans, broken wikilinks, index completeness, frontmatter validity. Uses the `llm-wiki` skill from the research category.

## GitHub Shared Repo Sync (hermes-shared)

A private GitHub repo at `https://github.com/Marfart/hermes-shared` serves as the cross-machine file exchange between Tachikoma (Windows) and Xiaoma (macOS).

**Local path:** `~/hermes-shared/`

### Sync Protocol

1. When hermes skills/scripts/config change, copy updated files to `~/hermes-shared/` under the same relative path
2. Update `聊天记录.md` with **every file's detailed description** (Kali's explicit requirement)
3. `git add -A && git commit -m "feat: <summary>" && git push origin main`

### What goes in the shared repo

| Directory | Content |
|-----------|---------|
| `skills/` | Skill SKILL.md + references/ + scripts/ (same layout as hermes) |
| `scripts/` | Shared Python scripts (feishu_send, pollers, etc.) |
| `watchdog/` | Watchdog scripts (smart_watchdog, pool_timeout_detector) |
| `polling/` | Feishu polling scripts |
| `config/` | Config fragments |
| `macos-feishu/` | macOS-specific feishu poller launchd plists |
| `tachikoma-inventory/` | Tachikoma's skill/memory index document |
| `聊天记录.md` | Chat log with detailed per-file descriptions |

### .gitignore

Excludes: `*.env`, `*.key`, `*.pem`, `*.secret`, `__pycache__/`, `*.pyc`, `.DS_Store`, `Thumbs.db`, `*.tmp`, `*.bak`, `state.db`, `cache/`, `logs/`, `*.log`, state JSON files.

**Never commit:** auth.json, config.yaml (contains tokens), .env, state.db, sessions/.

### Push Protection Pitfalls

GitHub push protection can block `git push` with 403 even when "secrets" are just doc examples (`ghp_...` patterns in skill files). See `references/github-push-protection-pitfalls.md` for the full diagnosis and fix sequence (clean history + private repo + PAT in URL).

### Auto-Sync Cron (github_shared_sync.py)

Every 5 minutes, `github_shared_sync.py` (cron job_id=`59f5254858ef`, no_agent=True) automatically:
1. Scans hermes skills/scripts/memories/cron for file changes (mtime comparison)
2. Copies new/modified files to `~/hermes-shared/hermes-data/`
3. Sanitizes .env → `.env.template` (all values → `***REDACTED***`), auth.json → `auth.json.template`
4. Removes files from target that no longer exist in source
5. `git add -A && git commit && git push origin main`

**Run manually:** `python %LOCALAPPDATA%/hermes/scripts/github_shared_sync.py --once`

**Exclusions (critical for performance):**
| What | Why |
|------|-----|
| `node_modules/` | 11,000+ files, kills scan speed |
| `buyer-development/`, `joinf-crm-edm/` | Heavy JSON outputs, not needed in repo |
| `.hub/` cache | 38MB index file |
| `.db`, `.pdf`, `.exe`, `.png` | Binary/large files |
| `config.yaml` | Contains real API keys — NEVER commit |

**Key implementation detail:** Use `os.walk()` with `dirs[:]` pruning, NOT `Path.rglob()`. rglob traverses excluded directories before filtering — node_modules caused 11,489 files to be checked individually. os.walk with `dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]` drops to ~26 actual file checks.

### Kali's Rule

> 以后如果hermes文件夹里有更新，都需要同步上去，并在聊天文件里，写上每个文件的详细说明

This means: every sync must include a human-readable changelog entry in `聊天记录.md` with per-file descriptions, not just a git commit message.

## Related Skills
- `research/llm-wiki` — Karpathy-style knowledge base that lives alongside the Hermes backup at `Desktop/Working/wiki/`
- `devops/self-maintenance` — broader daily maintenance routine with Phase 7b (backup sync) documented
- `admin-helpers/feishu-group-bot` — Feishu polling that uses the shared repo for cross-machine bot communication

## What Gets Synced

| 同步 | 忽略 |
|------|------|
| ✅ `config.yaml` | ❌ `logs/` (太大) |
| ✅ `.env` | ❌ `state.db` (会话DB, 大+锁) |
| ✅ `auth.json` | ❌ `cache/`, `audio_cache/`, `image_cache/` |
| ✅ `skills/` (全量) | ❌ `sessions/` |
| ✅ `scripts/` (全量) | ❌ `hermes-agent/` (源码) |
| ✅ `memories/` (全量) | ❌ `chrome-profiles/`, `sandboxes/` |
| ✅ `cron/` | ❌ `node_modules/`, `venv/`, `.venv/` |
| ✅ `weixin/` | |
| ✅ `plugins/` | |
| ✅ `SOUL.md` | |

## Components

### 1. Live Sync Daemon (`scripts/hermes_live_sync.py`)

Python watchdog-based real-time file watcher. Runs as background daemon.

**Mechanism:**
- Uses `watchdog.FileSystemEventHandler` for OS-level filesystem events
- Debounce window: 500ms (prevents duplicate sync on rapid writes)
- MD5 content hash check before copy (avoids redundant I/O)
- Handles create/modify/delete/move events
- Persists synced file set to `memories/脚本缓存/hermes_live_sync_state.json`
- PID file at `.hermes_live_sync.pid` prevents duplicate daemon starts

**Initial sync:** On startup, walks all watched directories and syncs any files not in the persisted state. Subsequent syncs are real-time, file-by-file.

### 2. Startup Autostart (`memories/脚本缓存/Hermes_Live_Sync_Startup.cmd`)

Batch script placed in Windows Startup folder:
```
%APPDATA%/Microsoft/Windows/Start Menu/Programs/Startup/
```

Startup guard: checks PID file first, skips if already running. Launches as background (no window) via `start /B` or `Start-Process -WindowStyle Hidden`.

### 3. Crash Recovery Cron (Pure Python — Migrated from bash→PS bridge)

Cron job (job_id=0d232901ed33, every 5min, no_agent=True) checks daemon health via `check_live_sync_alive.py`:

```python
PID_FILE = Path(os.environ.get("USERPROFILE")) / "AppData/Local/hermes/.hermes_live_sync.pid"
if PID_FILE.exists():
    pid = int(PID_FILE.read_text().strip())
    r = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/NH"], capture_output=True, text=True, timeout=10)
    if str(pid) in r.stdout:
        return 0  # alive
# dead → restart via cmd.exe (not PowerShell Start-Process)
subprocess.run(["cmd.exe", "/c", "start", "/B", "", str(SCRIPT)], capture_output=True, timeout=10)
```

**Why pure Python?** The original bash→PowerShell bridge failed in cron's clean environment due to:
- 中文 path encoding (MSYS cannot decode Chinese chars) 
- `tasklist.exe //FI` locale-dependent output on Chinese Windows
- PowerShell `Start-Process` choking on POSIX paths from MSYS
- `$env:LOCALAPPDATA` empty in cron environment

See `self-maintenance/references/cron-environment-pitfalls.md` for full catalog.

## Path Reference

| What | Path |
|------|------|
| Sync daemon | `%LOCALAPPDATA%/hermes/scripts/hermes_live_sync.py` |
| PID file | `%LOCALAPPDATA%/hermes/.hermes_live_sync.pid` |
| State cache | `%LOCALAPPDATA%/hermes/memories/scripts_cache/hermes_live_sync_state.json` |
| Backup target | `%USERPROFILE%/Desktop/Working/Hermes/` |
| Startup script | `%APPDATA%/Microsoft/Windows/Start Menu/Programs/Startup/Hermes_Live_Sync_Startup.cmd` |
| Health check | `%LOCALAPPDATA%/hermes/scripts/check_live_sync_alive.py` |
| Cron ID | `0d232901ed33` (every 5min, no_agent=True) |

## Windows Compatibility

### `os.kill(pid, 0)` crashes with SystemError
git-bash Python throws `SystemError` (not `ProcessLookupError`). Use `tasklist` instead:
```python
r = subprocess.run(["tasklist", "/fi", f"PID eq {pid}", "/nh", "/fo", "csv"],
                   capture_output=True, text=False, timeout=5)
stdout = r.stdout.decode("gbk", errors="replace") if r.stdout else ""
return str(pid) in stdout
```

### Chinese locale in subprocess output
`tasklist`, `ping`, `ipconfig` output GBK-encoded text. Always:
```python
stdout = r.stdout.decode("gbk", errors="replace") if r.stdout else ""
```

### `pip install watchdog` in Hermes venv
The watchdog library isn't bundled with Hermes. It must be installed explicitly:
```bash
pip install watchdog
```
Install into the Hermes venv: `%LOCALAPPDATA%/hermes/hermes-agent/venv/Scripts/pip install watchdog`

## Usage

### First-time setup
1. Install dependency: `pip install watchdog`
2. Start daemon: `python %LOCALAPPDATA%/hermes/scripts/hermes_live_sync.py`
3. Add to Startup: copy `.cmd` to Startup folder
4. Create cron: job_id=`0d232901ed33`, script=`check_live_sync_alive.sh`, every 5min

### Check if daemon is running
```bash
cat %LOCALAPPDATA%/hermes/.hermes_live_sync.pid
tasklist /fi "PID eq <pid>"
```

### Verify sync works
```bash
# Write test file
echo "test" > %LOCALAPPDATA%/hermes/scripts/_test.txt
# Check backup (should appear within 1s)
ls %USERPROFILE%/Desktop/Working/Hermes/scripts/_test.txt
# Clean up
del %LOCALAPPDATA%/hermes/scripts/_test.txt
del %USERPROFILE%/Desktop/Working/Hermes/scripts/_test.txt
```

## Troubleshooting

### Daemon starts but nothing syncs
1. Check PID file: `.hermes_live_sync.pid`
2. Check daemon alive: `tasklist /fi "PID eq $(cat .hermes_live_sync.pid)"`
3. Check target exists: `%USERPROFILE%/Desktop/Working/Hermes/`
4. Check watchdog package: `pip show watchdog`
5. Check debug output: `%LOCALAPPDATA%/hermes/logs/live_sync.log`

### Daemon stops after some time
Common causes on Windows:
- Process killed by Windows memory pressure
- git-bash session ended (if started from terminal without `start /B`)
- **Fix:** The cron health check (every 5min) auto-restarts it. If it keeps dying, check for Python crashes in `live_sync.log`.

### File changes not syncing
- Check that the file is in a watched directory (see "What Gets Synced" above)
- File system events on Windows can be missed under heavy I/O. The initial sync on startup catches anything missed during daemon downtime.

### PID file orphaned after reboot
Windows doesn't clean PID files on reboot. The startup script's `Hermes_Live_Sync_Startup.cmd` checks PID first — if the old PID is dead (which it will be after reboot), it starts fresh. The cron health check also handles this case.