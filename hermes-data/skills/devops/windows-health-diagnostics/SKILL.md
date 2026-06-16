---
name: windows-health-diagnostics
description: "Windows PC 健康诊断 — RAM/磁盘/进程检查，加速优化建议。纯 Python stdlib + ctypes，不依赖 tasklist/wmic（git-bash 下不可靠）。"
version: 1.0.0
author: Tachikoma
platforms: [windows]
trigger: "电脑变慢|电脑卡|查看内存|磁盘空间|加速|优化|系统诊断|健康检查"
---

# Windows 健康诊断

扫描 Windows PC 的 **RAM / 磁盘 / 进程** 状态，定位卡顿根因并给出优化建议。所有诊断用纯 Python stdlib + ctypes Win32 API，不在 git-bash 下调 tasklist/wmic（已知会永久超时）。

## 脚本

`scripts/speed_diagnosis.py` — 一键诊断脚本

```bash
python speed_diagnosis.py
```

输出：内存总量/使用率、各分区磁盘空间、内存大户 TOP15、优化建议。

## 诊断项目

| 类别 | 方法 | 可靠度 |
|:-----|:-----|:-------|
| RAM 总量/剩余 | `ctypes.GlobalMemoryStatusEx` | ✅ 100% |
| RAM 使用率 | `MEMORYSTATUSEX.dwMemoryLoad` | ✅ 100% |
| 磁盘空间 | `shutil.disk_usage("C:\\")` | ✅ 100% |
| 进程列表 | `wmic process get Name,WorkingSet64` | ⚠️ 可能超时 |
| CPU 核心数 | `os.cpu_count()` | ✅ 100% |
| 开机时间 | `ctypes.GetTickCount64() // 1000` | ✅ 100% |

## 优化方案清单

### 内存不足（占用 >85% — 卡顿主因）

1. `Ctrl+Shift+Esc` → 进程 → 按内存排序 → 关掉不需要的
2. 任务管理器 → 启动 → 禁用不必要的开机自启
3. 微信/网易云/Chrome 浏览器每个标签页 200-500MB，用完退出
4. **终极方案：加内存条**（DDR4 笔记本 16GB ≈ 200元）

### C 盘空间不足

1. `Win+R → cleanmgr`（磁盘清理 → 清理系统文件）
2. **管理员 CMD: `powercfg -h off`**（关闭休眠，释放 ~4GB）
3. 把桌面大文件移到 D 盘（D 盘一般空间充足）
4. 微信文件存储路径改到 D 盘

### 执行方案

```bash
# 关闭休眠（管理员）
powercfg -h off

# 磁盘清理
cleanmgr

# 只查磁盘
python -c "import shutil; t,u,f=shutil.disk_usage('C:\\'); g=1024**3; print(f'C: {t/g:.0f}G total, {u/g:.0f}G used, {f/g:.0f}G free, {u/t*100:.0f}%')"
```

## 硬件深度诊断 — HWiNFO64

基础健康诊断不够用时要深入温度/电压/风扇转速，需要 HWiNFO64。

### 安装

```powershell
# HWiNFO 官网被 Cloudflare 屏蔽，用 SAC 镜像下载便携版
# https://www.sac.sk/download/utildiag/hwi_848.zip
# 解压即可用，含 HWiNFO32.exe + HWiNFO64.exe + HWiNFO_ARM64.exe
```

### 权限要求

- HWiNFO64 **必须管理员权限**（Error 740: 请求的操作需要提升）
- 因访问硬件传感器（CPU温度/电压/风扇）需要 Ring 0 级驱动
- 普通用户 WMI 只能读到 CPU/GPU/内存基础信息，读不到温度

### 不借助 HWiNFO 能读到什么

PowerShell WMI 可以在无需管理员权限下获取：

```powershell
# CPU 详细信息
Get-CimInstance Win32_Processor | Select-Object Name, NumberOfCores, NumberOfLogicalProcessors, MaxClockSpeed, L2CacheSize, L3CacheSize

# 内存总量
(Get-CimInstance Win32_PhysicalMemory | Measure-Object -Property Capacity -Sum).Sum

# GPU 信息（不含温度）
Get-CimInstance Win32_VideoController | Select-Object Name, AdapterRAM, DriverVersion

# 主板型号
Get-CimInstance Win32_BaseBoard | Select-Object Manufacturer, Product

# 电池状态
Get-CimInstance Win32_Battery | Select-Object EstimatedChargeRemaining, BatteryStatus

# 网卡信息
Get-CimInstance Win32_NetworkAdapter | Where-Object { $_.NetEnabled } | Select-Object Name, Speed, MACAddress

# 磁盘型号
Get-CimInstance Win32_DiskDrive | Select-Object Model, Size, InterfaceType
```

