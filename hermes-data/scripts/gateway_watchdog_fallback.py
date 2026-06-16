#!/usr/bin/env python
"""
Gateway 看门狗回退脚本 — Windows 计划任务版
===========================================
不依赖 Hermes cron 调度器。由 Windows Task Scheduler 每 3 分钟触发。
检测逻辑：
1. 读 gateway_state.json 中的 PID
2. 用 tasklist 确认该 PID 真的活着
3. 如果死了 → 重启 gateway
4. 如果重启失败 → 写日志到桌面失败标记

安装方法：
  python gateway_watchdog_fallback.py --install

卸载方法：
  python gateway_watchdog_fallback.py --uninstall
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# 路径配置
HERMES_HOME = Path.home() / "AppData" / "Local" / "hermes"
STATE_FILE = HERMES_HOME / "gateway_state.json"
HERMES_VENV = HERMES_HOME / "hermes-agent" / "venv" / "Scripts" / "hermes"
HERMES_PYTHON = HERMES_HOME / "hermes-agent" / "venv" / "Scripts" / "python.exe"
GATEWAY_MAIN = HERMES_HOME / "hermes-agent" / "hermes_cli" / "main.py"
LOG_DIR = HERMES_HOME / "logs"
FALLBACK_LOG = LOG_DIR / "gateway_fallback.log"
INCUBATOR_FILE = HERMES_HOME / "scripts" / ".watchdog_incubator.json"

LOG_DIR.mkdir(parents=True, exist_ok=True)


def log(msg: str) -> None:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"{ts} | {msg}"
    print(line)
    try:
        with open(FALLBACK_LOG, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass


def read_state() -> dict | None:
    if not STATE_FILE.exists():
        return None
    try:
        raw = STATE_FILE.read_text(encoding="utf-8")
        return json.loads(raw)
    except (json.JSONDecodeError, OSError):
        return None


def write_state(pid: int) -> None:
    """更新 gateway_state.json 的 PID（仅当 gateway 被看门狗重启时）"""
    state = read_state() or {}
    state["pid"] = pid
    state["gateway_state"] = "starting"
    state["restarted_by_watchdog"] = True
    try:
        STATE_FILE.write_text(
            json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8"
        )
    except OSError:
        pass


def is_pid_alive(pid: int) -> bool:
    """检查 PID 是否真实存在"""
    try:
        r = subprocess.run(
            ["tasklist", "/FI", f"PID eq {pid}", "/NH"],
            capture_output=True, text=True, timeout=10,
        )
        return str(pid) in r.stdout
    except (subprocess.TimeoutExpired, OSError):
        return True  # 无法判断时假定活着（避免误杀）


def find_existing_gateway() -> list[int]:
    """找所有已运行的 gateway 进程 PID"""
    try:
        r = subprocess.run(
            ["tasklist", "/FO", "CSV", "/NH"],
            capture_output=True, text=True, timeout=10,
        )
        pids = []
        for line in r.stdout.split("\n"):
            if "gateway" in line.lower() or "main.py" in line.lower():
                parts = line.split(",")
                if len(parts) >= 2:
                    pid = parts[1].strip().strip('"')
                    if pid.isdigit():
                        pids.append(int(pid))
        return pids
    except (subprocess.TimeoutExpired, OSError):
        return []


def restart_gateway() -> bool:
    """启动 gateway（杀掉旧进程后启动新进程）"""
    # 杀旧的
    existing = find_existing_gateway()
    for pid in existing:
        log(f"  杀旧进程 PID {pid}")
        subprocess.run(
            ["taskkill", "/f", "/pid", str(pid)],
            capture_output=True, timeout=5,
        )

    time.sleep(2)

    # 启动新的
    hermes_path = str(HERMES_VENV)
    log(f"  启动 gateway: {hermes_path}")
    try:
        proc = subprocess.Popen(
            [hermes_path, "gateway", "run"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        # 更新 state 文件中的 PID
        write_state(proc.pid)
        log(f"  → PID {proc.pid}")
        return True
    except OSError as e:
        log(f"  ❌ 启动失败: {e}")
        return False


def check_network() -> bool:
    """快速网络连通检查"""
    try:
        r = subprocess.run(
            ["ping", "-n", "1", "-w", "3000", "baidu.com"],
            capture_output=True, text=True, timeout=10,
        )
        return r.returncode == 0
    except (subprocess.TimeoutExpired, OSError):
        return False


def install_task() -> bool:
    """安装 Windows 计划任务"""
    script_path = Path(__file__).resolve()
    task_name = "HermesGatewayFallbackWatchdog"
    xml = f"""<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.4" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>Hermes Gateway 回退看门狗 — 不依赖 Hermes cron</Description>
  </RegistrationInfo>
  <Triggers>
    <BootTrigger>
      <Enabled>true</Enabled>
    </BootTrigger>
    <TimeTrigger>
      <Repetition>
        <Interval>PT3M</Interval>
        <Duration>P1D</Duration>
        <StopAtDurationEnd>false</StopAtDurationEnd>
      </Repetition>
      <StartBoundary>{datetime.now().strftime("%Y-%m-%dT%H:%M:%S")}</StartBoundary>
      <Enabled>true</Enabled>
    </TimeTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <UserId>{os.environ.get("USERDOMAIN", ".")}\\{os.environ.get("USERNAME", "Admin")}</UserId>
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>LeastPrivilege</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <Enabled>true</Enabled>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <RestartOnFailure>
      <Interval>PT1M</Interval>
      <Count>3</Count>
    </RestartOnFailure>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>python</Command>
      <Arguments>"{script_path}"</Arguments>
      <WorkingDirectory>{script_path.parent}</WorkingDirectory>
    </Exec>
  </Actions>
