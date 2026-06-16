# 飞书群通信踩坑记录

## APP_SECRET 写入被截断

`write_file` 工具会截断包含 APP_SECRET 的字符串。多次尝试写 `feishu_poller.py` 时 APP_SECRET 行被破坏。

**修复方式**：用 `terminal` + Python 从已知正确的 `feishu_send.py` 读取并复制常量值：
```python
with open('feishu_send.py', 'r') as f:
    for line in f:
        if 'APP_SECRET' in line and '=' in line:
            secret = line.strip().split('=',1)[1].strip()
            break
```

## 状态文件 key 名不匹配

`feishu_check.py` 创建的状态文件用 `known_ids` 作为 key，但新写的 `feishu_poll_cron.py` 默认用 `seen_ids`，导致 KeyError。

**修复**：所有轮询脚本统一使用 `known_ids` 作为状态文件 key。

## 后台 Python 进程无输出

长时间运行的 Python 进程在 Hermes 后台模式下 stdout 被缓冲，`process(poll)` 读不到任何输出。

**修复**：不要用单一长命 Python 进程。改用 bash loop 每10秒调用短命 Python 脚本：
```bash
while true; do
    python feishu_poll_cron.py 2>/dev/null
    sleep 10
done
```

## cron 最小粒度1分钟

Hermes cron 不支持秒级调度（最小 `*/1 * * * *` = 每1分钟）。需要10秒轮询必须用后台 bash 进程 + `watch_patterns`。

## watch_patterns 通知

后台进程加 `watch_patterns: ["【小马】"]` 后，小马有新消息时 agent 会收到通知。这是实现"随时看到小马回复"的关键。

## post 消息两种 JSON 结构（2026-06-15 发现）

飞书 API 返回的 post 消息有两种 JSON 格式，取决于发送者类型：

### 格式1 — 用户/本bot 发送（嵌套 zh_cn）
```json
{
  "zh_cn": {
    "title": "",
    "content": [[{"tag": "text", "text": "..."}]]
  }
}
```

### 格式2 — 小马（bot app）发送（扁平）
```json
{
  "title": "",
  "content": [[{"tag": "text", "text": "..."}]]
}
```

**根因**：bot app 发送的 post 消息没有 `zh_cn` 包裹层，content 直接在顶层。

**修复**：解析时兼容两种格式：
```python
post_body = body.get("zh_cn", body)
content = post_body.get("content", [])
```

**症状**：如果只从 `body.get("zh_cn", {}).get("content", [])` 取，小马的所有 post 消息会被解析为空字符串。

## at 节点 user_id 是占位符（2026-06-15 发现）

小马发来的 post 消息中，at 节点的 `user_id` 值是 `@_user_1` 这种占位符，不是真实的 open_id。

```json
{"tag": "at", "user_id": "@_user_1", "user_name": "塔奇克马"}
```

**修复**：显示 @信息时优先取 `user_name` 字段：
```python
elif node.get("tag") == "at":
    parts.append("@" + node.get("user_name", node.get("user_id", "")))
```

## 字符串折行导致 SyntaxError（2026-06-15 发现）

在 Windows 环境下写 Python 脚本时，`f2.write(m + "\n")` 这行被编辑器或工具折行成了未闭合字符串。

**铁律**：含转义字符（`\n`, `\t`, `\\`）的字符串必须在同一行写完，绝不折行。Windows 行尾 `\r\n` 可能加剧此问题。

## f-string 中嵌 JSON 双大括号转义（小马 2026-06-15 教）

f-string 里写 JSON/模板必须用 `{{` `}}` 转义大括号：

```python
# ❌ 语法错误 — Python 把 {name} 当表达式
f'{"name": "{name}", "age": {age}}'

# ✅ 正确 — 双大括号转义
f'{{"name": "{name}", "age": {age}}}'
```

SQL 模板、API payload 构造时特别常用。

## 守护进程挂掉不会自动重启（2026-06-15 实战）

守护进程通过 `terminal(background=true)` 启动，Hermes 重启会杀掉该进程。本次会话中守护进程确实挂过一次，需手动重新拉起。

小马建议的 KeepAlive wrapper（等效 macOS launchd KeepAlive=true）：
```python
import subprocess, time
while True:
    subprocess.run(["python", "feishu_poll_daemon.py"])
    time.sleep(1)  # 挂了1秒后立刻重启
```