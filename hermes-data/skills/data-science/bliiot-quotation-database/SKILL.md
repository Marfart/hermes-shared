---
name: bliiot-quotation-database
description: Import BLIIOT quotation Excel files into SQLite, preserving per-file price tier structures. Covers ARMxy, IIoT Gateways, RTU & Router, IO modules, DB Junction Box.
version: 2.0.0
author: Agent
tags: [bliiot, quotation, sqlite, excel-import, pricing, industrial-iot]
---

# BLIIOT Quotation Database

Import BLIIOT (钡铼技术) product quotation Excel files into a SQLite database for fast querying via MCP.

## Key Principles

1. **Preserve per-file price tier names** — never force generic tier mapping. Each file has its own structure:
   - IIoT Gateways: `Sample | 50pcs | 100pcs | 500pcs`
   - RTU & Router: `Samples | <50Pcs | >50Pcs | >100Pcs | >500Pcs`
   - ARMxy: `<100pcs | >=100pcs | Online Store & Quotation`
   - BL116/BL118: `Sample | <50Pcs | >50Pcs | >100Pcs | >500Pcs`
   - DB Junction Box: `Sample | 100PCS | 500PCS`

2. **Verify against source files before presenting** — always cross-check database values against original .xls/.xlsx before telling the user a price.

3. **Commit after each file section** — scripts that process many files risk crashing mid-way. Commit per-section so partial progress isn't lost on rollback.

## ARMxy File Structure

ARMxy files (`202511 ARMxy Series BL3xx Embedded Computer Price List.xls`) have a complex layout:

### Host/SOM/X-board section (standard layout)
| Col | Field |
|-----|-------|
| 0 | Model name |
| 1-6 | Specs (ETH, USB, HDMI, X Board, Y Board, Dimensions) |
| 7 | `<100pcs` price |
| 8 | `>=100pcs` price |
| 9 | **`Online Store & Quotation` price** = **Sample price** (user confirmed: "Online Store & Quotation就是样品架") |

For 1 unit (<10), **always use Col 9 (Online Store) as the sample price.**

⚠️ X-board models (X0~X9) have model name length=2 — do NOT filter with `len(model) < 3`.

### Y-board section (TWO-COLUMN layout)
Each row contains TWO Y-board models. Header row has 10 columns (2×5):
| Col | Left board | Col | Right board |
|-----|-----------|-----|------------|
| 0 | Model | 5 | Model |
| 1 | Description | 6 | Description |
| 2 | `<100pcs` price | 7 | `<100pcs` price |
| 3 | `>=100pcs` price | 8 | `>=100pcs` price |
| 4 | Online Store (ignore for Y) | 9 | Online Store (ignore for Y) |

**Y boards do NOT have Sample price in the file.** Sample = `<100pcs` price per user rule.
Y37 (4 IEPE Measurement, $970/$925) — user has deprecated this product, do not import.

### Y-board models found in BL335 file
Left column: Y01, Y02, Y11, Y12, Y13, Y21, Y22, Y24, Y31, Y33, Y34, Y36, Y37
Right column: Y41, Y43, Y46, Y51, Y52, Y53, Y54, Y56, Y57, Y58, Y63, Y95, Y96

Y24 (Relay) and Y31 (4-20mA), Y56 (Resistance), Y57 (Voltage) have `/` (no price) in source.

## BL10x 塑胶外壳 (BA Series)

File: `BL10x塑胶外壳USD报价单20240628.xls`
Same layout as IIoT Gateways: Col 2=Model, 3=Sample, 4=50pcs, 5=100pcs, 6=500pcs

⚠️ BA series (BACnet gateways) Physically appear in IIoT Gateways xls sheets but their
CORRECT price source is this BL10x file. Always verify product line before selecting source.

## IIoT Gateways File Format

File: `2026xx BLIIOT IIoT Gateways &BL116&BL118 Price List.xls`
Sheet "IIoT Gateways": Col 3=Sample, 4=50pcs, 5=100pcs, 6=500pcs
Sheet "BL116" and "BL118": Col 3=Sample, 4=<50Pcs, 5=>50Pcs, 6=>100Pcs, 7=>500Pcs

## RTU & Router File Format

File: `2026xx BLIIOT RTU&Router Price List.xls`
Header row: Row 7 (Model No. | Name | Description | Version | Samples | <50Pcs | >50Pcs | >100Pcs | >500Pcs)
Col 4=Samples, 5=<50Pcs, 6=>50Pcs, 7=>100Pcs, 8=>500Pcs

