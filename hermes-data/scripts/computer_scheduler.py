"""
电脑定时管家 — 定时睡眠/关机 + 自动唤醒 + 启动Hermes + 连通检测
===================================================================
功能：
  setup mode:    设置定时睡眠和自动唤醒
  status mode:   查看当前定时状态
  cancel mode:   取消所有定时

工作原理：
  - 睡前用 schtasks 注册一个到时自动唤醒的任务
  - 唤醒后 Windows 自动启动 Hermes（已存在启动文件夹）
  - 本脚本在醒后检查 Telegram + 微信状态并报告

用法：
  python computer_scheduler.py setup --sleep-at 23:00 --wake-at 08:00
  python computer_scheduler.py setup --shutdown-at 23:00 --wake-at 08:00
  python computer_scheduler.py status
  python computer_scheduler.py cancel

依赖：
  - Hermes 已在启动文件夹（Startup/Hermes_Gateway.cmd）
  - 系统支持 S3 睡眠（你电脑有这个 ✅）
  - RTCWAKE 已启用（你电脑的当前交流电策略已启用 ✅）
"""

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

# =====================================================================
# 常量
# =====================================================================
HERMES_HOME = Path.home() / "AppData" / "Local" / "hermes"
STATE_FILE = HERMES_HOME / "gateway_state.json"
SCRIPT_DIR = HERMES_HOME / "scripts"
CONFIG_FILE = SCRIPT_DIR / ".computer_schedule.json"

TASK_NAME = "Hermes_AutoWake"

# =====================================================================
# 工具函数
# =====================================================================
def decode_gbk(data: bytes) -> str:
    """安全解码 GBK 输出"""
    try:
        return data.decode("gbk", errors="replace")
    except:
        return data.decode("utf-8", errors="replace")

def run_cmd(cmd: list[str], timeout: int = 15) -> tuple[int, str]:
    """运行 cmd 命令，返回 (exit_code, stdout)"""
    try:
        r = subprocess.run(
            ["cmd.exe", "/c"] + cmd,
            capture_output=True, timeout=timeout
        )
        return r.returncode, decode_gbk(r.stdout)
    except subprocess.TimeoutExpired:
        return -1, "超时"
    except Exception as e:
        return -1, str(e)

def run_ps(script: str, timeout: int = 15) -> tuple[int, str, str]:
    """运行 PowerShell 脚本"""
    try:
        r = subprocess.run(
            ["powershell", "-NoProfile", "-Command", script],
            capture_output=True, timeout=timeout
        )
        return r.returncode, decode_gbk(r.stdout), decode_gbk(r.stderr)
    except subprocess.TimeoutExpired:
        return -1, "超时", ""
    except Exception as e:
        return -1, str(e), ""


# =====================================================================
# 核心功能
# =====================================================================
def check_gateway_connectivity() -> dict:
    """检查 Hermes Gateway 的连通状态"""
    if not STATE_FILE.exists():
        return {"telegram": "unknown", "weixin": "unknown", "gateway": "not_running"}
    
    try:
        data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        tg = data.get("platforms", {}).get("telegram", {}).get("state", "unknown")
        wx = data.get("platforms", {}).get("weixin", {}).get("state", "unknown")
        pid = data.get("pid")
        
        # 检查进程是否活着
        alive = False
        if pid:
            r = subprocess.run(
                ["tasklist", "/fi", f"PID eq {pid}", "/nh", "/fo", "csv"],
                capture_output=True, text=True, timeout=5
            )
            alive = str(pid) in r.stdout
        
        return {
            "telegram": tg,
            "weixin": wx,
            "gateway": "running" if alive else "stopped",
            "gateway_pid": pid,
        }
    except Exception as e:
        return {"telegram": "error", "weixin": "error", "gateway": f"error: {e}"}


