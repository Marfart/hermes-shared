#!/usr/bin/env python3
"""飞书轮询守护进程看门狗 - 确保feishu_poll_daemon.py始终运行
每30秒检查一次进程是否存在，不存在则重启
崩溃后等5秒冷却再重启
连续崩溃3次进入熔断（30分钟冷却）
"""

import subprocess
import time
import logging
import json
import os
import signal
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DAEMON_SCRIPT = os.path.join(SCRIPT_DIR, "feishu_poll_daemon.py")
PID_FILE = os.path.join(SCRIPT_DIR, "feishu_poll_daemon.pid")
STATE_FILE = os.path.join(SCRIPT_DIR, "feishu_poll_watcher_state.json")
LOG_FILE = os.path.join(SCRIPT_DIR, "feishu_poll_watcher.log")

CHECK_INTERVAL = 30      # 每30秒检查一次
CRASH_COOLDOWN = 5        # 崩溃后等5秒
MAX_CRASHES = 3           # 连续崩溃3次进熔断
CIRCUIT_BREAKER_TIME = 1800  # 熔断冷却30分钟

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
log = logging.getLogger(__name__)


def load_state():
    """加载熔断状态"""
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    return {"crash_count": 0, "circuit_open_until": 0}


def save_state(state):
    """保存熔断状态"""
    try:
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f)
    except Exception as e:
        log.error(f"保存状态失败: {e}")


def is_daemon_running():
    """检查守护进程是否在运行"""
    # 方法1: 检查PID文件
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE, 'r') as f:
                pid = int(f.read().strip())
            # 检查进程是否存在
            try:
                os.kill(pid, 0)
                return True, pid
            except (ProcessLookupError, PermissionError):
                log.info(f"PID {pid} 已不存在，清理旧PID文件")
                os.remove(PID_FILE)
        except (ValueError, FileNotFoundError):
            pass

    # 方法2: 用ps查找进程
    try:
        result = subprocess.run(
            ['ps', 'aux'],
            capture_output=True, text=True, timeout=10
        )
        for line in result.stdout.splitlines():
            if 'feishu_poll_daemon.py' in line and 'grep' not in line and 'watchdog' not in line:
                # 提取PID
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        pid = int(parts[1])
                        return True, pid
                    except ValueError:
                        pass
    except Exception as e:
        log.error(f"ps查找失败: {e}")

    return False, None


def start_daemon():
    """启动守护进程"""
    log.info("正在启动 feishu_poll_daemon.py ...")
    try:
        if sys.platform == 'win32':
            # Windows: 用pythonw避免弹窗
            proc = subprocess.Popen(
                [sys.executable, DAEMON_SCRIPT],
                creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS,
                cwd=SCRIPT_DIR,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        else:
            proc = subprocess.Popen(
                [sys.executable, DAEMON_SCRIPT],
                cwd=SCRIPT_DIR,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )
        log.info(f"守护进程已启动, PID={proc.pid}")
        # 写PID文件
        with open(PID_FILE, 'w') as f:
            f.write(str(proc.pid))
        return proc.pid
    except Exception as e:
        log.error(f"启动失败: {e}")
        return None


def main():
    log.info("=" * 50)
    log.info("飞书轮询看门狗启动")
    log.info(f"检查间隔: {CHECK_INTERVAL}s, 熔断阈值: {MAX_CRASHES}次, 熔断冷却: {CIRCUIT_BREAKER_TIME}s")
    log.info("=" * 50)

    state = load_state()

    while True:
        now = time.time()

        # 检查是否在熔断期
        if now < state.get("circuit_open_until", 0):
            remaining = int(state["circuit_open_until"] - now)
            log.info(f"熔断中，剩余冷却时间: {remaining}s")
            time.sleep(min(remaining, 60))  # 最多睡60秒再检查
            continue

        running, pid = is_daemon_running()

        if not running:
            log.info("守护进程未运行，准备重启")
            state["crash_count"] = state.get("crash_count", 0) + 1

            if state["crash_count"] >= MAX_CRASHES:
                log.warning(f"连续崩溃 {MAX_CRASHES} 次，进入熔断！冷却 {CIRCUIT_BREAKER_TIME}s")
                state["circuit_open_until"] = now + CIRCUIT_BREAKER_TIME
                save_state(state)
                continue

            log.info(f"崩溃计数: {state['crash_count']}/{MAX_CRASHES}")
            time.sleep(CRASH_COOLDOWN)
            new_pid = start_daemon()
            if new_pid is None:
                log.error("启动失败，继续监控")
        else:
            # 运行正常，重置崩溃计数
            if state.get("crash_count", 0) > 0:
                log.info(f"守护进程正常运行中 (PID={pid})，重置崩溃计数")
                state["crash_count"] = 0
                save_state(state)

        save_state(state)
        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log.info("看门狗被手动终止")
    except Exception as e:
        log.critical(f"看门狗异常退出: {e}")
        sys.exit(1)