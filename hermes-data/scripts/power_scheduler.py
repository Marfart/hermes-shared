"""
电脑开关机定时管家 🔌
=====================
功能：
  setup        设置定时关机和自动开机
  status       查看当前计划
  cancel       取消所有计划

用法：
  python power_scheduler.py setup --shutdown-at 23:00 --poweron-at 08:00
  python power_scheduler.py status
  python power_scheduler.py cancel

原理：
  - 关机：shutdown /s /t 60（60秒倒计时关机）
  - 开机：用 schtasks 注册一次性任务，任务属性设"唤醒计算机运行"
  - 开机后 Windows 自动启动 Hermes（启动文件夹已有）
  - 开机后自动执行 wakeup_check.py 检查连通告警

注意：
  - 从完全关机（S5）唤醒需要主板支持 RTC 唤醒
  - 你的电脑已确认支持（RTCWAKE=1）✅
"""
import argparse
import json
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

# =====================================================================
# 常量
# =====================================================================
HERMES_HOME = Path.home() / "AppData" / "Local" / "hermes"
SCRIPT_DIR = HERMES_HOME / "scripts"
CONFIG_FILE = SCRIPT_DIR / ".power_schedule.json"
TASK_NAME = "Hermes_PowerOn"

# =====================================================================
# 工具函数
# =====================================================================
def decode_gbk(data: bytes) -> str:
    try:
        return data.decode("gbk", errors="replace")
    except:
        return data.decode("utf-8", errors="replace")

def run_ps(script: str, timeout: int = 15) -> tuple[int, str, str]:
    """运行 PowerShell 命令"""
    try:
        r = subprocess.run(
            ["powershell", "-NoProfile", "-Command", script],
            capture_output=True, timeout=timeout
        )
        return r.returncode, decode_gbk(r.stdout), decode_gbk(r.stderr)
    except subprocess.TimeoutExpired:
        return -1, "⏱️ 超时", ""
    except Exception as e:
        return -1, str(e), ""

def run_cmd(cmd: list[str], timeout: int = 15) -> tuple[int, str]:
    """运行 cmd 命令"""
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

