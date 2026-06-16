"""tools.py — Hermes Plugin tool handlers for system-monitor"""

import json
import os
import platform
import shutil
import time
import subprocess
from datetime import datetime, timedelta


def _get_boot_time():
    """Get boot time via ctypes (Windows compat) or /proc/uptime (Linux)"""
    try:
        if platform.system() == "Windows":
            import ctypes

            class SYSTEMTIME(ctypes.Structure):
                _fields_ = [
                    ("wYear", ctypes.c_uint16),
                    ("wMonth", ctypes.c_uint16),
                    ("wDayOfWeek", ctypes.c_uint16),
                    ("wDay", ctypes.c_uint16),
                    ("wHour", ctypes.c_uint16),
                    ("wMinute", ctypes.c_uint16),
                    ("wSecond", ctypes.c_uint16),
                    ("wMilliseconds", ctypes.c_uint16),
                ]

            class LASTBOOTINFO(ctypes.Structure):
                _fields_ = [("dwSize", ctypes.c_uint32), ("stBoot", SYSTEMTIME)]

            lib = ctypes.windll.kernel32
            buf = LASTBOOTINFO()
            buf.dwSize = ctypes.sizeof(LASTBOOTINFO)
            success = lib.GetSystemTimes(
                ctypes.byref(buf), None, None
            )  # GetTickCount64 is simpler
            tick_ms = lib.GetTickCount64()
            boot_time = datetime.now() - timedelta(milliseconds=tick_ms)
            return boot_time
        else:
            with open("/proc/uptime") as f:
                uptime_seconds = float(f.read().split()[0])
            return datetime.now() - timedelta(seconds=uptime_seconds)
    except Exception:
        return datetime.now() - timedelta(hours=1)


def handle_sys_info(params, **kwargs):
    """Handler for sys_info tool"""
    detail = params.get("detail", "basic")

    info = {
        "os": platform.system(),
        "os_version": platform.version(),
        "os_release": platform.release(),
        "hostname": platform.node(),
        "architecture": platform.machine(),
        "processor": platform.processor(),
        "python_version": platform.python_version(),
    }

    if detail == "full":
        import ctypes

        # RAM info via ctypes (Windows compatible)
        try:
            kernel32 = ctypes.windll.kernel32
            mem_status = ctypes.c_longlong(0)
            kernel32.GetPhysicallyInstalledSystemMemory(
                ctypes.byref(mem_status)
            )
            total_ram_kb = mem_status.value
            info["ram_total_gb"] = round(total_ram_kb / (1024 * 1024), 1)
        except Exception:
            info["ram_total_gb"] = "unknown"

        # Environment
        info["cwd"] = os.getcwd()
        info["home"] = os.path.expanduser("~")
        info["cpu_count"] = os.cpu_count()

    return json.dumps({"success": True, "data": info})


def handle_disk_usage(params, **kwargs):
    """Handler for sys_disk_usage tool"""
    path = params.get("path", None)

    disks = []
    if platform.system() == "Windows":
        import string
        from ctypes import windll

        drives = []
        bitmask = windll.kernel32.GetLogicalDrives()
        for letter in string.ascii_uppercase:
            if bitmask & 1:
                drives.append(f"{letter}:\\")
            bitmask >>= 1

        if path:
            # Check specific path
            path = path.rstrip("\\")
            try:
                usage = shutil.disk_usage(path)
                disks.append(
                    {
                        "path": path,
                        "total_gb": round(usage.total / (1024**3), 1),
                        "used_gb": round(usage.used / (1024**3), 1),
                        "free_gb": round(usage.free / (1024**3), 1),
                        "used_pct": round(usage.used / usage.total * 100, 1),
                    }
                )
            except Exception:
                pass
        else:
            for drive in drives:
                try:
                    usage = shutil.disk_usage(drive)
                    disks.append(
                        {
                            "path": drive,
                            "total_gb": round(usage.total / (1024**3), 1),
                            "used_gb": round(usage.used / (1024**3), 1),
                            "free_gb": round(usage.free / (1024**3), 1),
                            "used_pct": round(usage.used / usage.total * 100, 1),
                        }
                    )
                except Exception:
                    pass
    else:
        target = path or "/"
        usage = shutil.disk_usage(target)
        disks.append(
            {
                "path": target,
                "total_gb": round(usage.total / (1024**3), 1),
                "used_gb": round(usage.used / (1024**3), 1),
                "free_gb": round(usage.free / (1024**3), 1),
                "used_pct": round(usage.used / usage.total * 100, 1),
            }
        )

    return json.dumps({"success": True, "disks": disks})


def handle_uptime(params, **kwargs):
    """Handler for sys_uptime tool"""
    output_format = params.get("format", "human")

    boot_time = _get_boot_time()
    uptime = datetime.now() - boot_time

    if output_format == "seconds":
        return json.dumps({"success": True, "uptime_seconds": uptime.total_seconds()})
    elif output_format == "dict":
        return json.dumps(
            {
                "success": True,
                "data": {
                    "days": uptime.days,
                    "hours": uptime.seconds // 3600,
                    "minutes": (uptime.seconds % 3600) // 60,
                    "seconds": uptime.seconds % 60,
                    "total_seconds": uptime.total_seconds(),
                },
            }
        )
    else:
        # human readable
        d = uptime.days
        h, rem = divmod(uptime.seconds, 3600)
        m, s = divmod(rem, 60)
        parts = []
        if d > 0:
            parts.append(f"{d}d")
        if h > 0:
            parts.append(f"{h}h")
        if m > 0:
            parts.append(f"{m}m")
        parts.append(f"{s}s")
        human = " ".join(parts)

        return json.dumps(
            {
                "success": True,
                "uptime": human,
                "boot_time": boot_time.strftime("%Y-%m-%d %H:%M:%S"),
            }
        )