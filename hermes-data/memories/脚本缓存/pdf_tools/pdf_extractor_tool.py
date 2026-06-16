#!/usr/bin/env python3
"""
BLIIOT PDF 智能提取工具 v1.0
===========================
支持自动检测 PDF 类型（文字型 vs 图片型）并选择最佳提取方法

依赖:
  pip install PyMuPDF pdfplumber
  (可选) pip install pytesseract pdf2image pillow + 安装 Tesseract OCR
  (可选) pip install paddlepaddle paddleocr

用法:
  python pdf_extractor_tool.py sample.pdf              # 自动检测并提取
  python pdf_extractor_tool.py sample.pdf --mode table  # 只提取表格
  python pdf_extractor_tool.py sample.pdf --output md   # 输出 Markdown
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Optional


# ============================================================
# 检测器：判断 PDF 是文字型还是图片型
# ============================================================

def detect_pdf_type(pdf_path: str) -> dict:
    """
    分析 PDF 文件：
    - 文字型（可以直接提取文字）
    - 图片型（需要 OCR）
    - 混合型（部分文字+部分图片）

    返回分析报告
    """
    import fitz  # PyMuPDF

    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    text_pages = 0
    image_pages = 0
    total_text_len = 0
    total_images = 0

    for page_num in range(total_pages):
        page = doc[page_num]
        text = page.get_text().strip()
        total_text_len += len(text)

        # 检查页面是否有文字
        if len(text) > 50:
            text_pages += 1

        # 检查页面中的图片
        images = page.get_images(full=True)
        total_images += len(images)
        if len(images) > 0 and len(text) < 50:
            image_pages += 1

    doc.close()

    # 判断类型
    text_ratio = text_pages / total_pages if total_pages > 0 else 0
    image_ratio = image_pages / total_pages if total_pages > 0 else 0

    if text_ratio > 0.8 and total_text_len > 500:
        pdf_type = "text"
    elif image_ratio > 0.6:
        pdf_type = "scanned_image"
    else:
        pdf_type = "mixed"

    return {
        "path": pdf_path,
        "total_pages": total_pages,
        "text_pages": text_pages,
        "image_pages": image_pages,
        "total_images": total_images,
        "total_text_len": total_text_len,
        "text_ratio": round(text_ratio, 2),
        "image_ratio": round(image_ratio, 2),
        "pdf_type": pdf_type,
    }


# ============================================================
# 提取器：纯文字提取（PyMuPDF）
# ============================================================

def extract_text_pymupdf(pdf_path: str, pages: Optional[list] = None) -> dict:
    """
    使用 PyMuPDF 提取文字内容
    最适合：文字型 PDF（矢量文字）
    """
    import fitz

    doc = fitz.open(pdf_path)
    result = {"pages": [], "total_text": ""}

    page_range = pages if pages else range(len(doc))

    for page_num in page_range:
        if page_num >= len(doc):
            break
        page = doc[page_num]

        # 提取文字（含布局信息）
        text = page.get_text("text")

        # 提取带位置信息的字典
        blocks = page.get_text("dict")["blocks"]

        # 按段落组织文本
        paragraphs = []
        for block in blocks:
            if block["type"] == 0:  # 文字块
                for line in block["lines"]:
                    line_text = " ".join(
                        span["text"] for span in line["spans"]
                    )
                    if line_text.strip():
                        paragraphs.append(line_text)

        page_data = {
            "page_num": page_num + 1,
            "text": text,
            "paragraphs": paragraphs,
            "char_count": len(text),
        }
        result["pages"].append(page_data)
        result["total_text"] += text + "\n\n" if text else ""

    doc.close()
    return result


# ============================================================
# 提取器：表格提取（pdfplumber）
# ============================================================

def extract_tables(pdf_path: str, pages: Optional[list] = None) -> dict:
    """
    使用 pdfplumber 提取表格
    最适合：带表格的 PDF（报价单、规格表）
    """
    import pdfplumber

    result = {"tables": [], "total_tables": 0}

    with pdfplumber.open(pdf_path) as pdf:
        page_range = pages if pages else range(len(pdf.pages))

        for page_num in page_range:
            if page_num >= len(pdf.pages):
                break
            page = pdf.pages[page_num]

            tables = page.extract_tables()
            for table_idx, table in enumerate(tables):
                # 清理空单元格
                cleaned = [
                    [cell.strip() if cell else "" for cell in row]
                    for row in table
                ]
                result["tables"].append(
                    {
                        "page": page_num + 1,
                        "table_index": table_idx,
                        "rows": len(cleaned),
                        "cols": len(cleaned[0]) if cleaned else 0,
                        "data": cleaned,
                    }
                )
                result["total_tables"] += 1

    return result


# ============================================================
# 提取器：OCR 提取（需要 Tesseract 或 PaddleOCR）
# ============================================================

def extract_ocr(pdf_path: str, engine: str = "auto",
                pages: Optional[list] = None) -> dict:
    """
    OCR 提取图片型 PDF 的文字
    需要安装：pip install pytesseract pdf2image pillow

    engine: "tesseract" | "paddle" | "auto"
    """
    import fitz

    doc = fitz.open(pdf_path)
    result = {"pages": [], "engine": engine, "warning": ""}
    page_range = pages if pages else range(len(doc))

    try:
        import pdf2image
        import pytesseract
        from PIL import Image
        import io

        has_tesseract = True
        result["engine"] = "tesseract"
    except ImportError:
        has_tesseract = False

    try:
        from paddleocr import PaddleOCR
        has_paddle = True
        result["engine"] = "paddle"
    except ImportError:
        has_paddle = False

    if not has_tesseract and not has_paddle:
        result["warning"] = (
            "OCR 引擎未安装！\n"
            "  选项1: pip install pytesseract pdf2image pillow\n"
            "          + 安装 Tesseract OCR (https://github.com/tesseract-ocr/tesseract)\n"
            "  选项2: pip install paddlepaddle paddleocr\n"
        )
        return result

    # PyMuPDF 自带 OCR 接口（调用 Tesseract）
    try:
        for page_num in page_range:
            if page_num >= len(doc):
                break
            page = doc[page_num]

            # 方案A：PyMuPDF 内置 OCR（如果 Tesseract 可用）
            # 将页面转为 pixmap 做 OCR
            try:
                text = page.get_text()
                if len(text.strip()) < 20:
                    # 文字太少，尝试 OCR
                    pix = page.get_pixmap(dpi=300)
                    img_bytes = pix.tobytes("png")

                    if has_tesseract:
                        from PIL import Image
                        import io
                        img = Image.open(io.BytesIO(img_bytes))
                        ocr_text = pytesseract.image_to_string(img, lang="eng+chi_sim")
                        text = ocr_text

                result["pages"].append(
                    {"page_num": page_num + 1, "text": text}
                )
            except Exception as e:
                result["pages"].append(
                    {"page_num": page_num + 1, "text": f"[OCR Error] {e}"}
                )

    except Exception as e:
        result["warning"] += f"\nOCR 执行错误: {e}"

    doc.close()
    return result


# ============================================================
# 统一提取器（自动选择最佳方法）
# ============================================================

def extract_all(pdf_path: str, mode: str = "auto", output: str = "text",
                pages: Optional[list] = None) -> dict:
    """
    统一提取入口 - 自动选择最佳策略

    mode: "auto" | "text" | "table" | "ocr"
    output: "text" | "json" | "md" (markdown)
    """
    if not os.path.exists(pdf_path):
        return {"error": f"文件不存在: {pdf_path}"}

    result = {
        "file": os.path.basename(pdf_path),
        "file_size": f"{os.path.getsize(pdf_path) / 1024:.1f} KB",
    }

    # 1. 分析 PDF 类型
    analysis = detect_pdf_type(pdf_path)
    result["analysis"] = analysis

    # 2. 根据模式提取
    if mode == "table":
        result["tables"] = extract_tables(pdf_path, pages)
    elif mode == "ocr":
        result["ocr"] = extract_ocr(pdf_path, pages=pages)
    elif mode == "text":
        result["text"] = extract_text_pymupdf(pdf_path, pages)
    else:
        # auto: 根据 PDF 类型选择
        if analysis["pdf_type"] == "text":
            result["text"] = extract_text_pymupdf(pdf_path, pages)
            result["tables"] = extract_tables(pdf_path, pages)
        elif analysis["pdf_type"] == "scanned_image":
            result["ocr"] = extract_ocr(pdf_path, pages=pages)
        else:
            result["text"] = extract_text_pymupdf(pdf_path, pages)
            result["tables"] = extract_tables(pdf_path, pages)
            # 如果文字太少也试试 OCR
            if analysis["total_text_len"] < 200:
                result["ocr"] = extract_ocr(pdf_path, pages=pages)

    # 3. 格式转换
    if output == "md":
        result["_markdown"] = _to_markdown(result)

    return result


def _to_markdown(result: dict) -> str:
    """将提取结果转为 Markdown 格式"""
    md = f"# PDF 提取结果: {result['file']}\n\n"
    md += f"文件大小: {result['file_size']}\n\n"

    if "analysis" in result:
        a = result["analysis"]
        md += f"## 分析\n- 类型: {a['pdf_type']}\n- 页数: {a['total_pages']}\n"
        md += f"- 文字页: {a['text_pages']}\n- 图片页: {a['image_pages']}\n\n"

    if "text" in result and "pages" in result["text"]:
        md += "## 文字内容\n\n"
        for p in result["text"]["pages"]:
            md += f"### 第 {p['page_num']} 页\n\n"
            md += p["text"][:2000] + ("\n\n[... 截断]\n\n" if len(p["text"]) > 2000 else "\n\n")

    if "tables" in result and result["tables"]["total_tables"] > 0:
        md += "## 表格\n\n"
        for t in result["tables"]["tables"]:
            md += f"### 第 {t['page']} 页 - 表格 {t['table_index'] + 1} ({t['rows']}行 x {t['cols']}列)\n\n"
            # Markdown 表格
            header = "| " + " | ".join(str(c) for c in t["data"][0]) + " |\n"
            separator = "| " + " | ".join("---" for _ in t["data"][0]) + " |\n"
            rows = ""
            for row in t["data"][1:]:
                rows += "| " + " | ".join(str(c) for c in row) + " |\n"
            md += header + separator + rows + "\n"

    if "ocr" in result and "pages" in result["ocr"]:
        md += "## OCR 提取\n\n"
        md += f"引擎: {result['ocr'].get('engine', 'N/A')}\n\n"
        for p in result["ocr"]["pages"]:
            md += f"### 第 {p['page_num']} 页\n\n{p['text'][:2000]}\n\n"

    return md


# ============================================================
# CLI 入口
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="BLIIOT PDF 智能提取工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python pdf_extractor_tool.py sample.pdf                      # 自动检测
  python pdf_extractor_tool.py sample.pdf --mode table         # 只提取表格
  python pdf_extractor_tool.py sample.pdf --output md          # 输出 MD
  python pdf_extractor_tool.py sample.pdf --pages 1-3          # 只提取1-3页
  python pdf_extractor_tool.py sample.pdf --output md --save   # 保存到文件
        """,
    )
    parser.add_argument("pdf", help="PDF 文件路径")
    parser.add_argument(
        "--mode", choices=["auto", "text", "table", "ocr"],
        default="auto", help="提取模式 (默认: auto)"
    )
    parser.add_argument(
        "--output", choices=["text", "json", "md"],
        default="text", help="输出格式 (默认: text)"
    )
    parser.add_argument("--pages", help="页码范围，如 1-3 或 1,3,5")
    parser.add_argument("--save", action="store_true", help="保存到同名 .md/.json 文件")

    args = parser.parse_args()

    # 解析页码范围
    page_list = None
    if args.pages:
        if "-" in args.pages:
            start, end = args.pages.split("-")
            page_list = list(range(int(start) - 1, int(end)))
        else:
            page_list = [int(p) - 1 for p in args.pages.split(",")]

    # 执行提取
    result = extract_all(args.pdf, mode=args.mode, output=args.output,
                         pages=page_list)

    if "error" in result:
        print(f"[✗] {result['error']}")
        sys.exit(1)

    # 按格式输出
    if args.output == "md" and "_markdown" in result:
        output_text = result["_markdown"]
    elif args.output == "json":
        output_text = json.dumps(result, indent=2, ensure_ascii=False)
    else:
        # text 模式：直接拼接所有文字
        lines = []
        if "analysis" in result:
            a = result["analysis"]
            lines.append(f"=== PDF 分析 ===")
            lines.append(f"类型: {a['pdf_type']}")
            lines.append(f"页数: {a['total_pages']} | 文字: {a['total_text_len']}字符")
            lines.append("")

        if "text" in result:
            lines.append("=== 文字内容 ===")
            for p in result["text"]["pages"]:
                lines.append(f"\n--- 第 {p['page_num']} 页 ---")
                lines.append(p["text"])

        if "tables" in result and result["tables"]["total_tables"] > 0:
            lines.append("\n=== 表格 ===")
            for t in result["tables"]["tables"]:
                lines.append(f"\n[第{t['page']}页-表格{t['table_index']+1}]")
                for row in t["data"]:
                    lines.append("  | " + " | ".join(str(c) for c in row) + " |")

        if "ocr" in result:
            if "warning" in result["ocr"] and result["ocr"]["warning"]:
                lines.append(f"\n=== OCR ===")
                lines.append(result["ocr"]["warning"])
            else:
                lines.append("\n=== OCR 提取 ===")
                for p in result["ocr"]["pages"]:
                    lines.append(f"\n--- 第 {p['page_num']} 页 ---")
                    lines.append(p["text"])

        output_text = "\n".join(lines)

    if args.save:
        # 保存到文件
        base = os.path.splitext(args.pdf)[0]
        ext = ".md" if args.output == "md" else ".txt" if args.output == "text" else ".json"
        save_path = base + ext
        with open(save_path, "w", encoding="utf-8") as f:
            f.write(output_text)
        print(f"[✓] 已保存到: {save_path}")
    else:
        print(output_text)


if __name__ == "__main__":
    main()