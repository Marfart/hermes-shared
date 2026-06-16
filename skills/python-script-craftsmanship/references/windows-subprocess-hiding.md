# Windows Subprocess 黑窗隐藏

## 问题

在 Windows 上，每个 `subprocess.run()` / `subprocess.Popen()` 调用一个控制台模式 .exe（powershell.exe、tasklist.exe、taskkill.exe、curl.exe 等）时，默认会弹出一个 cmd 黑窗口瞬间闪现。

## 为什么单独修每个脚本不够

cron 调度器（`scheduler.py`）启动脚本时用了 `windows_hide_flags()`（即 `creationflags=CREATE_NO_WINDOW`）隐藏了**主 Python 进程**的窗口。但 **`CREATE_NO_WINDOW 不会被 Python 子进程继承**——主进程隐藏了，但它内部 `subprocess.run()` 启动的 powershell/taskkill/tasklist/curl 仍然是独立的子进程，默认会有自己的控制台窗口。

## 修复模式

每个涉及外部命令调用的 `subprocess.run()` 都必须单独加 `creationflags`：

```python
import subprocess
import sys

# 跨平台写法（Windows 才传 flags，Linux/macOS 无此问题）
_flags = subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0

# 应用到所有 subprocess.run 调用
r = subprocess.run(
    ["tasklist", "/FI", f"PID eq {pid}", "/NH"],
    capture_output=True, text=True, timeout=10,
    creationflags=_flags  # ← 必须加
)
```

## 常见需要隐藏的命令

| 命令 | 场景 |
|------|------|
| `powershell.exe` | guard_monitor 的 PS 检测模块 |
| `tasklist.exe` | 进程存在性检查 |
| `taskkill.exe` | idle_killer 杀进程 |
| `curl.exe` | 网络连通性检测 (watchdog) |
| `ipconfig.exe` | DNS 刷新 |
| `schtasks.exe` | 计划任务管理 |

## Popen 后台进程的写法

对于需要长时间后台运行的子进程（daemon），用 `DETACHED_PROCESS` 分离：

```python
subprocess.Popen(
    [python_exe, script_path],
    creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NO_WINDOW,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
    stdin=subprocess.DEVNULL,
)
```

## Hermes 内置 API

`hermes_cli/_subprocess_compat.py` 提供了集中式助手：

- `windows_hide_flags()` → 返回 `CREATE_NO_WINDOW` (0x08000000)，适用于 **同步** `subprocess.run()`（保留 stdout 捕获）
- `windows_detach_flags()` → `CREATE_NO_WINDOW | DETACHED_PROCESS | CREATE_BREAKAWAY_FROM_JOB`，适用于 **后台** `subprocess.Popen()`
- `windows_detach_flags_without_breakaway()` → 同上但不含 BREAKAWAY（降级备用）
- `windows_detach_popen_kwargs()` → 返回 `{"creationflags": ...}` 字典，适用于 `**kwargs` 展开

但注意：这些是 **cron 调度器**用的，直接引用它们需要导入路径。脚本内部最简单的是直接用 `subprocess.CREATE_NO_WINDOW`。

## 安全模式

在 cron no_agent 脚本中，确保所有 `subprocess.run` 调用都有 `creationflags`：

```python
# 完整的安全模式
_subprocess_hide = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' and hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
```

## 验证方法

运行脚本后观察是否有 cmd.exe 窗口闪现。或者用 Process Monitor 看进程树——隐藏的子进程的父进程仍是 Python，但没了控制台窗口。

## 系统扫描清单（每次调试时跑一遍）

当用户报有黑窗闪现时，不要只修已知看门狗——用这把扫描所有 cron 脚本：

```bash
# 在 Hermes scripts 目录搜索所有 subprocess.run 调用
grep -rn "subprocess\.run\b" ~/AppData/Local/hermes/scripts/ | grep -v "\.pyc"
```

然后逐个检查每个 `subprocess.run()` 调用是否带了 `creationflags=`。

**已知修复的脚本及状态：**

| 脚本 | 频率 | 状态 | 最后一次修复日期 |
|:-----|:----:|:----:|:----------------|
| guard_monitor.py | 每2分钟 | ✅ 所有 subprocess.run 都有 CREATE_NO_WINDOW | 2026-06-05 |
| smart_watchdog_v8.py | 每2分钟 | ✅ SubprocessRunner.run() 自带 flags | 已内建 |
| check_live_sync_alive.py | 每5分钟 | ✅ tasklist + Popen 都有 flags | 已内建 |
| idle_killer.py | 每5分钟 | ✅ taskkill 有 flags | 已内建 |
| content_feed_harvester.py | 每小时 | ✅ curl 调用已加 creationflags | 2026-06-10 ← 最新修复 |

**教训：** 每小时的频率虽然低，但 content_feed_harvester.py 的 curl 调用**每次跑都会被 cron 调度器触发**。加上它是 `no_agent=True` 模式 → 每次 curl 弹一个黑窗再关 → 用户会看到每小时闪一次。**任何**有 subprocess.run 的 no_agent cron 脚本都需要检查。

## 通用修复模式（复制粘贴用）

```python
# 文件顶部定义全局常量
import subprocess, sys
_SHOW_HIDE = subprocess.CREATE_NO_WINDOW if sys.platform=='win32' and hasattr(subprocess,'CREATE_NO_WINDOW') else 0

# 所有 subprocess.run 调用加 creationflags
result = subprocess.run(
    ['curl', '-s', '-L', url],
    capture_output=True, text=True, timeout=20,
    creationflags=_SHOW_HIDE   # ← 每个调用都要有
)
```

## 为什么传递性总是漏

cron 调度器 (`_run_job_script` in `scheduler.py` line 1047) 已经把 `creationflags=windows_hide_flags()` 传给主脚本进程了。但：
1. `CREATE_NO_WINDOW` **不会被 Python 子进程自动继承** — 每个子进程是独立的 PE 加载
2. 主脚本里调 `subprocess.run(['curl', ...])` 没加 flags → curl 的 CREATE_CONSOLE 行为弹新黑窗
3. 脚本作者以为「调度器已经隐藏了主进程窗口」就够了 → 漏了脚本内的 subprocess 调用

**每次修完一个脚本后，检查这个脚本是否还有其他 subprocess.run/Popen 调用——常见的是有的加了有的漏了。**