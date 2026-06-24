---
name: bliiot-product-knowledge
description: "BLIIOT 工业物联网产品知识库 — 全产品线规格书、报价、协议支持、选型指南。覆盖ARMxy边缘控制器、IIoT网关、RTU/路由器、IO模块、交换机、隔离器等20+产品系列的完整技术参数和商务信息。"
version: 2.0.0
author: Kali / Tachikoma
tags: [bliiot, product-knowledge, industrial-iot, datasheet, pricing, armxy, gateway, rtu, router, io-module, protocol-conversion]
triggers:
  - "产品规格"
  - "报价"
  - "price list"
  - "datasheet"
  - "specification"
  - "BL116"
  - "BL118"
  - "ARMxy"
  - "BL301"
  - "BL460"
  - "RTU"
  - "R40路由器"
  - "IOy"
  - "protocol support"
  - "IEC104"
  - "Modbus"
  - "OPC UA"
  - "产品选型"
  - "product matching"
---

# BLIIOT 产品知识库

> 深圳钡铼技术有限公司（BLIIOT）工业物联网产品完整知识库。所有产品规格书、报价、协议支持信息集中管理。

## 产品矩阵总览

| 产品线 | 定位 | 处理器 | 关键协议 | 典型应用 |
|--------|------|--------|----------|----------|
| **ARMxy 边缘控制器** | 边缘计算/协议网关 | RPi CM4/CM5 (Cortex-A76) | Modbus, OPC UA, MQTT, IEC104 | 智能工厂、电力监控 |
| **IIoT 高性能网关** (BL116/BL118/BE116/BA116) | 协议转换+边缘计算 | 双核Cortex-A7 1.2GHz | 全协议栈 | 能源、楼宇、工业互联 |
| **塑胶壳网关** (BL10x/BE10x/BA10x/BL120/BL121) | 经济型协议转换 | 300MHz ARM MCU | Modbus, BACnet, OPC UA | 暖通、电力、工业协议转换 |
| **RTU/路由器** (S27x/R40/Mxxx) | 远程监控/4G传输 | ARM Cortex-A7 / MIPS | MQTT, Modbus, 4G LTE | 油田、水务、环境监测 |
| **IOy 远程IO** (BL190/BL191/BL192/BL193) | 分布式I/O模块 | 300MHz ARM | Modbus RTU/TCP, RS485 | 数据采集、工业自动化 |
| **K系列 DTU** (K5/K6/K9) | 无线数据传输 | 多种 | 4G LTE, MQTT | 远程监控、环保 |
| **交换机** (BL16x) | 工业以太网交换 | 工业级 | Ethernet | 工业网络拓扑 |
| **隔离器** (BL15x) | 信号隔离 | 模拟 | 4-20mA, 0-10V | 工业信号传输 |
| **IPM100** | IP67远程IO | 嵌入式 | Modbus RTU, RS485 | 恶劣环境 |

## 选型决策树

```
客户需求
├── 需要边缘计算/本地逻辑？
│   ├── 是 → ARMxy 系列 (BL310~BL460)
│   └── 否 ↓
├── 需要协议转换？
│   ├── 只需要 Modbus RTU/TCP → MQTT
│   │   └── BL120 (经济型, 300MHz ARM)
│   ├── 需要 OPC UA
│   │   └── BL121 (OPC UA 网关)
│   ├── 需要 IEC 61850 (电力)
│   │   └── BE120 (双核Cortex-A7, 钛合金外壳)
│   └── 需要多协议全栈
│       └── BL116/BL118 (高性能网关)
├── 需要本地 I/O (DI/AI/DO/AO)？
│   ├── 是 → BL118 + X/Y 扩展板 (Node-RED)
│   │   或 IOy 远程IO模块 (RS485总线)
│   └── 否 ↓
├── 需要 4G/5G 远程传输？
│   ├── 是 → R40 路由器 (4G+WiFi+以太网+防火墙+VPN)
│   │   或 S275 RTU (4G+IO+RS485)
│   └── 否 ↓
└── 需要 IP67 防护？
    └── IPM100 (IP67远程IO, 8路DI)
```

## 协议支持矩阵

