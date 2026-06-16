"""Test ollama API through Vortex proxy with DIRECT rule"""
import subprocess, os, json

# Read key from .env
key = ""
with open(os.path.expanduser("~/AppData/Local/hermes/.env")) as f:
    for line in f:
        line = line.strip()
        if line.startswith("OLLAMA_API_KEY=") and not line.startswith("#"):
            key = line.split("=", 1)[1]
            break

print(f"Key length: {len(key)}")

# Test 1: List models through proxy
print("\n=== GET /v1/models through proxy ===")
r1 = subprocess.run(
    ["curl", "-s", "--connect-timeout", "10", "--max-time", "15",
     "-x", "http://127.0.0.1:7897",
     "https://ollama.com/v1/models",
     "-H", f"Authorization: Bearer {key}"],
    capture_output=True, text=True, timeout=20)
lines = r1.stdout.strip().split("\n")
print(f"Response: {lines[-1][:200]}..." if len(lines[-1]) > 200 else f"Response: {lines[-1]}")

# Test 2: Chat completion through proxy
print("\n=== POST /v1/chat/completions through proxy ===")
payload = json.dumps({
    "model": "deepseek-v4-flash",
    "messages": [{"role": "user", "content": "say hello"}],
    "max_tokens": 5
})
r2 = subprocess.run(
    ["curl", "-s", "--connect-timeout", "10", "--max-time", "30",
     "-x", "http://127.0.0.1:7897",
     "https://ollama.com/v1/chat/completions",
     "-H", "Content-Type: application/json",
     "-H", f"Authorization: Bearer {key}",
     "-d", payload],
    capture_output=True, text=True, timeout=35)
print(f"HTTP exit code: {r2.returncode}")
print(f"Result: {r2.stdout[-300:]}")
if r2.stderr:
    print(f"Stderr: {r2.stderr[:200]}")
