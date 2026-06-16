# Check user lock/unlock and switch events
$events = Get-WinEvent -FilterHashtable @{LogName='Security'; ID=4800,4801,4802,4803,4647,4778,4779} -MaxEvents 20
$out = @()
$lookup = @{
    4800 = '工作站锁定(Lock)'
    4801 = '工作站解锁(Unlock)'
    4802 = '屏幕保护启动(Screensaver)'
    4803 = '屏幕保护关闭(Screensaver off)'
    4647 = '用户主动注销(Logoff)'
    4778 = '会话重连(Reconnect)'
    4779 = '会话断开(Disconnect)'
}
foreach ($e in $events) {
    $desc = $lookup[$e.Id]
    if (-not $desc) { $desc = 'ID:' + $e.Id }
    $user = ''
    if ($e.Properties.Count -gt 0) { $user = $e.Properties[0].Value }
    $out += ($e.TimeCreated.ToString('yyyy-MM-dd HH:mm:ss') + ' | ' + $desc + ' | ' + $user)
}
$out | Out-File C:\Users\Admin\Desktop\session_log.txt -Encoding UTF8
