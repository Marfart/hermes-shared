# Cua Driver Autostart Installer - Run as Admin
$cua = "$env:LOCALAPPDATA\Programs\Cua\cua-driver\bin\cua-driver.exe"
if (!(Test-Path $cua)) {
    Write-Host "cua-driver.exe not found at $cua" -ForegroundColor Red
    exit 1
}
Write-Host "Found cua-driver at: $cua" -ForegroundColor Green
Write-Host "Enabling autostart..." -ForegroundColor Yellow
& $cua autostart enable 2>&1
$exitCode = $LASTEXITCODE
Write-Host "Exit code: $exitCode" -ForegroundColor Cyan
if ($exitCode -eq 0) {
    Write-Host "Autostart enabled successfully!" -ForegroundColor Green
} else {
    Write-Host "Autostart enable returned exit code $exitCode" -ForegroundColor Red
    # Fallback: try with the binary directly from packages
    & $cua autostart status 2>&1
}
pause
