#!/bin/bash
# 飞书群消息轮询守护进程 — 每10秒调用feishu_poll_cron.py
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
while true; do
    python "$SCRIPT_DIR/feishu_poll_cron.py" 2>/dev/null
    sleep 10
done