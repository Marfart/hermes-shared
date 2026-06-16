# 电脑小卫士 v2 (全面监控)
# 由 cron job (job_id=6882df9f6b5c) 每2分钟调用
# 检测: 重启/新登录/屏幕解锁/USB接入/远程连接/唤醒/人机活动
# no_agent=True 模式：有警报才输出

param(
    [string]$StateFile = ""
)

# 如果 cron 环境不给 LOCALAPPDATA，写死路径
if (-not $StateFile) {
    $StateFile = "$env:LOCALAPPDATA\hermes\memories\scripts_cache\guard_state.json"
    if (-not $env:LOCALAPPDATA) {
        $StateFile = "C:\Users\Admin\AppData\Local\hermes\memories\scripts_cache\guard_state.json"
    }
}

# 读取状态
if (Test-Path $StateFile) {
    $state = Get-Content $StateFile -Raw -Encoding UTF8 | ConvertFrom-Json
} else {
    $state = [PSCustomObject]@{
        armed = $false
        lastBoot = ""
        knownSessions = @()
        notifiedBoot = $false
        notifiedSessions = @()
        notifiedUnlocks = @()
        notifiedUSB = @()
        notifiedRemoteDesktop = @()
        version = 2
    }
}

# 如果没布防，啥也不做
if (-not $state.armed) {
    exit 0
}

$output = @()

# ===== 1. 重启检测 =====
try {
    $boot = (Get-CimInstance Win32_OperatingSystem).LastBootUpTime
    $bootStr = $boot.ToString('yyyy-MM-dd HH:mm:ss')
    if ($state.lastBoot -and $state.lastBoot -ne $bootStr -and -not $state.notifiedBoot) {
        $output += "⚠️ 电脑防｜系统重启"
        $output += "上次启动: $($state.lastBoot)"
        $output += "本次启动: $bootStr"
        $output += "你还没说『我回来了』——请确认是你本人操作"
        $state.notifiedBoot = $true
    }
    $state.lastBoot = $bootStr
} catch { }

# ===== 2. 新登录检测 =====
try {
    $sessions = Get-CimInstance Win32_LogonSession -Filter "LogonType=2 OR LogonType=10" -ErrorAction SilentlyContinue
    $currentSessions = @()
    foreach ($s in $sessions) {
        if ($s.UserName -and $s.UserName -ne "" -and $s.UserName -notlike "DWM-*" -and $s.UserName -notlike "UMFD-*") {
            $startStr = $s.StartTime.ToString('yyyy-MM-dd HH:mm:ss')
            $key = "$($s.UserName)|$startStr"
            $currentSessions += $key
            if ($state.knownSessions -notcontains $key -and $state.notifiedSessions -notcontains $key) {
                $output += "⚠️ 电脑卫士｜新用户登录"
                $output += "用户: $($s.UserName) 时间: $startStr"
                $state.notifiedSessions += @($key)
            }
        }
    }
    $allKnown = @($state.knownSessions) + $currentSessions
    $state.knownSessions = @($allKnown | Select-Object -Unique)
    if ($state.knownSessions.Count -gt 100) {
        $state.knownSessions = $state.knownSessions[-80..-1]
    }
} catch { }

# ===== 3. 屏幕解锁检测 (工作站解锁事件 4801) =====
try {
    $unlockEvents = Get-WinEvent -FilterHashtable @{LogName='Security'; ID=4801} -MaxEvents 5 -ErrorAction SilentlyContinue
    foreach ($evt in $unlockEvents) {
        $t = $evt.TimeCreated.ToString('yyyy-MM-dd HH:mm:ss')
        $key = "unlock|$t"
        if ($state.notifiedUnlocks -notcontains $key) {
            $output += "⚠️ 电脑卫士｜屏幕被唤醒解锁"
            $output += "时间: $t  —— 有人操作了电脑"
            $state.notifiedUnlocks += @($key)
        }
    }
} catch { }

# ===== 4. USB 存储设备检测 =====
try {
    # 读取USBSTOR注册表
    $usbKey = "HKLM:\SYSTEM\CurrentControlSet\Enum\USBSTOR"
    if (Test-Path $usbKey) {
        $usbDevices = Get-ChildItem $usbKey -ErrorAction SilentlyContinue
        foreach ($dev in $usbDevices) {
            $devName = $dev.PSChildName
            # 检查该USB设备的序列号子项
            $serials = Get-ChildItem "$usbKey\$devName" -ErrorAction SilentlyContinue
            foreach ($ser in $serials) {
                $serialKey = "$usbKey\$devName\$($ser.PSChildName)"
                $friendly = (Get-ItemProperty $serialKey -Name "FriendlyName" -ErrorAction SilentlyContinue).FriendlyName
                $serialStr = $ser.PSChildName
                $notifyKey = "usb|$devName|$serialStr"
                if ($state.notifiedUSB -notcontains $notifyKey) {
                    $output += "⚠️ 电脑卫士｜USB存储设备接入"
                    $output += "设备: $($friendly -replace '^(Msft ).*','$1 ')"
                    $output += "序列号: $serialStr"
                    $state.notifiedUSB += @($notifyKey)
                }
            }
        }
    }
} catch { }

