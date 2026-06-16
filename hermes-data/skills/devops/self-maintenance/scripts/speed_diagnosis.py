# speed_diagnosis.py — 一键健康诊断脚本

本脚本由 `windows-health-diagnostics` 技能提供，放在此处方便 cron/手动执行。

```bash
python speed_diagnosis.py
```

输出：RAM状态 + 磁盘空间 + TOP15进程 + 优化建议。

技术栈：纯 Python stdlib + ctypes（`GlobalMemoryStatusEx`），不依赖 tasklist/wmic。