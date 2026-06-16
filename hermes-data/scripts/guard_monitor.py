#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""美团卫士 v3 — 纯Python版（no_agent模式）
去除bash→PowerShell桥梁，直接在Python内做所有检测。
exit 0 = 无警报（安静），exit 0 + stdout = 有警报，exit非0 = 错误"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# ── 常量 ─────────────────────────────────────────────
STATE_DIR = Path(os.environ.get("LOCALAPPDATA", "C:\\Users\\Admin\\AppData\\Local")) / "hermes" / "memories" / "scripts_cache"
STATE_FILE = STATE_DIR / "guard_state.json"
MAX_RECORDS = 50

# ── 状态管理 ──────────────────────────────────────────
def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {
        "armed": False,
        "lastBoot": "",
        "knownSessions": [],
        "notifiedBoot": False,
        "notifiedSessions": [],
        "notifiedUnlocks": [],
        "notifiedUSB": [],
        "notifiedRemoteDesktop": [],
        "notifiedWake": [],
        "notifiedRemoteSoftware": False,
        "remoteSoftwareDetected": False,
        "version": 3,
    }

def save_state(state: dict) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    for key in ["notifiedSessions", "notifiedUnlocks", "notifiedUSB", "notifiedRemoteDesktop", "notifiedWake"]:
        if len(state.get(key, [])) > MAX_RECORDS:
            state[key] = state[key][-MAX_RECORDS:]
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")

# ── PowerShell命令调用（返回stdout文本）───────────────
def ps(cmd: str) -> str:
    """运行PowerShell命令，返回stdout"""
    try:
        r = subprocess.run(
            ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", cmd],
            capture_output=True, text=True, timeout=15, errors="replace",
            creationflags=0x08000000  # CREATE_NO_WINDOW — 不让黑窗弹出
        )
        return r.stdout.strip()
    except Exception as e:
        return f""

def ps_json(cmd: str) -> list | dict | None:
    """运行PowerShell命令并解析JSON输出"""
    raw = ps(cmd)
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None

# ── 检测模块 ──────────────────────────────────────────
def detect_reboot(state: dict, output: list) -> None:
    """1. 系统重启检测"""
    boot_str = ps("(Get-CimInstance Win32_OperatingSystem).LastBootUpTime | ForEach-Object { $_.ToString('yyyy-MM-dd HH:mm:ss') }")
    if not boot_str:
        return
    if state.get("lastBoot") and state["lastBoot"] != boot_str and not state.get("notifiedBoot"):
        output.append(f"⚠️ 电脑卫士｜系统重启")
        output.append(f"上次启动: {state['lastBoot']}")
        output.append(f"本次启动: {boot_str}")
        output.append(f"你还没说『我回来了』——请确认是你本人操作")
        state["notifiedBoot"] = True
    state["lastBoot"] = boot_str

def detect_new_logons(state: dict, output: list) -> None:
    """2. 新登录检测"""
    sessions = ps_json(
        "Get-CimInstance Win32_LogonSession -Filter \"LogonType=2 OR LogonType=10\" | "
        "Where-Object { $_.UserName -and $_.UserName -ne '' -and $_.UserName -notlike 'DWM-*' -and $_.UserName -notlike 'UMFD-*' } | "
        "Select-Object UserName, @{N='StartStr';E={$_.StartTime.ToString('yyyy-MM-dd HH:mm:ss')}} | ConvertTo-Json -Compress"
    )
    if not sessions:
        return
    if isinstance(sessions, dict):
        sessions = [sessions]
    current_keys = []
    for s in sessions:
        user = s.get("UserName", "")
        start = s.get("StartStr", "")
        key = f"{user}|{start}"
        current_keys.append(key)
        if key not in state.get("knownSessions", []) and key not in state.get("notifiedSessions", []):
            output.append(f"⚠️ 电脑卫士｜新用户登录")
            output.append(f"用户: {user} 时间: {start}")
            state.setdefault("notifiedSessions", []).append(key)
    state["knownSessions"] = list(set(state.get("knownSessions", []) + current_keys))

def detect_unlock(state: dict, output: list) -> None:
    """3. 屏幕解锁检测（事件4801）"""
    unlocks = ps_json(
        "Get-WinEvent -FilterHashtable @{LogName='Security'; ID=4801} -MaxEvents 5 -ErrorAction SilentlyContinue | "
        "Select-Object @{N='Time';E={$_.TimeCreated.ToString('yyyy-MM-dd HH:mm:ss')}} | ConvertTo-Json -Compress"
    )
    if not unlocks:
        return
    if isinstance(unlocks, dict):
        unlocks = [unlocks]
    for u in unlocks:
        t = u.get("Time", "")
        key = f"unlock|{t}"
        if key not in state.get("notifiedUnlocks", []):
            output.append(f"⚠️ 电脑卫士｜屏幕被唤醒解锁")
            output.append(f"时间: {t} —— 有人操作了电脑")
            state.setdefault("notifiedUnlocks", []).append(key)

