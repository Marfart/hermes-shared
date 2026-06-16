---
name: bliiot-plastic-gateways
description: BLIIoT BL10/BA10/BE10 系列塑胶壳新型网关 — BL101-BL110P / BA100-BA115P / BE102-BE115P 完整规格、选型指南、协议支持
---

# BLIIoT BL10/BA10/BE10 系列塑胶壳新型网关

## 产品线总览

### BL10 系列 — IIoT通用网关
| 型号 | 差异点 | 功能 |
|------|--------|------|
| BL101 | 基础款 | Modbus RTU→MQTT |
| BL101P | +PoE供电 | 支持PoE供电版本 |
| BL102 | 2×串口 | 增强型 |
| BL102P | +PoE | PoE版本 |
| BL103 | CAN+RS485 | 支持CAN总线 |
| BL103P | +PoE | PoE版本 |
| BL104 | 更多功能 | 增强功能版本 |
| BL104P | +PoE | PoE版本 |
| BL110 | 高级型号 | 更多功能配置 |
| BL110P | +PoE | PoE版本 |

### BA10 系列 — BACnet楼宇自控网关
| 型号 | 差异点 | 功能 |
|------|--------|------|
| BA100 | 基础款 | Modbus↔BACnet/IP |
| BA100P | +PoE | PoE版 |
| BA101 | ... | ... |
| BA102 | ... | ... |
| ... | 全系列 100-115P | 每个型号有标准版和PoE版两种 |
| BA115P | 最高型号 | 功能最全 |

### BE10 系列 — 能源/光伏网关
| 型号 | 差异点 | 功能 |
|------|--------|------|
| BE102 | 基础款 | Modbus↔IEC 104/61850 |
| BE102P | +PoE | PoE版 |
| BE103 | 带CAN | 支持CAN总线 |
| ... | 全系列 102-115P | 每个型号有标准版和PoE版 |

## 统一硬件规格
- **处理器**: 300MHz ARM MCU
- **RAM**: 128MB, **Flash**: 64MB
- **以太网**: 2×RJ45 10/100Mbps, MDI/MDIX自适应
- **串口**: 2CH RS485 或 RS232, 2400-115200bps
- **4G**: 可选(L-E/L-CE/L-A/L-AU/L-AF/CAT-1)
- **GPS**: 可选, 跟踪灵敏度 >-148dBm
- **USB**: 1×Micro USB OTG下载 + 1×调试
- **SIM**: 1×NANO SIM卡槽
- **供电**: DC 9~36V, 反接保护
- **功耗**: 70mA@12V(正常), 168mA@12V(最大)
- **尺寸**: 30×83×110mm
- **保护**: ESD ±6kV(接触)/±8kV(空气), EFT 1kV/5kHz
- **WiFi**: 可选 802.11a/b/g/n, 150Mbps, 2.4G+5G

## 协议栈
- BL10: Modbus RTU/TCP↔MQTT, 透明传输, 云平台对接
- BA10: Modbus↔BACnet/IP (BACnet MS/TP)
- BE10: Modbus↔IEC 104 (电力/能源专用)
- 支持: TCP/UDP, DHCP, DNS, 静态IP, SNMP

## 文档路径
`产品规格书/英文资料/BL系列塑胶壳新型网关/`