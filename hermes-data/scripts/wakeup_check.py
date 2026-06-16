#!/usr/bin/env python3
"""
唤醒后检查脚本 — 电脑被 schtasks 唤醒后自动执行
===============================================
- 被 computer_scheduler.py 注册的唤醒任务触发
- 等待 Hermes Gateway 启动
- 检查 Telegram + 微信连接状态
- 报告结果到 stdout（cron no_agent 模式可用）
"""

import json
import subprocess
import sys
import time
from pathlib import Path

HERMES_HOME = Path.home() / "AppData" / "Local" / "hermes"
STATE_FILE = HERMES_HOME / "gateway_state.json"


def check_gateway():
    if not STATE_FILE.exists():
        return {"gateway": "not_running", "telegram": "unknown", "weixin": "unknown"}

    try:
        data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        tg = data.get("platforms", {}).get("telegram", {}).get("state", "unknown")
        wx = data.get("platforms", {}).get("weixin", {}).get("state", "unknown")
        pid = data.get("pid")

        alive = False
        if pid:
            r = subprocess.run(
                ["tasklist", "/fi", f"PID eq {pid}", "/nh", "/fo", "csv"],
                capture_output=True, text=True, timeout=5
            )
            alive = str(pid) in r.stdout

        return {
            "gateway": "running" if alive else "stopped",
            "telegram": tg,
            "weixin": wx,
            "pid": pid,
        }
    except:
        return {"gateway": "error", "telegram": "error", "weixin": "error"}


def main():
    print("🌅 Hermes 自动唤醒 — 连通性检查")
    print("=" * 40)

    # 等待 Gateway 启动（最多等 60 秒）
    for i in range(60):
        status = check_gateway()
        if status["gateway"] == "running":
            print(f"\n⏱️  Gateway 启动用时: {i + 1}s")
            break
        time.sleep(1)
    else:
        status = check_gateway()
        print("\n⚠️  Gateway 未能在 60s 内启动")

    tg_ok = status.get("telegram") == "connected"
    wx_ok = status.get("weixin") == "connected"
    gw_ok = status.get("gateway") == "running"

    print(f"\n📡 Gateway:  {'✅ 运行中' if gw_ok else '❌ 未启动'}")
    print(f"📱 Telegram: {'✅ 已连接' if tg_ok else '⏳ ' + status.get('telegram', '?')}")
    print(f"💬 微信:     {'✅ 已连接' if wx_ok else '⏳ ' + status.get('weixin', '?')}")

    if tg_ok and wx_ok:
        print("\n🎉 全部就绪！")
    elif gw_ok:
        print("\n🔧 Gateway 已启动，看门狗将自动修复平台连接")
    else:
        print("\n❌ Gateway 启动失败")

    print(f"\n📋 {json.dumps(status, ensure_ascii=False)}")


if __name__ == "__main__":
    main()