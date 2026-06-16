$targets = @(
    @{IP='192.168.1.1'; Port=80; Name='Gateway'},
    @{IP='192.168.1.9'; Port=8080; Name='Host-9'},
    @{IP='192.168.1.15'; Port=8080; Name='Host-15'},
    @{IP='192.168.1.21'; Port=80; Name='Host-21'},
    @{IP='192.168.1.21'; Port=8080; Name='Host-21-alt'},
    @{IP='192.168.1.67'; Port=80; Name='Host-67'},
    @{IP='192.168.1.78'; Port=80; Name='Host-78'},
    @{IP='192.168.1.78'; Port=8080; Name='Host-78-alt'}
)

Write-Host "Checking HTTP titles and response headers..." -ForegroundColor Yellow
Write-Host ""

foreach ($t in $targets) {
    $ip = $t.IP
    $port = $t.Port
    $name = $t.Name
    $url = "http://${ip}:${port}/"
    
    try {
        # Get HTTP headers and first part of body
        $request = [System.Net.WebRequest]::Create($url)
        $request.Timeout = 3000
        $request.Method = 'GET'
        $response = $request.GetResponse()
        
        $statusCode = $response.StatusCode
        $server = $response.Headers['Server']
        $wwwAuth = $response.Headers['WWW-Authenticate']
        $contentType = $response.ContentType
        
        # Read first 4KB of body
        $stream = $response.GetResponseStream()
        $reader = New-Object System.IO.StreamReader($stream)
        $body = $reader.ReadToEnd()
        $reader.Close()
        $stream.Close()
        $response.Close()
        
        # Extract title
        $title = ''
        if ($body -match '<title>(.*?)</title>') { $title = $matches[1] }
        
        $desc = "$ip`:$port ($name)"
        
        if ($wwwAuth) {
            Write-Host "$desc" -ForegroundColor Cyan
            Write-Host "  Status: $([int]$statusCode) $($statusCode)" 
            Write-Host "  Server: $server"
            Write-Host "  Auth: $wwwAuth"
            Write-Host "  Title: $title"
            Write-Host ""
        } elseif ($title) {
            Write-Host "$desc" -ForegroundColor Cyan
            Write-Host "  Status: $([int]$statusCode) $($statusCode)"
            Write-Host "  Server: $server"
            Write-Host "  Title: $title"
            Write-Host ""
        } else {
            Write-Host "$desc" -ForegroundColor Cyan
            Write-Host "  Status: $([int]$statusCode) $($statusCode)"
            Write-Host "  Server: $server"
            Write-Host "  Type: $contentType"
            Write-Host "  (no title tag found)"
            Write-Host ""
        }
    } catch {
        Write-Host "$ip`:$port ($name) - Error: $($_.Exception.Message)" -ForegroundColor DarkYellow
    }
}

Write-Host "Investigating RTSP (port 554) on all live hosts..." -ForegroundColor Yellow
$liveHosts = @('192.168.1.1','192.168.1.3','192.168.1.9','192.168.1.14','192.168.1.15','192.168.1.21','192.168.1.41','192.168.1.47','192.168.1.51','192.168.1.57','192.168.1.66','192.168.1.67','192.168.1.68','192.168.1.78')
$rtspFound = $false

foreach ($ip in $liveHosts) {
    $tcp = New-Object System.Net.Sockets.TcpClient
    try {
        $async = $tcp.BeginConnect($ip, 554, $null, $null)
        $wait = $async.AsyncWaitHandle.WaitOne(300, $false)
        if ($wait -and $tcp.Connected) {
            Write-Host "  RTSP OPEN: $ip:554" -ForegroundColor Red
            $rtspFound = $true
        }
        $tcp.Close()
    } catch { try { $tcp.Dispose() } catch {} }
}

if (-not $rtspFound) { Write-Host "  No RTSP (port 554) open on any live host." -ForegroundColor DarkYellow }

# Also check ONVIF port 3702 (WS-Discovery multicast)
Write-Host "Checking ONVIF WS-Discovery (port 3702)..." -ForegroundColor Yellow
$onvifFound = $false
foreach ($ip in $liveHosts) {
    $tcp = New-Object System.Net.Sockets.TcpClient
    try {
        $async = $tcp.BeginConnect($ip, 3702, $null, $null)
        $wait = $async.AsyncWaitHandle.WaitOne(300, $false)
        if ($wait -and $tcp.Connected) {
            Write-Host "  ONVIF OPEN: $ip:3702" -ForegroundColor Red
            $onvifFound = $true
        }
        $tcp.Close()
    } catch { try { $tcp.Dispose() } catch {} }
}
if (-not $onvifFound) { Write-Host "  No ONVIF (port 3702) open." -ForegroundColor DarkYellow }

Write-Host "`nCamera investigation complete."
