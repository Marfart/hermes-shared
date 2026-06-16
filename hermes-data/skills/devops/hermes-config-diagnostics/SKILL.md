---
name: hermes-config-diagnostics
title: Hermes Configuration Diagnostics
description: Diagnose why a Hermes provider isn't connecting — stale model.base_url override, provider mismatch, wrong model name format, or API key env var. Step-by-step triangulation from config to direct curl test to built-in provider defaults.
tags: [hermes, provider, config, debugging, api, connectivity]
triggers:
  - User says "Ollama not working" / "provider cannot connect" / "API error" / "model not found"
  - User expresses frustration about a provider that used to work but now doesn't
  - Any "Model `X` was not found in this provider's model listing" error
  - API returns 401/429/timeout from a previously-working provider
  - User says "Feishu not connecting" / "Lark disconnected" / "飞书连不上" / "platform disconnected"
  - Any messaging platform shows "disconnected" in gateway_state after config was added
---

# Hermes Configuration Diagnostics 🩺

Diagnose why a Hermes provider isn't connecting, returning auth errors, or routing to the wrong endpoint.

## Quick Checks (in order)

### 1. Triangulate the config

```bash
grep -A5 "^model:" ~/AppData/Local/hermes/config.yaml
```

Check these fields:
- **`provider`** — Which provider Hermes thinks it's using (e.g. `ollama-cloud`, `deepseek`, `openrouter`)
- **`base_url`** — ⚠️ **THE MOST COMMON TRAP**. If set, it overrides the built-in provider's default. Should be empty string `''` for built-in providers that have their own base URL.
- **`model`** — The model name string. May need a prefix (e.g. `z-ai/glm-5.1` on OpenRouter vs just `glm-5.1` on ollama-cloud)

### 2. Check the API key in .env

```bash
grep -i "API_KEY" ~/AppData/Local/hermes/.env | grep -v "^#"
```

Verify the right env var is set for your provider (e.g. `OLLAMA_API_KEY` for ollama-cloud, `OPENROUTER_API_KEY` for OpenRouter).

### 3. Test the API directly with curl

```bash
# Get the key
KEY=$(grep "^OLLAMA_API_KEY=*** ~/AppData/Local/hermes/.env | cut -d= -f2-)

# Test with the expected base URL (NOT what's in config — what the provider SHOULD use)
curl -s --max-time 10 https://ollama.com/v1/models -H "Authorization: Bearer *** this succeeds but Hermes can't connect → the config's `base_url` is probably wrong/stale.

### 4. Check built-in provider definition

The authoritative defaults live in `~/.hermes/hermes-agent/hermes_cli/auth.py`:

```bash
grep -B2 -A5 '"ollama-cloud":' ~/AppData/Local/hermes/hermes-agent/hermes_cli/auth.py
```

This shows the built-in provider's:
- `inference_base_url` — URL it should use by default
- `api_key_env_vars` — which env var(s) it reads for the API key
- `base_url_env_var` — optional env var to override the base URL

### 5. Check provider_models_cache

Models available on the provider are cached in `~/AppData/Local/hermes/provider_models_cache.json`:

```bash
python3 -c "import json; d=json.load(open(r'~/AppData/Local/hermes/provider_models_cache.json')); print(json.dumps(d.get('ollama-cloud',{}).get('models',[]), indent=2))"

# Or grep for a specific model
grep "glm-5.1" ~/AppData/Local/hermes/provider_models_cache.json
```

If the model IS in the cache but `hermes model <name>` says "not found", the session might be using a different provider than expected.

## Common Pitfalls

### ⚠️ Stale `model.base_url` (the one that bites most often)

If `model.base_url` is set to `https://openrouter.ai/api/v1` but `model.provider` is `ollama-cloud`, **all ollama-cloud API calls silently route through OpenRouter instead of ollama.com**.

**Fix:** Clear the stale base_url:
```bash
hermes config set model.base_url ""
```

### ⚠️ Provider mismatch

The session's provider (set via `hermes model <name>` or `model.provider` in config) must match where the model actually lives. `glm-5.1` exists on both OpenRouter (as `z-ai/glm-5.1`) and ollama-cloud (as `glm-5.1`) — using the wrong one silently fails with auth/timeout errors.

### ⚠️ OpenRouter prefix vs bare name

OpenRouter uses vendor-prefixed model names (`z-ai/glm-5.1`, `deepseek/deepseek-v4-flash`). ollama-cloud uses bare names (`glm-5.1`, `deepseek-v4-flash`). If you see "Similar models: `z-ai/glm-X`" suggestions in error output, you're likely hitting OpenRouter's model listing, not ollama-cloud's.

### ⚠️ `model.default` stale value

