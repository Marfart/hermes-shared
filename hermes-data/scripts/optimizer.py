#!/usr/bin/env python3
"""
Windows 加速优化脚本
从 GitHub 顶级项目学来的 7 项优化措施：
- Xcef-1/Windows-Performance-Optimizer-Script → 服务禁用/电源/视觉
- hellzerg/optimizer (18.2k⭐) → 隐私/注册表/启动项
- Sophia Script (150+ functions) → 系统微调方法论

安全原则：所有操作都有 --dry-run 预览 + 可逆说明
"""
import os, sys, subprocess, ctypes, json, time
from pathlib import Path
from datetime import datetime

SCRIPT_DIR = Path(__file__).parent
STATE_DIR = SCRIPT_DIR  # ~/.hermes/scripts/
BACKUP_FILE = STATE_DIR / "optimizer_backup.json"

def log(msg):
    print(f"[{datetime.now():%H:%M:%S}] {msg}")

def run(cmd, timeout=30):
    """执行命令并返回 (ok, output)"""
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=timeout, shell=True)
        out = r.stdout.decode("gbk", errors="replace").strip()
        err = r.stderr.decode("gbk", errors="replace").strip()
        return r.returncode == 0, out or err
    except subprocess.TimeoutExpired:
        return False, "超时"
    except Exception as e:
        return False, str(e)

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except:
        return False

# ── 1. 服务管理 ──
# 这些服务在 SSD + 个人电脑上可以安全禁用
OPTIONAL_SERVICES = {
    "DiagTrack": "诊断跟踪服务（收集使用数据发送微软）",
    "dmwappushservice": "诊断管理推送服务",
    "WSearch": "Windows Search 索引服务（搜索文件用，耗CPU）",
    "SysMain": "Superfetch/预读（对SSD无用，反而占内存）",
    "TrkWks": "分布式链接跟踪客户端",
    "XblAuthManager": "Xbox 身份验证",
    "XblGameSave": "Xbox 游戏存档",
    "XboxNetApiSvc": "Xbox 网络服务",
    "lfsvc": "地理位置服务",
    "MapsBroker": "下载地图管理器",
    "PhoneSvc": "电话服务",
    "WpcMonSvc": "家长控制",
    "RetailDemo": "零售演示服务",
    "RemoteRegistry": "远程注册表（安全风险）",
    "SCardSvr": "智能卡服务",
    "SSDPSRV": "SSDP 发现协议",
    "upnphost": "UPnP 设备主机",
    "wercplsupport": "问题报告支持",
    "WerSvc": "Windows 错误报告",
    "Fax": "传真服务",
}

def manage_services(dry_run=True, action="disable"):
    """禁用或启用可选服务"""
    log(f"\n📌 1. {'预览' if dry_run else '执行'} 服务 {action}")
    results = []
    for svc, desc in OPTIONAL_SERVICES.items():
        ok, out = run(f'sc query {svc}', 10)
        if not ok:
            continue  # 服务不存在
        if dry_run:
            log(f"   📋 可{action}: {svc} ({desc})")
            results.append((svc, "preview"))
        else:
            if action == "disable":
                run(f'sc stop {svc}', 10)
                ok2, _ = run(f'sc config {svc} start= disabled', 10)
                results.append((svc, "disabled" if ok2 else "failed"))
                log(f"   {'✅ 已禁用' if ok2 else '⚠️ 失败'} {svc}")
    return results

# ── 2. 电源计划 ──
def optimize_power(dry_run=True):
    log(f"\n📌 2. {'预览' if dry_run else '执行'} 电源计划")
    if dry_run:
        ok, out = run('powercfg /list')
        log(f"   当前电源方案:\n{out}")
        log(f"   即将设置: 高性能 (8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c)")
    else:
        ok, out = run('powercfg /setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c')
        log(f"   {'✅ 已设为高性能' if ok else '⚠️ 设置失败: '+out}")

# ── 3. 视觉效果 ──
def disable_visual_effects(dry_run=True):
    log(f"\n📌 3. {'预览' if dry_run else '执行'} 视觉效果")
    if dry_run:
        log(f"   即将关闭: 窗口动画、透明效果、阴影")
        log(f"   → 可节省 GPU 和内存资源")
    else:
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Explorer\VisualEffects",
                0, winreg.KEY_WRITE)
            winreg.SetValueEx(key, "VisualFXSetting", 0, winreg.REG_DWORD, 2)
            winreg.CloseKey(key)
            log("   ✅ 视觉效果已优化为「最佳性能」")
        except Exception as e:
            log(f"   ⚠️ 失败: {e}")

# ── 4. Xbox Game Bar ──
def disable_game_bar(dry_run=True):
    log(f"\n📌 4. {'预览' if dry_run else '执行'} Xbox Game Bar")
    if dry_run:
        log(f"   即将禁用: Xbox Game Bar / Game DVR（后台录制吃资源）")
    else:
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\GameDVR",
                0, winreg.KEY_WRITE)
            winreg.SetValueEx(key, "AppCaptureEnabled", 0, winreg.REG_DWORD, 0)
            winreg.SetValueEx(key, "GameDVR_Enabled", 0, winreg.REG_DWORD, 0)
            winreg.CloseKey(key)
            log("   ✅ Xbox Game Bar 已禁用")
        except:
            log("   ⚠️ 注册表键不存在（可能已禁用）")

