# Data-Driven Comparison Report Generation

Generate polished comparison/recommendation DOCX reports backed by web research and a structured scoring model. Covers the full pipeline: research → data model → scoring → DOCX with rankings, budget segmentation, itinerary plans, and appendices.

This pattern applies to any "compare N options" task: travel destinations, products, services, tools, suppliers — anything where you need to rank alternatives by multiple weighted criteria and produce a client-ready document.

## Pipeline Overview

```
1. Web Research ──→ 2. Data Modeling ──→ 3. Scoring/Ranking ──→ 4. DOCX Assembly
                           ↓                        ↓
                    Dataclass definitions      Weighted score model
```

## Step 1: Data Research (Web Search)

Search for each candidate option with targeted queries. For travel/leisure destinations, these queries are effective:

```
f"{place} 攻略 费用 2025"
f"{place} 海钓 船费 价格"
f"深圳到{place} 交通 高铁 自驾 费用"
f"{place} 住宿 民宿 酒店 价格"
```

**Rule**: Gather at least one data point per dimension (transport, accommodation, activity cost, pros/cons). If web search returns weak results, try alternative queries with different keywords or use the browser tool for richer sources.

## Step 2: Data Modeling

Use `dataclass` with enums and typed fields for clean, self-documenting data:

```python
@dataclass
class ActivityOption:
    name: str
    type: str
    price_per_person: int
    duration: str
    items_included: str
    notes: str = ""

@dataclass
class Destination:
    name: str
    region: str
    location: str
    quality: str               # emoji rating e.g. "⭐⭐⭐⭐"
    scenery_rating: int        # 1-10
    experience_rating: int     # 1-10
    accessibility_rating: int  # 1-10
    cost_rating: int           # 1-10 (higher = better value)
    transport_description: str
    transport_time: str
    transport_cost: int
    accommodation_range: str
    accommodation_avg: int
    activity_options: List[ActivityOption]
    estimated_total: int
    pros: List[str]
    cons: List[str]
    description: str
    keywords: List[str]
```

**Key design choice**: Use `@dataclass` + typed fields — avoids dict key typos, enables IDE autocomplete, and keeps data self-documenting.

## Step 3: Scoring Model

### Weighted scoring function

```python
def score(destinations, weights=None):
    w = weights or {"scenery": 0.25, "activity": 0.20,
                    "access": 0.10, "value": 0.25}
    scores = []
    for d in destinations:
        composite = (
            d.scenery_rating * w["scenery"] +
            d.experience_rating * w["activity"] +
            d.accessibility_rating * w["access"] +
            d.cost_rating * w["value"]
        )
        # Budget penalty: cheaper = higher budget score
        budget_score = min(10, 10 - d.estimated_total / 1000 * 2)
        composite += budget_score * 0.20
        
        scores.append({
            "name": d.name, "composite_score": round(composite, 2),
            "estimated_cost": d.estimated_total,
        })
    return sorted(scores, key=lambda x: x["composite_score"], reverse=True)
```

### Budget segmentation (most reader-friendly)

```python
def segment(scores):
    """Returns dict of {label: [items]} organized by budget tiers."""
    tiers = [
        ("Budget (≤¥1500)", lambda s: s["estimated_cost"] <= 1500),
        ("Mid-range (¥1500-3000)", lambda s: 1500 < s["estimated_cost"] <= 3000),
        ("Premium (≥¥3000)", lambda s: s["estimated_cost"] >= 3000),
    ]
    return {label: [s for s in scores if pred(s)] for label, pred in tiers}
```

## Step 4: DOCX Report Structure

### A. Cover Page
- Large title (28pt navy), subtitle (16pt), date range
- 6 blank paragraphs above title for visual centering

### B. Table of Contents
Numbered chapter list.

### C. Methodology Section
Explain data sources, rating dimensions, weight formula in a table.

### D. Summary Table (ALL options at a glance)
Columns: Name | Region | Quality | Activity | Transport | Budget | Value

### E. Ranking Table (with medals)
Bronze/silver/gold styling on Top 3.

### F. Detailed Destination Pages (one per option, sorted by rank)
1. **Info card**: 7-row x 2-col table (Location, Region, Quality, Activity, Transport, Time, Budget)
2. **Description paragraph** (italic)
3. **✅ Pros + ⚠️ Cons** bullet lists
4. **Activity options table** (name, type, price, duration, included, notes)
5. **Accommodation reference**
6. **Keywords/tags**

### G. Budget Segmentation Tables
Budget band → destination → score → budget → reason column.

### H. Top 3 Itinerary Plans
Day-by-day breakdowns with small tables: Day column + Activity column.
Mark holidays: `"🐉端午"`.

### I. Travel Tips Section
Bulleted: Packing, Timing, Saving, Safety, Apps.

### J. Appendix: Full Comparison Matrix
Name | Scenery(10) | Activity(10) | Transport(10) | Value(10) | Budget(¥) | Composite

## Key Helper Functions

