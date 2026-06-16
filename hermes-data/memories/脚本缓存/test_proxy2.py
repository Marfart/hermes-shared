"""Simple test: ollama API through Vortex proxy DIRECT rule"""
import urllib.request, json, os

# Read key from env file at runtime
key = ""
with open(os.path.expanduser("~/AppData/Local/hermes/.env")) as f:
    for line in f:
        line = line.strip()
        if line.startswith("OLLAMA_API_KEY=") and not line.startswith("#OLLAMA"):
            key = line.split("=", 1)[1]
            break

print("Key len: %d" % len(key))

# Test chat completion through Vortex proxy
data = json.dumps({
    "model": "deepseek-v4-flash",
    "messages": [{"role": "user", "content": "hi"}],
    "max_tokens": 5
}).encode()

req = urllib.request.Request("https://ollama.com/v1/chat/completions", data=data)
req.add_header("Content-Type", "application/json")
req.add_header("Authorization", "Bearer " + key)

# Through proxy
proxy = urllib.request.ProxyHandler({
    "https": "http://127.0.0.1:7897",
    "http": "http://127.0.0.1:7897"
})
opener = urllib.request.build_opener(proxy)

try:
    resp = opener.open(req, timeout=30)
    print("HTTP: %d" % resp.status)
    body = resp.read().decode()
    print("Result: " + body[:200])
except Exception as e:
    print("ERROR: " + str(e))
