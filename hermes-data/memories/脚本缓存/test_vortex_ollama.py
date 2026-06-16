"""Test ollama.com through Vortex proxy"""
import subprocess, os

# Read key
key = ""
with open(os.path.expanduser("~/AppData/Local/hermes/.env")) as f:
    for line in f:
        line = line.strip()
        if line.startswith("OLLAMA_API_KEY=") and not line.startswith("#"):
            key = line.split("=", 1)[1]
            break

# Test through proxy
r = subprocess.run(
    ["curl", "-s", "--connect-timeout", "15", "--max-time", "30",
     "-x", "http://127.0.0.1:7897",
     "https://ollama.com/v1/chat/completions",
     "-H", "Content-Type: application/json",
     "-H", f"Authorization: Bearer {key}",
     "-d", '{"model":"deepseek-v4-flash","messages":[{"role":"user","content":"hello"}],"max_tokens":5}',
     "-w", "\nHTTP:%{http_code}"],
    capture_output=True, text=True, timeout=35)
print("=== API RESULT ===")
print(r.stdout[-300:])

# Check Vortex log
r2 = subprocess.run(
    ["tail", "-5", os.path.expanduser("~/.config/com.vortex.helper/service_20260611.out.log")],
    capture_output=True, text=True)
print("\n=== VORTEX LOG ===")
print(r2.stdout)
