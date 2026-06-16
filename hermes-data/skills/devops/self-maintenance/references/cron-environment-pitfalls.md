# Cron Environment Pitfalls on Windows (MSYS)

When running `no_agent=True` cron scripts on a Windows host via MSYS git-bash, the environment differs significantly from an interactive terminal session. This document catalogs known issues and verified fixes.

## Issue Catalog

### 1. Empty Environment Variables

**Symptom:** `$env:LOCALAPPDATA` or `$env:USERPROFILE` returns empty string in PowerShell called from cron.

**Root cause:** Cron launches scripts in a minimal environment — user-scoped env vars may not propagate.

**Fix (Python — recommended):** Use `os.environ.get("VAR", "fallback")`:
```python
STATE_DIR = Path(os.environ.get("LOCALAPPDATA", "C:\\Users\\Admin\\AppData\\Local")) / "hermes"
```

### 2. Chinese Characters in Paths

**Symptom:** Script exits with code 1 silently. Logs show nothing.

**Root cause:** MSYS bash under cron cannot resolve paths containing Chinese characters (e.g., `脚本缓存`).

**Fix:** Use only ASCII path segments. Move files from `脚本缓存/` to `scripts_cache/` or `scripts/`.

### 3. PowerShell Start-Process Path Format

**Symptom:** `Start-Process -FilePath '/c/Users/Admin/.../script.cmd'` fails.

**Root cause:** MSYS converts paths to POSIX format (`/c/Users/...`), which PowerShell doesn't recognize.

**Fix:** Use Windows-native paths (backslashes, drive letter) in PowerShell, or better, avoid PowerShell entirely.

### 4. tasklist.exe Locale Dependency

**Symptom:** `tasklist.exe //FI "PID eq 1234"` returns locale-specific output that `grep` can't match.

**Fix (bash):** Use `kill -0 $PID` instead:
```bash
kill -0 "$OLD_PID" 2>/dev/null && echo "alive" || echo "dead"
```

### 5. cmd.exe /c start Hangs Cron (120s timeout)

**Symptom:** Cron job that spawns a background process via `cmd /c start /B script.cmd` times out after 120 seconds.

**Root cause:** `start /B` launches a process that inherits the parent's console — cron sees the process as still running.

**Fix — DETACHED_PROCESS (Python):**
```python
import subprocess
subprocess.Popen(
    [python_exe, script_path],
    creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NO_WINDOW,
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL,
)
```

This completely disconnects the child process from cron's wait tracking.

### 6. stdout Encoding: Unicode Output Becomes Garbled (CP936/GBK Mojibake)

**Symptom:** Cron output with Chinese characters, emoji, or any Unicode renders as garbled text. Common examples:
- `🔍` → `馃攼`
- `证书升级` → `璇佷功鍗囩骇`
- `⚠️` → `寮傚父`

**Root cause:** When `no_agent=True` cron captures a script's stdout, it reads the bytes using the system's default ANSI codepage (cp936/GBK on Chinese Windows, cp932 on Japanese, cp1251 on Russian, etc.). Python's `sys.stdout.reconfigure(encoding='utf-8')` inside the script does NOT change how cron decodes the captured bytes.

The captured bytes ARE correct UTF-8, but cron then decodes them with the system encoding:
```
Script:  print("🔍")
  → Python writes UTF-8 bytes (F0 9F 94 8D) to stdout pipe
  → cron reads bytes and decodes as cp936
  → cp936 tries to interpret F0 9F as GBK characters → produces garbled Unicode
  → Telegram/WeChat receives garbled text
```

**Fix — Pure ASCII output only:** Every string that reaches `print()` or stdout must use only ASCII characters (codepoints 0-127). Replace all non-ASCII with ASCII equivalents:

