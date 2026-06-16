$liveHosts = @('192.168.1.1','192.168.1.3','192.168.1.9','192.168.1.14','192.168.1.15','192.168.1.21','192.168.1.41','192.168.1.47','192.168.1.51','192.168.1.57','192.168.1.66','192.168.1.67','192.168.1.68','192.168.1.78')
$ports = @(80, 554, 8080, 37777, 34567, 8899, 3702, 8554)
Write-Host "Scanning $($liveHosts.Count) live hosts x $($ports.Count) camera ports..."
$openPorts = @()

foreach ($ip in $liveHosts) {
    foreach ($port in $ports) {
        $tcp = New-Object System.Net.Sockets.TcpClient
        try {
            $async = $tcp.BeginConnect($ip, $port, $null, $null)
            $wait = $async.AsyncWaitHandle.WaitOne(200, $false)
            if ($wait -and $tcp.Connected) {
                Write-Host "  OPEN $ip`:$port" -ForegroundColor Red
                $openPorts += "$ip`:$port"
            }
            $tcp.Close()
        } catch {
            try { $tcp.Dispose() } catch {}
        }
    }
}

if ($openPorts.Count -eq 0) {
    Write-Host "`nNo open camera ports found on any live host." -ForegroundColor DarkYellow
} else {
    Write-Host "`nFound $($openPorts.Count) open camera-related ports:" -ForegroundColor Green
    $openPorts | ForEach-Object { Write-Host "  $_" -ForegroundColor Red }
}
Write-Host "Targeted camera scan complete."
