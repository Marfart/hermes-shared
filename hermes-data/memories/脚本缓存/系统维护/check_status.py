#!/usr/bin/env python3
"""检查 RAM + 磁盘"""
import os

# ── 内存（RAM） ──
try:
    with open("/proc/meminfo") as f:
        data = f.read()
    for line in data.splitlines():
        if line.startswith("MemTotal"):
            total_kb = int(line.split()[1])
        if line.startswith("MemAvailable"):
            avail_kb = int(line.split()[1])
    total_gb = total_kb / 1024 / 1024
    avail_gb = avail_kb / 1024 / 1024
    used_gb = total_gb - avail_gb
    print(f"📌 RAM:")
    print(f"   总内存:  {total_gb:.1f} GB")
    print(f"   已使用:  {used_gb:.1f} GB  ({used_gb/total_gb*100:.0f}%)")
    print(f"   剩余:    {avail_gb:.1f} GB  ({avail_gb/total_gb*100:.0f}%)")
except:
    print("📌 RAM: 无法读取")

# ── 磁盘 ──
import shutil
print(f"\n📌 磁盘分区:")
for d in ["C:", "D:", "G:"]:
    try:
        t, u, f = shutil.disk_usage(f"{d}\\")
        gb = 1024**3
        print(f"   {d}   {t/gb:.0f}G 总  {u/gb:.0f}G 已用  {f/gb:.0f}G 剩余  {u/t*100:.0f}%")
    except:
        print(f"   {d}  无法读取")