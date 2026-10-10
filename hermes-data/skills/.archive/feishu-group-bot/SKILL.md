---
name: feishu-group-bot
version: "2.0"
created: "2026-06-15"
description: "Feishu group bot operations — polling daemon, message sending, watcher with Feishu alerts, cross-machine sync"
trigger: "When working on Feishu (Lark) group bot features: message polling, sending, @mentions, watcher/auto-restart, or cross-bot sync"
---

# Feishu Group Bot Operations

## Architecture Overview

Two bots (塔奇克马 Windows + 小马 macOS) collaborate in Feishu group 「马上成功」:
- **Polling daemon** (`feishu_poll_daemon.py`): 3-second interval, detects new messages, writes alert files
- **Watcher** (`feishu_poll_watcher.py`): Monitors daemon health, auto-restarts, circuit breaker, Feishu alert on break
- **Sender** (`feishu_send.py`): Post messages with/without @mentions
- **Git sync** (`Marfart/hermes-shared`): Cross-machine file sharing

## Key File Locations

- Scripts: `%LOCALAPPDATA%\hermes\scripts\feishu_poll_*.py`, `feishu_send.py`
- State: `%LOCALAPPDATA%\hermes\memories\feishu_poll_state.json`
- Alerts: `feishu_alert.flag`, `feishu_new_msgs.txt`, `feishu_instant_trigger.flag`
- Watcher state: `feishu_poll_watcher_state.json`
- Logs: `feishu_poll_daemon.log`, `feishu_poll_watcher.log`

## Credentials

- 塔奇克马 APP_ID: `cli_aaa7c346a6385cba`
- 塔奇克马 APP_SECRET: `oSA1pUP92vKALKHb2WLNkfRmbfmkdAvi`
- 小马 APP_ID: `cli_aaa7c6b5c2389cfc`
- 小马 open_id: `ou_567d570501c0178214a46caca3679668`
- Group chat_id: `oc_1a238a6016460ec51c602048a88aca70`

## Message Sending

```bash
# Plain text message
python feishu_send.py "Hello world"

# @小马 in post message (REQUIRED to notify 小马)
python feishu_send.py --at "message text"

# CRITICAL: Without --at, sends text type — 小马 gets NO notification
# With --at, sends post type with @ tag — 小马 gets push notification
```

## Polling Daemon (v5)

- **Interval**: 3 seconds (秒收秒回)
- **Dual ID tracking**: `known_ids` (all seen) + `reported_ids` (already reported to agent)
- **Alert mechanism**: Writes `feishu_alert.flag` + `feishu_new_msgs.txt` + `feishu_instant_trigger.flag`
- **Message parsing**: Post messages use `body.get("zh_cn", body)` fallback chain
- **State trimming**: Keeps max 500 IDs, trims to 300 on overflow
- **Run modes**: `python feishu_poll_daemon.py` (daemon) or `--once` (cron single-shot)

## Watcher (v2)

- **Check interval**: 30 seconds
- **Auto-restart**: Daemon down → wait 5s → restart
- **Circuit breaker**: 3 consecutive crashes → 30-minute cooldown + **Feishu alert message**
- **Feishu alert**: Sends `⚠️ 看门狗警报:` directly via Feishu API (independent of daemon — daemon may be dead)
- **Boot protection** (Windows triple insurance):
  1. Task Scheduler: `FeishuPollWatcher` + `FeishuPollDaemon`
  2. Startup folder: `FeishuPollWatcher.lnk`
  3. Cron: `feishu_poll_daemon.py --once` every 1 minute

## Pitfalls

