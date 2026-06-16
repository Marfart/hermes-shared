---
name: bliiot-highperf-gateways
description: BLIIoT 高性能边缘网关系列 — BL116/BE116/BA116/BL118 完整规格、处理器、接口、协议、应用场景
---

# BLIIoT 高性能边缘网关系列

## 产品总览

| 型号 | 定位 | 处理器 | 协议侧重点 | 预装环境 |
|------|------|--------|-----------|---------|
| BL116 | IIoT通用边缘网关 | 双核CA7@1.2GHz | Modbus/MQTT/OPC UA | BLIoTLink+BLRAT |
| BE116 | 智能电网边缘网关 | 双核CA7@1.2GHz | IEC 61850/IEC 104 | BLIoTLink+BLRAT |
| BA116 | 楼宇暖通边缘网关 | 双核CA7@1.2GHz | BACnet/IP | BLIoTLink+BLRAT |
| BL118 | Node-RED边缘网关 | 双核CA7@1.2GHz | 全协议+Node-RED | Node-RED+BLIoTLink |

## 核心规格

### 共同平台（BL116/BE116/BA116）
- 处理器: 双核Cortex-A7 @1.2GHz
- RAM: 512MB, 存储: 8GB eMMC + SD卡扩展
- 采集: 10,000数据点, 1000点/1.5秒
- 串口: 4~8路隔离RS485/232
- 无线: WiFi/4G/5G可选
- 安全: OpenVPN, TLS/SSL, 远程升级
- 温宽: -40°C ~ 85°C
- 钛合金金属外壳, DIN35导轨

### BL116 — IIoT通用型
- 通用协议转换: Modbus ↔ MQTT/OPC UA/HTTP
- 路由+采集+协议转换三合一
- 应用: 智慧工厂, 智慧能源, 智慧城市

### BE116 — 电网专用型
- Modbus ↔ IEC 61850 / IEC 104
- 应用: 智慧能源, 储能系统

### BA116 — 楼宇专用型
- Modbus ←→ BACnet/IP (MS/TP)
- 应用: 智慧楼宇, HVAC暖通制冷

### BL118 — Node-RED可视化编程型 🌟
- 处理器: 双核CA7@1.2GHz
- RAM/存储: 512MB~1GB / 4GB~8GB Flash
- 预装: Node-RED + Ubuntu 20.04
- 串口: 4~8路隔离RS485/232/CAN
- 扩展IO: GPIO, DI, DO, AI, AO, RTD, TC
- 协议: 西门子/三菱/欧姆龙/施耐德/台达/汇川PLC + Modbus RTU/ASCII/TCP + BACnet + CAN + OPC UA + MQTT + HTTP + WebSocket
- 温宽: -45°C ~ 80°C（注意下限更低）
- 应用: 工业可视化, 边缘计算, 数字化转型

## 通用特性
- 独立硬件看门狗
- 电气隔离(串口/以太网)
- EMC/EMI抗干扰
- 钛合金金属外壳
- DIN35导轨安装
- 预装BLIoTLink+BLRAT

## 文档路径
`产品规格书/英文资料/ARM高性能网关/` 每个型号独立目录