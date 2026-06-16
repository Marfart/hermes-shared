# Telegram Group Chat Setup

## Problem
By default, Telegram bots have `can_read_all_group_messages: false` (Group Privacy mode ON). This means the bot only receives:
- `/command` messages (slash commands)
- Messages where the bot is `@mentioned`
- Replies to the bot's own messages

It does NOT receive regular group messages.

## Fix Steps

1. **Turn off Group Privacy in BotFather:**
   - Open @BotFather in Telegram
   - `/mybots` → select your bot → Bot Settings → Group Privacy → **Turn OFF**
   - This changes `can_read_all_group_messages` from `false` to `true`

2. **Remove and re-add the bot to the group:**
   - The privacy setting change does NOT take effect for existing group memberships
   - Kick the bot from the group, then re-add it
   - Only after re-adding will the bot start receiving all group messages

3. **Verify the setting took effect:**
   ```bash
   TOKEN=$(grep TELEGRAM_BOT_TOKEN ~/.hermes/.env | head -1 | cut -d= -f2)
   curl -s -x "http://127.0.0.1:7897" "https://api.telegram.org/bot${TOKEN}/getMe" | python -m json.tool
   ```
   Look for `"can_read_all_group_messages": true`

4. **Get the group chat ID:**
   ```bash
   curl -s -x "http://127.0.0.1:7897" "https://api.telegram.org/bot${TOKEN}/getUpdates?limit=10" | python -m json.tool
   ```
   Or check Hermes gateway logs for `group:-XXXXXXXXX` session identifiers.

5. **Optionally add to Hermes config:**
   ```yaml
   telegram:
     allowed_chats: '-XXXXXXXXX'  # Add group chat ID
   ```
   Note: Hermes auto-detects groups even without `allowed_chats` entries.

## Important Notes

- **Hermes routes group messages to a separate session** — `telegram:group:<chat_id>:<user_id>`. This is a different session from the DM `telegram:dm:<user_id>`. Messages received in the group are NOT visible in the DM conversation and vice versa.
- **Group sessions are per-user** — with `group_sessions_per_user: true`, each user who sends a group message gets their own agent session within the group context.
- **Hermes gateway long-polling consumes updates** — `getUpdates` API calls may return empty because Hermes already consumed them. Check `gateway.log` for actual message routing: `grep "group:" ~/.hermes/logs/gateway.log`.
- **Proxy required for Telegram API calls** — from China, `api.telegram.org` is blocked. Use Vortex proxy: `curl -x http://127.0.0.1:7897`.
- **Group Privacy is per-bot, not per-group** — once turned off, it applies to ALL groups the bot is in.

## Current Setup (2026-06-13)

- Bot: @Lurallpo_bot (小马)
- Group: "Kali & Kali, 小马" (chat_id: -5381168616)
- Student bot: @KaliMarfar_bot
- Privacy mode: OFF (verified `can_read_all_group_messages: true`)
- Hermes gateway session: `agent:main:telegram:group:-5381168616:8314311281`