**限制**: `Get-CimInstance` 在 git-bash 中直接执行时 `$_.` 会被 bash 吃掉变量引用。必须：
- 写入 `.ps1` 文件后用 `powershell -File` 执行
- 或用 `cat << 'EOF'` 风格（**单引号** EOF 阻止变量展开）

### 温度/电压数据获取方案（需要管理员）

| 工具 | 方式 | 数据 |
|:-----|:-----|:-----|
| HWiNFO64 | GUI → Sensors-only | 全量传感器（温度/电压/风扇/频率） |
| OpenHardwareMonitor | WMI (root\OpenHardwareMonitor) | 部分温度/电压，需先安装服务 |
| LibreHardwareMonitor | WMI (root\LibreHardwareMonitor) | OHM 开源替代，需安装 |
| `wmic /namespace` | 某些主板厂商提供 WMI 温度接口 | 不可靠，取决于 BIOS |

## 关键教训

- **不要**用 `tasklist` / `wmic process` 查进程 — git-bash 下永久超时
- **不要**用 `python -c` 内联写 Windows 路径（反斜杠被 MSYS 吞掉）——改写成脚本文件执行
- HWiNFO64 等硬件诊断工具需管理员权限（Error 740）——用 PowerShell `Start-Process -Verb RunAs` 提权
- `$_.` 在 bash 的多行字符串（双引号 heredoc）中会被 bash 展开——用 `.ps1` 文件或单引号 heredoc
- D 盘空间充裕时优先把文件迁移过去，而不是删掉
- 通过 `Get-CimInstance Win32_*` 可免提权获取 CPU/GPU/内存/主板/网卡规格

## 硬件深度诊断 — HWiNFO64 HTML 报告生成（CUA 驱动）

通过 CUA 驱动（后台无人值守）操作 HWiNFO64 GUI，生成完整 HTML 报告。不需要人工点击。

### 前置

1. HWiNFO64 已安装并已提权运行（见上文「硬件深度诊断 — HWiNFO64」）
2. CUA 驱动守护进程已在运行

### CUA 驱动 GUI 交互流程

```bash
# 1. 确认 HWiNFO 窗口
cua-driver call --tool list_windows
# → 找到 HWiNFO® 64 的 window_id 和 pid

# 2. 获取窗口 UI 树
cua-driver call --tool get_window_state --json '{"pid":30368,"window_id":3938640}'
# → 返回完整 UIA 树，所有交互元素带 element_index

# 3. 点击 "Create a Report File"（索引因版本而异）
cua-driver call --tool click --json '{"pid":30368,"window_id":3938640,"element_index":14}'

# 4. 选择 HTML 格式
cua-driver call --tool click --json '{"pid":30368,"window_id":3938640,"element_index":3}'

# 5. 下一页 → 完成
cua-driver call --tool click --json '{"pid":30368,"window_id":3938640,"element_index":16}'
cua-driver call --tool click --json '{"pid":30368,"window_id":3938640,"element_index":18}'

# 6. 读取生成的报告
# 默认路径: HWiNFO64 目录下 PS2022MIXSNJQO.HTM（主机名.HTM）
```

### UIA 树结构关键元素

| 功能 | 操作 | 备注 |
|------|------|------|
| 首页按钮 | element_index 根据版本浮动 | 用 get_window_state 确认索引 |
| "Create a Report File" | 首页按钮之一 | 点击后打开创建日志文件对话框 |
| HTML 格式 | 对话框内按钮 | 选 HTML 生成完整报告 |
| 下一页 / 完成 | 对话框底部按钮 | 先 Next 再 Finish |
| 报告文件 | 默认 `主机名.HTM` | 与 HWiNFO64.exe 同目录，~150KB HTML |

### 报告内容解析

HTML 报告约 3000 行，含所有硬件子系统的详细规格。用 Python 的 re.findall 提取关键字段：

```python
import re

with open("PS2022MIXSNJQO.HTM", encoding="utf-8") as f:
    html = f.read()

# 提取关键值
re.findall(r'<TD[^>]*>([^<]*?)<.*?<TD[^>]*>([^<]*?)<', html, re.DOTALL)
# 可提取：主板型号、CPU TDP、最大睿频、内存模块、GPU 型号、磁盘容量等
```

### 提权注意事项

HWiNFO64 需要管理员权限（Error 740）。提权方式：

