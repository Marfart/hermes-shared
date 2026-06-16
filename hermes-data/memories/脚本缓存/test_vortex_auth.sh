#!/bin/bash
# Test with API key through Vortex DIRECT
export HTTP_PROXY=http://127.0.0.1:7897
export HTTPS_PROXY=http://127.0.0.1:7897

# Read key
KEY=***
KEY=$(grep "^OLLAMA_API_KEY=*** ~/AppData/Local/hermes/.env | tail -1 | cut -d= -f2-)

echo "=== POST with auth through Vortex DIRECT ==="
curl -s --connect-timeout 10 --max-time 30 \
  "https://ollama.com/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer *** \
  -d '{"model":"deepseek-v4-flash","messages":[{"role":"user","content":"say hello"}],"max_tokens":5}' \
  -w "\nHTTP:%{http_code}"
