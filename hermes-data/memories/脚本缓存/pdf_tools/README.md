<!-- SKILL.md -->
---
name: pdf-extractor
description: "PDF 智能提取工具 — 自动检测文字型/图片型 PDF，多引擎提取文字和表格"
version: 1.0.0
author: agent (小马)
---

# PDF 智能提取工具

## 核心要点

### PDF 类型检测
- **文字型**：`page.get_text()` -> 超过50字符/页 -> text_ratio > 0.8
- **图片型（扫描件）**：get_images() > 0 且文字 < 50字符/页 -> 需要 OCR
- **混合型**：部分文字 + 部分图片

### 提取引擎优先级

| 方法 | 依赖 | 适用场景 | 准确率 |
|------|------|---------|-------|
| PyMuPDF (fitz) | 内置 | 文字型 PDF | 98%+ |
| pdfplumber | pip 安装 | 表格提取 | 95%+ |
| PyMuPDF OCR | +Tesseract | 图片型 PDF 英文 | 80-95% |
| PaddleOCR | pip 安装 | 中英文图片 | 90%+ |

### 安装 OCR 引擎

```bash
# Tesseract OCR（PyMuPDF OCR 依赖）
# 1. 下载安装：https://github.com/tesseract-ocr/tesseract
# 2. 加入 PATH

# PaddleOCR（中英文效果好）
pip install paddlepaddle paddleocr

# 纯 Python OCR
pip install pytesseract pdf2image pillow
```

## 用法

```bash
# 自动检测类型并提取
python pdf_extractor_tool.py sample.pdf

# 只提取表格
python pdf_extractor_tool.py sample.pdf --mode table

# 输出 Markdown
python pdf_extractor_tool.py sample.pdf --output md

# 指定页码范围
python pdf_extractor_tool.py sample.pdf --pages 1-3

# 保存到文件
python pdf_extractor_tool.py sample.pdf --output md --save
```

## 脚本
**位置**: `memories/脚本缓存/pdf_tools/pdf_extractor_tool.py`