```powershell
# 方法 1：ShellExecuteW runas（Python）
ctypes.windll.shell32.ShellExecuteW(None, "runas", exe_path, "", None, 0)

# 方法 2：PowerShell Start-Process（但 git-bash 会吃掉 $ 符号）
Start-Process -FilePath "HWiNFO64.exe" -Verb RunAs

# 方法 3：ShellExecute 返回 >32 表示成功启动
# UAC 弹窗会出现在用户桌面上，用户需点击"是"
```

## 瓶颈分析框架

拿到完整硬件数据后，这条分析链判断"电脑瓶颈在哪"：

```
内存占用 >85% ─────────────── → 加内存（DDR4 16GB ≈ ¥150）
                ↓ yes                
CPU 温度 >90°C ─────────────── → 清灰/换散热器/降压
                ↓ yes                
SATA SSD ──────────────────── → 换 NVMe（理论快 5-10x）
                ↓ yes                
无独显 + 集显 UHD 630 ────── → 只影响游戏/视频剪辑/双 4K 外接
                ↓                    
CPU i5-10400 (6C/12T) ────── → 办公够用，不是瓶颈
```

### 2026 年办公电脑分级参考

| 级别 | 配置 | 淘汰状态 |
|:-----|:-----|:---------|
| D+ / C- | i5-10400, 16GB DDR4, SATA SSD, UHD 630 | **你的位置** — 5年前中低端 |
| C / C+ | i5-12xxx, 16GB DDR4, NVMe PCIe 3.0 | 勉强能用 |
| B | i5-13xxx/Ultra 5, 32GB DDR5, NVMe PCIe 4.0 | 2026主流办公 |
| A | Ultra 7/9, 32-64GB, NVMe PCIe 5.0, 独显 | 高配 |

关键对比：你的 SATA SSD（~550MB/s）vs 2026主流 NVMe（~7,000MB/s）= **慢 13 倍**。

## 性能优化工具链

### ThrottleStop — CPU 性能释放（免费，效果最大）

- **效果**：+10-25%（通过解除降频 + 锁定睿频）  
- **⚠️ 零蓝屏偏好**：本用户要求绝对安全。降压等灰色操作用户说了才能做。
- **下载**：从 TechPowerUp 或 Uptodown 下载 `.zip`，解压即用  
- **Uptodown Playwright 下载**：接受 Cookie → 点 Download → 文件在 `~/.playwright-mcp/`
- **CUA 驱动自动化**：`references/throttlestop-safe-config.md` 有完整的无人值守配置流程（主窗口 → FIVR → Options → Turn On）

### ThrottleStop 安全配置（i5-10400 + H510MHP）

```text
打开 ThrottleStop.exe，主界面：

✅ 安全操作（基本无害，可以直接做）：
  1. 勾选 Set Multiplier → 填 43（锁定最高 4.3GHz 睿频）
  2. 勾选 Speed Shift → EPP 拉到 0（偏向性能）
  3. 取消勾选 BD PROCHOT（阻止主板误报温度降频）

⚠️ 灰色操作（必须用户开口才能做）：
  4. FIVR → CPU Core / Cache 偏移电压 -50mV（降压降温）
     — 用户说"不能有蓝屏的可能性，必须安全"时必须回退
  → 回退方法：FIVR → Zero Offset → "OK - Do not save voltages"

🔴 不作死操作（别在你这台做）：
  5. 拉高 PL1 功耗墙 — 原装散热器压不住 85W+
  6. 加核心电压 — 可能损坏 CPU
  7. 全程禁用 C-State — 加速老化
```

**效果预测**：关 BD PROCHOT（+5-10%）+ 锁睿频（+10-15%）+ 降压（降 3-5°C）= 综合提升 **15-25%**。

**自启设置**：Options → Start Minimized → 设为开机启动。

### 性能优化工具全对比

| 工具 | 用途 | 安全等级 | 对你的效果 | 下载 |
|:-----|:-----|:---------|:-----------|:-----|
| **ThrottleStop** | CPU 解功耗墙+降压 | 🟢 安全操作 ✅ | **+15-25%** | 首选 |
| Intel XTU | Intel 官方调优 | 🟢✅ | 功能重叠，不如 TS | 微软商店 |
| Process Lasso | CPU 调度优化 | 🟢✅ | 多开时不卡 | freeware |
| QuickCPU | 电源调度 | 🟢✅ | 替代品，轻量 | freeware |
| MSI Afterburner | 监控+轻量超频 | 🟡⚠️ | 集显没必要 | freeware |
| Razer Cortex | 一键释放内存 | 🟢✅ | 偶尔有用 | free |
| **卓越性能电源** | 系统自带 | 🟢✅ | +5-10% 不花钱 | 系统自带 |
| **关视觉效果** | 系统自带 | 🟢✅ | 省 300MB 内存 | 系统自带 |
| **关 SysMain** | 系统自带 | 🟢✅ | SSD 上反而快 | 系统自带 |

