# PDF Generation Technique for Chinese Financial Briefings

## Environment
- **OS**: Windows 10
- **Python PDF lib**: `fpdf2` (pip install fpdf2)
- **Chinese fonts**: Windows ships with `C:\Windows\Fonts\msyh.ttc` (微软雅黑) and `C:\Windows\Fonts\simsun.ttc` (宋体)
- **Delivery**: Send PDF via WeChat using `MEDIA:C:\path\to\file.pdf` in send_message

## Key Technique — Unicode Font Registration

fpdf2's default Helvetica/Courier/Times fonts do NOT support Chinese characters. You MUST register a Unicode font:

```python
from fpdf import FPDF

pdf = FPDF()
pdf.add_font('yh', '', r'C:\Windows\Fonts\msyh.ttc', uni=True)
pdf.add_font('yh', 'B', r'C:\Windows\Fonts\msyhbd.ttc', uni=True)

# Then use like:
pdf.set_font('yh', 'B', 16)  # bold, 16pt
pdf.set_font('yh', '', 9)    # regular, 9pt
```

## File Naming Convention
- Output file: `C:/Users/Admin/Desktop/小马财经日报.pdf`
- NOT the latin-named version (`XiaoMa_Financial_Daily...`)
- The file will appear in WeChat chat as a downloadable attachment

## Font Size Guidelines (user preference)
- Cover title: 32pt bold
- Section headings: 16pt bold
- Sub-headings: 11pt bold
- Body text: 9pt
- Quiz explanations: 8pt
- Footer/disclaimer: 7pt

## Section Structure
1. Cover (title + date + issue number + data sources)
2. Global Market Overview (A-shares + US + HK + FX + Oil + Commodities analysis)
3. Hot Sectors & Global News (top 3 sectors + 6-8 headlines from global sources)
4. Strategy & Fund Analysis (core+satellite framework with actual valuation metrics)
5. **Fund Recommendation & Data Analysis** (one fund + 4-dimension industry analysis) — REQUIRED
6. Investment Quiz (5-6 questions covering different weekly topics)
7. Daily Summary (6 labeled rows + next issue preview)

## Data Sources (user requires global + Chinese)
- Global: Bloomberg, Reuters, CNBC, WSJ, FT, Yahoo Finance
- Chinese: 东方财富, 新浪财经, 华尔街见闻, 第一财经, 格隆汇, 雪球

## Fund Recommendation Section (Section 4 — REQUIRED, added 2026-05-29)

This section sits between Strategy (Section 3) and Quiz (Section 5). Structure:

```python
pdf.sec('四', '基金推荐与数据分析')

# Cover box
pdf.set_draw_color(180, 100, 30)
pdf.set_line_width(0.5)
y = pdf.get_y()
pdf.rect(12, y, 186, 38)
pdf.set_xy(14, y+2)
# Fund name (12pt bold orange), type/size/成立 (9pt), performance stats (9pt gray)

# Three logic chains
## 逻辑一：与今日最强板块高度吻合
## 逻辑二：全球宏观环境持续利好
## 逻辑三：基金经理业绩验证
# Each: bold orange heading (9pt) + body text (9pt, indented at x=14)

# 行业数据分析
## 供给端 / 库存端 / 需求端 / 成本端
# Use bullet() helper with bold prefix: bold='供给端'

# 估值分析
# Body text with PE range and forward outlook

# 风险提示 (RED, size=8)
# Explicit warnings

# 免责声明 (small italic red)
```
Path: `memories/脚本缓存/admin助手/gen_finance_v2.py`
Run with: `python "/c/Users/Admin/AppData/Local/hermes/memories/脚本缓存/admin助手/gen_finance_v2.py"`

## Pitfalls
- **Helvetica cannot render Chinese**: If you get `FPDFUnicodeEncodingException: Character "小" at index 0... outside the range of characters supported by the font "helvetica"` — you forgot to register and use a Unicode font. The error is definitive: switch to a registered CJK font.
- **latin-1 codec error on Unicode escapes**: If the Python source contains `\uXXXX` escape sequences AND you're using single-byte font, the code will fail at runtime. Solution: remove all Unicode escapes from string literals. The `\u5c0f\u9a6c` style escapes decode to Chinese characters at Python parse time — they still need a Unicode font to render.
### multi_cell overflow on quiz options (FIXED 2026-05-29)

The quiz loop does:
```python
pdf.set_x(12)
pdf.cell(6, 5.5, o[0] + ')', 0, 0)  # advances x to 18
pdf.set_x(18)
pdf.multi_cell(0, 5.5, txt)  # w=0 = auto remaining width
```

The OLD code was `multi_cell(W-8, ...)` where W=190. After `cell()` advances x to 18, remaining width = `210 - 18 - 10 = 182`. `W-8 = 182` happens to fit, but if x is any farther right (e.g. after a `set_x(20)` or a wider `cell()`), `190-8=182` EXCEEDS the real remaining width and you get `FPDFException: Not enough horizontal space`.

**Fix applied everywhere**: Always use `multi_cell(0, h, txt)` after resetting x. Never hardcode a width number.

Same issue in the `bullet()` helper when it did `multi_cell(W-6, ...)` after `set_x(16)`. Fixed to `multi_cell(0, ...)`.

Also in `stat()` — the value column `cell(35, ...)` clips text longer than 35mm. Extended to 40mm for safety.
- **File not sent via MEDIA**: The MEDIA: prefix in send_message MUST be followed by an absolute path. The file must exist at that path. Delivery goes as native file attachment on WeChat.
- **multi_cell with hardcoded width overflows on option/quiz text**: The quiz loop renders `pdf.cell(6, 5.5, o[0] + ')', 0, 0)` then `pdf.set_x(18)` then `pdf.multi_cell(W-8, 5.5, txt)`. This overflows when `W-8` (e.g. 182) exceeds the real remaining width from x=18 to right margin (which is `210 - 18 - 10 = 182` only at exact margin positions; with any prior indentation it's less). Fix: use `multi_cell(0, ...)` after `set_x()`, which auto-calculates remaining space.
- **Stat block text clipping**: The `cell(35, 5, f' {val}', ...)` in `stat()` fixes a 35mm width for the value column. Long values like `"438KB, 7页"` or `"+2.55% 领涨"` can clip. Increase to 40mm for safety, or use `multi_cell` for variable-width output.
- **File re-generation after PermissionError**: If the PDF is open in another app (e.g. WeChat has it cached or user previewed it), `pdf.output()` raises `PermissionError: [Errno 13] Permission denied`. Workaround: write to a temp path first, then copy to Desktop: `os.rename(src, dst)` after confirming `dst` is not busy.
