# IOy Series Edge IO Module Pricing Reference

Source: `202605 BLIIOT IOy Series Edge IO Module Price List.xls`
Date: 2026-05

## Host Modules (202605, <100pcs)

| Model | Uplink Protocol | <100pcs | >=100pcs | Online Store |
|-------|----------------|:-------:|:--------:|:------------:|
| BL190 | Modbus TCP | $37 | $32 | $40 |
| BL191 | OPC UA Server | $47 | $42 | $53 |
| BL192 | MQTT | $45 | $39 | $51 |
| BL192Pro | MQTT, OPC UA, Modbus TCP | $52 | $45 | $60 |
| BL193 | SNMP V3 | $58 | $50 | $65 |
| BA190 | BACnet/IP | $42 | $38 | $45 |
| BA190Pro | BACnet/IP, MQTT, OPC UA, Modbus TCP | $56 | $47 | $66 |

All hosts: 2x100M ETH, 1x RS485, Modbus Master, programmable logic control

## Y-Boards (202605 IOy, <100pcs)

Left column:

| Model | Description | <100pcs | >=100pcs |
|-------|-------------|:-------:|:--------:|
| Y01 | 4DI+4DO, NPN | $12 | $9 |
| Y02 | 4DI+4DO, PNP | $12 | $9 |
| Y11 | 8DI, NPN | $12 | $9 |
| Y12 | 8DI, PNP | $12 | $9 |
| Y13 | 8DI, Dry Contact | $12 | $9 |
| Y21 | 8DO, PNP | $12 | $9 |
| Y22 | 8DO, NPN | $13 | $10 |
| Y24 | 4DO, Relay | $13 | $10 |
| Y31 | 4AI, single-ended, 0/4~20mA | $18 | $15 |
| Y33 | 4AI, single-ended, 0~5/10V | $18 | $15 |
| Y34 | 4AI, differential, 0~5/10V | $17 | $14 |
| Y36 | 4AI, differential, ±5V/±10V | $17 | $14 |
| Y37 | 4 IEPE Measurement | / (deprecated) | / |

Right column:

| Model | Description | <100pcs | >=100pcs |
|-------|-------------|:-------:|:--------:|
| Y41 | 4AO, 0/4~20mA | $19 | $16 |
| Y43 | 4AO, 0~5/10V | $22 | $20 |
| Y46 | 4AO, ±5V/±10V | $22 | $20 |
| Y51 | 2RTD, 3-Wire PT100 | $18 | $16 |
| Y52 | 2RTD, 3-Wire PT1000 | $18 | $16 |
| Y53 | 2RTD, 4-Wire PT100 | $18 | $16 |
| Y54 | 2RTD, 4-Wire PT1000 | $18 | $16 |
| Y56 | Resistance measurement | / | / |
| Y57 | Voltage measurement | / | / |
| Y58 | 4TC | $19 | $17 |
| Y61 | 4 RS485 or RS232 | $17 | $15 |
| Y95 | 4 PWM + 4 Pulse Cnt, NPN | $27 | $24 |
| Y96 | 4 PWM + 4 Pulse Cnt, PNP | $27 | $24 |

Note: Y61 can only be selected once per host (cannot be Y1 + Y2).

## Price Bundling

Price = Host price + Y1 board price + Y2 board price + Y3 board price

Examples:
- BL193-Y11-Y31 (qty=1): $58 + $12 + $18 = $88
- BL190-Y01-Y41 (qty=1): $37 + $12 + $19 = $68

## 202511 Update (for reference)

The 202511 IOy file has lower prices:
- BL193: <100pcs=$50, >=100pcs=$43, Online=$56
- Y11: <100pcs=$10, >=100pcs=$8
- Y31: <100pcs=$15, >=100pcs=$13
