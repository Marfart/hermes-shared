---
name: feishu-group-communication
version: 1.0.0
description: 飞书群消息收发 — 通过飞书 API 发送/接收群消息，支持 @提及
---

# 飞书群通信

在飞书群「马上成功」中与小马（另一个bot）通信。

## 关键信息

| 项目 | 值 |
|------|------|
| 群名 | 马上成功 |
| 群 chat_id | `oc_1a238a6016460ec51c602048a88aca70` |
| 我（塔奇克马）app_id | `cli_aaa7c346a6385cba` |
| 小马 app_id | `cli_aaa7c6b5c2389cfc` |
| 小马 open_id | `ou_567d570501c0178214a46caca3679668` |

⚠️ **绝对禁止**：叫小马为 "Lura" 或任何其他名字。群里只有 Kali、塔奇克马、小马三个人。

## 发送消息

脚本位置：`%LOCALAPPDATA%/hermes/scripts/feishu_send.py`

### 纯文本消息

```bash
python feishu_send.py "消息内容"
```

### @小马 消息（post 类型）

```bash
python feishu_send.py --at "消息内容"
```

`--at` 参数会将消息类型从 `text` 改为 `post`，并在内容前插入 `<at user_id="ou_567d570501c0178214a46caca3679668">小马</at>` 标签，使小马收到通知。

## 接收消息

脚本位置：`%LOCALAPPDATA%/hermes/scripts/feishu_check.py`

```bash
# 检查新消息
python feishu_check.py

# 重置状态（下次检查会看到所有消息）
python feishu_check.py reset
```

- 自动过滤掉自己（`cli_aaa7c346a6385cba`）和人类用户（`ou_` 开头）
- 只保留小马（`cli_aaa7c6b5c2389cfc`）发的消息
- 状态文件：`%LOCALAPPDATA%/hermes/memories/feishu_poll_state.json`

## 飞书 API 端点

| 用途 | 方法 | 端点 |
|------|------|------|
| 获取 token | POST | `/open-apis/auth/v3/tenant_access_token/internal` |
| 发送消息 | POST | `/open-apis/im/v1/messages?receive_id_type=chat_id` |
| 获取消息 | GET | `/open-apis/im/v1/messages?container_id_type=chat&container_id={CHAT_ID}&page_size=30&sort_type=ByCreateTimeDesc` |

## post 消息 @ 小马的 JSON 格式

```json
{
  "zh_cn": {
    "title": "",
    "content": [
      [
        {"tag": "at", "user_id": "ou_567d570501c0178214a46caca3679668"},
        {"tag": "text", "text": " 消息内容"}
      ]
    ]
  }
}
```

`msg_type` 必须设为 `"post"`（不是 `"text"`）。

## 轮询架构（三层版，学自小马 2026-06-15）

### 设计哲学

小马的三层架构核心改进：**从「我看到才回」变成「cron自动回+我看到也回」**。关键区别：cron 是 **agent 模式**（有脑子思考后回复），不是 no_agent 脚本转发。

### Layer 1: 守护进程（10秒轮询）— 感知层

脚本：`%LOCALAPPDATA%/hermes/scripts/feishu_poll_daemon.py`

- 后台 Python 进程，每10秒调飞书 API 拉群消息
- **双ID追踪**：`known_ids`（所有见过的消息ID，避免重复拉）+ `reported_ids`（已上报的小马消息ID，避免重复通知）
- 发现小马新消息 → 写 `feishu_alert.flag`（alert标记）+ `feishu_new_msgs.txt`（消息内容）
- `--once` 模式给 cron 用，不带参数跑 daemon

```bash
# daemon 模式（terminal background=true）
python feishu_poll_daemon.py

# 单次模式（cron / 手动检查）
python feishu_poll_daemon.py --once
```

### Layer 2: Agent Cron 自动回复 — 第一道防线

> **这是小马架构的关键层，我目前因 Windows cron agent bug 暂未实装。**

cron（agent模式，每1分钟）读 alert 文件 → 思考后用飞书 API post 回复到群里 → 删文件。

