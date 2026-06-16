#!/usr/bin/env bash
# 检查 hermes_live_sync 是否活着，不在就重启
# cron no_agent=True 模式
# 注意：所有路径必须用Windows原生格式（不经过MSYS路径转换）

HERMES_HOME="$HOME/AppData/Local/hermes"
PID_FILE="$HERMES_HOME/.hermes_live_sync.pid"
# Windows原生路径（PowerShell不认识POSIX路径）
SCRIPT="C:\\Users\\Admin\\AppData\\Local\\hermes\\Hermes_Live_Sync_Startup.cmd"

if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE" 2>/dev/null)
    if [ -n "$OLD_PID" ]; then
        # 用 kill -0 检查进程（不依赖tasklist的语言环境）
        kill -0 "$OLD_PID" 2>/dev/null && exit 0
    fi
fi

# 进程死了，重启
# 用 cmd /c start 后台启动（无窗口），不经过PowerShell
cmd.exe /c start /B "" "$SCRIPT" 2>/dev/null
echo "[live-sync-mon] ⚡ 守护进程已重启"