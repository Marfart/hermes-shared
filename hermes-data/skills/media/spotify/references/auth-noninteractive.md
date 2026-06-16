# Spotify Auth in Non-Interactive Sessions

When the user asks to set up Spotify but the agent is running in a non-interactive
context (messaging platform like WeChat/Telegram, or the `terminal` tool without `pty=true`),
the `hermes auth spotify` command will fail because it requires stdin input.

## Symptoms

```
Spotify Client ID: Spotify setup cancelled.
```

Exit code 1, immediate failure on the first prompt.

## Workflow: Guided Setup via Browser

Instead of running `hermes auth spotify` blindly, do this:

### Step 1 — Open the Developer Dashboard

Navigate the browser to `https://developer.spotify.com/dashboard` and ask the user
to log in with their Spotify account (the agent cannot know the user's credentials).

### Step 2 — User Creates a Developer App

Guide the user through the "Create app" form in the dashboard:

| Field | Value |
|-------|-------|
| App name | `hermes-agent` (or anything) |
| Description | Anything |
| Redirect URI | **`http://127.0.0.1:43827/spotify/callback`** |
| Which API/SDKs? | (see note below) |

⚠️ The Redirect URI **must** match exactly — it is the local callback server
Hermes starts during `hermes auth spotify`.

**⚠️ Note on API/SDK selection:** The old "Web API" checkbox may not appear in Spotify's Create App form anymore; only Web Playback SDK, Ads API, iOS, and Android checkboxes are shown. **This is not a problem** — Web API is now **enabled by default** for all registered apps. Just fill in the other fields and save.

### Step 3 — User Provides Client ID

After saving the app, the user opens Settings and reads the **Client ID** (and optionally the **Client Secret**). Ask the user to send these to you.

**Note on PKCE flow:** `hermes auth spotify` uses the PKCE (Proof Key for Code Exchange) OAuth flow. Only the **Client ID** is strictly required — the Client Secret is optional. If you set the Client ID in `.env` beforehand, the command skips the interactive prompt entirely.

### Step 4 — Run Auth with Env-Var Configuration (Recommended)

The cleanest approach: set `HERMES_SPOTIFY_CLIENT_ID` in the Hermes `.env` file, then run `hermes auth spotify`. It auto-detects the Client ID and skips the interactive prompt, proceeding directly to the browser OAuth consent page.

```bash
# Add to $HERMES_HOME/.env (check HERMES_HOME path first!)
echo "HERMES_SPOTIFY_CLIENT_ID=<your_client_id>" >> "$HERMES_HOME/.env"

# Then run auth — no interactive prompts needed
hermes auth spotify
```

**Finding the right .env path:** On Unix it's usually `~/.hermes/.env`; on Windows it's `~/AppData/Local/hermes/.env`. Check `echo $HERMES_HOME` if unsure.

**Option A (fallback): PTY mode** — if you can't pre-set the env var, use terminal with pty=true, then submit the Client ID when prompted:

```bash
# Use terminal(pty=true), then:
process(action="submit", data="<client_id>")
```

The Client Secret prompt does NOT appear in PKCE mode — it will proceed directly to the browser after the Client ID is entered.

### Step 5 — Browser OAuth Consent

After entering the credentials, `hermes auth spotify` will open a browser to
`accounts.spotify.com/authorize` for the OAuth consent page. The user needs to
approve the permissions (click "Agree"). Hermes then receives the callback on
`http://127.0.0.1:43827/spotify/callback` and stores the refresh token.

### Step 6 — Verify

```bash
# Check if spotify credentials exist in auth.json
python3 -c "import json; auth=json.load(open('$HERMES_HOME/auth.json')); print('Spotify:', 'present' if 'spotify' in auth.get('providers',{}) else 'missing')"

# Also try:
hermes auth list
```

Note: `hermes auth list` shows only **credential pool** entries (like `DEEPSEEK_API_KEY`). OAuth-based providers like Spotify are stored in `auth.json` under `providers.spotify` and may NOT appear in `hermes auth list` output. Use the Python one-liner above to confirm. If the auth command completed without errors and showed "login successful", the credentials are stored correctly.

Then the user needs to `/reset` or start a new session for the Spotify tools to appear.
