---
name: browser-media-playback
title: Play Music / Audio / Video via Browser
description: When a user asks to hear music, audio, or video, open the content on the user's LOCAL machine (not the headless browser). The headless browser is only for searching/finding working links, never for playback the user can't see.
tags: [music, audio, video, playback, browser, youtube, netease, stream]
---

# Local Machine Media Playback

**CRITICAL RULE:** Your headless browser tool plays audio the user CANNOT hear. Never play audio in your headless browser. Always open playback on the user's **local machine** through their native browser.

## ⚠️ ⚠️ ⚠️ GOLDEN RULES ⚠️ ⚠️ ⚠️

### Rule 1: ASK EARLY, FAIL FAST

If your FIRST playback approach fails (Spotify has no devices, `orpheus://` protocol doesn't respond, YouTube link is dead), do NOT silently try 3+ more approaches. The worst outcome is trying 4 approaches, failing at all of them, and getting "你放了一下午都没放出来".

**Ask the user immediately after ONE failure:** "我试了XX方式没成功，你用哪个平台/在哪登录的？要我怎么帮你放？"

### Rule 2: NEVER bring windows to foreground

Some users explicitly demand: "**不要弹出Chrome窗口，不要在后台打开网页，让链接自然跳转到软件，整个过程都不要移到前台**"

This means:
- ❌ NO `start chrome "URL"` — this brings Chrome to the foreground
- ❌ NO `[Win32]::SetForegroundWindow()` — never steal focus
- ❌ NO `[Win32]::ShowWindow(_, 3)` (SW_MAXIMIZE) — never resize/restore user's windows
- ❌ NO `[System.Windows.Forms.Cursor]::Position = ...` — never move the user's mouse
- ❌ NO `mouse_event` — never simulate clicks; the mouse jumps and the user finds it extremely disruptive
- ❌ NO `[System.Windows.Forms.SendKeys]::SendWait(' ')` — Space key rarely reaches the right target
- ❌ NO `taskkill /F /IM chrome.exe` — this destroys the user's browsing session and all their tabs

✅ DO: Use `orpheus://` protocol to send songs directly to the NetEase desktop client
✅ DO: Use PowerShell Start-Process with `-WindowStyle Minimized` or just `Start-Process 'protocol://...'`
✅ DO: Ask the user to click play once if automation fails — "页面已经打开了，就差你点一下播放按钮啦～"

### Rule 3: PowerShell keyboard/mouse simulation almost never works

PowerShell SendKeys + mouse_event to click the 网易云 play button **does not work reliably**. Even though the script reports success, the user confirmed "你没有播放", "还是没有操作对", and "你连播放都不行". The nested iframes and autoplay policies prevent remote keyboard control.

**Don't try this approach at all.** Use `orpheus://` protocol or ask the user to click instead.

## Workflow

### 1. Search for content (use headless browser — user can't see this)

Use browser_navigate to find what the user wants on YouTube:

```python
browser_navigate("https://www.youtube.com/results?search_query=陈奕迅+浮夸")
browser_navigate("https://www.youtube.com/results?search_query=jazz+music+relax")
```

### 2. Find a working video URL

From the search results, identify a video. **CRITICAL: Verify the link is still available** before sending to the user. If the snapshot shows "this video isn't available anymore", pick a different result.

Good signals for reliable links:
- Official artist/channel uploads (look for artist/channel name badges)
- High view counts (millions)
- Official topic/artist audio uploads (e.g., "Eason Chan - Topic")
- Recently uploaded (less likely to be removed)

Prefer: official music videos → topic/artist audio → lyrics videos (歌词版) → live performances from official channels.

### 3. Extract the working URL

After clicking a result, get the URL:

```javascript
window.location.href
```

via `browser_console(expression='window.location.href')`

### 4. Open on the user's local machine

Open the URL in the user's **local browser**:

**Windows (git-bash / MSYS) — preferred:**
```bash
start "" "https://www.youtube.com/watch?v=VIDEO_ID"
```

**Alternative — direct exe launch (background):**
```bash
terminal(background=true, command='"/c/Program Files/Google/Chrome/Application/chrome.exe" "URL" --new-window')
```

Use `start` first — it opens the default browser via Windows shell.

### 5. Confirm to the user

Tell the user what's playing and that it should be open in their browser. They control playback (play/pause/volume/skip) from there.

## Alternative: NetEase Cloud Music (网易云音乐)

Some users explicitly prefer 网易云音乐 over YouTube (e.g. Chinese-speaking users on WeChat). If the user says "用网易云" or "网易云网页版", do NOT use YouTube — prioritize NetEase immediately.

### 🏆 PREFERRED: Direct client launch via `orpheus://` protocol (best approach)

**When the NetEase Cloud Music desktop client is installed** (most common for Chinese users), the best approach is to launch songs directly through the `orpheus://` protocol. See `references/netease-orpheus-protocol.md` for full details. This:
- ✅ Opens the song in the desktop client — no Chrome window needed
- ✅ No autoplay restrictions (client handles playback)
- ✅ No iframe navigation issues
- ✅ Nothing pops up in the user's face
- ✅ No mouse/keyboard simulation needed

**How to use it:**
```bash
# From git-bash/MSYS — use PowerShell or cmd.exe wrapper:
powershell -Command "Start-Process 'orpheus://song?id=SONG_ID'"

# Or via cmd.exe:
cmd.exe /c start orpheus://song?id=SONG_ID
```

**⚠️ IMPORTANT: Never bring windows to the foreground!** The user's ideal flow is: "不要弹出任何窗口，在后台打开，让链接自然跳转到软件，整个过程都不要移到前台". Always use Start-Process without WindowStyle (defaults to hidden), and never call ShowWindow/SetForegroundWindow on any browser or client window.

**Verify the client received the song:**
```bash
tasklist | grep -i cloudmusic
```

If the NetEase client processes are running, the protocol likely worked. But you can't verify playback status — trust the protocol and ask the user if they hear music.

### Search via API (preferred over headless browser)

网易云's web interface uses iframes that the headless browser struggles with. Always use the API for searching:

```bash
curl -s "https://music.163.com/api/search/get?type=1&s=<SEARCH_TERM>&limit=10" \
  -H "User-Agent: Mozilla/5.0"
```

- `type=1` = songs, `type=10` = albums, `type=1000` = playlists
- Response is JSON with `result.songs[]` array. Each song has `id`, `name`, `artists[].name`, `album.name`
- Fee field: `0` = free, `1`/`8` = may need login/subscription

### Fallback: Open song in browser (when orpheus:// protocol fails)

If the `orpheus://` approach doesn't work, open the song via Chrome — but **always minimized/background**:

```bash
# PowerShell — open minimized (no foreground popup):
powershell -Command "
\$psi = New-Object System.Diagnostics.ProcessStartInfo
\$psi.FileName = 'C:\Program Files\Google\Chrome\Application\chrome.exe'
\$psi.Arguments = 'https://music.163.com/#/song?id=SONG_ID'
\$psi.WindowStyle = [System.Diagnostics.ProcessWindowStyle]::Minimized
[System.Diagnostics.Process]::Start(\$psi)
"

# The page should auto-detect the NetEase client and redirect to orpheus://
# If it doesn't, the user may need to click ▶️ once
```

**DO NOT** use `start chrome "URL"` — this brings Chrome to the foreground and steals focus from whatever the user is working on.

### ⚠️ Auto-play limitation

网易云 web player does NOT auto-play songs due to browser autoplay policies. The user will see the song loaded in the player bar but must click ▶️ once.

#### Preferred approach: `orpheus://` protocol (background, no window)

If the NetEase Cloud Music desktop client is installed, try the `orpheus://` protocol to send a song directly to the client:

```bash
# PowerShell method (preferred - no window)
powershell -Command "Start-Process 'orpheus://song?id=SONG_ID'"

# Or via cmd.exe
cmd.exe /c start orpheus://song?id=SONG_ID
```

**CRITICAL RULES:**
- 🚫 Do NOT simulate mouse clicks or keyboard events — this is disruptive and unreliable
- 🚫 Do NOT bring Chrome to foreground, maximize windows, or move the cursor
- 🚫 Do NOT keep trying silently if it fails — ask the user early what service they use
- ✅ If auto-play fails, tell the user the page is open and ask them to click play once
- ✅ Use `Start-Process chrome -ArgumentList 'URL' -WindowStyle Minimized` if browser fallback needed

#### Failed approaches (do not retry):
- `start chrome` with PowerShell SendKeys Space — unreliable, disrupts user's workflow
- Headless Chrome `--headless` — protocol handlers may not trigger
- `cloudmusic_util.exe` — does not accept any useful command-line arguments
- Direct HTTP to port 20017 — not standard HTTP, cannot interact via curl

#### What NOT to do (I learned this the hard way):
- ❌ **Don't try Chrome DevTools Protocol** (`--remote-debugging-port=9222`) — requires killing and restarting Chrome, which destroys the user's session
- ❌ **Don't try browser_click on the headless browser** — the user can't hear audio from there
- ❌ **Don't try 4+ silent approaches** — ask the user after the FIRST failure
- ❌ **Don't send Space key via SendKeys** — it rarely works on 网易云's iframe-based player
- ❌ **Don't maximize/foreground Chrome windows** — the user finds this disruptive
- ❌ **Don't move the mouse cursor** — this is extremely jarring for the user
- ❌ **Don't use `taskkill /F /IM chrome.exe`** — this kills the user's browsing session
- ❌ **Don't keep restarting Chrome** — the user may have important tabs open
- ❌ **Don't use `start chrome "URL"` in git-bash** — it brings the window to foreground. Use PowerShell with WindowStyle=Minimized instead.

### Pitfalls

- ⚠️ **DO NOT play audio in your headless browser.** The user cannot hear it. You'll get "你没有打开网页哦" or similar. Always open on their machine.
- **Verify YouTube links work** before opening. "This video isn't available" = pick a different result. Dead links frustrate the user.
- **Check video duration**: Short durations like "0:39" in the initial snapshot may be an ad, not the video. The real duration appears after playback.
- **No skip/next from my end** — once opened on the user's machine, they control it.
- **No volume control** — user adjusts their speakers.
- **GUI-only music apps cannot be CLI-controlled** — NetEase Cloud Music desktop app, Spotify desktop app have no CLI. Use browser streaming (web version) instead. For 网易云, use the web API to search and open song URLs in the local browser.
- ⚠️ **afplay is macOS-only.** Do NOT suggest `afplay` on Windows — it does not exist. If user explicitly asks for CLI audio on Windows, try:
  1. `start "" "URL"` (opens in browser — preferred, user controls playback)
  2. `ffplay -nodisp -autoexit -volume 40 "URL"` (terminal audio via ffmpeg's player — requires a direct audio stream URL)
  3. Python with `winsound.SND_ASYNC` for local MP3 files
- **yt-dlp may not be installable** in this MSYS/git-bash environment (no pip, venv has no pip). For getting audio stream URLs from YouTube without yt-dlp, try invidio.us instances, or fall back to browser playback.
- **PowerShell is available** via `powershell.exe -Command "..."` from MSYS terminal, but pip/python from it may point to the Hermes venv (which has no pip). Use `Get-Command python*` to find system Python installations.
- **Do NOT try to interact with 网易云's iframe-based UI** via browser_click/browser_type. It loads content in nested iframes that the accessibility tree can't navigate properly. Use the API instead.
- **Search keyword "爵士" returned no results** from the web interface (iframe bug). Always use the API endpoint above for searching.
- **Autoplay does NOT work** — see the ⚠️ section above. If PowerShell fails, just tell the user to click ▶️ once. Do NOT keep trying more approaches.
- **Ask early** — see the GOLDEN RULE at the top. One failed approach → ask the user, don't go silent.

## Examples

| User request | Search query | Strategy |
|---|---|---|
| "来一首爵士乐" | `jazz+music+relax` (YouTube) or `jazz` (NetEase API) | Find long-form mix (1h+), open on local browser. If user said 网易云, use NetEase API instead. |
| "放一首陈奕迅的浮夸" | `陈奕迅+浮夸` | Find official or lyrics video, verify link, open locally |
| "放点轻音乐" | `relaxing+piano+music` | Find long-form mix, open locally |
| "我想听周杰伦" | `周杰伦+音乐` | Find official audio, open locally. If user said 网易云, use API search + song URL. |
| "播放白噪音" | `white+noise+sleep` | Find 8h+ mix, open locally |
| "用网易云放一首爵士" | NetEase API: `curl .../api/search/get?type=1&s=jazz` | Use API to search, pick a song ID, open `music.163.com/#/song?id=X` in Chrome. Note autoplay limitation. |
| "用网易云音乐放周杰伦" | NetEase API: `curl .../api/search/get?type=1&s=%E5%91%A8%E6%9D%B0%E4%BC%A6` | Same approach — API search → song URL. Warn about autoplay. |

## Windows-specific commands

```bash
# Open URL in default browser (preferred for YouTube)
start "" "https://www.youtube.com/watch?v=VIDEO_ID"

# ✅ PREFERRED: Open 网易云 song via orpheus:// protocol (desktop client, no Chrome)
powershell -Command "Start-Process 'orpheus://song?id=SONG_ID'"

# ✅ Open 网易云 song page in MINIMIZED Chrome (auto-redirects to client)
powershell -Command "
\$psi = New-Object System.Diagnostics.ProcessStartInfo
\$psi.FileName = 'C:\Program Files\Google\Chrome\Application\chrome.exe'
\$psi.Arguments = 'https://music.163.com/#/song?id=SONG_ID'
\$psi.WindowStyle = [System.Diagnostics.ProcessWindowStyle]::Minimized
[System.Diagnostics.Process]::Start(\$psi)
"

# ❌ AVOID: `start chrome "URL"` — brings window to foreground
# ❌ AVOID: Any SetForegroundWindow/ShowWindow/ShowWindowAsync calls
# ❌ AVOID: Any SendKeys or mouse_event calls — user finds these disruptive

# Auto-play NetEase song via improved V3 script (orpheus:// first)
powershell -ExecutionPolicy Bypass -File "scripts/netease-auto-play.ps1" -SongId "2538829" -SongTitle "Misty"

# Search 网易云 API for songs
curl -s "https://music.163.com/api/search/get" -d "s=SEARCH_TERM&type=1&limit=10" -H "User-Agent: Mozilla/5.0"

# Verify Chrome launched (minimized)
tasklist | grep chrome
```