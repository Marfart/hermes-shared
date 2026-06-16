---
name: camera-reconnaissance
description: "Three-phase camera/webcam discovery: local devices, local network IP cameras (RTSP/ONVIF/HTTP), and public internet OSINT (Shodan, Insecam, Google Dorks). Output is a verified status per phase."
version: "1.0"
triggers:
  - user mentions camera, webcam, IP camera, 摄像头
  - user asks about surveillance equipment on network
  - security recon involving video devices
---

# Camera Reconnaissance

## When to Use
User asks about finding cameras — either on the local machine, local network, or exposed on the public internet. Always go in this order.

## Phase 1: Local Device Enumeration

### Windows (PowerShell via PS1 file — avoid git-bash `$_` issues)
```powershell
# Write to a .ps1 file, then: powershell -ExecutionPolicy Bypass -File <path>
Get-CimInstance Win32_PnPEntity | Where-Object { $_.PNPClass -eq 'Camera' -and $_.Status -eq 'OK' }
Get-CimInstance Win32_PnPEntity | Where-Object { $_.PNPClass -eq 'Image' -and $_.Status -eq 'OK' }
Get-CimInstance Win32_PnPEntity | Where-Object { $_.Name -match 'camera|webcam|usb video' }
```

### Check virtual camera software
Check for DroidCam, iVCam, OBS, NDI — both installed software and running services.

### Check USB devices
```powershell
Get-CimInstance Win32_USBControllerDevice | ForEach-Object { $_.Dependent } | Where-Object { $_.Name -match 'camera|webcam|video|imaging' }
```

### Expected output
- Camera class devices (actual webcams): OK means built-in or USB camera
- Image class devices: usually scanners, not cameras
- Empty result: no local camera

## Phase 2: Local Network IP Cameras

### Key ports
| Port | Protocol | Brand |
|------|----------|-------|
| 80 | HTTP web interface | Most IP cameras |
| 554 | RTSP video stream | All IP cameras |
| 8080 | HTTP alt | Many brands |
| 37777 | TCP | Dahua |
| 34567 | TCP | Hikvision |
| 8899 | TCP | ONVIF |
| 3702 | UDP | ONVIF WS-Discovery |

### Methodology
1. Find local IP, figure subnet
2. Ping sweep to find live hosts
3. TCP port scan live hosts on camera ports (200ms timeout per check)
4. Check RTSP (554) — if open, it's almost certainly an IP camera

### Pitfalls
- ICMP ping may be blocked; scan all hosts on common IPs (.1-.254) anyway
- RTSP open = confirmed camera. HTTP open alone is inconclusive
- Camera HTTP interfaces often have distinct titles: "V2.0.x", "Network Camera", "Live View"
- Use .NET TcpClient for better control than PowerShell Test-Connection

## Phase 3: Public Internet Camera OSINT

### 3a. Insecam (No login required — best first stop)
```
http://insecam.org/
```
- World's largest directory of unsecured cameras
- Filter by: country, manufacturer, city, tag, timezone
- Click a camera: page shows embedded MJPEG stream
- 2000+ online cameras across 60+ countries
- Brands: Axis, Panasonic, D-Link, Foscam, TPLink, Hikvision, Sony, Vivotek, Bosch, etc.

**Extracting the actual stream URL** from an Insecam view page:
```javascript
document.querySelectorAll('img')
// Camera feed is an <img> tag with src pointing to MJPEG stream
// e.g. http://<ip>:<port>/mjpg/video.mjpg
```

### 3b. Shodan (requires free registration)
```
https://www.shodan.io/
```
Key queries:
| Query | What it finds |
|-------|---------------|
| webcam has_screenshot:true | Cameras with preview images |
| screenshot.label:webcam has_screenshot:true | Classified webcam images |
| port:554 has_screenshot:true | RTSP cameras with images |
| devicetype:webcam country:CN | Chinese cameras |
| server:D-Link webcam | D-Link cameras |
| server:AXIS has_screenshot:true | Axis cameras |

### 3c. Google Dorks
```
intitle:"Live View / - AXIS" | inurl:view/view.shtml
inurl:"ViewerFrame?Mode=" intitle:"Live View"
intitle:"EvoCam" inurl:"webcam.html"
inurl:"axis-cgi/jpg" intitle:"Live View"
inurl:"/view/index.shtml" intitle:"Live View"
intitle:"snc-rz30 home"
allintitle:"Network Camera NetworkCamera"
```

