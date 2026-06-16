"""Camera scan - local devices and network IP cameras"""
import subprocess, json, re, socket, sys
from pathlib import Path

def scan_local_cameras():
    """Scan for locally connected camera devices"""
    print("=" * 60)
    print("PHASE 1: LOCAL CAMERA DEVICES")
    print("=" * 60)
    
    # Method 1: PowerShell to query PnP devices for cameras
    try:
        ps_cmd = 'powershell -Command "Get-CimInstance Win32_PnPEntity | Where-Object { $_.PNPClass -eq \'Camera\' -or $_.PNPClass -eq \'Image\' -or ($_.Name -match \'camera|webcam|usb video|imaging\') } | Select-Object Name, PNPClass, Status, DeviceID | Format-List"'
        result = subprocess.run(ps_cmd, capture_output=True, text=True, shell=True, timeout=15)
        if result.stdout.strip():
            print("PnP Camera/Image devices found:")
            print(result.stdout[:3000])
        else:
            print("No PnP Camera/Image devices reported.")
    except Exception as e:
        print(f"PnP query error: {e}")
    
    # Method 2: Check for video input devices via DirectShow / device enumeration
    try:
        ps_cmd2 = 'powershell -Command "Get-CimInstance Win32_PnPEntity | Where-Object { $_.PNPClass -eq \'Media\' -or $_.PNPClass -eq \'System\' } | Select-Object Name, PNPClass | Format-List"'
        result2 = subprocess.run(ps_cmd2, capture_output=True, text=True, shell=True, timeout=15)
        media_devices = result2.stdout.strip()
        if 'cam' in media_devices.lower() or 'video' in media_devices.lower() or 'webcam' in media_devices.lower():
            print("Media devices (filtered for camera-related):")
            for line in media_devices.split('\n'):
                if any(kw in line.lower() for kw in ['cam', 'video', 'webcam', 'imaging', 'usb']):
                    print(f"  {line.strip()}")
    except Exception as e:
        print(f"Media query error: {e}")
    
    # Method 3: Check WMI for USB devices that could be cameras
    try:
        ps_cmd3 = 'powershell -Command "Get-CimInstance Win32_USBControllerDevice | ForEach-Object { $_.Dependent } | Where-Object { $_.Name -match \'camera|webcam|video|imaging\' } | Select-Object Name, Status | Format-List"'
        result3 = subprocess.run(ps_cmd3, capture_output=True, text=True, shell=True, timeout=15)
        if result3.stdout.strip():
            print("USB Camera devices:")
            print(result3.stdout[:2000])
        else:
            print("No USB camera devices found.")
    except Exception as e:
        print(f"USB camera query error: {e}")

    # Method 4: DirectShow / video capture devices via registry
    print("\nRegistry: video capture devices...")
    try:
        ps_cmd4 = 'powershell -Command "Get-ItemProperty -Path \'HKLM:\\SOFTWARE\\Microsoft\\Windows Media Foundation\\HardwareMFT\' -ErrorAction SilentlyContinue | Select-Object *"'
        result4 = subprocess.run(ps_cmd4, capture_output=True, text=True, shell=True, timeout=15)
        if result4.stdout.strip():
            lines = [l.strip() for l in result4.stdout.split('\n') if l.strip()]
            for line in lines:
                if any(kw in line.lower() for kw in ['cam', 'video', 'webcam', 'mft']):
                    print(f"  {line}")
    except Exception as e:
        print(f"MFT query error: {e}")


def scan_network_cameras():
    """Scan the local network for IP cameras on common ports"""
    import subprocess, sys
    
    print("\n" + "=" * 60)
    print("PHASE 2: NETWORK IP CAMERA SCAN")
    print("=" * 60)
    
    # Get local IP and subnet
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(2)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        subnet = '.'.join(local_ip.split('.')[:-1]) + '.'
        print(f"Local IP: {local_ip}, scanning subnet: {subnet}0/24")
    except:
        print("Could not determine local IP")
        return
    
    # Check if nmap is available
    try:
        result = subprocess.run(['where', 'nmap'], capture_output=True, text=True, timeout=5)
        nmap_available = result.returncode == 0
    except:
        nmap_available = False
    
    # Common camera ports: 80 (HTTP web interface), 554 (RTSP), 8080 (HTTP alt), 
    # 37777 (Dahua), 34567 (Hikvision ONVIF), 8899 (ONVIF), 3702 (WS-Discovery)
    camera_ports = [80, 554, 8080, 37777, 34567, 8899, 3702, 8554]
    
    if nmap_available:
        print("\n[nmap found] Scanning for cameras...")
        port_str = ','.join(str(p) for p in camera_ports)
        try:
            result = subprocess.run(
                ['nmap', '-sn', f'{subnet}0/24', '--open', '-T4'],
                capture_output=True, text=True, timeout=120
            )
            print("Host discovery results:")
            print(result.stdout[:2000])
            
            # Quick port scan on camera ports
            print(f"\nPort scan (camera ports: {port_str})...")
            result2 = subprocess.run(
                ['nmap', '-sT', '--open', '-T4', f'-p{port_str}', f'{subnet}0/24'],
                capture_output=True, text=True, timeout=180
            )
            print(result2.stdout[:3000])
        except Exception as e:
            print(f"nmap scan error: {e}")
    else:
        print("\n[nmap not found] Using Python socket scan...")
        # Quick TCP connect scan on common camera ports for live hosts
        import socket, concurrent.futures
        
        def check_port(ip, port):
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(1)
                result = s.connect_ex((ip, port))
                s.close()
                if result == 0:
                    return (ip, port, True)
                return (ip, port, False)
            except:
                return (ip, port, False)
        
        live_hosts = []
        # First, ping sweep to find live hosts
        print("Ping sweeping subnet...")
        for i in range(1, 255):
            ip = f"{subnet}{i}"
            try:
                r = subprocess.run(['ping', '-n', '1', '-w', '500', ip], 
                                 capture_output=True, text=True, timeout=2)
                if 'TTL=' in r.stdout or 'Reply from' in r.stdout:
                    live_hosts.append(ip)
                    print(f"  LIVE: {ip}")
            except:
                pass
        
        if not live_hosts:
            print("No live hosts found (ping may be blocked)")
            # Try scanning all hosts on common camera ports anyway
            live_hosts = [f"{subnet}{i}" for i in [1, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 200, 201, 254]]
        
        print(f"\nPort scanning {len(live_hosts)} live/possible hosts on camera ports...")
        found_cameras = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
            futures = []
            for ip in live_hosts:
                for port in camera_ports[:5]:  # Scan top 5 camera ports
                    futures.append(executor.submit(check_port, ip, port))
            for f in concurrent.futures.as_completed(futures):
                ip, port, open_port = f.result()
                if open_port:
                    found_cameras.append(f"{ip}:{port}")
                    print(f"  OPEN {ip}:{port}")
        
        if found_cameras:
            print(f"\nFound {len(found_cameras)} potential camera endpoints:")
            for c in found_cameras:
                print(f"  {c}")
        else:
            print("No open camera ports found on scanned hosts")


if __name__ == '__main__':
    scan_local_cameras()
    scan_network_cameras()
    print("\n" + "=" * 60)
    print("SCAN COMPLETE")
    print("=" * 60)
