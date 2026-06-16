# PySNMP 7.x Debugging: From Zero to Working SNMP

Full debugging path from a session where an SNMP agent was built from scratch using pysnmp 7.1.27 on Windows.

## Phase 1: Agent won't respond

**Symptom**: `socket.timeout` when sending SNMP requests to the agent, even though `netstat` shows the port is listening.

**Root cause**: BER encoding uses wrong ASN.1 tags.

**Fix**: Use pysnmp's protocol module types, not raw `univ.Sequence()`.

```python
# WRONG — uses universal Sequence tag 0x30
pdu = univ.Sequence()

# CORRECT — uses context-specific tag 0xA0-0xA5
from pysnmp.proto import api
pMod = api.PROTOCOL_MODULES[api.SNMP_VERSION_1]
pdu = pMod.GetRequestPDU()
```

## Phase 2: `'Tag' object has no attribute 'getTagId'`

**Symptom**: AttributeError when reading PDU tag.

**Root cause**: pyasn1 0.6+ uses `.tagId` (property), not `.getTagId()` (method).

**Fix**:
```python
# WRONG
pdu.getTagSet()[0].getTagId()

# CORRECT
pdu.getTagSet()[0].tagId
```

Needed in both agent and manager code (search all files).

## Phase 3: `'ObjectName' object has no attribute 'split'`

**Symptom**: Error when trying to parse OID from varbind.

**Root cause**: `pMod.apiPDU.get_varbinds()` returns OID as `ObjectName` objects (subclass of ObjectIdentifier), not strings. You can't call `.split('.')` on them.

**Fix**:
```python
# WRONG
oid = tuple(int(x) for x in name_str.split('.'))

# CORRECT
oid = tuple(name_obj)  # ObjectName is iterable → yields ints
```

## Phase 4: Walk infinite loop — same OID every time

**Symptom**: GETNEXT keeps returning the same OID indefinitely.

**Root cause**: `next_oid()` uses `>=` instead of `>`, so when the requested OID exists in MIB, it returns itself.

**Fix**:
```python
def next_oid(base):
    for o in OID_SORTED:
        if o > base:    # strictly greater
            return o
    return None
```

## Phase 5: `Type <TagSet> not found` in set_varbinds

**Symptom**: `PyAsn1Error: Type <TagSet object, tags 64:0:67> not found`

**Root cause**: Custom ASN.1 subclasses of `univ.Integer` with Application-class tags aren't recognized by pysnmp's internal type registry.

**Fix**: Use pysnmp's built-in type aliases from the protocol module:

```python
# WRONG — custom subclass
class TimeTicks(univ.Integer):
    tagSet = univ.Integer.tagSet.tagImplicitly(
        tag.Tag(tag.tagClassApplication, tag.tagFormatSimple, 0x43))

# CORRECT — use pysnmp's types
TimeTicks = pMod.TimeTicks  # From rfc1155
Counter32 = pMod.Counter
Gauge32 = pMod.Gauge
```

## Phase 6: UDP port still in use after killing process

**Symptom**: `OSError: [WinError 10048] address already in use` on restart.

**Root cause**: Windows holds UDP ports for a few seconds after process exit. The PID shifts between kills.

**Fix**: Use PowerShell to reliably find and kill:
```powershell
$pid = Get-NetUDPEndpoint -LocalPort 1161 | Select-Object -ExpandProperty OwningProcess
Stop-Process -Id $pid -Force
Start-Sleep -Seconds 3
```

## Import Reference

Working imports for pysnmp 7.1.27:
```python
from pyasn1.codec.ber import encoder, decoder
from pyasn1.type import univ
from pysnmp.proto import api

pMod = api.PROTOCOL_MODULES[api.SNMP_VERSION_1]

# Available types through pMod:
# pMod.Integer, pMod.OctetString, pMod.Null, pMod.ObjectIdentifier
# pMod.TimeTicks, pMod.Counter, pMod.Gauge, pMod.IpAddress
# pMod.GetRequestPDU, pMod.GetNextRequestPDU, pMod.GetResponsePDU
# pMod.SetRequestPDU, pMod.Message
# pMod.apiPDU, pMod.apiMessage, pMod.apiVarBind
```

## Working Test Snippet

```python
import socket
from pyasn1.codec.ber import encoder, decoder
from pysnmp.proto import api

pMod = api.PROTOCOL_MODULES[api.SNMP_VERSION_1]

# Build GetRequest for sysName.0
pdu = pMod.GetRequestPDU()
pMod.apiPDU.set_defaults(pdu)
pMod.apiPDU.set_varbinds(pdu, (
    (pMod.ObjectIdentifier((1,3,6,1,2,1,1,5,0)), pMod.Null('')),
))
msg = pMod.Message()
pMod.apiMessage.set_defaults(msg)
pMod.apiMessage.set_community(msg, b'public')
pMod.apiMessage.set_pdu(msg, pdu)
data = encoder.encode(msg)

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.settimeout(2)
sock.sendto(data, ('127.0.0.1', 1161))
resp, _ = sock.recvfrom(4096)
sock.close()

rsp_msg, _ = decoder.decode(resp, asn1Spec=pMod.Message())
rsp_pdu = pMod.apiMessage.get_pdu(rsp_msg)
err = int(pMod.apiPDU.get_error_status(rsp_pdu))
vbs = pMod.apiPDU.get_varbinds(rsp_pdu)
for name_obj, val in vbs:
    print(f'{tuple(name_obj)} = {val.asOctets().decode()}')
```
