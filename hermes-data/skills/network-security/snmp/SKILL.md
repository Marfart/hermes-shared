---
name: snmp
category: network-security
tags: [snmp, ber, pysnmp, network-monitoring, protocol, security-audit]
description: SNMP protocol — learning, agent/manager implementation, network scanning, and security auditing.
triggers:
  - user wants to learn SNMP
  - user asks about SNMP scanning / walk / community strings
  - need to build an SNMP agent or manager in Python
  - debugging BER encoding issues with pysnmp
  - network device discovery via SNMP
---

# SNMP Proficency

Simple Network Management Protocol — the universal device management protocol for network gear, industrial gateways, and embedded systems.

## Architecture

```
Manager ──── GET/WALK ────→ Agent (UDP 161)
         ←── RESPONSE ────
         ──── SET ────────→ (modify values)
         ←── TRAP ──────── (async alerts, UDP 162)
```

- **Manager**: polling side (Zabbix, Cacti, your code)
- **Agent**: runs on the managed device (router, switch, gateway)
- **MIB**: Management Information Base — defines the OID tree
- **SMI**: Structure of Management Information — ASN.1 subset for SNMP

## Versions

| Version | Auth | Encryption | Deployed | Notes |
|---------|------|------------|----------|-------|
| v1 (1988) | Plaintext community | ❌ | Declining | Obsolete, rare |
| **v2c** (1993) | Plaintext community | ❌ | **~90%** | Add GetBulkRequest |
| v3 (2002) | USM (user+password) | AES/DES | ~5% | Complex, few devices support |

**Reality**: 95% of SNMP runs v2c with default `public` (read) / `private` (write).

## Core Protocol Operations

| PDU Tag | Operation | Purpose |
|---------|-----------|---------|
| 0xA0 | GetRequest | Fetch exact OID |
| 0xA1 | GetNextRequest | Fetch next lexicographic OID (walk primitive) |
| 0xA2 | GetResponse | Server's answer to any request |
| 0xA3 | SetRequest | Modify OID value |
| 0xA5 | GetBulkRequest | v2c: fetch N rows at once |

## BER Encoding Critical Knowledge

SNMP PDUs use **context-specific** ASN.1 tags (0xA0-0xA5), NOT universal Sequence (0x30).

**WRONG** — agent won't respond:
```python
pdu = univ.Sequence()  # Tag 0x30 — not SNMP!
```

**CORRECT** — use pysnmp protocol types:
```python
from pysnmp.proto import api
pMod = api.PROTOCOL_MODULES[api.SNMP_VERSION_1]
pdu = pMod.GetRequestPDU()    # Has correct 0xA0 tag
pdu = pMod.GetNextRequestPDU()   # 0xA1
pdu = pMod.GetResponsePDU()   # 0xA2
pdu = pMod.SetRequestPDU()    # 0xA3
```

## pysnmp 7.x API (proven to work)

All verified live against a working agent:

### Building a request
```python
pdu = pMod.GetRequestPDU()
pMod.apiPDU.set_defaults(pdu)
pMod.apiPDU.set_varbinds(pdu, (
    (pMod.ObjectIdentifier((1,3,6,1,2,1,1,5,0)), pMod.Null('')),
    (pMod.ObjectIdentifier((1,3,6,1,2,1,1,1,0)), pMod.Null('')),
))
msg = pMod.Message()
pMod.apiMessage.set_defaults(msg)
pMod.apiMessage.set_community(msg, b'public')
pMod.apiMessage.set_pdu(msg, pdu)
data = encoder.encode(msg)
```

### Decoding a response
```python
rsp_msg, _ = decoder.decode(data, asn1Spec=pMod.Message())
rsp_pdu = pMod.apiMessage.get_pdu(rsp_msg)
err = int(pMod.apiPDU.get_error_status(rsp_pdu))
vbs = pMod.apiPDU.get_varbinds(rsp_pdu)
for name_obj, val in vbs:
    oid_tuple = tuple(name_obj)  # ObjectName → tuple
    tid = val.getTagSet()[0].tagId
    if tid == 4:   # OctetString
        text = val.asOctets().decode()
    elif tid == 2: # Integer
        num = int(val)
```

