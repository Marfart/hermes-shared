# 电脑活动完整报告 - 昨天(5/28) + 今天(5/29)
$reportFile = [System.IO.Path]::GetTempFileName() + "_report.txt"
$out = New-Object System.Collections.ArrayList

[void]$out.Add("==========================================")
[void]$out.Add("  电脑活动完整报告")
[void]$out.Add("  2026-05-28 (昨天) ~ 2026-05-29 (今天)")
[void]$out.Add("==========================================")
[void]$out.Add("")

# -- 1. 开机/关机记录 --
[void]$out.Add("=== [开机/关机] ===")
$bootDesc = @{12="开机(Boot)"; 13="关机(Shutdown)"; 6005="日志服务启动"; 6006="日志服务停止(关机)"; 1074="用户关机/重启"}
try {
    $bootEvents = Get-WinEvent -FilterHashtable @{LogName='System'; ID=12,13,6005,6006,1074} -MaxEvents 30
    foreach ($e in $bootEvents) {
        $t = $e.TimeCreated.ToString('yyyy-MM-dd HH:mm:ss')
        $d = $bootDesc[$e.Id]
        if (-not $d) { $d = "ID:$($e.Id)" }
        if ($e.TimeCreated -ge (Get-Date '2026-05-28')) {
            [void]$out.Add("$t | $d")
        }
    }
} catch { [void]$out.Add("  (获取失败: $($_.Exception.Message))") }
[void]$out.Add("")

# -- 2. 用户登录 --
[void]$out.Add("=== [用户登录] 仅显示交互式=2和远程=10 ===")
$loginType = @{2="交互式(Interactive)"; 5="服务(Service)"; 10="远程(Remote)"}
try {
    $logins = Get-WinEvent -FilterHashtable @{LogName='Security'; ID=4624} -MaxEvents 150
    foreach ($e in $logins) {
        $t = $e.TimeCreated.ToString('yyyy-MM-dd HH:mm:ss')
        $user = $e.Properties[5].Value
        $type = $e.Properties[8].Value
        $typeName = $loginType[[int]$type]
        if (-not $typeName) { $typeName = "类型$type" }
        $isInteract = ($type -eq 2 -or $type -eq 10)
        if ($isInteract -and ($e.TimeCreated -ge (Get-Date '2026-05-28'))) {
            [void]$out.Add("$t | $user | $typeName")
        }
    }
} catch { [void]$out.Add("  (获取失败: $($_.Exception.Message))") }
[void]$out.Add("")

# -- 3. 锁定/解锁/注销 --
[void]$out.Add("=== [锁定/解锁/注销] ===")
$evtDesc = @{4800="工作站锁定(Lock)"; 4801="工作站解锁(Unlock)"; 4647="用户注销(Logoff)"}
try {
    $sessionEvents = Get-WinEvent -FilterHashtable @{LogName='Security'; ID=4800,4801,4647} -MaxEvents 50
    foreach ($e in $sessionEvents) {
        $t = $e.TimeCreated.ToString('yyyy-MM-dd HH:mm:ss')
        $d = $evtDesc[$e.Id]
        if ($e.TimeCreated -ge (Get-Date '2026-05-28')) {
            [void]$out.Add("$t | $d")
        }
    }
} catch { [void]$out.Add("  (获取失败: $($_.Exception.Message))") }
[void]$out.Add("")

# -- 4. 当前状态 --
[void]$out.Add("=== [当前系统状态] ===")
try {
    $boot = (Get-CimInstance Win32_OperatingSystem).LastBootUpTime
    $uptime = (Get-Date) - $boot
    [void]$out.Add("开机时间: $($boot.ToString('yyyy-MM-dd HH:mm:ss'))")
    [void]$out.Add("已运行: $($uptime.Days)天 $($uptime.Hours)小时 $($uptime.Minutes)分钟")
    [void]$out.Add("当前用户: $env:USERNAME")
} catch { [void]$out.Add("  (获取失败)") }

[void]$out.Add("")
[void]$out.Add("==========================================")

# Write to file
$out -join "`r`n" | Set-Content $reportFile -Encoding UTF8
Write-Output "REPORT_FILE:$reportFile"
