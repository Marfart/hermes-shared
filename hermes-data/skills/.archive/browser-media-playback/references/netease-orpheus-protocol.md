# NetEase Cloud Music `orpheus://` Protocol

## Overview

NetEase Cloud Music (网易云音乐) desktop client registers a custom URL protocol `orpheus://` on Windows. This allows launching songs directly in the desktop client without opening a browser.

## Usage

```powershell
# Launch a song by ID
Start-Process 'orpheus://song?id=SONG_ID'

# From cmd.exe
cmd.exe /c start orpheus://song?id=SONG_ID
```

## Advantages over browser approach

| Aspect | Browser approach | orpheus:// protocol |
|--------|-----------------|-------------------|
| Window focus | Brings Chrome to foreground | No window shown |
| Autoplay | Blocked by browser policy | Plays in client |
| User disruption | Moves mouse, maximizes window | Silent background |
| Reliability | iframe issues, SendKeys fails | Direct client communication |

## Auto-redirect flow

When a user opens `https://music.163.com/#/song?id=X` in Chrome:
1. Page JavaScript detects the NetEase client via protocol handler registration
2. Page redirects to `orpheus://song?id=X`
3. Windows shell routes the protocol to the NetEase client
4. Client picks up the song and plays it

This is the "natural redirect" flow. To trigger it without user disruption:
1. Open Chrome minimized: `$psi.WindowStyle = Minimized`
2. The page loads in background
3. Auto-redirect happens silently
4. Client plays the song

## Registry

The protocol association is stored at:
- `HKCU\Software\Microsoft\Windows\CurrentVersion\ApplicationAssociationToasts\orpheus_orpheus`

This shows the protocol was handled before and the user has acknowledged it.

## Known working song IDs

| ID | Song | Artist | Notes |
|----|------|--------|-------|
| 17888356 | Misty | Ella Fitzgerald | Jazz classic |
| 2538829 | Touch | Endorphin | Trip-hop/chill, fee=0 (free) |
| 22575474 | Teardrop | Massive Attack | Classic trip-hop, fee=1 |

## Notes

- The protocol handler may not be registered if NetEase client was installed per-user vs per-machine
- The `cloudmusic_util.exe` binary in the NetEase install dir accepts no known useful parameters
- When the protocol fails or the client isn't installed, fall back to minimized Chrome
