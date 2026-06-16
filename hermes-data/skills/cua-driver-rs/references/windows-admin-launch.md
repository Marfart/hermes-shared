# Windows: 启动需要管理员权限的应用程序 + CUA 驱动自动化

## 问题

许多 Windows 硬件诊断工具（HWiNFO64、CPU-Z、HWMonitor、CrystalDiskInfo 等）需要**管理员权限**才能访问传感器数据。`cua-driver launch_app` 默认不提升权限，导致工具启动后无法读取硬件数据（传感器窗口为空或灰显）。

## 方案：使用 ShellExecuteW "runas" 提权启动

```python
import ctypes

exe_path = r"C:\Path\To\YourApp.exe"
shell32 = ctypes.windll.shell32

# SW_HIDE = 0, SW_SHOWNORMAL = 1, SW_SHOWMINIMIZED = 2, SW_SHOWNOACTIVATE = 4
result = shell32.ShellExecuteW(None, "runas", exe_path, "", None, 0)

if result > 32:
    print("✅ 已以管理员身份启动")
else:
    print("❌ 启动失败（用户取消了 UAC 或出错）")
```

**原理：**
- `ShellExecuteW` + `"runas"` 动词 = Windows 标准的提权启动方式
- 会触发 UAC 弹窗（用户需要点击"是"）
- 返回码 > 32 表示成功，≤ 32 表示失败或取消
- 启动后 HWiNFO 等工具就能正常读取 CPU 温度、电压、风扇转速等传感器

**参数说明：**
- 第4个参数 `""` 是命令行参数（空表示无参数）
- 第5个参数 `None` 是工作目录（默认用程序所在目录）
- 第6个参数是窗口状态（0=隐藏, 1=正常显示, 4=显示但不激活）

## 之后用 CUA 驱动自动化

UAC 弹窗后程序启动，CUA 驱动可以正常接管：

```bash
# 1. 确认进程已运行
cua-driver list_windows | grep HWiNFO

# 2. 获取窗口状态（需要 pid + window_id）
cua-driver get_window_state '{"pid":30368,"window_id":3938640}'

# 3. 点击界面元素（通过 UIA element_index）
cua-driver click '{"pid":30368,"window_id":3938640,"element_index":14}'

# 4. 再次快照验证操作结果
cua-driver get_window_state '{"pid":30368,"window_id":3938640}'
```

**关键点：** 需要同时传 `pid` 和 `window_id`（从 `list_windows` 或 `launch_app` 的返回中获取）。

## 典型场景：HWiNFO64 硬件报告导出

完整流程（Python + CUA 驱动）：

```python
import ctypes, time, subprocess, json

# 1. 提权启动
exe = r"C:\Users\Admin\Desktop\Working\HWiNFO64\HWiNFO64.exe"
shell32 = ctypes.windll.shell32
shell32.ShellExecuteW(None, "runas", exe, "", None, 0)
time.sleep(3)

# 2. 找到 HWiNFO 窗口（从 list_windows 输出解析 pid 和 window_id）
# 假设 pid=30368, window_id=3938640

# 3. 点击"Create a Report File"按钮
subprocess.run([
    "cua-driver", "click",
    json.dumps({"pid": 30368, "window_id": 3938640, "element_index": 14})
])
time.sleep(2)

# 4. 选择 HTML 格式 → 点击"完成"
subprocess.run([
    "cua-driver", "click",
    json.dumps({"pid": 30368, "window_id": 3938640, "element_index": 3})  # HTML format
])

# 5. 点击 Next / Finish
subprocess.run([
    "cua-driver", "click",
    json.dumps({"pid": 30368, "window_id": 3938640, "element_index": 16})  # Next
])
subprocess.run([
    "cua-driver", "click",
    json.dumps({"pid": 30368, "window_id": 3938640, "element_index": 18})  # Finish
])
time.sleep(3)

# 6. 读取生成的报告文件
# 默认保存在程序目录，文件名如 PS2022MIXSNJQO.HTM

# 7. 关闭程序
subprocess.run(["cua-driver", "kill_app", json.dumps({"pid": 30368})])
```

## 复杂多窗口自动化案例：ThrottleStop 全自动配置

ThrottleStop 是比 HWiNFO 更复杂的多窗口 GUI 自动化范例，涉及 **主窗口 → FIVR 子窗口 → Options 子窗口** 三层交互，使用 checkbox、radio button、spinner edit field、keyboard input 等控件。

### 完整流程

