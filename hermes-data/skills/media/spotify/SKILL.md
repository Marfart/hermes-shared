---
name: spotify
description: "Spotify: play, search, queue, manage playlists and devices."
version: 1.1.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
prerequisites:
  tools: [spotify_playback, spotify_devices, spotify_queue, spotify_search, spotify_playlists, spotify_albums, spotify_library]
metadata:
  hermes:
    tags: [spotify, music, playback, playlists, media]
    related_skills: [gif-search]
---

# Spotify

Control the user's Spotify account via the Hermes Spotify toolset (7 tools). Setup guide: https://hermes-agent.nousresearch.com/docs/user-guide/features/spotify

## Setup / Prerequisites

Three steps are required, in order:

### 1. Enable the Spotify plugin
The Spotify plugin is bundled with Hermes but **disabled by default**.
```bash
hermes plugins enable spotify
```

### 2. Enable the Spotify toolset
```bash
hermes tools enable spotify
```

### 3. Authenticate with Spotify
```bash
hermes auth spotify
```
This opens a browser to authorize Hermes to control your Spotify account.

**IMPORTANT: This is an interactive command.** On first run per machine it requires:
- Registering a Spotify Developer App via the browser (create an app with Redirect URI `http://127.0.0.1:43827/spotify/callback`)
- Pasting the **Client ID** into the terminal prompt

The auth uses **PKCE flow** — the **Client Secret is NOT required**, only the Client ID.

**Trick:** If you set `HERMES_SPOTIFY_CLIENT_ID=<your_client_id>` in `.env` (at `$HERMES_HOME/.env`) before running `hermes auth spotify`, the command auto-detects the Client ID and skips the interactive prompt — proceeding directly to the browser OAuth consent page. This is the best approach for non-interactive agent workflows.

**⚠️ Pitfall — Spotify Developer portal has changed its Create App UI.** The old "Web API" checkbox may not appear anymore; only Web Playback SDK, Ads API, iOS, and Android checkboxes are shown. **This is fine** — Web API is now **enabled by default** for all registered apps. Just fill in the app name, description, Redirect URI, and save. Don't let the missing checkbox block the auth flow.

**⚠️ Pitfall — Missing Redirect URI blocks auth silently.** The Redirect URI field in the Spotify app **must** contain exactly `http://127.0.0.1:43827/spotify/callback` (no trailing slash). If it's missing or wrong, `hermes auth spotify` opens the browser OAuth page, the user clicks Agree, but the callback fails silently — the process hangs forever with no error message. **Always verify the Redirect URI is saved in the app Settings before running auth.** If the process already hung, kill it, add the Redirect URI, then retry.

If you run this via the Hermes terminal tool in non-interactive mode (default, no pty) without pre-setting the env var, the command will fail immediately with "Spotify setup cancelled" because it cannot accept stdin input for the Client ID prompt. See `references/auth-noninteractive.md` for how to handle this.

Then start a **new session** (`/reset` in chat, or a fresh `hermes` invocation) — plugin and toolset changes do NOT take effect mid-conversation.

### ⚠️ Diagnostic: tools not showing up?

If `hermes tools list` shows `✓ enabled  spotify  🎵 Spotify` but you still don't see any Spotify tools (`spotify_playback`, `spotify_search`, etc.) in your function list:

1. Check the plugin status first — this is the most common root cause:
   ```bash
   hermes plugins list | grep spotify
   ```
   If it shows `not enabled`, run `hermes plugins enable spotify` first, then `/reset`.

2. Verify the toolset is enabled:
   ```bash
   hermes tools list | grep spotify
   ```

3. Verify OAuth is set up:
   ```bash
   hermes auth list | grep spotify
   ```

The toolset being "enabled" at the tools level does NOT mean the plugin itself is enabled — they are separate settings. Both must be enabled, and both require a `/reset` to take effect.
## When to use this skill

The user says something like "play X", "pause", "skip", "queue up X", "what's playing", "search for X", "add to my X playlist", "make a playlist", "save this to my library", etc.

## The 7 tools

- `spotify_playback` — play, pause, next, previous, seek, set_repeat, set_shuffle, set_volume, get_state, get_currently_playing, recently_played
- `spotify_devices` — list, transfer
- `spotify_queue` — get, add
- `spotify_search` — search the catalog
- `spotify_playlists` — list, get, create, add_items, remove_items, update_details
- `spotify_albums` — get, tracks
- `spotify_library` — list/save/remove with `kind: "tracks"|"albums"`

Playback-mutating actions require Spotify Premium; search/library/playlist ops work on Free.

## Canonical patterns (minimize tool calls)

### "Play <artist/track/album>"
One search, then play by URI. Do NOT loop through search results describing them unless the user asked for options.

```
spotify_search({"query": "miles davis kind of blue", "types": ["album"], "limit": 1})
→ got album URI spotify:album:1weenld61qoidwYuZ1GESA
spotify_playback({"action": "play", "context_uri": "spotify:album:1weenld61qoidwYuZ1GESA"})
```

For "play some <artist>" (no specific song), prefer `types: ["artist"]` and play the artist context URI — Spotify handles smart shuffle. If the user says "the song" or "that track", search `types: ["track"]` and pass `uris: [track_uri]` to play.

### "What's playing?" / "What am I listening to?"
Single call — don't chain get_state after get_currently_playing.

```
spotify_playback({"action": "get_currently_playing"})
```

If it returns 204/empty (`is_playing: false`), tell the user nothing is playing. Don't retry.

### "Pause" / "Skip" / "Volume 50"
Direct action, no preflight inspection needed.