### 不花钱先做的优化（效果大）

```powershell
# 1. 开启卓越性能电源
powercfg -duplicatescheme e9a42b02-d5df-448d-aa00-03f14749eb61
# 控制面板 → 电源选项 → 选"卓越性能"

# 2. 关 SysMain（Superfetch），SSD 上反而拖慢
sc stop SysMain
sc config SysMain start=disabled

# 3. 关视觉效果：系统属性 → 高级 → 性能 → 调整为最佳性能
# 可释放 300-500MB 内存
```

### 硬件瓶颈真实物理限制

| 瓶颈 | 优化能救 | 必须花钱换 |
|:-----|:---------|:-----------|
| SATA SSD 550MB/s | ❌ 优化不了 | ✅ 换 NVMe（¥300） |
| 16GB 内存吃满 | ⚠️ 关软件能省几百 MB | ✅ 加 16GB（¥150） |
| UHD 630 集显 | ❌ 只能降低画质 | ✅ 加独显（¥500+） |
| CPU 频率受限 | ✅ ThrottleStop 解 15-25% | 还可再战 2 年 |

## Cron 定时监控脚本（no_agent 模式）

Hermes 的 cron 调度器支持 `no_agent=True` 模式——零 token 消耗，纯系统级脚本定时运行。

### 适用场景

- 周期性健康检查（磁盘/内存/网络）
- 看门狗模式（只在异常时静默报告）
- 阈值告警（当 X > Y 时发通知）

### 创建定时看门狗

```bash
cronjob action=create name="系统健康检查" schedule="every 5m" \
  no_agent=true script=health_check.py deliver=origin
```

- `no_agent=true` — 不调用 LLM，纯跑脚本
- `script` — 相对于 `%LOCALAPPDATA%/hermes/scripts/` 的路径
- `deliver=origin` — 输出到当前会话；`all` → 全平台

### 运行逻辑（看门狗模式）

脚本正常时保持静默（`print("")` 或不打印），异常时才输出报告。
cron 只传递非空 stdout。设计原则：**安静 = 正常，有输出 = 有问题**。

### Windows 中文编码陷阱

**⚠️ Python 脚本在 Windows cron 下输出中文会乱码。**

根因：cron 的 no_agent 模式用 `subprocess` 捕获 stdout，Windows 默认系统编码为 **cp936(GBK)**。即使脚本设了 `encoding='utf-8'`，cron 仍用 cp936 解码管道输出。

**修复：**

```python
# 脚本最前面（模块级别，import 之后）
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='gbk')
```

同时 **替换所有 emoji**（❌✅🔧🔐⏱️📊📋⚠️💥⚡🔄⛔），因为 GBK 不支持 emoji，会触发 `UnicodeEncodeError`。详见 `references/cron-noagent-encoding-fix.md`。

### 看门狗脚本生命周期

```bash
# 查看所有 cron 任务
cronjob action=list

# 手动跑一次
cronjob action=run job_id=<ID>

# 暂停
cronjob action=pause job_id=<ID>

# 删除
cronjob action=remove job_id=<ID>
```

## Windows 蓝屏/崩溃诊断（BugCheck 分析）

当用户报告"电脑突然重启"或"报错重启"时，按以下流程诊断：

### 快速诊断流程

```powershell
# 1. 查最近2小时系统错误+关键事件
Get-WinEvent -FilterHashtable @{LogName='System'; Level=1,2; StartTime=(Get-Date).AddHours(-2)} -MaxEvents 30

# 2. 查蓝屏转储记录（BugCheck Event 1001）
Get-WinEvent -FilterHashtable @{LogName='System'; Id=1001; StartTime=(Get-Date).AddHours(-2)}

# 3. 查意外关机记录（Kernel-Power Event 41）
Get-WinEvent -FilterHashtable @{LogName='System'; ProviderName='Microsoft-Windows-Kernel-Power'; StartTime=(Get-Date).AddHours(-2)}
```

### 关键 Event ID 速查

| Event ID | 来源 | 含义 |
|:--------:|:-----|:-----|
| 41 | Kernel-Power | 系统未正常关机（蓝屏/断电/死机） |
| 1001 | BugCheck | 蓝屏转储写入，含 BugCheck 代码和 dump 文件路径 |
| 6008 | EventLog | "上一次关机是意外的"（比41更精确的崩溃时间） |
| 1076 | USER32 | 用户手动触发重启 |
| 161 | BugCheck | 转储文件写入失败（内存不足或磁盘空间不够） |

