---
name: desktop-watchdog
description: "Monitor a Windows desktop for unauthorized access after the user leaves. Cron-driven, no_agent=true. Arms on '我走了', disarms on '我来了'. Detects 7 event types: reboot, login, screen unlock, USB storage, RDP, remote software, wake-from-sleep."
version: 2.0.0
author: Hermes Agent
license: MIT
platforms: [windows]
trigger: "user says '我走了' (I'm leaving) and wants the computer monitored while away; or any setup of a watch/guard procedure"
metadata:
  hermes:
    tags: [watchdog, guard, desktop-monitor, security, cron, windows, wmi, alarm]
    related_skills: [windows-system-forensics, self-maintenance]
---

# Desktop Watchdog

Monitor a Windows desktop for unauthorized access when the user is away. Uses cron + `no_agent=true` script for silent heartbeat checks, with alert delivery to WeChat or any configured Hermes channel.

Detects **7 event types** without admin elevation (leveraging WMI and available Windows logs):

| # | Event | Detection Method |
|---|-------|-----------------|
| 1 | 🔄 System reboot | `Get-CimInstance Win32_OperatingSystem` boot time comparison |
| 2 | 👤 New user logon | `Get-CimInstance Win32_LogonSession` sessions diff |
| 3 | 🔓 Screen unlock | `Get-WinEvent -FilterHashtable @{LogName='Security'; ID=4801}` |
| 4 | 💾 USB storage insertion | `HKLM:\SYSTEM\CurrentControlSet\Enum\USBSTOR` registry enumeration |
| 5 | 🖥️ RDP remote desktop | `Get-CimInstance Win32_TerminalServiceSession` active RDP sessions |
| 6 | 📡 Remote software running | Process scan for TeamViewer/AnyDesk/向日葵/ToDesk/mstsc/VNC |
| 7 | ⏰ System wake from sleep | `Get-WinEvent -FilterHashtable @{LogName='System'; ID=1,42,107}` |

## When to Use

- User says "我走了" ("I'm leaving") — arm the guard
- User says "我来了" ("I'm back") — disarm the guard
- User asks "有人动过电脑吗?" / "was someone on this computer?"
- Setting up a new guard/monitoring cron job
- Any machine-level presence/intrusion detection

## Architecture (Required: Pure Python)

The bash→PowerShell bridge (**DEPRECATED — DO NOT USE**) is unreliable in cron's clean environment. MSYS bash under cron cannot resolve Chinese paths, `$env:LOCALAPPDATA` is often empty, and `tasklist.exe //FI` output is locale-dependent. **Pure Python is the only supported approach.**

```
┌──────────────────┐    cron every 2 min     ┌──────────────────────────┐
│  User says        │ ─────────────────────→  │  guard_monitor.py        │
│  "我走了" /         │                          │  (no_agent=true Python,  │
│  sets armed=true   │                          │   stdlib + subprocess    │
└──────────────────┘                          │   for WMI calls via PS)  │
                                              └──────┬───────────────────┘
                                                     │
                                              ┌──────▼───────────────────┐
                                              │  guard_state.json        │
                                              │  { armed, lastBoot,      │
                                              │    knownSessions,        │
                                              │    ... v3 fields }       │
                                              └──────┬───────────────────┘
                                                     │ alert detected?
                                                     │ → stdout printed
                                                     │ → cron delivers
                                                     ▼ via configured channel
```

**Why Python over bash→PowerShell bridge:**

| Issue | Bash→PowerShell | Python |
|-------|----------------|--------|
| Path encoding | Chinese chars fail | `pathlib.Path` with ASCII dirs |
| Env vars | `$env:X` may be empty | `os.environ.get("X", fallback)` |
| Process check | `tasklist` locale issues | `subprocess.run` + `str(pid) in stdout` |
| File I/O | `ConvertFrom-Json` fragile | `json.loads()` with error handling |
| Exit codes | Implicit | Explicit `sys.exit(n)` |

## Setup

### 1. Create the state file (`guard_state.json`)

