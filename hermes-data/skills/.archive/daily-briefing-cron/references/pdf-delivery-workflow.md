# PDF Delivery Workflow for XiaoMa Financial Daily

## When to use

- User asks for the daily financial briefing
- The cron job fires and needs to deliver
- User says "字太多了" → immediate signal to switch to PDF

## Prerequisites

```bash
pip install fpdf2
```

Already installed on this machine. If missing, install with the above command.

## Script paths (v2 = active, v1 = fallback)

**v2 (recommended) — Chinese, global sources, larger fonts:**
```
C:\Users\Admin\AppData\Local\hermes\memories\脚本缓存\admin助手\gen_finance_v2.py
```
Run: `python "/c/Users/Admin/AppData/Local/hermes/memories/脚本缓存/admin助手/gen_finance_v2.py"`

Output: `C:/Users/Admin/Desktop/xm_finance.pdf` (then copy to 小马财经日报.pdf)

**v1 (compatibility fallback) — Chinese, fewer sources:**
```
C:\Users\Admin\AppData\Local\hermes\memories\脚本缓存\admin助手\gen_cn_finance_pdf.py
```

## Output file handling

The script outputs to `xm_finance.pdf` first. The canonical target is `C:/Users/Admin/Desktop/小马财经日报.pdf`.

If the file is LOCKED (PermissionError), the previous copy is still open in some app. Handle by:
1. Writing to a temp path instead
2. Using `os.replace(src, dst)` which works atomically on Windows
3. Or just deliver the temp file directly

## PDF structure (8 pages)

| Page | Section | Content |
|------|---------|---------|
| 0 | Cover | "小马财经日报" title, date, issue #, data sources |
| 1 | 全球大盘纵览 | A-share + US indices + HSI + FX + Oil + Commodities analysis |
| 2 | 热点板块与全球要闻 | Top 3 movers + global news headlines + risk monitor |
| 3 | 策略与基金分析 | Core+Satellite approach, valuation metrics, watchlist |
| **4** | **基金推荐与数据分析** | **Fund pick + 4-dimension industry analysis (added 2026-05-29)** |
| 5 | 投资小课堂 | 6 quiz questions with full explanations |
| 6 | 今日总结 | Summary table + next issue preview |

## Font size table (user-corrected)

| Element | Size | Weight |
|---------|------|--------|
| Cover title | 32pt | Bold |
| Section headings | 16pt | Bold |
| Sub-headings | 11pt | Bold |
| Body text | **9pt** (was 8pt — too small) | Regular |
| Quiz explanations | 8pt | Regular |
| Footer/disclaimer | 7pt | Regular |

## Delivery

Send via WeChat using MEDIA: syntax:
```python
send_message(target="weixin", message="📄 小马财经日报...\n\nMEDIA:C:\\Users\\Admin\\Desktop\\小马财经日报.pdf")
```

The PDF arrives as a native file download in WeChat. Do NOT use file-sharing URL services (tmpfiles.org, etc.) — the user rejected them.

## Data sources (user requires both)

- **Global**: Bloomberg, Reuters, CNBC, WSJ, FT, Yahoo Finance
- **Chinese**: 东方财富, 新浪财经, 华尔街见闻, 第一财经, 格隆汇, 雪球

## Common pitfalls

1. **multi_cell overflows after cell()**: When `cell()` is called (advancing cursor x) then `multi_cell(0, h, txt)`, the "0" width = remaining space from current x. If the cell consumed too much width, the remaining space is too narrow. Fix: always `set_x(left + indent)` before `multi_cell(0, ...)`.

2. **file busy → PermissionError**: PDF open in another app. Write to a fresh filename.

3. **multi_cell width hardcoded to `W-n`**: When x is at 16 (after `set_x(18)`), remaining width = `210 - 18 - 10 = 182`. If you pass `190 - 8 = 182`, it fits. If you pass anything bigger, it overflows. Safest: always `multi_cell(0, ...)` after resetting x.

4. **Chinese text with Helvetica font**: Crashes with `FPDFUnicodeEncodingException`. Register `C:\\Windows\\Fonts\\msyh.ttc` with `pdf.add_font('yh', '', path, uni=True)` before any CJK text.

5. **File open → PermissionError**: PDF viewer or WeChat cache has the file locked. Workaround: use `import tempfile; temp_path = tempfile.mktemp(suffix='.pdf'); pdf.output(temp_path); shutil.copy(temp_path, dst)` to avoid conflict.
