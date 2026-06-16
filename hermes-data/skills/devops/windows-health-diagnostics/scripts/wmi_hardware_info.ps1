<#
.SYNOPSIS
    免提权收集 Windows 硬件信息（CPU/内存/GPU/主板/磁盘/网卡）
.DESCRIPTION
    全部用 Get-CimInstance 读取 WMI，不需管理员权限。
    可用于快速了解机器硬件配置。
.NOTES
    在 git-bash 中必须用 powershell -File 运行此脚本，
    不可用内联字符串避免 $_. 被 bash 展开。
#>

$ErrorActionPreference = "SilentlyContinue"

Write-Output "===== CPU ====="
$cpu = Get-CimInstance Win32_Processor
Write-Output "Model: $($cpu.Name)"
Write-Output "Cores: $($cpu.NumberOfCores) / Threads: $($cpu.NumberOfLogicalProcessors)"
Write-Output "Max Clock: $($cpu.MaxClockSpeed) MHz"
Write-Output "L2 Cache: $($cpu.L2CacheSize) KB / L3 Cache: $($cpu.L3CacheSize) KB"

Write-Output "`n===== Memory ====="
$totalMem = (Get-CimInstance Win32_PhysicalMemory | Measure-Object -Property Capacity -Sum).Sum
$os = Get-CimInstance Win32_OperatingSystem
$usedGB = [math]::Round(($totalMem/1GB) - ($os.FreePhysicalMemory/1MB/1024), 1)
$pct = [math]::Round(($totalMem - $os.FreePhysicalMemory*1024)/$totalMem*100, 1)
Write-Output "Total: $([math]::Round($totalMem/1GB, 1)) GB"
Write-Output "Used: $usedGB GB / Free: $([math]::Round($os.FreePhysicalMemory/1MB, 1)) GB ($pct%)"

Write-Output "`n===== GPU ====="
$gpus = Get-CimInstance Win32_VideoController
foreach ($gpu in $gpus) {
    $vram = if ($gpu.AdapterRAM) { "$([math]::Round($gpu.AdapterRAM/1GB, 2)) GB" } else { "N/A" }
    Write-Output "$($gpu.Name): VRAM=$vram, Driver=$($gpu.DriverVersion)"
}

Write-Output "`n===== Motherboard ====="
$board = Get-CimInstance Win32_BaseBoard
Write-Output "$($board.Manufacturer) $($board.Product)"

Write-Output "`n===== Disks ====="
$disks = Get-CimInstance Win32_DiskDrive
foreach ($d in $disks) {
    Write-Output "$($d.Model): $([math]::Round($d.Size/1GB, 1)) GB, $($d.InterfaceType)"
}

Write-Output "`n===== Storage ====="
$vols = Get-CimInstance Win32_LogicalDisk -Filter "DriveType=3"
foreach ($v in $vols) {
    $p = [math]::Round(($v.Size-$v.FreeSpace)/$v.Size*100, 1)
    Write-Output "$($v.DeviceID): $([math]::Round($v.FreeSpace/1GB,1))/$([math]::Round($v.Size/1GB,1)) GB ($p%)"
}

Write-Output "`n===== Battery ====="
$batt = Get-CimInstance Win32_Battery
if ($batt) { Write-Output "$($batt.EstimatedChargeRemaining)% remaining" }
else       { Write-Output "(no battery - desktop)" }

Write-Output "`n===== Network ====="
$nets = Get-CimInstance Win32_NetworkAdapter | Where-Object { $_.NetEnabled }
foreach ($n in $nets) {
    $speed = if ($n.Speed) { "$([math]::Round($n.Speed/1MB, 0)) Mbps" } else { "N/A" }
    Write-Output "$($n.Name): $speed, MAC=$($n.MACAddress)"
}
