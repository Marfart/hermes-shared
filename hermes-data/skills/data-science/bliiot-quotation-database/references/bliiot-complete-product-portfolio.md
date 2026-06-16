# BLIIoT Complete Product Portfolio

> Source: 103 datasheet .docx files under `产品规格书\英文资料\`
> All specs verified against official BLIIoT datasheets (2025-2026 versions)

---

## 1. ARMxy Embedded Computers (ARM嵌入式控制器)

Flagship product line. Modular: SOM + X Board (communication) + Y Board (I/O). **4000+ combinations.**

### Processor Roadmap

| Series | SoC | Cores | NPU | Max Freq | Node | RAM | eMMC |
|--------|-----|-------|-----|----------|------|-----|------|
| **BL310** | NXP i.MX6ULL | Cortex-A7 ×1 | — | 800MHz | — | — | — |
| **BL330** | Allwinner T113-i | Cortex-A7 ×2 + RISC-V + DSP | — | 1.2GHz | — | 128M~1G DDR3 | 4/8GB |
| **BL335** | Allwinner T113-i | Cortex-A7 ×2 | — | 1.2GHz | — | — | — |
| **BL340** | Allwinner T507-H | **Cortex-A53 ×4** | — | 1.4GHz | — | 1/2GB DDR4 | 8/16GB |
| **BL350** | TI Sitara AM62x | Cortex-A53 ×1/2/4 + M4F | — | 1.4GHz | **16nm** | — | — |
| **BL360** | NXP i.MX8M Mini | **Cortex-A53 ×4** + M4 | — | 1.6GHz | **14nm** | — | — |
| **BL370** 🔥 | Rockchip RK3562/J | Cortex-A53 ×4 + M0 | **1 TOPS** | 1.8/2.0GHz | — | 1/2/4GB LPDDR4X | 8/16/32GB |
| **BL410** 🔥 | Rockchip RK3568J/B2 | **Cortex-A55 ×4** | *indirect* | 1.8/2.0GHz | — | 1/2/4GB LPDDR4X | 8/16/32GB |
| **BL440** 🔥🔥 | Rockchip RK3576J | **Cortex-A72 ×4 + A53 ×4 + M0** | **6 TOPS** | 2.2GHz | — | — | — |
| **BL450** 🔥🔥🔥 | Rockchip RK3588J | **Cortex-A76 ×4 + A55 ×4 + M0 ×3** | **6 TOPS** | 2.0/2.4GHz | — | — | — |

### Common Features (all ARMxy)
- DIN35 rail mount, -40~85°C wide temp
- Ubuntu 20.04 / Docker / Node-RED / Qt
- Pre-installed: BLIoTLink + BLRAT + QuickConfig
- X-series board: RS485/RS232/CAN/GPIO/DI/DO
- Y-series board: DI/DO/AI/AO/Relay/RTD/TC/Pulse
- Mini PCIe for WiFi/4G/5G

### Target Customers by Model

| Model | Best For |
|-------|----------|
| **BL330/335** | Cost-sensitive industrial IoT, photovoltaic, data acquisition |
| **BL340** | Edge computing gateway, energy storage, mid-range control |
| **BL350** | Industrial PLC replacement, **EMS/BMS**, motion control, EV chargers |
| **BL360** | AIoT, video processing, HMI |
| **BL370** 🎯 | **AGV robots, machine vision** (1 TOPS NPU), smart manufacturing |
| **BL440** 🎯 | **Advanced machine vision, AIoT** (6 TOPS NPU), multi-tasking |
| **BL450** 🎯🎯 | **Flagship AI, smart manufacturing, AGV, edge AI** (6 TOPS NPU) |

---

## 2. IOy Series Edge I/O Modules

Programmable remote I/O that can **replace PLC** for simple control tasks.

### Protocol Variants

| Model | Uplink Protocol | Security | Best Fit |
|-------|----------------|----------|----------|
| **BL190** | Modbus TCP | — | Industrial automation, PLC extension |
| **BL191** | **OPC UA Server** | X.509, AES-256, IEC62453 | **IT/OT fusion, SCADA, MES** |
| **BL192** | **MQTT** | — | IoT cloud platforms (AWS/ThingsBoard/Alibaba/Huawei) |
| **BL192Pro** | MQTT + OPC UA + Modbus TCP | Multi-protocol | Complex integration scenarios |
| **BL193** | **SNMP v1/v2c/v3** | SNMP v3 encryption, MIB | **IT network management, data center** |
| **BA190** | **BACnet/IP** | — | **Building automation, BMS, HVAC** |
| **BA190Pro** | BACnet/IP + enhanced | — | Complex building systems |
| **BE190** | **IEC 104** | — | **Power monitoring, substation automation** |

### Common IOy Features
- 2 × 10/100M Ethernet (cascading support)
- 1 × isolated RS485 (Modbus RTU master)
- 1-3 × I/O expansion slots (Y boards)
- Built-in web server for logic control (PLC alternative)
- BLRAT remote maintenance (firmware upgrade, config)
- -45~80°C, electrical isolation, hardware watchdog

### Target Applications (from datasheets)

| Application | Relevant IOy Model |
|-------------|-------------------|
| Smart manufacturing / PLC extension | Any (BL190/191/192/193) |
| Building automation / BMS | **BA190** |
| Power substation / SCADA | **BE190** (IEC 104) |
| Energy storage monitoring | BL191 (OPC UA) or BL192 (MQTT) |
| Wind power generation | BL191/BL192 |
| Subway station equipment monitoring | Any with Y boards |
| Robotic arm I/O | Any with Y boards |
| Agriculture / environmental | BL192 (MQTT → cloud) |
| IT network management / data center | **BL193** (SNMP) |

---

## 3. High-Performance ARM Gateways

### BL116 / BE116 / BA116 Series

All share: dual-core Cortex-A7 @1.2GHz, **10,000 data points in 1.5s**

| Model | Target Market | Uplink Protocols |
|-------|--------------|-----------------|
| **BL116** | IIoT / Smart Factory | MQTT, OPC UA, Modbus TCP, Huawei/AWS/Alibaba Cloud |
| **BE116** | **Smart Grid / Energy** | IEC104, MQTT, OPC UA, Modbus TCP |
| **BA116** | **Building HVAC** | BACnet/IP, BACnet MS/TP, MQTT, OPC UA |

### BE120 — Modbus to IEC61850 Gateway

| Feature | Detail |
|---------|--------|
| **Purpose** | Convert Modbus RTU/TCP to IEC61850 (substation standard) |
| **SCL file** | System Configuration Language file support |
| **Ports** | 4/8 isolated RS485 + dual Ethernet |
| **Temp** | -45~80°C, titanium alloy enclosure |
| **Application** | Smart substation, solar/wind power, power IoT |

### Common Features (all ARM gateways)
- 4/8 isolated RS485/232 serial ports
- Dual Ethernet + WiFi/4G/5G
- OpenVPN, TLS/SSL encryption
- Remote PLC program download
- -40~85°C, titanium metal casing
- Electrical isolation

---

## 4. Plastic Housing Gateways (BL10x / BA10x / BE10x)

Low-cost protocol conversion gateways. Same physical form factor:
- **30mm wide** (standard) or **40mm wide** (P suffix = PoE)
- Compact DIN35 mount

### Sub-series

| Prefix | Protocol | Market |
|--------|----------|--------|
| **BL10x** | Modbus/MQTT/OPC UA | General IIoT |
| **BA10x** | **BACnet** | Building automation |
| **BE10x** | **IEC104/IEC61850** | Power/energy |
| **BL120xx** | **Scenario-specific** | AC=HVAC, BN=BACnet, DT=Data, ML=Multi, PM=Power meter |
| **BL121xx** | Enhanced BL120 series | Same scenarios + PO=Protocol conversion |
| **BE120** | Modbus↔IEC61850 | Smart substation |

---

## 5. RTU Remote Terminal Units

### RTU5024/5034 (GSM/3G relay controller)
- **Up to 200 authorized phone numbers**
- **Caller-ID access control** — dial to trigger relay (no call cost)
- SMS relay confirmation
- **Applications:** Gates, barriers, door access, remote switching, parking

### RTU5025 (Upgraded, 4G)
- **Up to 999 authorized phone numbers**
- 1000 event log (download via USB or GPRS)
- **Digital inputs** for sensor/motion detection → SMS alert
- Android APP (search "3G Gate Opener RTU5025")
- **Applications:** Same as 5024 + security/motion alerts

### Common RTU Use Cases
- Remote gate/door control (no distance limit)
- Parking system access
- Remote equipment ON/OFF
- SMS alert on sensor trigger

---

## 6. IIoT Routers (R40 Series)

### R40 — Industrial 4G Router
- 3 × LAN + 1 × WAN/LAN (PoE optional)
- Dual SIM, auto failover
- WiFi STA/AP, VPN (L2TP/IPSec/OpenVPN)
- Hardware watchdog, -40~85°C
- **Applications:** Unattended rooms, smart city, tunnel, bridge, water, forest fire, ATM

### R40A/R40B — 4G Edge Control Terminal
- Same as R40 + **DI/DO/AI + RS485/232**
- **Built-in edge computing + logic control**
- Modbus master protocol, 2000+ data points
- **Applications:** Same as R40 + data acquisition, edge control

---

## 7. Signal Isolators (BL150~155 Series)

| Series | Type |
|--------|------|
| BL150Ax | Analog input isolator |
| BL151V | Voltage signal isolator |
| BL152Rxx | Resistance/RTD isolator |
| BL153Txx | Temperature (TC) isolator |
| BL154A/V | Analog/Voltage isolator |
| BL155S | Serial signal isolator |

(Note: most datasheets are image-based; no extractable text)

---

## 8. Industrial Ethernet Switches (BL16x Series)

Range: 5-port to 16-port, 100Mbit to Gigabit, managed/unmanaged, PoE/non-PoE.
- BL16x = 100Mbit, BL16xG = Gigabit
- BL16xP = PoE, BL16xM = Managed
- BL16xGM = Gigabit Managed, BL16xGMP = Gigabit Managed PoE
- SFP fiber models available (SFP suffix)
- **Applications:** Industrial network backbone, machine vision, security

---

## 9. EdgePLC Controllers (BL23x~BL246)

Edge controllers supporting **CODESYS / OpenPLC / NexPLC** (IEC 61131-3).

| Model | Processor | Cores | Special |
|-------|-----------|-------|---------|
| **BL233** | Allwinner T113-i | A7 ×2 + RISC-V + DSP | IGH EtherCAT, up to 32 N-series I/O |
| **BL234** | Allwinner T507-H | **A53 ×4** | CODESYS support, motion control option |
| **BL235** | — | — | Mid-range |
| **BL237** 🎯 | Rockchip RK3562/J | A53 ×4 + M0 | **1 TOPS AI NPU + YOLO/OpenCV** |
| **BL241** 🎯 | Rockchip RK3568J/B2 | A55 ×4 | **1 TOPS AI NPU, CODESYS Pro** |
| **BL244** 🎯 | — | — | AI edge controller |
| **BL245** 🎯 | — | — | AI edge controller |
| **BL246** 🎯 | — | — | AI edge controller |

### EdgePLC Common Features
- Ubuntu 20.04 + Docker + Node-RED + Python/C++
- IEC 61131-3 (OpenPLC/NexPLC/CODESYS)
- IGH EtherCAT hard real-time master
- Up to 32x N-series I/O modules (DI/DO/AI/AO/TC/RTD)
- **BL237/BL241/BL244+:** AI vision (YOLOv5/8, OpenCV)

---

## 10. Software Ecosystem (pre-installed on all devices)

| Tool | Function |
|------|----------|
| **BLIoTLink** | Industrial protocol conversion: PLC protocols → cloud/SCADA |
| **BLRAT** | Remote access & maintenance: firmware upgrade, config, debug |
| **QuickConfig** | Web-based quick config: one-click setup, system management |
| **Node-RED** | Visual IoT programming (pre-installed with custom nodes) |
| **BLIoTLink cloud** | BEILAI Cloud platform integration |

---

## Customer Targeting Reference

| Product Line | Best Customer Profile | Search Keywords |
|-------------|----------------------|-----------------|
| **ARMxy BL330-360** | Factory automation, energy storage, photovoltaic | "PLC automation", "industrial control", "energy storage EMS", "photovoltaic monitoring" |
| **ARMxy BL370-450** 🎯 | **AGV, machine vision, AI manufacturing** | "machine vision", "AGV robots", "AI manufacturing", "edge AI inference" |
| **IOy BL191 (OPC UA)** | SCADA/integration projects | "OPC UA integration", "SCADA system", "IT OT convergence", "Industry 4.0" |
| **IOy BL192 (MQTT)** | IoT cloud platform projects | "IoT cloud platform", "AWS IoT", "ThingsBoard", "smart factory" |
| **IOy BA190 (BACnet)** | Building automation contractors | "BACnet BMS", "building automation", "HVAC control", "smart building" |
| **IOy BE190 (IEC 104)** | Power utility / substation | "IEC 104", "power SCADA", "substation automation", "distribution automation" |
| **BE120 (IEC61850)** | Electric utility, substation | "IEC61850 gateway", "smart substation", "power grid monitoring" |
| **BA116/BE116** | Building/energy system integrators | "HVAC gateway", "BACnet gateway", "energy monitoring system" |
| **BL116** | IIoT system integrators | "industrial IoT gateway", "PLC remote monitoring", "edge gateway" |
| **R40/R40A/R40B** | M2M, remote monitoring | "4G router industrial", "remote monitoring", "unattended site" |
| **RTU5024/5025** | Gate/door/access control | "GSM gate opener", "remote relay controller", "access control" |
| **EdgePLC BL237/BL241** 🎯 | **AI manufacturing, smart factory** | "AI edge controller", "machine vision controller", "smart manufacturing" |
| **S250 (discontinued)** | Power transformer anti-theft | "transformer anti-theft", "power facility alarm", "GSM alarm controller" |
