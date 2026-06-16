# Cron Environment Pitfalls on Windows

## Root Cause

Hermes cron jobs with `no_agent=True` run in a **clean environment** via bash (MSYS/git-bash). This environment differs significantly from an interactive terminal session in ways that cause silent failures.

## Known Issues

### 1. `$env:LOCALAPPDATA` is empty

PowerShell scripts that rely on `$env:LOCALAPPDATA` or `$env:USERPROFILE` may find them undefined in cron's clean environment. When these vars are used in `param()` default values, the parameter silently becomes empty string.

**Fix:** Provide a hardcoded fallback:
```powershell
param([string]$StateFile = "")
if (-not $StateFile) {
    $StateFile = "$env:LOCALAPPDATA\hermes\memories\scripts_cache\guard_state.json"
    if (-not $env:LOCALAPPDATA) {
        $StateFile = "C:\Users\Admin\AppData\Local\hermes\memories\scripts_cache\guard_state.json"
    }
}
```

### 2. Chinese paths cause silent exit 1

MSYS bash cannot decode Chinese characters in cron's clean environment. Any path containing Chinese characters (like `脚本缓存`) resolves to a non-existent file, causing `exit 1` without any visible error.

**Fix:** All script paths in cron-adjacent scripts must use pure ASCII. Migrate away from Chinese directory names.

### 3. `tasklist.exe` output locale dependency

On Chinese Windows, `tasklist.exe` outputs Chinese text. `tasklist //FI "PID eq X"` produces messages like:
```
信息: 没有运行的任务匹配指定标准
```

Using `grep -q "$PID"` fails because the output doesn't contain the numeric PID as a match — it's embedded in Chinese prose.

**Fix:** Use `kill -0 $PID` (POSIX, locale-independent) instead of `tasklist` for process existence checks in bash scripts. In Python, use `os.kill(pid, 0)` (but see also: `SystemError` with git-bash Python — fallback to `tasklist` with bytes decode).

### 4. PowerShell doesn't understand POSIX paths

When started from MSYS cron, `Start-Process -FilePath '/c/Users/Admin/...'` receives POSIX-style paths that PowerShell cannot resolve. Even quoted properly, `/c/Users/Admin/...` is not a valid Windows path.

**Fix:** Always pass Windows native paths (`C:\Users\Admin\...`) to PowerShell in cron scripts. Prefer `cmd.exe /c start /B "" "C:\path\to\script.cmd"` over `Start-Process` for background process startup — it handles native paths correctly.

### 5. `$HOME` resolves but may start with `/c/`

MSYS bash translates `%USERPROFILE%` to `$HOME` as `/c/Users/Admin/...`. This POSIX path works for bash commands but not when passed directly to `powershell.exe` or `cmd.exe`. Always double-quote and use MSYS's automatic path conversion, or pass explicit Windows paths.

## Testing Protocol

To simulate cron's clean environment for debugging:
```bash
cd /
env -i HOME="$HOME" PATH="/usr/bin:/bin:/c/Windows/System32:/c/Windows/System32/WindowsPowerShell/v1.0" \
  bash "$HOME/AppData/Local/hermes/scripts/your_script.sh"
echo "EXIT=$?"
```

The `env -i` strips all inherited environment variables, matching cron's sandbox. Only `HOME` and `PATH` are explicitly reintroduced.

## Prevention Checklist for New Cron Scripts

- [ ] All file paths are pure ASCII (no Chinese characters)
- [ ] Script does not rely on `$env:LOCALAPPDATA`, `$env:USERPROFILE`, or other env vars without fallback
- [ ] PowerShell calls use `C:\path\to\file` format, not POSIX `/c/path/to/file`
- [ ] Process checks use `kill -0 $PID` (bash) or `os.kill(pid, 0)` (Python), not locale-dependent `tasklist`
- [ ] Background process startup uses `cmd.exe /c start /B "" ...` not `Start-Process`
- [ ] Tested with `env -i` clean environment before registering as cron