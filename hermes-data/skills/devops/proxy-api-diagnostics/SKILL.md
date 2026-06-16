---
name: proxy-api-diagnostics
description: Diagnose and fix API connectivity issues caused by system HTTP proxies (Clash/Vortex/V2Ray etc.). Covers routing inspection, DIRECT rules, fake-ip DNS issues, and Windows service management.
version: 1.0.0
platforms: [windows]
---

# Proxy API Diagnostics

## When to Load This Skill

- Hermes/gateway API calls time out or return unexpected errors
- Small requests work but large ones (100K+ tokens) fail
- User reports "it worked before but now it doesn't" for LLM API access through a proxy
- Proxies like Vortex (壁新网络/BiXin), Clash Meta, V2Ray, or similar system-level proxies are installed

## Diagnostics Workflow

### 1. Check Proxy Routing (Vortex/Clash)

Proxies log where they route each connection. Check:

```bash
# Vortex/Clash service log
tail -20 ~/.config/com.vortex.helper/service_YYYYMMDD.out.log

# Look for the target domain in the log
grep "ollama\|openai\|deepseek\|your-api-domain" ~/.config/com.vortex.helper/service_*.out.log
```

Routing indicators:
- `using DIRECT` — going direct (good for APIs)
- `using BiXin Network[🇺🇸 美国 XX]` — going through a foreign proxy node (can cause timeouts)
- `match Match using` — caught by the catch-all `MATCH` rule

### 2. Compare Through Proxy vs Direct

```bash
# Through proxy (simulates Hermes default behavior)
curl -s --connect-timeout 10 --max-time 15 \
  -x "http://127.0.0.1:7897" \
  "https://api.example.com/v1/models" \
  -w "\nHTTP:%{http_code} TIME:%{time_total}s"

# Bypass proxy entirely
curl -s --connect-timeout 10 --max-time 15 --noproxy "*" \
  "https://api.example.com/v1/models" \
  -w "\nHTTP:%{http_code} TIME:%{time_total}s"

# Through proxy with env vars (alternative method)
HTTPS_PROXY=http://127.0.0.1:7897 HTTP_PROXY=http://127.0.0.1:7897 \
curl -s "https://api.example.com/v1/models" ...
```

### 3. Check Proxy Config Structure

```yaml
# Key sections in Clash/Vortex config.yaml
mode: rule          # rule = apply rules, direct = force all DIRECT
mixed-port: 7897    # proxy listen port
rules:
  - DOMAIN-SUFFIX,some-api.com,DIRECT   # <-- ADD THIS for problem APIs
  - MATCH,BiXin Network                # catch-all for non-Chinese traffic
```

Common config issues:
- **fake-ip DNS** (`enhanced-mode: fake-ip`) — proxy returns fake IPs (198.18.x.x), can interfere with DIRECT connections
- **NoDirect: true** — subscription-level flag forcing all traffic through proxy nodes, overrides local settings
- **MATCH rule** — catches all traffic not matched by earlier rules, typically routes through foreign proxy nodes

### 4. Add DIRECT Rule for an API

Add before the `MATCH` line:

```yaml
  - DOMAIN-SUFFIX,example.com,DIRECT
  # ... other rules ...
  - MATCH,BiXin Network
```

### 5. Restart the Proxy Service (Windows)

Standard `net stop/net start` requires **elevated privileges**:

```bash
# From non-admin shell - use elevated PowerShell
powershell.exe -Command "Start-Process powershell -Verb RunAs -ArgumentList '-Command \"Restart-Service com.vortex.helper; Write-Host Done\"'"

# Verify PID changed (means service actually restarted)
tasklist | grep vortex
```

If the PID doesn't change after restart, the service didn't actually restart — elevation was denied or the command failed silently.

### 6. Verify the Fix

```bash
# Check proxy log for the domain
tail -5 ~/.config/com.vortex.helper/service_*.out.log | grep your-api-domain

# Expected output:
# [TCP] ... --> your-api-domain:443 using DIRECT

# Test through proxy
curl -s --connect-timeout 10 --max-time 15 \
  -x "http://127.0.0.1:7897" \
  "https://your-api-domain/v1/..." \
  -w "\nHTTP:%{http_code}"
```