### ⚠️ Sub-row Version Pattern

RTU & Router files use a **version sub-row layout**: one model spans multiple rows for different regional versions.

```
Row 6:  R40  | [Description] | [Spec] | 4G (E version)  | 126 | 120 | 114 | 108 | 103
Row 7:  (空) | (空)          | (空)   | 4G (CE version) | 122 | 116 | 110 | 105 | 100
Row 8:  (空) | (空)          | (空)   | 4G (AU version) | 131 | 124 | 118 | 112 | 107
```

- First row has full data (Model + Name + Description + Version + prices)
- Sub-rows only fill **Version (Col 3)** and price columns — Model/Name/Description are empty
- **Must inherit Model/Name/Description from the previous non-empty row**
- Available versions: `4G (E version)`, `4G (CE version)`, `4G (AU version)`, `4G (A version)`, `4G (J version)`
- Same pattern applies to R40A (rows 11-15) and R40B (rows 16-20)

```python
# Correct parsing pattern for RTU version sub-rows
current_model, current_name, current_desc = None, None, None
for r in range(start_row, end_row):
    model = str(sh.cell_value(r, 0)).strip()
    name = str(sh.cell_value(r, 1)).strip()
    if model:
        current_model, current_name = model, name
        current_desc = str(sh.cell_value(r, 2)).strip()
    # Inherit model/name/desc from parent row
    version = str(sh.cell_value(r, 3)).strip()
    if version:
        samples  = round(float(sh.cell_value(r, 4)))
        lt_50    = round(float(sh.cell_value(r, 5)))
        gt_50    = round(float(sh.cell_value(r, 6)))
        gt_100   = round(float(sh.cell_value(r, 7)))
        gt_500   = round(float(sh.cell_value(r, 8)))
```

## IOy Series File Format

File: `2026xx BLIIOT IOy Series Edge IO Module Price List.xls`
Product naming: `Host Model - Y1 Board Model - Y2 Board Model - Y3 Board Model`
e.g. `BL193-Y11-Y31` = BL193 host + Y11 as Y1 + Y31 as Y2

### Host section columns (Row 10+)
| Col | Field |
|-----|-------|
| 0 | Model |
| 1 | Name |
| 2 | (empty) |
| 3 | Uplink Protocol |
| 4 | Modbus Master |
| 5 | ETH |
| 6 | RS485 |
| 7 | `<100pcs` price |
| 8 | `>=100pcs` price |
| 9 | `Online Store & Quotation` price |

No Samples column in IOy host section.

IOy host models (202605, <100pcs): BL190=$37, BL191=$47, BL192=$45, BL192Pro=$52, BL193=$58, BA190=$42, BA190Pro=$56

### Y-board section (TWO-COLUMN layout, Row 23+)
Each row contains TWO Y-board models. Same column layout as ARMxy Y-boards:

| Col | Left board | Col | Right board |
|-----|-----------|-----|------------|
| 0 | Model | 5 | Model |
| 1 | Description | 6 | Description |
| 2 | `<100pcs` price | 7 | `<100pcs` price |
| 3 | `>=100pcs` price | 8 | `>=100pcs` price |
| 4 | Online Store (ignore for Y) | 9 | Online Store (ignore for Y) |

**No Samples column for Y-boards in IOy files.**

### Key Y-board prices (202605 IOy, <100pcs)
Left column: Y01=$12, Y02=$12, Y11=$12, Y12=$12, Y13=$12, Y21=$12, Y22=$13, Y24=$13, Y31=$18, Y33=$18, Y34=$17, Y36=$17, Y37=deprecated
Right column: Y41=$19, Y43=$22, Y46=$22, Y51=$18, Y52=$18, Y53=$18, Y54=$18, Y56=/, Y57=/, Y58=$19, Y61=$17, Y95=$27, Y96=$27

### IOy vs ARMxy Y-board prices differ
Same Y-board model may have DIFFERENT prices in IOy vs ARMxy files. Always use the file matching the product line:
- BL193 host uses IOy file Y-board prices
- BL310~BL460 host uses ARMxy file Y-board prices

### Price calculation example
```python
# BL193-Y11-Y31, qty=1
# Rule: no Samples column, so use <100pcs prices
bl193_price = 58     # <100pcs from host section
y11_price   = 12     # <100pcs from Y-board section
y31_price   = 18     # <100pcs from Y-board section
total       = 88     # bl193_price + y11_price + y31_price
```

