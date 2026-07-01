import os, json, urllib.request, urllib.error

# Read the API key
with open(os.path.expanduser('~\\AppData\\Local\\hermes\\.env'), 'r') as f:
    key = None
    for line in f:
        if line.startswith('OPENROUTER_API_KEY='):
            key = line.strip().split('=', 1)[1].strip()
            # Remove quotes if present
            if (key.startswith('"') and key.endswith('"')) or (key.startswith("'") and key.endswith("'")):
                key = key[1:-1]
            break

if not key:
    print("KEY NOT FOUND")
    exit(1)

# Test 1: Check if model appears in model list
print("=== Test 1: Model in list? ===")
req = urllib.request.Request('https://openrouter.ai/api/v1/models')
try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.load(resp)
        owl_models = [m['id'] for m in data['data'] if 'owl' in m['id'].lower()]
        print(f"Owl models found: {owl_models}")
        print(f"Total models: {len(data['data'])}")
except Exception as e:
    print(f"Error: {e}")

# Test 2: Try to call the model
print("\n=== Test 2: Can we call it? ===")
url = 'https://openrouter.ai/api/v1/chat/completions'
payload = json.dumps({
    'model': 'openrouter/owl-alpha',
    'messages': [{'role': 'user', 'content': 'Say just: ping'}],
    'max_tokens': 10
}).encode()

req = urllib.request.Request(url, data=payload, headers={
    'Authorization': f'Bearer {key}',
    'Content-Type': 'application/json'
})
try:
    with urllib.request.urlopen(req, timeout=20) as resp:
        result = json.load(resp)
        print(f"HTTP {resp.status}")
        print(f"Response: {result['choices'][0]['message']['content']}")
except urllib.error.HTTPError as e:
    body = e.read().decode()
    print(f"HTTP {e.code}: {body[:500]}")
except Exception as e:
    print(f"Error: {e}")