```json
{
  "armed": false,
  "lastBoot": "2026-06-05 12:57:02",
  "knownSessions": [],
  "notifiedBoot": false,
  "notifiedSessions": [],
  "notifiedUnlocks": [],
  "notifiedUSB": [],
  "notifiedRemoteDesktop": [],
  "notifiedWake": [],
  "notifiedRemoteSoftware": false,
  "remoteSoftwareDetected": false,
  "version": 2
}
```

Save to `~/AppData/Local/hermes/memories/脚本缓存/guard_state.json`.

### 2. Create the monitor script (Python, required)

**File:** `guard_monitor.py` (in `~/AppData/Local/hermes/scripts/`)

```python
#!/usr/bin/env python3
"""Guard monitor — pure Python (no_agent=True, cron-safe)."""
import json, os, subprocess, sys
from pathlib import Path

STATE_DIR = Path(os.environ.get("LOCALAPPDATA", "C:\\Users\\Admin\\AppData\\Local")) / "hermes" / "memories" / "scripts_cache"
STATE_FILE = STATE_DIR / "guard_state.json"

def load_state() -> dict:
    if STATE_FILE.exists():
        try: return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except: pass
    return {"armed": False, "lastBoot": "", "knownSessions": [], ...}

def save_state(state: dict) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")

def ps(cmd: str) -> str:
    try:
        r = subprocess.run(["powershell.exe","-NoProfile","-ExecutionPolicy","Bypass","-Command",cmd],
                          capture_output=True, text=True, timeout=15, errors="replace")
        return r.stdout.strip()
    except: return ""

def main() -> int:
    state = load_state()
    if not state.get("armed"): save_state(state); return 0
    output = []
    # ... 7 detection modules call ps() / ps_json() via subprocess ...
    save_state(state)
    if output: sys.stdout.write("\n".join(output))
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

See `scripts/guard_monitor.py` on disk for the full implementation.

### 3. Register the cron job

```bash
hermes cron update <job_id> --script guard_monitor.py
```

Or to create fresh:
```bash
hermes cron create --name "桌面卫士" --schedule "every 2m" --no-agent --script guard_monitor.py --deliver telegram
```

**IMPORTANT:** Use `.py` scripts, not `.sh` wrappers. Cron runs Python scripts directly; `.sh` → `powershell.exe` bridges fail due to:
- Empty `$env:LOCALAPPDATA` in cron's clean environment
- Chinese character resolution failures in MSYS bash
- Locale-dependent `tasklist.exe` output

Find the user's WeChat ID in `channel_directory.json` under the `weixin` platform.

## Arm/Disarm Protocol

### Arm — "我走了" (I'm leaving)

```python
# Python approach (preferred — best control flow)
import json, subprocess, datetime

state_file = os.path.expanduser('~/AppData/Local/hermes/memories/脚本缓存/guard_state.json')
with open(state_file) as f:
    state = json.load(f)

state['armed'] = True
state['notifiedBoot'] = False
state['notifiedSessions'] = []
state['notifiedUnlocks'] = []
state['notifiedUSB'] = []
state['notifiedRemoteDesktop'] = []
state['notifiedRemoteSoftware'] = False
state['notifiedWake'] = []
state['remoteSoftwareDetected'] = False

# Refresh boot time and known sessions
r = subprocess.run(['powershell.exe', '-NoProfile', '-Command',
    '$boot=(Get-CimInstance Win32_OperatingSystem).LastBootUpTime.ToString(\'yyyy-MM-dd HH:mm:ss\');'
    '$s=Get-CimInstance Win32_LogonSession -Filter "LogonType=2 OR LogonType=10"|Where{$_.UserName}|%{"$($_.UserName)|$($_.StartTime.ToString(\'yyyy-MM-dd HH:mm:ss\'))"};'
    "Write-Output \"$boot\";$s -join ';'"],
    capture_output=True, text=True)

parts = r.stdout.strip().split('\n', 1)
state['lastBoot'] = parts[0].strip()
state['knownSessions'] = parts[1].strip().split(';') if len(parts) > 1 else []

