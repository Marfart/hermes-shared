Write-Host "========================================" -ForegroundColor Cyan
Write-Host "PHASE 1: LOCAL CAMERA DEVICES" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Check PnP Camera/Image devices
Write-Host "`n[PnP Devices - Camera/Image class]" -ForegroundColor Yellow
$cameras = Get-CimInstance Win32_PnPEntity | Where-Object { $_.PNPClass -eq 'Camera' -and $_.Status -eq 'OK' }
if ($cameras) {
    $cameras | Select-Object Name, PNPClass, Status | Format-List
} else {
    Write-Host "  No Camera class devices found." -ForegroundColor DarkYellow
}

$images = Get-CimInstance Win32_PnPEntity | Where-Object { $_.PNPClass -eq 'Image' -and $_.Status -eq 'OK' }
if ($images) {
    Write-Host "`n[Image class devices (scanners):]"
    $images | Select-Object Name, Status | Format-List
}

# Check for any USB video/camera devices 
Write-Host "`n[USB devices containing 'cam' or 'video']"
$usbCams = Get-CimInstance Win32_PnPEntity | Where-Object { $_.Name -match 'camera|webcam|usb video' -and $_.Status -eq 'OK' }
if ($usbCams) {
    $usbCams | Select-Object Name, Status | Format-Table -AutoSize
} else {
    Write-Host "  No USB camera/webcam devices found." -ForegroundColor DarkYellow
}

# Check all video capture devices via registry
Write-Host "`n[Registry: Windows Media Foundation Hardware MFT]"
try {
    $mft = Get-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows Media Foundation\HardwareMFT" -ErrorAction SilentlyContinue
    if ($mft) {
        $mft.PSObject.Properties | Where-Object { $_.Name -match 'cam|video|mft' } | Select-Object Name, Value
    }
} catch { Write-Host "  No MFT entries." }

# Check for camera apps
Write-Host "`n[Camera-related software installed]"
$camSoftware = Get-CimInstance Win32_Product | Where-Object { $_.Name -match 'camera|webcam|droidcam|iVCam|epoccam|dslr' -and $_.Name -notmatch 'runtime|sdk|driver|update' }
if ($camSoftware) {
    $camSoftware | Select-Object Name, Vendor | Format-Table -AutoSize
} else {
    Write-Host "  No camera software found." -ForegroundColor DarkYellow
}

# Check for DroidCam/iVCam/phone-as-camera services
Write-Host "`n[Services related to virtual cameras]"
$camServices = Get-CimInstance Win32_Service | Where-Object { $_.Name -match 'droidcam|ivcam|ndi|virtualcam|obs' -and $_.State -eq 'Running' }
if ($camServices) {
    $camServices | Select-Object Name, DisplayName, State | Format-Table -AutoSize
} else {
    Write-Host "  No virtual camera services running." -ForegroundColor DarkYellow
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "PHASE 2: NETWORK IP CAMERA SCAN" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Get local IP
$localIP = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.InterfaceAlias -notmatch 'Loopback|Virtual|Bluetooth' -and $_.PrefixOrigin -eq 'Dhcp' }).IPAddress
if (-not $localIP) { $localIP = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.InterfaceAlias -notmatch 'Loopback' }).IPAddress | Select-Object -First 1 }
$subnet = ($localIP -split '\.')[0..2] -join '.'
Write-Host "Local IP: $localIP" -ForegroundColor Green
Write-Host "Scanning subnet: ${subnet}.0/24" -ForegroundColor Green

# Quick TCP port scan on common camera ports using .NET sockets
$ports = @(80, 554, 8080, 37777, 34567, 8899, 3702, 8554, 1024, 5000)
$openPorts = @()
$total = 254 * $ports.Count
$count = 0

Write-Host "`nScanning 255 hosts x $($ports.Count) ports = $total checks..." -ForegroundColor Yellow

# First, ping sweep
Write-Host "`n[Ping sweep to find live hosts]"
$liveHosts = @()
foreach ($i in 1..254) {
    $ip = "${subnet}.$i"
    if (Test-Connection -ComputerName $ip -Count 1 -Quiet -TimeToLive 5 -ErrorAction SilentlyContinue) {
        $liveHosts += $ip
        Write-Host "  LIVE: $ip" -ForegroundColor Green
    }
    $count++
    if ($count % 50 -eq 0) { Write-Host "  ...pinged $count hosts" }
}

if ($liveHosts.Count -eq 0) {
    Write-Host "  No live hosts found via ping (may be blocked). Scanning common gateway/device IPs..." -ForegroundColor DarkYellow
    $liveHosts = @(1..5 | ForEach-Object { "${subnet}.$_" }) + "${subnet}.254"
}

# Port scan live hosts
Write-Host "`n[Port scanning live hosts on camera ports]" -ForegroundColor Yellow
foreach ($ip in $liveHosts) {
    foreach ($port in $ports) {
        $tcp = New-Object System.Net.Sockets.TcpClient
        try {
            $async = $tcp.BeginConnect($ip, $port, $null, $null)
            $wait = $async.AsyncWaitHandle.WaitOne(300, $false)
            if ($wait -and $tcp.Connected) {
                Write-Host "  OPEN ${ip}:$port" -ForegroundColor Red
                $openPorts += "${ip}:$port"
                $tcp.EndConnect($async)
            }
            $tcp.Close()
        } catch { $tcp.Dispose() }
    }
}

if ($openPorts.Count -eq 0) {
    Write-Host "`nNo open camera ports found on the local network." -ForegroundColor DarkYellow
} else {
    Write-Host "`nFound $($openPorts.Count) potential camera endpoints:" -ForegroundColor Green
    $openPorts | ForEach-Object { Write-Host "  $_" -ForegroundColor Red }
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "SCAN COMPLETE" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