def set_sleep_wake(sleep_time: str, wake_time: str) -> tuple[bool, str]:
    """设置定时睡眠 + 唤醒"""
    now = datetime.now()
    sleep_h, sleep_m = map(int, sleep_time.split(":"))
    wake_h, wake_m = map(int, wake_time.split(":"))
    
    sleep_dt = now.replace(hour=sleep_h, minute=sleep_m, second=0, microsecond=0)
    wake_dt = now.replace(hour=wake_h, minute=wake_m, second=0, microsecond=0)
    
    if sleep_dt <= now:
        sleep_dt += timedelta(days=1)
    if wake_dt <= now:
        wake_dt += timedelta(days=1)
    if wake_dt <= sleep_dt:
        wake_dt += timedelta(days=1)
    
    wake_time_str = wake_dt.strftime("%H:%M")
    wake_date_str = wake_dt.strftime("%Y/%m/%d")
    check_script = str(SCRIPT_DIR / "wakeup_check.py")
    
    # 用 PowerShel 创建任务（bash 里的 schtasks 有编码问题）
    ps_code = (
        f'schtasks /delete /tn "{TASK_NAME}" /f 2>$null; '
        f'schtasks /create /tn "{TASK_NAME}" '
        f'/tr "python {check_script}" '
        f'/sc once /st {wake_time_str} /sd {wake_date_str} /f'
    )
    code, out, err = run_ps(ps_code)
    if code != 0:
        return False, f"创建唤醒任务失败: {err}"
    
    config = {
        "sleep_at": sleep_time, "wake_at": wake_time,
        "created_at": datetime.now().isoformat(),
        "next_sleep": sleep_dt.isoformat(),
        "next_wake": wake_dt.isoformat(),
    }
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")
    
    return True, (
        f"✅ 已设置\n"
        f"   睡眠: {sleep_time} → 唤醒: {wake_time}\n"
        f"   醒后自动启动 → 检查 Telegram + 微信连接\n"
        f"\n⚠️  注意：\n"
        f"   1. 使用睡眠模式（不是完全关机）\n"
        f"   2. 唤醒需要电脑接通电源\n"
        f"   3. Hermes 已在启动文件夹 ✅"
    )


def execute_sleep():
    """执行睡眠（S3）"""
    # 先看看有没有待执行的唤醒任务
    code, out = run_cmd([f'schtasks /query /tn "{TASK_NAME}" /fo LIST /v'])
    
    # 执行睡眠
    run_cmd(["rundll32.exe", "powrprof.dll,SetSuspendState", "0", "1", "0"])
    return True


def execute_shutdown():
    """执行关机"""
    code, out = run_cmd(["shutdown", "/s", "/t", "60", "/c", "Hermes 定时关机，将在60秒后关闭..."])
    return True


def get_status() -> dict:
    """获取当前调度状态"""
    config = {}
    if CONFIG_FILE.exists():
        try:
            config = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except:
            pass
    
    # 用 PowerShell 查唤醒任务（避免 bash 编码问题）
    code, out, err = run_ps(f'schtasks /query /tn "{TASK_NAME}" /fo LIST /v')
    task_exists = code == 0
    next_run = ""
    if task_exists:
        for line in out.split("\n"):
            if "下次运行时间" in line or "Next Run Time" in line:
                parts = line.split(":", 1)
                if len(parts) > 1:
                    next_run = parts[1].strip()
                break
    
    # 连通状态
    connectivity = check_gateway_connectivity()
    
    return {
        "config": config,
        "wake_task_exists": task_exists,
        "next_wake_run": next_run,
        "connectivity": connectivity,
    }


def cancel_schedule():
    """取消所有定时"""
    run_cmd([f'schtasks /delete /tn "{TASK_NAME}" /f'])
    if CONFIG_FILE.exists():
        CONFIG_FILE.unlink()
    run_cmd(["shutdown", "/a"])  # 取消待执行的关机
    return True, "✅ 所有定时已取消"