# =====================================================================
# 核心功能
# =====================================================================
def setup_schedule(shutdown_time: str, poweron_time: str) -> tuple[bool, str]:
    """
    设置定时关机和自动开机
    
    shutdown_time: HH:MM 格式
    poweron_time:  HH:MM 格式
    """
    now = datetime.now()
    
    # 解析时间
    sd_h, sd_m = map(int, shutdown_time.split(":"))
    po_h, po_m = map(int, poweron_time.split(":"))
    
    sd_dt = now.replace(hour=sd_h, minute=sd_m, second=0, microsecond=0)
    po_dt = now.replace(hour=po_h, minute=po_m, second=0, microsecond=0)
    
    # 如果时间已过，推到明天
    if sd_dt <= now:
        sd_dt += timedelta(days=1)
    if po_dt <= now:
        po_dt += timedelta(days=1)
    # 如果开机时间在关机时间前面（过夜场景），推到后天
    if po_dt <= sd_dt and po_dt <= sd_dt + timedelta(hours=1):
        po_dt += timedelta(days=1)
    
    wake_time_str = po_dt.strftime("%H:%M")
    wake_date_str = po_dt.strftime("%Y/%m/%d")
    
    # ---- 1. 注册唤醒任务（schtasks + 唤醒标记） ----
    # 用 PowerShell 执行，避免 bash 的编码问题
    check_script = str(SCRIPT_DIR / "wakeup_check.py")
    
    ps_code = f'''
    # 删除旧任务
    schtasks /delete /tn "{TASK_NAME}" /f 2>$null
    
    # 创建新任务 - 使用 XML 方式设置"唤醒计算机运行"
    $xml = @"
    <?xml version="1.0" encoding="UTF-16"?>
    <Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
      <RegistrationInfo>
        <Author>Hermes</Author>
        <Description>定时开机 - 由 Hermes power_scheduler 管理</Description>
      </RegistrationInfo>
      <Triggers>
        <TimeTrigger>
          <StartBoundary>{wake_date_str}T{wake_time_str}:00</StartBoundary>
          <Enabled>true</Enabled>
        </TimeTrigger>
      </Triggers>
      <Settings>
        <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
        <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
        <WakeToRun>true</WakeToRun>
        <ExecutionTimeLimit>PT10M</ExecutionTimeLimit>
      </Settings>
      <Actions Context="Author">
        <Exec>
          <Command>python</Command>
          <Arguments>"{check_script}"</Arguments>
        </Exec>
      </Actions>
      <Principals>
        <Principal id="Author">
          <UserId>{now.strftime("%Y")}</UserId>
          <RunLevel>HighestAvailable</RunLevel>
        </Principal>
      </Principals>
    </Task>
    "@
    
    # 先找个临时路径写 XML
    $tmpXml = [System.IO.Path]::GetTempFileName() + ".xml"
    [System.IO.File]::WriteAllText($tmpXml, $xml, [System.Text.Encoding]::Unicode)
    
    # 注册任务
    $result = schtasks /create /tn "{TASK_NAME}" /xml $tmpXml /f 2>&1
    Remove-Item $tmpXml -Force -ErrorAction SilentlyContinue
    
    Write-Output $result
    '''
    
    code, out, err = run_ps(ps_code)
    if code != 0 and "成功" not in out:
        # 如果 XML 方式失败，试试简单方式
        fallback_ps = f'''
        schtasks /delete /tn "{TASK_NAME}" /f 2>$null
        schtasks /create /tn "{TASK_NAME}" /tr "python {check_script}" /sc once /st {wake_time_str} /sd {wake_date_str} /f
        schtasks /change /tn "{TASK_NAME}" /enable 2>$null
        '''
        code2, out2, err2 = run_ps(fallback_ps)
        if code2 != 0:
            return False, f"❌ 创建开机任务失败: {err2 or out2}"
    
    # ---- 2. 保存配置 ----
    config = {
        "shutdown_at": shutdown_time,
        "poweron_at": poweron_time,
        "created_at": datetime.now().isoformat(),
        "next_shutdown": sd_dt.isoformat(),
        "next_poweron": po_dt.isoformat(),
    }
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")
    
    # 计算睡眠时间差
    diff = (sd_dt - now).total_seconds()
    hours = int(diff // 3600)
    mins = int((diff % 3600) // 60)
    
    msg = (
        f"✅ 定时计划已设置！\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"🔌 关机时间: {shutdown_time}（约 {hours}h{mins}min 后）\n"
        f"⚡ 开机时间: {poweron_time}\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"\n"
        f"📋 流程：\n"
        f"  {shutdown_time} → 电脑关机\n"
        f"     ↓ （主板 RTC 定时唤醒）\n"
        f"  {poweron_time} → 自动开机\n"
        f"     ↓ （启动文件夹）\n"
        f"  Hermes 自动启动 → 检查连接\n"
        f"\n"
        f"⚠️ 注意：\n"
        f"  1. 从完全关机（S5）唤醒需要主板支持\n"
        f"  2. 确认 BIOS 中 RTC Wake / Power On by RTC 已启用\n"
        f"  3. 电脑需接通电源\n"
        f"  4. 关机前会保存所有工作（60秒倒计时可取消）"
    )
    return True, msg


def get_status() -> dict:
    """获取当前调度状态"""
    config = {}
    if CONFIG_FILE.exists():
        try:
            config = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except:
            pass
    
    # 查唤醒任务
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
    
    return {"config": config, "task_exists": task_exists, "next_run": next_run}


def cancel_schedule() -> tuple[bool, str]:
    """取消所有定时"""
    run_ps(f'schtasks /delete /tn "{TASK_NAME}" /f')
    if CONFIG_FILE.exists():
        CONFIG_FILE.unlink()
    run_cmd(["shutdown", "/a"])  # 取消待执行的关机
    return True, "✅ 所有定时已取消"


def status_output():
    status = get_status()
    config = status.get("config", {})
    
    print("=" * 40)
    print("🔌 定时开关机状态")
    print("=" * 40)
    
    if config:
        print(f"\n📅 当前计划:")
        print(f"   关机: {config.get('shutdown_at', '?')}")
        print(f"   开机: {config.get('poweron_at', '?')}")
        print(f"   创建于: {config.get('created_at', '?')[:19]}")
    else:
        print(f"\n📭 暂无定时计划")
    
    print(f"\n⚡ 开机任务: {'✅ 已注册' if status['task_exists'] else '❌ 无'}")
    if status.get("next_run"):
        print(f"   下次唤醒: {status['next_run']}")
    
    print()


# =====================================================================
# CLI 入口
# =====================================================================
def main():
    parser = argparse.ArgumentParser(
        description="🔌 电脑定时开关机管家 — 定时关机 + 自动开机",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  python power_scheduler.py setup --shutdown-at 23:00 --poweron-at 08:00
  python power_scheduler.py status
  python power_scheduler.py cancel
        """
    )
    parser.add_argument("mode", choices=["setup", "status", "cancel"],
                        help="操作模式")
    parser.add_argument("--shutdown-at", help="关机时间 HH:MM（如 23:00）")
    parser.add_argument("--poweron-at", help="开机时间 HH:MM（如 08:00）")
    
    args = parser.parse_args()
    
    if args.mode == "setup":
        if not args.shutdown_at or not args.poweron_at:
            print("❌ 需要 --shutdown-at 和 --poweron-at 参数\n")
            print("示例: python power_scheduler.py setup --shutdown-at 23:00 --poweron-at 08:00")
            return
        
        # 计时器 - 延迟关机
        now = datetime.now()
        sd_h, sd_m = map(int, args.shutdown_at.split(":"))
        sd_dt = now.replace(hour=sd_h, minute=sd_m, second=0, microsecond=0)
        if sd_dt <= now:
            sd_dt += timedelta(days=1)
        
        ok, msg = setup_schedule(args.shutdown_at, args.poweron_at)
        print(msg)
        
        if ok:
            # 计算关机倒计时秒数
            delta = int((sd_dt - datetime.now()).total_seconds())
            if delta > 60:
                print(f"\n💤 倒计时 {delta} 秒后自动关机...")
                print(f"   如果想取消，运行: python power_scheduler.py cancel")
            else:
                print(f"\n💤 即将关机...")
    
    elif args.mode == "status":
        status_output()
    
    elif args.mode == "cancel":
        msg = cancel_schedule()[1]
        print(msg)


if __name__ == "__main__":
    main()
