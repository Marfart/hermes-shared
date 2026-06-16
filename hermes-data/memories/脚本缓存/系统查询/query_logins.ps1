# Get last 50 interactive logon events (Event ID 4624, Logon Type 2=interactive, 10=remote)
Write-Host "=== 最近登录记录 ===" -ForegroundColor Cyan

$events = Get-WinEvent -FilterHashtable @{LogName='Security'; ID=4624} -MaxEvents 50
foreach ($evt in $events) {
    $time = $evt.TimeCreated.ToString('yyyy-MM-dd HH:mm:ss')
    $userId = $evt.Properties[5].Value
    $logonType = $evt.Properties[8].Value
    $typeName = switch ($logonType) {
        2 {'交互式(Interactive)'}
        10 {'远程(RemoteInteractive)'}
        default {"其他($logonType)"}
    }
    # Only show interactive logons
    if ($logonType -eq 2 -or $logonType -eq 10) {
        Write-Host "$time | $userId | $typeName"
    }
}

Write-Host ""
Write-Host "=== 关机/睡眠事件 (Event ID 42/1074/6006) ===" -ForegroundColor Cyan
$shutdownEvents = Get-WinEvent -FilterHashtable @{LogName='System'; ID=42,1074,6006} -MaxEvents 10
foreach ($evt in $shutdownEvents) {
    $time = $evt.TimeCreated.ToString('yyyy-MM-dd HH:mm:ss')
    $msg = $evt.Message -replace "`n"," " -replace "`r",""
    Write-Host "$time | $($evt.Id) | $($msg.Substring(0, [Math]::Min(100, $msg.Length)))"
}