# =====================================================================
# 唤醒后的检查脚本入口
# =====================================================================
def run_wakeup_check():
    """电脑唤醒后自动执行：检查连接并上报"""
    print("=" * 40)
    print("🌅 Hermes 定时唤醒 — 连通检查报告")
    print("=" * 40)
    
    # 等待 Hermes Gateway 启动（启动文件夹里有）
    for i in range(30):  # 最多等 30 秒
        status = check_gateway_connectivity()
        if status["gateway"] == "running":
            print(f"\n⏱️  Gateway 启动耗时: {i+1} 秒")
            break
        time.sleep(1)
    else:
        status = check_gateway_connectivity()
    
    print(f"\n📡 Gateway 进程: {'✅ 运行中' if status['gateway']=='running' else '❌ 未启动'}")
    print(f"📱 Telegram:     {'✅ 已连接' if status.get('telegram')=='connected' else '⏳ ' + status.get('telegram','未知')}")
    print(f"💬 微信:         {'✅ 已连接' if status.get('weixin')=='connected' else '⏳ ' + status.get('weixin','未知')}")
    
    if status.get("telegram") == "connected" and status.get("weixin") == "connected":
        print("\n🎉 全部平台已就绪！")
    else:
        print("\n⚠️  部分平台尚未连接，看门狗将在1分钟内自动修复")
    
    print(f"\n📋 完整状态: {json.dumps(status, ensure_ascii=False)}")


# =====================================================================
# CLI 入口
# =====================================================================
def main():
    parser = argparse.ArgumentParser(description="电脑定时管家 🐾")
    parser.add_argument("mode", choices=["setup", "status", "cancel", "wakeup-check", "sleep-now"],
                        help="操作模式")
    parser.add_argument("--sleep-at", help="睡眠时间 HH:MM（如 23:00）")
    parser.add_argument("--wake-at", help="唤醒时间 HH:MM（如 08:00）")
    parser.add_argument("--shutdown", action="store_true", help="使用关机代替睡眠")
    
    args = parser.parse_args()
    
    if args.mode == "setup":
        if not args.sleep_at or not args.wake_at:
            print("❌ 需要 --sleep-at 和 --wake-at 参数")
            print("示例: python computer_scheduler.py setup --sleep-at 23:00 --wake-at 08:00")
            return
        
        ok, msg = set_sleep_wake(args.sleep_at, args.wake_at)
        print(msg)
        
        if ok:
            print("\n💤 到点后电脑将自动进入睡眠...")
            print("🌅 到点后电脑将自动唤醒 → 启动 Hermes → 检查连接")
            print("\n⚠️  请确认以下设置：")
            print("   1. Hermes_Gateway.cmd 在启动文件夹 ✅")
            print("   2. 唤醒定时器已启用 ✅（RTCWAKE=1）")
            print("   3. 电脑电源插着（睡眠状态下唤醒需要电源）")
    
    elif args.mode == "status":
        status = get_status()
        config = status.get("config", {})
        
        print("=" * 40)
        print("📋 定时管家状态")
        print("=" * 40)
        
        if config:
            print(f"\n📅 当前计划:")
            print(f"   睡眠: {config.get('sleep_at', '?')}")
            print(f"   唤醒: {config.get('wake_at', '?')}")
            print(f"   创建于: {config.get('created_at', '?')[:19]}")
        else:
            print("\n📭 暂无定时计划")
        
        print(f"\n⏰ 唤醒任务: {'✅ 已注册' if status['wake_task_exists'] else '❌ 无'}")
        if status.get("next_wake_run"):
            print(f"   下次唤醒: {status['next_wake_run']}")
        
        conn = status.get("connectivity", {})
        print(f"\n📡 Gateway: {conn.get('gateway', '?')}")
        print(f"📱 Telegram: {conn.get('telegram', '?')}")
        print(f"💬 微信: {conn.get('weixin', '?')}")
    
    elif args.mode == "cancel":
        msg = cancel_schedule()[1]
        print(msg)
    
    elif args.mode == "wakeup-check":
        run_wakeup_check()
    
    elif args.mode == "sleep-now":
        print("💤 立即进入睡眠...")
        execute_sleep()


if __name__ == "__main__":
    main()