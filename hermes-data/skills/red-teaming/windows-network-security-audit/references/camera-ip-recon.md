# IP Camera Reconnaissance (3-Tier Discovery)

A structured methodology for discovering cameras at three levels: local machine, local network, and public internet.

## Tier 1: Local Camera Devices (Windows)

### Quick PowerShell scan (write to .ps1 file to avoid git-bash `$_` mangling)

```powershell
# save as scan_cameras.ps1, then: powershell -ExecutionPolicy Bypass -File scan_cameras.ps1
Get-CimInstance Win32_PnPEntity | Where-Object { $_.PNPClass -eq 'Camera' -and $_.Status -eq 'OK' } | Select-Object Name, PNPClass, Status
Get-CimInstance Win32_PnPEntity | Where-Object { $_.PNPClass -eq 'Image' -and $_.Status -eq 'OK' } | Select-Object Name, Status
```

### Registry check (video capture devices)
```powershell
Get-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows Media Foundation\HardwareMFT" -ErrorAction SilentlyContinue
```

### Check virtual camera software/services
```powershell
Get-CimInstance Win32_Service | Where-Object { $_.Name -match 'droidcam|ivcam|ndi|virtualcam|obs' -and $_.State -eq 'Running' }
```

### ⚠️ git-bash + PowerShell: `$_` variable expansion bug
When running PowerShell inline commands through git-bash, `$_` gets expanded by bash before reaching PowerShell. **Symptoms:** PowerShell errors about `C:\Users\Admin.PNPClass` being treated as a variable.

**Fixes:** (a) Write PowerShell scripts to `.ps1` files and run via `powershell -File`, or (b) escape `$` as `\$` in inline commands, or (c) use single-quoted strings where bash won't expand.

## Tier 2: Network IP Cameras (LAN)

### Camera-Specific Ports

| Port | Protocol | Typical Use |
|------|----------|-------------|
| 80/8080 | HTTP | Camera web interface, MJPEG stream |
| 443 | HTTPS | Encrypted camera web interface |
| 554 | RTSP | Real-Time Streaming Protocol — main video stream |
| 8554 | RTSP alt | Alternative RTSP port |
| 3702 | WS-Discovery | ONVIF discovery protocol |
| 8899 | ONVIF | ONVIF device control |
| 37777 | Dahua | Dahua camera protocol |
| 34567 | Hikvision | Hikvision camera protocol |
| 37777 | TCP | Dahua/NVR discovery |

### Ping Sweep + Port Scan (PowerShell, .NET sockets)

Write this to a `.ps1` file to avoid git-bash issues:

```powershell
$subnet = '192.168.1.'
$ports = @(80, 554, 8080, 37777, 34567, 8899, 3702, 8554)
$liveHosts = @()

# Phase 1: Ping sweep
foreach ($i in 1..254) {
    $ip = "${subnet}${i}"
    if (Test-Connection -ComputerName $ip -Count 1 -Quiet -TimeToLive 5 -ErrorAction SilentlyContinue) {
        $liveHosts += $ip
    }
}

# Phase 2: Port scan live hosts
foreach ($ip in $liveHosts) {
    foreach ($port in $ports) {
        $tcp = New-Object System.Net.Sockets.TcpClient
        try {
            $async = $tcp.BeginConnect($ip, $port, $null, $null)
            $wait = $async.AsyncWaitHandle.WaitOne(200, $false)
            if ($wait -and $tcp.Connected) {
                Write-Host "OPEN ${ip}:${port}" -ForegroundColor Red
            }
            $tcp.Close()
        } catch { try { $tcp.Dispose() } catch {} }
    }
}
```

### HTTP Service Identification

Once you find open HTTP/8080 ports, identify the device:

```powershell
$request = [System.Net.WebRequest]::Create("http://IP:PORT/")
$request.Timeout = 3000
$response = $request.GetResponse()
$server = $response.Headers['Server']  # e.g. "Apache/2.4.41 (Ubuntu)"
$auth = $response.Headers['WWW-Authenticate']  # "Basic realm=AXIS_..."
# Read body for <title> tag
$stream = $response.GetResponseStream()
$reader = New-Object System.IO.StreamReader($stream)
$body = $reader.ReadToEnd()
if ($body -match '<title>(.*?)</title>') { $title = $matches[1] }
```

Camera identifiers in HTTP headers:
- `Server: AXIS` or `WWW-Authenticate: Basic realm="AXIS_..."` → Axis camera
- `Server: D-Link webcam` or `realm="DCS-"` → D-Link camera
- `Server: TP-LINK` → TP-Link camera
- `Server: Hikvision` → Hikvision camera
- Title contains "Live View / - AXIS" → Axis camera web interface

