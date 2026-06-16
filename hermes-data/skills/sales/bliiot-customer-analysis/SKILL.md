---
name: bliiot-customer-analysis
description: BLIIOT customer data analysis pipeline. Enriched JSON input → product matching → DOCX report + XLSX spreadsheet with application memos.
version: 1.0.0
metadata:
  hermes:
    tags: [bliiot, sales, customer-analysis, product-matching, report-generation]
    category: sales
---

# BLIIOT Customer Analysis Pipeline

## Overview
Analyze enriched customer data (from JoinF / Google Maps) against BLIIOT product families, generate product-match scores and application scenario memos, output as DOCX + XLSX.

## Scripts Location
All scripts live in: `memories/脚本缓存/客户挖掘/`

| Script | Purpose |
|--------|---------|
| `customer_analysis.py` | Read enriched JSON → match products → output JSON report |
| `report_generator.py` | Read JSON report → export DOCX + XLSX |
| `bliiot_product_knowledge.py` | Product knowledge base + matching engine (imported by customer_analysis.py) |

## Usage

### Step 1: Analyze customer data
```bash
python "memories/脚本缓存/客户挖掘/customer_analysis.py" \
  "memories/buyer-development/joinf_business_search_enriched_YYYY-MM-DD.json" \
  --top 63 \
  --output "~/Desktop/Working/BLIIOT_full_analysis.json"
```

### Step 2: Generate reports
```bash
python "memories/脚本缓存/客户挖掘/report_generator.py" \
  "~/Desktop/Working/BLIIOT_full_analysis.json" \
  --docx "~/Desktop/Working/BLIIOT_Customer_Analysis_Report.docx" \
  --xlsx "~/Desktop/Working/BLIIOT_Customer_Analysis_Data.xlsx"
```

## Product Families Covered (7)
1. **Industrial Gateways** (BL116/BL118/BE116/BA116) — PLC/SCADA protocol conversion
2. **ARMxy Edge Controllers** — Edge computing, Linux-based
3. **Remote IO / RTU (IOy Series)** — Field data acquisition
4. **R40 Series Routers** — 4G/5G VPN connectivity
5. **RTU50xx Series** — SCADA telemetry
6. **Signal Isolators** — 4-20mA signal conditioning
7. **Software (BLIoTLink / BLRAT)** — Remote maintenance

## Output Structure

### DOCX Report
- Cover page with title + date
- Overview table (total/matched/date)
- Industry distribution
- Country distribution
- Product match distribution
- Top customers with full details
- Product application memos per customer

### XLSX Workbook (3 sheets)
- **Overview** — Stats, industry/country/product distributions
- **Customer Details** — Full table: name, country, industry, fit score, product match(es), why BLIIOT, priority
- **Application Memos** — Concise memos with product recommendation + follow-up strategy

## Scoring Logic
- Keywords match (product-specific terms): +2 each
- Use case overlap (shared words): +1 each
- Industry alignment: +1
- Scenario-specific boosters (PLC/SCADA -> gateway, data acquisition -> IO, etc.): +2~3
- Total capped at 10

## IEC 104 / Power Grid Customer Technical Evaluation

当客户反馈 IEC 104 时间戳问题时，查看 `references/iec104-product-evaluation.md`。

关键要点：
- **"NT" 在 IEC 104 中 = No Time（无时标）**，不是 National Transmission
- BE102P 实测**不支持**模拟量带时标（M_ME_TF_1 / CP56Time2a）
- BE116（Smart Grid 网关）/ BE190（IEC 104 专用 I/O 模块）是候选，需向工程确认固件支持
- 规格书只写协议级别，不写 ASDU 类型——最终答案找王工确认 BLIoTLink 固件

## Product Spec-Matching Workflow

当客户描述需求（协议、I/O、供电、安装、软件）并询问推荐产品时，查看 `references/product-spec-matching-workflow.md`。

**核心原则：**
1. 读完客户全部需求再推荐，不要读一行就跳结论
2. 只推荐一个主要产品，不要中途切换型号
3. 用表格清晰列出 ✅ 能滿足 / ❌ 不能滿足
4. 诚实说明客户需要自己解决的部分
5. 解释为什么推荐这款而不是其他

## Alternative Data Source: LinkedIn X-ray (no login)

LinkedIn does not expose emails or phone numbers on public profiles. The correct pipeline is:

```
web_search("site:linkedin.com/in SCADA South Africa system integrator")
  -> Get: name, company name, LinkedIn URL
Search company name on web
  -> Find: official website
Crawl website /contact /about /contact-us pages
  -> Extract: email addresses, phone numbers
```

**Key findings (2026-06-04):**
- `web_search` can find LinkedIn profiles without login (tested, works)
- DuckDuckGo HTML endpoint blocks direct parsing (returns 202)
- Solution: use Hermes `web_search` tool + manual URL visiting
- LinkedIn company pages list employees without login
- Africa phone numbers (+27, +234, +254, +263) are WhatsApp-enabled
- Script: `scripts/linkedin_xray_pipeline.py`

## Pitfalls
- `memory` is NOT a valid path - always use `memories` (plural!)
- Google Maps data has short descriptions -> low match rate (~18%)
- JoinF enriched data has richer descriptions -> better match rate (~37%)
- For LOW match customers (score <2), the text is generic
- LinkedIn X-ray CANNOT extract emails or WhatsApp without login - always pair with company website crawl