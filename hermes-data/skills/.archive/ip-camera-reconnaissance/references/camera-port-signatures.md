# IP Camera Port Signatures Reference

## Standard Ports by Manufacturer

| Manufacturer | Web UI | RTSP | ONVIF | Discovery | Proprietary |
|-------------|--------|------|-------|-----------|-------------|
| **Axis** | 80/443 | 554 | 8899 | 3702 | - |
| **Dahua (大华)** | 80/443 | 554 | 8899 | 3702 | **37777** (TCP config) |
| **Hikvision (海康)** | 80/443 | 554 | 8899 | 3702 | **34567** (SDK) |
| **D-Link** | 80/8080 | 554 | - | - | - |
| **Panasonic** | 80/443 | 554 | 8899 | - | - |
| **Sony SNC** | 80/443 | 554 | - | - | - |
| **Reolink** | 80/443 | 554 | 8000 | - | - |
| **TP-Link Tapo** | 80/443 | 554/8554 | - | - | - |
| **Foscam** | 80/443 | 554 | - | - | - |
| **Amcrest** | 80/443 | 554/8554 | 8899 | 3702 | 37777 |

## Protocol Descriptions

### RTSP (554 / 8554 / 10554)
Real-Time Streaming Protocol — the primary video streaming protocol for IP cameras.
RTSP URLs typically look like:
```
rtsp://192.168.1.100:554/onvif1
rtsp://192.168.1.100:554/live/main
rtsp://admin:password@192.168.1.100:554/stream1
```

### ONVIF (8899 / 3702)
Open Network Video Interface Forum standard.
- **3702**: WS-Discovery (multicast) — used to discover ONVIF devices on the LAN
- **8899**: ONVIF HTTP — the standard web service interface for camera control
- Note: ONVIF can also run on ports 80 or 8080

### HTTP Web Interface (80 / 8080 / 443)
The camera's built-in web management interface. Common URL paths:
```
http://ip:port/
http://ip:port/view/view.shtml       — Axis
http://ip:port/view/index.shtml      — Axis
http://ip:port/ViewerFrame?Mode=     — Generic
http://ip:port/axis-cgi/jpg/image.cgi — Axis snapshot
http://ip:port/cgi-bin/snapshot.cgi  — Hikvision
http://ip:port/cgi-bin/imageserver   — Generic
http://ip:port/live/index.html? Language=0 — Hikvision
```

## Default Credentials (notable)

| Brand | Username | Password |
|-------|----------|----------|
| Axis | root | pass / <blank> |
| Hikvision | admin | 12345 / admin |
| Dahua | admin | admin / 666666 |
| D-Link | admin | <blank> |
| TP-Link | admin | admin |
| Reolink | admin | <blank> |

## Google Dork Identification

When verifying a potential camera via HTTP, check for these HTML signatures:

- **Axis**: `<title>Live View / - AXIS` or `<title>Live View - AXIS`
- **Hikvision**: `<title>Hikvision` or path includes `/doc/page/login.asp`
- **Dahua**: Path includes `/web/` with javascript authentication
- **D-Link**: `<title>D-Link` or `DCS-` in URL
- **Foscam**: `foscam` in URL or `<title>Foscam`

Reference: Session 2026-06-08 camera scanning — all RTSP/ONVIF/Dahua/Hikvision ports were closed on the target network.
