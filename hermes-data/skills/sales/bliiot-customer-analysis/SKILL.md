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

## Data Source: Joinf CRM API (authenticated, full customer database)

直接从富通天下CRM通过API提取完整客户数据。需要登录态（CDP浏览器或cookie认证）。

### Authentication
1. CDP浏览器导航到 `https://cloud.joinf.com`（登录页）
2. 填入账号密码（bliiot03 / [在.env中]）
3. 点击「安全登录」按钮（腾讯拼图验证码会自动通过，或需手动滑动）
4. 登录成功后cookie保持会话

### API Endpoint
```
GET https://trade.joinf.com/rapi/d/customers?num={page}&paging=true&size={pageSize}&sortColumn=&sortType=&isAsterisk=0
```

### Data Structure
- `result.data.headLists[]` — 75个列定义（name, columnName, type, dataDictionary）
- `result.data.values[]` — 每条客户是完整JSON对象（不是数组！）
- `result.totalRecords` — 总记录数
- `result.totalPage` — 总页数

### Key Fields (per customer object)
| Field | 说明 | Example |
|-------|------|---------|
| `name` | 客户名称 | "Zip Automations Limited" |
| `contactName` | 联系人 | "Oladimeji Fatona" |
| `contactEmail` | 邮箱 | "dimeji.f@zipautomations.com" |
| `contactMobile` | 手机 | "+234 2348135933718" |
| `displayRegion` | 国家/地区 | "尼日利亚 NIGERIA" |
| `displayType` | 客户类型 | "潜在工业客户"/"成交工业客户"/"成交家用客户" |
| `source` | 来源 | "阿里询盘"/"官网询价"/"谷歌开发"/"领英开发" |
| `description` | 备注 | 客户跟进历史 |
| `webSite` | 企业网站 | "https://zipautomations.com/" |
| `address` | 联系地址 | 完整地址 |
| `displaySalesman` | 业务员 | "Kali Marfa(bliiot03)" |
| `code` | 客户代码 | "C00001932" |
| `displayCreateTime` | 创建时间 | Unix毫秒时间戳 |
| `industryType` | 行业类型 | "系统集成商"/"自动化解决方案" |
| `orderCount` | 成交订单数 | null或数字 |
| `orderAmountUsd` | 成交金额USD | null或数字 |
| `businessType` | 业务类型 | "代采"/"编程服务"等 |
| `grade` | 客户等级 | null或等级 |
| `cooperationPeriod` | 合作年限 | null或年数 |
| `linkedinAccount` | LinkedIn | URL |
| `faceBookCmpMain` | Facebook主页 | URL |

### Pagination
- 每页最多50条（size=50稳定，size=200返回空data）
- 例：1948条 / 50 = 需40页

### Data Verification (Kali铁律)
提取数据后**必须验证**：
1. **数据归属** — 确认是"我的客户"还是"公海"（tab=0 vs tab=1）
2. **今日新增数** — 用displayCreateTime过滤今天UTC+8时间戳，确认与CRM页面一致
3. **业务员分布** — 检查displaySalesman字段，确认数据来源
4. **客户类型分布** — 检查displayType分布是否合理

### Full Export Script
```javascript
// 在已登录的CDP浏览器中执行（Playwright evaluate）
async () => {
  const allCustomers = [];
  const pageSize = 50;
  const totalPages = Math.ceil(1948 / pageSize);
  for (let page = 1; page <= totalPages; page++) {
    const resp = await fetch(`/rapi/d/customers?num=${page}&paging=true&size=${pageSize}&sortColumn=&sortType=&isAsterisk=0`, {credentials: 'include'});
    const result = await resp.json();
    allCustomers.push(...(result.data?.values || []));
  }
  // Extract key fields and save
  const export_data = allCustomers.map(c => ({
    name: c.name, contact: c.contactName, email: c.contactEmail,
    phone: c.contactMobile, country: c.displayRegion, type: c.displayType,
    source: c.source, website: c.webSite, remark: c.description,
    salesman: c.displaySalesman, code: c.code, industry: c.industryType,
    orderCount: c.orderCount, orderAmountUsd: c.orderAmountUsd
  }));
  return JSON.stringify({total: allCustomers.length, data: export_data});
}
```

### Capabilities
- ✅ 读：全部1948条客户完整数据（API已验证）
- ⚠️ 写：编辑客户名称等字段——API路径未知（见下方Pitfalls）
- ✅ 写：新建客户、发邮件、加备注（UI操作，非API）
- ✅ 沟通：WhatsApp/邮件集成
- ✅ 商机：商机/报价/订单模块
- ❌ 客户数据更新API：PUT/POST到`/rapi/d/customers`返回200+"系统繁忙"，`/save`/`/update`/`/edit`路径全部404。需通过UI操作编辑（见Pitfalls和`references/joinf-crm-write-api-attempts.md`）

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
- **客户名称修改只能通过UI操作** — API端点全部失败（PUT/POST `/rapi/d/customers`返回"系统繁忙"，`/save`/`/update`/`/edit`返回404）。需要在客户详情页点击名字旁的编辑图标才能修改
- **客户数据中的姓名错误需人工核对** — 例：邮箱显示英文名(Abhinav)但客户名写了俄文名(Вадим)，这类跨语言录入错误需要你主动发现并修正
- **CDP Playwright MCP偶尔断连** — 长时间页面操作后Playwright MCP可能断连，需要重连或重新导航