### 常见 BugCheck 代码

| 代码 | 名称 | 常见原因 |
|:----:|:-----|:---------|
| 0x18 | REFERENCE_BY_POINTER | 内核引用无效对象指针，常为驱动bug或内存损坏 |
| 0x0A | IRQL_NOT_LESS_OR_EQUAL | 驱动访问了错误权限的内存 |
| 0x3B | SYSTEM_SERVICE_EXCEPTION | 系统服务异常，驱动或硬件问题 |
| 0x50 | PAGE_FAULT_IN_NONPAGED_AREA | 内存损坏或驱动bug |
| 0xD1 | DRIVER_IRQL_NOT_LESS_OR_EQUAL | 驱动IRQL不匹配 |
| 0xEF | CRITICAL_PROCESS_DIED | 关键系统进程崩溃 |
| 0x133 | DPC_WATCHDOG_VIOLATION | DPC超时，驱动卡死 |
| 0x139 | KERNEL_SECURITY_CHECK_FAILURE | 内核安全检查失败 |

### 2026-06-15 实战案例：0x18 REFERENCE_BY_POINTER

**时间线：**
- 10:15:17 上一次意外关机（Event 6008）
- 10:26:38 蓝屏（Event 41），BugCheck 0x18
- 10:26:46 转储写入 `C:\WINDOWS\Minidump\061526-11781-01.dmp`（Event 1001）
- 10:28:43 系统准备重启（Kernel-Power 109, Reason=Kernel API）
- 10:31:01 多个服务启动失败（ovpnhelper_service, AliPaladin）

**根因：** AliPaladin（阿里巴巴安全/反盗版内核驱动）与 ovpnhelper_service（OpenVPN驱动）同时运行触发驱动冲突。AliPaladin 在 10:26:48 启动失败（"设备没有正常运行"），与蓝屏时间高度吻合。kis_service.exe（金蝶KIS云客户端）也崩溃（0xc0000005 访问违例）。

**结论：** 多个内核级驱动（阿里安全+OpenVPN+金蝶）在同一系统上冲突 → 0x18 无效指针引用 → 蓝屏。建议禁用不常用的内核驱动服务（AliPaladin、ovpnhelper_service）。

### Dump 文件分析

转储文件位于 `C:\Windows\Minidump\`（小内存转储）或 `C:\Windows\MEMORY.DMP`（完整转储）。需要管理员权限访问。用 WinDbg 或 BlueScreenView 分析：

```
# WinDbg 分析命令（打开 .dmp 后）
!analyze -v
```

## 网络代理 API 诊断

当 LLM provider / API 连不上时，可能是 Vortex 代理（`127.0.0.1:7897`）在损坏 HTTPS 请求。

**快速判断**：`curl --noproxy "*"` 直连正常 vs `curl -x 127.0.0.1:7897` 报 401 Unauthorized = 代理 HTTPS 转发损坏。

详见 `references/proxy-api-diagnostics.md` — 三步诊断法 + 4 种修复方案。

## 关联技能

- `python-script-craftsmanship` → 模式 Z（Windows 诊断工具替代策略）和模式 AA（python -c 反斜杠陷阱）
- `file-cleanup-3y` → 旧文件扫描清理
- `self-maintenance` → 自动日常健康检查
- `windows-system-forensics` → 系统日志调查
- `cua-driver-rs` → CUA 驱动 GUI 自动化，用于无人值守操作 HWiNFO64/ThrottleStop（`references/windows-admin-launch.md` 有完整流程）

## Reference Files

- `references/python-c-backslash-trap.md` — MSYS 吞反斜杠/花括号的完整分析，含 4 种解决方案
- `references/hwinfo64-setup.md` — HWiNFO64 下载安装、Cloudflare 绕过、SAC 镜像
- `references/bottleneck-analysis.md` — 硬件瓶颈分析框架、性能分级对比、工具链对比表
- `references/throttlestop-safe-config.md` — ThrottleStop 下载安装、安全配置步骤、BD PROCHOT/降压/自启详细说明
- `references/cron-noagent-encoding-fix.md` — Windows cron 中文编码修复方案（GBK vs UTF-8 陷阱 + emoji 替换规则 + 验证方法）
- `scripts/wmi_hardware_info.ps1` — 免提权硬件信息一键收集脚本（CPU/GPU/内存/主板/磁盘/网卡）