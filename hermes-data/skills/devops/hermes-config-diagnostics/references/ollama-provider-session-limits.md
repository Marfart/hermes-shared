# Ollama Provider Session Limits

## Rate Limit Types (per ollama.com/pricing)

| Limit Type | Reset Cycle | Affects |
|-----------|-------------|---------|
| Session usage limit | **Every 5 hours** | Per-session token/request count |
| Weekly usage limit | **Every 7 days** | Total weekly usage across all sessions |

## Diagnosing Session Limit Exhaustion

### Check auth.json credential status

The ollama credential pool stores the last error state:

```python
import json
a = json.load(open(r'C:\Users\Admin\AppData\Local\hermes\auth.json'))
cp = a['credential_pool']['ollama-cloud']
for entry in cp:
    print(entry.get('last_status'))
    print(entry.get('last_error_code'))
    print(entry.get('last_error_reason'))
    print(entry.get('last_error_message'))
    print('reset_at:', entry.get('last_error_reset_at'))
```

### Expected values when exhausted:

| Field | Value |
|-------|-------|
| `last_status` | `exhausted` |
| `last_error_code` | `429` |
| `last_error_message` | `you (noobloy) have reached your session usage limit, upgrade for higher limits: https://ollama.com/upgrade or add extra usage: https://ollama.com/settings (ref: ...)` |
| `last_error_reset_at` | `None` (system doesn't set this — rely on 5h cycle) |

### Recovery

1. **Automatic**: Session limits reset every **5 hours** from first request in the session. No manual action needed.
2. **Manual**: Go to https://ollama.com/settings to add extra usage, or https://ollama.com/upgrade to increase plan limits.

### Last error timestamp → next reset estimate

```python
import datetime
ts = entry.get('last_status_at')  # Unix timestamp
last_fail = datetime.datetime.fromtimestamp(ts)
reset_time = last_fail + datetime.timedelta(hours=5)
print(f"Failed at: {last_fail}")
print(f"Estimated reset: {reset_time}")
```

## Usage note

The user (noobloy) is a **paid subscriber**. Session limits exist at all plan tiers — paid ≠ unlimited. The 5-hour reset applies to all plans.
