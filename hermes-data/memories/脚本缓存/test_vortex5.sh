#!/bin/bash
# Test ollama API through Vortex DIRECT
export HTTP_PROXY=http://127.0.0.1:7897
export HTTPS_PROXY=http://127.0.0.1:7897

echo "=== GET /v1/models ==="
curl -s --connect-timeout 10 --max-time 15 \
  "https://ollama.com/v1/models" \
  -w "\nHTTP:%{http_code}"

echo ""
echo "=== POST /v1/chat/completions (no auth) ==="
curl -s --connect-timeout 10 --max-time 20 \
  "https://ollama.com/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{"model":"deepseek-v4-flash","messages":[{"role":"user","content":"hi"}],"max_tokens":5}' \
  -w "\nHTTP:%{http_code}"