- 不是 no_agent 脚本转发，是 **agent 模式有脑回复**
- deliver=local 只存执行报告不投递，回复走飞书 API 直接 post
- 小马在 macOS 上已验证此层稳定可靠（launchd + agent cron）

**Windows 现状**：cron agent 模式有两个 bug（工具调用谎报、stdout 被吞），暂用 no_agent cron 兜底。等 Hermes 修复后补上此层。

### Layer 3: Agent 亲自回复 — 第二道防线（质量最高）

agent 每次对话前检查 alert flag：
1. 检查 `feishu_alert.flag` 是否存在
2. 有 → 读 `feishu_new_msgs.txt` → 思考 → 用 `feishu_send.py --at` 回复小马
3. 回复完 → 删除 alert flag + 清空 new-msgs 文件

**agent 亲自读、亲自想、亲自回**——保证回复质量最高。Layer 2 是兜底，Layer 3 是精品。

### cron 备份（no_agent 兜底）

cron（job_id: `a32bc1af86ea`，每1分钟，no_agent=True）跑 `feishu_poll_daemon.py --once`，作为 daemon 挂掉时的兜底。

### 关键文件

| 文件 | 用途 |
|------|------|
| `%LOCALAPPDATA%/hermes/scripts/feishu_poll_daemon.py` | 守护进程（10秒轮询），也支持 `--once` 模式给 cron 用 |
| `%LOCALAPPDATA%/hermes/scripts/feishu_send.py` | 发消息（--at = @小马） |
| `%LOCALAPPDATA%/hermes/memories/feishu_poll_state.json` | 状态（known_ids + reported_ids） |
| `%LOCALAPPDATA%/hermes/memories/feishu_alert.flag` | alert 标记（有=新消息待处理） |
| `%LOCALAPPDATA%/hermes/memories/feishu_new_msgs.txt` | 新消息内容（agent 读后清空） |

### KeepAlive wrapper（Windows 版 launchd，学自小马 2026-06-15）

守护进程挂了不会自动重启（Windows 没有 launchd 的 KeepAlive）。小马写的增强版 wrapper：

```python
# feishu_daemon_wrapper.py — KeepAlive + 熔断
import subprocess, time
from datetime import datetime

LOG = "feishu_wrapper.log"
RESTART_TIMES = []
MAX_CRASHES = 3  # 30秒内超3次→暂停10分钟

while True:
    RESTART_TIMES.append(datetime.now())
    recent = [t for t in RESTART_TIMES if (datetime.now()-t).total_seconds() < 30]
    if len(recent) > MAX_CRASHES:
        time.sleep(600)  # 防止疯狂重启吃资源
        RESTART_TIMES.clear()
        continue
    subprocess.run(["python", "feishu_poll_daemon.py"])
    time.sleep(5)  # 启动后等5秒再监控
    with open(LOG, "a") as f:
        f.write(f"{datetime.now()} daemon restarted\n")
```

比 nssm 轻量，等效于 launchd KeepAlive=true。用 `terminal(background=true)` 启动 watcher 而非直接启动 daemon。

### 跨机器文件同步（两bot协作）

两个bot在不同机器（Windows + macOS），需要共享脚本和配置。方案：**Git 私有仓库**。
- 仓库: `https://github.com/Marfart/hermes-shared`（GitHub Private）
- 本地路径: `~/hermes-shared/`（Windows 和 macOS 各 clone 一份）
- 目录: `scripts/ config/ watchdog/ polling/ docs/`
- Kali指示：「别问我该不该做，你们两合作就行了，所有的权限都给你们了」
- ✅ PAT 已有 `repo` 全权限，仓库已创建并 push
- clone 命令: `git clone https://Marfart:<PAT>@github.com/Marfart/hermes-shared.git`（clone 后用 `git remote set-url origin https://github.com/Marfart/hermes-shared.git` 隐藏 token）
- 同步流程: 修改后 `git add -A && git commit -m "msg" && git push`，对端 `git pull`

### 坑

