#!/usr/bin/env python3
"""
Telegram Watchdog Alarm Bridge — cron 调用脚本
由 cron 每分钟触发，检查 .telegram_status 文件，
如果为 disconnected，输出警报文字到当前终端。
输出为空时 cron 静默不发送（不打扰）。
"""
import json, time
from pathlib import Path

HERMES_HOME = Path.home() / "AppData" / "Local" / "hermes"
STATUS_FILE = HERMES_HOME / "logs" / ".telegram_status"

if not STATUS_FILE.exists():
    # 无状态文件 = 初次运行或刚清理，静默
    exit(0)

try:
    data = json.loads(STATUS_FILE.read_text())
except Exception:
    exit(0)

status = data.get("status", "connected")
detail = data.get("detail", "")
ts = data.get("ts", 0)
age = time.time() - ts

# 只在 5 分钟内断连才报警（避免旧状态残留）
if status == "disconnected" and age < 300:
    print(f"⚠️⚠️⚠️ Telegram 连接已断开！⚠️⚠️⚠️")
    print(f"   时间: {time.strftime('%H:%M:%S', time.localtime(ts))}")
    if detail:
        print(f"   原因: {detail}")
    print(f"   建议: 在终端运行 hermes gateway restart 恢复")
elif status == "connected" and age < 120:
    # 刚刚恢复时安静提示
    pass