```
spotify_playback({"action": "pause"})
spotify_playback({"action": "next"})
spotify_playback({"action": "set_volume", "volume_percent": 50})
```

### "Add to my <playlist name> playlist"
1. `spotify_playlists list` to find the playlist ID by name
2. Get the track URI (from currently playing, or search)
3. `spotify_playlists add_items` with the playlist_id and URIs

```
spotify_playlists({"action": "list"})
→ found "Late Night Jazz" = 37i9dQZF1DX4wta20PHgwo
spotify_playback({"action": "get_currently_playing"})
→ current track uri = spotify:track:0DiWol3AO6WpXZgp0goxAV
spotify_playlists({"action": "add_items",
                   "playlist_id": "37i9dQZF1DX4wta20PHgwo",
                   "uris": ["spotify:track:0DiWol3AO6WpXZgp0goxAV"]})
```

### "Create a playlist called X and add the last 3 songs I played"
```
spotify_playback({"action": "recently_played", "limit": 3})
spotify_playlists({"action": "create", "name": "Focus 2026"})
→ got playlist_id back in response
spotify_playlists({"action": "add_items", "playlist_id": <id>, "uris": [<3 uris>]})
```

### "Save / unsave / is this saved?"
Use `spotify_library` with the right `kind`.

```
spotify_library({"kind": "tracks", "action": "save", "uris": ["spotify:track:..."]})
spotify_library({"kind": "albums", "action": "list", "limit": 50})
```

### "Transfer playback to my <device>"
```
spotify_devices({"action": "list"})
→ pick the device_id by matching name/type
spotify_devices({"action": "transfer", "device_id": "<id>", "play": true})
```

## Critical failure modes

**"Spotify setup cancelled" on first auth** — the `hermes auth spotify` command is interactive and requires stdin input for the Client ID (PKCE flow — no Client Secret needed). In non-interactive terminal mode (default terminal tool, no pty), it will fail immediately. Use `references/auth-noninteractive.md` for the guided workflow: open the Spotify Developer Dashboard in the browser, ask the user for their Client ID, then complete auth via env-var configuration (set `HERMES_SPOTIFY_CLIENT_ID` in `.env` to auto-detect) or pty mode.

**`403 Forbidden — No active device found`**** on any playback action means Spotify isn't running anywhere. Tell the user: "Open Spotify on your phone/desktop/web player first, start any track for a second, then retry." Don't retry the tool call blindly — it will fail the same way. You can call `spotify_devices list` to confirm; an empty list means no active device.

**`403 Forbidden — Premium required`** means the user is on Free and tried to mutate playback. Don't retry; tell them this action needs Premium. Reads still work (search, playlists, library, get_state).

**`204 No Content` on `get_currently_playing`** is NOT an error — it means nothing is playing. The tool returns `is_playing: false`. Just report that to the user.

**`429 Too Many Requests`** = rate limit. Wait and retry once. If it keeps happening, you're looping — stop.

**`401 Unauthorized` after a retry** — refresh token revoked. Tell the user to run `hermes auth spotify` again.

**`hermes auth spotify` hangs / never completes** — the command opened the OAuth consent page in the browser and the user approved, but the callback server never received the redirect. **Almost always caused by the Redirect URI not being allow-listed in the Spotify Developer App settings.** The user must go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard) → their app → Settings → **Redirect URIs** and add `http://127.0.0.1:43827/spotify/callback`. Kill the hung process (`process kill`) and re-run `hermes auth spotify` after saving. Also check that the Redirect URI in the app matches exactly — trailing slashes, case, and protocol all matter.

**Generic `Spotify rejected the request` error on `spotify_search` (no status code)** — this is NOT normal. The skill says search works on Free tier, so if even search fails with this generic error, the stored OAuth token is likely stale or invalid. Run `hermes auth spotify` to refresh it. After successful re-auth, try `spotify_search` again — if it works, the token was the problem. Also note: `hermes auth list | grep spotify` returning nothing is **not** evidence that Spotify isn't authenticated — OAuth tokens live in `auth.json` under `providers.spotify`, not in the credential pool that `hermes auth list` inspects. Verify with: `grep -c '"spotify"' "$HERMES_HOME/auth.json"`.

## URI and ID formats

Spotify uses three interchangeable ID formats. The tools accept all three and normalize:

- URI: `spotify:track:0DiWol3AO6WpXZgp0goxAV` (preferred)
- URL: `https://open.spotify.com/track/0DiWol3AO6WpXZgp0goxAV`
- Bare ID: `0DiWol3AO6WpXZgp0goxAV`

When in doubt, use full URIs. Search results return URIs in the `uri` field — pass those directly.

Entity types: `track`, `album`, `artist`, `playlist`, `show`, `episode`. Use the right type for the action — `spotify_playback.play` with a `context_uri` expects album/playlist/artist; `uris` expects an array of track URIs.

## What NOT to do

- **Don't call `get_state` before every action.** Spotify accepts play/pause/skip without preflight. Only inspect state when the user asked "what's playing" or you need to reason about device/track.
- **Don't describe search results unless asked.** If the user said "play X", search, grab the top URI, play it. They'll hear it's wrong if it's wrong.
- **Don't retry on `403 Premium required` or `403 No active device`.** Those are permanent until user action.
- **Don't use `spotify_search` to find a playlist by name** — that searches the public Spotify catalog. User playlists come from `spotify_playlists list`.
- **Don't mix `kind: "tracks"` with album URIs** in `spotify_library` (or vice versa). The tool normalizes IDs but the API endpoint differs.
