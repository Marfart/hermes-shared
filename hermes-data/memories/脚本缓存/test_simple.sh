#!/bin/bash
# Simple test through Vortex DIRECT
KEY=$(cat ~/AppData/Local/hermes/.env | grep "OLLAMA_API_KEY=*** | grep -v "^#" | cut -d= -f2-)
echo "Key OK: ${#KEY} chars"

curl -s --connect-timeout 10 --max-time 30 \
  -x "http://127.0.0.1:7897" \
  "https://ollama.com/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer *** \
  -d '{"model":"deepseek-v4-flash","messages":[{"role":"user","content":"hi"}],"max_tokens":5}'
