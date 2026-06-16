---
name: windows-system-forensics
description: "Investigate Windows system state: login history, event logs, boot/shutdown records, session activity. Run from non-elevated git-bash/MSYS terminals by using Start-Process -Verb RunAs elevation pattern."
version: 1.2.0
author: Hermes Agent
license: MIT
platforms: [windows]
trigger: "user asks about recent logins, who used the computer, boot/shutdown history, or any Windows event log query"
metadata:
  hermes:
    tags: [windows, forensics, event-log, security, login-history, system-audit, windows-admin]
    related_skills: [self-maintenance]
---

# Windows System Forensics

Query Windows Security and System event logs from a **non-elevated git-bash/MSYS terminal** to answer questions like "who logged in last night?", "when was the last shutdown?", "was someone on this computer?"

## When to Use

- User asks "有人动过我的电脑吗？" / "有人用过这台电脑吗？" / "was anyone on this computer?"
- User asks about login times, shutdown times, boot history
- Any investigation of Windows Security or System event logs
- Checking user session activity (lock/unlock/logoff)

## ⚡ Quick Checks First (No Elevation Needed)

For the common question "有人动过我电脑吗", **start here** — these techniques work from git-bash/MSYS as a non-admin user and handle ~90% of cases without needing elevation:

### 1. Uptime → how long since last boot

```bash
sys_uptime()  # or from terminal: 'cat /proc/uptime' (not on Windows)
# Git-bash workaround:
powershell -Command "(Get-CimInstance Win32_OperatingSystem).LastBootUpTime.ToString('yyyy-MM-dd HH:mm:ss')"
```

### 2. Desktop file timeline (best evidence)

This is the **single most useful non-elevated check**. Users touch Desktop files in chronological order:

```bash
python -c "
import os, datetime
desktop = os.path.expanduser('~/Desktop')
now = datetime.datetime.now()
today = now.replace(hour=0, minute=0, second=0, microsecond=0)
for f in sorted(os.listdir(desktop), key=lambda x: os.path.getmtime(os.path.join(desktop, x)), reverse=True):
    fp = os.path.join(desktop, f)
    if os.path.isfile(fp):
        mtime = datetime.datetime.fromtimestamp(os.path.getmtime(fp))
        if mtime >= today:
            print(f\"{mtime.strftime('%H:%M')} | {os.path.getsize(fp)//1024:>5}KB | {f[:55]}\")
"
```

**Pattern**: If all file timestamps match the user's known working hours and the files they were working on, no intrusion. Anomalous files or timestamps outside user's active hours = further investigation.

### 3. Network connections → external IPs

```bash
netstat -n | grep ESTABLISHED | grep -v "127.0.0.1\|\[::1\]"
```

This catches RDP, TeamViewer, or any remote connection originating from outside. If **all** established connections are `127.0.0.1:7897` (Vortex proxy) and `127.0.0.1:39798` (Hermes itself), you're clean.

### 4. Remote software processes

```bash
python -c "
import subprocess
r = subprocess.run('tasklist //NH', shell=True, capture_output=True, text=True, timeout=10)
kws = ['rdpclip','mstsc','teamviewer','anydesk','vnc','remote','rdp','sunlogin','gameviewer','todesk']
text = r.stdout.lower()
for kw in kws:
    if kw in text: print(f'FOUND: {kw}')
print('No remote software running' if all(kw not in text for kw in kws) else '')
"
```

### 5. Startup items (persistence check)

```bash
python -c "
import subprocess
r = subprocess.run('reg query \"HKCU\\\\SOFTWARE\\\\Microsoft\\\\Windows\\\\CurrentVersion\\\\Run\"', shell=True, capture_output=True, text=True, timeout=10)
print(r.stdout[:2000])
"
```

### Decision Tree

```
User asks "有人动过吗？"
  │
  ├─ Check uptime (was it rebooted?)
  ├─ Check Desktop timeline (files match user's work?)
  ├─ Check network connections (any external IPs?)
  ├─ Check remote software processes
  ├─ Check startup items (new autoruns?)
  │
  ├─ All clean → report "没有人动过 ✅"
  └─ Suspicious → proceed to elevated event log forensics below
```

## Core Technique: Elevated PowerShell from Non-Elevated Terminal

The fundamental challenge: from git-bash/MSYS, you're running with a filtered (non-elevated) token even as an admin user. You cannot read the Security event log directly. The Windows elevation pattern is `Start-Process -Verb RunAs`, but **stdout from the elevated process is NOT captured** by the parent.

