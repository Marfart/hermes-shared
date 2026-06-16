#!/usr/bin/env python3
"""
SNMP Manager CLI — snmpget/snmpwalk/snmpset equivalent.
Uses pysnmp proto API for correct BER encoding.

Usage:
  python snmp_manager.py get 1.3.6.1.2.1.1.1.0 [--port 1161]
  python snmp_manager.py walk 1.3.6.1.2.1.1     [--port 1161]
  python snmp_manager.py set sysName.0="NewBox" [--port 1161]
  python snmp_manager.py discover                 [--port 1161]
"""

import asyncio, argparse, sys
from pyasn1.codec.ber import encoder, decoder
from pyasn1.type import univ
from pysnmp.proto import api

pMod = api.PROTOCOL_MODULES[api.SNMP_VERSION_1]

OID_NAMES = {
    (1,3,6,1,2,1,1,1,0): "sysDescr",
    (1,3,6,1,2,1,1,2,0): "sysObjectID",
    (1,3,6,1,2,1,1,3,0): "sysUpTime",
    (1,3,6,1,2,1,1,4,0): "sysContact",
    (1,3,6,1,2,1,1,5,0): "sysName",
    (1,3,6,1,2,1,1,6,0): "sysLocation",
    (1,3,6,1,2,1,1,7,0): "sysServices",
    (1,3,6,1,2,1,2,1,0): "ifNumber",
}

def fmt_oid(oid):
    d = ".".join(str(x) for x in oid)
    n = OID_NAMES.get(tuple(oid), "")
    return f"{d} ({n})" if n else d

def fmt_val(val):
    tid = val.getTagSet()[0].tagId
    if tid == 2: return str(int(val))
    if tid == 4:
        raw = val.asOctets() if hasattr(val, 'asOctets') else bytes(val)
        try: return raw.decode()
        except: return f"0x{raw.hex()}"
    if tid == 5: return "NULL"
    if tid == 6: return ".".join(str(x) for x in val)
    if tid == 67:
        t = int(val)
        return f"{t//8640000}d {(t//360000)%24:02d}:{(t//6000)%60:02d}:{(t//100)%60:02d}"
    if tid in (65, 66): return str(int(val))
    return str(val)

def parse_oid(s): return tuple(int(x) for x in s.strip().split("."))
def oid_str(t): return ".".join(str(x) for x in t)
def matches(oid, prefix):
    return len(oid) >= len(prefix) and oid[:len(prefix)] == prefix


def build_get_msg(oids, community="public"):
    pdu = pMod.GetRequestPDU()
    pMod.apiPDU.set_defaults(pdu)
    pMod.apiPDU.set_varbinds(pdu, tuple((oid_str(o), pMod.Null('')) for o in oids))
    msg = pMod.Message()
    pMod.apiMessage.set_defaults(msg)
    pMod.apiMessage.set_community(msg, community.encode())
    pMod.apiMessage.set_pdu(msg, pdu)
    return encoder.encode(msg)


def build_getnext_msg(oids, community="public"):
    pdu = pMod.GetNextRequestPDU()
    pMod.apiPDU.set_defaults(pdu)
    pMod.apiPDU.set_varbinds(pdu, tuple((oid_str(o), pMod.Null('')) for o in oids))
    msg = pMod.Message()
    pMod.apiMessage.set_defaults(msg)
    pMod.apiMessage.set_community(msg, community.encode())
    pMod.apiMessage.set_pdu(msg, pdu)
    return encoder.encode(msg)


def build_set_msg(items, community="public"):
    """items: [(oid_tuple, value), ...]"""
    vbs = []
    for o, v in items:
        if isinstance(v, str) and v.startswith('"') and v.endswith('"'):
            vbs.append((oid_str(o), pMod.OctetString(v[1:-1].encode())))
        elif isinstance(v, str) and v.isdigit():
            vbs.append((oid_str(o), pMod.Integer(int(v))))
        elif isinstance(v, str):
            vbs.append((oid_str(o), pMod.OctetString(v.encode())))
        elif isinstance(v, int):
            vbs.append((oid_str(o), pMod.Integer(v)))
        elif isinstance(v, bytes):
            vbs.append((oid_str(o), pMod.OctetString(v)))
        else:
            vbs.append((oid_str(o), pMod.OctetString(str(v).encode())))
    pdu = pMod.SetRequestPDU()
    pMod.apiPDU.set_defaults(pdu)
    pMod.apiPDU.set_varbinds(pdu, tuple(vbs))
    msg = pMod.Message()
    pMod.apiMessage.set_defaults(msg)
    pMod.apiMessage.set_community(msg, community.encode())
    pMod.apiMessage.set_pdu(msg, pdu)
    return encoder.encode(msg)


