# PDF Localization — In-Place Text Replacement (Preferred Method)

When the user wants an English PDF translated to Chinese **with 100% of screenshots, charts, colors, layout, and formatting preserved intact**, the proven approach is **in-place text span replacement** using pymupdf's redact+insert. NOT a screenshot-rebuild (the user explicitly rejected that).

## Core Principle

Use pymupdf to surgically replace each English text span with its Chinese translation, leaving every pixel of images, screenshots, and background graphics untouched. The result is a native PDF — not an image-overlay — with selectable/searchable Chinese text.

## Prerequisites

```bash
# pymupdf has built-in CJK fonts — no external font install needed
pip install pymupdf
```

Available built-in CJK fonts:
- `china-ss` — sans-serif (SimSun-like)
- `china-s` — serif (SimHei-like)

## Step 1: Extract & Analyze

```python
import pymupdf

doc = pymupdf.open("input.pdf")
for i in range(doc.page_count):
    page = doc[i]
    blocks = page.get_text("dict")["blocks"]
    print(f"=== PAGE {i+1} ({len(blocks)} blocks) ===")
    for b in blocks:
        if b["type"] == 0:  # text
            for line in b["lines"]:
                for span in line["spans"]:
                    print(f'  T({span["origin"][0]:.0f},{span["origin"][1]:.0f}) '
                          f'sz={span["size"]:.1f} font={span["font"]} '
                          f'color={span["color"]:06x} '
                          f'"{span["text"][:80]}"')
        elif b["type"] == 1:  # image
            print(f'  IMAGE bbox={b["bbox"]}')
```

Critical: note the exact (x, y) origin coordinates, font size, and hex color of every text span. Also check whether text sits ON TOP of an image (screenshot-embedded text = unchangeable).

## Step 2: Build the Replacement Map

For each page, create a list of (x, y, original_text, translated_text, fontsize, color_hex) tuples. Rules:
- **Preserve all numbers** (device IDs, counts, percentages, coordinates, EUI values)
- **Preserve organization names** (ZODSAT, ZETDC, Powertel, SmartGrid Africa)
- **Preserve proper nouns** (LoRa, GPS, MQTT, HTTP, JSON)
- **Preserve permission code names** (VIEW_USERS, LOCK_USER, etc.)
- **Translate everything else**: titles, captions, descriptions, labels, footers

Common patterns where text sits inside screenshots (unchangeable):
- Dashboard KPI values and labels layered over a background image
- Form field labels rendered as part of a screenshot
- Map markers, chart data labels in PNG images
- Status indicators (colored dots, LEDs, icons with text overlays)

## Step 3: Apply Replacements (The Core Technique)

**Critical: use WIDE redaction boxes.** English text is typically longer than the Chinese replacement. If your redaction box is too narrow, English remnants will show through.

```python
def replace_line(page, x, y, new_text, fontsize, color_hex,
                 width=300, fontname="china-ss"):
    """Redact a generously-sized box, then insert Chinese."""

    # KEY INSIGHT: redact box must allow for:
    #   - English text being wider than Chinese (width w needs to be 2-3x larger)
    #   - Font descent below baseline (bottom margin)
    #   - Font ascent above baseline (top margin = fontsize)
    r = pymupdf.Rect(
        x - 10,              # left: generous margin
        y - fontsize - 5,    # top: full font height above baseline
        x + width,           # right: wide enough for English original
        y + 8                # bottom: room for descenders
    )
    page.add_redact_annot(r, fill=None)
    page.apply_redactions()

    if not new_text.strip():
        return

    c = ((color_hex >> 16 & 0xFF) / 255,
         (color_hex >> 8 & 0xFF) / 255,
         (color_hex & 0xFF) / 255)
    page.insert_text((x, y), new_text,
                     fontname=fontname,
                     fontsize=fontsize,
                     color=c)


def replace_box(page, coords, new_text, fontsize, color_tuple, fontname="china-ss"):
    """Redact a box area and insert wrapped text."""
    r = pymupdf.Rect(coords)
    page.add_redact_annot(r, fill=None)
    page.apply_redactions()
    if new_text:
        page.insert_textbox(r, new_text,
                            fontname=fontname,
                            fontsize=fontsize,
                            color=color_tuple)
```

**Size of `width` parameter**: start at 300 for 10pt text, 500 for 22pt+ headings. The original English could be 3x the pixel width of the Chinese replacement. Better too wide than too narrow — overlapping an adjacent text block is fine since you're replacing that one next.

## Critical Pitfalls

| Problem | Cause | Fix |
|---------|-------|-----|
| English text remnant visible | Redaction box too narrow (Chinese shorter than English) | Widen `width` param — use 300+ for 10pt, 500+ for 22pt |
| English text remnant visible (partial overlap) | Redaction box too short vertically | Set top = `y - fontsize - 5`, bottom = `y + 8` |
| `color=(n,n,n)` error | Passed raw int instead of float tuple | Use `((h>>16&0xFF)/255, (h>>8&0xFF)/255, (h&0xFF)/255)` |
| `ValueError: save to original must be incremental` | Trying to save with deflate=True to same file | Use `incremental=True` for same-file saves, or save to a new path with `deflate=True` |
| `Can't do incremental writes when changing encryption` | PDF has encryption that blocks incremental save | Always save to a NEW file path, not the same path |
| Text inserted at wrong position | Used `insert_textbox` with wrong baseline | `insert_text` takes (x, y) as the **baseline** left edge; `insert_textbox` takes a Rect |
| `need font file or buffer` | Called `insert_font()` on a page, then `insert_text()` passed the XREF number as fontname | Use built-in `china-ss` / `china-s` fontname string instead |
| Chinese CJK chars render as boxes | Missing font registration | Use built-in fonts `china-ss` or `china-s` — no `add_font()` needed |

## Verification

After replacement, verify every page:

```python
issues = 0
for i in range(doc.page_count):
    page = doc[i]
    for b in page.get_text("dict")["blocks"]:
        if b["type"] == 0:
            for line in b["lines"]:
                for span in line["spans"]:
                    t = span["text"].strip()
                    # Flag text that's >8 chars and >60% ASCII alpha
                    if (len(t) > 8 and
                        sum(1 for c in t if c.isascii() and c.isalpha()) > len(t) * 0.6):
                        issues += 1
                        print(f"P{i+1} REMNANT: {t[:60]}")
```

Some English remnants are **unavoidable** if the text is embedded in a PNG screenshot (e.g. UI form labels, map labels, chart data points). These are pixels, not editable text spans.

## Test: Quick Spot-Check

Extract text from the first and last pages to confirm translation:

```bash
python -c "
import pymupdf
doc = pymupdf.open('output.pdf')
for i in [0, doc.page_count-1]:
    print(f'=== P{i+1} ===')
    print(doc[i].get_text()[:200])
"
```

## When NOT to Use This

- **DOCX/PPTX source**: use python-docx/python-pptx native editing instead
- **Text-only PDF with no screenshots**: consider extracting → rewriting with python-docx (smaller, fully searchable)
- **Light edits (e.g. fix a few words)**: use nano-pdf CLI instead
- **Scanned/image-only PDF**: this technique does NOT work — there's no text layer to replace; use OCR → regenerate instead

## Reference Scripts

See the session scripts at `memories/脚本缓存/pdf_tools/` for complete working examples:
- `translate_tais_v4.py` — full 25-page PDF translation (the reference implementation)