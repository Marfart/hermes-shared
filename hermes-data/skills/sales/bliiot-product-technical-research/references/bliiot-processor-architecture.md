# BLIIOT Product Processor Architecture Reference

## Quick Answer: Does BLIIOT use ESP32?

**No.** None of BLIIOT's current product lines use ESP32 (Xtensa LX6/LX7) chips.

BLIIOT targets **industrial protocol conversion gateways** — Modbus↔MQTT, Modbus↔OPC UA, Modbus↔IEC104, BACnet, etc. These require:
- Higher processing power (protocol stacks, 512-10,000 data points)
- Industrial temperature range (-40°C to 85°C)
- EMC/EMI industrial immunity
- Multi-network access (4G/WiFi/Ethernet)

ESP32 is common in consumer IoT (smart home, sensor nodes, WiFi-direct devices) but underpowered for BLIIOT's industrial gateway workloads.

## Processor Map by Product Line

### Tier 1: ARM MCU 300MHz (塑胶壳入门级网关)
**Products:** BL101-110, BL101P-110P, BL120/120P series, BE102-115, BA100-115, BL121 series
**Processor:** Embedded ARM MCU @ 300MHz
**Storage:** 128MB RAM, 64MB Flash
**OS:** Linux
**Role:** Protocol conversion gateway (Modbus, PLC, BACnet, IEC104 → MQTT/OPC UA/Cloud)
**Data points:** 512 (standard) / 4000 (P series)
**Notes:** All BL10x/BE10x/BA10x/BL120/BL121 share the same 300MHz ARM MCU platform. The "P" suffix adds more serial ports (6 vs 2) and higher data point capacity, but same processor.

### Tier 2: Dual-Core Cortex-A7 1.2GHz (金属壳高性能网关)
**Products:** BL116, BE116, BA116
**Processor:** 2× Cortex-A7 @ 1.2GHz
**Storage:** Not specified in datasheet (Linux-based)
**OS:** Linux
**Role:** High-performance edge gateway, 10,000 data points, 1,000 points in 1.5s
**Notes:** Titanium metal casing, -40°C to 85°C, isolated RS485, 4G/5G/WiFi

### Tier 3: Allwinner T113-i (Node-RED可编程网关)
**Product:** BL118
**Processor:** Allwinner T113-i (22nm)
  - 2× ARM Cortex-A7 @ 1.2GHz
  - 1× HiFi4 DSP @ 600MHz
  - 1× Xuantie C906 RISC-V (64-bit) @ 1008MHz
**Storage:** 512MB/1GB RAM, 4GB/8GB Flash (configurable via SOM)
**OS:** Linux + Node-RED pre-installed
**Role:** Visual programming edge gateway, drag-and-drop Node-RED
**Notes:** Modular design — X/Y expansion boards for custom I/O. RISC-V co-processor is notable.

### Tier 4: Raspberry Pi CM4/CM5 (ARMxy嵌入式控制器)
**Products:** BL301-370, BL410-460
**Processor:** 
  - CM4: Broadcom BCM2711 (4× Cortex-A72 @ 1.8GHz)
  - CM5: Broadcom BCM2712 (4× Cortex-A76 @ 2.4GHz)
**Storage:** 1-8GB RAM, 0-64GB eMMC
**OS:** Raspberry Pi OS / custom Linux
**Role:** Full edge computer, runs BLIoTLink for protocol conversion
**Notes:** Most flexible platform. Can run custom applications. SD slot only on Lite (0GB eMMC) variants.

### Tier 5: Industrial RTU/Controllers
**Products:** S275, S27x series, RTU50xx series
**Processor:** Various ARM MCUs (not ESP32)
**Role:** Remote Terminal Units for industrial monitoring
**Notes:** S275 is the base for ZODSAT Zimbabwe transformer anti-theft project

## Why Not ESP32?

| Requirement | ESP32 | BLIIOT's ARM MCU / Cortex-A7 |
|-------------|-------|-------------------------------|
| Protocol stacks | Limited (ESP-IDF) | Full Linux + protocol libraries |
| Data points | ~100 max | 512-10,000 |
| Temperature range | -40°C to 85°C (some) | -40°C to 85°C (all) |
| 4G/LTE | External modem | Integrated module |
| RS485 isolation | Not native | Isolated, ESD protection |
| Multi-Ethernet | 1 port | 2 ports (WAN+LAN) |
| Industrial EMC | Limited | Full EMC/EMI testing |

## If Customer Asks for ESP32

If a customer specifically asks for ESP32-based products:
1. BLIIOT does not currently offer ESP32-based gateways
2. The closest alternative is the BL118 (Allwinner T113-i with RISC-V co-processor) for low-cost edge computing
3. For pure WiFi IoT sensor nodes, consider custom ODM development
4. For industrial protocol conversion, the ARM MCU 300MHz series is the entry point
