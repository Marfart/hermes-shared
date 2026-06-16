# Desktop Watchdog — Cross-Reference

The `desktop-watchdog` skill (under `devops/`) provides the complete system for
monitoring a Windows desktop for unauthorized access when the user is away.

It complements `windows-system-forensics` by providing the **real-time monitoring
and alerting** layer, while this skill provides the **forensic investigation**
layer (looking back at what happened).

## When to use which

| You want... | Use... |
|-------------|--------|
| Real-time alert when someone opens the computer | `desktop-watchdog` |
| Investigate what happened last night / yesterday | `windows-system-forensics` |
| Full admin-level event log access | `windows-system-forensics` (elevated) |
| No-admin-needed presence detection | `desktop-watchdog` (WMI-based) |
| Alert delivery via WeChat/Telegram | `desktop-watchdog` (cron delivery) |

## Script locations

The guard monitor scripts are stored under `memories/脚本缓存/系统查询/`:
- `guard_monitor.ps1` — the PowerShell monitor
- `guard_monitor.sh` — bash wrapper (also symlinked in `~/AppData/Local/hermes/scripts/`)
- `guard_state.json` — arm/disarm state and known sessions tracking

## Pitfall shared by both skills

**Elevated-only Security log access** — The watchdog avoids this by using WMI
(no admin needed), but at the cost of only seeing *currently active* sessions.
If you need to catch sessions that started-and-ended between cron ticks,
use the elevated `Get-WinEvent` pattern from this skill instead.
