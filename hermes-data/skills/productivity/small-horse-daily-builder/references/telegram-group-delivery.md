# Telegram Group Delivery Setup

## Problem
Hermes bot (`@Lurallpo_bot`) can't see group messages by default because `can_read_all_group_messages=false`.

## Fix Steps
1. **BotFather**: Go to @BotFather → `/mybots` → Select bot → Bot Settings → Group Privacy → **Turn OFF**
2. **Re-add bot**: Remove bot from group, then re-add it. Privacy setting changes do NOT take effect for existing memberships — must re-add.
3. **Verify**: Check `can_read_all_group_messages: true` via API
   ```bash
   TOKEN=*** TELEGRAM_BOT_TOKEN ~/.hermes/.env | head -1 | cut -d= -f2)
   curl -s -x "http://127.0.0.1:7897" "https://api.telegram.org/bot${TOKEN}/getMe" | python -m json.tool
   # Look for "can_read_all_group_messages": true
   ```
4. **Get chat_id**: Check Hermes gateway logs (more reliable than getUpdates, which Hermes long-polling consumes)
   ```bash
   grep "group:" ~/.hermes/logs/gateway.log | tail -5
   # Look for: telegram:group:-5381168616:8314311281
   ```
5. **Optionally add to config**: `hermes config set telegram.allowed_chats '-5381168616'` (Hermes auto-detects groups even without this)

## Key Facts (verified 2026-06-13)

- **Group**: "Kali & Kali, 小马" (chat_id: **-5381168616**)
- **Student bot**: @KaliMarfar_bot
- **Hermes session key**: `telegram:group:-5381168616:8314311281`
- **Group Privacy**: OFF (verified `can_read_all_group_messages: true`)
- **Proxy required** from China: `curl -x http://127.0.0.1:7897` for all Telegram API calls
- **Group messages route to separate sessions** — NOT visible in DM conversations
- **`group_sessions_per_user: true`** — each user gets their own agent session within the group context
- **`getUpdates` often returns empty** — Hermes long-polling consumes updates before API calls can see them. Check gateway.log instead.

## Send to Group

```python
# Via Hermes send_message tool
send_message(target="telegram:-5381168616", message="Hello from 小马!")
```