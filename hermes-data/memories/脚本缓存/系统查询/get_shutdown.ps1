$events = Get-WinEvent -FilterHashtable @{LogName='System'; ID=1074,6006} -MaxEvents 10
$out = @()
foreach ($e in $events) {
    $out += ($e.TimeCreated.ToString('yyyy-MM-dd HH:mm:ss') + ' | ID:' + $e.Id)
}
$out | Out-File C:\Users\Admin\Desktop\shutdown_log.txt -Encoding UTF8
