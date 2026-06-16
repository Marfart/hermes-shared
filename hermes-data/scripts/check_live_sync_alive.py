#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查 hermes_live_sync 是否活着，不在就重启 (no_agent=True)
直接用 DETACHED_PROCESS 启动 Python 同步脚本，不经过 .cmd 桥梁"""
import os
import subprocess
import sys
from pathlib import Path

HERMES_HOME = Path(os.environ.get("USERPROFILE", "C:\\Users\\Admin")) / "AppData" / "Local" / "hermes"
PID_FILE = HERMES_HOME / ".hermes_live_sync.pid"
VENV_PYTHON = HERMES_HOME / "hermes-agent" / "venv" / "Scripts" / "python.exe"
SYNC_SCRIPT = HERMES_HOME / "scripts" / "hermes_live_sync.py"

def main() -> int:
    # 检查PID文件
    if PID_FILE.exists():
        try:
            pid_str = PID_FILE.read_text().strip()
            if pid_str:
                pid = int(pid_str)
                # 用 os.kill(pid, 0) 快速检查进程（Windows上带权限问题）
                # 改用 tasklist（更兼容Windows）
                _flags = subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
                r = subprocess.run(
                    ["tasklist", "/FI", f"PID eq {pid}", "/NH"],
                    capture_output=True, text=True, timeout=10, errors="replace",
                    creationflags=_flags
                )
                if str(pid) in r.stdout:
                    return 0  # 进程活着
        except (ValueError, OSError, subprocess.TimeoutExpired):
            pass

    # 进程死了，重启
    python_exe = str(VENV_PYTHON)
    script_path = str(SYNC_SCRIPT)

    # 确保脚本存在
    if not SYNC_SCRIPT.exists():
        # fallback to system python if venv python missing
        python_exe = "python"

    # DETACHED_PROCESS (0x8) + CREATE_NO_WINDOW (0x08000000) = 完全分离后台进程
    subprocess.Popen(
        [python_exe, script_path],
        creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NO_WINDOW,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
    )
    print("[live-sync-mon] ⚡ 守护进程已重启（DETACHED）")
    return 0

if __name__ == "__main__":
    sys.exit(main())