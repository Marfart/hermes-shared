# Zimbabwe ZODSAT Project — DOCX Generation Notes

**Date**: 27 May 2026
**Project**: Zimbabwe ZODSAT Transformer Anti-Theft & Intrusion Prevention
**Hardware**: BLIIOT S275 LoRaWAN Custom Terminal Node

## Source Files Structure

```
津巴布尔客户/
├── WhatsApp 文件记录/
│   ├── _chat.txt                          # Full WhatsApp conversation
│   └── 一些文件/                           # Attachments (PDFs, images)
├── 功能需求/
│   └── 津巴布韦客户定制项目时间预估(1).docx  # Timeline estimate (Chinese)
├── 签署文件/
│   ├── 更新的功能需求及规划时间初版/
│   │   └── 仍需改良的确认文件.docx           # Source doc to improve
│   ├── 最初的功能技术确认/
│   │   ├── Requirements Confirmation.docx   # Reference format doc
│   │   └── BLIIOT_SmartGrid_TAIS Endnode Requirements Confirmation signed 27042026.pdf
│   ├── 钡铼英文LOGO.png                     # Company logo for watermark (481×302 px)
│   └── 更新后新文件_v2.0.docx               # Final generated output
└── 外购配件及价格汇总/
    ├── 太阳能板/                            # Solar panel quotes
    ├── 太阳能板控制器/                      # Solar controller quotes
    ├── 报价/                               # Pricing screenshots
    └── 整合总价初版/                        # Integrated pricing
```

## Key Techniques Used

### Watermark
- Converted inline `<wp:inline>` to anchored `<wp:anchor>` with `behindDoc="1"`
- Position: ~2100000 EMU horizontal, ~4200000 EMU vertical (roughly centered on A4)
- Image size: 3.5" × 2.2" (scaled from 481×302px logo)
- Verified in `word/header1.xml` — NOT in document.xml

### Table styling
- Dark navy headers: `#1E3A5F` with white text
- Alternating data rows: `#F8FAFC` / `#FFFFFF`
- First column bold: `#1E293B`, other columns: `#475569`
- Full borders (all 4 sides + inside)
- Font: Calibri Latin + 微软雅黑 CJK fallback

### TOC
Original source ("仍需改良的确认文件") had 8 sections:
1. Overall Technical Route
2. Key Hardware & I/O
3. Sensor & Output Function List
4. Power, Battery, Solar & Enclosure
5. Platform (ThingsBoard) Boundary
6. Integrated Accessories & Commercial (pricing table)
7. Project Schedule
8. Customer Confirmation & Signature

### XML extraction command
```bash
unzip -p input.docx word/document.xml 2>/dev/null | grep -oP '<w:t[^>]*>\K[^<]+'
```

### Reference format doc differences
- Original ("最初的功能技术确认"): lighter, simpler, 6 sections
- Updated ("仍需改良的确认文件"): 8 sections, added pricing and schedule
- Final ("更新后新文件"): professional format with proper watermark, styled tables

## Python Environment
- Python: `C:\Users\Admin\AppData\Local\Programs\Python\Python313\python.exe`
- Library: python-docx 1.2.0 + lxml 6.1.1
- pip: `C:\Users\Admin\AppData\Local\Programs\Python\Python313\python.exe -m pip install python-docx`
