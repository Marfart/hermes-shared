import sys, json, urllib.request

url = "https://openrouter.ai/api/v1/models"
req = urllib.request.Request(url)
with urllib.request.urlopen(req, timeout=15) as resp:
    data = json.load(resp)

found = []
for m in data['data']:
    mid = m['id'].lower()
    if 'owl' in mid or 'alpha' in mid or 'deepseek' in mid or 'claude' in mid or 'gpt' in mid:
        p = m.get('pricing', {})
        pp = p.get('prompt', '?')
        cp = p.get('completion', '?')
        found.append(f"  {m['id']} - ${pp}/${cp}")

print(f"Total models on OpenRouter: {len(data['data'])}")
print(f"\nRelevant models (owl/alpha/deepseek/claude/gpt):")
for f in found:
    print(f)
