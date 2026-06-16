#!/usr/bin/env python3
"""
SNMP Agent Simulator (v1) - uses pysnmp proto API for correct BER encoding.
Listens on UDP, responds to GET/GETNEXT/SET requests.

Usage:
  python snmp_agent.py [--port PORT] [--community COM]
"""

import asyncio, argparse
from pyasn1.codec.ber import encoder, decoder
from pyasn1.type import univ, tag
from pysnmp.proto import api

pMod = api.PROTOCOL_MODULES[api.SNMP_VERSION_1]

# Application-specific types - use pysnmp's built-in types from pMod
TimeTicks = pMod.TimeTicks
Counter32 = pMod.Counter  # pysnmp calls it Counter
Gauge32 = pMod.Gauge     # pysnmp calls it Gauge

# MIB: {oid_tuple: (name, value)}
MIB = {}
def set_mib(oid, name, val):
    MIB[oid] = (name, val)

set_mib((1,3,6,1,2,1,1,1,0),  "sysDescr",       pMod.OctetString(b"SNMP Simulator v1.0 - BLIIoT Virtual Gateway"))
set_mib((1,3,6,1,2,1,1,2,0),  "sysObjectID",    pMod.ObjectIdentifier((1,3,6,1,4,1,99999,1)))
set_mib((1,3,6,1,2,1,1,3,0),  "sysUpTime",      TimeTicks(9476123))
set_mib((1,3,6,1,2,1,1,4,0),  "sysContact",     pMod.OctetString(b"admin@example.com"))
set_mib((1,3,6,1,2,1,1,5,0),  "sysName",        pMod.OctetString(b"BLIIoT-BE116-Gateway-01"))
set_mib((1,3,6,1,2,1,1,6,0),  "sysLocation",    pMod.OctetString(b"Shenzhen, China - Rack 3"))
set_mib((1,3,6,1,2,1,1,7,0),  "sysServices",    pMod.Integer(72))
set_mib((1,3,6,1,2,1,2,1,0),  "ifNumber",       pMod.Integer(3))
set_mib((1,3,6,1,2,1,2,2,1,1,1),  "ifIndex.1",  pMod.Integer(1))
set_mib((1,3,6,1,2,1,2,2,1,1,2),  "ifIndex.2",  pMod.Integer(2))
set_mib((1,3,6,1,2,1,2,2,1,1,3),  "ifIndex.3",  pMod.Integer(3))
set_mib((1,3,6,1,2,1,2,2,1,2,1),  "ifDescr.1",  pMod.OctetString(b"eth0 (WAN - 4G/LTE)"))
set_mib((1,3,6,1,2,1,2,2,1,2,2),  "ifDescr.2",  pMod.OctetString(b"eth1 (LAN - 192.168.1.1)"))
set_mib((1,3,6,1,2,1,2,2,1,2,3),  "ifDescr.3",  pMod.OctetString(b"wlan0 (WiFi AP)"))
set_mib((1,3,6,1,2,1,2,2,1,3,1),  "ifType.1",   pMod.Integer(6))
set_mib((1,3,6,1,2,1,2,2,1,3,2),  "ifType.2",   pMod.Integer(6))
set_mib((1,3,6,1,2,1,2,2,1,3,3),  "ifType.3",   pMod.Integer(71))
set_mib((1,3,6,1,2,1,2,2,1,4,1),  "ifMtu.1",    pMod.Integer(1500))
set_mib((1,3,6,1,2,1,2,2,1,4,2),  "ifMtu.2",    pMod.Integer(1500))
set_mib((1,3,6,1,2,1,2,2,1,4,3),  "ifMtu.3",    pMod.Integer(1500))
set_mib((1,3,6,1,2,1,2,2,1,5,1),  "ifSpeed.1",  Gauge32(100000000))
set_mib((1,3,6,1,2,1,2,2,1,5,2),  "ifSpeed.2",  Gauge32(1000000000))
set_mib((1,3,6,1,2,1,2,2,1,5,3),  "ifSpeed.3",  Gauge32(54000000))
set_mib((1,3,6,1,2,1,2,2,1,6,1),  "ifPhysAddr.1", pMod.OctetString(b'\x00\x1a\x2b\x3c\x4d\x5e'))
set_mib((1,3,6,1,2,1,2,2,1,6,2),  "ifPhysAddr.2", pMod.OctetString(b'\x00\x1a\x2b\x3c\x4d\x5f'))
set_mib((1,3,6,1,2,1,2,2,1,6,3),  "ifPhysAddr.3", pMod.OctetString(b'\x00\x1a\x2b\x3c\x4d\x60'))
set_mib((1,3,6,1,2,1,2,2,1,10,1), "ifInOctets.1", Counter32(1847293847))
set_mib((1,3,6,1,2,1,2,2,1,10,2), "ifInOctets.2", Counter32(4294967295))
set_mib((1,3,6,1,2,1,2,2,1,10,3), "ifInOctets.3", Counter32(892374))
set_mib((1,3,6,1,2,1,2,2,1,16,1), "ifOutOctets.1", Counter32(982734987))
set_mib((1,3,6,1,2,1,2,2,1,16,2), "ifOutOctets.2", Counter32(3829347219))
set_mib((1,3,6,1,2,1,2,2,1,16,3), "ifOutOctets.3", Counter32(1234567))
set_mib((1,3,6,1,4,1,99999,1,1,0), "productModel", pMod.OctetString(b"BE116 Edge Gateway"))
set_mib((1,3,6,1,4,1,99999,1,2,0), "firmwareVersion", pMod.OctetString(b"v2.4.1-RELEASE"))
set_mib((1,3,6,1,4,1,99999,1,3,0), "temperatureCelsius", pMod.Integer(25))
set_mib((1,3,6,1,4,1,99999,1,4,0), "humidityPercent", pMod.Integer(68))
set_mib((1,3,6,1,4,1,99999,1,5,0), "connectedDevices", pMod.Integer(12))
set_mib((1,3,6,1,4,1,99999,1,6,0), "relayState", pMod.Integer(1))

