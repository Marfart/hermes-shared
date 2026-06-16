---
name: pdf-extractor
description: "PDF 智能提取工具 — 自动检测文字型/图片型 PDF，多引擎提取+表格"
version: 1.0.0
author: agent
---

# PDF 智能提取工具

当需要从 PDF 提取文字/表格，尤其是 BLIIOT 产品规格书时加载此技能。

## 脚本位置
`memories/脚本缓存/pdf_tools/pdf_extractor_tool.py`

## 用法
```bash
python pdf_extractor_tool.py sample.pdf               # 自动检测
python pdf_extractor_tool.py sample.pdf --mode table  # 只提取表格
python pdf_extractor_tool.py sample.pdf --output md   # 输出 Markdown
python pdf_extractor_tool.py sample.pdf --pages 1-3   # 指定页
python pdf_extractor_tool.py sample.pdf --output md --save  # 保存到文件
```

## 类型检测逻辑
- `page.get_text() > 50 字符/页` → 文字型 (PyMuPDF)
- `get_images() > 0 且文字 < 50` → 图片型 (需OCR)
- 混合型 → 文字+表格都提，文字不够200字符也OCR

## 引擎
| 方法 | 安装 | 适用 |
|------|------|------|
| PyMuPDF | 内置 | 文字型 PDF (98%+) |
| pdfplumber | 内置 | 表格提取 (95%+) |
| Tesseract OCR | +安装 | 图片PDF英文 |
| PaddleOCR | pip | 中英文混合 |

## BLIIOT 规格书处理
- specs在 `Desktop/Working/产品规格书/英文资料/`
- DOCX优先（corrupt docx需要 python-docx 修复）
- PDF图片型无法直接提取文字 → OCR