with open(state_file, 'w') as f:
    json.dump(state, f, ensure_ascii=False)
```

### Disarm — "我来了" (I'm back)

```python
state['armed'] = False
state['notifiedBoot'] = False
state['notifiedSessions'] = []
state['notifiedUnlocks'] = []
state['notifiedUSB'] = []
state['notifiedRemoteDesktop'] = []
state['notifiedRemoteSoftware'] = False
state['notifiedWake'] = []
# Refresh known sessions + boot time (same as arm)
# Save
```

## 3-Minute Idle Confirmation (Optional)

Pair arm with idle check to confirm the user actually left:

```python
IDLE_THRESHOLD = 180  # 3 minutes — user preference
import ctypes, ctypes.wintypes
last_input = ctypes.wintypes.DWORD()
ctypes.windll.user32.GetLastInputInfo(ctypes.byref(last_input))
idle = (ctypes.windll.kernel32.GetTickCount() - last_input.value) // 1000
if idle < IDLE_THRESHOLD:
    print(f"User said 'leaving' but idle={idle}s — waiting to confirm.")
```

**Why 3 minutes:** The user reads silently — 30s of no input is normal reading, not "away." 180s was confirmed after testing.

## Alert Format

Designed for mobile at-a-glance:

```
⚠️ 电脑卫士｜系统重启
上次启动: 2026-06-04 08:00:00  本次启动: 2026-06-05 12:57:02
```

```
⚠️ 电脑卫士｜屏幕被唤醒解锁
时间: 2026-06-05 14:30:22 — 有人操作了电脑
```

## Pitfalls

### 1. Cron stops when machine shuts down
Watchdog only runs while machine is on + Hermes runs. Boot detection fires ~1-2 min after restart. That gap is acceptable.

### 2. Cron stops when gateway dies (silent disarm)
The cron scheduler lives inside the gateway. If the gateway crashes, `guard_state.json` says `armed=true` but no one checks. **Mitigations:**
- Pair with gateway fallback watchdog (see `self-maintenance` skill)
- After returning, check `guard_state.json` for staleness

### 3. Hermes must auto-start
Use Startup folder: `~/AppData/Roaming/Microsoft/Windows/Start Menu/Programs/Startup/hermes_gateway.cmd`

### 4. No admin = no Security event log
Events 4801 (screen unlock) and 4624 (logon) require admin rights for `Get-WinEvent -FilterHashtable @{LogName='Security'}`. If running without admin, those checks silently fail (try/catch) and the watchdog still covers reboot + logon via WMI.

### 5. State file atomic writes
Always write to `.tmp` then `Move-Item` to avoid corruption from mid-write interruption.

### 6. Filter out service accounts
Skip `DWM-*`, `UMFD-*`, `SYSTEM` logons — these are desktop manager accounts appearing on every boot.

### 7. Notified list growth
Each `notified*` array grows unbounded. Prune to last 50 entries on every run (shown in cleanup loop above).

### 9. Cron environment pitfalls

See `self-maintenance/references/cron-environment-pitfalls.md` for the full catalog:

- `$env:LOCALAPPDATA` can be empty in cron's clean environment
- Chinese characters in paths are unresolvable by MSYS cron
- `tasklist.exe //FI` output is Windows-locale dependent
- PowerShell `Start-Process` chokes on POSIX paths passed from MSYS

**Preferred mitigation:** Use pure Python scripts instead of the bash→PowerShell bridge. Python handles all of these issues natively.

### 8. False positives on first arm
When arming for the first time, the script sees ALL current USB devices as "new." To avoid this, the arm script should also record current connected USB serials before setting `armed=true`.

## Verification

- [ ] State file is valid JSON
- [ ] Script exits 0 when disarmed
- [ ] Script prints alert when armed with stale boot time
- [ ] All 7 detection types fire during testing
- [ ] Cron delivers to WeChat
- [ ] Arm/disarm toggles correctly
- [ ] Re-arming after disarm does NOT re-alert already-known events

## References

See `references/guard-state-management.md` for the full state file schema, atomic write patterns, and delivery ID lookup.