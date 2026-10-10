---
name: word-document-creation
title: Word Document Creation with python-docx
description: Create, format, and generate professional .docx documents with python-docx — styled tables, headers/footers, watermarks, signature sections, and structured layouts.
tags: [docx, python-docx, document-generation, word, professional-formatting, tables, watermark, signatures]
---

# Word Document Creation with python-docx

Generate professional Word (.docx) documents programmatically. Covers the full pipeline: install → structure → table styling → watermarks → signature blocks.

## Prerequisites

```bash
pip install python-docx
```

On Windows (git-bash), specify the full path to Python if `pip` resolution is broken:

```bash
/c/Users/Admin/AppData/Local/Programs/Python/Python313/python.exe -m pip install python-docx
```

## Document Structure (Recommended)

A professional client-facing document typically follows this structure:

### 1. Title Header Table
A 2-column table (no visible borders, bottom border only):
- Left: Project title (bold, large font) + subtitle (colored accent)
- Right: Company logo image

```python
title_table = doc.add_table(rows=1, cols=2)
# Remove borders
borders = parse_xml('<w:tblBorders ...><w:bottom w:val="single" w:sz="18" .../></w:tblBorders>')
# Title: bold, 22pt, dark color
# Subtitle: bold, 15pt, blue accent (e.g., #1D4ED8)
# Logo: run.add_picture(logo_path, width=Inches(1.5))
```

