---
name: bliiot-product-technical-research
title: BLIIOT Product Technical Feature Research
description: Search BLIIOT product specification documents (datasheets, manuals) for specific protocols, features, and capabilities — then map findings to customer technical requirements. Used for pre-sales technical qualification, solution engineering, and competitive analysis.
tags: [bliiot, product-research, protocol-analysis, IEC104, pre-sales, solution-engineering]
---

# BLIIOT Product Technical Feature Research

## Overview

When a customer asks "which products support [protocol X] for [use case Y]", this workflow systematically searches the BLIIOT product specification library to find matching products and present actionable recommendations.

The product spec library lives at `~/Desktop/Working/产品规格书/英文资料/` and has an indexed knowledge base at `~/Desktop/Working/Hermes/memories/product-knowledge/` (117 DOCX datasheets pre-extracted).

## Workflow

### Phase 1: Query the indexed knowledge base (fast path)

The file `english_datasheet_catalog.json` contains all 117 datasheet entries with highlights and full text. The file `english_datasheet_knowledge.md` is a human-readable summary by product category.

```python
# Search the indexed KB for protocol/feature mentions
search_files(
    pattern="IEC104|IEC 104|IEC 60870", 
    path="~/Desktop/Working/Hermes/memories/product-knowledge/",
    target="content"
)
```

This returns matches with line numbers, showing which products mention the target protocol/feature.

### Phase 2: Deep-dive into specific datasheets (slow path)

When the KB has shallow matches (e.g. protocol mentioned but timestamp not explicit), extract the full DOCX text programmatically:

```python
import zipfile, xml.etree.ElementTree as ET

p = r"C:\Users\Admin\Desktop\Working\产品规格书\英文资料\<category>\<model>\<filename>.docx"

with zipfile.ZipFile(p) as z:
    xml_content = z.read("word/document.xml")
    root = ET.fromstring(xml_content)
    texts = []
    for para in root.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p"):
        pt = []
        for t in para.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t"):
            if t.text: pt.append(t.text)
        full = "".join(pt).strip()
        if full: texts.append(full)
    
    # Search for keywords
    for kw in ["IEC104", "timestamp", "time stamp", "CP56", "protocol", "downlink", "uplink"]:
        matches = [(i, t) for i, t in enumerate(texts) if kw.lower() in t.lower()]
        for i, t in matches[:8]:
            print(f"P{i}: {t[:300]}")
```

### Phase 3: Understand protocol context for proper recommendations

IEC 104 (IEC 60870-5-104) is a telecontrol protocol for electrical power systems. When asked about it:

- **Timestamp support is implicit in IEC 104** — the protocol defines CP56Time2a time-tagged information objects. Products implementing full IEC 104 stack inherently support timestamped data.
- **NTP/PTP time sync** is a separate feature — supported via Linux-based products that can run NTP client for time synchronization.
- **Downlink IEC 104** = device acts as IEC 104 client, collecting data from power equipment
- **Uplink IEC 104** = device acts as IEC 104 server, reporting to SCADA/dispatch center
- **Both directions** = full gateway capability

### Phase 4: Organize findings by tier

When presenting IEC 104 product matches, rank by relevance:

**Tier 1 (★★★★★) — Purpose-built for the protocol:**
Products explicitly named for the protocol (e.g. BE190 "iec104 EDGE I/O Module") or products whose product name/marketing targets the exact use case (e.g. BE116 "Smart Grid Edge Gateway")

**Tier 2 (★★★★) — Strong protocol support:**
Products where IEC 104 appears on both downlink AND uplink, or where the product family is in the energy/power category (BE10x series)

**Tier 3 (★★★) — Protocol available in one direction:**
Products where IEC 104 appears only as downlink (protocol conversion from IEC 104 to something else) or only as uplink

## ⛔ 鐵律：產品族完整掃描（用戶最常糾正的痛點！）

**用戶明確說過：「我懷疑你沒看」「除了ARMxy以外的其他系列產品呢」——產品掃描不完整是最大的信任受損。**

### 必掃目錄清單

在回答任何「哪個產品有XXX功能」之前，必須掃描以下 **全部** 產品族：