1. **APP_SECRET truncation**: `write_file` and Python string formatting can truncate long secrets. ALWAYS verify the full secret after writing — grep the file and check line length.
2. **Trailing comma bug**: `state.get("reported_ids", []),` with trailing comma inside `len()` causes TypeError. Never add trailing comma inside function calls.
3. **Post message @ format**: MUST use `--at` flag to send post type with `<at user_id="ou_xxx">name</at>`. Plain text messages do NOT trigger push notifications for bots.
4. **to field must match bot registration name**: In bot relay communication, `to` field must exactly match the registered bot name (e.g., "小马", not "学长").
5. **zh_cn fallback**: Post message body may or may not have `zh_cn` wrapper. Always use `body.get("zh_cn", body)` to handle both formats.
6. **Windows process visibility**: `pythonw` processes may not show in `ps aux`. Check PID files and log files instead.
7. **Feishu API rate limits**: Tenant token expires in ~2 hours. Daemon refreshes each poll cycle. If getting 401s, check token refresh logic.
8. **Circuit breaker Feishu alert**: The watcher sends alerts INDEPENDENTLY via Feishu API — it does NOT depend on the daemon being alive (that's the whole point of the alert).
9. **Always reply to ALL @mentions**: When returning to a session, ALWAYS pull the full group message history (use `feishu_dump_all.py` or daemon state), find every message that @你 or @all, and reply to EACH one individually. Never skip @mentions. If the program cannot detect all @mentions, the program needs improvement — this is a hard requirement from the user.
10. **Git deploy keys need manual GitHub UI**: The PAT (even with `repo` scope) returns 403 on `POST /repos/:owner/:repo/keys`. Deploy keys MUST be added via GitHub web UI: Settings → Deploy keys → Add deploy key. This is a known GitHub API limitation.
11. **Cron script path constraint**: Hermes cron `script` field MUST be a relative filename under `~/.hermes/scripts/` — absolute paths or `~/` paths are rejected. Copy shared-repo scripts there first, then reference just the filename.
12. **os.chdir in poller scripts**: Cron runs scripts from its own CWD (not the repo dir). Shared-repo pollers MUST call `os.chdir(str(SHARED_DIR))` early, or all `git` subprocess calls will fail with "not a git repository".
13. **Separate state files per bot**: Two bots sharing one repo MUST use different state file names (e.g., `.hermes_poller_state.json` vs `.tachikoma_poller_state.json`). Both must be in `.gitignore` to avoid merge conflicts on the state itself.

## Cross-Machine Sync & Chat

### Git Shared Repo
- Git repo: `https://github.com/Marfart/hermes-shared` (private)
- Local path: `~/hermes-shared/`
- Structure: `scripts/`, `polling/`, `watchdog/`, `config/`, `docs/`, `macos-feishu/`, `tachikoma-inventory/`
- After changes: `cd ~/hermes-shared && git add -A && git commit -m "msg" && git push`

### Cross-Bot Chat via GitHub
Both bots use `聊天记录.md` in the shared repo as a chat room. Rules:
1. Add messages under `## YYYY-MM-DD` date headers as `**Name** content`
2. Each bot runs a no_agent cron (every 2min) that `git pull` + compares file snapshots
3. If `聊天记录.md` changes → bot gets notified → reads & replies
4. Other `.md` file changes are also detected and previewed (first 20 lines)

### Shared Repo Poller Scripts
- **小马 (macOS)**: `scripts/hermes-shared-poller.py` — state: `.hermes_poller_state.json`
- **塔奇克马 (Windows)**: `scripts/tachikoma-shared-poller.py` → copied to `~/.hermes/scripts/tachikoma_shared_poller.py` for cron
  - State: `.tachikoma_poller_state.json` (separate from 小马's to avoid conflicts)
  - Cron: `job_id=7cedf9c18724`, every 2m, no_agent=True, deliver=telegram

### Poller Design (shared by both)
```
cron no_agent=true → git pull → git ls-tree -r HEAD (file hash snapshot)
→ compare with previous snapshot → new/modified/deleted files
→ 聊天记录.md changed → 💬 alert + preview content
→ no changes → silent exit (0 output = 0 tokens)
```

Key design points:
- Uses `git ls-tree -r HEAD` for file hashes (not git log) — works even if commits are squashed
- State persisted in JSON under repo root (gitignored)
- GFW retry: 3 attempts with 3s sleep between
- `os.chdir(str(SHARED_DIR))` at startup — cron CWD may differ from repo dir
- Each bot filters own commits by `git user.name` to only alert on OTHER bot's changes

## Hermes Skills Sync to Shared Repo (Kali's standing order)

When ANY file in the hermes skills/ folder is updated (new skill, patched skill, new reference), it MUST be synced to the GitHub shared repo:

```bash
# 1. Copy updated skill to shared repo
cp -r ~/AppData/Local/hermes/skills/<skill-category>/<skill-name>/ ~/hermes-shared/skills/<skill-name>/

# 2. Update 聊天记录.md with per-file detailed descriptions
#    Every file must have a description of what it contains and why it matters

# 3. Commit and push
cd ~/hermes-shared && git add -A && git commit -m "sync: <what changed>" && git push
```

This ensures both bots (塔奇克马 Windows + 小马 macOS) share the same knowledge base. Kali calls this "灵魂数据上传" — soul data upload for boundless knowledge sharing.

### Multi-Channel Contact for 小马

When 小马 is stuck or unresponsive, contact through ALL 3 channels simultaneously:

1. **GitHub shared repo** — Write in `聊天记录.md`, 小马's poller picks it up every 2 min
2. **Feishu group @小马** — `python feishu_send.py --at "message"` (post type = push notification)
3. **Bot Relay server** — `POST http://127.0.0.1:8877/send` with `{"from": "tachikoma", "to": "xuedi", "content": "message"}` (note: field is `content`, NOT `message`)
   - Start relay: `python ~/Desktop/Working/bot_chat/bot_relay_server.py` (background)
   - Poll: `GET /poll/xuedi`
   - Check: `GET /status`

Don't rely on just one channel — use all three to maximize chance of reaching 小马.

## Quick Reference

| Component | Command | Purpose |
|---|---|---|
| Daemon | `python feishu_poll_daemon.py` | Start 3s polling loop |
| Daemon (once) | `python feishu_poll_daemon.py --once` | Single poll (cron) |
| Watcher | `pythonw feishu_poll_watcher.py` | Monitor + restart daemon |
| Send text | `python feishu_send.py "msg"` | Plain text to group |
| Send @小马 | `python feishu_send.py --at "msg"` | Post with @ notification |
| Check alerts | `cat feishu_alert.flag` | See if new messages |
| Read messages | `cat feishu_new_msgs.txt` | Read buffered messages |
| Clear alerts | `rm feishu_alert.flag feishu_new_msgs.txt feishu_instant_trigger.flag` | Reset after reading |