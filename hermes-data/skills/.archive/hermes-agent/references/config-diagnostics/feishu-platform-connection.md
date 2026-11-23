# Feishu (Lark) Platform Connection Diagnostics

## Session Context (2026-06-15)

User configured Feishu in config.yaml with `app_id: cli_aaa7c346a6385cba` and `app_secret`, but platform showed `disconnected` after gateway restart.

## Key Finding: Feishu Uses Webhook Callback Model

Unlike Telegram (long-polling, outbound connections from Gateway), Feishu requires the Gateway to **expose a public HTTPS endpoint** that Feishu servers push events to. This is a fundamentally different connection architecture.

## Diagnostic Flow (verified)

1. **Config present?** — `python -c "import yaml; d=yaml.safe_load(open(config_path)); print(d.get('platforms',{}))"` — Confirmed `feishu` key with app_id/app_secret
2. **Gateway state?** — Showed `{"state": "disconnected"}` — Config was there but not connecting
3. **Gateway restart** — `hermes gateway restart` — PID changed, but Feishu stayed disconnected
4. **Gateway logs empty** — `gateway.log` was 0 bytes (Windows path issue), checked `gateway-stdio.log` and `errors.log` — no Feishu entries at all

## Root Cause (likely)

The disconnected state with no error messages suggests the Feishu integration either:
- Doesn't have a callback URL configured (Feishu needs one to deliver events)
- App isn't published/enabled on open.feishu.cn
- Required permissions (`im:message:receive`, `im:message:send`) aren't granted
- Hermes Feishu integration may require a webhook endpoint that isn't auto-configured

## Checklist for Feishu Setup

1. [ ] App created on open.feishu.cn
2. [ ] App published/enabled (not in Draft status)
3. [ ] Event subscription configured with public callback URL
4. [ ] Permissions: `im:message:receive`, `im:message:send` granted
5. [ ] Verification token matches between Feishu and Hermes config
6. [ ] Public callback URL reachable from internet (test with external curl)
7. [ ] Gateway restarted after config changes

## Platform Connection Model Comparison

| Platform | Direction | How Gateway Receives Messages |
|----------|-----------|-------------------------------|
| Telegram | Outbound (Gateway → API) | Long-polling getUpdates |
| WeChat | Outbound (Gateway → ilinkai) | Long-polling via ilinkai relay |
| Discord | Outbound (Gateway → API) | WebSocket connection |
| Feishu | **Inbound (API → Gateway)** | Webhook/event callback POST |

This architectural difference means Feishu requires additional infrastructure (public URL + TLS) that other platforms don't.