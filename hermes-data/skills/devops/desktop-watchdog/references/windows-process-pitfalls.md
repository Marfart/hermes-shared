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

## 2. `tasklist` output crashes on Chinese locale

On Chinese Windows, `tasklist` outputs CJK characters. Python's `_readerthread` uses UTF-8 decoder and crashes:

```
UnicodeDecodeError: 'utf-8' codec can't decode byte 0xb4 in position 0: invalid start byte
```

**Fix:** Use `subprocess.run(capture_output=True, text=True)` — the error only manifests in `Popen` background threads, not `run()` (which controls the pipe lifecycle cleanly). If you must use `Popen`, add `encoding='utf-8', errors='replace'` to the constructor.

## 3. Process kill: `taskkill /f` not `os.kill`

`os.kill(pid, signal.SIGTERM)` on Windows maps to `TerminateProcess` — same as `taskkill /f`. But `os.kill` can leave zombie processes. Use `taskkill` directly:

```python
subprocess.run(["taskkill", "/f", "/pid", str(pid)],
               capture_output=True, timeout=5)
```

## 4. Gateway process naming in tasklist

The gateway appears as `pythonw.exe` or `python.exe` — NOT as "gateway" or "hermes". Searching `tasklist` CSV output for "gateway" only works if the argument string is in the output (which `tasklist` doesn't include — use `wmic process` or `Get-Process` for that). Prefer PID from `gateway_state.json` as source of truth.

## 5. `subprocess.CREATE_NO_WINDOW` for background daemons

When spawning a background gateway or service process, pass `creationflags` to suppress the console flash:

```python
subprocess.Popen(
    [...],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    creationflags=subprocess.CREATE_NO_WINDOW
)
```

Only works with `Popen`, not `subprocess.run()`.