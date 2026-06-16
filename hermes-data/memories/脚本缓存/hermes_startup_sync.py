#!/usr/bin/env python3
"""
Hermes 一次性全量同步到桌面备份目录
用途：开机启动时跑一次，确保 Desktop/Working/Hermes/ 是最新版本
"""

import os, sys, time
sys.path.insert(0, os.path.join(
    os.environ.get("LOCALAPPDATA", os.path.join(os.environ["USERPROFILE"], "AppData", "Local")),
    "hermes", "scripts"
))

from hermes_sync import main as sync_main

if __name__ == "__main__":
    # 延迟5秒等 Hermes 完全启动
    time.sleep(5)
    sync_main()
    print("✅ Hermes 全量同步完成")