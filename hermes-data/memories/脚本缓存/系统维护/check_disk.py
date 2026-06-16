#!/usr/bin/env python3
"""检查各分区磁盘用量"""
import shutil

drives = ["C:", "D:", "G:"]
for d in drives:
    try:
        t, u, f = shutil.disk_usage(f"{d}\\")
        gb = 1024 ** 3
        pct = u / t * 100
        print(f"{d}:  {t/gb:.0f}G 总数  {u/gb:.0f}G 已用  {f/gb:.0f}G 剩余  {pct:.0f}%")
    except Exception as e:
        print(f"{d}: 无法读取 — {e}")