## Price Integer Rounding

xlrd reads Excel float cells with floating-point precision artifacts (e.g. 92.38893712115384 instead of 92). **All prices must be `round(val)` when importing.** The source files store prices as integers.

```python
# CORRECT:
p = round(float(val))  # 92.3889... → 92

# WRONG:
p = val  # leaves precision artifacts
```

## Commit Per Section

When running batch import scripts, **commit after EACH file section**. A crash mid-script rolls back ALL uncommitted changes. This is critical when processing 10+ files.

```python
# CORRECT:
conn.execute("INSERT ...")
conn.commit()  # ← commit per file section

# WRONG:
# (do all files, then commit once at end)
# → crash on file 6 loses files 1-5
```

## BA Series Source Clarification

⚠️ BA series (BACnet gateways: BA110, BA110P, BA110W, BA108, BA108P, etc.) physically appear in the **Building HVAC section** of the IIoT Gateways file (Row 254+). Their prices from the **202605 IIoT Gateways file are CORRECT** (e.g. BA110P Sample=$92). Do NOT substitute BL10x file prices for BA series — the 202605 IIoT Gateways file is the authoritative latest price list.

The BL10x file (`BL10x塑胶外壳USD报价单20240628.xls`) has the same BA series models at older/outdated prices ($80 vs $92 for BA110P Sample). Only use it when specifically asked for historical pricing.

## Price Tier Selection Rule

When determining which price to show for a given quantity:

**RULE (user-given):** "如果有样品价，小于10台的按样品价算，没有就按照文档上的价格算"

| Scenario | Action |
|----------|--------|
| File HAS a Samples column AND qty < 10 | Use Samples price |
| File has NO Samples column | Use documented lowest tier (e.g. <100pcs) |

### Per-file application

| File | Has Samples? | <10 units uses | Source |
|------|:-----------:|:--------------:|:------|
| IIoT Gateways (Col 3 = Sample) | Yes | Samples | file header |
| RTU & Router (Col 4 = Samples) | Yes | Samples | file header |
| BL116/BL118 (Col 3 = Sample) | Yes | Samples | file header |
| BLIIoT Price List 20240527 (Col 4 = Samples) | Yes | Samples | file header |
| **ARMxy (Col 9 = Online Store)** | **Yes — user confirmed** | **Online Store price** | user: "Online Store & Quotation就是样品架" |
| IOy Series | No | <100pcs | no Samples column |
| BL16 Switch | No | documented lowest tier | no Samples column |
| DB Junction Box | No | documented lowest tier | no Samples column |

```python
def price_for_qty(prices, qty):
    \"\"\"prices: dict with tier names as keys, qty: requested quantity\"\"\"
    if qty < 10 and 'Samples' in prices:
        return prices['Samples'], 'Samples'
    if qty < 10 and 'Sample' in prices:
        return prices['Sample'], 'Sample'
    if qty < 10 and 'Online Store' in prices:
        return prices['Online Store'], 'Online Store'
    for fallback in ['Samples', 'Sample', '<100pcs', '<50Pcs', 'Online Store']:
        if fallback in prices:
            return prices[fallback], fallback
    return None, None
```

## User Pricing Display Rules

When presenting quotation data to the user:
- Show a total row at the bottom
- SOM module price on its own row (price changes frequently — "som板价格经常会变")
- Never combine components into a single composite price row
- Use markdown tables, keep concise — user preferred simple format ("不要组合报价单，太多了")

## Response Protocol (User Corrections)

When the user says "价格错了" / "你在乱说" / "你文件都不会读了吗" / "不对啊啊啊啊" / "简直乱搞":

1. **STOP immediately** — do not argue or explain what you did.
2. **Re-read the raw source file** cell by cell using Python xlrd — verify every column mapping.
3. **Check product line** — ensure you're looking at the correct source file for that product model.
4. **Round to integer** — verify `round(val)` wasn't skipped.
5. **Fix silently** — just present the corrected data; don't apologize profusely.
6. **Learn for next time** — the pattern of error is more important than fixing one price.

## Product Line Cross-Reference

Different product lines may coexist in the same physical Excel file but use different price sources:

