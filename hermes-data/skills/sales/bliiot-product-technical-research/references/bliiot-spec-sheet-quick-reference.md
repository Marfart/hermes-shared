# BLIIOT Product Spec Sheet Quick Reference (Verified 2026-06-23)

## Temperature Ranges (from actual PDF spec sheets)

| Product | Operating Temp | Storage Temp | Humidity | IP Rating | Enclosure |
|---------|---------------|--------------|----------|-----------|-----------|
| R40/R40A/R40B | **-20~+65°C** | -40~+85°C | 5~95% RH | IP30 | Aluminum Alloy |
| S270/S271 | **-20~+70°C** | — | 95% RH | IP30 | Metal |
| S275 | **-20~+70°C** | — | 95% RH | IP30 | Metal |
| IPM100 | **-20~+70°C** | -40~+85°C | — | **IP67** | Potted |
| BL116/BE116/BA116 | -40~+85°C | — | — | IP30 | — |
| BL118 | -45~+80°C | — | — | IP30 | — |

**Key insight**: R40 series operating temp is -20~+65°C, NOT 70°C. If customer strictly needs +70°C, R40 is 5°C short. S27x series and IPM100 cover the full -20~+70°C range.

## R40 Series Detailed Specs (from Data Sheet V2.0)

### R40 (Router-only)
- **CPU**: MIPS 580MHz
- **Memory**: 128MB RAM, 16MB Storage
- **WAN**: 1× RJ45 10/100Mbps
- **LAN**: 3× RJ45 10/100Mbps (PoE optional, IEEE 802.3af/at, 30W/port)
- **WiFi**: 802.11a/b/g/n, 2.4GHz, AP/STA mode, 300Mbps max, 16 clients
- **Cellular**: 4G LTE, 2× SIM slots (drawer-style, 1.8V/3V)
- **Console**: 1× Mini USB
- **RS485/RS232/DI/DO/AI**: ❌ NONE
- **VPN**: IPsec, OpenVPN, L2TP
- **Protocols**: PPP, PPPoE, TCP, UDP, DHCP, ICMP, NAT, HTTP, HTTPS, DNS, ARP, NTP, SMTP, SSH2, DDNS, SNMP
- **Power**: 9~36VDC (standard) or 48~57VDC (PoE version)
- **Current**: 240mA@12V (standard), 70mA@48V (PoE)
- **Protection**: ESD Level 3, EFT Level 3, Reverse polarity
- **Watchdog**: Independent hardware watchdog
- **Mounting**: DIN35 rail, wall mount
- **Weight**: 500g

### R40A (Router + IO + Modbus Master)
- All R40 features PLUS:
- **RS485**: 1× (isolated, ESD Level 3)
- **RS232**: 1× (isolated, ESD Level 3)
- **DI**: 2× (isolated)
- **DO**: 2× (isolated)
- **Modbus**: Master + Slave, up to 2000 data points
- **MQTT**: AWS IoT Core, Alibaba Cloud, Huawei Cloud, Thingsboard
- **Logic control**: Built-in

### R40B (Router + Extended IO)
- All R40A features PLUS:
- **AI**: 4× (12-bit, 0~5V, 0/4~20mA, isolated)
- Otherwise same as R40A

### R40 4G Module Options
| Part Number | Module | GPS | Bands |
|-------------|--------|-----|-------|
| 024031 | EC25AFFA-512-SGA | ✅ | WCDMA:B2,B4,B5; LTE-FDD:B2,B4,B5,B12,B13,B14,B66,B71 |
| 024009 | EC25-AFA MINIPCIE | ✅ | WCDMA:B2,B4,B5; LTE-FDD:B2,B4,B12 |
| 024010 | EC25-AUXGA-PCIE | ✅ | GSM:B2,B3,B5,B8; WCDMA:B1,B2,B5,B8; LTE-FDD:B1,B2,B3,B4,B5,B7,B8,B28; LTE-TDD:B40 |
| 024027 | EC25-EUXGR PCIE | ✅ | GSM:B3,B8; WCDMA:B1,B5,B8; LTE-FDD:B1,B3,B5,B7,B8,B20; LTE-TDD:B38,B40,B41 |
| 024050 | EC200U-EUAB | ❌ | GSM:B2,B3,B5,B8; LTE-FDD:B1,B3,B5,B7,B8,B20,B28; LTE-TDD:B38,B40,B41 |
| 024051 | EC200A-EUHA | ❌ | GSM:B3,B8; WCDMA:B1,B5,B8; LTE-FDD:B1,B3,B5,B7,B8,B20,B28; LTE-TDD:B38,B40,B41 |
| 024034 | EC20CEHDLG-MINI-PCIE-CB | ✅ | GSM:900,1800; CDMA:BC0; WCDMA:B1,B8; TD-SCDMA:B34,B39; LTE-FDD:B1,B3,B5,B8; LTE-TDD:B34,B38,B39,B40,B41 |
| 024026 | EC200NCNLA-N05-MN0CA PCIE | ❌ | LTE-FDD:B1,B3,B5,B8; LTE-TDD:B34,B38,B39,B40,B41 |

