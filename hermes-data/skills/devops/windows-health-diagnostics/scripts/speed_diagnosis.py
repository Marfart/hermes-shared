#!/usr/bin/env python3
"""🏎️ Windows 健康诊断 — 纯 Python stdlib + ctypes（不依赖 tasklist/wmic）"""
import os, shutil, subprocess, ctypes
from pathlib import Path

g = 1024**3

print("=" * 60)
print("🏎️  Windows 健康诊断报告")
print("=" * 60)

# ── 1. RAM ──
print("\n🔴 内存状态：")
class MEMORYSTATUSEX(ctypes.Structure):
    _fields_ = [
        ('dwLength', ctypes.c_ulong),
        ('dwMemoryLoad', ctypes.c_ulong),
        ('ullTotalPhys', ctypes.c_ulonglong),
        ('ullAvailPhys', ctypes.c_ulonglong),
        ('ullTotalPageFile', ctypes.c_ulonglong),
        ('ullAvailPageFile', ctypes.c_ulonglong),
        ('ullTotalVirtual', ctypes.c_ulonglong),
        ('ullAvailVirtual', ctypes.c_ulonglong),
        ('ullAvailExtendedVirtual', ctypes.c_ulonglong),
    ]
m = MEMORYSTATUSEX()
m.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
used_gb = (m.ullTotalPhys - m.ullAvailPhys) / g
total_gb = m.ullTotalPhys / g
print(f"   总内存: {total_gb:.1f} GB")
print(f"   已使用: {used_gb:.1f} GB  ({m.dwMemoryLoad}%)")
print(f"   剩余:   {m.ullAvailPhys/g:.1f} GB")
if m.dwMemoryLoad > 85:
    print(f"   ⚠️  占用 {m.dwMemoryLoad}% — 这是卡顿主因！")

# ── 2. 磁盘 ──
print(f"\n🟡 磁盘空间：")
for d in ["C:", "D:", "G:"]:
    try:
        t, u, f = shutil.disk_usage(f"{d}\\")
        print(f"   {d}  {t/g:.0f}G 总  {u/g:.0f}G 已用  {f/g:.0f}G 剩余  {u/t*100:.0f}%")
    except:
        pass

# ── 3. 内存大户（wmic — 可能超时，跳过不影响诊断） ──
print(f"\n🔴 内存占用 TOP15：")
try:
    r = subprocess.run(
        'cmd.exe //c "wmic process get Name,WorkingSet64"',
        capture_output=True, timeout=60, shell=True
    )
    out = r.stdout.decode("gbk", errors="replace")
    procs = []
    for line in out.strip().split("\n")[1:]:
        parts = line.strip().split()
        if len(parts) >= 2:
            try:
                wss = int(parts[-1])
                name = " ".join(parts[:-1])
                if wss > 0 and wss < 10**11:
                    procs.append((wss, name))
            except:
                pass
    procs.sort(reverse=True)
    print(f"   {'进程':<32} {'内存':>8}")
    print(f"   {'-'*42}")
    for wss, name in procs[:15]:
        print(f"   {name:<32} {wss/1024/1024:>7.1f} MB")
except Exception as e:
    print(f"   获取失败（不影响诊断结论）: {e}")

# ── 4. 建议 ──
print(f"\n{'='*60}")
print(f"💡 加速建议")
print(f"{'='*60}")

c_free_gb = shutil.disk_usage("C:\\")[2] / g
d_free_gb = shutil.disk_usage("D:\\")[2] / g
suggestions = []

if m.dwMemoryLoad > 85:
    suggestions.append("\n🔴 内存是最大瓶颈 (已使用 {m.dwMemoryLoad}%)")
    suggestions.append("   ① Ctrl+Shift+Esc → 进程 → 按内存排序, 关掉不需要的")
    suggestions.append("   ② 关掉不用的 Chrome 标签页 (每个 200-500MB)")
    suggestions.append("   ③ 任务管理器 → 启动 → 禁用不必要的开机启动")
    suggestions.append("   ④ 微信/网易云/QQ 用完退掉")
    suggestions.append("   ⑤ 终极: 加一条 DDR4 笔记本内存到 32GB (~200元)")

if c_free_gb < 40:
    suggestions.append(f"\n🟡 C盘空间不足 (剩 {c_free_gb:.0f}GB)")
    suggestions.append("   ① Win+R → cleanmgr → 清理系统文件")
    suggestions.append("   ② 管理员运行: powercfg -h off (释放 ~4GB)")
    suggestions.append(f"   ③ D 盘有 {d_free_gb:.0f}GB, 把大文件移过去")

print("\n".join(suggestions) if suggestions else "   电脑状态不错 !")
print()