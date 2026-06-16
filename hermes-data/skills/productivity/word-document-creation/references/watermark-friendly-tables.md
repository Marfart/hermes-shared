# Watermark-Friendly Table Styling

## The Problem

In OOXML (Word), `w:shd` (table cell background shading) lives in the **text rendering layer**, while `behindDoc="1"` images live in the **drawing layer** below it. This means:

> **Even a correctly configured behindDoc watermark is completely blocked by any table cell that has a `w:shd` fill.**

The watermark renders perfectly *under* plain paragraphs, but the moment a table with colored backgrounds is on the page, the watermark vanishes behind those cell fills.

## The Fix

**Remove ALL cell shading.** Replace it with border-based styling + text formatting:

| Before (blocked watermark) | After (visible watermark) |
|---|---|
| `w:shd` on header cells → block watermark | Thick bottom border on header → lets watermark through |
| `w:shd` on alternating data rows → block watermark | Alternating text colors → no background needed |
| `w:shd` on info box → block watermark | Blue border frame + left accent bar → no fill |
| `w:shd` on dark banner → block watermark | Thick left accent bar + bottom border → no fill |

## Helper: Set Individual Cell Border

```python
def set_cell_border(c, side="bottom", sz=8, color="1E3A5F"):
    """Set a specific border on a single cell side. Can be called multiple times."""
    tcPr = c._tc.get_or_add_tcPr()
    borders = tcPr.find(qn('w:tcBorders'))
    if borders is None:
        borders = ET.SubElement(tcPr, qn('w:tcBorders'))
    else:
        # Remove existing border for this side if present
        for b in borders.findall(qn('w:' + side)):
            borders.remove(b)
    ET.SubElement(borders, qn('w:' + side)).attrib.update({
        qn('w:val'): 'single', qn('w:sz'): str(sz),
        qn('w:space'): '0', qn('w:color'): color
    })
```

## Complete Pattern: Watermark-Friendly Table

```python
def mk_table(doc, hdrs, rows):
    """Table with NO cell shading — watermark shows through."""
    t = doc.add_table(rows=1+len(rows), cols=len(hdrs))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(t)  # standard light-gray borders
    
    # Header row — no shading, just bottom border
    for i, h in enumerate(hdrs):
        c = t.rows[0].cells[i]
        set_cell_margins(c, 80, 80, 150, 150)
        set_cell_border(c, "bottom", 12, "1E3A5F")  # thick navy bottom border
        add_formatted_para(c, h, bold=True, font_size=9.5, color="1E3A5F")
    
    # Data rows — no shading, text-color alternation
    for ri, rd in enumerate(rows):
        for ci, tx in enumerate(rd):
            c = t.rows[ri+1].cells[ci]
            set_cell_margins(c, 60, 60, 150, 150)
            clr = "1E293B" if ci == 0 else ("475569" if ri % 2 == 0 else "334155")
            add_formatted_para(c, str(tx), bold=(ci == 0), font_size=8.5, color=clr)
    return t
```

## Complete Pattern: Watermark-Friendly Info Box

```python
def info_box(doc, txt, sz=9, clr="1E3A5F"):
    """Bordered info box — no fill, watermark visible behind."""
    t = doc.add_table(rows=1, cols=1)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    c = t.rows[0].cells[0]
    set_cell_margins(c, 100, 100, 180, 180)
    set_table_borders(t, "60A5FA", "60A5FA", "60A5FA", "60A5FA", "60A5FA")
    # Left accent bar
    tcPr = c._tc.get_or_add_tcPr()
    borders = ET.SubElement(tcPr, qn('w:tcBorders'))
    ET.SubElement(borders, qn('w:left')).attrib.update({
        qn('w:val'): 'single', qn('w:sz'): '24',
        qn('w:space'): '0', qn('w:color'): '3B82F6'
    })
    add_formatted_para(c, txt, font_size=sz, color=clr, line_spacing=1.15)
```

## Complete Pattern: Watermark-Friendly Highlight Banner

```python
def dark_banner(doc, line1, line2):
    """Banner with no fill — uses left accent + bottom border."""
    t = doc.add_table(rows=1, cols=1)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    c = t.rows[0].cells[0]
    set_cell_margins(c, 100, 100, 180, 180)
    # Left accent bar + bottom border
    tcPr = c._tc.get_or_add_tcPr()
    borders = ET.SubElement(tcPr, qn('w:tcBorders'))
    ET.SubElement(borders, qn('w:left')).attrib.update({
        qn('w:val'): 'single', qn('w:sz'): '36',
        qn('w:space'): '0', qn('w:color'): '1D4ED8'
    })
    ET.SubElement(borders, qn('w:bottom')).attrib.update({
        qn('w:val'): 'single', qn('w:sz'): '12',
        qn('w:space'): '0', qn('w:color'): '1D4ED8'
    })
    # Standard table borders (light gray) for frame
    set_table_borders(t, "E2E8F0", "E2E8F0", "E2E8F0", "E2E8F0", "E2E8F0")
    add_formatted_para(c, line1, bold=True, font_size=12, color="1E3A5F",
                       alignment=WD_ALIGN_PARAGRAPH.CENTER)
    add_formatted_para(c, line2, font_size=8, color="3B82F6",
                       alignment=WD_ALIGN_PARAGRAPH.CENTER)
```

## Verification

After generating the DOCX, verify the watermark renders correctly behind tables:

```bash
# Check that header has the anchor image (behindDoc=1)
unzip -p /path/to/output.docx word/header1.xml | grep -c 'behindDoc="1"'

# Check that NO table cells have w:shd (which would block the watermark)
unzip -p /path/to/output.docx word/document.xml | grep -oP '<w:shd[^>]*/>' | head -5
# Only section-number badges (<w:shd w:fill="1D4ED8">) should appear.
# If you see table-cell-sized w:shd elements, the watermark will be blocked.
```

## Example: Complete Working Script

For a full working example of this technique in a real 8-section client-facing document, see the `generate_v4.py` script in the Hermes scripts directory:

```
C:\Users\Admin\AppData\Local\hermes\scripts\generate_v4.py
```

This script generates Zimbabwe ZODSAT project documentation using all border-based (no fill) table techniques, with:
- DML anchor watermark (behindDoc=1, grayscl, 18% opacity)
- Border-based headers with thick bottom borders
- Alternating text colors for row distinction
- Left-accent info box and NRE banner
- Page number footer with confidentiality label
