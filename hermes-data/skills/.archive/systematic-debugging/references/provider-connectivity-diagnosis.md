# Provider Connectivity Diagnosis

A systematic workflow for determining why an LLM API provider isn't responding — and whether the fault is the provider, the proxy, or the API key.

## The Three-Axis Diagnosis

Every provider failure falls into one (or more) of these categories:

| Axis | Symptom | Common Causes |
|------|---------|---------------|
| **Auth** | `401 Unauthorized` | Expired key, rotated key, wrong key in .env |
| **Network/Proxy** | Timeout, connection refused, 401 through proxy but OK direct | Proxy mangling HTTPS headers, proxy node dead |
| **Provider limits** | Timeout on large requests, 429 rate limit, 503 overload | Free tier caps, context-length limits, quota exhaustion |

## Step 1 — Read the Error from Logs

Always check gateway and conversation logs first — they contain the provider name, model, and exact error type:

```bash
grep -i "ollama\|429\|timeout\|401\|rate.limit\|provider=" ~/AppData/Local/hermes/logs/gateway-stdio.log | tail -30
```

Key fields to extract:
- `provider=...` — which provider was selected
- `model=...` — which model
- `error_type=...` — APITimeoutError, RateLimitError, UnauthorizedError
- `summary=...` — human-readable description
- `tokens=~...` — token count (large = provider limit issue)

## Step 2 — Test Direct (Bypass Proxy)

```bash
KEY="$(grep "^PROVIDER_API_KEY=" ~/AppData/Local/hermes/.env | cut -d= -f2-)"

# Test model listing endpoint (needs less auth, quick check)
curl -s --connect-timeout 15 --max-time 30 --noproxy "*" \
  "https://provider.com/v1/models" \
  -H "Authorization: Bearer $KEY" \
  -w "\nHTTP:%{http_code} TIME:%{time_total}s"

# Test actual chat completion (the real test)
curl -s --connect-timeout 15 --max-time 30 --noproxy "*" \
  "https://provider.com/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $KEY" \
  -d '{"model":"model-name","messages":[{"role":"user","content":"hi"}],"max_tokens":10}' \
  -w "\nHTTP:%{http_code} TIME:%{time_total}s"
```

**If direct works:** the issue is the proxy. Go to Step 3.
**If direct 401s:** the key is wrong or expired. Go to Step 4.
**If direct times out:** the provider's API is slow/capped. Go to Step 5.

## Step 3 — Test Through the Proxy

Your system proxy is typically at `HTTP_PROXY=http://127.0.0.1:7897` (Vortex/Clash, V2Ray, etc.):

```bash
# Same test but sent through the proxy
curl -s --connect-timeout 15 --max-time 30 \
  -x "http://127.0.0.1:7897" \
  "https://provider.com/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $KEY" \
  -d '{"model":"model-name","messages":[{"role":"user","content":"hi"}],"max_tokens":10}' \
  -w "\nHTTP:%{http_code} TIME:%{time_total}s"
```

Compare direct vs proxy:
- **Direct 200, Proxy 401** → Proxy is mangling the Authorization header (known Clash/Vortex issue with HTTPS MITM)
- **Direct 200, Proxy timeout** → Proxy node is dead/slow
- **Both 200** → Proxy is not the issue, check provider limits instead (Step 5)

### Clash/Vortex Proxy Deep Diagnostics

**Vortex (壁新网络/BiXin)** stores config and logs at:
- Config: `C:\Users\<user>\.config\com.vortex.helper\config.yaml`
- Logs: `C:\Users\<user>\.config\com.vortex.helper\service_YYYYMMDD.out.log`

**Step 1 — Check the actual routing (not just the config mode)**

Even when `mode: direct` is set, traffic can still route through proxy nodes:

```bash
# Check Vortex log for the domain
grep "provider.com" ~/'.config/com.vortex.helper/service_*.out.log' | tail -5
```

Log entries look like:
```
[TCP] curl.exe --> ollama.com:443 match Match using BiXin Network[🇺🇸 [Lv2] 美国 02]
[TCP] python.exe --> api.deepseek.com:443 match GeoIP(CN) using DIRECT
```

Key patterns:
- `match Match using BiXin Network[...]` → caught by catch-all, routed through proxy node
- `match GeoIP(CN) using DIRECT` → Chinese IP, goes direct — correct
- `match DomainSuffix(...) using DIRECT` → matched a specific DIRECT rule
- `using DIRECT` (without `match`) → after config change, shows the effective route
- `dial DIRECT ... error: i/o timeout` → DIRECT connection to a foreign server failed (blocked by GFW)

**Step 2 — Check subscription-level overrides**

```bash
cat ~/'.config/com.vortex.helper/.cloud_cache.*.store.json' | grep -o '"NoDirect":[^,]*'
```

If `"NoDirect":true` is set, the subscription overrides local DIRECT rules — all foreign traffic MUST go through proxy nodes.

**Step 3 — Check the catch-all rule**

In config.yaml, look for the last rule before the MATCH:
```
- GEOIP,CN,DIRECT
- MATCH,BiXin Network         # <-- catch-all: non-Chinese traffic goes through proxy
```

If your provider's domain isn't in the DOMAIN-SUFFIX lists and isn't a Chinese site, it hits this catch-all.

**Step 4 — Add a DIRECT rule for the provider**