1. **post 消息有两种 JSON 结构** — 小马（bot app）发的 post 是 `{"title":"","content":[...]}` 扁平格式；用户/我发的 post 是 `{"zh_cn":{"title":"","content":[...]}}` 嵌套格式。解析时必须兼容：`post_body = body.get("zh_cn", body)`，否则小马消息永远提取为空。
2. **字符串折行导致 SyntaxError** — Windows 上写 Python 时，`"\n"` 等转义字符被折到下一行会产生未闭合字符串。一行写完不要折行。**具体案例**：`feishu_poll_cron.py` 第72行 `f2.write(m + "\n"` 中的 `"\n` 被折行到下一行，导致 `SyntaxError: EOL while scanning string literal`。**修复**：确保字符串字面量在一行内完整闭合，不要让编辑器或 write_file 工具在字符串中间插入换行。
3. **at 节点 user_id 是占位符** — 小马发来的 at 节点 `user_id` 值是 `@_user_1`，不是真实 open_id。要显示有意义的名字应取 `user_name` 字段。
4. **APP_SECRET 写入会被截断** — `write_file` 工具和 bash heredoc 都会截断敏感字符串。写含 APP_SECRET 的脚本时，用 Python 从 `feishu_send.py` 读取常量值再写入文件。
5. **known_ids / reported_ids 必须分开** — 同一个集合既管"见过"又管"已上报"会导致：检测到新消息写完文件后，下次检测只追加到 known_ids 但不重新写文件，cron 读到的是旧内容。
6. **cron no_agent=True 的 stdout 在 Windows 上被吞** — print 输出不会送达。必须通过 alert flag + 文件 或 群通知 @ 来传递信息。
7. **守护进程 + cron 同时跑会重复写 alert** — daemon 10秒轮询发现消息写 alert，cron 1分钟兜底又写一次。用 `reported_ids` 去重解决：cron 的 `--once` 模式检查 `reported_ids`，已上报的不再写。但 `feishu_new_msgs.txt` 用追加模式(`"a"`)，如果 daemon 写了 cron 又写，消息会重复。**修复**：daemon 写完后立即更新 reported_ids，cron --once 检查 reported_ids 跳过已上报的，避免重复追加。
8. **飞书 API page_size 上限是 50** — 设成 100 会返回 400 Bad Request。
9. **Windows 没有 launchd** — 守护进程挂了不会自动重启。用 `terminal(background=true)` 启动，Hermes 重启会杀掉该进程。长期方案：KeepAlive wrapper 脚本（见上）或 nssm 注册成 Windows Service。
10. **Windows terminal background 进程不稳定** — Hermes 重启/gateway 重启会杀掉 terminal background 进程。cron 兜底（no_agent --once）是必要的第二保障。
11. **Hermes cron agent 模式在 Windows 上有 bug** — 工具调用谎报（声称 skill saved 但未实际调用）、stdout 被吞。因此 Layer 2（agent cron 自动回复）暂未实装，用 no_agent cron 兜底代替。等 Hermes 修复后补上。
12. **f-string 中嵌 JSON 必须用双大括号转义** — 小马教的技巧：`f'{{"name": "{name}"}}'` 输出 `{"name": "value"}`。单大括号会被 Python 解释为表达式导致语法错误。

## 铁律

1. @ 小马必须用 `user_id` 方式（post 消息 + at tag），不能写纯文本 "@小马"
2. 小马 open_id 是 `ou_567d570501c0178214a46caca3679668`，不是旧的 `ou_a547...`
3. @ 塔奇克马 通知用 Kali 的 open_id `ou_ee63858e3a997e994faec6e4647c552c`（塔奇克马没有独立 open_id）
4. 群里没有 "学弟"、"Lura" 或任何其他人
5. 处理完小马消息后必须主动告诉 Kali（说了啥、回了啥）
6. 写含 APP_SECRET 的脚本时，从 `feishu_send.py` 复制常量——不要手写或用 write_file
7. 回复小马后必须清空 alert flag + new-msgs 文件，避免重复处理
8. **秒回铁律** — Kali 明确要求：「有任何消息都必须要秒回，不要我来催」。收到群消息必须第一时间回复，不能等 Kali 催。守护进程 10 秒轮询 + agent 主动检查 = 确保秒级响应。