"""Test ollama through Vortex DIRECT rule"""
import subprocess, os

# Read key - try multiple patterns
key = ""
with open(os.path.expanduser("~/AppData/Local/hermes/.env")) as f:
    for line in f:
        line = line.strip()
        if "OLLAMA_API_KEY" in line and "=" in line and not line.startswith("#"):
            parts = line.split("=", 1)
            if len(parts) > 1 and len(parts[1]) > 10:
                key = parts[1]

print("Key len:", len(key))

# Test 1: POST without auth (just connection test)
r1 = subprocess.run([
    "curl", "-s", "--connect-timeout", "10", "--max-time", "20",
    "-x", "http://127.0.0.1:7897",
    "https://ollama.com/v1/chat/completions",
    "-H", "Content-Type: application/json",
    "--data-binary", '{"model":"deepseek-v4-flash","messages":[{"role":"user","content":"hi"}],"max_tokens":5}',
    "-w", "\\nHTTP:%{http_code}"
], capture_output=True, text=True, timeout=25)
print("Test 1 (no auth) exit:", r1.returncode)
if r1.stdout:
    print("Out:", r1.stdout[-200:])
else:
    print("No stdout")
if r1.stderr:
    print("Err:", r1.stderr[:200])

# Test 2: POST with auth
r2 = subprocess.run([
    "curl", "-s", "--connect-timeout", "10", "--max-time", "20",
    "-x", "http://127.0.0.1:7897",
    "https://ollama.com/v1/chat/completions",
    "-H", "Content-Type: application/json",
    "-H", "Authorization: Bearer " + key,
    "--data-binary", '{"model":"deepseek-v4-flash","messages":[{"role":"user","content":"hi"}],"max_tokens":5}',
    "-w", "\\nHTTP:%{http_code}"
], capture_output=True, text=True, timeout=25)
print("\\nTest 2 (with auth) exit:", r2.returncode)
if r2.stdout:
    print("Out:", r2.stdout[-300:])
if r2.stderr:
    print("Err:", r2.stderr[:200])
