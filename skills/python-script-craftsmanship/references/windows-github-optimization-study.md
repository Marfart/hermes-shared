# Windows 优化 — GitHub 顶级项目研究笔记

研究时间: 2026-06-03
研究目的: 找出可以直接改善 Kali 电脑速度的实操方案
来源: 3 个 GitHub 项目 + Xcef-1 Python 脚本源码分析

## 研究项目

### 1. hellzerg/optimizer (18.2k⭐) — 已归档
- 链接: https://github.com/hellzerg/optimizer
- 语言: C# (.NET 4.8.1)
- 特点: 24种语言、GUI界面、隐私+安全+性能优化
- 关键功能: 禁用遥测/Cortana/Office遥测、关闭Win10/11自动更新、卸载UWP应用、DNS快速切换、Hosts编辑、系统变量编辑
- 已归档, 继任者: hellzerg/optimizerNXT
- 适合场景: 新装Windows后一次性运行

### 2. Xcef-1/Windows-Performance-Optimizer-Script (Python)
- 链接: https://github.com/Xcef-1/Windows-Performance-Optimizer-Script
- 语言: Python (302行, 单文件)
- 7个优化模块:
  1. Power Settings → 高性能电源计划 (`powercfg /setactive 8c5e7fda...`)
  2. Services Management → 禁用 DiagTrack, WSearch, SysMain, Xbox服务等20个
  3. Process Management → psutil 杀 OneDrive/Spotify/Discord 等
  4. System Cleanup → cleanmgr /sagerun:1
  5. Visual Effects → 注册表 VisualFXSetting=2 (最佳性能)
  6. Xbox Game Bar → GameDVR 注册表禁用
  7. Windows Tips/Ads → ContentDeliveryManager 注册表禁用
- 优点: 纯Python、模块化、好理解
- 缺点: 需要管理员权限、进程列表硬编码

### 3. Sophia Script for Windows (150+ functions, PowerShell)
- 链接: https://github.com/farag2/Sophia-Script-for-Windows
- 语言: PowerShell
- 特点: 150+ 函数, 模块化设计, 专注稳定性
- GUI变体: Sophia-Community/SophiApp (130+ 微调项)
- 适合场景: 高级用户、批量部署

## 已封装的优化脚本

`~/.hermes/scripts/optimizer.py` — 借鉴 Xcef-1 的7项措施 + 预览/执行双模式:

```bash
python optimizer.py          # 预览模式（默认）
python optimizer.py --apply  # 执行模式(需管理员)
```

已保存备份: `memories/脚本缓存/系统维护/optimizer.py`

## 与已有可执行内容的对应关系

| GitHub项目 | 对应的小马工具 |
|-----------|---------------|
| 服务禁用 | optimizer.py #1 |
| 电源计划优化 | optimizer.py #2 |
| 视觉效果关闭 | optimizer.py #3 |
| Xbox Game Bar | optimizer.py #4 |
| Windows广告 | optimizer.py #5 |
| 临时文件清理 | optimizer.py #6 |
| 启动项管理 | optimizer.py #7 (手动管理提示) |
| 进程空闲自动杀 | idle_killer.py (cron) |
| 旧文件清理 | file_cleanup_3y.py |

## Kali 电脑当前评估

RAM 最关键瓶颈 (86%, 剩2.2GB/15.8GB):
- 关程序比改设置更有效
- idle-killer 已部署自动杀2小时空闲进程
- optimizer 可以执行一次优化电源/服务/视觉效果

C盘 90% (剩30GB):
- 休眠已关闭 (hiberfil.sys 不存在)
- 3年/1年旧文件扫描无大垃圾
- 建议把大文件移 D 盘