**The fix: write .ps1 scripts to disk → elevate → Out-File to a known path → read the result.**

### Step-by-Step

```powershell
# 1. Write a script that queries what you need and saves output to a file
Write-Output "...query..." | Out-File C:\Users\Admin\Desktop\result.txt -Encoding UTF8

# 2. Launch it elevated
Start-Process powershell -Verb RunAs -ArgumentList '-NoProfile -ExecutionPolicy Bypass -File C:\Users\Admin\Desktop\script.ps1' -WindowStyle Hidden -PassThru | Wait-Process

# 3. Read the result
Get-Content C:\Users\Admin\Desktop\result.txt
```

⚠️ **Always pair `-PassThru` with `| Wait-Process`** to ensure the elevated command completes before you try to read the output file.

## Event ID Reference

### Security Log (Event ID 4624 — Logon)
| Logon Type | Meaning |
|------------|---------|
| 2 | Interactive (local console login) |
| 5 | Service (background services — ignore these) |
| 10 | RemoteInteractive (RDP) |

### System Log — Boot/Shutdown
| Event ID | Meaning |
|----------|---------|
| 12 | OS boot (kernel start) |
| 6005 | Event log service started (shows boot completion) |
| 6006 | Event log service stopped (graceful shutdown) |
| 1074 | Shutdown initiated (shows reason + user) |
| 41 | Unexpected shutdown (blue screen / power loss) |
| 6008 | Unexpected shutdown (previous shutdown was dirty) |

### Security Log — Session Events
| Event ID | Meaning |
|----------|---------|
| 4800 | Workstation locked |
| 4801 | Workstation unlocked |
| 4802 | Screensaver started |
| 4803 | Screensaver stopped |
| 4647 | User initiated logoff |

## Common Queries

### All interactive logins (last 500 events)

```powershell
Get-WinEvent -FilterHashtable @{LogName='Security'; ID=4624} -MaxEvents 500 |
    Where-Object { $_.Properties[8].Value -eq 2 -or $_.Properties[8].Value -eq 10 } |
    ForEach-Object { 
        $_.TimeCreated.ToString('yyyy-MM-dd HH:mm:ss') + ' | ' + $_.Properties[5].Value + ' | Type:' + $_.Properties[8].Value 
    }
```

### Today's full timeline (logins + sessions)

```powershell
# Logins
Get-WinEvent -FilterHashtable @{LogName='Security'; ID=4624} -MaxEvents 200 | Where-Object { $_.Properties[8].Value -in @(2,10) } | ForEach-Object { ... }

# Lock/unlock/logoff
Get-WinEvent -FilterHashtable @{LogName='Security'; ID=4800,4801,4802,4803,4647} -MaxEvents 50 | ForEach-Object { ... }
```

### Last N shutdown/boot events

```powershell
# Shutdowns
Get-WinEvent -FilterHashtable @{LogName='System'; ID=1074,6006} -MaxEvents 10

# Boots
Get-WinEvent -FilterHashtable @{LogName='System'; ID=12,6005} -MaxEvents 5
```

### User SID resolution

If events show SIDs (e.g. `S-1-5-21-...-1000`) instead of usernames:
```powershell
$sid = [System.Security.Principal.SecurityIdentifier]::new('S-1-5-21-...-1000')
$sid.Translate([System.Security.Principal.NTAccount]).Value
```

## Pitfalls

### 1. Elevated stdout is invisible
The most common mistake: call `Start-Process -Verb RunAs` expecting to capture output. You won't get any. Always redirect to a file inside the elevated script, then read that file.

### 2. UAC dialog in headless mode
If running non-interactively (cron job, headless server), UAC elevation won't work — no GUI to click "Yes". In that case, the script must already be running as admin or use a scheduled task (which itself requires admin).

### 3. CodexSandboxOffline / service accounts
Don't confuse service accounts with human users. `CodexSandboxOffline` is created by Codex CLI. `DWM-1` / `UMFD-0` are Windows desktop/session manager accounts — they show up on every boot+login.

### 4. Wait-Process is essential
Without `-PassThru | Wait-Process`, the parent terminal continues immediately and reads an empty/stale output file. Always wait.

### 5. Filter out Logon Type 5 (Service)
Service logons (Type 5) from SYSTEM account dominate the Security log and create noise. Always filter with `Where-Object { $_.Properties[8].Value -in @(2,10) }` unless you specifically need service logons.

### 6. Non-elevated fallbacks are limited
Without elevation, you can still get partial info via:
- `Get-CimInstance Win32_LogonSession` (current sessions only)
- `Get-CimInstance Win32_NetworkLoginProfile` (last logon time per user, no logoff)
- `wmic netlogin get name,lastlogon` (same data)
These are useful for quick checks but lack the full event log detail.

