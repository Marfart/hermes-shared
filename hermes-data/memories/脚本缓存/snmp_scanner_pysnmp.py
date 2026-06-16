"""SNMP scanner using pysnmp - scan local network for SNMP devices"""
from pysnmp.hlapi import *
import time

# Common community strings
COMMUNITIES = ['public', 'private', 'snmp', 'manager', 'admin', 'read', 'write',
               'cisco', 'huawei', 'all', 'monitor', 'netman', 'default', 'test']

# Target IPs to check
TARGETS = []
for suffix in [1, 254, 2, 3, 4, 5, 6, 7, 8, 9, 10, 50, 100, 101, 102, 200, 201, 202]:
    TARGETS.append(f"192.168.1.{suffix}")

# OIDs to check
OIDS = [
    '1.3.6.1.2.1.1.1.0',    # sysDescr
    '1.3.6.1.2.1.1.5.0',    # sysName
    '1.3.6.1.2.1.1.3.0',    # sysUpTime
]

def try_community(ip, community):
    """Try an SNMP GET with given community string"""
    for oid in OIDS:
        try:
            iterator = getCmd(
                SnmpEngine(),
                CommunityData(community),
                UdpTransportTarget((ip, 161), timeout=2, retries=0),
                ContextData(),
                ObjectType(ObjectIdentity(oid))
            )
            errorIndication, errorStatus, errorIndex, varBinds = next(iterator)
            
            if errorIndication:
                continue
            if errorStatus:
                continue
            
            if varBinds:
                return varBinds
        except:
            continue
    return None

def main():
    print("=" * 60)
    print("SNMP Scanner - 192.168.1.0/24")
    print("=" * 60)
    print(f"{len(COMMUNITIES)} communities × {len(TARGETS)} targets")
    print("=" * 60)
    
    found = 0
    for ip in TARGETS:
        for community in COMMUNITIES:
            result = try_community(ip, community)
            if result:
                found += 1
                print(f"\n[+] ✓ {ip}:{161} community='{community}'")
                for name, val in result:
                    print(f"    ├─ {name} = {val.prettyPrint()}")
                break  # Don't try more communities on this IP
        else:
            # Timeout-based progress indicator
            pass
    
    if found == 0:
        print("\n[-] No SNMP devices found on this subnet.")
        print()
        print("→ Router might not have SNMP enabled")
        print("→ Try: open 192.168.1.1 in browser and check SNMP settings")
        print("→ Or install net-snmp for snmpwalk -c public 192.168.1.1")
    else:
        print(f"\n[+] Found {found} SNMP device(s)!")

if __name__ == '__main__':
    start = time.time()
    main()
    print(f"\nTime: {time.time()-start:.1f}s")