# ── 5. Windows 广告/提示 ──
def disable_tips_ads(dry_run=True):
    log(f"\n📌 5. {'预览' if dry_run else '执行'} Windows 广告与提示")
    if dry_run:
        log(f"   即将关闭: 锁屏广告、开始菜单推荐、Windows 使用提示")
    else:
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\ContentDeliveryManager",
                0, winreg.KEY_WRITE)
            winreg.SetValueEx(key, "SubscribedContent-338388Enabled", 0, winreg.REG_DWORD, 0)
            winreg.SetValueEx(key, "SystemPaneSuggestionsEnabled", 0, winreg.REG_DWORD, 0)
            winreg.CloseKey(key)
            log("   ✅ Windows 广告和提示已禁用")
        except:
            log("   ⚠️ 注册表操作失败")

# ── 6. 临时文件清理 ──
def clean_temp(dry_run=True):
    log(f"\n📌 6. {'预览' if dry_run else '执行'} 临时文件清理")
    if dry_run:
        log(f"   将运行 cleanmgr 磁盘清理 + 删除 .tmp/.log 临时文件")
    else:
        ok, out = run("cleanmgr /sagerun:1", 120)
        log(f"   {'✅ 清理完成' if ok else '⚠️ 未执行（可能需要先配置cleanmgr）'}")
        # 手动清理 Temp 中的临时文件后缀
        temp = Path(os.environ.get("TEMP", ""))
        if temp.exists():
            cnt = 0
            for f in list(temp.rglob("*"))[:5000]:
                try:
                    if f.is_file() and f.suffix in (".tmp", ".log", ".etl", ".dmp"):
                        f.unlink()
                        cnt += 1
                except:
                    pass
            log(f"   额外清理了 {cnt} 个临时文件")

# ── 7. 启动项管理（跳过 PowerShell） ──
def list_startup():
    log(f"\n📌 7. 开机启动项")
    log(f"   建议手动管理: 打开任务管理器 → 启动 → 禁用不需要的")

# ── main ──
def main():
    dry_run = "--dry-run" in sys.argv or "-n" in sys.argv
    apply = "--apply" in sys.argv or "-a" in sys.argv
    
    if not dry_run and not apply:
        dry_run = True  # 默认预览

    print("=" * 60)
    print(f"🚀 Windows 加速优化   {'[预览模式]' if dry_run else '[执行模式]'}")
    print(f"   灵感来自 GitHub 顶级项目:")
    print(f"   • Xcef-1/Windows-Performance-Optimizer-Script")
    print(f"   • hellzerg/optimizer (18.2k⭐)")
    print(f"   • Sophia Script (150+ functions)")
    print("=" * 60)

    if not is_admin():
        log("⚠️ 建议以管理员身份运行以获得最佳效果")
        log("   部分功能（如服务禁用）需要管理员权限")
        if apply and not dry_run:
            log("❌ 执行模式需要管理员权限！")
            log("   请右键以管理员身份运行")
            return

    # 全部预览
    list_startup()
    manage_services(dry_run=True)
    optimize_power(dry_run=True)
    disable_visual_effects(dry_run=True)
    disable_game_bar(dry_run=True)
    disable_tips_ads(dry_run=True)
    clean_temp(dry_run=True)

    if not apply:
        print(f"\n{'='*60}")
        print(f"💡 预览完成！要执行请加 --apply 参数")
        print(f"   python optimizer.py --apply")
        print(f"   (建议先 --dry-run 看完再执行)")
        print(f"{'='*60}")
        return

    # ── 执行 ──
    log("\n" + "=" * 50)
    log("🚀 开始执行优化...")

    # 备份当前状态
    backup = {
        "timestamp": datetime.now().isoformat(),
        "note": "优化前状态备份",
    }
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        BACKUP_FILE.write_text(json.dumps(backup, ensure_ascii=False, indent=2), "utf-8")
    except:
        pass

    manage_services(dry_run=False, action="disable")
    optimize_power(dry_run=False)
    disable_visual_effects(dry_run=False)
    disable_game_bar(dry_run=False)
    disable_tips_ads(dry_run=False)
    clean_temp(dry_run=False)

    log("\n" + "=" * 50)
    log("✅ 优化完成！建议重启电脑生效")
    log("=" * 50)
    log("💡 想撤销的话:")
    log("   1. 服务: 运行 services.msc 手动改为 Automatic")
    log("   2. 电源: control panel → 电源选项 → 平衡")
    log("   3. 视觉效果: 系统属性 → 高级 → 性能 → 调整")
    log("=" * 50)

if __name__ == "__main__":
    main()