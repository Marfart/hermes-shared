---
name: ip-camera-reconnaissance
category: red-teaming
description: Three-layer surveillance camera discovery — local USB/captured devices, LAN IP cameras, and public-internet OSINT via Shodan/Insecam/Google Dorks. Port signatures, tool pitfalls, and search operator reference.
triggers:
  - "scan for cameras"
  - "find cameras on the network"
  - "public cameras / webcam OSINT"
  - "scan for surveillance devices"
  - "公网摄像头 / 摄像头扫描 / 网络摄像头发现"
---

# IP Camera Reconnaissance (三重扫描方法论)

## 三层架构

```
Layer 1: 本机 (Local USB/PnP)
  ↓
Layer 2: 局域网 (LAN IP Cameras)
  ↓
Layer 3: 公网 (Public Internet OSINT)
```

---

## Layer 1: 本机摄像头检测

### PowerShell 扫描（注意 git-bash 坑）

直接跑 `powershell -c "..."` 会失败——git-bash 把 `$_` 当成 bash 变量展开。
**必须** 先写 `.ps1` 文件，再用 `powershell -ExecutionPolicy Bypass -File path\to\script.ps1` 执行。

```powershell
# 保存为 .ps1 文件执行
$cameras = Get-CimInstance Win32_PnPEntity | Where-Object {
    $_.PNPClass -eq 'Camera' -and $_.Status -eq 'OK'
}
$cameras | Select-Object Name, PNPClass, Status | Format-List
```

### 检测项清单
| 检测项 | 方法 |
|--------|------|
| PnP Camera 设备 | `Get-CimInstance Win32_PnPEntity -Filter "PNPClass='Camera'"` |
| PnP Image 设备 (扫描仪) | 同上, `PNPClass='Image'` |
| USB 摄像头 | `Get-CimInstance Win32_PnPEntity -Filter "Name LIKE '%camera%' OR Name LIKE '%webcam%'"` |
| 虚拟摄像头软件 | 检查 DroidCam / iVCam / OBS-VirtualCam / NDI |
| 摄像头服务 | `Get-CimInstance Win32_Service -Filter "Name LIKE '%droidcam%' OR Name LIKE '%ivcam%'"` |

---

## Layer 2: 局域网 IP 摄像头扫描

### 摄像头端口签名

| 端口 | 协议 | 品牌/用途 |
|------|------|-----------|
| **554** | RTSP | IP摄像头核心流协议 |
| **80** | HTTP | 摄像头Web管理界面 |
| **8080** | HTTP Alt | 替代Web端口 |
| **37777** | TCP | Dahua / 大华 |
| **34567** | TCP | Hikvision / 海康威视 |
| **8899** | ONVIF HTTP | ONVIF摄像头标准接口 |
| **3702** | WS-Discovery | ONVIF设备发现 |
| **8554** | RTSP Alt | 替代RTSP端口 |

### 扫描脚本 (PowerShell ./NET TCP)

```powershell
$liveHosts = @('192.168.1.1','192.168.1.2',...)
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

### 发现存活主机后验证
用 WebRequest 读 HTTP 标题，判断是否为摄像头面板：
```powershell
$request = [System.Net.WebRequest]::Create("http://$ip`:$port/")
$response = $request.GetResponse()
$reader = New-Object System.IO.StreamReader($response.GetResponseStream())
$body = $reader.ReadToEnd()
# 提取 <title> 标签判断
```

### 已知坑（本环境）
- **nmap 7.80 on MSYS2**: Assertion failed: `htn.toclock_running == true, file ..Target.cc, line 503` — 原生 nmap 在 git-bash 上会崩。用 PowerShell .NET TCP 扫描替代。
- **Vortex proxy (127.0.0.1:7897)**: HTTPS 转发会默默失效（端口 LISTENING 但连接挂死）。扫描时用 `--noproxy "*"` 直连。

---

## Layer 3: 公网摄像头 OSINT

### 方法 A: Shodan（最强，需免费注册）
```
https://www.shodan.io/
```

关键查询：
| Shodan Dork | 目标 |
|-------------|------|
| `webcam has_screenshot:true` | 所有带截图的摄像头 |
| `screenshot.label:webcam has_screenshot:true` | ML分类为摄像头的 |
| `screenshot.label:webcam country:"CN"` | 中国摄像头 |
| `screenshot.label:webcam country:"US"` | 美国摄像头 |
| `server:"D-Link webcam" city:"beijing"` | 特定品牌+城市 |
| `port:554 has_screenshot:true` | RTSP摄像头 |
| `devicetype:"webcam" country:"CN"` | 中国webcam |
| `port:37777` | Dahua |
| `port:34567` | Hikvision |

Shodan 现有 **215万+** IP摄像头数据。免费注册后可查看部分截图（会员全部）。

### 方法 B: Insecam（无需注册，可直接看快照）
```
http://insecam.org/
http://insecam.org/en/bytype/Axis/
http://insecam.org/en/bytype/Hikvision/
```
全球最大无密码摄像头目录。按品牌/国家分类。网页直接有实时快照。
不需要注册。

### 方法 C: Google Dorks（不用任何账号）
直接搬去 Google 搜：

| Google Dork | 目标品牌 |
|------------|----------|
| `intitle:"Live View / - AXIS" \| inurl:view/view.shtml` | Axis |
| `inurl:"ViewerFrame?Mode="` | 通用 IP Cam |
| `intitle:"EvoCam" inurl:"webcam.html"` | EvoCam |
| `intitle:"snc-rz30 home"` | Sony SNC |
| `inurl:"axis-cgi/jpg"` | Axis 静态截图 |
| `inurl:"/view/index.shtml"` | 通用 |
| `intitle:"Live NetSnap Cam-Server feed"` | NetSnap |
| `inurl:"lvappl"` | 通用 |
| `intitle:"WJ-NT104 Main"` | Panasonic |
| `allintitle:"Network Camera NetworkCamera"` | 通用网络摄像头 |

### 方法 D: GitHub 项目
```
https://github.com/fury999io/public-ip-cams    — 公开摄像头URL合集
https://github.com/Tobee1406/Awesome-Google-Dorks — Dork全集
https://github.com/Y0oshi/Project-Eyes-On       — 摄像头扫描Python工具
```

### 方法 E: 替代搜索引擎
```
https://netlas.io/blog/find_online_cameras/  — Shodan替代品
https://censys.io/                             — 证书/设备搜索引擎
https://hacked.camera/map/                     — 870万摄像头漏洞地图
```

---

## 完整扫描流程（本机+网络）

参考脚本位置：`memories/脚本缓存/camera_scan.py` 和 `memories/脚本缓存/scan_cameras.ps1`

标准流程：
1. Run Layer 1 PowerShell script (via `.ps1` file, not inline)
2. Run Layer 2 ping sweep → TCP port scan on camera ports
3. Verify open HTTP ports by reading web titles
4. Report Layer 3 public OSINT sources for user to explore

---

## 关键铁则

- **安全/黑客研究与 BLIIOT 业务绝对隔离** — 永远不把摄像头扫描结果联系到公司业务
- PowerShell 脚本一定要写文件再执行，不能 inline `-c` 传参（git-bash 吃 `$_`）
- 先做本机（Layer 1）再扫网络（Layer 2）最后公网（Layer 3）
