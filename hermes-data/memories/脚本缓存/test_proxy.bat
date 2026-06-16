@echo off
setlocal
REM Read key from .env
for /f "tokens=1,* delims==" %%a in ('findstr /b "OLLAMA_API_KEY=***" "%APPDATA%\..\Local\hermes\.env"') do set "KEY=%%~b"
echo Key length: %KEY:~0,8%...

curl -s --connect-timeout 10 --max-time 30 -x http://127.0.0.1:7897 https://ollama.com/v1/chat/completions -H "Content-Type: application/json" -H "Authorization: Bearer %KEY%" -d "{\"model\":\"deepseek-v4-flash\",\"messages\":[{\"role\":\"user\",\"content\":\"hi\"}],\"max_tokens\":5}" -w "\nHTTP:%%http_code%%"