### 7. PowerShell 5.1 UTF-8 encoding sensitivity
When the agent's `write_file` tool saves `.ps1` files, it writes **UTF-8 without BOM**. PowerShell 5.1 (the default on Windows 10/11) sometimes rejects these files with `ParserError: UnexpectedToken` — the error message may show wrong line numbers (e.g. `} else {` at line 9). The actual problem is the encoding, not the syntax.

**Fix:** After `write_file`, re-encode the file through PowerShell itself:
```powershell
Get-Content '.ps1' -Raw -Encoding UTF8 | Out-File '.ps1' -Encoding UTF8
```
Or use `Set-Content -Encoding UTF8` from within the elevated script when writing output. For script files that will be executed by PowerShell directly, always ensure a BOM or UTF16 encoding.

### 8. `2>$null` eaten by bash parser
When invoking PowerShell from **bash** (git-bash/MSYS), the syntax `2>$null` is interpreted by bash's shell parser as a file redirect to a file named `$null`, NOT as PowerShell's null-stream redirect. This causes PowerShell parser errors like `MissingFileSpecification`.

**Fix options:**
- Replace `2>$null` with `-ErrorAction SilentlyContinue` (PowerShell parameter)
- Wrap the entire PowerShell command string in **single quotes** from bash's perspective
- Use `$null` with proper quoting: write a `.ps1` script file instead of inline commands
- Example of the failure: `powershell -Command "Get-Process -Name 'foo' 2>$null"` → bash eats the `2>`
- Example of the fix: `powershell -Command "Get-Process -Name 'foo' -ErrorAction SilentlyContinue"`

### 9. Temp script cleanup (Agent habit)
After running forensics queries, temp `.ps1` scripts and output files accumulate. **Never leave them on the Desktop.** Store reusable helpers under:
```
~/AppData/Local/hermes/memories/脚本缓存/<category>/
```
Use subfolders like `admin助手/`, `系统查询/` to keep organized. Clean up output files from `$env:TEMP` after reading results.

## Reference Files / Scripts

| File | Purpose |
|------|---------|
| `references/login-query-scripts.md` | Ready-to-copy .ps1 script templates for common forensics queries |
| `scripts/run-admin.ps1` | Generic admin elevation runner (pass -Command or -ScriptPath) |
| `scripts/admin-ps.sh` | Bash wrapper — add to PATH for quick `admin-ps "command"` |

## Related Skills

### 🥇 Golden Rule: Local Data First

When asked about security/credentials on a Windows machine, **check local data before reaching for remote tools**. Priority:

1. Browser saved passwords (Edge AES-GCM) — yields the most credentials
2. Config files (.env, auth.json, .git-credentials) — API keys in plaintext
3. Credential Manager (cmdkey) — stored app/network credentials
4. Shell history — often contains API keys and passwords
5. Office temp files (~$) — hints about password spreadsheets
6. SAM/SYSTEM hives (via UAC elevation) — NTLM hashes

**Validated (2026-06-08):** Edge browser yielded **208 decrypted passwords across 160+ domains** — more valuable than any single remote scan. SAM extraction yielded the Admin NTLM hash, though it was not crackable with rockyou (see `references/credential-harvesting.md` for the full workflow).

**Complete credential extraction workflow:**
- No elevation needed: browser passwords, config files, git credentials, shell history
- Elevation needed (UAC prompt): SAM/SYSTEM hive dump → NTLM hash → hashcat crack
- Tools: Python (DPAPI + cryptography), pypykatz OffineRegistry, hashcat -m 1000

### Local Credential Harvesting (`references/credential-harvesting.md`)

**When to use:** user asks about extracting credentials from this machine, or when doing a thorough security audit of what data is exposed locally. Covers Edge/Chrome AES-GCM password decryption, .env and config file discovery, git credential extraction, cmdkey enumeration, PowerShell history scanning, Office temp file recovery, and SAM/SYSTEM hive dump with UAC elevation. **Browser passwords work without elevation**; SAM dump requires UAC.

## Related Skills

### Desktop Watchdog (`desktop-watchdog`)
While this skill is for **investigating** past activity (forensics), the companion
`desktop-watchdog` skill provides **real-time monitoring**: it watches the desktop
while the user is away and sends alerts when someone boots the computer or logs in
without permission. See `references/companion-guard-skill.md` for details.

## Detecting Stuck / Idle / Zombie Processes