| # | 產品線 | 目錄路徑 | 關鍵類別 |
|---|--------|----------|----------|
| 1 | BL10x/BL10xP | `BL系列塑膠殼新型閘道/BL10系列` | Modbus RTU/TCP→MQTT/O產UA |
| 2 | BL120系列 | `BL系列塑膠殼新型閘道/BL120系列` | BACnet/IEC104/DL645/PLC協議轉換 |
| 3 | BL121系列 | `BL系列塑膠殼新型閘道/BL121系列` | 協議→OPC UA |
| 4 | BE10x系列 | `BL系列塑膠殼新型閘道/BE10系列` | 能源/電力IEC104協議 |
| 5 | BA10x系列 | `BL系列塑膠殼新型閘道/BA10系列` | 樓宇HVAC |
| 6 | BE120系列 | `BL系列塑膠殼新型閘道/BE120系列` | 電力協議 |
| 7 | BL116/BE116/BA116 | `ARM高性能閘道/BL116`（等） | 雙核Cortex-A7 1.2GHz高性能 |
| 8 | **BL118** | `ARM高性能閘道/BL118` | Node-RED + X/Y板I/O擴展 |
| 9 | **IOy系列** | `IOy系列多功能可編程遠程IO/規格書` | BE190/BL190/BL191/BL192/BL193邊緣IO模組 |
| 10 | **MxxxT系列** | `Mxxx 系列/MxxxT/產品說明書` | 乙太網IO模組，內置DI/DO/AI/AO |
| 11 | **R40路由器** | `路由器Rxx/R40` 或 `2025新版R40系列` | **工業4G路由器，含防火牆+DMZ+VPN** |
| 12 | **R10路由器** | `路由器Rxx/R10` | 工業路由器 |
| 13 | ARMxy嵌入式控制器 | `ARM嵌入式控制器/BL301~BL460` | RPi CM4/CM5邊緣計算 |
| 14 | S27x系列 | `S27x系列` | 工業RTU（S275等） |
| 15 | S130/S150 | `S130-150` | 短信控制器/SMS報警 |
| 16 | S47x | `S47x` | 工業控制器 |
| 17 | IPM100 | `IPM100 IP67 IO模組` | IP67遠程IO |
| 18 | K系列 | `K系列/K5/K5s` | 工業控制器 |
| 19 | 隔離器 | `隔離器/規格書` | 信號隔離器BL150系列 |
| 20 | 交換機 | `交換機/BL16系列` | 工業交換機 |

### 掃描方法

**第一步：列出所有產品線（terminal找目錄）**
```bash
find "產品規格書/英文資料" -type d -maxdepth 2 | sort
```

**第二步：從每個產品線找規格文檔（.docx優先，.pdf備用）**
```bash
ls "產品規格書/英文資料/<產品線>/<子目錄>/"
```

**第三步：對每個DOCX提取處理器/協定/I/O關鍵資訊**
```python
import zipfile, xml.etree.ElementTree as ET
# 提取文檔後搜索關鍵字
```

**第四步：對照結果——如果某產品線找不到規格文檔也要註明「已檢查但無文檔」，不能跳過不提**

### 不可跳過的產品線

以下產品線**最容易漏掉**但**對客戶需求至關重要**：

1. **IOy系列** — 邊緣I/O模組，支援DI/AI/DO/AO/RTD/TC，RS485或乙太網連接，是閘道器缺乏本地IO的最佳補充
2. **MxxxT系列** — 乙太網IO模組，自帶8DI+8DO+4AI+2AO等多種型號組合，可獨立工作（無需閘道器）
3. **R40路由器** — 工業4G路由器，**內建防火牆（DMZ/DoS防護/IP過濾/MAC過濾/埠映射/存取控制）+ VPN（IPsec/OpenVPN/L2TP）**。這是BLIIOT唯一有防火牆功能的產品！MIPS CPU 580MHz
4. **R40路由器 RS485/DI/DO/AI版** — R40路由器不僅是路由器，部分版本提供**1×RS485+1×RS232+DI+DO+AI**，支援Modbus主/從、MQTT、邏輯控制功能。這是「路由器+IO+協定轉換」三合一產品！
5. **BL118** — Node-RED預裝 + X/Y板擴展I/O（DI/DO/AI/AO/RTD/TC），適合需要本地I/O的客戶

