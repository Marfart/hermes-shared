#!/bin/bash
# feishu-poller-watchdog.sh
# 飞书群消息轮询守护进程的看门狗
# 检测是否存活 + state文件是否及时更新
# 不健康时自动重启

PIDFILE="/tmp/feishu-poller-watchdog.pid"
STATE_FILE="/tmp/feishu-group-poller-state.json"
LABEL="ai.hermes.feishu-group-poller"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
LOG="$HOME/.hermes/logs/feishu-poller-watchdog.log"

# Prevent concurrent runs
if [ -f "$PIDFILE" ]; then
    OLD_PID=$(cat "$PIDFILE")
    if kill -0 "$OLD_PID" 2>/dev/null; then
        exit 0  # Already running
    fi
fi
echo $$ > "$PIDFILE"
trap 'rm -f "$PIDFILE"' EXIT

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG"; }

# 1. Check process existence
PROC_PID=$(launchctl list | grep "$LABEL" | awk '{print $1}')
if [ -z "$PROC_PID" ] || [ "$PROC_PID" = "-" ]; then
    log "⚠️ 进程不存在，重启 launchd"
    launchctl unload "$PLIST" 2>/dev/null
    launchctl load "$PLIST"
    exit 0
fi

# 2. Check state file freshness (should be updated every ~10s)
if [ -f "$STATE_FILE" ]; then
    NOW=$(date +%s)
    MTIME=$(stat -f "%m" "$STATE_FILE" 2>/dev/null || echo "0")
    AGE=$((NOW - MTIME))
    if [ "$AGE" -gt 60 ]; then
        log "⚠️ state 文件已 $AGE 秒未更新（超60s），进程可能卡死，强制重启"
        kill -9 "$PROC_PID" 2>/dev/null
        launchctl unload "$PLIST" 2>/dev/null
        launchctl load "$PLIST"
        exit 0
    fi
fi

# Healthy — no output (silent = zero tokens)
exit 0