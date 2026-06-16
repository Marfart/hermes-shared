# Telegram Group Chat Setup

## Problem
By default, Telegram bots have `can_read_all_group_messages: false` (Group Privacy mode ON).
This means the bot only receives `/command` messages, `@mention` messages, and replies to its own messages.
It does NOT receive regular group messages.

## Fix Steps

1. **Turn off Group Privacy in BotFather:**
   - @BotFather → /mybots → select bot → Bot Settings → Group Privacy → **Turn OFF**

2. **Remove and re-add the bot to the group:**
   - The privacy setting change does NOT take effect for existing group memberships.
   - Kick the bot from the group, then re-add it.
   - Only after re-adding will the bot start receiving all group messages.

3. **Verify:**
   ```bash
   curl -s -x "http://127.0.0.1:7897" "https://api.telegram.org/bot<TOKEN>/getMe" | python -m json.tool
   # Look for "can_read_all_group_messages": true
   ```

4. **Get group chat ID:**
   ```bash
   # Method 1: getUpdates (may be empty if Hermes long-polling consumed them)
   curl -s -x "http://127.0.0.1:7897" "https://api.telegram.org/bot<TOKEN>/getUpdates?limit=10"
   # Method 2: Check Hermes gateway logs
   grep "group:" ~/.hermes/logs/gateway.log
   ```

## Key Notes

- Hermes routes group messages to separate sessions: `telegram:group:<chat_id>:<user_id>`
- Group sessions are NOT visible in DM conversations and vice versa
- Proxy required for Telegram API from China: `curl -x http://127.0.0.1:7897`
- Hermes auto-detects groups even without `allowed_chats` entries

## Current Setup

- Bot: @Lurallpo_bot (小马)
- Group: "Kali & Kali, 小马" (chat_id: -5381168616)
- Student bot: @KaliMarfar_bot
- Privacy mode: OFF (verified)