def parse_response(data):
    rsp_msg, _ = decoder.decode(data, asn1Spec=pMod.Message())
    rsp_pdu = pMod.apiMessage.get_pdu(rsp_msg)
    err = int(pMod.apiPDU.get_error_status(rsp_pdu))
    err_map = {0:"noError", 1:"tooBig", 2:"noSuchName", 3:"badValue", 4:"readOnly", 5:"genErr"}
    if err:
        return None, f"SNMP Error: {err_map.get(err, str(err))}"
    vbs = pMod.apiPDU.get_varbinds(rsp_pdu)
    results = [(tuple(int(x) for x in name_str.split('.')), val) for name_str, val in vbs]
    return results, None


class ClientProtocol(asyncio.DatagramProtocol):
    def __init__(self):
        self.response = None
        self.event = asyncio.Event()
    def datagram_received(self, data, addr):
        self.response = data
        self.event.set()


async def query(host, port, data, timeout=3.0):
    loop = asyncio.get_running_loop()
    proto = ClientProtocol()
    transport, _ = await loop.create_datagram_endpoint(
        lambda: proto, remote_addr=(host, port))
    transport.sendto(data)
    try:
        await asyncio.wait_for(proto.event.wait(), timeout=timeout)
        transport.close()
        return parse_response(proto.response)
    except asyncio.TimeoutError:
        transport.close()
        return None, f"Timeout ({timeout}s): {host}:{port}"


async def cmd_get(args):
    oids = [parse_oid(o) for o in args.oids]
    data = build_get_msg(oids, args.community)
    results, err = await query(args.host, args.port, data)
    if err: print(f"ERROR: {err}"); return
    for o, v in results:
        print(f"  {fmt_oid(tuple(o))} = {fmt_val(v)}")


async def cmd_walk(args):
    start = parse_oid(args.oid)
    cur = [start]
    count = 0
    while True:
        data = build_getnext_msg(cur, args.community)
        results, err = await query(args.host, args.port, data)
        if err: print(f"ERROR: {err}"); break
        for o, v in results:
            ot = tuple(o)
            if not matches(ot, start):
                return count
            if v.getTagSet()[0].tagId == 5:  # Null = end
                return count
            print(f"  {fmt_oid(ot)} = {fmt_val(v)}")
            count += 1
            cur = [o]
        if args.max and count >= args.max:
            break
    return count


async def cmd_set(args):
    items = []
    for kv in args.oid_values:
        if "=" not in kv:
            print(f"Invalid: {kv}. Use OID=VALUE"); return
        o, v = kv.split("=", 1)
        items.append((parse_oid(o.strip()), v.strip()))
    data = build_set_msg(items, args.community)
    results, err = await query(args.host, args.port, data)
    if err: print(f"ERROR: {err}"); return
    for o, v in results:
        print(f"  SET {fmt_oid(tuple(o))} = {fmt_val(v)}")


async def cmd_discover(args):
    groups = [
        ((1,3,6,1,2,1,1), "System Group"),
        ((1,3,6,1,2,1,2), "Interfaces Group"),
        ((1,3,6,1,4,1,99999,1), "Enterprise (BLIIoT)"),
    ]
    for start, desc in groups:
        print(f"--- {desc} ---")
        cur = [start]
        while True:
            data = build_getnext_msg(cur, args.community)
            results, err = await query(args.host, args.port, data)
            if err: print(f"  {err}"); break
            for o, v in results:
                ot = tuple(o)
                if not matches(ot, start):
                    cur = []; break
                if v.getTagSet()[0].tagId == 5:
                    cur = []; break
                print(f"  {fmt_oid(ot)} = {fmt_val(v)}")
                cur = [o]
            if not cur:
                break
        print()


def main():
    p = argparse.ArgumentParser(description="SNMP Manager CLI")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=1161)
    p.add_argument("--community", default="public")
    p.add_argument("--max", type=int, default=0)
    args, remaining = p.parse_known_args()

    sp = argparse.ArgumentParser()
    subs = sp.add_subparsers(dest="cmd")
    gp = subs.add_parser("get", help="Get OID values"); gp.add_argument("oids", nargs="+")
    wp = subs.add_parser("walk", help="Walk MIB"); wp.add_argument("oid")
    sp2 = subs.add_parser("set", help="Set OID"); sp2.add_argument("oid_values", nargs="+")
    subs.add_parser("discover", help="Discover agent")
    sub_args = sp.parse_args(remaining)
    if not sub_args.cmd:
        p.print_help(); return
    for k, v in vars(sub_args).items():
        setattr(args, k, v)
    asyncio.run(dispatch(args))


async def dispatch(args):
    cmds = {"get": cmd_get, "walk": cmd_walk, "set": cmd_set, "discover": cmd_discover}
    await cmds[args.cmd](args)


if __name__ == "__main__":
    main()
