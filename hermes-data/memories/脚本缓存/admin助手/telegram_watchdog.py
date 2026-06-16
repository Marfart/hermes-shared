#!/usr/bin/env python3
"""
Telegram Watchdog — 零消耗守护脚本
功能：监控 → 诊断 → 自动修复 → 简约通知
"""
import os, re, time, json, subprocess, signal
from pathlib import Path
from datetime import datetime

HERMES_HOME = Path(os.environ.get("HERMES_HOME",
    Path.home() / "AppData" / "Local" / "hermes"))
GATEWAY_LOG = HERMES_HOME / "logs" / "gateway.log"
STATUS_FILE = HERMES_HOME / "logs" / ".telegram_status"
CHECK_INTERVAL = 15

# 断连特征
DISCONNECT_PATTERNS = [
    (re.compile(r"\[Telegram\] .*?send_path_degraded"), "Telegram 发送通道异常"),
    (re.compile(r"\[Telegram\] .*?Failed to deliver"), "Telegram 消息投递失败"),
    (re.compile(r"\[Telegram\] .*?Network error"), "Telegram 网络错误"),
    (re.compile(r"\[Telegram\] .*?Timed out"), "Telegram 请求超时"),
    (re.compile(r"✗ telegram.*?error"), "Telegram 连接错误"),
    (re.compile(r"\[Telegram\] .*?disconnect"), "Telegram 主动断开"),
]
RECONNECT_PATTERN = re.compile(r"\[Telegram\] Connected")
HEARTBEAT_PATTERN = re.compile(r"memory_monitor.*?uptime=")

_alerted = False
_repairing = False

def now_str():
    return datetime.now().strftime("%H:%M:%S")

def is_gateway_alive():
    """检查 gateway 是否还在跑"""
    try:
        lines = open(GATEWAY_LOG, encoding="utf-8", errors="replace").readlines()[-30:]
        for line in reversed(lines):
            if HEARTBEAT_PATTERN.search(line):
                m = re.match(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", line)
                if m:
                    ts = datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S")
                    return (datetime.now() - ts).total_seconds() < 180
    except: pass
    return False

def restart_gateway():
    """尝试重启 gateway"""
    # 先找 gateway 进程杀掉
    try:
        result = subprocess.run(
            ["tasklist", "/fi", "IMAGENAME eq python*", "/fo", "csv", "/nh"],
            capture_output=True, text=True, timeout=10
        )
        for line in result.stdout.split("\n"):
            if "gateway" in line.lower() or "hermes" in line.lower():
                # 尝试找 PID
                parts = line.split(",")
                if len(parts) >= 2:
                    pid = parts[1].strip().strip('"')
                    if pid.isdigit():
                        try:
                            os.kill(int(pid), signal.SIGTERM)
                        except: pass
    except: pass

    time.sleep(2)

    # 启动新的 gateway
    hermes_bin = str(HERMES_HOME / "hermes-agent" / "venv" / "Scripts" / "hermes")
    subprocess.Popen(
        [hermes_bin, "gateway", "run"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0
    )

def diagnose(lines):
    """诊断断联原因"""
    for line in reversed(lines):
        for pat, desc in DISCONNECT_PATTERNS:
            if pat.search(line):
                return desc
    return "Gateway 进程异常退出"

def wait_for_reconnect(timeout=60):
    """等待网关重新连上 Telegram"""
    deadline = time.time() + timeout
    # 先清空旧的状态——等新日志
    while time.time() < deadline:
        try:
            with open(GATEWAY_LOG, encoding="utf-8", errors="replace") as f:
                recent = f.readlines()[-20:]
            for line in reversed(recent):
                if RECONNECT_PATTERN.search(line):
                    return True
        except: pass
        time.sleep(3)
    return False

def run():
    global _alerted, _repairing
    while True:
        try:
            log_exists = GATEWAY_LOG.exists()
            if not log_exists:
                if not _alerted:
                    print(f"🚨 [{now_str()}] 断联原因: gateway.log 不存在，gateway 未启动")
                    print(f"🛠️  [{now_str()}] 自动修复中...预计 1 分钟")
                    restart_gateway()
                    _alerted = True
                    _repairing = True
                time.sleep(CHECK_INTERVAL)
                continue

            with open(GATEWAY_LOG, encoding="utf-8", errors="replace") as f:
                lines = f.readlines()[-100:]

            # 检查是否有 Telegram 连接
            has_telegram = any("[Telegram]" in l for l in lines)
            connected = any(RECONNECT_PATTERN.search(l) for l in lines)

            if connected:
                if _repairing or _alerted:
                    # 刚刚修复成功
                    print(f"✅ [{now_str()}] 已修复，可以正常连接了")
                    _repairing = False
                    _alerted = False
                    STATUS_FILE.write_text(json.dumps({
                        "ts": time.time(), "status": "connected"
                    }))
                _alerted = False
                time.sleep(CHECK_INTERVAL)
                continue

            # Telegram 日志存在但没有连接状态
            if has_telegram:
                # 检测是否有错误
                has_error = False
                for line in reversed(lines):
                    for pat, _ in DISCONNECT_PATTERNS:
                        if pat.search(line):
                            has_error = True
                            break
                    if has_error: break

                if has_error and not _alerted:
                    cause = diagnose(lines)
                    print(f"🚨 [{now_str()}] 断联原因: {cause}")
                    print(f"🛠️  [{now_str()}] 自动修复中...预计 1 分钟")
                    _alerted = True
                    _repairing = True
                    STATUS_FILE.write_text(json.dumps({
                        "ts": time.time(), "status": "disconnected",
                        "detail": cause,
                        "fixing": True
                    }))

                if _repairing and not connected:
                    # 修理中，检查一下 gateway 是否需要重启
                    if not is_gateway_alive():
                        print(f"🛠️  [{now_str()}] Gateway 无响应，重新启动...")
                        restart_gateway()
                        if wait_for_reconnect():
                            print(f"✅ [{now_str()}] 已修复，可以正常连接了")
                            _repairing = False
                            _alerted = False
                            STATUS_FILE.write_text(json.dumps({
                                "ts": time.time(), "status": "connected"
                            }))

            else:
                # 完全没有 Telegram 日志
                if not is_gateway_alive():
                    if not _alerted:
                        print(f"🚨 [{now_str()}] 断联原因: Gateway 进程无响应")
                        print(f"🛠️  [{now_str()}] 自动修复中...预计 1 分钟")
                        _alerted = True
                        _repairing = True
                        STATUS_FILE.write_text(json.dumps({
                            "ts": time.time(), "status": "disconnected",
                            "detail": "Gateway 进程无响应",
                            "fixing": True
                        }))
                    restart_gateway()
                    if wait_for_reconnect():
                        print(f"✅ [{now_str()}] 已修复，可以正常连接了")
                        _repairing = False
                        _alerted = False
                        STATUS_FILE.write_text(json.dumps({
                            "ts": time.time(), "status": "connected"
                        }))

        except Exception as e:
            print(f"⚠️ [{now_str()}] Watchdog 异常: {e}")

        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        pass