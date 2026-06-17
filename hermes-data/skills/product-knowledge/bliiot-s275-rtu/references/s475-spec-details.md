# S475/S475E Detailed Specifications

## S475 Key Specs (from User Manual v1.6.4)

### Networking
- GSM: 850/900/1800/1900MHz quad band
- 3G/4G: Optional WCDMA/TDD-LTE/FDD-LTE (tell sales the target country)
- Dual SIM card (SIM1 active, SIM2 standby)
- Ethernet: 1×RJ45 10/100Mbps
- Protocols: SMS, GPRS/UDP, TCP, MQTT, Modbus RTU, Modbus TCP
- TCP Server mode: up to 5 client connections
- MQTT: Client ID + Username/Password auth, publish/subscribe topics

### Digital Inputs (8×DI)
- 8 channels, compatible dry/wet contact
- DIN0: high-speed pulse counter, max 1MHz
- DIN1-3: low-speed pulse counter, max 1KHz
- DIN1: can also arm/disarm
- Logic levels: 0~0.5V or short = close, +3~30V or open = open

### Analog Inputs (6×AI)
- **24-bit resolution** (vs S275's 12-bit)
- Signal types: **0-5V, 0-20mA, 4-20mA**
- ⚠️ **NO 0-10V range** — this is a critical limitation
- Can switch to PT100 RTD mode for temperature measurement
- Configurable per channel via DIP switch + software

### Relay Outputs (4×DO)
- 5A/30VDC, 5A/250VAC per relay
- Supports pulse output mode

### Temperature & Humidity
- 1×external AM2301 sensor input
- Temp: -40~80°C, ±0.5°C
- Humidity: 0~99%RH, ±3%

### RS485 (2 ports)
- 2×RS485 serial ports
- Modbus RTU Master and Slave simultaneously
- Transparent transmission mode
- Can extend up to 320 I/O tags via Modbus

### Storage
- Built-in 32G SD card
- Saves up to 100,000 historical data and events
- MQTT data retransmission when network disconnects

### Power
- Supply: 9~36VDC, over-voltage and phase-reversal protection
- Standby: 12V/130mA, Working Max: 12V/500mA
- 1×power output for external device
- Backup battery: 3.7V 850mAh (optional, order separately)

### Physical
- Dimension: 70×87×52mm
- Weight: 350g
- IP30 protection class
- DIN35 rail or wall mount

### S475E Differences
- Same I/O as S475
- **No cellular module** — cannot make calls or send SMS alarms
- Ethernet-only communication
- Cheaper than S475 for LAN-only applications

## Model List

| Model | GSM/3G/4G | Ethernet | DI | AI | Relay | T&H | SD Card | Boolean | 16-Bit | 32-Bit | 64-Bit | RS485 Port |
|-------|-----------|----------|----|----|-------|-----|---------|---------|--------|--------|--------|------------|
| S475  | ✓ | ✓ | 8 | 6 | 4 | 1 | 32G | 64 | 128 | 64 | 64 | 2 |
| S475E | ✗ | ✓ | 8 | 6 | 4 | 1 | 32G | 64 | 128 | 64 | 64 | 2 |

## Customer Matching Pitfalls

### 0-10V AI Input Gap
S-series RTUs (S270 through S475) only support:
- 0-5V (voltage)
- 0-20mA / 4-20mA (current)
- PT100 (temperature)

**They do NOT support 0-10V analog input.**

When a customer requests "0-10V analog input" with LTE/MQTT:
1. **S475 + signal conditioner**: Use a 0-10V → 4-20mA transmitter per channel (~$5-15/ch)
2. **BL118 gateway + MxxxT module**: MxxxT supports 0-10V natively, BL118 provides 4G+MQTT
3. **MxxxE (4G version of MxxxT)**: Best single-device solution, but check availability with sales

### S475 vs S275 Decision Guide
- Choose S475 when: need higher AI resolution (24-bit vs 12-bit), 2×RS485, more counters, MQTT, or larger SD storage
- Choose S275 when: basic monitoring is sufficient, cost is priority, only 1×RS485 needed