#!/usr/bin/env python3
"""Quick SNMP probe - just check public/private community, one shot per host."""
import socket, sys
from pyasn1.codec.ber import encoder, decoder
from pysnmp.proto import api

pMod = api.PROTOCOL_MODULES[api.SNMP_VERSION_1]

def build_req(community):
    pdu = pMod.GetRequestPDU()
    pMod.apiPDU.set_defaults(pdu)
    pMod.apiPDU.set_varbinds(pdu, (('1.3.6.1.2.1.1.5.0', pMod.Null('')), ('1.3.6.1.2.1.1.1.0', pMod.Null(''))))
    msg = pMod.Message()
    pMod.apiMessage.set_defaults(msg)
    pMod.apiMessage.set_community(msg, community.encode())
    pMod.apiMessage.set_pdu(msg, pdu)
    return encoder.encode(msg)

def get_varbinds(data):
    rsp_msg, _ = decoder.decode(data, asn1Spec=pMod.Message())
    rsp_pdu = pMod.apiMessage.get_pdu(rsp_msg)
    err = int(pMod.apiPDU.get_error_status(rsp_pdu))
    if err: return f"err #{err}"
    vbs = pMod.apiPDU.get_varbinds(rsp_pdu)
    lines = []
    for name_str, val in vbs:
        raw = val.asOctets() if hasattr(val, 'asOctets') else bytes(val)
        tid = val.getTagSet()[0].tagId
        if tid == 4:
            try: lines.append(raw.decode())
            except: lines.append(f"0x{raw.hex()}")
        elif tid in (2, 65, 66, 67):
            lines.append(str(int(val)))
        elif tid == 6:
            lines.append('.'.join(str(x) for x in val))
        else:
            lines.append(str(val))
    return ' | '.join(lines)

def probe(host, port=161, timeout=1.0):
    for comm in ['public', 'private']:
        try:
            data = build_req(comm)
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(timeout)
            sock.sendto(data, (host, port))
            resp, _ = sock.recvfrom(4096)
            sock.close()
            info = get_varbinds(resp)
            return comm, info
        except socket.timeout:
            continue
        except Exception as e:
            continue
        finally:
            try: sock.close()
            except: pass
    return None, None

if __name__ == '__main__':
    hosts = sys.argv[1:] if len(sys.argv) > 1 else ['127.0.0.1']
    for h in hosts:
        comm, info = probe(h)
        if comm:
            print(f"  {h:15s} community='{comm}'  {info}")
        else:
            print(f"  {h:15s}  ─  no response")
