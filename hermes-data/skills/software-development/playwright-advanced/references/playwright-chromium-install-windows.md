# Playwright Chromium Install on Windows (Vortex Proxy Workaround)

## The problem
Playwright 1.59 ships expecting `chromium_headless_shell-1217`, but its CDN
(`cdn.playwright.dev`) downloads at <30 KB/s through the Vortex HTTPS proxy.
The download fails predictably after 5+ minutes of timeout.

## The workaround
Use the **existing** chromium-1223 that a prior Playwright version already
downloaded. Pass it via `executable_path`:

```python
browser = await p.chromium.launch(
    headless=True,
    executable_path=(
        r"C:\Users\Admin\AppData\Local\ms-playwright\chromium-1223"
        r"\chrome-win64\chrome.exe"
    ),
    args=["--disable-blink-features=AutomationControlled"],
)
```

This path works because the Playwright driver protocol is backward-compatible
across minor revisions — chromium-1223 handles all commands that 1217 would.

## Checking what's installed
```bash
python -c "import os; d=r'C:\Users\Admin\AppData\Local\ms-playwright'; print([n for n in os.listdir(d) if 'chromium' in n])"
```

## Known installed versions on this machine
| Revision | Path | Status |
|----------|------|--------|
| chromium-1223 | `...\ms-playwright\chromium-1223\chrome-win64\chrome.exe` | ✅ Works |
| chromium_headless_shell-1223 | `...\ms-playwright\chromium_headless_shell-1223\` | ✅ Exists (not needed) |
| chromium_headless_shell-1217 | (expected by 1.59, never downloaded) | ❌ CDN too slow |