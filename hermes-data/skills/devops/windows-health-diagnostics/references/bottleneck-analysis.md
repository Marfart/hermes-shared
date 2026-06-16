# 硬件瓶颈分析框架

## 分析链条

拿到完整硬件数据后，按优先级判断瓶颈：

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

## 数据采集方法

### 免提权（HWiNFO64 未装时也能用）

```powershell
# CPU
Get-CimInstance Win32_Processor | Select-Object Name, NumberOfCores, NumberOfLogicalProcessors, MaxClockSpeed

# 内存
(Get-CimInstance Win32_PhysicalMemory | Measure-Object -Property Capacity -Sum).Sum / 1GB

# GPU
Get-CimInstance Win32_VideoController | Select-Object Name, AdapterRAM/1GB

# 磁盘
Get-CimInstance Win32_DiskDrive | Select-Object Model, Size/1GB, InterfaceType

# 主板
Get-CimInstance Win32_BaseBoard | Select-Object Manufacturer, Product
```

⚠️ git-bash 执行 PowerShell 时用 `.ps1` 文件或单引号 EOF，不要用双引号字符串内联 E (`$_` 会被 bash 吃掉)。

### 管理员权限（需要 HWiNFO64）

用 HWiNFO64 + CUA driver 生成完整 HTML 报告（含温度/电压/风扇/频率传感器数据），见 SKILL.md 中的「CUA 驱动 GUI 交互流程」。

## 2026 年办公电脑分级

| 级别 | 代表配置 | 说明 |
|:-----|:---------|:-----|
| D+ / C- | i5-10400, 16GB DDR4, SATA SSD, UHD 630 | 5年前中低端，到淘汰边缘 |
| C / C+ | i5-12xxx, 16GB DDR4, NVMe PCIe 3.0 | 勉强能用 |
| B | i5-13xxx/Ultra 5, 32GB DDR5, NVMe PCIe 4.0 | 2026主流办公标配 |
| A | Ultra 7/9, 32-64GB, NVMe PCIe 5.0, 独显 | 高配工作站 |

## 关键速度对比

| 部件 | 你的 | 2026主流 | 差距 |
|:-----|:-----|:---------|:-----|
| SSD | SATA ~550 MB/s | NVMe PCIe 4.0 ~7,000 MB/s | **13x** |
| 内存 | DDR4-2666 16GB | DDR5-5600 32GB | 2x容量+2x速度 |
| CPU | 6C/12T 14nm | 10-14C 大小核 7nm | 单核快 50-70% |
| GPU | UHD 630 集显 | Intel Arc / Iris Xe | 图形性能翻倍+AV1硬解 |

## 各瓶颈花多少钱能解决

| 问题 | 方案 | 花费 | 效果 |
|:-----|:-----|:-----|:-----|
| 内存不够 | 加 DDR4 16GB | ~¥150 | 立竿见影 |
| 硬盘慢 | 换 NVMe SSD 512GB | ~¥300 | 开机/加载快 3-5x |
| CPU 降频 | ThrottleStop 优化 | ¥0 | +15-25% |
| 温度高 | 换塔式散热器 | ~¥100 | 温度降 10-15°C |
