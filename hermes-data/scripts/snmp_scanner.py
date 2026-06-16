"""SNMP community string brute forcer - scan local network for vulnerable SNMP devices"""
import socket
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# Common community strings to try
COMMUNITIES = ['public', 'private', 'snmp', 'manager', 'admin', 'read', 'write', 
               'cisco', 'huawei', 'all', 'monitor', 'netman', 'security', 'default',
               'internal', 'external', 'community', 'test', 'guest', 'staff']

# Common SNMP OIDs to query
TARGET_OIDS = [
    (1,3,6,1,2,1,1,1,0),    # sysDescr
    (1,3,6,1,2,1,1,5,0),    # sysName
    (1,3,6,1,2,1,1,3,0),    # sysUpTime
    (1,3,6,1,2,1,1,4,0),    # sysContact
    (1,3,6,1,2,1,1,6,0),    # sysLocation
]

def encode_oid(oid_tuple):
    """Encode an OID tuple into BER-encoded OID bytes"""
    parts = [40 * oid_tuple[0] + oid_tuple[1]]
    for num in oid_tuple[2:]:
        if num < 128:
            parts.append(num)
        else:
            bytes_list = []
            while num > 0:
                bytes_list.insert(0, num & 0x7f)
                num >>= 7
            for i, b in enumerate(bytes_list[:-1]):
                bytes_list[i] = b | 0x80
            parts.extend(bytes_list)
    result = b''
    for p in parts:
        if p < 128:
            result += bytes([p])
        else:
            # Already handled above for multi-byte
            result += bytes([p])
    return result

def encode_length(length):
    """BER encode length"""
    if length < 128:
        return bytes([length])
    # Length is < 256 for our use case
    return bytes([0x81, length])

def build_snmp_get(community, oid_tuple):
    """Build a raw SNMPv2c GetRequest packet"""
    # Encode OID
    oid_encoded = b'\x06'  # Tag for OID
    oid_data = encode_oid(oid_tuple)
    oid_encoded += encode_length(len(oid_data))
    oid_encoded += oid_data
    
    # Null value
    null_val = b'\x05\x00'
    
    # Varbind: Sequence(oid, null)
    varbind_data = oid_encoded + null_val
    varbind = b'\x30' + encode_length(len(varbind_data)) + varbind_data
    
    # Varbind list
    vblist_data = varbind
    vblist = b'\x30' + encode_length(len(vblist_data)) + vblist_data
    
    # PDU: GetRequest (0xA0)
    req_id = int(time.time() * 1000) & 0x7fffffff
    pdu_body = b''
    # request-id (INTEGER)
    req_id_bytes = req_id.to_bytes(4, 'big')
    if req_id < 128:
        pdu_body += b'\x02\x01' + bytes([req_id])
    else:
        pdu_body += b'\x02\x04' + req_id_bytes
    # error-status (INTEGER 0)
    pdu_body += b'\x02\x01\x00'
    # error-index (INTEGER 0)
    pdu_body += b'\x02\x01\x00'
    # varbind-list
    pdu_body += vblist
    
    pdu = b'\xa0' + encode_length(len(pdu_body)) + pdu_body
    
    # Message wrapper: Sequence(version, community, pdu)
    version = b'\x02\x01\x01'  # v2c
    comm_bytes = community.encode()
    comm = b'\x04' + encode_length(len(comm_bytes)) + comm_bytes
    
    msg_data = version + comm + pdu
    msg = b'\x30' + encode_length(len(msg_data)) + msg_data
    
    return msg

def try_snmp_get(ip, community, port=161, timeout=2):
    """Send SNMP GetRequest to target IP with community string"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(timeout)
    
    results = []
    for oid in TARGET_OIDS:
        try:
            packet = build_snmp_get(community, oid)
            sock.sendto(packet, (ip, port))
            data, addr = sock.recvfrom(4096)
            
            # Parse response - extract the value bytes
            # Minimal parsing: find OctetString or INTEGER tag
            if len(data) > 30:
                # Look for readable string in response
                response_text = data[30:].decode('utf-8', errors='replace').strip('\x00')
                # Clean up non-printable
                clean = ''.join(c if c.isprintable() or c in '\n\r\t' else '.' for c in response_text)
                results.append(clean[:200])
        except socket.timeout:
            pass
        except Exception as e:
            pass
    
    sock.close()
    return results

def check_target(ip):
    """Check if a target responds to any community string"""
    for community in COMMUNITIES:
        results = try_snmp_get(ip, community)
        if results:
            return (ip, community, results)
    return None

def main():
    # Target IPs to check
    targets = []
    # Common gateway/routers
    for suffix in [1, 254]:
        targets.append(f"192.168.1.{suffix}")
    # Some common IPs in the subnet
    for suffix in range(1, 20):
        targets.append(f"192.168.1.{suffix}")
    for suffix in [100, 101, 102, 200, 201, 202]:
        targets.append(f"192.168.1.{suffix}")
    
    print("=" * 60)
    print("SNMP Community Scanner - Scanning 192.168.1.0/24")
    print("=" * 60)
    print(f"Trying {len(COMMUNITIES)} community strings on {len(targets)} targets")
    print("=" * 60 + "\n")
    
    found = 0
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(check_target, ip): ip for ip in targets}
        for future in as_completed(futures):
            result = future.result()
            if result:
                ip, community, data = result
                found += 1
                print(f"[+] ✓ {ip}:{161} community='{community}'")
                for d in data[:2]:
                    print(f"    └─ {d}")
                print()
    
    if found == 0:
        print("[-] No SNMP devices found on local subnet.")
        print()
        print("Possible reasons:")
        print("  1. Router/firewall blocks UDP 161 from LAN")
        print("  2. Devices don't have SNMP enabled")
        print("  3. Custom community string not in our wordlist")
        print()
        print("Next steps:")
        print("  - Try the gateway's admin web interface to enable SNMP")
        print("  - Install net-snmp for more thorough scanning")
        print("  - Try nmap UDP scan of whole subnet (slow but complete)")
    else:
        print(f"\n[+] Found {found} SNMP device(s). Next: snmpwalk the full MIB tree!")

if __name__ == '__main__':
    main()
