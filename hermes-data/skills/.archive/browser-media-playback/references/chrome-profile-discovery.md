# Chrome Profile Discovery on Windows

## Finding the user's Chrome profile

When interacting with Chrome on the user's Windows machine, the browser may be running under a non-default profile (e.g., `--profile-directory="Profile 1"` instead of `--profile-directory="Default"`).

### Commands to check

```bash
# List Chrome processes with their command lines (WMI)
wmic process where "name='chrome.exe'" get processid,commandline

# Or via tasklist + wmic (slower but works in MSYS)
powershell -Command "Get-CimInstance Win32_Process -Filter \"name='chrome.exe'\" | Select-Object ProcessId,CommandLine"
```

### Typical profile locations

- Default profile: `C:\Users\<USER>\AppData\Local\Google\Chrome\User Data\Default`
- Profile 1: `C:\Users\<USER>\AppData\Local\Google\Chrome\User Data\Profile 1`
- Profile 2, 3, etc.: Same base path with numbered profile directories

### When launching Chrome with a specific profile

```bash
# Must use full path for non-default profiles
"/c/Program Files/Google/Chrome/Application/chrome.exe" \
  --profile-directory="Profile 1" \
  "https://example.com"
```

### ⚠️ Important caveats

- **Killing Chrome destroys the session** — `taskkill /F /IM chrome.exe` kills ALL Chrome windows, including the user's other tabs. Avoid unless absolutely necessary.
- **Cannot restart Chrome with `--remote-debugging-port`** if Chrome is already running — the new flags are ignored. You'd need to kill all instances first, which drops the user's session.
- **`start chrome "URL"` uses the already-running instance** — it opens a new tab/window in whatever Chrome profile is already active. This is the safest approach.
- **Chrome window titles with CJK characters** may appear garbled in PowerShell output (`Misty - Ella Fitzgerald - ���� - ����������`) but `*Misty*` pattern matching still works.
- **Chrome can open MINIMIZED** — when started programmatically via `start chrome` or `terminal(background=true)`, the window may appear at offset (-32000, -32000). **⚠️ Do NOT restore or maximize the window** if the user has explicitly told you not to bring windows to foreground. SendKeys to a minimized window goes nowhere — that's fine, use the `orpheus://` protocol instead (see `netease-orpheus-protocol.md`).
- **Mouse-click simulation is UNRELIABLE and DISRUPTIVE** — do NOT use mouse_event or SendKeys to try to click the 网易云 play button. This approach was tried in production and the user confirmed "没有播放", "还是没有操作对", and "你连播放都不行". The mouse jumps across the screen, windows pop up, and the user finds this extremely disruptive. Use `orpheus://` protocol or ask the user to click play once.