| Product Line | Correct Price Source | Example Models |
|-------------|-------------------|----------------|
| **BL120** IIoT Gateways | `2026xx IIoT Gateways &BL116&BL118 Price List.xls` (Sheet: IIoT Gateways) | BL120, BL120L, BL121W |
| **BL116** Edge Gateway | Same file (Sheet: BL116) | BL116, BA series??? |
| **BL118** Node-RED Gateway | Same file (Sheet: BL118) | BL118, SOM modules |
| **BA series** BACnet Gateways | `BL10x塑胶外壳USD报价单20240628.xls` | BA110, BA110P, BA110W |
| **BL10x** Plastic Housing | `BL10x塑胶外壳USD报价单20240628.xls` | BA110 series |
| **ARMxy** Embedded Computers | `202511 ARMxy Series BL3xx Price List.xls` | BL310~BL460 |
| **RTU & Router** | `2026xx BLIIOT RTU&Router Price List.xls` | R40, BL70~BL108 |
| **IOy** Edge IO Modules | `2026xx BLIIOT IOy Series Edge IO Module Price List.xls` | BL190~BL193, BA190, BA190Pro, Y01~Y96 |

⚠️ **BA series (BACnet) products** appear in the IIoT Gateways file physically but their CORRECT pricing comes from the BL10x塑胶外壳报价单. Always identify the correct product line before selecting a price source.

## Script Safety

When running batch import scripts:

1. **Commit after EACH file section** — never batch all commits at the end. A crash mid-script rolls back everything.
2. **Never `DELETE FROM prices` without re-importing ALL files in the same commit** — partial re-import = missing data.
3. **Use try/except with explicit rollback on failure** to surface errors without losing prior sections.
4. **Verify BL121W or another known product after import** — if the first product you check has wrong/missing prices, the import is broken.

## User Interaction

User tests database accuracy by asking for specific product prices. Response protocol:

1. **Always query the database** (not re-parse the file) for speed — 10ms vs seconds.
2. **Show the source file name** next to each price so user knows where it came from.
3. If user says "价格错了" / "乱搞" / "重新看文件":
   - STOP immediately
   - Go read the RAW source file (Python xlrd) — verify cell by cell
   - Check if you're using the CORRECT source file for that product line
   - Don't argue — fix and re-verify
4. **Prefer concise tabular output** — markdown tables, no long explanations.
5. When user gives a correction, apply it immediately — don't explain what you plan to do.
6. **Apply Price Tier Selection Rule** before presenting prices — check if the file has Samples column, then apply the rule for <10 quantities.

## Database Schema

```sql
-- Products
CREATE TABLE products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id INTEGER REFERENCES product_categories(id),
    model TEXT NOT NULL,
    name TEXT,
    version TEXT,
    description TEXT,
    source_file TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(model, version)
);

-- Price tiers (per-file original names preserved)
CREATE TABLE price_tiers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,  -- original name from file
    min_qty INTEGER,
    max_qty INTEGER,
    sort_order INTEGER DEFAULT 0
);

-- Prices
CREATE TABLE prices (
    product_id INTEGER NOT NULL,
    tier_id INTEGER NOT NULL,
    price_usd REAL,
    price_date DATE DEFAULT (date('now')),
    UNIQUE(product_id, tier_id)
);
```

## Common Pitfalls