The `default` field in model config may point to a removed/free-tier model. Clear it:
```bash
hermes config set model.default ""
```

## Disabling a Platform (Discord, etc.)

**⚠️ config.yaml alone is NOT enough.** Setting `discord: 'null'` or `discord.disabled: true` in config.yaml does NOT stop the Gateway from loading and connecting to that platform. As long as the platform's credential exists in `.env`, the Gateway will try to connect it, retrying on failure (30s timeout × exponential backoff up to 300s), wasting resources and potentially exhausting httpx connection pools.

**To truly disable a platform:**

1. Remove the credential lines from `.env` (e.g. `DISCORD_BOT_TOKEN=...` and `DISCORD_ALLOWED_USERS=...`)
2. Restart the gateway: `hermes gateway restart`
3. Verify in `gateway.log` that no `Connecting to discord` or `Reconnecting discord` lines appear
4. Verify `hermes config show` shows `Discord: disabled` (not `configured`)

**Symptoms of partial disable (config only, .env still has token):**
- `hermes config show` says `Discord: configured`
- Gateway log shows repeated `discord connect timed out after 30s` every 60-300s
- httpx connection pool may get exhausted if proxy is unstable, cascading to Telegram/WeChat failures
- ~13.5 minutes/day wasted on useless Discord reconnection attempts

## Platform (Messaging) Connection Diagnostics

When a messaging platform (Telegram, WeChat, Discord, Feishu/Lark, etc.) shows `disconnected` in gateway_state, follow this sequence:

### 1. Check config and gateway_state

```bash
# Verify platform config exists
python -c "import yaml; d=yaml.safe_load(open(r'C:\Users\Admin\AppData\Local\hermes\config.yaml')); print(d.get('platforms',{}))"

# Check gateway_state for the platform
python -c "import json; d=json.load(open(r'C:\Users\Admin\AppData\Local\hermes\gateway_state.json')); print(d.get('platforms',{}).get('feishu',{}))"
```

If config exists but gateway_state shows `{}` or `disconnected`, the Gateway may need a restart to pick up new config.

### 2. Restart gateway after config changes

```bash
hermes gateway restart
```

Wait 5 seconds, then re-check gateway_state. If still disconnected, proceed to platform-specific checks.

### 3. Platform-specific requirements

| Platform | Connection Mode | Common Failure Cause |
|----------|----------------|---------------------|
| Telegram | Long-polling (outbound) | Bot token invalid, proxy blocking api.telegram.org |
| WeChat | Long-polling via ilinkai | ilinkai service down, pairing not approved |
| Discord | WebSocket | Bot token invalid, proxy timeout |
| **Feishu/Lark** | **Webhook callback (inbound)** | **Missing callback URL, app not published, permissions not granted** |

### Feishu/Lark-specific checks

Feishu uses a **webhook callback** model (unlike Telegram's long-polling). The Gateway must expose a public URL for Feishu to push events to. Key requirements:

1. **App must be published/enabled** on Feishu Open Platform (open.feishu.cn) — "Draft" status apps cannot receive events
2. **Event subscription URL must be configured** — Feishu needs a public HTTPS endpoint (e.g. via Cloudflare Tunnel) to deliver messages
3. **Permissions must be granted** — especially `im:message:receive` (receive messages) and `im:message:send` (send messages)
4. **Verification token** must match between Feishu Open Platform config and Hermes config

If all 4 are met and gateway still shows disconnected, check:
- Is the callback URL reachable from the internet? (Test with `curl` from outside)
- Does Hermes support Feishu natively or does it need a plugin? Check `hermes tools` output
- Check gateway logs for Feishu-specific error messages

### 4. Gateway log locations (Windows)

Gateway logs may appear in multiple locations. Check in order:
- `$LOCALAPPDATA/hermes/gateway.log` (primary)
- `$LOCALAPPDATA/hermes/gateway-stdio.log` (fallback)
- `$LOCALAPPDATA/hermes/errors.log` (error-specific)

```bash
grep -i "feishu\|lark" "$LOCALAPPDATA/hermes/gateway-stdio.log" | tail -20
grep -i "feishu\|lark" "$LOCALAPPDATA/hermes/errors.log" | tail -20
```

## Repair

After fixing config, start a **new session**. The current session's provider connection is established at load time and won't pick up config changes mid-session.

```bash
hermes config set model.provider <correct-provider>
hermes config set model.model <correct-model-name>
hermes config set model.base_url ""       # clear any stale override
hermes config set model.default ""         # clear stale default
```

## Verification

After config fix + new session, confirm the correct endpoint:
1. Check the session banner — it shows the provider and model name at startup
2. Run a simple query — if API responds normally, the fix worked
3. If still failing, repeat step 3 (direct curl test) to isolate config vs credential issue
