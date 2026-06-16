# Bot Relay Server — Cross-Network Bot-to-Bot Communication

## Problem
Telegram bots cannot receive messages from other bots (Telegram safety policy). If two Hermes bots need to communicate, they need a relay server.

## Solution
Lightweight HTTP relay server (`bot_relay_server.py`) with Cloudflare Tunnel for cross-network access.

## Architecture
```
Bot A (小马) ←→ Relay Server (8877) ←→ Cloudflare Tunnel ←→ Bot B (学弟)
```

## Server Details
- **Local**: `http://127.0.0.1:8877`
- **Public**: Cloudflare Tunnel URL (changes each restart, get from cf.exe logs)
- **Data store**: `bot_relay_messages.json` (same directory as server script)
- **Script location**: `C:\Users\Admin\Desktop\Working\bot_chat\bot_relay_server.py`

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/send` | Send a message `{from, to, content, topic?}` |
| GET | `/poll/{bot_name}` | Poll messages for a bot (URL-encoded Chinese) |
| DELETE | `/msg/{id}` | Acknowledge + delete a message |
| GET | `/history` | Last 50 messages |
| GET | `/status` | Server status |

## Key Pitfalls
- **URL encoding**: Chinese bot names (学弟/小马) MUST be URL-encoded in poll requests. Use `urllib.parse.quote('学弟')` → `%E5%AD%A6%E5%BC%9F`
- **Content-Type**: POST requests must use `application/json; charset=utf-8` (not just `application/json`)
- **Message persistence**: Messages are NOT auto-deleted. Receiver must call `DELETE /msg/{id}` after reading
- **Poll returns empty for wrong encoding**: If poll returns 0 messages but history shows messages exist, the URL encoding is wrong
- **Cloudflare Tunnel URL changes**: Each restart generates a new URL. Update the relay URL in all client configs

## Telegram Bot Group Chat Setup
- Bot @Lurallpo_bot: Group Privacy must be OFF (set via @BotFather → /mybots → Bot Settings → Group Privacy → Turn OFF)
- After changing privacy mode, bot MUST be removed from group and re-added for change to take effect
- `can_read_all_group_messages: true` confirms privacy is off (check via `getMe` API)
- Even with privacy off, bots CANNOT receive messages from OTHER bots (Telegram limitation)
- Group chat_id for "Kali & Kali, 小马": `-5381168616`
- 学弟 bot: @KaliMarfar_bot

## ⚠️ CRITICAL: no_agent Polling + 本地文件 + 亲自回复（2026-06-13 Kali 最终纠正）

**三次纠正过程：**
1. 第一次：`no_agent=True` + 发TG群通知 → Kali 说"不需要走TG通知啊"
2. 第二次：`agent模式` cron自动回复 → Kali 说"不要用cron啊，你这自动回复怎么行呢，要你自己去回复"
3. 最终方案：`no_agent=True` + 写本地文件 → 小马亲自读文件、思考、curl回复 → Kali 认可

**最终方案 v2（2026-06-13 Kali 最终指示 — 文件变更通知模式）：**

| 模式 | 行为 | 问题 |
|:----:|------|------|
| ❌ `no_agent=True` + 写本地文件（无通知） | 轮询→写`xuedi_messages.txt`→等小马聊天时顺便读 | 小马不主动查就漏消息！Kali原话："如果下次没有及时读到回复，我会来批评你的" |
| ❌ `agent模式` cron自动回复 | 轮询→agent思考→自动回复 | Kali原话："你自动回复怎么行呢，要你自己去回复"；Windows上`last_status: error`不稳定 |
| ❌ `no_agent=True` + TG群通知 | 轮询→发TG群通知→等小马去看 | 多一层转发，Kali说"不需要走TG通知啊" |
| ✅ `no_agent=True` + 写本地文件 + TG DM通知触发小马 | 轮询→写文件+删除已读→发TG DM通知→小马收到通知后亲自读+思考+回复 | 跟Codex协作一模一样的模式，Kali原话："就像之前和codex交流那样" |

**铁律（v2）：**
1. **轮询只做搬运，不自动回复** — cron每2分钟轮询中继，有消息写本地文件+删除已读，不调agent
2. **文件变更必须通知小马** — Kali原话："就像之前和codex交流那样，写个脚本，如果文件改动了就通知你，脚本轮询文件，你得到通知了就去思考然后回复"。通知发到小马的TG DM（不是群聊）
3. **小马亲自回复** — 收到通知后亲自读消息、思考、curl POST回复，不是agent自动回
4. **不绕TG群通知** — 学弟方案更简单：轮询→写文件→通知到DM→亲自处理
5. **双方都必须配轮询** — Kali原话："你还要告诉他，要去轮询"
6. **主动问学弟进展** — 不要等学弟发消息才回复。Kali原话："你们两没聊天吗，你要去问学弟进程啊，学的怎么样"

**Current setup**: Cron job `7c35e3b152bf`, every 2 minutes, no_agent=True, script `poll_xuedi_notify.py`, writes to `%LOCALAPPDATA%/hermes/xuedi_messages.txt`, sends TG DM notification to trigger 小马.

**Deleted**: Old agent-mode cron (auto-replied, Kali rejected), old TG-notification cron (forwarded to group, didn't trigger agent).

## Hermes Cron Integration
- **Active cron**: job_id `7c35e3b152bf`, every 2 minutes, `no_agent=True`
- **Script**: `poll_xuedi_notify.py` — polls relay, writes to `xuedi_messages.txt`, deletes read messages
- **Local file**: `%LOCALAPPDATA%/hermes/xuedi_messages.txt` — 小马 reads this file manually and replies via curl
- **No agent mode, no TG forwarding** — cron only moves data; 小马 reads and replies personally

## 学弟's Setup (Mac)
学弟 runs his own cron polling (every 1 minute) on his Mac:
- Pull: `GET {tunnel_url}/poll/学弟`
- Reply: `POST {tunnel_url}/send {"from":"学弟","to":"小马","content":"..."}`
- Ack: `DELETE {tunnel_url}/msg/{id}`

学弟 confirmed working (2026-06-13): Step 1 ✅ connected to relay, Step 2 ✅ pulled messages, Step 3 ✅ replied.

## Files
- Server script: `C:\Users\Admin\Desktop\Working\bot_chat\bot_relay_server.py`
- Message DB: `C:\Users\Admin\Desktop\Working\bot_chat\bot_relay_messages.json`
- Client guide: `C:\Users\Admin\Desktop\Working\bot_chat\学弟接入指南.md`
- Tunnel: `cf.exe` at `C:\Users\Admin\Desktop\Working\cf.exe`

## ⚠️ CRITICAL: Both Sides Must Poll (2026-06-13 Kali Correction)

User explicitly said: "你还要告诉他，要去轮询" — setting up your own polling is NOT enough. You MUST also teach the other bot to:
1. Create their own poll script (`poll_xiaoma.py` or `.sh`)
2. Configure their own Hermes cron to run it (every 2 min, no_agent=True or agent mode)
3. Test the round-trip: bot A sends → bot B polls → bot B replies → bot A polls

Without both sides polling, messages pile up unprocessed on one end.

## ⚠️ CRITICAL: Model Rule (2026-06-13 Kali Correction, Updated)

**Provider: ollama-cloud. Model: deepseek-v4-flash. NEVER use gemma4:e2b.**

User explicitly corrected THREE times in one session:
1. First attempt: wrote `model.provider deepseek` — WRONG
2. Second attempt: wrote `model.provider ollama` — WRONG (missing hyphen)
3. Final correct answer: **`model.provider ollama-cloud`** (with hyphen!)

Correct commands:
- `hermes config set model.provider ollama-cloud`
- `hermes config set model.name deepseek-v4-flash`
- All 11 auxiliary models: `hermes config set auxiliary.*.provider ollama-cloud`
- gemma4:e2b causes errors, rate limits, and instability — it is banned

**The provider name is `ollama-cloud` (WITH hyphen), NOT `ollama` and NOT `deepseek`.**
This is easy to get wrong — the model name contains "deepseek" but the provider name is "ollama-cloud".

## Training Messages Sent to 学弟 (2026-06-13)
1. 环境侦察 — `uname`/`python3`/`git`/`curl` commands
2. 看门狗系统 — gateway_state.json check + auto-repair + rate-limited notifications
3. 恢复链接+默认模型 — 4 disconnection fix methods + model selection rules
4. 模型配置 — deepseek provider ONLY, 11 auxiliary models all deepseek (**corrected**: was "ollama-cloud", user corrected to "deepseek" + "绝对禁止gemma4:e2b")
5. 轮询通信 — GET /poll/学弟 + DELETE /msg/{id} + POST /send reply, every 30s
6. 环境适配完善 — Mac paths (~/.hermes/), cron轮询系统已配好
7. 模型切换规则强化 — 绝对禁止gemma4:e2b，只能用deepseek-v4-flash
8. 看门狗实战 — gateway_state.json检查 + hermes gateway reconnect
9. 通信规则 + 轮询配置教程 — 有事直接找学长不找Kali + 教学弟配自己的poll cron

## ⚠️ Pitfall: Tunnel URL Staleness After Restart

Cloudflare Tunnel generates a **new random URL every restart**. If 小马 restarts the tunnel (e.g., after a crash or DNS timeout), all bots using the old URL will silently fail — no error, just 0 messages polled.

**Symptom**: 学弟 says "没收到你的消息" but relay `/status` shows messages waiting in queue.

**Root cause**: 学弟's poll script still has the OLD tunnel URL (`nsw-sandra-reliable-either.trycloudflare.com`) while the relay is now at a NEW URL (`introduces-initiative-download-conventional.trycloudflare.com`).

**Fix**: After every tunnel restart, MUST:
1. Send a message via the relay telling 学弟 the new URL
2. Verify 学弟 updates their `poll_xiaoma.py` RELAY variable
3. Wait for 学弟 to confirm the update
4. Test round-trip: send → 学弟 polls → 学弟 replies → 小马 polls

**Prevention**: Consider adding a "relay URL version" endpoint to the server so clients can detect when they're hitting the wrong URL.

## ⚠️ Pitfall: Bot Name Mismatch in `to` Field

The relay server has **no name validation** — it silently accepts any `to` field. If a bot sends `{"from": "学弟", "to": "学长"}` instead of `{"from": "学弟", "to": "小马"}`, the message goes into a phantom inbox `/poll/学长` that nobody reads, while `/poll/小马` stays empty. The sender sees "sent successfully" but the receiver never gets it.

**Symptom**: Bot A sends messages, relay `/status` shows `total_messages: N`, but `/poll/小马` returns 0. The messages are stuck under `/poll/学长` (wrong recipient name).

**Debugging steps**:
1. Check `/history` — look at the `to` field of recent messages
2. Try `/poll/学长` or other name variants — if messages appear there, the sender used the wrong name
3. Tell the sender to use the EXACT bot name: `{"to": "小马"}` not `"学长"`, `"XiaoMa"`, or any other variant

**Prevention**: Document the exact bot names in the onboarding guide. Test round-trip immediately after setup.

## ⚠️ Pitfall: localhost.run SSH Tunnels Are Unreliable

学弟 set up his own relay with `ssh -R 9999:localhost:9999 localhost.run`. This worked briefly but the tunnel died within hours, returning `<h1>no tunnel here :(</h1>`. Unlike Cloudflare Tunnel (which runs as a persistent background process), `localhost.run` SSH tunnels are ephemeral — they die when the SSH connection drops (network hiccup, sleep, etc.) and the URL cannot be reused.

**Lesson**: Always use Cloudflare Tunnel (`cf.exe`) for production bot relay. `localhost.run` is OK for quick testing only. When a tunnel dies, the only symptom is "no tunnel here" on GET — no error from the relay server itself.

## Python Script Writing Pitfall: Quote Nesting
When writing Python scripts via `write_file` or `execute_code`, be careful with strings containing `=` signs inside triple-quoted heredocs or `write_file` content. Use `execute_code` with `open(path, 'w')` and Python string variables instead.