```bash
# 1. 提权启动（UAC 弹窗用户需确认）
# Python: ctypes.windll.shell32.ShellExecuteW(None, "runas", exe_path, "", None, 0)

# 2. 确认窗口存在（等待启动）
cua-driver list_windows | grep ThrottleStop
# → PID=8156, wid=985590, title="ThrottleStop 9.7 - Monitoring"

# 3. 每次操作前必须 get_window_state 刷新 element_index 缓存
cua-driver get_window_state '{"pid":8156,"window_id":985590}' > /dev/null

# 4. 主界面：勾选框 + 设置数值
cua-driver click '{"pid":8156,"window_id":985590,"element_index":5}'    # Set Multiplier
cua-driver click '{"pid":8156,"window_id":985590,"element_index":16}'   # 聚焦 multiplier edit 字段
cua-driver press_key '{"pid":8156,"window_id":985590,"key":"Delete"}'
cua-driver press_key '{"pid":8156,"window_id":985590,"key":"4"}'
cua-driver press_key '{"pid":8156,"window_id":985590,"key":"3"}'       # 设 43

cua-driver click '{"pid":8156,"window_id":985590,"element_index":34}'   # Speed Shift EPP
# EPP edit 通常紧邻 checkbox，值设 0
cua-driver click '{"pid":8156,"window_id":985590,"element_index":35}'
cua-driver press_key '{"pid":8156,"window_id":985590,"key":"Delete"}'
cua-driver press_key '{"pid":8156,"window_id":985590,"key":"0"}'

cua-driver click '{"pid":8156,"window_id":985590,"element_index":8}'    # 取消 BD PROCHOT

# 5. Apply 并 Turn On
cua-driver click '{"pid":8156,"window_id":985590,"element_index":105}'

# 6. 打开 FIVR 子窗口 → 设 Core/Cache 降压
cua-driver get_window_state '{"pid":8156,"window_id":985590}'
cua-driver click '{"pid":8156,"window_id":985590,"element_index":20}'   # FIVR 按钮
sleep 2
cua-driver get_window_state '{"pid":8156,"window_id":985590}'           # 刷新树（包含 FIVR 子窗口）

# FIVR 窗口内操作：选 FIVR Control 标签 → 解锁电压 → 设 Offset
cua-driver click '{"pid":8156,"window_id":985590,"element_index":24}'   # "FIVR Control" radio
cua-driver click '{"pid":8156,"window_id":985590,"element_index":30}'   # "Unlock Adjustable Voltage"
cua-driver click '{"pid":8156,"window_id":985590,"element_index":33}'   # Offset Voltage edit
cua-driver hotkey '{"pid":8156,"window_id":985590,"keys":["Ctrl","A"]}' # 全选
cua-driver press_key '{"pid":8156,"window_id":985590,"key":"Delete"}'
cua-driver press_key '{"pid":8156,"window_id":985590,"key":"-"}'
cua-driver press_key '{"pid":8156,"window_id":985590,"key":"5"}'
cua-driver press_key '{"pid":8156,"window_id":985590,"key":"0"}'        # → -50 mV

# 一样的方法设 CPU Cache（先选 list 中的 CPU Cache item）
cua-driver click '{"pid":8156,"window_id":985590,"element_index":47}'
cua-driver click '{"pid":8156,"window_id":985590,"element_index":33}'
cua-driver hotkey '{"pid":8156,"window_id":985590,"keys":["Ctrl","A"]}'
cua-driver press_key '{"pid":8156,"window_id":985590,"key":"Delete"}'
cua-driver press_key '{"pid":8156,"window_id":985590,"key":"-"}'
cua-driver press_key '{"pid":8156,"window_id":985590,"key":"5"}'
cua-driver press_key '{"pid":8156,"window_id":985590,"key":"0"}'

# 选 "Save voltages immediately" 并点 OK
cua-driver click '{"pid":8156,"window_id":985590,"element_index":58}'
cua-driver click '{"pid":8156,"window_id":985590,"element_index":60}'   # OK

# 7. 打开 Options 设自启
cua-driver get_window_state '{"pid":8156,"window_id":985590}'           # 子窗口关闭后刷新树
cua-driver click '{"pid":8156,"window_id":985590,"element_index":104}'  # Options 按钮
sleep 2
cua-driver get_window_state '{"pid":8156,"window_id":985590}'
cua-driver click '{"pid":8156,"window_id":985590,"element_index":13}'   # Start Minimized
cua-driver click '{"pid":8156,"window_id":985590,"element_index":0}'    # OK

# 8. 最终 Apply + 关闭
cua-driver click '{"pid":8156,"window_id":985590,"element_index":105}'
cua-driver kill_app '{"pid":8156}'
```

### 关键洞见

| 操作 | 注意事项 |
|:-----|:---------|
| **checkbox toggle** | UIA Invoke 直接切换状态，不需要先检查当前状态 |
| **hotkey (Ctrl+A)** | 需要传 `window_id`，无窗口 ID 时报 "No windows found" |
| **press_key** | 也需 `window_id`，按键发送到目标进程的当前聚焦控件 |
| **子窗口操作** | FIVR/Options 打开后必须重新 `get_window_state`，子窗口元素会合并到同一个 pid+window_id 的树中，**不需要**单独的 window_id |
| **element_index 变换** | 子窗口打开/关闭后主窗口的元素索引会**重新编号**，必须重新 snapshot |
| **get_window_state 输出过大** | 管道到 Python 可能因 JSON 太大而截断。解决方案：重定向到文件再读取 |
| **Apply (Turn On)** | Turn On 后 ThrottleStop 默认最小化到系统托盘，窗口消失。需 kill 再重启才能继续操作 |

## 注意事项

- **UAC 弹窗需要用户交互**：用户必须在电脑前点击"是"。在用户确认授权前调用会返回失败。
- **窗口 ID 会变**：进程重启后 window_id 和 element_index 都会变化，必须重新获取。
- **element_index 单次快照有效**：每次 `get_window_state` 后的 element_index 只在下一次快照前有效。
- **get_window_state JSON 太大**：当树有 140+ 元素时 (~80KB JSON)，管道传递可能截断。保存到文件处理：

```bash
cua-driver get_window_state '{"pid":8156,"window_id":985590}' > /tmp/state.json
python -c "import json; data = json.load(open('/tmp/state.json')); print(data['tree_markdown'][:500])"
```

注意：在 git-bash 中 `/tmp/` 路径映射到 MSYS tmp，用 Python 读取时需要使用 Windows 绝对路径。

- **替代方案**：硬件信息也可以用 WMI 获取（不需要管理员权限），但 HWiNFO 提供更全面的传感器数据（温度、电压、风扇转速等）。
- **自启配置**：Option A（CUA 驱动 Options 窗口），Option B（直接放启动文件夹快捷方式）：

```powershell
$ws = New-Object -ComObject WScript.Shell
$sc = $ws.CreateShortcut("$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\ThrottleStop.lnk")
$sc.TargetPath = "C:\Path\To\ThrottleStop.exe"
$sc.Save()
```