</Task>"""

    task_file = HERMES_HOME / "scripts" / "hermes_watchdog_task.xml"
    try:
        task_file.write_text(xml, encoding="utf-16")
    except OSError as e:
        log(f"❌ 无法写入任务文件: {e}")
        return False

    log(f"📝 任务文件已写入: {task_file}")

    # 注册任务
    r = subprocess.run(
        ["schtasks", "/Create", "/XML", str(task_file), "/TN", task_name, "/F"],
        capture_output=True, timeout=15,
    )
    err = r.stderr.decode("gbk", errors="replace").strip() if r.stderr else ""
    if r.returncode == 0:
        log(f"✅ 计划任务注册成功: {task_name}")
        log(f"   每 3 分钟自动检查，开机自动启动")
        return True
    else:
        log(f"❌ 计划任务注册失败: {err}")
        return False


def uninstall_task() -> bool:
    task_name = "HermesGatewayFallbackWatchdog"
    r = subprocess.run(
        ["schtasks", "/Delete", "/TN", task_name, "/F"],
        capture_output=True, timeout=10,
    )
    err = r.stderr.decode("gbk", errors="replace").strip() if r.stderr else ""
    if r.returncode == 0:
        log(f"✅ 已卸载计划任务: {task_name}")
        return True
    else:
        log(f"⚠️ 卸载失败（可能没有该任务）: {err}")
        return False


def main() -> int:
    # 处理 --install / --uninstall
    if "--install" in sys.argv:
        return 0 if install_task() else 1
    if "--uninstall" in sys.argv:
        return 0 if uninstall_task() else 1

    # === 正常检查逻辑 ===
    state = read_state()

    if not state:
        log("⚠️ gateway_state.json 不存在 → 启动 gateway")
        restart_gateway()
        return 0

    pid = state.get("pid")
    gateway_state = state.get("gateway_state", "unknown")

    if not pid:
        log(f"⚠️ state 文件中无 PID（state={gateway_state}）→ 启动 gateway")
        restart_gateway()
        return 0

    # 确认 PID 活着
    if is_pid_alive(pid):
        # 一切正常 → 静默退出
        return 0

    # PID 死了！
    platforms = state.get("platforms", {})
    plat_summary = ", ".join(
        f"{p}: {s.get('state', '?')}" for p, s in platforms.items()
    )
    log(f"🚨 Gateway PID {pid} 已死亡！")
    log(f"   最后状态: {plat_summary}")

    # 网络检查
    net_ok = check_network()
    if not net_ok:
        log("   网络不通 — 跳过重启，等网络恢复后再试")
        # 但还是要尝试，因为可能是代理问题
        log("   仍尝试重启...")

    ok = restart_gateway()
    if ok:
        log("✅ Gateway 已通过回退看门狗重启")
    else:
        log("❌ 重启失败！")

    return 0


if __name__ == "__main__":
    sys.exit(main())