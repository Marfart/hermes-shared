#!/usr/bin/env python3
"""
进程看门狗 — 杀掉2小时内无CPU活动的空闲进程
使用 Windows API (CreateToolhelp32Snapshot) 枚举进程，不依赖外部命令
"""
import json, os, subprocess, sys, time, ctypes
from ctypes import wintypes
from pathlib import Path
from datetime import datetime

# ── 配置 ──
HERMES_HOME = Path(os.environ.get("HERMES_HOME",
                   str(Path.home() / "AppData" / "Local" / "hermes")))
STATE_FILE = HERMES_HOME / "memories" / "脚本缓存" / "系统维护" / "idle_killer_state.json"
STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
IDLE_MINUTES = 120
CHECK_INTERVAL = 5  # cron 每5分钟

# 白名单（小写）
PROTECTED = {
    "system", "idle process", "system idle process",
    "smss.exe", "csrss.exe", "wininit.exe",
    "winlogon.exe", "services.exe", "lsass.exe", "svchost.exe",
    "fontdrvhost.exe", "spoolsv.exe", "dwm.exe", "conhost.exe",
    "sihost.exe", "taskhostw.exe", "runtimebroker.exe", "ctfmon.exe",
    "securityhealthsystray.exe", "securityhealthservice.exe",
    "widgets.exe", "widgetservice.exe",
    "explorer.exe", "taskmgr.exe", "cmd.exe",
    "powershell.exe", "windowsterminal.exe",
    "chrome.exe", "msedge.exe", "firefox.exe",
    "wechat.exe", "wechat",
    "dingtalk.exe",
    "cloudmusic.exe",
    "code.exe", "obsidian.exe",
    "sublime_text.exe", "notepad++.exe",
    "teamviewer.exe", "sunloginclient.exe",
    "python.exe",
    "bash.exe",
    "hermes.exe", "codex.exe",
    "winword.exe", "excel.exe", "powerpnt.exe",
    "wps.exe", "wps",
    "acrobat.exe", "acrord32.exe",
    "tasklist.exe", "wmic.exe",
    "mmc.exe", "regedit.exe",
    "openvpn.exe",
}

def log(msg):
    print(f"[{datetime.now():%H:%M:%S}] {msg}")

# ── Windows API 遍历进程 ──
TH32CS_SNAPPROCESS = 0x00000002

class PROCESSENTRY32(ctypes.Structure):
    _fields_ = [
        ("dwSize", wintypes.DWORD),
        ("cntUsage", wintypes.DWORD),
        ("th32ProcessID", wintypes.DWORD),
        ("th32DefaultHeapID", ctypes.POINTER(ctypes.c_ulong)),
        ("th32ModuleID", wintypes.DWORD),
        ("cntThreads", wintypes.DWORD),
        ("th32ParentProcessID", wintypes.DWORD),
        ("pcPriClassBase", ctypes.c_long),
        ("dwFlags", wintypes.DWORD),
        ("szExeFile", ctypes.c_char * 260),
    ]

kernel32 = ctypes.windll.kernel32

def get_process_list():
    """用 CreateToolhelp32Snapshot 获取所有进程 PID + 名称"""
    procs = []
    snapshot = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    if snapshot == -1:
        return procs
    try:
        pe = PROCESSENTRY32()
        pe.dwSize = ctypes.sizeof(PROCESSENTRY32)
        if kernel32.Process32First(snapshot, ctypes.byref(pe)):
            while True:
                name = pe.szExeFile.decode("utf-8", errors="replace").lower()
                if name:
                    procs.append((pe.th32ProcessID, name))
                if not kernel32.Process32Next(snapshot, ctypes.byref(pe)):
                    break
    finally:
        kernel32.CloseHandle(snapshot)
    return procs

def get_foreground_pid():
    try:
        user32 = ctypes.windll.user32
        hwnd = user32.GetForegroundWindow()
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        return pid.value
    except:
        return None

def main():
    dry_run = "--dry-run" in sys.argv or "-n" in sys.argv
    if "--reset" in sys.argv:
        STATE_FILE.unlink(missing_ok=True)
        log("✅ 状态已重置")
        return

    state = {}
    if STATE_FILE.exists():
        try:
            state = json.loads(STATE_FILE.read_text("utf-8"))
        except:
            state = {}

    procs = get_process_list()
    fg_pid = get_foreground_pid()
    if not procs:
        log("⚠️ 获取进程列表失败")
        return

    now = int(time.time())
    killed = []
    updated = {}

    for pid, name in procs:
        key = f"{pid}_{name}"

        # 保护检查
        if name in PROTECTED or pid == fg_pid:
            updated[key] = {"ts": now, "idle": 0}
            continue

        if key in state:
            prev = state[key]
            idle = prev.get("idle", 0)
            idle += CHECK_INTERVAL

            if idle >= IDLE_MINUTES:
                try:
                    if not dry_run:
                        subprocess.run(
                            ['taskkill', '/F', '/PID', str(pid)],
                            capture_output=True, timeout=10
                        )
                    log(f"{'🔪 [预览]' if dry_run else '🔪 已杀'} {name} (PID:{pid}) 空闲{idle}分钟")
                    killed.append((name, pid, idle))
                except Exception as e:
                    log(f"⚠️ 杀 {name} 失败: {e}")
                continue

            updated[key] = {"ts": now, "idle": idle}
        else:
            # 新进程从1分钟开始累积（减少误杀）
            updated[key] = {"ts": now, "idle": CHECK_INTERVAL}

    # 清理已结束的进程
    active_keys = {f"{pid}_{name}" for pid, name in procs}
    for k in list(state):
        if k not in active_keys:
            del state[k]

    state.update(updated)
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), "utf-8")

    if not killed:
        log("✅ 无空闲进程")

if __name__ == "__main__":
    main()