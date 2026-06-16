# Connection Healing Pattern — Multi-tier Watchdog (v6)

Generic pattern for auto-healing intermittent platform connection failures,
learned from Weixin/iLink/Telegram断联修复. v6 fixed three design flaws
that made v5 invisible to the user.

## Core Design Principles (v6)

```
[x] Problems MUST be reported (don't heal silently)
[x] Recovery MUST be reported (user needs to know it's back)
[x] Multi-channel delivery (what if the broken channel IS the delivery target?)
[x] Script-level diagnosis (read logs, curl network check — don't just read state file)
[x] Same-problem rate-limiting by minute (don't spam)
[x] Watchdog exceptions MUST also be reported
```

## The Tiered Repair Chain

When a messaging platform (Weixin, Telegram, Discord) disconnects, the watchdog
runs a **tiered repair chain**. Each tier is cheaper/faster than the next. Exit
as soon as a tier succeeds.

```
Tier 1: Flush DNS (ipconfig /flushdns)     ← 0.1s, no restart needed
Tier 2: Update SSL cert bundle (certifi)   ← 3s, no restart needed
Tier 3: Restart gateway                    ← 10s, disrupts all platforms
```

## Tier Details

### Tier 1 — DNS Refresh
```bash
ipconfig /flushdns
```
Fixes: transient network issues where DNS resolution goes stale. Common on
Windows with unstable VPN/proxy connections. The fastest fix and completely
safe — always try this first.

**Detection signal:** Multiple platforms disconnect simultaneously
(Telegram + Weixin + Discord all go down at the same timestamp).

### Tier 2 — SSL Cert Update
```python
pip install --upgrade certifi
```
Fixes: `SSL: CERTIFICATE_VERIFY_FAILED` errors where the server's cert chain
references a root CA that the system bundle doesn't trust. This happens when:
- Tencent iLink uses a self-signed intermediate that the OS CA store rejects
- certifi bundle is outdated
- Corporate proxy/VPN intercepts SSL with a local CA

**Detection signal:** `SSLCertVerificationError` or `certificate verify failed:
self-signed certificate in certificate chain` in gateway logs.

**IMPORTANT:** Both the system-wide pip AND the Hermes venv pip need upgrading:
```bash
pip install --upgrade certifi                          # system
%LOCALAPPDATA%/hermes/hermes-agent/venv/Scripts/pip install --upgrade certifi  # venv
```

### Tier 3 — Gateway Restart
```bash
hermes gateway run  # via subprocess.Popen
```
Fixes: process-level issues — orphaned connections, stuck poll loops, memory
corruption. Rate-limit restarts via the watchdog state file counter.

**When to skip directly to Tier 3:** Gateway process has exited or gateway_state.json
shows all platforms disconnected. DNS/SSL fixes won't help a dead process.

## Notification Rules (v6 — Always Inform)

| Outcome | Behavior | Example |
|---------|----------|---------|
| Normal (all connected) | Silent | nothing |
| Repaired by Tier 1-2 | **Reported** | `✅ 全部恢复 — Telegram ✓ 微信 ✓ (已自动重启 1 次)` |
| Repaired by Tier 3 | **Reported** | same format |
| Not repaired | **Reported** | `⚠️ 通道断开：telegram(retrying) + 微信(connecting)` |
| Same problem <10min ago | Suppressed (dedup) | same sentinel fingerprint skips second report |

**Implementation:** State file with `incident.json` — tracks `last_sentinel` (minute-based
hash of the problem), `last_broken` timestamps per platform, `total_restarts` counter.
Only prints to stdout when sentinel changes — `no_agent=True` cron only delivers
chatty stdout.

**Delivery target:** Use `deliver=all` so the notification reaches ALL configured
channels (WeChat + Telegram + SMS). If the watchdog only delivers to the broken
channel, the user will never see the alert.

## v5 → v6 Migration: What Changed

| Aspect | v5 (old) | v6 (new) | Why |
|--------|----------|----------|-----|
| Notification on restart | Silent (`T1_SILENT_RESTART`) | Always reports | User needs to know |
| SSL diagnosis | None | Scans log for `sslcert` | Root cause of 90% of WeChat disconnects |
| Network check | Proxy port ping | `curl baidu.com` | Real internet, not just proxy |
| Delivery target | Single WeChat user | `deliver=all` (multi-channel) | Broken platform can't deliver alert |
| Restart escalation | 3 failures → notify | First failure → notify | Don't wait for user to notice |
| Script self-error | Silent (`except: pass`) | Reports "自身异常" | Watchdog failures shouldn't be invisible |

## Three Root Causes of Weixin Disconnections

| Cause | Log Signature | Fix |
|-------|--------------|-----|
| Network blip | `Cannot connect to host ilinkai.weixin.qq.com:443 ssl:default [None]` (also hits Telegram) | Tier 1 (DNS flush) |
| SSL chain issue | `SSLCertVerificationError: self-signed certificate in certificate chain` | Tier 2 (certifi update) — most common |
| iLink rate limit | `ret=-2 errcode=-2 errmsg=rate limited` | Backoff + wait. Never bother user. |

## Diagnostic Flow (in-script, no agent required)

```
gateway_state.json alive?
  ├─ NO → print "⚠️ 状态文件丢失！重启中..." → restart → report
  │
  └─ YES → extract platform states
       ├─ ALL connected → silent (mark recovered if was broken)
       │
       └─ ANY broken → diagnose:
            ├─ curl baidu.com?  ← real internet check
            │   └─ FAIL → "📡 网络不通 — 请检查代理/VPN"
            │       (don't restart — won't help)
            │
            ├─ scan log for "sslcert"?
            │   └─ FOUND → "🔐 SSL 证书问题 — 正在修复..."
            │       → flush DNS + upgrade certifi
            │
            ├─ restart gateway
            ├─ wait 60s for reconnect
            │
            ├─ RECOVERED → "✅ 恢复成功 — TG: connected, 微信: connected"
            └─ FAILED → "⏳ 超时 — TG: retrying, 微信: connecting"
```

## Windows-Specific

- `ipconfig /flushdns` succeeds silently on Windows (no output on success)
- DNS cache on Windows can hold stale entries for the TTL of the record
- PowerShell stdout is gbk-encoded — capture as bytes, then decode
- Chinese text in `tasklist` / `ipconfig` output is gbk-encoded
- SSL certificate store is per-user on Windows — `certifi` upgrade in Hermes venv suffices
- `os.kill(pid, 0)` crashes with `SystemError` on git-bash Python — use `tasklist` instead

## Reference: Canonical Watchdog Script

`%LOCALAPPDATA%/hermes/scripts/smart_watchdog_v6.py` — the v6 implementation
with all principles above baked in. Deployed as `no_agent=True` cron job,
`deliver=all`, every 2 minutes.