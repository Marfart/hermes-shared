# Python Windowless Mode on Windows (pythonw.exe)

## Problem
On Windows, cron scripts using `python.exe` (or `python3` shebang) spawn a visible console window (小黑窗) for every execution. With 10+ cron jobs running every 2-5 minutes, this creates constant popup spam.

## Root Cause
- `venv/Scripts/python.exe` — Python launcher that allocates a console window
- `venv/Scripts/pythonw.exe` — Python launcher that does NOT allocate a console window
- Both are identical Python launchers (same MD5, same size), differing only in console allocation
- git-bash PATH resolves `python` → `python.exe` (the console version)

## Fix (2026-06-22)
Replace `python.exe` with a copy of `pythonw.exe` in the venv Scripts directory:

```bash
cd $HERMES_HOME/hermes-agent/venv/Scripts/
mv python.exe python_console.exe   # backup original
cp pythonw.exe python.exe          # windowless version takes over
```

After this, all scripts that call `python` (via shebang `#!/usr/bin/env python3` or PATH resolution) will run windowless.

## Notes
- WindowsApps `python.exe` and `python3` (0-byte stubs that redirect to Microsoft Store) are not used — git-bash resolves to venv first
- If you need a console window for debugging, use `python_console.exe` explicitly
- This affects ALL Python scripts run from git-bash/cron, not just Hermes scripts
- Hermes itself is a Node.js app, unaffected by this change
