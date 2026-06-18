# MxxxT / MxxxE Series — Ethernet I/O Modules

## Product Overview

MxxxT series: Ethernet I/O modules (1×RJ45, 1×RS485, Modbus TCP + MQTT)
MxxxE series: Same as MxxxT but with **2×RJ45** (dual Ethernet, can cascade)

Both series: 32-bit MCU, metal shell IP30, DIN35 rail, 9~36VDC, -40~85°C

## Model Matrix (from User Manual V4.1)

| Model | DI | AI | DO | AO | TC | RTD | Pulse Counter | Price (<100pcs) |
|:------|:--:|:--:|:--:|:--:|:--:|:---:|:-------------:|:---------------:|
| M100T | 2 | 2 | 2 | — | — | — | DI1 700KHz | $87 |
| M110T | 4 | — | 4 | — | — | — | DI1 700KHz | — |
| M120T | 4 | 4 | 4 | 2 | — | — | DI1 700KHz | $114 |
| M130T | 8 | — | 4 | — | — | — | DI1 700KHz | — |
| M140T | 8 | — | 8 | — | — | — | DI1 700KHz | — |
| M150T | 8 | 4 | 4 | — | — | — | DI1 700KHz | — |
| **M160T** | **8** | **8** | **8** | — | — | — | DI1 700KHz | **$128** |
| M170T | — | — | — | — | — | — | — | — |
| M180T | — | — | — | — | — | — | — | — |
| M200T | — | — | — | 2 | — | — | — | — |
| M210T | 4 | — | — | — | — | — | DI1 700KHz | — |
| M220T | — | — | 4 | — | — | — | — | — |
| M230T | — | 4 | — | — | — | — | — | — |
| M310T | 8 | — | — | — | — | — | DI1 700KHz | — |
| M320T | — | — | 8 | — | — | — | — | — |
| M330T | — | 8 | — | — | — | — | — | — |
| M340T | — | — | — | — | — | 6 RTD | — | — |
| **M350T** | — | — | — | — | **8TC** | — | — | **~$80** |
| M360T | — | — | — | — | — | — | — | — |
| M410T | 16 | — | — | — | — | — | DI1 700KHz | — |
| M420T | — | — | 16 | — | — | — | — | — |
| M320R | — | — | 8DO+8Relay | — | — | — | — | — |

### MxxxE (Dual Ethernet) Pricing

| Model | Same I/O as | Price (<100pcs) |
|:------|:-----------:|:---------------:|
| M100E | M100T | $116 |
| M120E | M120T | $143 |
| **M160E** | **M160T** | **$157** |
| M420E | M420T | $143 |

## Key Specs

- **AI**: 16-bit resolution, supports 0~20mA, 4~20mA, 0-5VDC, **0-10VDC** (select at order, not field-switchable)
- **DI**: Wet contact default, dry contact optional (order-time selection, not field-switchable)
- **Pulse counter**: DI1 = high-speed up to 700KHz; DIN2~DIN12 = low-speed up to 1KHz (anti-jitter 1~2000ms)
- **DO**: Sink output, DO1 supports high-speed pulse output 10Hz~300KHz
- **TC (M350T)**: 8TC, types B/E/J/K/N/R/S/T
- **RTD (M340T)**: 6 RTD, 2/3/4-wire PT100/PT1000
- **RS485**: 1 port, Modbus RTU master/slave, can cascade external Modbus I/O modules
- **Register mapping**: All models support register mapping for cascaded Modbus devices
- **Protocols**: Modbus TCP, Modbus RTU over TCP, MQTT
- **No 4G/LTE**: Ethernet only (MxxxT = 1 port, MxxxE = 2 ports)

## Pricing Data Source

`1.报价文件/202605 BLIIOT RTU&Router Price List.xls` → Sheet "Price List"
- M100T/M120T/M160T/M420T rows
- M100E/M120E/M160E/M420E rows (same I/O, dual Ethernet, ~$29 more)

## Customer Requirement Matching

### All-in-One: DI + AI + TC + Pulse

**No single Mxxx model covers all 4.** Closest combos:

1. **M160T** (8DI+8AI+8DO+pulse) + **M350T** (8TC) = ~$208 — two devices via Ethernet
2. **M160T alone** = 8DI+8AI+pulse ✅ but no TC ❌
3. **M350T alone** = 8TC ✅ but no DI/AI/pulse ❌

### 0-10V AI Support

Unlike S475/S275 (0-5V only), MxxxT/E supports **0-10V** AI natively. This is a key differentiator.