## S27x Series Detailed Specs (from Data Sheet V3.0 / V1.2)

### S270
- **MCU**: ARM Cortex-M4 32-bit, 168MHz, RTOS
- **DI**: 2× (dry/wet contact, first can be counter @1MHz, second Arm/Disarm)
- **AI**: 2× (12-bit, 0-5V/0-20mA/4-20mA)
- **Relay**: 2× (5A/30VDC, 5A/250VAC)
- **Temp/Hum sensor**: 1× AM2301 (-40~80°C, 0-99%RH)
- **Serial**: 1× USB (config/firmware)
- **SD Card**: ❌
- **RS485**: ❌
- **Protocols**: SMS, GPRS UDP/TCP, Modbus RTU over TCP, King Pigeon RTU
- **Power**: 9~36VDC, standby 50mA@12V, max 150mA@12V
- **Backup battery**: 3.7V 900mAh
- **SMS**: 10 alert numbers, auto dial, free charge call access control
- **Dimensions**: 195×88×30mm, 650g

### S271
- Same as S270 but: **4DI + 4AI + 4Relay**

### S275
- **DI**: 8×
- **AI**: 6× (supports PT100 RTD via 4-20mA converter)
- **Relay**: 4×
- **RS485**: 1× (Modbus RTU Slave + Master, up to 16 slaves, 320 tags)
- **SD Card**: 8GB built-in (100,000 events)
- **Temp/Hum sensor**: 1× AM2301
- **Power output**: 2× DC for external transducers
- **Dimensions**: 195×88×30mm, 350g
- **Note**: Does NOT support direct PT100 — needs PT100-to-4-20mA converter

## IPM100 (from User Manual V1.0)
- **IP Rating**: IP67 (potting waterproof)
- **DI**: 8× dry contact (also supports wet contact NPN/PNP)
- **Serial**: 1× RS485 (Modbus RTU)
- **Baud rate**: 2400~128000
- **Power**: 9~36VDC, 1W rated
- **Operating temp**: -20~+70°C
- **Storage temp**: -40~+85°C
- **Dimensions**: 55×154×27.5mm
- **Cable**: 8×0.3mm² + 3×0.75mm² (gray)
- **LED**: Power (Red), Signal (Red)
- **NOT a gateway** — just an IO module, needs a master device

## Reading PDF Spec Sheets in This Environment

Use `execute_code` with `fitz` (pymupdf) to extract text from PDF spec sheets:

```python
import fitz

doc = fitz.open(r"<path_to_pdf>")
for i, page in enumerate(doc):
    text = page.get_text()
    if text.strip():
        print(f"--- Page {i+1} ---")
        print(text[:3000])
doc.close()
```

**Important**: The `exec` tool does NOT exist in this environment. Always use `execute_code` for Python script execution.

## IP Rating Summary (Critical for Customer RFQs)

| IP Rating | Products | Notes |
|-----------|----------|-------|
| IP30 | ALL gateways, routers, RTUs | Indoor use only |
| IP65 | IPM100T variant | Tool-free terminal block version |
| IP67 | IPM100 | Potted cable version |

**When customer requires IP65+**: Must use external IP54/IP65 enclosure for any gateway/RTU product. IPM100 (IP67) can be deployed outdoors directly but is just an IO module, not a standalone solution.
