#!/usr/bin/env python3
"""
PDF英文→中文翻译脚本 — redact+insert 原位替换
用法: python translate_pdf_redact.py input.pdf [translations.py]

依赖于同目录下的 translations_MODULE.py （包含 T 字典映射）
内置默认的 T 字典作为示例。
"""
import pymupdf, os, sys, json

def load_translations(module_path=None):
    """Load translation dictionary from a Python file or generate from JSON"""
    if module_path and os.path.exists(module_path):
        import importlib.util
        spec = importlib.util.spec_from_file_location("trans", module_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.T
    return {}

def translate_pdf(input_path, output_path, T, keep_patterns=None):
    """
    Translate an English PDF to Chinese using redact+insert.
    
    Args:
        input_path: Path to source PDF
        output_path: Path for output PDF
        T: dict mapping English text -> Chinese text
        keep_patterns: list of strings to keep in English (matched by substring)
    """
    if keep_patterns is None:
        keep_patterns = [
            'Designed & Maintained', 'ZODSAT', 'Powertel', 'ZETDC',
            'National Project', 'Government of Zimbabwe', 'All rights reserved',
            'https://', 'maps?q=', '-17.', 'Page ', 'HARARE-REGION',
            '📍', '🔒', 'PDF, Excel, CSV',
        ]
    
    doc = pymupdf.open(input_path)
    tmp_path = output_path + ".tmp"
    
    for pn in range(doc.page_count):
        page = doc[pn]
        blocks = page.get_text("dict")["blocks"]
        todo = []
        matched = set()
        
        for b in blocks:
            if b["type"] != 0:
                continue
            for line in b["lines"]:
                for s in line["spans"]:
                    text = s["text"].strip()
                    if not text:
                        continue
                    # Skip intentionally kept patterns
                    if any(k in text for k in keep_patterns):
                        continue
                    cn = T.get(text)
                    if cn and cn != text:
                        rect = pymupdf.Rect(s["bbox"])
                        todo.append((rect, cn, s["size"]))
                        matched.add(text)
        
        if not todo:
            continue
        
        # 1) Redact all
        for rect, cn, size in todo:
            page.add_redact_annot(rect, fill=(1, 1, 1))
        
        # 2) Apply (keep images!)
        page.apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_NONE)
        
        # 3) Insert Chinese
        for rect, cn, size in todo:
            page.insert_text(
                (rect.x0, rect.y1 - 1),
                cn,
                fontname='china-ss',
                fontsize=size,
                color=(0, 0, 0)
            )
        
        print(f"Page {pn+1}: {len(todo)} translations")
    
    doc.save(tmp_path, garbage=4, deflate=True)
    doc.close()
    os.replace(tmp_path, output_path)
    print(f"\nSaved: {os.path.getsize(output_path)//1024} KB -> {output_path}")

def find_remaining_english(pdf_path, keep_patterns=None):
    """Scan a translated PDF for remaining untranslated English text."""
    if keep_patterns is None:
        keep_patterns = [
            'Designed & Maintained', 'ZODSAT', 'Powertel', 'ZETDC',
            'National Project', 'Government of Zimbabwe', 'All rights reserved',
            'https://', 'maps?q=', '-17.', 'Page ', 'HARARE-REGION',
            '📍', '🔒', 'PDF, Excel, CSV',
        ]
    
    doc = pymupdf.open(pdf_path)
    remaining = []
    cn_pages = 0
    
    for pn in range(doc.page_count):
        text = doc[pn].get_text()
        if any('\u4e00' <= c <= '\u9fff' for c in text):
            cn_pages += 1
        
        for line in text.split('\n'):
            l = line.strip()
            if len(l) > 3 and all(c.isascii() for c in l) and any(c.isalpha() for c in l):
                if not any(k in l for k in keep_patterns):
                    remaining.append(f"P{pn+1}| {l[:120]}")
    
    doc.close()
    return remaining, cn_pages


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python translate_pdf_redact.py input.pdf output.pdf [translations.py]")
        print("  translations.py: optional Python file with T = {...} dict")
        sys.exit(1)
    
    SRC = sys.argv[1]
    OUT = sys.argv[2]
    T = load_translations(sys.argv[3] if len(sys.argv) > 3 else None)
    
    if not T:
        print("ERROR: No translations provided. Create a translations file with T = {...}")
        print("Example format:")
        print('  T = {')
        print('      "Original English": "中文翻译",')
        print('      "Another text": "另一段翻译",')
        print('  }')
        sys.exit(1)
    
    translate_pdf(SRC, OUT, T)
    
    # Verify
    remaining, cn_pages = find_remaining_english(OUT)
    if remaining:
        print(f"\n⚠️ {len(remaining)} untranslated English texts:")
        for r in remaining[:20]:
            print(f"  {r}")
        if len(remaining) > 20:
            print(f"  ... and {len(remaining)-20} more")
    else:
        print("\n✅ ALL TEXT TRANSLATED!")
    print(f"📊 {cn_pages}/25 pages have Chinese text")