| 协议 | BL120 | BL121 | BL116/BL118 | ARMxy | IOy | R40 | S275 |
|------|:-----:|:-----:|:-----------:|:-----:|:---:|:---:|:----:|
| Modbus RTU/TCP | yes主/从 | yes主/从 | yes主/从 | yes(via BLIoTLink) | yes从 | no | yes主 |
| OPC UA | no | yes服务器 | yes服务器 | yes(via BLIoTLink) | no | no | no |
| MQTT | yes | yes | yes | yes | no | yes | yes |
| BACnet/IP | no | no | yes(BA系列) | yes(via BLIoTLink) | no | no | no |
| IEC 61850 | no | no | yes(BE120) | yes(via BLIoTLink) | no | no | no |
| IEC 60870-5-104 | no | no | yes(BE116) | yes(via BLIoTLink) | no | no | no |
| 4G LTE | yes(可选) | yes(可选) | yes(可选) | no(外接) | no | yes | yes |
| WiFi | no | yes(可选) | yes(可选) | yes(CM4/CM5) | no | yes | no |
| Node-RED | no | no | yes(BL118预装) | yes(可选) | no | no | no |

## 报价体系

详见 `references/quotation-system.md` — 完整的报价文件结构、价格层级规则、4G模块加价、汇率换算方法。

## 产品规格书库

原始规格书存放路径: `C:\Users\Admin\Desktop\Working\产品规格书\英文资料\`

详细的产品规格和技术参数见各子产品参考文件：
- `references/armxy-bl460-series.md` — ARMxy BL310~BL460 边缘控制器完整规格
- `references/iiot-highperf-gateways.md` — BL116/BL118/BE116/BA116 高性能网关
- `references/plastic-gateways.md` — BL10x/BE10x/BA10x/BL120/BL121 塑胶壳网关
- `references/rtu-router-series.md` — S27x/R40/Mxxx RTU和路由器
- `references/ioy-series.md` — IOy 远程IO模块 (BL190~BL193)
- `references/k-series.md` — K5/K6/K9 无线DTU
- `references/switches.md` — BL16x 工业交换机
- `references/isolators.md` — BL15x 信号隔离器
- `references/ipm100.md` — IPM100 IP67远程IO
- `references/bliotlink-software.md` — BLIoTLink 协议转换软件

## 产品技术调研工作流

当客户问"哪个产品支持[协议X]用于[场景Y]"时，按以下流程执行：

### Phase 1: 查询知识库（快速路径）
搜索 `references/` 下的产品参考文件获取协议支持信息。

### Phase 2: 深入规格书（慢速路径）
当参考文件信息不足时，提取原始 DOCX 规格书全文搜索：

```python
import zipfile, xml.etree.ElementTree as ET
ns = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
p = r"C:\Users\Admin\Desktop\Working\产品规格书\英文资料\<category>\<model>\<filename>.docx"
with zipfile.ZipFile(p) as z:
    xml_content = z.read("word/document.xml")
    root = ET.fromstring(xml_content)
    texts = []
    for para in root.iter(f"{ns}p"):
        pt = [t.text for t in para.iter(f"{ns}t") if t.text]
        full = "".join(pt).strip()
        if full: texts.append(full)
```

### Phase 3: 完整扫描（铁律）
回答"哪个产品有XXX功能"之前，必须扫描全部20+产品族。不可跳过的产品族清单见 `references/product-scan-checklist.md`。

### Phase 4: 分层推荐

```
Best Match: — 完全匹配所有需求
Alternative: — 部分满足，有折中
Alternative: — 勉强满足
Gap: — 无产品满足，建议方案
```

## 铁律

1. **产品族完整扫描** — 用户最常纠正的痛点：只查了ARMxy就回答"没有"。必须扫完全部产品线才能下结论。
2. **报价必须核对原始文件** — 数据库价格可能与实际不符，生成报价前必须 cross-check。
3. **SOM335 特殊价** — 文件写$62但实际420 RMB，必须按最新汇率换算。
4. **4G模块加价30 RMB** — 文件价格未含4G模块加价，必须按最新汇率换算后加上。
5. **4G与WiFi互斥** — 同一设备只能选一个无线模块。
6. **BA系列价格来源** — BA110/BA111等最新价格来自202605 IIoT Gateways文件，不是BL10x文件。
7. **displayValue不能为空** — 富通CRM跟进记录API中displayValue字段必须非空。
8. **报价单格式** — 各部件单独列+合计，不要组合单价。

## 关联技能

- `bliiot-sales-pipeline` — 销售管道（客户开发、CRM、邮件营销）
- `bliiot-quotation` — 报价单生成全流程
- `joinf-crm-api` — 富通CRM API操作