When a user reports "another X is stuck/frozen/hanging", use this diagnostic chain to determine whether the process is actually blocked or just waiting for input.

### 1. List candidate processes

```powershell
Get-Process -Name hermes,node,codex -ErrorAction SilentlyContinue |
    Select-Object Id, ProcessName, CPU, StartTime, Responding, Threads |
    Format-Table -AutoSize
```

Key indicator: **CPU ≈ 0 + Responding=True + no recent activity** usually means the process is alive but stuck waiting for user input or blocked on I/O.

### 2. Check parent process (is it a terminal waiting for input?)

```powershell
Get-CimInstance Win32_Process -Filter 'ProcessId=<TARGET_PID>' |
    Select-Object ProcessId, Name, CommandLine, ParentProcessId, CreationDate
```

Then check the parent:
```powershell
Get-CimInstance Win32_Process -Filter 'ProcessId=<PARENT_PID>' |
    Select-Object ProcessId, Name, CommandLine
Get-Process -Id <PARENT_PID> | Select-Object Id,Name,MainWindowTitle
```

- If `MainWindowTitle` is empty → background/headless terminal — likely waiting for stdin
- If `MainWindowTitle` has a path or prompt → the user left a terminal open

### 3. Check for visible windows

```powershell
Add-Type @"
using System;
using System.Runtime.InteropServices;
using System.Text;
public class WinAPI {
    [DllImport("user32.dll")] public static extern IntPtr GetWindowThreadProcessId(IntPtr hWnd, out uint lpdwProcessId);
    [DllImport("user32.dll")][return: MarshalAs(UnmanagedType.Bool)] public static extern bool EnumWindows(EnumWindowsProc lpEnumFunc, IntPtr lParam);
    public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);
    [DllImport("user32.dll", CharSet=CharSet.Auto)] public static extern int GetWindowText(IntPtr hWnd, StringBuilder lpString, int nMaxCount);
    [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr hWnd);
}
"@
$results = [System.Collections.ArrayList]::new()
$callback = [WinAPI+EnumWindowsProc]{ param($hWnd,$lParam)
    $sb = New-Object System.Text.StringBuilder 512
    [WinAPI]::GetWindowText($hWnd, $sb, 512) | Out-Null
    $pid = 0; [void][WinAPI]::GetWindowThreadProcessId($hWnd, [ref]$pid)
    if ($pid -eq <TARGET_PID> -or $pid -eq <PARENT_PID>) {
        [void]$results.Add([PSCustomObject]@{Title=$sb.ToString(); Pid=$pid; Visible=[WinAPI]::IsWindowVisible($hWnd)})
    }; return $true
}
[WinAPI]::EnumWindows($callback, [IntPtr]::Zero) | Out-Null
$results | Format-Table -AutoSize
```

**⚠️ PowerShell $pid variable conflict:** Inside the callback, the automatic variable `$pid` is read-only (it always holds the current PowerShell process ID). Using `$pid` as a local variable causes `SessionStateUnauthorizedAccessException`. Always use a different variable name like `$procId` or `$pIdOut`.

### 4. Interpretation

| Pattern | Likely Diagnosis |
|---------|-----------------|
| CPU=0, Responding=True, parent is a terminal | CLI tool waiting for stdin — user opened it and left |
| CPU=0, Responding=True, no parent visible | Background daemon or cron job waiting for schedule |
| CPU=0, Responding=False | Deadlock — process is hung on a mutex or kernel call |
| CPU=100%, Responding=True | Actively working — not stuck |
| CPU >0 but no output in 10+ min | Blocked on I/O (network, file lock, or pipe buffer full) |

### 5. Resolution

Once diagnosed, offer to kill the stuck process:
```powershell
taskkill //F //PID <TARGET_PID>
```

Or from bash/git-bash:
```bash
taskkill //F //PID <TARGET_PID> 2>/dev/null
```

⚠️ Only kill if the user confirms — a process that's "waiting for input" is not truly stuck and may be something the user intentionally left running.

## Verification

- [ ] Can read Security log events (ID 4624) via elevated PowerShell
- [ ] Can distinguish interactive (Type 2) from service (Type 5) logons
- [ ] Can reconstruct full timeline: boot → login → activity → lock → unlock → logoff → shutdown
- [ ] Output file written successfully after Wait-Process returns
- [ ] Can detect idle/stuck processes by examining CPU + Responding + parent chain
- [ ] Knows to avoid PowerShell `$pid` conflict in EnumWindows callbacks
- [ ] Can offer precise kill command when user confirms a stuck process
