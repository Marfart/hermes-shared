# Cron Burst & Cloud Sync Coordination

## The Problem: iLink Rate Limiting from Cron Bursts

Multiple cron jobs delivering to Weixin simultaneously trigger iLink rate limiting (`ret=-2`). The iLink API enforces per-account frequency limits.

**Log signature:**
```
rate limited for o9cq8070; backing off 3.0s before retry  (×4)
→ iLink sendmessage rate limited: ret=-2 errcode=None errmsg=rate limited
```

## Mitigation Strategies

### 1. Stagger Cron Schedules
Avoid having multiple cron jobs fire at the same minute:
- Daily update: `0 12 * * *` 
- Finance briefing: `30 8 * * 1-5`
- Self-evolution: `0 10 * * *`

### 2. Use `deliver=local` for Silent Jobs
Cron jobs that only run scripts or check state (no user message) should use `deliver=local`. They don't touch the iLink channel at all — zero rate limit risk.

### 3. Watchdog Scripts as `no_agent=True`
All gateway health check scripts run as `no_agent=True` with `script=` path — zero LLM tokens, zero iLink usage unless they detect a real problem.

## Backup Sync: Cron + Cloud Drive

### Architecture
```
Hermes home (%LOCALAPPDATA%/hermes/)
  └─ every 3m ──▶ Desktop/Working/Hermes/ (Google Drive sync target)
```

### Why no bidirectional sync?
Hermes hardcodes `%LOCALAPPDATA%/hermes/` paths internally. Changing this to a cloud-drive path would break tool discovery, config loading, and session storage. Instead, a one-way incremental sync pushes new/changed files to the cloud-synced copy.

### The Sync Script Pattern
- md5 hash comparison, not mtime (survives file moves)
- State file at `memories/脚本缓存/hermes_sync_state.json`
- Silent on no-change; only stdout on actual sync
- Startup sync via Windows Startup folder `.cmd` wrapper

### Files to Sync (small, meaningful)
`config.yaml`, `.env`, `auth.json`, `skills/`, `scripts/`, `memories/`, `cron/`, `weixin/`

### Files to Skip (too large or transient)
`state.db*` (session DB), `logs/`, `cache/*`, `audio_cache/`, `hermes-agent/` (git), `sessions/`, `venv/`, `node_modules/`