# Windows Process Management Pitfalls (git-bash / MSYS)

Cross-cutting lessons for any watchdog, monitor, or process-manager script running from the Hermes git-bash/MSYS environment.

## 1. `os.kill(pid, 0)` crashes with SystemError

**Problem:** On git-bash Python (`cpython-3.11-windows-x86_64`), calling `os.kill(pid, 0)` to check if a process exists throws:

```
SystemError: <class 'OSError'> returned a result with an exception set
```

This is NOT a `ProcessLookupError` you can catch — it's a Python-level crash in the signal module. The `try/except OSError` pattern doesn't work because the error escapes the exception hierarchy on this platform.

**Fix:** Use `tasklist` to check PID existence:

```python
import subprocess

def is_process_alive(pid):
    if not pid:
        return False
    try:
        r = subprocess.run(
            ["tasklist", "/fi", f"PID eq {pid}", "/nh", "/fo", "csv"],
            capture_output=True, text=True, timeout=5
        )
        return str(pid) in r.stdout
    except:
        return False
```

## 2. `subprocess.Popen` output thread crashes on Chinese locale

**Problem:** On Chinese Windows, `tasklist` outputs CJK characters. Python's `_readerthread` uses UTF-8 decoder and crashes:

```
UnicodeDecodeError: 'utf-8' codec can't decode byte 0xb4 in position 0: invalid start byte
```

**Fix:** Use `capture_output=True, text=True` with explicit errors handling, or pipe through `chcp 65001` first. For `tasklist` specifically, adding `/nh` reduces some noise but the CP437/936 encoding still bleeds through. Best practice: wrap in `subprocess.run()` with `errors='replace'` or (simpler) just don't read stdout when you only need the exit code.

## 3. Windows process kill: `taskkill` not `os.kill`

**Problem:** `os.kill(pid, signal.SIGTERM)` has unreliable behaviour on Windows — it may succeed on the call but leave a zombie. Python 3.11's `os.kill` on Windows maps to `TerminateProcess` (not `GenerateConsoleCtrlEvent`), which is equivalent to `taskkill /f`.

**Fix:** Use `taskkill /f /pid <PID>` for reliable forceful termination:

```python
subprocess.run(["taskkill", "/f", "/pid", str(pid)],
               capture_output=True, timeout=5)
```

## 4. Gateway process naming

The gateway process appears as `pythonw.exe` or `python.exe` in tasklist, NOT as "gateway" or "hermes". Searching for "gateway" in tasklist CSV output only works if the command line argument appears — which `tasklist` doesn't show. Use the PID from `gateway_state.json` as the source of truth.

## 5. `subprocess.CREATE_NO_WINDOW` only applies to Popen

When spawning a background gateway process, pass `creationflags=subprocess.CREATE_NO_WINDOW` to avoid a flashing console window:

```python
subprocess.Popen(
    [hermes_bin, "gateway", "run"],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    creationflags=subprocess.CREATE_NO_WINDOW
)
```

This flag only works with `Popen` — `subprocess.run()` ignores it.