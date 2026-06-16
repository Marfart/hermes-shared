# Get boot events (ID 12=OS boot, ID 13=shutdown) or 6005=event log started
$events = Get-WinEvent -FilterHashtable @{LogName='System'; ID=6005,12} -MaxEvents 5
$out = @()
foreach ($e in $events) {
    $out += ($e.TimeCreated.ToString('yyyy-MM-dd HH:mm:ss') + ' | ID:' + $e.Id + ' | ' + $e.LevelDisplayName)
}
$out | Out-File C:\Users\Admin\Desktop\boot_log.txt -Encoding UTF8
