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

**⚠️ SOM335价格修正（2026-06-17）**:
官方报价文件中SOM335价格为$49（Sample），但实际价格为**￥420人民币**（已从￥400更新为￥420）。
按汇率0.148换算：￥420 × 0.148 = $62.16 → 取$62。
>=100pcs和Online Store按原比例换算：$58 / $66。
**其他SOM型号可能也有类似偏差，报价前必须向公司确认最新SOM价格！**

### BL118主机价格

| 型号 | <100pcs | >=100pcs | Online Store |
|------|---------|----------|-------------|
| BL118 | $54 | $52 | $56 |
| BL118A | $55 | $54 | $59 |
| BL118B | $58 | $55 | $63 |

### SOM价格（⚠️ SOM335需确认最新价格）

| 型号 | MCU | RAM | eMMC | 温度 | <100pcs | >=100pcs | Online Store |
|------|-----|-----|------|------|---------|----------|-------------|
| SOM334 | T113-i 2×A7 | 512MB | 8GB | -40~85℃ | $30 | $26 | $33 |
| SOM335 | T113-i 2×A7 | 1GB | 8GB | -40~85℃ | **$62** ⚠️ | **$58** ⚠️ | **$66** ⚠️ |

**⚠️ SOM335官方文件价$49≠实际价￥420 RMB ($62.16)。SOM334目前未见偏差。**

### X系列IO板价格

| 型号 | RS485 | RS232 | CAN | GPIO | PIN | <100pcs | >=100pcs | Online Store |
|------|-------|-------|-----|------|-----|---------|----------|-------------|
| X0 | × | × | × | 8 | 2×5PIN | $5 | $4 | $7 |
| X1 | 4 | × | × | × | 2×5PIN | $8 | $6 | $9 |
| X2 | × | 4 | × | × | 2×5PIN | $8 | $6 | $9 |
| X3 | 2 | 2 | × | × | 2×5PIN | $8 | $6 | $9 |
| X4 | 2 | × | 2 | × | 2×5PIN | $8 | $6 | $9 |
| X5 | × | 2 | 2 | × | 2×5PIN | $8 | $6 | $9 |
| X6 | 2 | × | × | 4 | 2×5PIN | $6 | $5 | $8 |
| X7 | × | 2 | × | 4 | 2×5PIN | $6 | $5 | $8 |
| X8 | 1 | 1 | 1 | 2 | 2×5PIN | $6 | $5 | $8 |

### Y系列IO板完整价格（双列布局）

左列（DI/DO/AI）：

| 型号 | 描述 | <100pcs | >=100pcs |
|------|------|---------|----------|
| Y01 | 4DI+4DO, NPN | $10 | $9 |
| Y02 | 4DI+4DO, PNP | $10 | $9 |
| Y11 | 8DI, NPN | $10 | $9 |
| Y12 | 8DI, PNP | $10 | $9 |
| Y13 | 8DI, Dry Contact | $10 | $9 |
| Y21 | 8DO, PNP | $10 | $9 |
| Y22 | 8DO, NPN | $12 | $11 |
| Y24 | 4DO, Relay | $12 | $11 |
| Y31 | 4AI, single-ended, 0/4~20mA | $18 | $17 |
| Y33 | 4AI, single-ended, 0~5/10V | $18 | $17 |
| Y34 | 4AI, differential, 0~5/10V | $17 | $15 |
| Y36 | 4AI, differential, ±5V/±10V | $17 | $15 |
| Y37 | 4 IEPE Measurement | $970 | $925 |

右列（AO/RTD/TC/通信）：

| 型号 | 描述 | <100pcs | >=100pcs |
|------|------|---------|----------|
| Y41 | 4AO, 0/4~20mA | $17 | $15 |
| Y43 | 4AO, 0~5/10V | $17 | $15 |
| Y46 | 4AO, ±5V/±10V | $17 | $15 |
| Y51 | 2RTD, 3-Wire PT100 | $15 | $14 |
| Y52 | 2RTD, 3-Wire PT1000 | $15 | $14 |
| Y53 | 2RTD, 4-Wire PT100 | $15 | $14 |
| Y54 | 2RTD, 4-Wire PT1000 | $15 | $14 |
| Y56 | Resistance measurement | / | / |
| Y57 | Voltage measurement | / | / |
| Y58 | 4TC | $17 | $15 |
| Y63 | 4 RS485 or RS232 | $14 | $13 |
| Y95 | 4 PWM+4 Pulse Counter, NPN | $23 | $21 |
| Y96 | 4 PWM+4 Pulse Counter, PNP | $23 | $21 |

**⚠️ Y63选中时不能再选第二个Y板**
**⚠️ Y37（IEPE测量）价格异常高（$970），确认非笔误**

### 组合计价示例：BL118B-SOM334-X1-Y01

| 部件 | <100pcs价 |
|------|-----------|
| BL118B 主机（2×100M ETH, 2 Y-board slots） | $58 |
| SOM334（512MB DDR3, 8GB eMMC） | $30 |
| X1（4×RS485） | $8 |
| Y01（4DI+4DO, NPN） | $10 |
| **基础合计** | **$106** |
| + WiFi双频 | +$9 → **$115** |
| + 4G EU/Russia（EC25-EUXGR+GPS） | +$23 → **$129** |

### 组合计价示例：BL118B-SOM335-X4-Y02-Y31

