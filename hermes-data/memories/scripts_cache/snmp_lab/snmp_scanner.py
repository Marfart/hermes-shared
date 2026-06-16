#!/usr/bin/env python3
"""
Quick SNMP scanner - sends GetRequest(sysDescr.0) to each host,
listens for responses. Faster than nmap UDP scan.
"""
import socket, sys, struct, time
from pyasn1.codec.ber import encoder, decoder
from pysnmp.proto import api

pMod = api.PROTOCOL_MODULES[api.SNMP_VERSION_1]

# SNMP GetRequest for sysDescr.0
def build_probe():
    pdu = pMod.GetRequestPDU()
    pMod.apiPDU.set_defaults(pdu)
    pMod.apiPDU.set_varbinds(pdu, (('1.3.6.1.2.1.1.1.0', pMod.Null('')),))
    msg = pMod.Message()
    pMod.apiMessage.set_defaults(msg)
    pMod.apiMessage.set_community(msg, b'public')
    pMod.apiMessage.set_pdu(msg, pdu)
    return encoder.encode(msg)

PROBE = build_probe()

def try_community(host, community, timeout=1.5):
    """Try a specific community string."""
    pdu = pMod.GetRequestPDU()
    pMod.apiPDU.set_defaults(pdu)
    pMod.apiPDU.set_varbinds(pdu, (('1.3.6.1.2.1.1.1.0', pMod.Null('')),))
    msg = pMod.Message()
    pMod.apiMessage.set_defaults(msg)
    pMod.apiMessage.set_community(msg, community.encode())
    pMod.apiMessage.set_pdu(msg, pdu)
    data = encoder.encode(msg)
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(timeout)
    sock.sendto(data, (host, 161))
    try:
        resp, _ = sock.recvfrom(4096)
        sock.close()
        # Decode response
        rsp_msg, _ = decoder.decode(resp, asn1Spec=pMod.Message())
        rsp_pdu = pMod.apiMessage.get_pdu(rsp_msg)
        err = int(pMod.apiPDU.get_error_status(rsp_pdu))
        if err:
            return f"(community={community}, err={err})"
        vbs = pMod.apiPDU.get_varbinds(rsp_pdu)
        for name_str, val in vbs:
            raw = val.asOctets() if hasattr(val, 'asOctets') else bytes(val)
            try:
                return raw.decode('utf-8', errors='replace')
            except:
                return raw.hex()
        return "(empty response)"
    except socket.timeout:
        return None
    except Exception as e:
        return None
    finally:
        try: sock.close()
        except: pass

def scan_host(host, timeout=1.0):
    """Probe a single host for SNMP with default community."""
    communities = ['public', 'private', 'snmp', 'manager', 'admin', 'cisco', 'read', 'write']
    
    # Quick check with public first
    result = try_community(host, 'public', timeout)
    if result:
        return 'public', result
    
    # Try other common communities
    for c in communities:
        result = try_community(host, c, timeout * 0.5)
        if result:
            return c, result
    
    return None, None

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('targets', nargs='+', help='IPs or CIDR ranges')
    parser.add_argument('--timeout', type=float, default=1.0)
    parser.add_argument('--threads', type=int, default=50)
    args = parser.parse_args()
    
    # Parse targets
    hosts = []
    for t in args.targets:
        if '/' in t:
            import ipaddress
            for ip in ipaddress.IPv4Network(t, strict=False):
                hosts.append(str(ip))
        elif '-' in t:
            parts = t.split('-')
            start = parts[0]
            end = int(parts[1])
            base = '.'.join(start.split('.')[:-1])
            start_num = int(start.split('.')[-1])
            for i in range(start_num, end + 1):
                hosts.append(f'{base}.{i}')
        else:
            hosts.append(t)
    
    if not hosts:
        hosts = ['127.0.0.1']
    
    print(f"[+] Scanning {len(hosts)} hosts for SNMP...")
    print(f"[+] Checking communities: public, private, snmp, manager, admin, cisco, read, write")
    print()
    
    found = 0
    for i, host in enumerate(hosts):
        if i % 10 == 0 and i > 0:
            print(f"  ... {i}/{len(hosts)} scanned, {found} found", file=sys.stderr)
        
        community, info = scan_host(host, args.timeout)
        if community:
            print(f"  {host:15s}  community='{community}'  ─  {info[:80]}")
            found += 1
    
    print()
    print(f"[+] Done. {found} SNMP devices found out of {len(hosts)} hosts")

if __name__ == '__main__':
    main()