# ===== 5. 远程桌面/3389 连接检测 =====
try {
    # 检查是否有RDP监听和活动会话
    $rdpKey = "HKLM:\SYSTEM\CurrentControlSet\Control\Terminal Server"
    if (Test-Path $rdpKey) {
        $rdpEnabled = (Get-ItemProperty $rdpKey -Name "fDenyTSConnections" -ErrorAction SilentlyContinue).fDenyTSConnections
        if ($rdpEnabled -eq 0) {
            # RDP已启用 - 检查活动会话
            $rdpSessions = Get-CimInstance Win32_TerminalServiceSession -ErrorAction SilentlyContinue | Where-Object { $_.UserName -and $_.UserName -ne "" -and $_.SessionId -gt 0 }
            foreach ($rs in $rdpSessions) {
                $key = "rdp|$($rs.UserName)|$($rs.SessionId)"
                if ($state.notifiedRemoteDesktop -notcontains $key) {
                    $output += "⚠️ 电脑卫士｜远程桌面活动连接"
                    $output += "用户: $($rs.UserName) 会话ID: $($rs.SessionId)"
                    $state.notifiedRemoteDesktop += @($key)
                }
            }
        }
    }
} catch { }

# ===== 6. 最近运行的远程协助软件检测 =====
try {
    $remoteProcs = @('mstsc.exe', 'TeamViewer.exe', 'AnyDesk.exe', 'VNC*.exe', 'TightVNC*.exe', 
                     'todesk.exe', 'SunLoginClient.exe', '向日葵*.exe', 'RDPClip.exe')
    $currentProcs = Get-Process -ErrorAction SilentlyContinue | Select-Object -ExpandProperty ProcessName
    $foundRemote = $false
    foreach ($rp in $remoteProcs) {
        $baseName = $rp -replace '\.exe$', ''
        $wild = $baseName -replace '\*', ''
        $match = $currentProcs | Where-Object { $_ -like "*$wild*" }
        if ($match) {
            $foundRemote = $true
            break
        }
    }
    # 如果发现远程进程运行，记录但只报一次
    if ($foundRemote) {
        $state.remoteSoftwareDetected = $true
        if (-not $state.notifiedRemoteSoftware) {
            $output += "⚠️ 电脑卫士｜检测到远程控制软件正在运行"
            $state.notifiedRemoteSoftware = $true
        }
    } else {
        $state.remoteSoftwareDetected = $false
    }
} catch { }

# ===== 7. 唤醒来源检测 =====
try {
    $lastWake = Get-WinEvent -FilterHashtable @{LogName='System'; ID=1,12,42,107,200} -MaxEvents 3 -ErrorAction SilentlyContinue | Where-Object { $_.Id -eq 1 -or $_.Id -eq 42 -or $_.Id -eq 107 }
    foreach ($w in $lastWake) {
        $t = $w.TimeCreated.ToString('yyyy-MM-dd HH:mm:ss')
        $key = "wake|$t"
        if ($state.notifiedWake -notcontains $key -and $state.notifiedUnlocks -notcontains "unlock|$t") {
            $msg = $w.Message
            $source = if ($msg -match '(Wake Source|原因|Source).*?: (.+?)[\r\n.]') { $matches[2] } else { "未知" }
            $output += "⚠️ 电脑卫士｜系统从睡眠唤醒"
            $output += "时间: $t  来源: $source"
            $state.notifiedWake += @($key)
        }
    }
} catch { }

# ===== 清理旧通知记录 (只保留最近50条) =====
foreach ($prop in @('notifiedSessions', 'notifiedUnlocks', 'notifiedUSB', 'notifiedRemoteDesktop', 'notifiedWake')) {
    if ($state.$prop.Count -gt 50) {
        $state.$prop = @($state.$prop[-50..-1])
    }
}

# ===== 写回状态 =====
$state.version = 2
$json = $state | ConvertTo-Json -Compress
Set-Content -Path $StateFile -Value $json -Encoding UTF8

# ===== 有警报才输出 =====
if ($output.Count -gt 0) {
    Write-Output ($output -join "`n")
}