| 部件 | <100pcs价 |
|------|-----------|
| BL118B 主机 | $58 |
| SOM335（1GB DDR3, 8GB eMMC） ⚠️ | $62 ⚠️ |
| X4（2×RS485+2×CAN） | $8 |
| Y02（4DI+4DO, PNP） | $10 |
| Y31（4AI, 0/4~20mA） | $18 |
| **基础合计** | **$156** |

## 4G/5G模块区域映射（报价必备）

WiFi模块和4G/5G模块互斥——只能选一个。

| 模块 | 类型 | GPS | 适用地区 | <100pcs | 备注 |
|------|------|-----|---------|---------|------|
| EC25AFFA-512-SGAS | 4G CAT4 | √ | 北美 | $33 | |
| EC25-AFA | 4G CAT4 | √ | 北美 | $30 | |
| EC25-AUXGA | 4G CAT4 | √ | **拉美**、澳洲、台湾 | $25 | **Peru/巴西/南美客户选这个** |
| EC25-EUXGR | 4G CAT4 | √ | **欧洲/俄罗斯/非洲/中东/亚洲/东南亚** | $23 | **俄罗斯/EU/中东客户选这个** |
| EC200U-EUAB | 4G CAT1 | × | 欧洲 | $12 | 低成本无GPS |
| EC200A-EUHA | 4G CAT4 | × | 欧洲 | $15 | CAT4无GPS |
| EC20-CE | 4G CAT4 | √ | 国内 | $21 | |
| EC20CEHDLG | 4G CAT4 | × | 国内全网通、**印度** | $19 | |
| EC200NCNLA | 4G CAT1 | × | 国内 | $9 | |
| 5G全网通 | 5G | × | 国内 | $58 | |
| 5G Redcap | 5G | × | 国内 | $42 | |
| 双频WiFi | WiFi | — | 2.4G+5.8G | $9 | |
| 单频WiFi | WiFi | — | 2.4G | $8 | |

**选型速查**：
- 印尼/东南亚 → EC25-EUXGR（$23）
- 俄罗斯 → EC25-EUXGR（$23）
- 秘鲁/巴西/拉美 → EC25-AUXGA（$25）
- 中东/非洲 → EC25-EUXGR（$23）
- 印度 → EC20CEHDLG（$19）
- 北美 → EC25AFFA（$33）

## 报价生成工作流（WhatsApp客户→报价文件）

1. **读WhatsApp消息**：Playwright打开WhatsApp Web → 点击客户聊天 → snapshot提取消息内容
2. **解析客户需求**：提取型号、数量、目标国家（决定4G频段）
3. **查价格**：从报价Excel文件中逐项查价（主机+SOM+X板+Y板+4G/WiFi模块各自独立计价）
4. **生成报价**：模块化分项列出 + 备选配置（WiFi版/不同4G模块/无无线模块）
5. **保存到桌面**：`BLIIOT_Quotation_<客户名>_<国家>.txt`
6. **4G模块按客户地区选择**：参照上方区域映射表

### 报价格式模板

```
BLIIOT Quotation — <客户名> (<国家>)
Date: YYYY-MM-DD
Product: <完整型号>
Quantity: N unit(s)

====================================================
Item Breakdown (Unit Price USD):
====================================================

1. <主机型号> Host (...)
   Price: $XX

2. <SOM型号> (...)
   Price: $XX

3. X板 (接口说明)
   Price: $XX

4. Y板 (描述)
   Price: $XX

5. 4G/WiFi模块 (频段, 地区)
   Price: $XX

----------------------------------------------------
Total: $XXX USD
====================================================

====================================================
Alternative Configurations:
====================================================

Option A — With WiFi: <型号W版>
  ...

Option B — With 4G (不同模块): <型号L版>
  ...

====================================================
Shipping to <国家> (DHL/FedEx estimated):
====================================================
...

====================================================
Notes:
====================================================
- All prices are FOB Shenzhen
- Sample price tier (<100pcs) applied
- 4G module and WiFi module are mutually exclusive
- ...
```

### 关键铁律
- BL118/BL460是模块化定价：**主机 + SOM + X板 + Y板 + 无线模块** 各自单独计价再相加
- 有"Samples"/"Online Store & Quotation"独立列的取该列，否则取<100pcs列
- Y板"Online Store"写"Refer to <100pcs"时用<100pcs列价格
- 报价单必须包含备选配置（WiFi版/不同4G模块/无无线模块三种以上）
- 4G模块按客户所在国家/地区选择（见区域映射表）
- 样品单（<10台）用样品价或<100pcs价格层级

## 文档路径
`产品规格书/英文资料/ARM高性能网关/` 每个型号独立目录

## 定价数据源文件
- BL118报价: `1.报价文件/2026/202605 BLIIOT IIoT Gateways &BL116&BL118 Price List_Updated.xls`
- ARMxy报价: `1.报价文件/2025/202512 ARMxy Series Embedded Computer Price List(1).xlsx`（**注意：ARMxy在2025目录，不是2026**）
- RTU报价: `1.报价文件/2026/202605 BLIIOT RTU&Router&Mxxx Price List(1).xls`
- IOy报价: `1.报价文件/2026/202605 BLIIOT IOy Series Edge IO Module Price List.xls`
- 塑胶壳网关报价: `1.报价文件/2026/202605 BLIIOT IIoT Gateways &BL116&BL118 Price List_Updated.xls`（含BA115等Building HVAC区域）
- **⚠️ Excel格式陷阱**: ARMxy文件是.xlsx格式，xlrd无法读取，必须用openpyxl！其他文件是.xls用xlrd