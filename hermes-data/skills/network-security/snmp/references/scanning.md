# SNMP Security Scanning

## Reconnaissance

```bash
# 1. Discover SNMP hosts on subnet
nmap -sU -p 161 --open -n 192.168.1.0/24

# 2. If you have net-snmp tools:
snmpwalk -v2c -c public  TARGET system
snmpwalk -v2c -c private TARGET system

# 3. Community string brute force
hydra -l public -P wordlist.txt TARGET snmp
```

## What a Walk Exposes

A successful `snmpwalk -c public TARGET` reveals:

**System Info** (1.3.6.1.2.1.1)
- Device model, firmware version
- Admin contact info
- Physical location
- Uptime (patch level inference)

**Network Interfaces** (1.3.6.1.2.1.2)
- All interface IPs, MACs, speeds
- Traffic counters (RX/TX bytes)

**IP/ARP Tables** (1.3.6.1.2.1.4 / 1.3.6.1.2.1.3)
- Other hosts on the same network
- Routing tables

**Process List** (1.3.6.1.2.1.25.4) — host-resources MIB
- Running processes
- Installed software

**Storage** (1.3.6.1.2.1.25.2)
- Disk usage, memory

## Write Access (private community)

With `-c private` you can:
- Change sysName, sysLocation (masquerade)
- Set ifAdminStatus (disable interfaces)
- Write enterprise-specific OIDs

## Defenses

- Change community from defaults (use strong random strings)
- Restrict SNMP access by source IP (ACL)
- Use SNMPv3 with USM auth+encryption
- Disable SNMP entirely if not needed
- Monitor for excessive SNMP queries (rate limiting)

## On Windows

Windows has built-in SNMP service (`SNMP` service name). Enable via:
```powershell
Add-WindowsCapability -Online -Name "SNMP.Client~~~~0.0.1.0"
```
Or via "Turn Windows features on/off" → "Simple Network Management Protocol (SNMP)".

The service runs on UDP 161 and uses registry settings in `HKLM\SYSTEM\CurrentControlSet\Services\SNMP\Parameters`.

## Python Scanner (without net-snmp)

See scripts at `scripts_cache/snmp_lab/snmp_scanner.py` and `snmp_quick_probe.py`.

Key probe logic:
```python
import socket
from pyasn1.codec.ber import encoder
from pysnmp.proto import api

pMod = api.PROTOCOL_MODULES[api.SNMP_VERSION_1]

def build_probe(community='public'):
    pdu = pMod.GetRequestPDU()
    pMod.apiPDU.set_defaults(pdu)
    pMod.apiPDU.set_varbinds(pdu, (
        (pMod.ObjectIdentifier((1,3,6,1,2,1,1,5,0)), pMod.Null('')),
        (pMod.ObjectIdentifier((1,3,6,1,2,1,1,1,0)), pMod.Null('')),
    ))
    msg = pMod.Message()
    pMod.apiMessage.set_defaults(msg)
    pMod.apiMessage.set_community(msg, community.encode())
    pMod.apiMessage.set_pdu(msg, pdu)
    return encoder.encode(msg)
```

## nmap Output Interpretation

```
PORT    STATE         SERVICE
161/udp open|filtered snmp
```

`open|filtered` means nmap received no ICMP Port Unreachable — but it doesn't know if the port is actually open or a firewall dropped the probe silently. Only an actual SNMP response confirms the agent is accessible.