| Replace | With |
|---------|------|
| `🔍` / `⏱️` / `📊` / `📋` | `[WATCH]` / `[TIME]` / `[STATUS]` / `[DIAG]` |
| `✅` / `❌` / `⚠️` | `[OK]` / `[FAIL]` / `[WARN]` |
| `🔧` / `🔐` / `🔄` | `[FIX]` / `[SSL]` / `[RESTART]` |
| Chinese status text | English equivalents |
| Any Unicode emoji | `[TAG]` style markers |

**Verification that fix works:**
```bash
python -c "
import subprocess, sys
r = subprocess.run([sys.executable, 'your_script.py'], capture_output=True)
cp936 = r.stdout.decode('cp936', errors='replace')
utf8 = r.stdout.decode('utf-8', errors='replace')
print('SAME:', cp936 == utf8)  # Should be True
"
```

**This is a DESIGN LIMITATION of the cron capture pipeline, not a script bug.** No amount of Python-side encoding configuration (reconfigure, TextIOWrapper, PYTHONIOENCODING) changes how cron decodes captured stdout. The only reliable solution is ASCII-only output.

**Case study:** `smart_watchdog_v8.py` was fully converted to ASCII-only output on 2026-06-08 after multiple encoding fix attempts failed. The output went from garbled Chinese to clean English `[OK]`/`[WARN]`/`[STATUS]` markers.

### 7. Python Availability in Cron

**Symptom:** Cron can't find `python` or uses wrong interpreter.

**Fix:** Use absolute path to the venv Python or system python.

### 8. PowerShell subprocess.run Pops a Flash Window (CREATE_NO_WINDOW)

**Symptom:** Every 2 minutes (or whatever the cron interval is), a PowerShell black window pops up and disappears instantly. Many such windows flash in rapid succession, alarming the user.

**Root cause:** `subprocess.run(["powershell.exe", "-NoProfile", ...], ...)` on Windows creates a visible console window by default for each invocation. When a no_agent=True cron script calls PowerShell 7+ times per tick (e.g., guard_monitor.py's 7 detection modules), the result is 7+ rapid-fire flash windows every cron cycle.

**Fix — `creationflags=0x08000000`:** Add `creationflags=subprocess.CREATE_NO_WINDOW` (or the raw constant `0x08000000`) to every `subprocess.run` that invokes powershell.exe:
```python
r = subprocess.run(
    ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", cmd],
    capture_output=True, text=True, timeout=15, errors="replace",
    creationflags=0x08000000  # ← CREATE_NO_WINDOW — no black popup
)
```

**Also fix `subprocess.Popen` for the same reason** when launching PowerShell or any Win32 GUI tool:
```python
subprocess.Popen(
    [...],
    creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NO_WINDOW,
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL,
)
```

**Verification:** After applying the fix, run the script manually from a bash/terminal session:
```bash
python guard_monitor.py
```
No PowerShell windows should flash. The script output still works correctly.

**Detection pattern in code review:** When reviewing a new or modified no_agent cron script on Windows, search for:
- `subprocess.run` without `creationflags=subprocess.CREATE_NO_WINDOW`
- `subprocess.Popen` without `creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NO_WINDOW`
- Any bare `["powershell.exe", ...]` call with no window suppression

**Note:** This only fixes the *flash window* problem. If the PowerShell command itself is slow (e.g., `Get-WinEvent` scanning the entire Security log), the total run time of the script still accumulates. Consider reducing the number of PowerShell calls per tick, or coalescing multiple detections into a single PowerShell command.

## Verification Protocol

After any cron script fix, test identically to how cron runs:

```bash
cd /
env -i HOME="$HOME" PATH="/usr/bin:/bin:/c/Windows/System32" bash script.sh
# Or for Python
cd /
env -i HOME="$HOME" PATH="/usr/bin:/bin:/c/Windows/System32/WindowsPowerShell/v1.0" python script.py
echo "EXIT=$?"
```

## Golden Rule

**Use pure Python for all no_agent cron jobs.** The bash→PowerShell bridge is a source of constant environment-dependent failures. Python handles all of the above issues natively.
