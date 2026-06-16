# Gateway Fallback Watchdog — Reference Implementation

## Problem

Hermes cron runs inside the gateway process. When the gateway crashes, all cron jobs die with it — including the watchdog that's supposed to restart the gateway. This creates a dead-locked failure: "who watches the watcher?"

## Solution Architecture

**Windows Task Scheduler** is the platform-level watchdog. It does not depend on Hermes, Python, or any runtime that the gateway manages. It runs as a standalone `schtasks` entry triggered every 3 minutes.

```
schtasks (every 3 min)
  ↓
gateway_watchdog_fallback.bat
  ↓
gateway_watchdog_fallback.py
  ↓
  ├─ Read gateway_state.json (PID)
  ├─ tasklist /FI "PID eq X"  →  confirm alive?
  │   ├─ YES → silent exit (0 output, 0 returncode)
  │   └─ NO  → kill residuals → restart gateway → update state file PID
  ↓
Gateway reconnects → cron fires → Layer-2 watchdog delivers "all clear"
```

## Key Design Decisions

### 1. .bat wrapper, not direct .py execution
On Windows, `.py` file association may point to PyCharm or another IDE instead of `python.exe`. This causes `schtasks` to open PyCharm instead of running the script. The `.bat` wrapper explicitly invokes the Hermes venv's python:

```bat
@echo off
"%~dp0..\hermes-agent\venv\Scripts\python.exe" "%~dp0gateway_watchdog_fallback.py"
```

### 2. PID liveness check via tasklist
`os.kill(pid, 0)` crashes with `SystemError` on git-bash Python. Instead use:
```python
r = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/NH"], capture_output=True, timeout=10)
return str(pid) in (r.stdout or b"").decode("gbk", errors="replace")
```

### 3. GBK decoding for Chinese Windows locale
All Windows built-in tools (`schtasks`, `tasklist`, `ipconfig`, `ping`) output in the system locale (GBK on Chinese Windows). Using `text=True` with `subprocess.run` causes `UnicodeDecodeError`. Always:
```python
r = subprocess.run([...], capture_output=True, timeout=10)  # bytes mode
out = r.stdout.decode("gbk", errors="replace") if r.stdout else ""
err = r.stderr.decode("gbk", errors="replace") if r.stderr else ""
```

### 4. Clean gateway restart
```python
# Kill any residual gateway processes
r = subprocess.run(["tasklist", "/FO", "CSV", "/NH"], capture_output=True, timeout=10)
for line in out.split("\n"):
    if "gateway" in line.lower() or "main.py" in line.lower():
        pid = parts[1].strip().strip('"')
        subprocess.run(["taskkill", "/f", "/pid", pid], capture_output=True, timeout=5)

# Start new gateway
proc = subprocess.Popen(
    [str(hermes_venv), "gateway", "run"],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    creationflags=subprocess.CREATE_NO_WINDOW,
)
write_state(proc.pid)
```

### 5. State file PID update
After restarting, update `gateway_state.json` with the new PID so that:
- Subsequent watchdog checks use the correct PID
- The cron-based Layer-2 watchdog finds the live process

## Installation

```cmd
schtasks /CREATE /TN HermesGatewayFallbackWatchdog /SC MINUTE /MO 3 /TR "C:\path\to\gateway_watchdog_fallback.bat" /F
```

## Verification

```powershell
schtasks /QUERY /TN HermesGatewayFallbackWatchdog /FO LIST /V
# Expected: Status=Ready, Schedule=every 3 min, Task=...fallback.bat
```

Test the fallback by killing the current gateway:
```powershell
taskkill /F /PID <current-gateway-pid>
# Wait up to 3 minutes → checkpoint task list
tasklist /FI "IMAGENAME eq python*" | findstr hermes
# Should see a new gateway process
```

## When Not to Use

- If the gateway process is not running as a persistent daemon (e.g., running CLI-only sessions without a gateway)
- If the computer has no Windows Task Scheduler (Linux, macOS) → use systemd timers or launchd instead