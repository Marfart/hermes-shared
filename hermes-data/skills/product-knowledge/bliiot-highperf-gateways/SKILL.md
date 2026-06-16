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

## BL118 模块化报价规则 ⚠️

BL118是模块化组合定价：**主机 + SOM + X板 + Y板** 各自单独计价再相加。

**型号命名规则**: `BL118[B]-SOM335-X4-Y02-Y31`
- BL118B = 主机（2个Y板位）
- SOM335 = SOM模块（决定RAM/存储）
- X4 = X系列IO板
- Y02 + Y31 = 两块Y系列IO板

**价格层级取法**:
- 有"Samples"或"Online Store & Quotation"独立列的部件 → 取该列价格
- Y板"Online Store & Quotation"列写"Refer to <100pcs" → 用<100pcs列价格
- X板同理，有独立Sample列取Sample列

**⚠️ SOM335价格修正（2026-06-16）**:
官方报价文件中SOM335价格为$49（Sample），但实际价格为**￥400人民币**。
按汇率6.5换算：￥400 ÷ 6.5 ≈ $62 → 取整。
>=100pcs和Online Store按原比例换算：$58 / $66。
**其他SOM型号可能也有类似偏差，报价前必须向公司确认最新SOM价格！**

### BL118主机价格

| 型号 | <100pcs | >=100pcs | Online Store |
|------|---------|----------|-------------|
| BL118 | $54 | $52 | $56 |
| BL118A | $55 | $54 | $59 |
| BL118B | $58 | $55 | $63 |

### SOM价格（⚠️ 需确认最新价格）

| 型号 | MCU | RAM | eMMC | <100pcs | >=100pcs | Online Store |
|------|-----|-----|------|---------|----------|-------------|
| SOM334 | T113-i | 512MB | 8GB | $30 | $26 | $33 |
| SOM335 | T113-i | 1GB | 8GB | **$62** ⚠️ | **$58** ⚠️ | **$66** ⚠️ |

### X系列IO板价格

| 型号 | 接口 | <100pcs | >=100pcs | Online Store |
|------|------|---------|----------|-------------|
| X4 | 2×RS485 + 2×CAN | $8 | $6 | $9 |

### Y系列IO板价格（双列布局）

左列（DI/DO/AI）：

| 型号 | 描述 | <100pcs | >=100pcs |
|------|------|---------|----------|
| Y02 | 4DI+4DO, PNP | $10 | $9 |
| Y31 | 4AI, 0/4~20mA | $18 | $17 |

右列（AO/RTD/TC/通信）：

| 型号 | 描述 | <100pcs | >=100pcs |
|------|------|---------|----------|
| Y41 | 4AO, 0/4~20mA | $17 | $15 |
| Y51 | 2RTD, PT100 | $15 | $14 |

### 组合计价示例：BL118B-SOM335-X4-Y02-Y31

| 部件 | Sample价 | <100pcs价 |
|------|----------|-----------|
| BL118B 主机 | $63 | $58 |
| SOM335 | $66 ⚠️ | $62 ⚠️ |
| X4 | $9 | $6 |
| Y02 | $10 | $10 |
| Y31 | $18 | $18 |
| **合计** | **$166** | **$154** |

## 文档路径
`产品规格书/英文资料/ARM高性能网关/` 每个型号独立目录

## 定价数据源文件
- BL118报价: `1.报价文件/2026/202605 BLIIOT IIoT Gateways &BL116&BL118 Price List(1).xls`
- **已修正文件**: `1.报价文件/2026/202605 BLIIOT IIoT Gateways &BL116&BL118 Price List_Updated.xls`（SOM335价格已更新）