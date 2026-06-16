# Vortex / Clash Meta Config Reference

## Typical Vortex Config Layout

```yaml
mixed-port: 7897
mode: rule           # or "direct" (mode:direct should force all traffic, but subscriptions may override)
allow-lan: true
log-level: info
external-controller: 127.0.0.1:39797

dns:
  enable: true
  enhanced-mode: fake-ip
  fake-ip-range: 198.18.0.1/16
  # fake-ip causes DIRECT issues: proxy returns 198.18.x.x IPs
  # which are non-routable on the real network

# Subscription data: proxies, proxy-groups, rules are from the provider
enable-process: true   # process-based routing enabled

# Rule ordering matters — first match wins
rules:
  - DOMAIN-SUFFIX,some-chinese-site.com,DIRECT
  # ...
  - GEOIP,CN,DIRECT
  # INSERT CUSTOM DIRECT RULES HERE (e.g. ollama.com)
  - DOMAIN-SUFFIX,ollama.com,DIRECT
  - MATCH,BiXin Network   # catch-all → routes through proxy nodes
```

## Key Proxy-Group Types

```yaml
proxy-groups:
  - name: BiXin Network
    type: select           # user manually picks a node
    proxies:
      - 自动选择            # auto url-test
      - 故障转移            # failover
      - 🇭🇰 [Lv2] 香港 01   # individual nodes
      # ...

  - name: 自动选择
    type: url-test         # automatically picks fastest
    # ...
```

## Log Routing Patterns

| Log Entry | Meaning |
|-----------|---------|
| `using DIRECT` | Traffic goes direct (no proxy) |
| `using BiXin Network[🇺🇸 美国 02]` | Traffic routed through US proxy node |
| `match Match using BiXin Network` | Caught by catch-all MATCH rule |
| `match GeoIP(CN) using DIRECT` | Chinese IP → direct |
| `dial DIRECT ... error: i/o timeout` | Direct connection failed (site blocked from China) |

## Typical Route Flow

1. DNS query → proxy returns fake IP (198.18.x.x)
2. HTTPS request to fake IP → proxy maps back to real domain
3. Rule matching against domain:
   - Chinese domains → DIRECT
   - Non-Chinese domains → MATCH → proxy node
   - Custom DIRECT rules → DIRECT (before MATCH is reached)

## Subscription Cloud Cache

Found at `~/.config/com.vortex.helper/.cloud_cache.*.store.json`

Key fields:
- `NoDirect: true` — subscription forces all traffic through proxy nodes, overriding local mode setting
- `SubFlag: "meta"` — Clash Meta compatible