## Gateway Platform Connectivity (Telegram/Discord/WeChat)

When a Hermes gateway platform shows `state: retrying` with `connect timed out after 30s`, diagnose in this order:

### 1. Check gateway_state.json

```bash
cat ~/AppData/Local/hermes/gateway_state.json | python3 -c "
import sys,json
d=json.load(sys.stdin)
for p,s in d.get('platforms',{}).items():
    print(f\"{p}: {s['state']} — {s.get('error_message','')}\")"
```

### 2. Test Proxy vs Direct to the Platform API

```bash
# Direct (bypass proxy) — will fail if GFW blocks it
curl --noproxy "*" -s -o /dev/null -w "%{http_code} %{time_total}s" --connect-timeout 10 https://api.telegram.org/

# Through proxy — will fail if proxy mode is 'direct' or proxy tunnel is broken
curl -x http://127.0.0.1:7897 -s -o /dev/null -w "%{http_code} %{time_total}s" --connect-timeout 10 https://api.telegram.org/
```

**If both fail** → proxy is in `direct` mode or the proxy tunnel itself is down.

### 3. Check for DNS Pollution (GFW)

GFW poisons DNS for blocked domains. Quick test:

```bash
# Local DNS (may return poisoned result)
nslookup api.telegram.org

# Google DNS (returns real IP)
nslookup api.telegram.org 8.8.8.8
```

If local DNS returns a wrong IP (e.g., `31.13.87.34` = Facebook) but Google DNS returns a different IP (e.g., `74.86.226.234`), that's DNS pollution confirming GFW interference.

### 4. Check Vortex/Clash Proxy Mode (THE MOST COMMON CAUSE)

The `mode` setting at the top of `~/.config/com.vortex.helper/config.yaml` controls ALL routing:

| Mode | Behavior | Telegram/Discord |
|------|----------|-----------------|
| `rule` | Apply DOMAIN-SUFFIX/IP-CIDR rules | Works (rules route to proxy nodes) |
| `global` | ALL traffic through selected proxy node | Works |
| `direct` | ALL traffic goes direct, rules IGNORED | **Broken** — GFW blocks it |

**`mode: direct` is the #1 cause of gateway platform timeouts.** It silently disables all proxy routing — even though `DOMAIN-SUFFIX,telegram.org,BiXin Network` exists in the rules, direct mode overrides everything. Vortex may switch to direct mode after updates, crashes, or manual toggle.

**Detection shortcut:** Both `curl --noproxy "*"` AND `curl -x proxy` failing to the same blocked domain = proxy is in direct mode or proxy tunnel is down.

**Fix:** Change `mode: direct` → `mode: rule` in config.yaml, then restart Vortex. Requires user to manually toggle Vortex UI or edit the config file.

## Common Pitfalls

- **`mode: direct` silently kills all proxy routing** — the most common cause of Telegram/Discord gateway timeouts. Vortex may switch to direct mode after updates or crashes. Always check `mode:` first when gateway platforms are retrying.
- **DNS pollution on blocked domains** — api.telegram.org resolves to Facebook IPs (31.13.87.34) on local DNS but real IPs (74.86.226.234) via Google DNS. This confirms GFW interference, not a config error. Use `nslookup <domain> 8.8.8.8` to verify.
- **Proxy config changes don't auto-reload** — most Clash variants watch config files but not all. Always restart the service after editing config.yaml.
- **`taskkill /F` won't kill a service-protected process** — Windows SCM respawns it immediately. Use `Stop-Service` via elevated PowerShell.
- **fake-ip DNS breaks DIRECT connections** — when DNS returns a fake IP (198.18.x.x), the DIRECT route tries to connect to a non-routable address. This is a known limitation.
- **Double proxy** — `curl -x` + system HTTP_PROXY env var creates two layers of proxying. Use env vars OR `-x`, not both.
- **`***` redaction** — Hermes's secret redaction can break shell commands that contain API keys. Use Python subprocess or write scripts to a file instead of inline shell commands.

## User Preferences (Embedded)

- When user insists on a specific provider/tool, **fix that path** — don't suggest switching to an alternative
- Don't assume account tier (free vs paid) — always investigate the actual root cause instead
- Big requests (100K+ tokens) timing out through a proxy node is a **proxy routing issue**, not a provider issue
