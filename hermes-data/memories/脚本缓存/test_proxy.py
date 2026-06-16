"""Simple test: ollama API through Vortex proxy"""
import urllib.request, json, os

# Read key
key = ""
with open(os.path.expanduser("~/AppData/Local/hermes/.env")) as f:
    for line in f:
        if line.startswith("OLLAMA_API_KEY=*** and "#" not in line:
            key = line.strip().split("=", 1)[1]
            break

print(f"Key: {key[:8]}... (len={len(key)})")

# Test through proxy (Vortex DIRECT rule)
proxy_handler = urllib.request.ProxyHandler({"https": "http://127.0.0.1:7897", "http": "http://127.0.0.1:7897"})
opener = urllib.request.build_opener(proxy_handler)

# Chat completion
data = json.dumps({"model": "deepseek-v4-flash", "messages": [{"role": "user", "content": "hi"}], "max_tokens": 5}).encode()
req = urllib.request.Request("https://ollama.com/v1/chat/completions", data=data)
req.add_header("Content-Type", "application/json")
req.add_header("Authorization", f"Bearer *** 
try:
    resp = opener.open(req, timeout=30)
    print(f"HTTP: {resp.status}")
    print(f"Response: {resp.read().decode()[:200]}")
except Exception as e:
    print(f"ERROR: {e}")
