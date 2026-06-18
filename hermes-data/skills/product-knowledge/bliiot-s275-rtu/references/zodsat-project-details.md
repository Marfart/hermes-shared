# ZODSAT / SmartGrid Africa Transformer Anti-Theft Project

## Customer Contacts
- **Name**: Arnold Chimambo
- **Company**: ZODSAT (Zimbabwe implementation) / SmartGrid Africa (transaction entity)
- **Email**: arnold@smartgrid.co.zw, arnold@zodsat.com
- **Phone**: via WhatsApp
- **Project**: TAIS (Transformer Anti-Intrusion System) — national project, ~50,000 units over 6 years, ~400-700 units/month

## System Architecture
- **Node**: Customized S275 with LoRaWAN module (replacing 4G module)
- **Gateway**: Milesight Solar Gateway SG50 (provided by customer, not BLIIOT's scope)
- **LoRaWAN Frequency**: EU868 (863-870 MHz), 8 multi-SF channels, ADR supported
- **Platform**: ThingsBoard (BLIIOT partner, customer engaging directly)
- **Current alternative platform**: Akenza (Swiss, expensive, being replaced)

## Key Technical Specs (per customer requirements confirmation doc)
- 8× Dry Contact DI (door/motion/PIR/vibration/power/tamper)
- 2× Relay DO (siren + optional load shedding)
- 2× AI (4-20mA or 0-10V, 12-bit)
- PT100 → 4-20mA signal converter (S275 does NOT support direct PT100)
- IoT smart lock (RFID, platform-controlled, mechanical emergency button backup, ~$1.50/unit)
- 8dBi antenna with 3m cable (upgraded from 7dBi per customer's field experience)
- Battery: 12V 5Ah Li-ion, ~$9.94/unit at MOQ 600
- Solar panel: 50W, ~$9.20/unit (customer's supplier: GAMKO)
- MPPT solar charge controller: 100W, ~$6.50/unit at 2000pcs
- Enclosure: custom transponder box with solar panel mounting bracket

## Pricing (from 2026-05-21, based on 50W solar panel)
- Development cost: USD 10,000 (2× samples + shipping)
- 2,000 pcs: USD 149/unit EXW
- 5,000 pcs: USD 144/unit EXW
- 10,000 pcs: USD 139/unit EXW
- Payment: 50% deposit, 50% before shipment

## ⚠️ LoRaWAN Communication Distance: NOT SPECIFIED
Despite reviewing all 3 data sources:
1. Full WhatsApp chat log (_chat.txt, 731 lines)
2. SmartGrid需求说明.pdf (customer's requirement spec)
3. SmartGrid防入侵技术与逻辑规范.pdf (technical/logic spec)

**Arnold Chimambo never mentioned a specific LoRaWAN communication distance.** No km/meter/range figure exists in any document. The only signal-related details are:
- Customer replaces stock antenna with 7dBi + 3m cable for outdoor placement
- Agreed to upgrade to 8dBi antenna
- Building a "nationwide LoRaWAN network"
- The spec doc describes LoRaWAN as "稳健的长距离链路" (robust long-range link) — qualitative only

When asked about distance, the agent should flag this gap and suggest asking the customer: "How far apart are your transformer sites? How many sites per gateway?"

## Key Documents
- `产品规格书/英文资料/S27x系列/S275/` — S275 datasheet & user manual
- `客户项目/津巴布尔客户/WhatsApp 文件记录/_chat.txt` — full WhatsApp transcript
- `C:\Users\Admin\Desktop\SmartGrid需求说明.pdf` — customer requirement spec
- `C:\Users\Admin\Desktop\SmartGrid防入侵技术与逻辑规范.pdf` — anti-intrusion logic spec
- `C:\Users\Admin\Desktop\SmartGrid_Anti_Intrusion_Detailed_Technical and Logical_Specification Doc.pdf` — detailed spec
- `客户项目/津巴布尔客户/签署文件/最初的功能技术确认/BLIIOT_SmartGrid_TAIS Endnode Requirements Confirmation signed 27042026.pdf` — signed requirements

## Status (as of 2026-06-18)
- ✅ Requirements confirmed and signed
- ✅ Pricing quoted (development + volume tiers)
- ✅ Solar panel specs finalized (50W, GAMKO)
- ✅ Battery specs finalized (12V 5Ah Li-ion)
- ✅ IoT lock spec confirmed
- ❌ Customer still waiting for formal technical proposal with production timeline
- ❌ ThingsBoard integration in progress (customer engaging directly)
- ❌ Battery sample status: customer agreed to pay, supplier sent outdated (2023) pricing, new quote pending