### Building a response (agent side)
```python
rsp_pdu = pMod.GetResponsePDU()
pMod.apiPDU.set_defaults(rsp_pdu)
pMod.apiPDU.set_request_id(rsp_pdu, req_id)
pMod.apiPDU.set_error_status(rsp_pdu, 0)
pMod.apiPDU.set_error_index(rsp_pdu, 0)
pMod.apiPDU.set_varbinds(rsp_pdu, (
    (name_obj, val),
    (pMod.ObjectIdentifier((1,3,6,1,2,1,1,5,0)), pMod.OctetString(b'mydevice')),
))
```

### Data Types
Use pysnmp's built-in types — custom ASN.1 subclasses will FAIL with `set_varbinds`:
```python
TimeTicks = pMod.TimeTicks   # NOT custom class
Counter32 = pMod.Counter     # NOT custom class
Gauge32   = pMod.Gauge       # NOT custom class
```

### Walk Algorithm (GETNEXT loop)
```python
cur = start_oid
while True:
    pdu = pMod.GetNextRequestPDU()
    pMod.apiPDU.set_defaults(pdu)
    pMod.apiPDU.set_varbinds(pdu, ((pMod.ObjectIdentifier(cur), pMod.Null('')),))
    # ... send, receive, decode ...
    for name_obj, val in vbs:
        ot = tuple(name_obj)
        if not matches_prefix(ot, start_oid):  # walked past subtree
            return
        if val.getTagSet()[0].tagId == 5:  # Null = end of MIB
            return
        print(ot, val)
        cur = ot  # advance
```

**CRITICAL**: The agent's `next_oid()` must use `>` not `>=`:
```python
def next_oid(base):
    for o in OID_SORTED:
        if o > base:    # NOT >=
            return o
    return None
```
Using `>=` causes infinite loop — always returns the same OID.

## Network Scanning

```bash
# nmap UDP scan (slow but thorough)
nmap -sU -p 161 --open -n 192.168.1.0/24

# Community string enumeration
snmpwalk -v2c -c public  192.168.1.1 system
snmpwalk -v2c -c private 192.168.1.1 system
```

Common community strings to try: `public`, `private`, `snmp`, `manager`, `admin`, `cisco`, `read`, `write`.

**Note**: `open|filtered` in nmap means firewall is silently dropping probes, not that SNMP is accessible. Use actual SNMP requests to confirm.

## Security Audit

A successful `snmpwalk -c public` on a target can leak:
- Full system description (model, firmware version)
- All interface IPs/MACs/routing table
- Running processes and installed software
- User accounts (on some devices)
- Custom enterprise MIB data

With `private` community (write access):
- Modify hostname, location (masquerade)
- Reboot interfaces (DoS)
- Some devices permit command execution via enterprise MIB tables

## User Preferences

- This is a hacking/security learning topic — KEEP COMPLETELY SEPARATE from BLIIOT work
- Must install tools + set up lab + run them — not just take notes
- Deliverable = working code, not explanation of what you'll do

## Pitfalls

| Issue | Root Cause | Fix |
|-------|-----------|-----|
| Agent not responding | Used `univ.Sequence` instead of `pMod.GetRequestPDU()` | Use pysnmp protocol types |
| `getTagId()` AttributeError | pyasn1 0.6+ uses `.tagId` not `.getTagId()` | Use `.tagId` |
| Walk infinite loop | `next_oid()` uses `>=` instead of `>` | Change to `>` |
| `Type <TagSet> not found` in set_varbinds | Custom ASN.1 subclasses not recognized | Use `pMod.Counter`, `pMod.TimeTicks` etc. |
| UDP port still in use after kill | Windows holds ports briefly | Wait 2-3s; use `Get-NetUDPEndpoint` to find PID |
| ObjectName.split() error | `get_varbinds` returns ObjectName objects, not strings | Use `tuple(name_obj)` to convert |
| pysnmp import errors | Various modules moved between versions | Import from `pysnmp.proto.api` and use `PROTOCOL_MODULES` |
