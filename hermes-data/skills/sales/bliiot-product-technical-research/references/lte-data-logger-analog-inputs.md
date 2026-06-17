# LTE Data Logger with Analog Inputs — Product Matching Guide

## Common Customer Requirement Pattern

A recurring pre-sales scenario: customer needs a **LTE/4G data logger** with:

- MQTT connectivity
- RS485 serial port(s)
- 0-10V and/or 0-20mA analog inputs
- Counter/pulse input channels

## Product Comparison Matrix

| Feature | S475 | S275 | MxxxT | MxxxE |
|---------|------|------|-------|-------|
| LTE/4G | ✅ GSM/3G/4G/LTE, dual SIM | ✅ GSM/3G/4G/LTE | ❌ Ethernet only | ✅ (from product images) |
| MQTT | ✅ Full client (pub/sub) | ✅ Supported | ✅ Supported | ✅ Likely |
| RS485 | ✅ **2×RS485** | ⚠️ **1×RS485** | ✅ 1×RS485 | ✅ 1×RS485 |
| AI type | 0-5V / 0-20mA / 4-20mA | 0-5V / 0-20mA / 4-20mA | **0-10V** / 0-5V / 0-20mA / 4-20mA | Likely same as MxxxT |
| AI resolution | **24-bit** | 12-bit | 16-bit | 16-bit |
| Counter inputs | ✅ DIN0: 1MHz, DIN1-3: 1KHz | ⚠️ Only DIN0 (1MHz) | ✅ DIN1: 700KHz, DIN2-12: 1KHz | Likely same as MxxxT |
| DI channels | 8 | 8 | Up to 16 | Up to 16 |
| DO/Relay | 4 relay | 4 relay | Up to 16 DO | Up to 16 DO |
| SD card | 32GB | 8GB | — | — |
| Backup battery | ✅ 3.7V 850mAh | ✅ | — | — |
| Price tier | Mid | Low | Low-Mid | Mid |

## Critical Limitation: 0-10V Analog Input

**S475 and S275 do NOT support 0-10V analog input.** Their AI range is:
- 0-5V
- 0-20mA
- 4-20mA

**Only MxxxT (and likely MxxxE) support 0-10V** (16-bit resolution).

### Workaround Options

| Option | Description | Pros | Cons |
|--------|-------------|------|------|
| **Use 0-20mA instead** | If customer accepts current signal | No extra hardware | May not match existing sensors |
| **0-10V → 4-20mA converter** | External signal converter (~$5-15/ch) | Works with any sensor | Extra cost, extra wiring |
| **S475 + MxxxT combo** | S475 for LTE/MQTT, MxxxT for 0-10V AI via RS485 | Full feature coverage | Two devices, more complex |
| **MxxxE (if available)** | 4G version of MxxxT | Single device | No datasheet available |

## MxxxE Series — Unknown Territory

From product images in `产品规格书/英文资料/Mxxx 系列/MxxxE/MXXXE主图/`:
- Models seen: M120E, M160E, M420E
- These appear to be the **4G/LTE cellular version** of the MxxxT Ethernet I/O series
- **No datasheet, user manual, or specification document exists** in the product spec library
- Only product images and a configuration software ZIP are available

**When a customer asks about MxxxE:**
> "We have M120E, M160E, and M420E models in our product line, but we currently do not have published datasheets. Please contact our sales team (bl42@bliiot.com) for confirmed specifications."

## Recommended Response Template

When a customer asks for "LTE data logger with MQTT, RS485, 0-10V/0-20mA, and counter inputs":

```
Thank you for your inquiry. We have reviewed our product line and found the following options:

**Best match: S475** — Cellular IoT RTU
- ✅ LTE/4G (dual SIM), MQTT, 2×RS485
- ✅ 6× analog inputs: 0-20mA / 4-20mA / 0-5V (24-bit)
- ✅ 4× counter inputs (DIN0: 1MHz, DIN1-3: 1KHz)
- ⚠️ Does NOT support 0-10V directly — only 0-5V / 0-20mA
- 🔧 Workaround: external 0-10V to 4-20mA signal converter

**If 0-10V is mandatory:**
- MxxxT series has 0-10V support but NO LTE (Ethernet only)
- MxxxE series (M120E/M160E/M420E) may be the 4G version — please contact sales for confirmed specs

Please let us know if 0-20mA is acceptable, or if you need the 0-10V workaround.
```

## Source Documents

- S475 User Manual V1.6.4: `产品规格书/英文资料/S47x/产品说明书/BLIIoT S475 S475E_usermanual_v1.6.4.pdf`
- S275 Datasheet V1.2: `产品规格书/英文资料/S27x系列/停用/S273_274_275/产品规格书/S273-S275_Data Sheet_V1.2.pdf`
- MxxxT User Manual V4.1: `产品规格书/英文资料/Mxxx 系列/MxxxT/产品说明书/BLIIoT MxxxT series Ethernet IO Module_User Manual_V4.1.pdf`
- MxxxE product images: `产品规格书/英文资料/Mxxx 系列/MxxxE/MXXXE主图/`