### 如果客戶需要還沒找到——必須說「已掃全部產品線，未找到」

不要假設某個功能不存在——必須實際掃描了相應產品線的規格書才能下結論。
一定要說清楚：
- 哪些產品線掃了（列出來）
- 哪些沒掃（為什麼，路徑不對還是無文檔）
- 結論是基於完整掃描還是部分掃描
|----------|------|-------------|--------------|
| ARM高性能网关 | `ARM高性能网关/` | BE116, BL116, BL118, BA116 | Full protocol conversion (high-end) |
| IOy系列远程IO | `IOy系列多功能可编程远程IO/` | BE190, BA190, BL190-193 | Protocol-specific Edge I/O modules |
| 塑胶壳新型网关 BA10 | `BL系列塑胶壳新型网关/BA10系列/` | BA102, BA110, BA115 | Building automation + power protocols |
| 塑胶壳新型网关 BE10 | `BL系列塑胶壳新型网关/BE10系列/` | BE102-115 | Energy & photovoltaic gateways |
| 塑胶壳新型网关 BL120 | `BL系列塑胶壳新型网关/BL120系列/` | BL120DT, BL120ML | Dedicated protocol conversion |
| 塑胶壳新型网关 BL121 | `BL系列塑胶壳新型网关/BL121系列/` | BL121DT, BL121ML | Protocol to OPC UA conversion |
| ARM嵌入式控制器 | `ARM嵌入式控制器/` | BL310-460 | Edge computing (protocols via BLIoTLink) |

## Model Naming Convention: ARMxy BL460 Series

BL460 series uses a structured part number. When a customer provides a model like `BL461L-CM5002016-X10`, decode it to understand specs:

### Part Structure

```
BL461L - CM5 00 2 016 - X10
  │        │   │ │  │      │
  │        │   │ │  │      └── I/O expansion board type (e.g. X10 = 2 ETH + 4 RS485)
  │        │   │ │  └──────── eMMC capacity: 000=0GB(Lite) 016=16GB 032=32GB 064=64GB
  │        │   │ └─────────── LPDDR4X RAM: 2=2GB 4=4GB 8=8GB 16=16GB
  │        │   └───────────── Wireless config: 00=no WiFi/BT 10=PCB/ext antenna
  │        └───────────────── Compute Module: CM5=BCM2712(Cortex-A76, 2.4GHz, RPi5-based)
  └────────────────────────── Base variant: 460 (standard), 461 (1ETH variant), etc.
```

### SD Card Slot Rule (critical!)

**SD slot is ONLY present on Lite SOM versions (0GB eMMC).**

| CM5 variant | eMMC | SD Slot | Boot method |
|-------------|------|---------|-------------|
| CM5002000 (Lite) | 0GB | ✅ Has SD slot | Boot from SD card |
| CM5002016 | 16GB | ❌ No SD slot | Boot from eMMC |
| CM5002032 | 32GB | ❌ No SD slot | Boot from eMMC |
| CM5002064 | 64GB | ❌ No SD slot | Boot from eMMC |

### Storage Selection Guide

| Need | Choose | Why |
|------|--------|-----|
| Custom OS / SD card | Lite SOM (0GB eMMC) | SD slot enables OS boot |
| Fast pre-installed boot | 16/32/64GB eMMC | Ship ready-to-run |
| Light data logging | 16GB eMMC | ~1yr metrics per device |
| Heavy edge computing | 64GB eMMC variant | Max onboard storage |

Source: `ARMxy BL460 Datasheet V1.0.docx` at `产品规格书/英文资料/ARM嵌入式控制器/BL460/`

## Understanding Customer Requirements from WhatsApp/Chat Records

BLIIOT's key customers often communicate via WhatsApp. Interpreting their raw messages correctly is critical for pre-sales qualification.

### Key Lesson: Don't Assume the Customer Specified the Sensor

From the ZODSAT Zimbabwe project (Apr-May 2026):
- Customer said: "connect ... temperature, vibration sensors etc"
- BLIIOT proposed: "1 x RS485 / PT100 Interface: For real-time transformer oil temperature monitoring"
- Customer confirmed with no pushback: "thanks we accept any solution as long as we can measure the temperature"
- **BLIIOT proposed PT100, not the customer.** The customer just wanted "temperature measurement."

