$p = Get-Process -Id 29984
Write-Host ("PID: " + $p.Id)
Write-Host ("Name: " + $p.ProcessName)
Write-Host ("CPU: " + [math]::Round($p.CPU, 4))
Write-Host ("Start: " + $p.StartTime)
Write-Host ("Threads: " + $p.Threads.Count)
Write-Host ("Responding: " + $p.Responding)