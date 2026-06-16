---
name: idle-process-killer
description: "进程空闲自动杀手 — 2小时无活动进程自动杀，释放内存"
version: 1.0.0
author: Tachikoma
platforms: [windows]
trigger: "进程杀手|空闲进程|自动清理|idle killer|内存释放"
---

# 进程空闲杀手

每5分钟检查一次，杀掉2小时无CPU活动的空闲进程，自动释放内存。

## 脚本位置

- 主脚本: `~/.hermes/scripts/idle_killer.py`
- 状态文件: `~/.hermes/memories/脚本缓存/系统维护/idle_killer_state.json`

## cron 配置

- job_id: `b78688dcb23f`
- 频率: 每5分钟
- 模式: no_agent=True（静默后台运行，无空闲进程时不输出）

## 安全白名单

### 系统核心（不杀）
svchost.exe, services.exe, lsass.exe, dwm.exe, conhost.exe 等

### 常用软件（不杀）
Chrome, Firefox, Edge, WeChat, DingTalk, Code, Obsidian, 网易云等

### Agent 进程（不杀 — 致命的漏杀会被用户纠正）
python.exe, bash.exe, **hermes.exe**, **codex.exe**
(2026-06-03 用户纠正: codex.exe 不在白名单, 后台有8个实例在跑)

### 前台保护（不杀）
当前正在使用的窗口进程自动跳过

## ⚠️ 关键陷阱

### 白名单完整性
用户明确要求: **hermes.exe 和 codex.exe 绝对不能杀**。查错方法:
```python
# 检查当前运行的 Agent 进程
import ctypes
TH32CS_SNAPPROCESS = 0x00000002
k = ctypes.windll.kernel32
s = k.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
# 遍历确认 hermes.exe 和 codex.exe 都在白名单
```
任何修改白名单的操作后, 先跑 `--dry-run` 确认不会误杀后再上线。

### 前台检测不杀当前窗口
用 `GetForegroundWindow()` + `GetWindowThreadProcessId()` 获取前台窗口 PID,
与空闲进程 PID 比对, 相等则跳过。

## 手动操作

```bash
# 预览（查看哪些会被杀）
python idle_killer.py --dry-run

# 重置状态
python idle_killer.py --reset
```