# Provider/Model Availability Verification

> When a configured model stops responding or the user asks "why is model X gone?", use this methodology to determine availability.

## Three-Pronged Check

### 1. Provider Model Listing API

OpenRouter:
```bash
# Fetch all models, grep for the one you need
curl -s --noproxy "*" "https://openrouter.ai/api/v1/models" | python -c "
import sys, json
data = json.load(sys.stdin)
for m in data['data']:
    if 'keyword' in m['id'].lower():
        print(m['id'])
"
```

### 2. Web Search for Status Changes

Search patterns (try multiple):
- `"model-name" discontinued/retired/removed/sunset`
- `"model-name" openrouter replacement`
- Generic: `openrouter <model> status`

Check official announcements:
- OpenRouter CEO (EMostaque) on X/Twitter
- Provider's blog/changelog
- modelpedia.dev for change history

### 3. Direct API Test

```python
import urllib.request, json
payload = json.dumps({
    'model': 'provider/model-name',
    'messages': [{'role': 'user', 'content': 'ping'}],
    'max_tokens': 5
}).encode()
req = urllib.request.Request(
    'https://openrouter.ai/api/v1/chat/completions',
    data=payload,
    headers={
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json'
    }
)
# Check response - 404/400 suggests retired, 200 suggests live
```

### 4. Fallback/Replacement Identification

If the model is retired:
- Check if the provider has a newer model with a related name (e.g., `fusion` replaced `owl-alpha`)
- Ask the user which model they want to switch to
- Suggest alternatives at similar price/quality tier

## Common Reasons Models Disappear

| Reason | Signal | Action |
|--------|--------|--------|
| Stealth-launch retirement | API 404, web search confirms "retiring" | Switch to successor or alternative |
| Provider removed | API returns nothing, no web presence | Remove from config |
| Renamed | Old name fails, new name works | Update config |
| Temporary outage / rate limit | 429 / 5xx | Wait and retry; check provider status page |

## Example: Owl Alpha Case

- **Model**: `openrouter/owl-alpha`
- **What happened**: OpenRouter's own stealth-launch model (based on Meituan LongCat-2.0-Preview) announced retirement
- **Source**: X post from OpenRouter CEO — "Owl Alpha will be retiring soon. But this isn't an ending — stay tuned!"
- **Replacement candidates**: `openrouter/fusion`, `openrouter/pareto-code`, `openrouter/bodybuilder`
- **Timeline**: Launched Apr 28, 2026 → Top 3 globally → Retired ~late Jun 2026
