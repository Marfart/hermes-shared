# Watchdog V9 Architecture Patterns — Supervisor + AAF + processWatchdog

> Date: 2026-06-15
> Source repos: Supervisor (8.4k⭐), AAF, processWatchdog

## Pattern 1: Supervisor Process State Machine

**Source:** `supervisor/supervisor/process.py` (1021 lines), `supervisor/supervisor/states.py`

7-state lifecycle: STOPPED → STARTING → RUNNING / BACKOFF → STOPPING → EXITED → FATAL

Key design: **startsecs health gate** — a process must survive `startsecs` seconds to transition from STARTING → RUNNING. If it exits before startsecs, it transitions to BACKOFF instead.

```
STOPPED ──spawn()──→ STARTING ──alive>startsecs──→ RUNNING
                         │                           │
                         │ (exits too fast)           │ (unexpected exit)
                         ↓                           ↓
                      BACKOFF ──delay expired──→ STARTING
                         │
                         │ (exceeds startretries)
                         ↓
                       FATAL
```

Autorestart policies: `true` (always), `unexpected` (only on non-zero exit code), `false` (never).

## Pattern 2: AAF Event-Driven Decorator + Error Throttling

**Source:** `AAF/src/layer00_utils/watchdog/watchdog.py`, `watchdog_decorator.py`

- `@watchdog_decorator(module_name="SQL DB")` registers health checks as one-liners
- Success → heartbeat event, Failure → error event (60-second throttle per module)
- `WatchDog` class maintains `system_modules` dict for O(1) status updates
- Error throttle: same module's errors suppressed within 60-second window (prevents Broadcast Storm)

## Pattern 3: processWatchdog Heartbeat + Exponential Backoff

**Source:** `processWatchdog/src/process.c`, `heartbeat.c`, `apps.h`

- **Exponential backoff:** `delay = base_delay * 2^(retry_count - 1)`, capped at 3600s
- **PID reuse detection:** compare `/proc/<pid>/stat` start_time to detect PID recycling
- **Heartbeat grace period:** first heartbeat uses `max(interval, delay)` to allow startup time
- **Circuit breaker:** `max_retries` parameter stops retrying after N failures
- **Config-driven:** each process has independent `start_delay`, `heartbeat_delay`, `heartbeat_interval`, `max_retries`, `base_delay`

## V9 Implementation

All three patterns are implemented in `smart_watchdog_v9.py`:

1. **ProcessState enum** — 7 states (STOPPED, STARTING, RUNNING, BACKOFF, STOPPING, EXITED, FATAL)
2. **CircuitBreaker class** — tracks consecutive failures, opens after `startretries` (default 3)
3. **calculate_backoff()** — `delay = base * 2^(retry-1)`, cap at 3600s
4. **ErrorThrottle class** — 600-second window, same problem reported only once
5. **startsecs health gate** — after `gateway restart`, wait `startsecs` seconds then verify Telegram+WeChat are connected
6. **heartbeat_grace** — 60 seconds after restart, skip health checks (avoid false positives)
7. **restart_gateway_supervisor()** — 3-step: stop → wait → start → verify (solves v8 deadlock)

Verification code: `Desktop/Working/watchdog_patterns/watchdog_patterns_v9.py`