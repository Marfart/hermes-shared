# Cron Silent Failure Debugging

## The Two Failure Modes

### Mode 1: Agent-mode cron times out (no_agent=False, old theory)

The old skill (v3.0.0) claimed agent-mode cron *always* outputs 0 bytes. **This is wrong.** The real lesson is that agent-mode cron works fine as long as:
- `enabled_toolsets` is properly set (web, terminal, file, vision, search, github)
- The prompt is self-contained and doesn't rely on conversation context
- The agent can finish within a reasonable number of tool calls (~10-20)

**Verified working:** The autonomous-learning cron (job_id=29b2b9b1d7a0) runs agent-mode every 15 minutes with full tool access, reading GitHub, writing files, and delivering reports. Zero failures.

### Mode 2: Cron environment clears sys.path (no_agent=True Python scripts only)

**Symptom:** Script output shows `Status: silent (empty output)`. Running the same script manually from terminal works fine.

**Root cause:** Hermes cron scheduler clears `sys.path` before launching the script. Python can't find standard library modules (`logging`, `os`, etc.) or third-party packages. The script crashes silently at the first import.

**Fix:** At the very top of the script (before any imports), restore the standard library path:

```python
import sys as _sys
import os as _os
# cron环境可能清空sys.path，补回标准库路径
_stdlib = _os.path.join(_os.path.dirname(_os.__file__), "..", "Lib")
_stdlib = _os.path.normpath(_os.path.abspath(_stdlib))
if _stdlib not in _sys.path:
    _sys.path.insert(0, _stdlib)
# 再补venv的site-packages
_hermes_venv = _os.path.expanduser("~/AppData/Local/hermes/hermes-agent/venv/Lib/site-packages")
if _hermes_venv not in _sys.path:
    _sys.path.insert(0, _hermes_venv)
# 现在可以安全import了
import logging
from ddgs import DDGS
```

**Verification:**
```python
# Simulate cron environment
import sys
sys.path.clear()
# then run the fix code above, then imports
```

## Detection Pattern

When a cron shows `last_status: ok` but no output reaches the user:

1. **Agent mode (no_agent=False):** Check cron output file. If it has Prompt + Response with content, the task executed correctly but delivery didn't work (see `references/windows-cron-delivery-issues.md`). If it's silent, likely `enabled_toolsets` missing.
2. **Script mode (no_agent=True):** Check output file for `Status: silent (empty output)`. If yes, script crashed at import (sys.path issue). Run manually to confirm.
3. **Both modes on Windows:** Even with sys.path fixed, no_agent=True scripts may still output silent due to a separate stdout-capture bug in the Windows scheduler. This is NOT the sys.path issue — it happens even when all imports work. Use agent-mode cron instead.

## Prevention

- **Agent-mode cron:** Always set `enabled_toolsets` to the minimum needed. Don't leave it unset.
- **Script-mode cron:** Every script using third-party packages or stdlib modules beyond `sys`/`os` needs the sys.path fix.
- Test cron scripts by clearing `sys.path` before running.