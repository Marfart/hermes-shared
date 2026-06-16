$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\CuaDriver.lnk")
$Shortcut.TargetPath = "$env:LOCALAPPDATA\Programs\Cua\cua-driver\bin\cua-driver.exe"
$Shortcut.Arguments = "serve"
$Shortcut.WorkingDirectory = "$env:USERPROFILE\.cua-driver"
$Shortcut.WindowStyle = 7
$Shortcut.Description = "Cua Driver Background Computer-Use Agent - Autostart"
$Shortcut.Save()
Write-Host "Startup shortcut created at: $env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\CuaDriver.lnk" -ForegroundColor Green

# Also try autostart enable one more time
$cua = "$env:LOCALAPPDATA\Programs\Cua\cua-driver\bin\cua-driver.exe"
Write-Host "Checking autostart status..." -ForegroundColor Yellow
& $cua autostart status