def detect_usb(state: dict, output: list) -> None:
    """4. USB存储设备检测"""
    usb_json = ps_json(
        "Get-ChildItem 'HKLM:\\SYSTEM\\CurrentControlSet\\Enum\\USBSTOR' -ErrorAction SilentlyContinue | "
        "ForEach-Object { $dev = $_.PSChildName; Get-ChildItem \"HKLM:\\SYSTEM\\CurrentControlSet\\Enum\\USBSTOR\\$dev\" -ErrorAction SilentlyContinue | "
        "ForEach-Object { $ser = $_.PSChildName; $friendly = (Get-ItemProperty \"HKLM:\\SYSTEM\\CurrentControlSet\\Enum\\USBSTOR\\$dev\\$ser\" -Name FriendlyName -ErrorAction SilentlyContinue).FriendlyName; "
        "[PSCustomObject]@{Device=$dev; Serial=$ser; Friendly=$friendly} } } | ConvertTo-Json -Compress"
    )
    if not usb_json:
        return
    if isinstance(usb_json, dict):
        usb_json = [usb_json]
    for d in usb_json:
        dev = d.get("Device", "")
        serial = d.get("Serial", "")
        friendly = d.get("Friendly", "")
        key = f"usb|{dev}|{serial}"
        if key not in state.get("notifiedUSB", []):
            output.append(f"⚠️ 电脑卫士｜USB存储设备接入")
            output.append(f"设备: {friendly or dev}")
            output.append(f"序列号: {serial}")
            state.setdefault("notifiedUSB", []).append(key)

def detect_rdp(state: dict, output: list) -> None:
    """5. 远程桌面连接检测"""
    rdp_enabled = ps_json(
        "$v = (Get-ItemProperty 'HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Terminal Server' -Name fDenyTSConnections -ErrorAction SilentlyContinue).fDenyTSConnections; $v | ConvertTo-Json"
    )
    if rdp_enabled == 0:
        rdp_sessions = ps_json(
            "Get-CimInstance Win32_TerminalServiceSession -ErrorAction SilentlyContinue | "
            "Where-Object { $_.UserName -and $_.UserName -ne '' -and $_.SessionId -gt 0 } | "
            "Select-Object UserName, SessionId | ConvertTo-Json -Compress"
        )
        if rdp_sessions:
            if isinstance(rdp_sessions, dict):
                rdp_sessions = [rdp_sessions]
            for rs in rdp_sessions:
                user = rs.get("UserName", "")
                sid = rs.get("SessionId", "")
                key = f"rdp|{user}|{sid}"
                if key not in state.get("notifiedRemoteDesktop", []):
                    output.append(f"⚠️ 电脑卫士｜远程桌面活动连接")
                    output.append(f"用户: {user} 会话ID: {sid}")
                    state.setdefault("notifiedRemoteDesktop", []).append(key)

def detect_remote_software(state: dict, output: list) -> None:
    """6. 远程协助软件检测"""
    remote_names = ["mstsc", "TeamViewer", "AnyDesk", "VNC", "TightVNC", "todesk", "SunLoginClient", "向日葵", "RDPClip"]
    try:
        r = subprocess.run(
            ["powershell.exe", "-NoProfile", "-Command",
             "Get-Process | Select-Object -ExpandProperty ProcessName | ConvertTo-Json -Compress"],
            capture_output=True, text=True, timeout=10, errors="replace",
            creationflags=0x08000000  # CREATE_NO_WINDOW
        )
        procs = json.loads(r.stdout.strip()) if r.stdout.strip() else []
        if isinstance(procs, str):
            procs = [procs]
    except Exception:
        procs = []

    found = any(any(rn.lower() in p.lower() for rn in remote_names) for p in procs)
    if found:
        state["remoteSoftwareDetected"] = True
        if not state.get("notifiedRemoteSoftware"):
            output.append(f"⚠️ 电脑卫士｜检测到远程控制软件正在运行")
            state["notifiedRemoteSoftware"] = True
    else:
        state["remoteSoftwareDetected"] = False

def detect_wake(state: dict, output: list) -> None:
    """7. 唤醒来源检测"""
    wake_events = ps_json(
        "Get-WinEvent -FilterHashtable @{LogName='System'; ID=1,42,107} -MaxEvents 3 -ErrorAction SilentlyContinue | "
        "Select-Object Id, @{N='Time';E={$_.TimeCreated.ToString('yyyy-MM-dd HH:mm:ss')}}, Message | ConvertTo-Json -Compress"
    )
    if not wake_events:
        return
    if isinstance(wake_events, dict):
        wake_events = [wake_events]
    for w in wake_events:
        t = w.get("Time", "")
        key = f"wake|{t}"
        if key in state.get("notifiedWake", []):
            continue
        msg = w.get("Message", "")
        source = "未知"
        for line in msg.split("\n"):
            line = line.strip()
            if "Wake Source" in line or "来源" in line or "Source" in line:
                parts = line.split(":", 1)
                if len(parts) > 1:
                    source = parts[1].strip()
        output.append(f"⚠️ 电脑卫士｜系统从睡眠唤醒")
        output.append(f"时间: {t}  来源: {source}")
        state.setdefault("notifiedWake", []).append(key)


# ── 主流程 ──────────────────────────────────────────
def main() -> int:
    state = load_state()

    # 没布防就安静退出
    if not state.get("armed", False):
        save_state(state)
        return 0

    output: list[str] = []

    detect_reboot(state, output)
    detect_new_logons(state, output)
    detect_unlock(state, output)
    detect_usb(state, output)
    detect_rdp(state, output)
    detect_remote_software(state, output)
    detect_wake(state, output)

    save_state(state)

    if output:
        sys.stdout.write("\n".join(output))
    return 0


if __name__ == "__main__":
    sys.exit(main())