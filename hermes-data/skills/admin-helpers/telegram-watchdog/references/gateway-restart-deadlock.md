# Gateway Restart Deadlock (2026-06-15)

## The Bug

Watchdog v8 used `subprocess.Popen([hermes, "gateway", "run"])` to restart the Gateway. This does NOT kill the old process first. If the old process is stuck/zombied, its lock file and PID file remain on disk. The new process sees "Another gateway instance is already running (PID XXXX)" and immediately exits with `exit_nonzero`.

Result: **2 days of complete disconnection** (2026-06-13 23:50 to 2026-06-15 00:36).

## The Fix

Changed `restart_gateway_if_needed()` in `smart_watchdog_v8.py`:

```python
# ❌ OLD: Popen doesn't kill the old process → deadlock
subprocess.Popen([hermes_path, "gateway", "run"], ...)

# ✅ NEW: hermes gateway restart kills old + starts new
result = subprocess.run([hermes_path, "gateway", "restart"], 
                       capture_output=True, text=True, timeout=30,
                       creationflags=subprocess.CREATE_NO_WINDOW)
if result.returncode != 0:
    # Fallback: stop first, then run
    subprocess.run([hermes_path, "gateway", "stop"], 
                   capture_output=True, timeout=15,
                   creationflags=subprocess.CREATE_NO_WINDOW)
    time.sleep(3)
    subprocess.Popen([hermes_path, "gateway", "run"], ...)
```

## Diagnosis Trail

1. User reported "Telegram断了" (Telegram disconnected)
2. `gateway_state.json` showed: `gateway_state: "stopped"`, `restart_requested: true`, but `updated_at: 2026-06-13T15:50` — 2 days stale
3. `gateway.log` last entry: `Gateway stopped (total teardown 5.55s)` at 2026-06-13 23:50
4. `errors.log` showed: `Another gateway instance is already running (PID 2788)` — confirming the deadlock
5. Manual `hermes gateway restart` → `✓ Killed 1 gateway process(es)` → Telegram connected in 10 seconds

## Root Cause Chain

Discord proxy timeout → watchdog triggered restart → `Popen gateway run` → old process lock not released → new process exits immediately → no gateway running → 2 days offline

## The Other Issue Found Same Day

Discord was still trying to connect despite `discord: 'null'` in config.yaml. The real token source was `.env` (`DISCORD_BOT_TOKEN=f016e5...38c1`). As long as the .env token exists, Gateway loads Discord and retries every 60-300s, wasting ~13.5 min/day and potentially exhausting httpx connection pools.

Fix: Remove `DISCORD_BOT_TOKEN` and `DISCORD_ALLOWED_USERS` from `.env`, then `hermes gateway restart`.