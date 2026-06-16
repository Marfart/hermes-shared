"""Quick test: ollama POST through Vortex DIRECT rule"""
import subprocess, os

# Test POST to ollama through Vortex (without auth - just checking connection)
r = subprocess.run([
    "curl", "-s", "--connect-timeout", "10", "--max-time", "20",
    "-x", "http://127.0.0.1:7897",
    "https://ollama.com/v1/chat/completions",
    "-H", "Content-Type: application/json",
    "--data-binary", '{"model":"deepseek-v4-flash","messages":[{"role":"user","content":"hi"}],"max_tokens":5}',
    "-w", "\nHTTP:%{http_code}"
], capture_output=True, text=True, timeout=25)
print("Exit:", r.returncode)
print("Stdout:", r.stdout[-200:])
print("Stderr:", r.stderr[:200])

# Now test with auth  
print("\n--- With auth ---")
key = ""
with open(os.path.expanduser("~/AppData/Local/hermes/.env")) as f:
    for line in f:
        line = line.strip()
        if line.startswith("OLLAMA_API_KEY=*** and not line.startswith("#OLLAMA"):
            key = line.split("=", 1)[1]

r2 = subprocess.run([
    "curl", "-s", "--connect-timeout", "10", "--max-time", "20",
    "-x", "http://127.0.0.1:7897",
    "https://ollama.com/v1/chat/completions",
    "-H", "Content-Type: application/json",
    "-H", "Authorization: Bearer " + key,
    "--data-binary", '{"model":"deepseek-v4-flash","messages":[{"role":"user","content":"hi"}],"max_tokens":5}',
    "-w", "\nHTTP:%{http_code}"
], capture_output=True, text=True, timeout=25)
print("Exit:", r2.returncode)
print("Result:", r2.stdout[-300:])