### 3d. GitHub Resources
- https://github.com/fury999io/public-ip-cams
- https://github.com/Tobee1406/Awesome-Google-Dorks
- https://github.com/Y0oshi/Project-Eyes-On

### 3e. Alternative Search Engines
- https://censys.io/
- https://netlas.io/
- https://hacked.camera/map/

### Stream Verification
To check if a camera MJPEG stream is live via Playwright:
```javascript
img.naturalWidth > 0 && img.complete  // = loaded successfully
```

## Writing PowerShell Scripts from Git-Bash
git-bash interprets `$_` as bash variable. Always write PS1 scripts to files:
```bash
powershell -ExecutionPolicy Bypass -File "path/to/script.ps1"
```

## Pitfalls
- Proxy/Vortex blocks outbound HTTP: use Playwright MCP browser or curl --noproxy
- MJPEG is a continuous stream: extract one JPEG frame by splitting on FFD8/FFD9 markers
- Insecam has ads that open popup tabs: close them
- Cameras on Insecam may be offline (indexed IP may have changed)
- Shodan search filters require login
- nmap on Windows/MSYS2 may crash with assertion errors: use PowerShell socket scan instead

## Writing PowerShell Scripts from Git-Bash
git-bash interprets `$_` as bash variable. Always write PS1 scripts to files:
```bash
powershell -ExecutionPolicy Bypass -File "path/to/script.ps1"
```

## Complete Scan Flow (本机+网络三层扫描)

本机 Layer 1 → 局域网 Layer 2 → 公网 Layer 3

### Layer 1: Local Device Enumeration (Chinese)
```powershell
# 检测项清单
# - PnP Camera 设备: Get-CimInstance Win32_PnPEntity -Filter "PNPClass='Camera'"
# - PnP Image 设备 (扫描仪): PNPClass='Image'
# - USB 摄像头: Name LIKE '%camera%' OR Name LIKE '%webcam%'
# - 虚拟摄像头软件: 检查 DroidCam / iVCam / OBS-VirtualCam / NDI
# - 摄像头服务: Win32_Service -Filter "Name LIKE '%droidcam%' OR Name LIKE '%ivcam%'"
```

### Layer 2: LAN IP Camera Port Scan (PowerShell)
```powershell
$ports = @(80, 554, 8080, 37777, 34567, 8899, 3702, 8554)
foreach ($ip in $liveHosts) {
    foreach ($port in $ports) {
        $tcp = New-Object System.Net.Sockets.TcpClient
        try {
            $async = $tcp.BeginConnect($ip, $port, $null, $null)
            $wait = $async.AsyncWaitHandle.WaitOne(200, $false)
            if ($wait -and $tcp.Connected) {
                Write-Host "OPEN $ip`:$port" -ForegroundColor Red
            }
            $tcp.Close()
        } catch { try { $tcp.Dispose() } catch {} }
    }
}
```

**Known pitfalls (this environment):**
- nmap 7.80 on MSYS2: `Assertion failed: htn.toclock_running == true, file ..\\Target.cc, line 503`
- Vortex proxy (127.0.0.1:7897): HTTPS forwarding silently fails (port LISTENING but connection hangs)

### Layer 3: Public Internet Camera OSINT
**Shodan queries (free registration needed):**
| Query | Target |
|-------|--------|
| `webcam has_screenshot:true` | All cameras with screenshots |
| `screenshot.label:webcam country:"CN"` | Chinese cameras |
| `screenshot.label:webcam country:"US"` | US cameras |
| `server:"D-Link webcam" city:"beijing"` | Specific brand + city |
| `port:554 has_screenshot:true` | RTSP cameras |
| `devicetype:"webcam" country:"CN"` | Chinese webcams |
| `port:37777` | Dahua |
| `port:34567` | Hikvision |

**Google Dorks for cameras:**
查看 `references/camera-port-signatures.md` 获取更多端口签名和 Google Dork 列表。

### Key Principles
- **安全/黑客研究与 BLIIOT 业务绝对隔离**
- PowerShell 脚本一定要写文件再执行，不能 inline `-c` 传参
- 先做本机（Layer 1）再扫网络（Layer 2）最后公网（Layer 3）

## Verification Checklist
- [ ] Phase 1: checked PnP Camera class, USB devices, virtual camera software
- [ ] Phase 2: ping sweep + port scan (RTSP/ONVIF/HTTP) on subnet
- [ ] Phase 3a: checked Insecam for relevant country/manufacturer
- [ ] Stream verified: image dimensions > 0 and complete = true