- ❌ **YAML `\\U` escape in Windows paths** — always use single quotes `'C:/Users/...'` or forward slashes `C:/Users/...`. Double-quoted `"C:\\Users\\..."` crashes because YAML interprets `\\U` as a unicode escape sequence.
- ❌ Deleting prices then only re-importing from ONE file → must re-import ALL files
- ❌ Not committing between file sections → crash loses all prior work
- ❌ Filtering X0~X9 by `len(model) < 3` → these are valid 2-char model names
- ❌ Reading Y-board prices from Col 7/8 (that's the RIGHT-side board) — use Col 2/3 for left, Col 7/8 for right
- ❌ Forcing all files into a generic 3-tier schema → user requires per-file original names
- ❌ Not rounding prices to integers → xlrd returns 92.38893712 instead of 92
- ❌ Script crashes mid-import → commit per section so partial progress is preserved
- ❌ Presenting composite/combined quotes → user wants each component listed separately with a total row

## ARMxy Modular Pricing (Host + SOM + X Board + Optional Module)

The ARMxy system is modular. A complete product like BL352BL-SOM353-X25 consists of multiple components priced in SEPARATE sections of the same Excel file.

### Assembly Pattern

| Component | Source Section in File | Example |
|:----------|:----------------------|:--------|
| **Host** (base unit) | `ARMxy BL3xx Series Model List` | BL352 = $63 (Online Store = Sample) |
| **SOM** (system-on-module) | `ARMxy BL3xx Series SOM Model List` | SOM353 = $57 (Online Store = Sample) |
| **X board** (I/O expansion) | `X series I/O Board Model List` | X25 = $18 (<100pcs) |
| **Y board(s)** (I/O, optional) | `Y series I/O Board Model List` | Y11 = $10 (<100pcs) |
| **4G/WiFi module** (optional) | Bottom of file (rows 79-92) | EC25-EUXGR = $23 (<100pcs) |

### Price Rules for ARMxy

1. **Online Store & Quotation column IS the Sample price** — user confirmed: "Online Store & Quotation就是样品架"
2. **<10 units → use Online Store price** if it exists
3. **X/Y boards and modules** have `Refer to <100pcs` in their Online Store column → use <100pcs price
4. **WiFi and 4G/5G are mutually exclusive** — only one optional wireless module can be selected

### 4G Module Regional Selection

When user specifies a region (e.g. "亚洲"), map to the correct 4G module part number:

| User Says | Module | Part No. | Price |
|:----------|:-------|:---------|:-----:|
| "亚洲" / "欧亚" / "东南亚" | EC25-EUXGR | 024027 | $23 |
| "中国" / "国内" | EC20-CE | 024008 | $21 |
| "北美" / "美国" | EC25AFFA-512-SGAS | 024031 | $33 |
| "澳洲" / "澳大利亚" | EC25-AUXGA-PCIE | 024010 | $25 |
| "日本" | (J version via RTU router module) | — | — |

See `references/armxy-4g-module-pricing.md` for the full 4G/5G/WiFi module pricing table and 4G Band country mapping.

## S130 / S150 — GSM 3G 4G SMS Remote Controller

Source: `202605 BLIIOT RTU&Router Price List.xls`, rows 136-145 (sub-row version pattern).

**S130:** 2DI+2Relay, SMS alarm controller
**S150:** 8DI+2Relay, SMS alarm controller

Both have regional versions: E, CE, AU, A, J (same pattern as R40).

Key S130 prices (Sample tier):
| Version | S130 Sample | S150 Sample |
|:--------|:----------:|:----------:|
| 2G (GSM/GPRS) | $53 | — |
| 4G (E version) | $92 | $91 |
| 4G (CE version) | $82 | — |
| 4G (AU version) | $101 | $112 |
| 4G (A version) | $106 | $118 |
| 4G (J version) | $102 | $113 |

## References

- `references/bliiot-file-formats-reference.md` — per-file column layout reference (IIoT Gateways, RTU & Router, ARMxy, BL116/BL118, DB Junction Box)
- `references/armxy-y-board-two-column-layout.md` — ARMxy Y-board dual-column layout with full price table
- `references/r40-router-family-pricing.md` — R40/R40A/R40B 4G router family: regional versions (E/CE/AU/A/J), sub-row parsing pattern, selectable options (GPS/PoE)
- `references/ioy-series-pricing.md` — IOy series (BL190~BL193, BA190, Y01~Y96) host and Y-board pricing tables
- `references/armxy-4g-module-pricing.md` — ARMxy 4G/5G/WiFi optional module pricing table, 4G Band-to-country mapping, ARMxy naming conventions
- `references/bliiot-complete-product-portfolio.md` — Full product portfolio from 103 datasheets: processors, NPU specs, protocols, application domains, customer profiles. Read before any client outreach, quotation, or product-matching task.

## Datasheet Reading Protocol (BLIIoT Product Knowledge)

When asked to "learn the products" or read spec sheets:

1. **Read ALL datasheets** — never sample/skip/abridge. The user will check.
2. **DOCX only** (.docx) — do NOT read .pdf files. PDFs are mostly image-based and produce garbage text.
3. **Search path:** `C:\Users\Admin\Desktop\Working\产品规格书\英文资料\` contains all product datasheets organized by series.
4. **Skip User Manual/说明书** files unless explicitly asked — they are thick operational guides, not product specs. Focus on files with "Data Sheet" or "规格书" in the name.
5. **Isolator and Switch datasheets** are mostly image-based tables with no extractable text in docx — acknowledge this and move on.
6. **Output format:** Complete product matrix table with model, processor, cores, NPU, key specs, and target customer for EACH product.
7. After reading, save to `references/bliiot-complete-product-portfolio.md` so future sessions don't re-read raw files.
