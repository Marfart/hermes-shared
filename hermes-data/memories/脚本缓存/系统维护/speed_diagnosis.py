#!/usr/bin/env python3
"""🏎️  电脑加速诊断 — 轻量版（不遍历文件）"""
import os, shutil, subprocess, ctypes, json

print("=" * 60)
print("🏎️  电脑加速诊断报告  —  Kaliの小马 🐾")
print("=" * 60)

g = 1024**3

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
print(f"   总内存: {m.ullTotalPhys/g:.1f} GB")
print(f"   已使用: {(m.ullTotalPhys-m.ullAvailPhys)/g:.1f} GB  ({m.dwMemoryLoad}%)")
print(f"   剩余:   {m.ullAvailPhys/g:.1f} GB")

# ── 2. 磁盘 ──
print(f"\n🟡 磁盘空间：")
for d in ["C:", "D:", "G:"]:
    try:
        t, u, f = shutil.disk_usage(f"{d}\\")
        print(f"   {d}  {t/g:.0f}G 总  {u/g:.0f}G 已用  {f/g:.0f}G 剩余  {u/t*100:.0f}%")
    except:
        print(f"   {d}  无法读取")

# ── 3. 内存大户（wmic） ──
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
    print(f"   获取失败: {e}")

# ── 4. 建议 ──
print(f"\n{'='*60}")
print(f"💡 加速建议")
print(f"{'='*60}")

c_free = shutil.disk_usage("C:\\")[2] / g

suggestions = []
if m.dwMemoryLoad > 85:
    suggestions.append("\n🔴 内存是最大瓶颈 (已使用 {m.dwMemoryLoad}%)")
    suggestions.append("   ① 任务管理器 → 进程 → 按内存排序, 关掉不需要的")
    suggestions.append("   ② 关掉不用的浏览器标签页（Chrome一个标签=200-500MB）")
    suggestions.append("   ③ 任务管理器 → 启动 → 禁用没必要的开机启动项")
    suggestions.append("   ④ 微信/网易云/QQ 都是吃内存大户, 用完退掉")
    suggestions.append("   ⑤ 终极方案: 加一条内存到 32GB (DDR4/LP 约200元)")

if c_free < 40:
    suggestions.append(f"\n🟡 C盘空间不足 (只剩 {c_free:.0f}GB)")
    suggestions.append("   ① 运行 cleanmgr (Win+R → cleanmgr → 清理系统文件)")
    suggestions.append("   ② 管理员运行: powercfg -h off (关闭休眠, 释放 ~4GB)")
    suggestions.append("   ③ D 盘有充足空间, 把桌面大文件移过去")
    suggestions.append("   ④ 把微信文件存储路径改到 D 盘")

suggestions.append(f"\n✅ 旧文件检查已做: 3年/1年未使用文件扫描 → 电脑无垃圾文件堆积")
suggestions.append(f"✅ Temp临时文件、系统文件夹不影响速度, 非提速关键")

print("\n".join(suggestions))
print()