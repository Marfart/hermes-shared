# Windows 蓝牙诊断指南

## 症状

- 设置里看不到蓝牙开关
- 设备管理器没有蓝牙设备
- 蓝牙服务报错或无法启动

## 诊断流程

### 第一步：检查蓝牙服务

```powershell
Get-Service bthserv, bthport | Format-Table Name, Status, StartType -AutoSize
```

| 服务 | 含义 | 正常状态 |
|:-----|:-----|:---------|
| `bthserv` | 蓝牙支持服务 | Running |
| `bthport` | 蓝牙端口驱动 | Running 或 Stopped（无硬件时） |

### 第二步：检查蓝牙硬件是否存在

```powershell
# 方法1：PnP设备搜索（写入.ps1文件执行，不要用 inline -Command）
Get-PnpDevice | Where-Object { $_.InstanceId -match "BTH" } | Format-Table Status, FriendlyName, InstanceId -AutoSize
```

**⚠️ 关键陷阱**：`$_` 在 `powershell -Command` 中会被 bash 解释为路径（`C:\Users\Admin.Property`），导致 `CommandNotFoundException`。**必须写入 `.ps1` 文件后用 `powershell -File` 执行。**

### 第三步：检查USB蓝牙适配器

```powershell
Get-PnpDevice -Class USB | Where-Object { $_.FriendlyName -match "Bluetooth|BTH" } | Format-Table Status, FriendlyName -AutoSize
```

### 第四步：检查被禁用的设备

```powershell
Get-PnpDevice -Status Error | Select-Object FriendlyName, Class | Format-Table -AutoSize
```

## 常见结论

### 情况A：完全没有蓝牙硬件
- PnP 设备列表无任何 BTH/蓝牙设备
- USB 设备列表无蓝牙适配器
- **解决方案**：购买 USB 蓝牙适配器（推荐 TP-Link UB500 或绿联 CM391，约 ¥40-80）

### 情况B：有硬件但驱动未安装
- PnP 设备列表有 "Unknown device" 或 "Bluetooth" 但状态为 Error
- **解决方案**：安装蓝牙驱动（Windows Update 或厂商官网）

### 情况C：服务未启动
- `bthport` 为 Stopped
- **解决方案**：`Start-Service bthport`（需管理员权限）

## 蓝牙服务启动/停止

```powershell
# 启动蓝牙支持服务
Start-Service bthserv

# 设置自动启动
Set-Service bthserv -StartupType Automatic

# 启动蓝牙端口
Start-Service bthport
```

## USB 蓝牙适配器推荐

| 型号 | 蓝牙版本 | 价格 | 备注 |
|:-----|:---------|:-----|:-----|
| TP-Link UB500 | 5.0 | ¥50-80 | 即插即用，Win11 自动装驱动 |
| 绿联 CM391 | 5.0 | ¥40-60 | 小巧，免驱 |
| 绿联 CM591 | 5.3 | ¥60-90 | 最新协议，低延迟 |

## PowerShell 执行铁律（Windows git-bash 环境）

在 Hermes `terminal` 工具（git-bash）中执行 PowerShell 时：

1. **永远不要用 `powershell -Command` 传递含 `$_` 的命令** — bash 会展开 `$_` 为路径
2. **正确做法**：写入 `.ps1` 文件 → `powershell -File script.ps1`
3. **如果必须用 `-Command`**：用单引号包裹，且避免 `$_`（改用 `-Filter` 参数或变量）

```bash
# ❌ 错误 — $_ 被 bash 吃掉
powershell -Command "Get-Service | Where-Object { $_.Name -like 'bth*' }"

# ✅ 正确 — 写文件执行
cat > /tmp/bt.ps1 << 'EOF'
Get-Service | Where-Object { $_.Name -like 'bth*' } | Format-Table Name, Status
EOF
powershell -File /tmp/bt.ps1
```