### 2. Info Table
2-column table with alternating row backgrounds:
- Left: field labels (bold, bg #F8FAFC alternating with #FFFFFF)
- Right: field values

Fields to include: Prepared for, Prepared by, Document Purpose, Document Status, Prepared Date.

```python
def add_info_row(table, label, value, label_bg="F8FAFC"):
    set_cell_shading(cell_label, label_bg)
    set_cell_margins(cell, 80, 80, 150, 150)
```

### 3. Customer Review Instructions
A single-cell, blue-background (#EFF6FF) bordered box containing review guidance text. This appears near the top so customers understand what they're confirming.

### 4. Section Headers
Numbered sections (1., 2., 3., ...) with blue colored (#1D4ED8) bold 14pt text.
### 5. Data Tables (The Core)

Two main table style options depending on the document's tone:

**Option A — Light blue theme (client-facing confirmation docs)**
```python
# Header: bg #EFF6FF (light blue)
# Data rows: alternating #F8FAFC / #FFFFFF
set_table_borders(table, top_color="CBD5E1", bottom_color="CBD5E1", inside_color="E2E8F0")
```

**Option B — Dark navy theme (proposal-grade / formal commercial docs)**

**Two sub-variants** — pick based on whether a behindDoc watermark needs to show through tables:

**Sub-variant B1 — With cell shading (no watermark behind tables)**
```python
# Header: bg #1E3A5F (dark navy) or #1F4E79 (reference doc standard), text: white
# Data rows: alternating #F8FAFC / #FFFFFF
# First column: bold #1E293B, other columns: #475569
```

**Sub-variant B2 — Watermark-friendly border-based (let watermark show through)**
```python
# Header: no shading, thick bottom border (#1F4E79 or #1E3A5F), bold dark text
# Data rows: no shading, text-color alternation for row distinction
# First column: bold #1E293B, other cells: alternating #475569 / #334155
```

*Tip*: When matching an existing signed reference document, extract its exact header color via python-docx:
```python
tcPr = cell._tc.find(qn('w:tcPr'))
shd = tcPr.find(qn('w:shd'))
ref_color = shd.get(qn('w:fill'))  # often "1F4E79"
```

### Watermark-friendly tables (no cell fills)

**CRITICAL LIMITATION**: When using `behindDoc="1"` watermarks, table cell shading (`w:shd`) renders ON TOP of the watermark because cell fills live in the text rendering layer, not the background layer. Even with `behindDoc="1"`, a table with solid background fills will completely block the watermark underneath.

**Fix**: Remove ALL cell fills and use border-based styling + text formatting instead:

```python
def set_cell_border(c, side="bottom", sz=8, color="1E3A5F"):
    """Set a specific border on a single cell side."""
    tcPr = c._tc.get_or_add_tcPr()
    borders = tcPr.find(qn('w:tcBorders'))
    if borders is None:
        borders = ET.SubElement(tcPr, qn('w:tcBorders'))
    else:
        for b in borders.findall(qn('w:' + side)):
            borders.remove(b)
    ET.SubElement(borders, qn('w:' + side)).attrib.update({
        qn('w:val'): 'single', qn('w:sz'): str(sz),
        qn('w:space'): '0', qn('w:color'): color
    })
```

**Option C — Border-based (watermark-friendly) table style** — use when the document has a behindDoc watermark that must show through table content:

```python
# Header row: no shading, bottom border only
for h in headers:
    set_cell_border(cell, "bottom", 12, "1E3A5F")  # thick bottom border
    add_formatted_para(cell, h, bold=True, font_size=9.5, color="1E3A5F")

# Data rows: no shading, text-color alternation for row distinction
for ri, row in enumerate(rows):
    for ci, text in enumerate(row):
        color = "1E293B" if ci == 0 else ("475569" if ri % 2 == 0 else "334155")
        add_formatted_para(cell, str(text), bold=(ci == 0), font_size=8.5, color=color)
```

**Option D — Border-based info box (watermark-friendly)**:

```python
# Table with no cell shading, blue borders + thick left accent bar
t = doc.add_table(rows=1, cols=1)
c = t.rows[0].cells[0]
set_table_borders(t, "60A5FA", "60A5FA", "60A5FA", "60A5FA", "60A5FA")
# Add thick left border accent
tcPr = c._tc.get_or_add_tcPr()
borders = ET.SubElement(tcPr, qn('w:tcBorders'))
ET.SubElement(borders, qn('w:left')).attrib.update({
    qn('w:val'): 'single', qn('w:sz'): '24', qn('w:space'): '0', qn('w:color'): '3B82F6'
})
add_formatted_para(c, text, font_size=9, color="1E3A5F")
```

**Option E — Border-based highlight banner (watermark-friendly)**:

```python
# No background fill — uses thick left accent + bottom border instead
c = banner_table.rows[0].cells[0]
tcPr = c._tc.get_or_add_tcPr()
borders = ET.SubElement(tcPr, qn('w:tcBorders'))
ET.SubElement(borders, qn('w:left')).attrib.update({
    qn('w:val'): 'single', qn('w:sz'): '36', qn('w:space'): '0', qn('w:color'): '1D4ED8'
})
ET.SubElement(borders, qn('w:bottom')).attrib.update({
    qn('w:val'): 'single', qn('w:sz'): '12', qn('w:space'): '0', qn('w:color'): '1D4ED8'
})
add_formatted_para(c, main_text, bold=True, font_size=12, color="1E3A5F",
                   alignment=WD_ALIGN_PARAGRAPH.CENTER)
```

### 5b. Footnotes, Disclaimers & Notes Styling

In professional commercial documents, footnotes (accessories disclaimers, platform boundary notes, quotation terms, preliminary timeline notes) should be visually distinct from body content. **Preferred format: small red italic text**.

```python
# Footnote under pricing table
body_txt(doc, "*Accessories: list of components...", 
         sz=6, clr="B91C1C", it=True, sb=2, sa=1)

# Platform boundary note
body_txt(doc, "Note: Platform scope is separate from hardware...", 
         sz=6.5, clr="B91C1C", it=True)

# Preliminary timeline disclaimer
body_txt(doc, "Preliminary — subject to confirmation upon deposit.", 
         sz=6.5, clr="B91C1C", it=True)

# Quotation term footnote
body_txt(doc, "Quotation Term: EXW (Shenzhen)  •  All prices in USD.", 
         sz=6.5, clr="B91C1C", it=True, sb=1, sa=0)
```

**Convention**: `sz=6` for dense footnotes, `sz=6.5` for shorter disclaimers. Color `#B91C1C` (deep red) signals "important note" without competing with body text. Always italic. Do NOT use gray (`#64748B`) for notes — users consistently prefer red to distinguish notes from body text.

This applies consistently across both English and Chinese versions.

### 6. Highlight Box (NRE Fee / Important Notice)

A full-width colored table cell for emphasizing commercial terms or important notices:

```python
def add_highlight_box(doc, main_text, sub_text, bg_color="1E3A5F", 
                      text_color="FFFFFF", sub_color="93C5FD"):
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = table.rows[0].cells[0]
    set_cell_shading(cell, bg_color)
    set_cell_margins(cell, 100, 100, 180, 180)
    add_table_borders(table, top_color=bg_color, bottom_color=bg_color,
                      left_color=bg_color, right_color=bg_color)
    add_cell_para(cell, main_text, bold=True, font_size=11, color=text_color,
                  alignment=WD_ALIGN_PARAGRAPH.CENTER)
    add_cell_para(cell, sub_text, font_size=8.5, color=sub_color,
                  alignment=WD_ALIGN_PARAGRAPH.CENTER)
```

### 7. Customer Confirmation Box (Blue Background)

```python
add_info_box(doc, '"Confirmation text here..."', font_size=9, text_color="1E3A5F")
# Uses table with bg #EFF6FF and blue borders (#BFDBFE)
```

For a true watermark that appears semi-transparent **behind the text** and centered on each page, convert the inline header image to a DML `<wp:anchor>` element with `behindDoc="1"`:

```python
from lxml import etree as ET
import copy

def add_proper_watermark(section, image_path):
    """Logo centered on page, behind text — a true watermark."""
    header = section.header
    header.is_linked_to_previous = False
    for p in header.paragraphs:
        p.clear()
    
    p = header.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run()
    run.add_picture(image_path, width=Inches(3.5), height=Inches(2.2))
    
    # Convert inline <wp:inline> to anchored <wp:anchor behindDoc="1">
    drawing = run._r.find(qn('w:drawing'))
    inline = drawing.find(qn('wp:inline'))
    
    # Save the graphic content
    extent = inline.find(qn('wp:extent'))
    cx = extent.get('cx')
    cy = extent.get('cy')
    graphic = inline.find(qn('a:graphic'))
    
    # Build anchor XML with all required namespace declarations
    anchor_xml = '''<wp:anchor
        xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
        xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
        xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"
        xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
        distT="0" distB="0" distL="0" distR="0"
        simplePos="0" relativeHeight="0"
        behindDoc="1" locked="1"
        layoutInCell="0" allowOverlap="1">
        <wp:simplePos x="0" y="0"/>
        <wp:positionH relativeFrom="page">
            <wp:posOffset>2100000</wp:posOffset>
        </wp:positionH>
        <wp:positionV relativeFrom="page">
            <wp:posOffset>4200000</wp:posOffset>
        </wp:positionV>
        <wp:extent cx="''' + cx + '''" cy="''' + cy + '''"/>
        <wp:effectExtent l="0" t="0" r="0" b="0"/>
        <wp:wrapNone/>
        <wp:docPr id="999" name="Watermark" descr="Company Logo Background"/>
        <wp:cNvGraphicFramePr>
            <a:graphicFrameLocks noChangeAspect="1"/>
        </wp:cNvGraphicFramePr>
    </wp:anchor>'''
    
    anchor = ET.fromstring(anchor_xml.encode('utf-8'))
    if graphic is not None:
        anchor.append(copy.deepcopy(graphic))
    
    drawing.remove(inline)
    drawing.append(anchor)
```

**Key attributes for proper watermark behavior:**
- `behindDoc="1"` — renders the image behind the text
- `locked="1"` — prevents accidental repositioning in Word
- `allowOverlap="1"` — allows text to flow over it
- `positionH relativeFrom="page"` at ~2100000 EMU + `positionV` at ~4200000 EMU centers the image on an A4 page
- The image dimensions (`cx`, `cy`) are preserved from the original inline element
- ALL namespace prefixes MUST be declared in the anchor XML string, or lxml.etree will raise `XMLSyntaxError: Namespace prefix ... not defined`. The `wp14:` prefix for `anchorId` is especially tricky — just omit it.

**Important**: Verify the watermark is in `word/header1.xml`, NOT in `word/document.xml`. A count of `wp:anchor` in header1.xml should be > 0.

### Watermark washout effect (grayscale + semi-transparency)

A true watermark should look faded, not like a full-opacity logo. This is done by adding grayscale + alpha transparency to the `<a:blip>` element inside the anchor. However, appending child elements to the blip via python-docx's DOM is unreliable due to namespace resolution. **Post-process the saved DOCX instead:**

```python
def add_watermark_transparency(docx_path):
    """
    Post-process a saved DOCX to make the logo watermark grayscale + 82% transparent.
    Call this AFTER doc.save(), before delivering the file.
    """
    import zipfile, os, tempfile, shutil
    from lxml import etree as ET

    tmpdir = tempfile.mkdtemp()
    outdir = os.path.join(tmpdir, 'unpacked')
    with zipfile.ZipFile(docx_path, 'r') as z:
        z.extractall(outdir)

    NS_A = 'http://schemas.openxmlformats.org/drawingml/2006/main'
    for root, dirs, files in os.walk(outdir):
        for f in files:
            if f.startswith('header') and f.endswith('.xml'):
                path = os.path.join(root, f)
                tree = ET.parse(path)
                for blip in tree.findall('.//{%s}blip' % NS_A):
                    # Remove any existing effects
                    for child in list(blip):
                        tag = child.tag.split('}')[-1]
                        if tag in ('grayscl', 'alphaModFix', 'biLevel', 'duotone'):
                            blip.remove(child)
                    # Grayscale conversion
                    ET.SubElement(blip, '{%s}grayscl' % NS_A)
                    # 18% opacity = 82% transparent (classic watermark washout)
                    alpha = ET.SubElement(blip, '{%s}alphaModFix' % NS_A)
                    alpha.set('amt', '18000')
                tree.write(path, xml_declaration=True, encoding='UTF-8', standalone=True)

    with zipfile.ZipFile(docx_path, 'w', zipfile.ZIP_DEFLATED) as zout:
        for root, dirs, files in os.walk(outdir):
            for f in files:
                zout.write(os.path.join(root, f),
                           os.path.relpath(os.path.join(root, f), outdir))
    shutil.rmtree(tmpdir)
```

The effect combines `grayscl` (removes color) + `alphaModFix amt="18000"` (fades to 18% opacity). This produces the classic "washed-out logo" every page.

### Simple header-image watermark (alternative)

For cases that don't need true behind-text positioning, place the logo as a centered inline element in the header:

```python
def add_simple_header_logo(section, image_path):
    header = section.header
    header.is_linked_to_previous = False
    p = header.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run()
    run.add_picture(image_path, width=Inches(3.0), height=Inches(1.88))
    section.different_first_page_header_footer = False
```

## Page Number Footer

Add auto-updating page numbers to every page's footer using Word field codes:

```python
def add_page_number_footer(section):
    footer = section.footer
    footer.is_linked_to_previous = False
    pf = footer.paragraphs[0]
    pf.alignment = WD_ALIGN_PARAGRAPH.CENTER
    rl = pf.add_run("Page ")
    rl.font.size = Pt(7.5)
    rl.font.color.rgb = RGBColor.from_string("94A3B8")

    # Word field code: { PAGE }
    ru1 = pf.add_run()
    ru1._r.append(parse_xml('<w:fldChar %s w:fldCharType="begin"/>' % nsdecls("w")))
    ru2 = pf.add_run()
    ru2._r.append(parse_xml('<w:instrText %s xml:space="preserve"> PAGE </w:instrText>' % nsdecls("w")))
    ru3 = pf.add_run()
    ru3._r.append(parse_xml('<w:fldChar %s w:fldCharType="end"/>' % nsdecls("w")))
```

## Section Number Badges (Option A — badge style)

For professional section headings with a visual number badge:mber, title):
    p = doc.add_paragraph()
    # Thin separator line
    r = p.add_run("-" * 60)
    r.font.size = Pt(1)
    r.font.color.rgb = RGBColor.from_string("93C5FD")
    
    p2 = doc.add_paragraph()
    # Blue-background number badge
    r1 = p2.add_run(" %s " % number)
    r1.bold = True; r1.font.size = Pt(10)
    r1.font.color.rgb = RGBColor.from_string("FFFFFF")
    r1._r.get_or_add_rPr().append(
        parse_xml('<w:shd %s w:fill="1D4ED8" w:val="clear"/>' % nsdecls("w")))
    
    # Title text
    r2 = p2.add_run("  %s" % title)
    r2.bold = True; r2.font.size = Pt(14)
    r2.font.color.rgb = RGBColor.from_string("0F172A")
```

The `<w:shd>` element with `w:fill="1D4ED8"` creates a dark blue background behind just the number text, like a badge/pill.

### Section Title Option B — simple bold (matching reference signed docs)

For documents that follow the *original signed confirmation* style (e.g. Requirements Confirmation.docx), use a plain bold heading instead of the visual badge:

```python
def sec_title(doc, num, title):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_before = Pt(18); pf.space_after = Pt(6)
    pf.line_spacing = 1.2
    r = p.add_run("%s.  %s" % (num, title))
    r.bold = True; r.font.size = Pt(12)
    r.font.color.rgb = RGBColor.from_string("1F4E79")
    rf(r)
```

Format: `"1.  Overall Technical Route"` — 12pt bold, deep navy (#1F4E79).
Style the body text paragraph immediately after at 9pt (#334155) for a clean hierarchy.

## Page Setup

```python
for section in doc.sections:
    section.top_margin = Cm(1.65)
    section.bottom_margin = Cm(1.65)
    section.left_margin = Cm(1.6)
    section.right_margin = Cm(1.6)
```

**Margin guidance**: Professional signing documents typically use ~1.6 cm margins (the default in many reference templates), not 2.54 cm (1 inch). Check the reference document's margins if one exists:

```python
ref_margin = doc.sections[0].left_margin / 360000  # EMU → cm
```

## Pricing Matrix & Component Cost Recalculation

### Component-based pricing structure

When the commercial section has a pricing matrix where each row = (base node + accessories subtotal), model it as:

| Qty | Solar Panel | Base Node (USD) | Accessories* (USD) | Total (EXW) |

The accessories subtotal is a sum of individual component prices (battery + IoT lock + controller + solar panel + stand). Calculate once and round to 2 decimal places.

### Price recalculation when a component cost changes

When a single component's price changes mid-project (e.g., customer provides a cheaper supplier quote for solar panels, or battery prices are updated):

1. **Update the individual component price** in the accessories list
2. **Recalculate the accessories subtotal** by summing all components
3. **Recalculate the final total** = base node + new accessories subtotal
4. **Verify promotional prices** — GM-approved promo pricing may differ from calculated cost; both should be shown separately
5. **Document the price source** — note whether the price comes from customer's official quote (e.g., Gamko 50W for $9.20) or from BLIIOT's estimate ($19.50)

Example: 50W solar panel changes from $19.50 to $9.20 at 2,000 qty:
```
Before: Battery($10.51)+Lock($1.50)+Controller($6.50)+Panel($19.50)+Stand($5.12) = $43.13 → Total $123.13
After:  Battery($10.51)+Lock($1.50)+Controller($6.50)+Panel($9.20)+Stand($5.12)  = $32.83 → Total $112.83
```

Cross-check recalculated numbers against the pricing spreadsheet (采购单价.xlsx) and the latest WhatsApp chat message confirming final prices.

### Exchange rate handling

When accessories have mixed currencies (RMB + USD), use the agreed exchange rate:
```python
rate = 6.8375  # per project agreement
battery_usd = battery_rmb * 1.10 / rate  # add 10% tax, convert to USD
stand_usd = 35.0 / rate  # 35 RMB per unit
```

## Helper Functions to Reuse

### Cell shading
```python
def set_cell_shading(cell, color):
    shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color}"/>')
    cell._tc.get_or_add_tcPr().append(shading)
```

### Cell margins
```python
def set_cell_margins(cell, top=80, bottom=80, left=120, right=120):
    tcMar = parse_xml(
        f'<w:tcMar {nsdecls("w")}>'
        f'  <w:top w:w="{top}" w:type="dxa"/>'
        f'  <w:bottom w:w="{bottom}" w:type="dxa"/>'
        f'  <w:left w:w="{left}" w:type="dxa"/>'
        f'  <w:right w:w="{right}" w:type="dxa"/>'
        f'</w:tcMar>'
    )
```

### Formatted cell paragraph
```python
def add_formatted_para(cell, text, bold=False, font_size=10, 
                       color="1E293B", font_name="Segoe UI"):
    run = p.add_run(text)
    run.bold = bold
    run.font.size = Pt(font_size)
    run.font.color.rgb = RGBColor.from_string(color)
    # Also set East Asian font
    rFonts = rPr.find(qn('w:rFonts'))
    rFonts.set(qn('w:eastAsia'), '微软雅黑')
```

## Extracting Content from Existing DOCX Files

To read text from an input DOCX for synthesis:

```bash
unzip -p /tmp/input.docx word/document.xml 2>/dev/null | grep -oP '<w:t[^>]*>\K[^<]+'
```

This is much faster than loading python-docx to read, and works in a pipe. Use it to extract all text, then synthesize into the new document structure.

## Extracting Content from Existing PDF Reference Files

```bash
pdftotext "/path/to/reference.pdf" - 2>/dev/null | grep -oP '<w:t[^>]*>\K[^<]+'
# OR for simpler text PDFs:
pdftotext "/path/to/reference.pdf" - 2>/dev/null
```

## Pitfalls

- **python-docx 1.2.0 FutureWarning**: The `if drawing:` truth-test raises a FutureWarning on lxml elements. Use `if len(drawing.getchildren()) > 0:` or check the element directly instead of bare truthiness.
- **Chinese filenames in Windows**: When passing paths with Chinese characters to Python on Windows via git-bash, use raw strings or double-escaped backslashes. Better yet, copy the file to a simple /tmp/ path first (`cp "原文件.docx" /tmp/simple_name.docx`).
- **DOCX XML extraction**: The `word/document.xml` inside even a modest 186KB DOCX can be 2MB+ of XML. Piping through `unzip` + `grep -oP` is faster than loading via python-docx for text extraction. Reserve python-docx for **generation**, not reading.
- **Watermark XML namespace errors**: When building `<wp:anchor>` XML via lxml.etree.fromstring(), ALL namespace prefixes used in the XML string MUST be declared as xmlns attributes on the root element. Missing any prefix (e.g., `wp14:anchorId`) causes `XMLSyntaxError: Namespace prefix ... not defined`. Either declare ALL prefixes or omit the attribute entirely.
- **PermissionError on save**: If the output file is open in Word (e.g., the user viewed and forgot to close it), `doc.save()` fails with `PermissionError [Errno 13]`. Save to a temp path first (`C:\\Users\\Admin\\AppData\\Local\\hermes\\temp.docx`), then copy over the target location after closing the handle. If the target file is locked, you can also use a different filename (e.g., `_v2.docx`, `_v3.0.docx`).
- **Table column widths**: Always set `cell.width = Inches(x)` after creating the table. python-docx does not auto-set column widths properly without explicit widths.
- **Signature blanks**: Use underscore characters `_` repeated to create visible signature blanks that the customer fills in manually. Font size 9-14, color #CBD5E1 (light gray) for a clean "fill in" appearance.
- **Python f-string backslash limitation**: In Python f-strings, the expression part inside `{}` cannot contain backslash escapes like `\"` or `\'`. This causes `SyntaxError: f-string expression part cannot include a backslash`. To build XML strings with quote characters, use `%`-style formatting or regular concatenation instead of nested f-strings. Example: use `'<w:val="%s"/>' % val` instead of an f-string when `val` needs to contain escaped quotes.
- **East-Asian font fallback**: Always set both Latin and East-Asian fonts on runs that may contain Chinese characters. Use `set_run_font(run, name="Calibri", east_asia="微软雅黑")` — without this, Chinese characters may render incorrectly in some Word versions.
- **`w:shd` blocks behindDoc watermarks**: This is the #1 watermark pitfall. In OOXML rendering order, `w:shd` (table cell background fill) lives in the **text layer**, which renders ABOVE the drawing layer where `behindDoc="1"` images sit. This means even a correctly configured behindDoc watermark will be COMPLETELY blocked by any table cell that has a `w:shd` fill. The fix is NOT a different watermark technique — it's removing ALL `w:shd` from table cells and using border-based styling instead (see "Watermark-friendly tables" in Options C–E above). Similarly, `w:shd` on section number badges (`<w:shd w:fill="1D4ED8"/>`) is fine because those are tiny text-only elements, not full table backgrounds.
- **Removing old borders before adding new ones**: When modifying table borders via XML, always `for existing in tblPr.findall(qn('w:tblBorders')): tblPr.remove(existing)` before appending the new borders element. Otherwise stacked border elements cause unpredictable rendering.
- **Merge stamp row after all rows are created**: Cell merges (`cell.merge(other_cell)`) work best when called after ALL rows have been added to the table.
- **Chinese quotation marks in Python strings**: Chinese text often contains paired quotation marks (`"..."` and `'...'`). These look like ASCII double/single quotes to the Python parser and will cause `SyntaxError: invalid syntax`. Use single quotes for the outer Python string when the content contains both types of Chinese quotes: `'如...的"客户确认与签字"处签字。'` — this avoids parser confusion. The safest pattern is to wrap multi-line strings containing Chinese quotes in single quotes or triple-single-quotes.
- **Multi-language document generation**: When generating English + Chinese versions of the same document, maintain parallel generator scripts with identical structure but translated content. Key differences: Chinese footer reads "钡铼技术 机密文件  |  第 X 页", Chinese signature labels use "客户公司名称/授权代表姓名/职务/签字/日期", and Chinese NRE text reads "开发与工程 NRE 费用：10,000.00 美元". Always apply the same margin, color, watermark, and table style patterns to both versions so they're visually identical aside from language.

## User preferences to respect

- Format should follow the "最初的功能技术确认" reference document style: blue-themed headers (#EFF6FF), alternating row backgrounds, professional table borders.
- For formal/commercial proposal documents, use dark navy headers (#1E3A5F) for a more authoritative look.
- The document must be client-facing — language should describe what the final product CAN DO, not just what was discussed.
- Sections should include: technical specs, features list, pricing, timeline, and signature block.
- When creating from existing content, always synthesize and improve — don't just dump the old text into new formatting.
- The watermark must be a TRUE background watermark (behind text, centered on page), not just a header logo. Using the DML `<wp:anchor>` technique with `behindDoc="1"` is the expected approach.
- Tables should have proper borders on all four sides (left + right in addition to top/bottom), not just top/bottom borders.
- First column of data tables should be bold to distinguish labels from values.
- Unconfirmed timeline items should be clearly marked (e.g., italic red note "preliminary — TBC").
- The "signature" table header row should match the same style as other table headers in the document.

## Reference Files

- `references/zimbabwe-zodsat-docx-creation.md` — Complete session walk-through of an 8-section client-facing DOCX (professional dark-navy tables, pricing matrix, signature block).
- `references/zimbabwe-zodsat-project-structure.md` — Project file layout and source document extraction notes.
- **`references/watermark-friendly-tables.md`** — How to make tables watermark-transparent: remove `w:shd`, use borders + text colors instead. Complete patterns for data tables, info boxes, and highlight banners. **Refer to this whenever the document has a behindDoc watermark that needs to show through tables.**
- **`references/document-verification-checklist.md`** — Systematic cross-referencing workflow: after generating a docx, verify pricing, specs, accessories, company names, and payment terms against ALL source files (WhatsApp chats, pricing spreadsheets, originals, signed PDFs). **Refer to this before delivering any multi-source commercial document.**
- `scripts/generate_v4.py` (in the Hermes scripts dir) — Full working example of a watermark-friendly document.
- **`references/data-driven-comparison-reports.md`** — Full pipeline for generating comparison/recommendation reports: web research → structured data model → weighted scoring → DOCX with rankings, budget segmentation, itinerary plans, and appendix. Use this for any "compare N options" task (travel, products, services, vendors). See the working script at `memories/脚本缓存/海钓分析/dragon_boat_fishing_report.py`.
