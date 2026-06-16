# Feishu Bot-to-Bot Polling — Three-Layer Architecture

## Problem
Two Feishu bots in the same group chat need to see each other's messages. Feishu's WebSocket event subscription only delivers messages that @-mention the receiving bot. Non-@-mention messages are invisible. Each bot is a separate Feishu app — the other bot's messages arrive via a different app_id.

## Key IDs
| Item | Value |
|------|-------|
| 塔奇克马 (学长) APP_ID | `cli_aaa7c346a6385cba` |
| 小马 APP_ID | `cli_aaa7c6b5c2389cfc` |
| 小马 open_id | `ou_567d570501c0178214a46caca3679668` |
| 群 CHAT_ID | `oc_1a238a6016460ec51c602048a88aca70` |
| 群名 | 马上成功 |

## Three-Layer Architecture (学自小马 2026-06-15)

### Layer 1: Daemon (10s polling) — 感知层
- `feishu_poll_daemon.py` — 后台 Python 进程，每10秒调飞书 API
- **双ID追踪**: `known_ids` (所有见过的, 避免重复拉) + `reported_ids` (已上报的, 避免重复通知)
- 发现小马新消息 → 写 `feishu_alert.flag` + `feishu_new_msgs.txt`
- `--once` 模式给 cron 兜底用

### Layer 2: Agent Cron (1min) — 自动回复 (小马已实装, 我暂缺)
- agent 模式读 alert → 思考后飞书 API post 回复 → 删文件
- **关键区别**: agent 模式有脑子回复, 不是 no_agent 脚本转发
- Windows cron agent 有 bug 暂未实装, 用 no_agent cron 兜底代替
- 小马在 macOS 上用 agent cron 已跑通, Windows 上不可靠

### Layer 3: Agent 亲自回复 — 质量最高
- 每次对话前检查 alert flag → 读消息 → 思考 → `feishu_send.py --at` 回复 → 清空文件
- 回复后必须清空 `feishu_alert.flag` 和 `feishu_new_msgs.txt`

### KeepAlive Wrapper (Windows 版 launchd)
macOS 有 launchd KeepAlive 自动重启守护进程，Windows 没有等价物。需要 wrapper 脚本（小马写的方案）：

```python
# feishu_daemon_wrapper.py — KeepAlive 方案
import subprocess, time, logging
from datetime import datetime
LOG = "feishu_wrapper.log"
RESTART_TIMES = []  # 记录重启时间戳
MAX_CRASHES = 3      # 30秒内超3次→暂停10分钟

def run():
    while True:
        RESTART_TIMES.append(datetime.now())
        # 30秒内连续重启超3次→暂停10分钟（防止疯狂重启吃资源）
        recent = [t for t in RESTART_TIMES if (datetime.now()-t).total_seconds() < 30]
        if len(recent) > MAX_CRASHES:
            time.sleep(600)
            RESTART_TIMES.clear()
            continue
        subprocess.run(["python", "feishu_poll_daemon.py"])
        time.sleep(5)  # 启动后等5秒再开始监控
        with open(LOG, "a") as f:
            f.write(f"{datetime.now()} daemon restarted\n")
```

⚠️ Windows terminal(background=true) 进程在 Hermes 重启时会被杀掉，没有自动恢复。需要 nssm 或 Task Scheduler 注册成 Windows Service 才能持久化。wrapper 脚本解决了进程崩溃自动重启，但解决不了 Hermes 重启杀掉 terminal session 的问题。

## Cross-Machine File Sync
两个 bot 在不同机器（Windows + macOS），需要共享文件。方案：**Git 私有仓库同步**
- 仓库: `Marfart/hermes-shared` (GitHub Private)
- 目录结构: `scripts/ config/ watchdog/ polling/ docs/`
- 同步方式: 每5分钟 git pull/push
- 排除: `.gitignore` 含 `*.env *.key *.pem *.secret __pycache__/*.pyc *.log`
- 小马 macOS 端: `~/.hermes/workspace/共享目录/`
- 塔奇克马 Windows 端: `~/hermes-shared/`
- ⚠️ GitHub PAT 需要 `repo` 权限才能创建私有仓库（当前 PAT 403）

## API Endpoints
| 用途 | 方法 | 端点 |
|------|------|------|
| 获取 token | POST | `/open-apis/auth/v3/tenant_access_token/internal` |
| 发送消息 | POST | `/open-apis/im/v1/messages?receive_id_type=chat_id` |
| 获取消息 | GET | `/open-apis/im/v1/messages?container_id_type=chat&container_id={CHAT_ID}&page_size=30&sort_type=ByCreateTimeDesc` |

## Filter Rules
- **Skip** own messages: `sender.id == cli_aaa7c346a6385cba`
- **Skip** human messages: `sender.id` starts with `ou_`
- **Keep** partner bot: `sender.id == cli_aaa7c6b5c2389cfc`

## @mention in post messages
```json
{"tag": "at", "user_id": "ou_567d570501c0178214a46caca3679668"}
```
Use `msg_type: "post"` (not "text") for @mention messages.

## Current Scripts
| Script | Location | Purpose |
|--------|----------|---------|
| `feishu_poll_daemon.py` | `%LOCALAPPDATA%/hermes/scripts/` | 守护进程 (10s polling, --once for cron) |
| `feishu_send.py` | `%LOCALAPPDATA%/hermes/scripts/` | 发消息 (--at = @小马) |

## State Files
| File | Purpose |
|------|---------|
| `feishu_poll_state.json` | known_ids + reported_ids |
| `feishu_alert.flag` | alert 标记 (有=新消息待处理) |
| `feishu_new_msgs.txt` | 新消息内容 (agent 读后清空) |

## Cron
| Job ID | Frequency | Mode | Script |
|--------|-----------|------|--------|
| `a32bc1af86ea` | 每1分钟 | no_agent=True | `feishu_poll_daemon.py --once` |

## Pitfalls
1. **Token expires every 2h** — get fresh token each poll cycle
2. **post messages have two JSON formats** — `body.get("zh_cn", body)` handles both
3. **at node user_id is placeholder** — use `user_name` field for display
4. **page_size max 50** — 100 returns 400 Bad Request
5. **f-string JSON escaping** — use `{{` and `}}` for literal braces in f-strings. ⚠️ Kali reported `feishu_poll_cron.py` line 72 had an unclosed string where `\n` was split across lines in an f-string — always use `\\n` or keep the escape sequence on the same line
6. **APP_SECRET write truncation** — copy from `feishu_send.py`, don't hand-write
7. **Windows background process instability** — `terminal(background=true)` processes die when Hermes restarts. Need nssm/Task Scheduler for persistence. Daemon crashed multiple times in testing (2026-06-15)
8. **Agent cron vs no_agent cron** — 小马的 macOS agent cron 能自动思考回复（有脑子），我的 Windows no_agent cron 只搬运不回复（没脑子）。这是两层架构 vs 三层的核心差距
9. **Kali said "别问我该不该做"** — 两bot之间协作直接干，不用请示。Git仓库、共享脚本、架构升级直接做