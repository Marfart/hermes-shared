---
name: b2b-customer-scoring
description: "B2B客户分析 + 产品匹配引擎：从爬取数据到产品应用映射的完整管道"
category: sales
triggers:
  - "customer analysis"
  - "product matching"
  - "lead scoring"
  - "客户分析"
  - "产品匹配"
  - "匹配引擎"
  - "客户评分"
---

# B2B Customer Analysis & Product Matching

## Pipeline Overview

```
Raw enriched data (JSON) 
  → customer_analysis.py 
    → Industry classification 
    → Product matching (7 product families) 
    → Fit score (0-10) 
    → Application memo
```

## Installed Tools

| File | Purpose | Location |
|------|---------|----------|
| `bliiot_product_knowledge.py` | Product families + keyword library + match engine | `memories/脚本缓存/客户挖掘/` |
| `customer_analysis.py` | Full analysis pipeline (CLI tool) | `memories/脚本缓存/客户挖掘/` |
| `bliiot_pro_spider.py` | Web scraper (Scrapling-based, 3-layer) | `memories/脚本缓存/客户挖掘/` |

## Product Families (7 families matched to customer needs)

1. **Industrial Gateways** (BL116/BL118/BE116/BA116) — PLC protocol conversion, Modbus→MQTT, cloud connectivity
2. **ARMxy Edge Controllers** — Edge computing, Linux/Node-RED, local processing
3. **Remote IO / RTU** (IOy Series) — DI/DO/AI/AO, Modbus RTU, field data acquisition
4. **R40 Series Routers** — 4G/5G, VPN, remote site connectivity
5. **RTU50xx Series** — SCADA telemetry, remote terminal units
6. **Signal Isolators** (BL15x) — 4-20mA, analog signal conditioning
7. **Software** (BLIoTLink/BLRAT) — PLC remote access, device management

Each family has: keywords[], use_cases[], target_customers[]. See `bliiot_product_knowledge.py` for the full mapping.

## Usage

```bash
# Analyze enriched customer data
python customer_analysis.py enriched_data.json --top 20

# With output report
python customer_analysis.py enriched_data.json --top 15 --output report.json

# Scrape a single company website
python bliiot_pro_spider.py url "https://company.com"

# Search + scrape prospects
python bliiot_pro_spider.py search "system integrator South Africa" 10
```

## Matching Algorithm (simplified)

```python
score = 0
# 1. Keyword hit: +2 per keyword match
# 2. Use case overlap: +1 if >=2 words overlap
# 3. Industry alignment: +1 if target customer type matches
# 4. Scenario bonus: +3 for strong scenario match (e.g., PLC/SCADA → gateway)
```

## Industry Classification

Uses keyword-pattern matching. Current 9 industries:
- SCADA / PLC / Industrial Control
- System Integration
- Energy / Solar / Utility
- Water / Wastewater
- Industrial Automation / Manufacturing
- IIoT / Edge / Telecom
- Oil & Gas / Mining
- Building Automation
- Transportation

## Key Principles

- **Do NOT invent data** — if customer description is empty/missing, set industry to "General Industrial", score = 0
- **Application memo is generated not hardcoded** — `build_why_need()` uses top 3 product types to compose relevant description
- **WhatsApp is priority channel** for African/developing market prospects
- Report output includes: stats (by industry/country/product), top N matches, application memos

## Pitfalls

- ❌ Google Maps data has very short descriptions → match rate <20%
- ✅ JoinF / enriched data has longer descriptions → match rate ~37%
- ❌ Don't hardcode `fitScore` max — it's min(score, 10), but actual max depends on data quality
- ⚠️ Product family names in output should be user-friendly (use short names in reports, full names in JSON)