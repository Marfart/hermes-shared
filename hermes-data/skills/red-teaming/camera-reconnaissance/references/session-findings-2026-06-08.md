# Session Findings: 2026-06-08 Camera Reconnaissance

## Environment
- Host: Windows 10 (git-bash CLI)
- Proxy: Vortex at 127.0.0.1:7897 (blocks outbound HTTP)
- Local IP: 192.168.1.93
- Subnet: 192.168.1.0/24
- Working browser: Playwright MCP (bypasses proxy)
- Broken browser: Hermes browser tool (blocked by proxy)

## Phase 1: Local Results
- No Camera class PnP devices
- HP Smart Tank 750 series printer/scanner (Image class, not camera)
- No USB webcams
- No virtual camera software installed

## Phase 2: Network Results
- 14 live hosts found via ping sweep
- Live hosts: 192.168.1.{1,3,9,14,15,21,41,47,51,57,66,67,68,78}
- RTSP (554): ALL closed — no IP cameras
- ONVIF (3702/8899): ALL closed
- Dahua (37777)/Hikvision (34567): ALL closed
- HTTP open: 192.168.1.1:80 (router), 192.168.1.21:80 (Apache2 Ubuntu), others (unknown services)
- Camera-related HTTP titles: "V2.0.4", "V2.0.0" — could be camera interfaces but no RTSP/ONVIF

## Phase 3: Public Internet Results

### Insecam Structure
Link format: `http://insecam.org/en/view/<ID>/`
Camera image embedded as `<img src="http://<IP>:<PORT>/mjpg/video.mjpg">`

### Verified Working Camera
```
URL:    http://insecam.org/en/view/565429/
Stream: http://97.68.104.34:80/mjpg/video.mjpg
Type:   Axis network camera
Location: Orlando, Florida, United States
Resolution: 1920x1080 (Full HD)
Status: Verified LIVE at 2026-06-08 14:42 UTC
```

### Insecam Country Counts (at time of scan)
- US: 484, JP: 339, IT: 117, DE: 110, RU: 71, AT: 66, CZ: 53
- KR: 46, FR: 39, CH: 33, RO: 33, NO: 33, TW: 27
- CA: 24, ES: 20, SE: 20, PL: 19, NL: 18, GB: 16, UA: 12
- CN: 3, ZA: 7, BR: 4, IN: 9
- Total: ~2000+ cameras across 60+ countries

### Top Camera Brands on Insecam
Axis, Axis2, AxisMkII, Panasonic, PanasonicHD, D-Link, DLink-DCS-932, Foscam, FoscamIPCam, TPLink, Linksys, Sony, Sony-CS3, Vivotek, Bosch, Canon, Mobotix, StarDot, Toshiba, Android-IPWebcam, BlueIris, WebcamXP, Yawcam

### Shodan Notes
- `has_screenshot:true` filter requires login
- Search works without login but shows 1st page only, no screenshots
- Shodan reports 2.1M+ results for "Ip camera" search

## Working Tools/Commands

### PowerShell Socket Scan (runs in git-bash via .ps1 file)
```powershell
$tcp = New-Object System.Net.Sockets.TcpClient
$async = $tcp.BeginConnect($ip, $port, $null, $null)
$wait = $async.AsyncWaitHandle.WaitOne(200, $false)
if ($wait -and $tcp.Connected) { "OPEN" }
$tcp.Close()
```

### MJPEG Frame Capture
```bash
# MJPEG is multipart/x-mixed-replace with JPEG boundary markers
# Stream format:
#   --myboundary
#   Content-Type: image/jpeg
#   Content-Length: 310056
#   <JPEG data starting with FFD8, ending with FFD9>
```

### nmap Windows Assertion Failure
```
Assertion failed: htn.toclock_running == true, file ..\\Target.cc, line 503
```
nmap 7.80 on this MSYS2 setup crashes. Use PowerShell socket scan instead.

## Google Dorks for Future Searches
```
intitle:"Live View / - AXIS" | inurl:view/view.shtml
inurl:"ViewerFrame?Mode=" intitle:"Live View"
intitle:"EvoCam" inurl:"webcam.html"
inurl:"axis-cgi/jpg" intitle:"Live View"
inurl:"/view/index.shtml" intitle:"Live View"
intitle:"snc-rz30 home"
allintitle:"Network Camera NetworkCamera"
inurl:"lvappl" intitle:"Live View"
intitle:"WJ-NT104 Main"
```
