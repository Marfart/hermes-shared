# Discord Heartbeat Stale Trap — Root Cause Analysis

## Symptoms

A `no_agent=True` watchdog script (smart_watchdog_v8.py) running every 2 minutes keeps:

1. Detecting gateway as "frozen" (heartbeat > 300s stale)
2. Restarting the gateway process
3. Sending "restarted gateway" messages to the user every cycle

User reports: "一直在给我发消息 / 咋还是给我发一堆"

## Root Cause

### The Chain of Events

```
Discord platform configured in Hermes
  ↓
Discord connect fails repeatedly ("discord connect timed out after 30s")
  ↓
Discord state becomes "retrying" (never "connected")
  ↓
Gateway's global updated_at stops refreshing
    (gateway only updates the timestamp when ALL platforms' state changes;
     if Discord keeps retrying without resolution, the root timestamp freezes)
  ↓
Watchdog reads gateway_state.json:
    - PID exists ✓
    - But updated_at = 30+ minutes ago
    - HEARTBEAT_TIMEOUT = 300s → triggers "Gateway frozen" alert
  ↓
restart_gateway_if_needed sees gateway_alive=False → restarts gateway
  ↓
Gateway restarts → Discord also reconnects (but fails again) → cycle repeats
```

### Why the User Hates It

- The watchdog is working correctly but **too vocally**
- The underlying issue (Discord retrying) is **not actionable by the user**
- Each restart cycle produces a Telegram message
- At 2-minute intervals, this is a flood

## Fixes Applied (2026-06-09)

### Fix 1: Heartbeat timeout increased
`HEARTBEAT_TIMEOUT = 300` → `1800` (30 minutes)

The 300s (5 min) timeout is too aggressive when the gateway's `updated_at` may freeze due to a single stuck platform. 30 minutes is a reasonable threshold: if the gateway hasn't written anything for 30 minutes, it's almost certainly dead.

### Fix 2: Silent script design
Added the "only report when actually repairing/restarting" pattern:
```python
needs_report = bool(ctx.repair_actions) or ctx.should_restart
```

Routine diag results (SSL fail, DNS fail, proxy down) produce zero output.

### Fix 3: 10-minute cooldown
```python
if now - last_report_time > 600:
    # actually print
```

Even when there IS a repair, don't repeat within 10 minutes.

### Fix 4: deliver=local
Changed from `deliver: telegram` to `deliver: local`. Background monitoring should never bother the user directly.

## Detection Pattern

If you see a watchdog that keeps restarting the gateway:

1. Check `gateway_state.json` — is `updated_at` recent?
2. Check platform states — is any platform stuck on "retrying"?
3. Check Discord specifically — does `error_message` say "discord connect timed out"?
4. If Discord is not used, remove it from `platforms` config (`enabled: false`)
5. The watchdog's heartbeat timeout should be at least 1800s

## Related

- User preference (memory): "User does NOT want Discord platform"
- The Discord retry causes ~13.5 min/day of wasted connection time