### MJPEG Stream Verification (Playwright MCP)

Use Playwright MCP to verify a live camera stream (bypasses proxy issues):

```javascript
// In Playwright evaluate
const imgs = document.querySelectorAll('img');
// Check if an MJPEG or JPEG stream image actually loaded
imgs.forEach(img => {
    if (img.naturalWidth > 0 && img.complete) {
        // Stream is LIVE — image loaded successfully
        console.log(`Camera LIVE: ${img.src} @ ${img.naturalWidth}x${img.naturalHeight}`);
    }
});
```

Key indicators of a working camera:
- `img.naturalWidth > 0` AND `img.complete === true` → stream loaded
- Resolution like 1920×1080 or 720×576 → camera is pushing real frames
- Source URL containing `mjpg/video.mjpg`, `tmpfs/auto.jpg`, `cgi-bin/viewer/video.jpg` → camera URL patterns

## Tier 3: Public Internet Cameras (OSINT)

### Insecam (no registration needed)
```
http://insecam.org/ — World's largest directory of unsecured cameras
Browse by: /en/bycountry/CN/ (country), /en/bytype/Axis/ (manufacturer), /en/byrating/ (popularity)
```

As of 2026-06-08 Insecam had ~2,000+ indexed cameras across 60+ countries. Top countries: US (484), Japan (339), Italy (117), Germany (110), Russia (71), Taiwan (27), China (3).

### Shodan (requires free registration)
```
https://www.shodan.io/search?query=webcam+has_screenshot%3Atrue
https://www.shodan.io/search?query=port%3A554+has_screenshot%3Atrue  (RTSP cameras)
https://www.shodan.io/search?query=screenshot.label%3Awebcam+country%3A"CN"
```

Shodan reports ~2.1 million IP camera results worldwide.

### Google Dorks (direct Google search)
```
intitle:"Live View / - AXIS" | inurl:view/view.shtml
inurl:"ViewerFrame?Mode=" intitle:"Live View"
intitle:"EvoCam" inurl:"webcam.html"
intitle:"snc-rz30 home"
inurl:"axis-cgi/jpg" intitle:"Live View"
inurl:"top.htm" inurl:"currenttime" intitle:"Live View / -Axis"
allintitle:"Network Camera NetworkCamera"
intitle:"Live NetSnap Cam-Server feed"
```

### GitHub Repositories
- `fury999io/public-ip-cams` — Curated list of public camera URLs
- `Tobee1406/Awesome-Google-Dorks` — Google dork collection
- `Y0oshi/Project-Eyes-On` — Camera scanning tool with dorks

### Alternative Search Engines
- Netlas: https://netlas.io/blog/find_online_cameras/
- Censys: https://censys.io/
- Shodan Images: https://images.shodan.io/ (screenshot browser)

## Live MJPEG Stream Access

Common URL patterns for direct camera stream access:

| Pattern | Example |
|---------|---------|
| MJPEG stream | `http://IP:PORT/mjpg/video.mjpg` |
| Single JPEG | `http://IP:PORT/tmpfs/auto.jpg?COUNTER` |
| CGI snapshot | `http://IP:PORT/cgi-bin/viewer/video.jpg?r=COUNTER` |
| Axis CGI | `http://IP:PORT/axis-cgi/jpg/image.cgi` |
| Snap capture | `http://IP:PORT/webcapture.jpg?command=snap&channel=1` |

Replace `?COUNTER` with `?r=12345` or similar to bypass caching.

## 实战示例 (2026-06-08)

### Local machine (192.168.1.93)
- Camera class PnP devices: **None**
- USB webcams: **None**
- Virtual camera software: **None**
- Only HP Smart Tank 750 printer/scanner (Image class, not a camera)

### LAN (192.168.1.0/24, 14 live hosts)
- RTSP (554): **No open ports** — no standard IP cameras
- ONVIF (3702/8899): **No open ports**
- Dahua (37777) / Hikvision (34567): **No open ports**
- HTTP 80/8080: **8 open ports** — but all routers, web servers (Apache, nginx), and unknown services, not cameras

### Public internet (via Insecam)
- **Shenzhen, China** — FDT camera, **LIVE** at `http://14.0.135.27:80/cgi-bin/viewer/video.jpg?r=COUNTER` (720×576 PAL)
- **Foshan, China** — FDT camera, offline
- **Shenyang, China** — FDT camera, offline
- **Orlando, USA** — Axis camera, **LIVE** at `http://97.68.104.34:80/mjpg/video.mjpg` (1920×1080 Full HD)
