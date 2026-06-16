#!/usr/bin/env python3
"""
Telegram Watchdog v3 — 直接监控 gateway_state.json
- 每 1 分钟 cron 触发
- 检测到断连 → 自动重启 → 输出通知（投递给 Kali）
- 没问题时静默（empty stdout = silent）
"""
import json, time, subprocess, sys
from pathlib import Path

HERMES_HOME = Path.home() / "AppData" / "Local" / "hermes"
STATE_FILE = HERMES_HOME / "gateway_state.json"
LOG_FILE = HERMES_HOME / "logs" / "gateway.log"

def now_str():
    from datetime import datetime
    return datetime.now().strftime("%H:%M:%S")

def is_process_alive(pid):
    """检查 PID 是否存活（Windows 兼容）"""
    if not pid:
        return False
    try:
        # Windows: tasklist 查 PID
        r = subprocess.run(
            ["tasklist", "/fi", f"PID eq {pid}", "/nh", "/fo", "csv"],
            capture_output=True, text=True, timeout=5
        )
        return pid in r.stdout
    except:
        return False

def read_state():
    """读取 gateway_state.json"""
    if not STATE_FILE.exists():
        return None, "gateway_state.json 不存在"
    try:
        data = json.loads(STATE_FILE.read_text())
        tg = data.get("platforms", {}).get("telegram", {})
        return data, tg
    except Exception as e:
        return None, f"读取状态文件失败: {e}"

def diagnose_from_log():
    """从 gateway.log 里找断联原因"""
    if not LOG_FILE.exists():
        return "Gateway 未启动 (gateway.log 不存在)"
    try:
        lines = LOG_FILE.read_text(encoding="utf-8", errors="replace").splitlines()
        for line in reversed(lines):
            ll = line.lower()
            if "telegram" in ll and "error" in ll:
                # 截取关键信息
                return line.strip()[:120]
            if "telegram" in ll and "timeout" in ll:
                return "Telegram 连接超时"
            if "telegram" in ll and "disconnect" in ll:
                return "Telegram 连接断开"
            if "telegram" in ll and "fail" in ll:
                return "Telegram 消息投递失败"
            if "telegram" in ll and "close" in ll:
                # 看看是不是正常关闭
                continue
        # 看看最后几行有没有异常
        for line in reversed(lines[-20:]):
            if "error" in line.lower() and "traceback" in line.lower():
                return f"Gateway 进程异常: {line.strip()[:100]}"
    except:
        pass
    return "Gateway 进程异常退出 (日志无明显错误)"

def restart_gateway():
    """杀掉旧进程 + 启动新 gateway"""
    # 1. 读旧 PID 杀掉
    try:
        data = json.loads(STATE_FILE.read_text())
        old_pid = data.get("pid")
        if old_pid and is_process_alive(old_pid):
            subprocess.run(["taskkill", "/f", "/pid", str(old_pid)],
                           capture_output=True, timeout=5)
            time.sleep(2)
    except:
        pass

    # 2. 再清理一下所有残余的 gateway 进程
    try:
        result = subprocess.run(
            ["tasklist", "/fo", "csv", "/nh"],
            capture_output=True, text=True, timeout=10
        )
        for line in result.stdout.split("\n"):
            if "gateway" in line.lower():
                parts = line.split(",")
                if len(parts) >= 2:
                    pid = parts[1].strip().strip('"')
                    if pid.isdigit() and is_process_alive(int(pid)):
                        subprocess.run(["taskkill", "/f", "/pid", pid],
                                       capture_output=True, timeout=5)
        time.sleep(2)
    except:
        pass

    # 3. 启动新 gateway — 用 hermes CLI
    hermes_bin = str(HERMES_HOME / "hermes-agent" / "venv" / "Scripts" / "hermes")
    if not Path(hermes_bin).exists():
        # 安装版 hermes
        hermes_bin = "hermes"

    subprocess.Popen(
        [hermes_bin, "gateway", "run"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW
    )

def wait_for_reconnect(timeout=45):
    """等待 gateway_state.json 更新为 connected"""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            data = json.loads(STATE_FILE.read_text())
            tg_state = data.get("platforms", {}).get("telegram", {}).get("state", "")
            if tg_state == "connected":
                return True
        except:
            pass
        time.sleep(3)
    return False

def run():
    state_data, tg = read_state()

    # ===== 情况 1: 状态文件都读不了 =====
    if state_data is None:
        print(f"🚨 {tg}")  # tg is the error message here
        print(f"🛠️ 自动修复中...预计 1 分钟")
        restart_gateway()
        return

    tg_state = tg.get("state", "unknown") if isinstance(tg, dict) else "unknown"
    pid = state_data.get("pid")

    # ===== 情况 2: Telegram 连着的 =====
    if tg_state == "connected" and is_process_alive(pid):
        # ✅ 一切正常 — 静默
        return

    # ===== 情况 3: 有问题 =====
    cause = diagnose_from_log()

    if not is_process_alive(pid) and pid:
        output = (
            f"🚨 [{now_str()}] 断联原因: Gateway 进程 (PID {pid}) 已退出\n"
            f"🛠️ [{now_str()}] 自动修复中...预计 1 分钟"
        )
    elif tg_state in ("disconnected", "error", "retrying"):
        output = (
            f"🚨 [{now_str()}] 断联原因: {cause}\n"
            f"🛠️ [{now_str()}] 自动修复中...预计 1 分钟"
        )
    elif tg_state == "connecting":
        # 还在连，等下一次
        return
    else:
        output = (
            f"🚨 [{now_str()}] 断联原因: Telegram 状态异常 ({tg_state})\n"
            f"🛠️ [{now_str()}] 自动修复中...预计 1 分钟"
        )

    print(output)

    # 执行修复
    restart_gateway()

    # 等待恢复
    if wait_for_reconnect():
        print(f"✅ [{now_str()}] 已修复，Telegram 重新连上了！")
    else:
        print(f"⚠️ [{now_str()}] 修复后仍未连接，等待下次 cron 再试")

if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        print(f"⚠️ Watchdog 自身异常: {e}", file=sys.stderr)