Add before the `MATCH` line:
```
- DOMAIN-SUFFIX,ollama.com,DIRECT
- DOMAIN-SUFFIX,openrouter.ai,DIRECT
- MATCH,BiXin Network
```

**Step 5 — Restart the Vortex service**

The Windows service (com.vortex.helper) is protected by SCM recovery — `taskkill /F` and `net stop` fail without elevation:
```bash
# MUST use elevated PowerShell
powershell.exe -Command "Start-Process powershell -Verb RunAs -ArgumentList '-Command \"Restart-Service com.vortex.helper; Write-Host Done\"'"
```

Verify PID changed and service is back:
```bash
tasklist | grep vortex
netstat -ano | grep ":7897"
```

**Step 6 — Caveat: fake-ip DNS interference**

Even with a DIRECT rule, Vortex's `fake-ip` DNS mode can cause issues. It intercepts DNS and returns fake IPs (198.18.x.x range). When the DIRECT rule tries to connect to the real server, the fake-ip resolution may cause it to connect through the wrong path.

**Test connectivity after rule applied:**
```bash
curl -s --connect-timeout 15 --max-time 30 \
  -x "http://127.0.0.1:7897" \
  "https://ollama.com/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{"model":"deepseek-v4-flash","messages":[{"role":"user","content":"hi"}],"max_tokens":5}' \
  -w "\nHTTP:%{http_code}"
```

**Known limitation:** ollama.com API through Vortex may still timeout on very large conversations (>100K tokens) even when working correctly. This is an ollama.com server-side timeout issue, not proxy-related.

### Common Proxy Issues

**Clash/Vortex (壁新网络/BiXin):**
- Even in `mode: direct`, the `fake-ip` DNS mode plus `MATCH,BiXin Network` catch-all rule can route traffic through dead proxy nodes
- The proxy's HTTPS interception can corrupt Authorization headers on API calls to external providers
- Subscription-level `NoDirect:true` overrides local DIRECT rules
- Fix: add a `DOMAIN-SUFFIX,provider.com,DIRECT` rule before the `MATCH` rule, or switch Hermes provider to one not affected by the proxy

**Proxy nodes dead but proxy port still listening:**
- Common with Clash/Vortex: the process stays up, port 7897 shows LISTENING, but proxy nodes are unreachable
- The symptom is timeouts, not connection refused
- Check Vortex logs for `dial proxy ... error:` or `i/o timeout` on proxy node names

## Step 4 — Verify the API Key

```bash
# Get key length and prefix
KEY="$(grep "^PROVIDER_API_KEY=" ~/AppData/Local/hermes/.env | cut -d= -f2-)"
echo "Key length: ${#KEY}"
echo "Key prefix: ${KEY:0:8}..."

# Ensure the grep doesn't match comment lines (starting with #)
grep "^PROVIDER_API_KEY=" ~/AppData/Local/hermes/.env
```

Common pitfalls:
- `.env` has both a comment AND a real value line — `grep` without `^PROVIDER` prefix picks the comment
- Key was rotated on provider's website but not updated in `.env`
- Key expired (many free-tier keys have 30-90 day expiry)

## Step 5 — Test Provider Limits with Different Context Sizes

Some providers work for tiny requests but time out on large conversations:

```bash
# Small request (test basic connectivity)
curl -s --noproxy "*" ... \
  -d '{"model":"...","messages":[{"role":"user","content":"hi"}],"max_tokens":10}'

# Medium request (test reasonable load)
curl -s --noproxy "*" ... \
  -d '{"model":"...","messages":[{"role":"user","content":"Write 500 words about MQTT protocol"}],"max_tokens":1000}'
```

Known provider limit patterns:
- **ollama.com (ollama-cloud, free tier):** Works for tiny requests but times out on >50K token conversations. The `/v1/models` endpoint works even with a dead key.
- **OpenRouter (free tier):** Rate limits at 20 RPM, 429 after quota
- **Ollama Cloud:** Weekly quota exhaustion returns 429, resets after ~7 days

## Quick Reference: Provider-Specific Diagnosis

| Provider | Models Endpoint | Chat Endpoint | Key in .env | Known Issues |
|----------|----------------|---------------|-------------|--------------|
| **ollama-cloud** (ollama.com) | `GET /v1/models` (works even without valid key) | `POST /v1/chat/completions` | `OLLAMA_API_KEY` | Times out on large contexts; Vortex proxy corrupts auth headers |
| OpenRouter | `GET /v1/models` | `POST /v1/chat/completions` | `OPENROUTER_API_KEY` | Free tier 20 RPM, 20K context limit |
| DeepSeek | `GET /v1/models` | `POST /v1/chat/completions` | `DEEPSEEK_API_KEY` | Generally reliable, fewer proxy issues |

## The Fix Decision Tree

```
Is it working direct (--noproxy)?
├── YES: Is it working through the proxy?
│   ├── YES → It's a provider side limit (context timeout, rate limit)
│   └── NO  → It's a proxy issue (add DIRECT rule or switch provider)
└── NO: Is the API key valid?
    ├── YES → Provider outage or account ban
    └── NO  → Update the key in .env
```

## Config Check

Always check what provider Hermes is actually configured to use:

```bash
grep -E "provider:|model:" ~/AppData/Local/hermes/config.yaml | head -5
```

The `model.provider` field controls the main session model. All `auxiliary.*.provider` fields each control a separate subsystem (vision, compression, approval, etc.). A provider failure in gateway/cron may mean the main provider is still configured to one that's timing out.