### Temperature Monitoring in Transformer Anti-Theft Context

When the customer says "temperature from the transformer" in a security/anti-theft context, they don't mean oil temperature as a performance parameter. They mean:

> **Rapid temperature rise sensor** — if someone drains/steals transformer oil, the transformer loses cooling → temperature spikes → alarm triggers.

This is an **anti-theft trigger sensor**, not an oil quality monitoring sensor. The customer cares about detecting the act of theft (oil draining → overheating), not measuring oil temp for maintenance.

When a PT100-to-4-20mA converter is needed (S275 doesn't support direct PT100), the customer typically accepts the workaround — they just want reliable temperature detection.

### Rule: Check the Customer's Own Words

1. Read the customer's exact words — do they specify a sensor type, or just "temperature"?
2. Differentiate between **performance monitoring** (oil temp for maintenance) vs **anti-theft detection** (temp rise = oil stolen)
3. If BLIIOT proposed the sensor type, be transparent about why (e.g. "We recommend PT100 because it's the power industry standard for transformer oil temp")
4. When hardware limits block direct connection, offer alternatives (PT100→4-20mA converter) — customers almost always accept if the function works

### Watch for These Patterns

- **"e.g." vs hard spec** — customers often give example values, not strict specs (e.g. "oil temp exceeding 90°C" was just an example trigger threshold)
- **Current vs new system** — customers describe their CURRENT setup (Milesight UC300) vs what the NEW BLIIOT system should do. Don't conflate the two.
- **"any solution is fine"** = customer's real requirement is the FUNCTION, not the specific technology choice

## Factory OS Image Pre-Installation Workflow (ARMxy Series)

When a customer asks about factory pre-installation of their custom OS image:

### Prerequisites
- Customer develops their application on the BLIIOT hardware
- Customer provides a complete OS image (sector-by-sector raw .img, typically via rpiboot + Win32 Disk Imager)
- File is large: a 16GB eMMC produces a ~15GB raw image; use WeTransfer/OneDrive if email is too small

### What to tell the customer (safe default language)
- **Stage 1 (commitment)**: "The customer can complete the OS development, then we burn it into the device before factory shipment." — This states capability, not a firm promise.
- **Stage 2 (once image arrives)**: "Let our technical team review whether the image can be burned and boot successfully." — Always leave a review step.

### Important nuance
- The image MUST come from the same hardware model (e.g. BL461L image → BL461L production units)
- The image uses rpiboot mode (DIP switches 1&4 ON) to mount eMMC via USB Type-C
- If the image is already working on the customer's dev unit but won't boot on factory units, the issue is typically: wrong image size for target eMMC, boot partition corruption, or missing driver modules for the IO expansion board

### Customer conversation pattern
```
Customer: "If I provide you full image of my gateway, could you install that image 
           at the factory before shipment?"
Agent:    "The customer can complete the OS development, then we burn it into the 
           device before factory shipment."
Later (when image arrives):
Agent:    "I will ask our technical team to review whether the factory can pre-install 
           your image. We need to verify it boots correctly first."
```

### Pricing implication
- Factory pre-installation itself is a free service
- If the customer also wants RTC capacitor upgrades, add ~$2/unit

## RTC Battery / Capacitor Options (ARMxy BL460 Series)

When a customer asks about RTC backup for offline timekeeping:

### Stock configuration
- No battery on board for RTC
- One standard capacitor provides RTC retention only during brief power interruptions
- After power-on + network connect, time syncs via NTP and writes to RTC

### Upgrade options

| Option | Retention | Cost | Notes |
|--------|-----------|------|-------|
| Larger capacitor | ~3 days | +$2/unit | Tested and confirmed viable (May 2026) |
| External NTP server | Unlimited (with power) | $0 | Customer provides local NTP server; QuickConfig pre-configured |
| No upgrade | Minutes to hours (stock cap) | $0 | Only works if device reconnects to network after power restore |

### Key limitation
- **No network = no time sync**, regardless of capacitor/battery. Even with a battery, once it drains, the RTC loses time. After power restore, the device still needs an NTP connection to set the correct time.
- If the device operates in a completely offline environment for months, RTC backup alone is insufficient.

### What to tell the customer
1. Stock capacitor can be upgraded to a larger one → ~3 days RTC retention → +$2/unit
2. For longer offline periods, customer MUST provide an NTP server in their LAN
3. QuickConfig can be pre-installed and configured with the customer's NTP server address

## Temperature Monitoring in Transformer Anti-Theft (Refined)

### Customer intent: NOT oil monitoring, ANTI-THEFT

From the ZODSAT Zimbabwe project (April 2026), the customer (Arnold Chimambo) explicitly explained:

> "As you know the Transformer starts to boil if someone want to extract or steal the oil so it's there to protect it"

The logic chain is:
1. Thief opens transformer valve → drains oil
2. No oil → no cooling → transformer temperature **spikes**
3. PT100 sensor detects abnormal rise → alarm triggers
4. Control center alerts security → intercept theft

This is fundamentally an **anti-theft trigger sensor** — same category as PIR, door contact, and vibration sensors. NOT oil temperature monitoring for maintenance.

### "e.g." vs Hard Spec

When a customer says "oil temperature exceeding 90°C", note the **"e.g."** — it's an example trigger threshold, not a hard specification. The real requirement is "detect abnormal temperature rise caused by oil theft." The specific threshold is configurable in the IF-THEN logic engine.

### Sensor Selection Trap (Critical)

**Do NOT assume the customer specified the sensor type.** In the ZODSAT project:
1. Customer said vaguely: "connect ... temperature, vibration sensors etc"
2. BLIIOT (Kali) proposed PT100 as the solution
3. Customer accepted: "any solution as long as we can measure the temperature"
4. The customer never asked for PT100 specifically — BLIIOT proposed it as standard practice

### Why oil is stolen
- Transformer oil (insulation mineral oil) has resale value on black market
- Thieves drain oil → transformer loses cooling → overheats → further theft of copper windings/scrap metal
- Temperature monitoring catches the FIRST step (oil theft) before further damage

### Transformer Oil Temperature & Boiling Point (Quick Reference)

When a customer asks about temperature ranges or boiling points:

- **Normal transformer oil temp**: 60-80°C (under load)
- **Alarm threshold (typical)**: 90°C — customer's example trigger
- **Transformer oil boiling point**: ~300°C+ (mineral insulation oil, depends on grade)
- **"Boil" in customer context**: NOT literal boiling. Customer uses "boil" colloquially to mean "overheat dangerously." The transformer oil doesn't literally boil at 90°C — the transformer overheats because oil was stolen.
- **PT100 range**: -200°C to +850°C, well within transformer monitoring needs
- **Measurement**: PT100 measures oil temperature inside the transformer tank. Measuring oil temp = measuring transformer temp, since the oil is the thermal medium.

### Transformer Oil Temperature & Boiling Point (Quick Reference)

When a customer asks about temperature ranges or boiling points:

- **Normal transformer oil temp**: 60-80°C (under load)
- **Alarm threshold (typical)**: 90°C — customer's example trigger
- **Transformer oil boiling point**: ~300°C+ (mineral insulation oil, depends on grade)
- **"Boil" in customer context**: NOT literal boiling. Customer uses "boil" colloquially to mean "overheat dangerously." The transformer oil doesn't literally boil at 90°C — the transformer overheats because oil was stolen.
- **PT100 range**: -200°C to +850°C, well within transformer monitoring needs
- **Measurement**: PT100 measures oil temperature inside the transformer tank. Measuring oil temp = measuring transformer temp, since the oil is the thermal medium.
- **Key insight**: When the user asks "为什么是测变压器油温不是测变压器温度" — the answer is that the oil IS the thermal medium inside the transformer. Measuring oil temp = measuring transformer temp. There's no separate "transformer temperature" independent of oil temperature in oil-filled transformers.

### S275 Limitation
- BLIIOT S275 does **NOT** support direct PT100 connection
- Solution: PT100-to-4-20mA signal converter (customer almost always accepts)

## MES / ERP Integration Use Case Pattern

When a customer describes themselves as "a software company adding IoT to machines for MES software" and needs a complete data acquisition + IoT access solution, use this structured analysis.

### Customer Profile Template

```
Customer: [Company name], industrial software developer
Role: Adds IoT connectivity to machines, builds MES software
Need: Industrial-grade MES data acquisition + IoT access solution
Key protocols: Modbus RTU, Modbus TCP, OPC UA, MQTT
Target integration: Sage X3 ERP (or other ERP)
```

### Requirements Breakdown

| Layer | Requirements | BLIIOT Product Fit |
|-------|-------------|-------------------|
| **Field connectivity** | RJ45, RS485/RS232, 24V DC, DIN rail | ✅ All gateways |
| **Protocol conversion** | Modbus RTU/TCP, OPC UA, MQTT | ✅ BL116/BL118/BL10x |
| **Remote access** | VPN, remote config, remote upgrade | ✅ OpenVPN (BL116/BE116/BA116) |
| **Local I/O** | DI, AI, DO for sensors/actuators | ❌ No gateway has onboard I/O → need IOy modules or BL118 with X/Y boards |
| **IT/OT security** | DMZ, firewall, IT/OT isolation | ❌ Not in any gateway → customer must deploy industrial firewall |
| **Platform** | Real-time DB, Historian, KPI reports, alarms | ❌ Not in any gateway → needs ThingsBoard/Ignition SCADA |
| **ERP integration** | Sage X3 ERP | ❌ Not in any gateway → needs middleware via OPC UA/MQTT API |

### Single-Product Recommendation Logic

**If customer needs ONLY protocol conversion + remote access:**
→ **BL116** (dual Cortex-A7, OpenVPN, TLS/SSL, 4/8 RS485, 2×RJ45, 5G option)

**If customer needs local I/O (DI/AI/DO) in the same box:**
→ **BL118** (Node-RED, expandable X/Y boards for DI/DO/AI/AO/RTD/TC)
→ Trade-off: BL118 has NO VPN (only BLRAT remote tool), NO 5G (only 4G)

**If customer needs BOTH VPN AND local I/O:**
→ **BL116 + IOy remote I/O module** (RS485-connected)
→ BL116 handles VPN + protocol conversion
→ IOy module handles DI/AI/DO

### Feature Gap Table (BL116 as baseline)

| Feature | BL116 | BL118 | BL10x/BL120 | IOy Module |
|---------|-------|-------|-------------|------------|
| Modbus RTU/TCP | ✅ | ✅ | ✅ | — |
| OPC UA | ✅ | ✅ | ✅ (BL121) | — |
| MQTT | ✅ | ✅ | ✅ | — |
| OpenVPN | ✅ | ❌ (BLRAT only) | ✅ | — |
| TLS/SSL | ✅ | ❌ (not mentioned) | ✅ | — |
| Local DI/AI/DO | ❌ | ✅ (X/Y boards) | ❌ | ✅ |
| 5G option | ✅ | ❌ (4G only) | ❌ | — |
| Gigabit Ethernet | ❌ (100M) | ✅ (1×Gigabit) | ❌ (100M) | — |
| Node-RED | ❌ | ✅ (pre-installed) | ❌ | — |
| -40°C~85°C | ✅ | ✅ (-45°C~80°C) | ❌ (not specified) | — |
| DIN rail | ✅ | ✅ | ✅ | ✅ |
| 24V DC | ✅ (12~24V) | ✅ (12~36V) | ✅ (9~36V) | ✅ |

### What BLIIOT Cannot Provide (Must Be Customer-Side)

1. **IT/OT network isolation** — BLIIOT gateways are field devices. DMZ, firewall, and network segmentation are the customer's responsibility.
2. **Real-time database / Historian** — This is a platform/SCADA function. Recommend ThingsBoard, Ignition SCADA, or similar.
3. **ERP integration (Sage X3)** — BLIIOT gateways output MQTT/OPC UA. ERP integration requires a middleware layer (Node-RED, custom API gateway, or iPaaS).
4. **KPI dashboards and reports** — These are platform features, not gateway features.

### Recommended Architecture for MES + IoT Access

```
[Field Devices] → [BL116 Gateway] → [MQTT/OPC UA] → [ThingsBoard/Ignition] → [Sage X3 ERP]
     │                    │                    │
  PLCs, sensors        OpenVPN              TLS/SSL
  actuators            remote access         encryption
  (via IOy if DI/AI)   DIN rail, 24V
```

### Customer Conversation Pattern

```markdown
Customer: "We need to connect PLCs, sensors, and actuators via Modbus RTU, 
           Modbus TCP, OPC UA, and MQTT. We need IT/OT isolation, DMZ, 
           firewall, VPN remote maintenance, real-time database, Historian, 
           KPI reports, alarm notifications, and Sage X3 ERP integration."

Agent response structure:
1. ✅ What BLIIOT provides: [BL116/BL118 + features that match]
2. ❌ What BLIIOT doesn't provide: [local I/O, IT/OT isolation, platform, ERP]
3. 🔧 How to fill gaps: [IOy module, ThingsBoard, middleware]
4. 🏆 Single best product: [BL116 if no local I/O needed, BL118 if local I/O needed]
```

## Pitfalls

- **DOCX is the only searchable format** for protocol details. PDFs in the same folder are often image-based (product photos/layouts) and not text-searchable.
- **The word "timestamp" rarely appears explicitly** in BLIIOT specification sheets. It's an implicit feature of protocol implementations, not a separate bullet point. When asked about timestamp, explain it as part of the IEC 104 protocol standard.
- **Product names in the indexed catalog may have OCR/parsing errors** (spaces between letters: "IEC104" vs "IEC 104"). Search both patterns.
- **Two mirrored directory structures** exist: `产品规格书/英文资料/` and `英文资料/`. Always check both or search the one with more content.
- **BLIoTLink software** is the key enabler — all ARMxy edge controllers (BL310-460) run BLIoTLink which supports IEC 104 protocol conversion. For fully custom requirements, these are the most flexible option.
- **Customer terminology matters**: "NT" in power grid contexts usually means National Transmission or Network Transmission (power utility). Don't guess — confirm with the customer.
- **Model numbering traps**: BL461 is NOT a separate product line from BL460 — it's a config variant (different ETH count). Always look for the base model directory first (e.g. BL460/), then find the variant spec within.
- **SD card ≠ microSD card in spec sheets** — BLIIOT specs just say "SD Slot", which on ARMxy products means microSD. Check physical hardware photos to confirm form factor.
- **WhatsApp chat.txt files = full customer conversation** — when a customer asks about sensor ranges/specs, search the WhatsApp logs too. Don't rely solely on formal datasheets. The customer may have already answered their own question in a previous message.
- **R34 resistor removal** (for eMMC partitioning via rpiboot on Windows) uses soldering iron or hot air gun. See `references/armxy-bl460-hardware-gotchas.md` for full details.
- **RS485 auto direction control** is handled by hardware on ARMxy boards — no RTS toggling needed. See `references/armxy-bl460-hardware-gotchas.md`.
- **BLIIOT does NOT use ESP32** in any current product line. All gateways use ARM MCU (300MHz) or Cortex-A7 (1.2GHz) processors. See `references/bliiot-processor-architecture.md` for the full processor map and why ESP32 is unsuitable for industrial gateway workloads.

## Reference Files

- **`references/armxy-bl460-hardware-gotchas.md`** — Hardware quirks for ARMxy BL460 series: R34 resistor removal for eMMC partitioning, RS485 auto direction control, and other board-level gotchas.
- **`references/armxy-bl460-model-naming.md`** — BL460 series part number decoder (BL461L-CM5002016-X10 → CM5 + RAM + eMMC + I/O board).
- **`references/bliiot-processor-architecture.md`** — Full processor map across all BLIIOT product lines, including why ESP32 is not used.
- **`references/iec104-product-compatibility.md`** — IEC 60870-5-104 protocol support across BLIIOT products: which models support downlink/uplink, timestamp (CP56Time2a), and which don't.
- **`references/r40-router-firewall-vpn-capabilities.md`** — R40 industrial cellular router firewall & VPN capabilities: DMZ, DoS protection, IP/MAC/domain filtering, port mapping, access control, IPsec/OpenVPN/L2TP VPN tunnels, and the 3-in-1 router+firewall+IO capability of certain R40 models.
- **`references/lte-data-logger-analog-inputs.md`** — Product matching guide for LTE data logger + MQTT + RS485 + 0-10V/0-20mA analog inputs + counter inputs. Covers S475, S275, MxxxT, MxxxE comparison, the critical 0-10V limitation (S475/S275 don't support it), workaround options, and recommended customer response template.
