# BLIIOT IEC 104 Protocol Product Compatibility Matrix

*Last updated: 2026-06-08 | Source: 117 datasheets from 产品规格书/英文资料/*

## Summary

IEC 104 (IEC 60870-5-104) is the telecontrol network protocol for electrical power systems. BLIIOT has **30+ products** supporting IEC 104 across 4 product families.

## Tier 1 — Purpose-built for Power/IEC 104

### BE116 Smart Grid Edge Gateway
- **File**: `ARM高性能网关/BE116/BLIIOT BE116 High-Performance Smart Grid Edge Gateways Data Sheet V1.0.docx`
- **CPU**: Dual-core Cortex A7
- **Data Points**: Up to 10,000
- **Downlink IEC 104**: ✓ (as BT: Siemens, Mitsubishi, Omron, Delta PLCs, Modbus RTU/TCP, DL/T645, IEC104, BACnet/IP, MS/TP)
- **Uplink IEC 104**: ✓ (as UP: IEC104, MQTT, OPC UA, AWS IoT, Alibaba Cloud, Thingsboard, Ignition SCADA)
- **Certifications**: EMC/EMI, -40°C~85°C
- **Application**: Smart grid, energy & power IoT, substation monitoring
- **Best for**: Transformer/substation data aggregation + dispatch center reporting

### BE190 IEC104 Edge I/O Module (IOy Series)
- **File**: `IOy系列多功能可编程远程IO/规格书/BLIIOT BE190 IOy Series IEC104 Edge IO Module Data Sheet V1.0.docx`
- **Interfaces**: 2×10/100M Ethernet (cascading), 1×isolated RS485 (Modbus RTU Master → IEC104)
- **Protocol**: Standard IEC104, Modbus RTU → IEC104 conversion
- **Application scenarios documented in datasheet**:
  - Smart substation automation monitoring (breakers, disconnects, analog data)
  - Distribution network automation terminal (ring main units, switching stations)
  - New energy power plant centralized control (PV/wind farm inverters, box transformers)
  - Power grid dispatch data gateway (Modbus → IEC104 information objects)
  - Energy storage system monitoring
  - Remote power equipment monitoring & fault diagnosis (generators, transformers)

## Tier 2 — Strong Bidirectional IEC 104

### BE115 / BE115P Energy & Photovoltaic Gateway
- **Downlink**: BACnet/IP, MS/TP, Modbus RTU/TCP, DL/T645, IEC104, Siemens/Mitsubishi/Omron/Delta PLCs, AC protocols
- **Uplink**: **IEC104**, OPC UA, Modbus RTU/TCP, MQTT, AWS/Huawei/Alibaba IoT, Thingsboard, BLIIOT Cloud
- **Capacity**: 10/50 devices, 512/4000 data points
- **Note**: BE115P is the only non-BE116 product with IEC 104 on BOTH downlink AND uplink

## Tier 3 — Uplink IEC 104 (BE10x Energy Gateways)

These products collect data from field devices (via various downlink protocols) and **report upstream via IEC 104**:

| Model | Downlink Protocols | Capacity | Best For |
|-------|-------------------|----------|----------|
| **BE102 / BE102P** | Modbus RTU/TCP Master | 10/50 dev, 512/4000 pts | Pure Modbus instrument → IEC 104 |
| **BE103 / BE103P** | DL/T645, Modbus RTU/TCP | 10/50 dev, 512/4000 pts | Electric meter → IEC 104 |
| **BE104 / BE104P** | BACnet/IP, MS/TP, Modbus RTU/TCP | 10/50 dev, 512/4000 pts | Building power → IEC 104 |
| **BE107 / BE107P** | Siemens/Mitsubishi/Omron/Delta PLCs, Modbus RTU/TCP | 10/50 dev, 512/4000 pts | PLC plant → IEC 104 |
| **BE108 / BE108P** | AC protocols, Modbus RTU/TCP | 10/50 dev, 512/4000 pts | HVAC/power → IEC 104 |
| **BE110 / BE110P** | Siemens/Mitsubishi/Omron/Delta PLCs, DL/T645, BACnet, AC protocols, Modbus | 10/50 dev, 512/4000 pts | Full multi-protocol → IEC 104 |

## Tier 3 — Downlink IEC 104 (BE11x / BA10x Gateways)

These products **accept IEC 104 as a source protocol** and convert to other uplink protocols:

| Model | Downlink (incl. IEC 104) | Uplink | Best For |
|-------|-------------------------|--------|----------|
| **BE111 / BE111P** | Modbus RTU/TCP, DL/T645, IEC104 | Modbus RTU/TCP | IEC 104 → Modbus conversion |
| **BE112 / BE112P** | DL/T645, IEC104, Modbus RTU/TCP | OPC UA | IEC 104 → OPC UA for SCADA |
| **BE113 / BE113P** | Modbus RTU/TCP, DL/T645, IEC104 | MQTT (AWS/Huawei/Alibaba/Thingsboard) | IEC 104 → Cloud IoT |
| **BA102 / BA102P** | DL/T645, IEC104, Modbus RTU/TCP | BACnet/IP, MS/TP | Power meter → BACnet building mgmt |
| **BA110 / BA110P** | DL/T645, IEC104, BACnet, PLCs, AC, Modbus | BACnet/IP, MS/TP | Full bldg + power → BACnet |
| **BA115 / BA115P** | BACnet, Modbus, DL/T645, IEC104, PLCs, AC | BACnet, OPC UA, Modbus, MQTT + clouds | Versatile multi-protocol → cloud |

## Tier 4 — Dedicated Protocol Conversion Gateways

These are single-purpose gateway variants in the BL120 and BL121 series:

| Model | Function | Downlink | Uplink |
|-------|----------|----------|--------|
| **BL120DT** | DL/T645, IEC104 → Modbus | DL/T645, IEC104 | Modbus RTU/TCP (512 pts, 10 dev) |
| **BL120DTP** | DL/T645, IEC104 → Modbus (high-cap) | DL/T645, IEC104 | Modbus RTU/TCP (4000 pts, 50 dev) |
| **BL120ML** | Multi-protocol → Modbus | Modbus RTU/TCP, **IEC104**, DL/T645, BACnet | Modbus RTU/TCP (512 pts) |
| **BL120MLP** | Multi-protocol → Modbus (high-cap) | Modbus RTU/TCP, **IEC104**, DL/T645, BACnet | Modbus RTU/TCP (4000 pts) |
| **BL121DT** | DL/T645, IEC104 → OPC UA | DL/T645, IEC104 | OPC UA (512 pts, 10 dev) |
| **BL121DTP** | DL/T645, IEC104 → OPC UA (high-cap) | DL/T645, IEC104 | OPC UA (4000 pts, 50 dev) |
| **BL121ML** | Multi-protocol → OPC UA | Modbus RTU/TCP, **IEC104**, DL/T645, BACnet | OPC UA (512 pts) |
| **BL121MLP** | Multi-protocol → OPC UA (high-cap) | Modbus RTU/TCP, **IEC104**, DL/T645, BACnet | OPC UA (4000 pts) |

## ARMxy Edge Controllers (via BLIoTLink Software)

All ARMxy edge controllers (BL310, BL330, BL335, BL340, BL350, BL360, BL370, BL410, BL440, BL450, BL460) run **BLIoTLink** industrial protocol conversion software. The datasheets mention protocol capabilities at a high level but do NOT explicitly list IEC 104 in the extraction highlights. BLIoTLink is known to support IEC 104 as part of its protocol library — verify the specific BLIoTLink version for exact protocol support.

## Timestamp Support

No BLIIOT datasheet explicitly lists "timestamp" as a separate feature. However:

- **IEC 104 protocol inherently supports timestamped data** via CP56Time2a (7-byte time tag: millisecond + minute + hour + day + month + year + weekday). Any product implementing IEC 104 protocol stack automatically supports timestamped information objects.
- **NTP time synchronization** is available on all Linux-based products (all ARMxy controllers, BE116, BL116/BL118), enabling accurate time sync for IEC 104 timestamping.
- **BE190** specifically documents use cases that require data logging with timestamps (substation monitoring, fault recording), implying timestamp support in the IEC 104 implementation.

## Key Product Paths in Filesystem

```
产品规格书/英文资料/
├── ARM高性能网关/
│   └── BE116/*                     ← Primary: Smart Grid Gateway (dual IEC104)
├── IOy系列多功能可编程远程IO/
│   └── 规格书/BE190*               ← Primary: Dedicated IEC104 I/O Module
├── BL系列塑胶壳新型网关/
│   ├── BE10系列规格书/BE102-115*   ← Primary: Energy/PV gateways (uplink IEC104)
│   ├── BA10系列规格书/BA102-115*   ← Building automation (downlink IEC104)
│   ├── BL120系列规格书/BL120DT-DTP* ← Dedicated IEC→Modbus gateways
│   └── BL121系列规格书/BL121DT-DTP* ← Dedicated IEC→OPC UA gateways
```