WRITABLE = {(1,3,6,1,2,1,1,5,0), (1,3,6,1,2,1,1,6,0),
            (1,3,6,1,4,1,99999,1,3,0), (1,3,6,1,4,1,99999,1,6,0)}

OID_SORTED = sorted(MIB.keys())

def next_oid(base):
    b = tuple(base)
    for o in OID_SORTED:
        if o > b:
            return o
    return None

def make_varbind_items(items):
    """Convert [(oid_tuple, val), ...] to string tuples for pysnmp api."""
    return [(tuple(o), v) for o, v in items]


class AgentProtocol(asyncio.DatagramProtocol):
    def __init__(self, community="public"):
        self.community = community
        self.start_time = None

    def connection_made(self, transport):
        self.transport = transport
        self.start_time = asyncio.get_event_loop().time()
        print(f"[+] SNMP Agent: port={transport.get_extra_info('sockname')[1]} community={self.community}")

    def datagram_received(self, data, addr):
        try:
            resp = self.handle(data)
            if resp:
                self.transport.sendto(resp, addr)
        except Exception as e:
            import traceback, sys
            print(f"[!] Error from {addr}: {e}", flush=True)
            traceback.print_exc(file=sys.stdout)
            sys.stdout.flush()

    def handle(self, data):
        rsp_msg, _ = decoder.decode(data, asn1Spec=pMod.Message())
        community = bytes(pMod.apiMessage.get_community(rsp_msg)).decode()
        req_pdu = pMod.apiMessage.get_pdu(rsp_msg)

        if community != self.community:
            return None

        # Update sysUpTime
        elapsed = int((asyncio.get_event_loop().time() - self.start_time) * 100)
        MIB[(1,3,6,1,2,1,1,3,0)] = ("sysUpTime", TimeTicks(elapsed))

        req_id = pMod.apiPDU.get_request_id(req_pdu)
        req_vbs = pMod.apiPDU.get_varbinds(req_pdu)

        tag_id = req_pdu.getTagSet()[0].tagId

        if tag_id == 0:  # GetRequest
            result = []
            for name_obj, _ in req_vbs:
                oid = tuple(name_obj)
                rec = MIB.get(oid)
                if rec:
                    result.append((name_obj, rec[1]))
                else:
                    result.append((name_obj, pMod.Null('')))
            err_status = 0

        elif tag_id == 1:  # GetNextRequest
            result = []
            for name_obj, _ in req_vbs:
                oid = tuple(name_obj)
                n = next_oid(oid)
                if n:
                    val = MIB[n][1]
                    result.append((univ.ObjectIdentifier(n), val))
                else:
                    result.append((name_obj, pMod.Null('')))
            err_status = 0

        elif tag_id == 3:  # SetRequest
            result = []
            err_status = 0
            for name_obj, val in req_vbs:
                oid = tuple(name_obj)
                if oid in WRITABLE:
                    MIB[oid] = (MIB.get(oid, ("", ""))[0], val)
                    result.append((name_str, val))
                else:
                    err_status = 2
                    break

        else:
            return None

        # Build response
        rsp_pdu = pMod.GetResponsePDU()
        pMod.apiPDU.set_defaults(rsp_pdu)
        pMod.apiPDU.set_request_id(rsp_pdu, req_id)
        pMod.apiPDU.set_error_status(rsp_pdu, err_status)
        pMod.apiPDU.set_error_index(rsp_pdu, 0)
        pMod.apiPDU.set_varbinds(rsp_pdu, tuple(result))

        rsp_msg = pMod.Message()
        pMod.apiMessage.set_defaults(rsp_msg)
        pMod.apiMessage.set_version(rsp_msg, 0)
        pMod.apiMessage.set_community(rsp_msg, community.encode())
        pMod.apiMessage.set_pdu(rsp_msg, rsp_pdu)

        return encoder.encode(rsp_msg)


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=1161)
    parser.add_argument("--community", default="public")
    args = parser.parse_args()

    loop = asyncio.get_running_loop()
    transport, _ = await loop.create_datagram_endpoint(
        lambda: AgentProtocol(args.community),
        local_addr=("127.0.0.1", args.port)
    )
    print("[+] Ready")
    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        transport.close()

if __name__ == "__main__":
    asyncio.run(main())
