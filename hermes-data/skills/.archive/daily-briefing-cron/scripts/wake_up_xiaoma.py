#!/usr/bin/env python3
"""叫醒小马 — 6:25发🌅, 18:25发🌆 via Telegram Bot API

Deployment: cronjob(action='create', name='🌅 叫醒小马（早6:25/晚18:25）',
                    schedule='25 6,18 * * *', deliver='local',
                    no_agent=True, script='wake_up_xiaoma.py')

Flow: cron runs this script → Bot API sends emoji to Telegram chat
      → user sees it → user replies (1 word/emoji) → agent wakes → does work

CRITICAL: The agent is PASSIVE. Only user messages in the chat wake it.
Bot API messages appear in chat but do NOT trigger the agent session.
The user MUST reply to the emoji for the agent to start work.
"""
import datetime
import os
import sys
import urllib.request
import urllib.parse
import json

# Read Telegram bot credentials from .env
env_path = os.path.expanduser("~/AppData/Local/hermes/.env")
token = None
chat_id = None

with open(env_path, 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if line.startswith('TELEGRAM_BOT_TOKEN=') and '#' not in line:
            token = line.split('=', 1)[1].strip()
        elif line.startswith('TELEGRAM_HOME_CHANNEL=') and '#' not in line:
            chat_id = line.split('=', 1)[1].strip()

now = datetime.datetime.now()
hour = now.hour

if hour == 6:
    text = "🌅"
elif hour == 18:
    text = "🌆"
else:
    sys.exit(0)

if not token or not chat_id:
    print("ERROR: missing TELEGRAM_BOT_TOKEN or TELEGRAM_HOME_CHANNEL")
    sys.exit(1)

# Send via Telegram Bot API
url = f"https://api.telegram.org/bot{token}/sendMessage"
data = urllib.parse.urlencode({
    'chat_id': chat_id,
    'text': text
}).encode()

req = urllib.request.Request(url, data=data, method='POST')
try:
    resp = urllib.request.urlopen(req, timeout=10)
    result = json.loads(resp.read())
    if result.get('ok'):
        sys.exit(0)
    else:
        print(f"API error: {result}")
        sys.exit(1)
except Exception as e:
    print(f"Failed: {e}")
    sys.exit(1)