### Styled comparison table (navy header + alternating rows)

```python
def add_styled_table(doc, headers, rows, col_widths=None):
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = 'Table Grid'
    for i, h in enumerate(headers):
        cell = table.rows[0].cells[i]
        set_cell_text(cell, h, bold=True, size=10, alignment=WD_ALIGN_PARAGRAPH.CENTER)
        set_cell_shading(cell, "2F5496")
        cell.paragraphs[0].runs[0].font.color.rgb = RGBColor(255, 255, 255)
    for r_idx, row_data in enumerate(rows):
        for c_idx, val in enumerate(row_data):
            cell = table.rows[r_idx + 1].cells[c_idx]
            set_cell_text(cell, str(val), size=9, alignment=WD_ALIGN_PARAGRAPH.CENTER)
            if r_idx % 2 == 0:
                set_cell_shading(cell, "E8EDF5")
    if col_widths:
        for row in table.rows:
            for i, w in enumerate(col_widths):
                row.cells[i].width = Cm(w)
```

### Info card (7 rows, 2 columns, label bg navy)

```python
def add_info_card(doc, fields):
    """fields = [(label, value), ...]"""
    table = doc.add_table(rows=len(fields), cols=2)
    table.style = 'Table Grid'
    for i, (label, value) in enumerate(fields):
        c0, c1 = table.rows[i].cells[0], table.rows[i].cells[1]
        set_cell_text(c0, label, bold=True, size=10); set_cell_shading(c0, "2F5496")
        c0.paragraphs[0].runs[0].font.color.rgb = RGBColor(255, 255, 255)
        set_cell_text(c1, value, size=10)
        if i % 2 == 0: set_cell_shading(c1, "F2F7FB")
        c0.width = Cm(4); c1.width = Cm(12)
```

### Itinerary table

```python
def add_itinerary(doc, rows):
    """rows = [(day_label, activity_text), ...]"""
    table = doc.add_table(rows=1 + len(rows), cols=2)
    table.style = 'Table Grid'
    headers = ["时间", "安排"]
    for i, h in enumerate(headers):
        cell = table.rows[0].cells[i]
        set_cell_text(cell, h, bold=True, size=10, alignment=WD_ALIGN_PARAGRAPH.CENTER)
        set_cell_shading(cell, "2F5496")
        cell.paragraphs[0].runs[0].font.color.rgb = RGBColor(255, 255, 255)
    for i, (day, activity) in enumerate(rows):
        set_cell_text(table.rows[i+1].cells[0], day, bold=True, size=10)
        set_cell_text(table.rows[i+1].cells[1], activity, size=10)
        if i % 2 == 0:
            set_cell_shading(table.rows[i+1].cells[0], "E8EDF5")
            set_cell_shading(table.rows[i+1].cells[1], "E8EDF5")
        table.rows[i+1].cells[0].width = Cm(4)
        table.rows[i+1].cells[1].width = Cm(12)
```

### Set cell text with East-Asian font support

```python
def set_cell_text(cell, text, bold=False, color=None, size=None, alignment=None):
    cell.text = ""
    p = cell.paragraphs[0]
    if alignment: p.alignment = alignment
    run = p.add_run(str(text))
    if bold: run.bold = True
    if color: run.font.color.rgb = RGBColor(*color)
    if size: run.font.size = Pt(size)
    run.font.name = "微软雅黑"
    run._element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')
```

## Pitfalls

- **Chinese quotation marks in Python strings**: `"天赐白沙堤"` contains Chinese paired double-quotes that look like ASCII quotes to the parser. Use single-quote wrapping: `description='...有"天赐白沙堤"之美誉。'` — avoids `SyntaxError: invalid syntax`.
- **Web search quality varies**: Some queries return irrelevant results (adult content, car dealerships). Run 2-3 related queries per candidate and cross-reference. Use browser tool for richer sources when search fails.
- **Holiday price spikes**: Estimate ±15-25% markup during Golden Week / Dragon Boat / National Day. Always add a disclaimer: "实际价格以预订时为准".
- **Itinerary realism**: 3-day trips with complex multi-modal transport (fly → drive → ferry) are exhausting. Flag when a plan needs "请1天假" to be comfortable.
- **Scoring transparency**: Publish weights and the budget-score formula so rankings are auditable. A black-box ranking loses credibility.
- **Verify floating holidays**: Search engines may return last year's dates. Confirm on a calendar site before committing.
- **Font rendering on Windows**: Always set both `font.name` (Latin) and `rFonts.w:eastAsia` ("微软雅黑") on runs with Chinese text, or it may render as unreadable boxes.

## Source Script Reference

Full working implementation (Dragon Boat Festival 2026 sea fishing comparison, 8 destinations, 8 chapters) at:

```
C:\Users\Admin\AppData\Local\hermes\memories\脚本缓存\海钓分析\dragon_boat_fishing_report.py
```

To adapt: replace destination data, adjust weights/categories, and change section titles.