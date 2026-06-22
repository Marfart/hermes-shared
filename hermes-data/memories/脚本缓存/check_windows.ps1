# 检查所有 conhost 进程及其父进程
Get-Process conhost -ErrorAction SilentlyContinue | ForEach-Object {
    $c = Get-CimInstance Win32_Process -Filter "ProcessId=$($_.Id)" -ErrorAction SilentlyContinue
    if ($c) {
        $parent = Get-Process -Id $c.ParentProcessId -ErrorAction SilentlyContinue
        [PSCustomObject]@{
            ConHostPID = $_.Id
            ParentPID  = $c.ParentProcessId
            ParentName = if ($parent) { $parent.ProcessName } else { "N/A" }
            ParentCmd  = if ($parent) { $parent.Path } else { "N/A" }
        }
    }
} | Format-Table -AutoSize -Wrap

Write-Host "`n--- All processes with windows ---"
Get-Process | Where-Object { $_.MainWindowTitle -ne '' } | 
Select-Object Id, ProcessName, @{N='Title';E={$_.MainWindowTitle}} | 
Format-Table -AutoSize -Wrap

Write-Host "`n--- Recent process starts (last 60s) ---"
Get-Process | Where-Object { $_.StartTime -gt (Get-Date).AddSeconds(-60) } |
Select-Object Id, ProcessName, @{N='Start';E={$_.StartTime.ToString('HH:mm:ss')}} |
Format-Table -AutoSize

Write-Host "Done at $(Get-Date -Format 'HH:mm:ss')"
