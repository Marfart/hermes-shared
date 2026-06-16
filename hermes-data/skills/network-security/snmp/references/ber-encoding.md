# SNMP BER Encoding Deep Dive

SNMP uses **BER (Basic Encoding Rules)**, a TLV (Type-Length-Value) format for all wire data.

## Packet Structure (3-layer nest)

```
SNMP Message (Sequence, Tag 0x30)
├── Version (Integer, Tag 0x02)
│   └── 0 = v1, 1 = v2c
├── Community (OctetString, Tag 0x04)
│   └── "public", "private", etc.
└── PDU (Context-Specific, Tag 0xA0-0xA5)
    ├── request-id (Integer, Tag 0x02)
    ├── error-status (Integer, Tag 0x02)
    ├── error-index (Integer, Tag 0x02)
    └── VarBindList (Sequence, Tag 0x30)
        └── VarBind (Sequence, Tag 0x30)
            ├── name (ObjectIdentifier, Tag 0x06)
            └── value (ANY)
```

## PDU Tags (THE critical insight)

Each PDU type uses a **context-specific** tag — Application Class (10), Constructed (1), with a type-specific ID:

| PDU Type | Tag Byte | Tag Decimal | Meaning |
|----------|----------|-------------|---------|
| GetRequest | **0xA0** | 160 | Request to read |
| GetNextRequest | **0xA1** | 161 | Request next OID |
| GetResponse | **0xA2** | 162 | Response to any |
| SetRequest | **0xA3** | 163 | Request to write |
| Trap | **0xA4** | 164 | Async notification |
| GetBulkRequest | **0xA5** | 165 | v2c bulk read |

If you use `univ.Sequence()` (Tag 0x30 = 48), the agent will NOT recognize the message. This is the #1 mistake.

## Wire Example

A GetRequest for sysDescr.0 (`1.3.6.1.2.1.1.1.0`) with community "public":

```
30 26                    ── Sequence(38 bytes)
   02 01 00              ── Integer(1) = 0 (v1)
   04 06 70 75 62 6c 69 63  ── OctetString(6) = "public"
   a0 19                 ── GetRequest(25 bytes)     ← NOTE: a0 not 30!
      02 01 01           ── Integer(1) = request-id
      02 01 00           ── Integer(1) = error-status
      02 01 00           ── Integer(1) = error-index
      30 0e              ── Sequence(14 bytes) = VarBindList
         30 0c           ── Sequence(12 bytes) = VarBind
            06 08 2b 06 01 02 01 01 01 00  ── OID(8) = 1.3.6.1.2.1.1.1.0
            05 00        ── Null(0) = value (empty in request)
```

The GetResponse would be the same structure but with `0xa2` at the PDU position, and actual values instead of Null.

## Value Encoding by Tag

| Tag | Type | Example Wire | Python Decode |
|-----|------|-------------|---------------|
| 0x02 | Integer | `02 01 48` → 72 | `int(val)` |
| 0x04 | OctetString | `04 0c 42 4c 49 49 ...` → "BLIIoT..." | `val.asOctets().decode()` |
| 0x05 | Null | `05 00` | End-of-MIB marker |
| 0x06 | ObjectIdentifier | `06 03 2b 06 01` → 1.3.6.1 | `'.'.join(str(x) for x in val)` |
| 0x41 | Counter32 (App 1) | `41 02 03 e8` → 1000 | `int(val)` |
| 0x42 | Gauge32 (App 2) | `42 04 05 f5 e1 00` → 100000000 | `int(val)` |
| 0x43 | TimeTicks (App 3) | `43 03 90 b2 1b` → 9476123 ticks | `int(val)` → `f"{t//8640000}d ..."` |

## OID Encoding on Wire

OIDs are **compressed** — each byte pair encodes the next integer using a variable-length scheme:

```
1.3.6.1.2.1.1.1.0  →  2b 06 01 02 01 01 01 00
```
- First two components: `40 * first + second` = `40*1+3` = `0x2b`
- Subsequent components: single byte if < 128, otherwise multi-byte with continuation bit

## Wireshark Filter

```
snmp
```
Or for specific operations:
```
snmp.get_request
snmp.get_response
snmp.get_next_request
snmp.set_request
```
