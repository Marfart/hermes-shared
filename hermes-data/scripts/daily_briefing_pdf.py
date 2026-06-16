#!/usr/bin/env python3
"""
Hermes 全球前沿情报简报 → PDF 生成器
用法: python daily_briefing_pdf.py <markdown_file> [output_pdf]
输出: PDF文件，含公司logo水印、专业排版
"""
import sys
import os
from datetime import datetime

def md_to_pdf(md_path, pdf_path=None):
    """将Markdown简报转为专业PDF"""
    import fitz  # PyMuPDF
    
    if pdf_path is None:
        base = os.path.splitext(md_path)[0]
        pdf_path = base + ".pdf"
    
    # 读取Markdown内容
    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 创建PDF
    doc = fitz.open()
    
    # 页面设置 A4
    page_w, page_h = 595.27, 841.89  # A4
    margin_l, margin_r, margin_t, margin_b = 50, 50, 60, 50
    
    # 颜色定义
    COLOR_TITLE = (0.11, 0.22, 0.45)       # 深蓝
    COLOR_HEADING = (0.15, 0.35, 0.58)     # 中蓝
    COLOR_BODY = (0.18, 0.18, 0.18)         # 近黑
    COLOR_ACCENT = (0.85, 0.32, 0.10)       # 橙红强调
    COLOR_LINK = (0.20, 0.45, 0.75)         # 链接蓝
    COLOR_MUTED = (0.45, 0.45, 0.45)        # 灰色辅助文字
    
    # 水印文字
    WATERMARK = "BLIIOT × Hermes"
    
    def add_watermark(page):
        """添加对角线水印"""
        wm = fitz.TextFont("helv")
        page.insert_text(
            (page_w - 180, page_h - 30),
            WATERMARK,
            fontname="helv",
            fontsize=9,
            color=(0.88, 0.88, 0.88),
        )
    
    def write_page(doc, lines_on_page):
        """将一组行写入一页"""
        page = doc.new_page(width=page_w, height=page_h)
        add_watermark(page)
        return page
    
    # 解析Markdown为结构化块
    blocks = []
    current_block = {"type": "text", "content": "", "level": 0}
    
    for line in content.split("\n"):
        stripped = line.strip()
        if not stripped:
            if current_block["content"]:
                blocks.append(current_block)
            current_block = {"type": "text", "content": "", "level": 0}
            continue
        
        if stripped.startswith("### "):
            if current_block["content"]:
                blocks.append(current_block)
            current_block = {"type": "h3", "content": stripped[4:], "level": 3}
        elif stripped.startswith("## "):
            if current_block["content"]:
                blocks.append(current_block)
            current_block = {"type": "h2", "content": stripped[3:], "level": 2}
        elif stripped.startswith("# "):
            if current_block["content"]:
                blocks.append(current_block)
            current_block = {"type": "h1", "content": stripped[2:], "level": 1}
        elif stripped.startswith("---"):
            if current_block["content"]:
                blocks.append(current_block)
            blocks.append({"type": "hr", "content": "", "level": 0})
            current_block = {"type": "text", "content": "", "level": 0}
        elif stripped.startswith("▸ "):
            if current_block["content"]:
                blocks.append(current_block)
            current_block = {"type": "indent", "content": stripped[2:], "level": 0}
        elif stripped.startswith("→ "):
            if current_block["content"]:
                blocks.append(current_block)
            current_block = {"type": "indent2", "content": stripped[2:], "level": 0}
        else:
            # 追加到当前文本块
            if current_block["type"] == "text" and current_block["content"]:
                current_block["content"] += "\n" + stripped
            else:
                if current_block["content"]:
                    blocks.append(current_block)
                current_block = {"type": "text", "content": stripped, "level": 0}
    
    if current_block["content"]:
        blocks.append(current_block)
    
    # 渲染PDF
    page = doc.new_page(width=page_w, height=page_h)
    add_watermark(page)
    y = margin_t
    
    for block in blocks:
        btype = block["type"]
        text = block["content"]
        
        # 清理Markdown格式符号
        text = text.replace("**", "").replace("*", "•")
        
        if btype == "h1":
            font_size = 20
            color = COLOR_TITLE
            fontname = "helv"
            y += 15
        elif btype == "h2":
            font_size = 16
            color = COLOR_HEADING
            fontname = "helv"
            y += 12
        elif btype == "h3":
            font_size = 13
            color = COLOR_HEADING
            fontname = "helv"
            y += 10
        elif btype == "hr":
            # 画分隔线
            y += 8
            page.draw_line(
                (margin_l, y), (page_w - margin_r, y),
                color=(0.75, 0.75, 0.75), width=0.5
            )
            y += 8
            continue
        elif btype == "indent":
            font_size = 9.5
            color = COLOR_BODY
            fontname = "china-ss"
            text = "  ▸ " + text
        elif btype == "indent2":
            font_size = 9.5
            color = COLOR_MUTED
            fontname = "china-ss"
            text = "    → " + text
        else:
            font_size = 10.5
            color = COLOR_BODY
            fontname = "china-ss"
        
        # 处理emoji - 用文本替换
        emoji_map = {
            "🧠": "[INTEL]", "🔥": "[!]", "爵士": "爵士", "🎮": "[GAME]",
            "🎵": "[MUSIC]", "🌌": "[SPACE]", "💰": "[FIN]", "🏛️": "[POL]",
            "🌍": "[WORLD]", "🛡️": "[SEC]", "📄": "[PAPER]", "🔬": "[SCI]",
            "⚠️": "[RISK]", "🔍": "[SIGNAL]", "📋": "[TRACK]",
            "🚀": "↑", "📉": "↓", "✅": "✓", "🐴✨": ""
        }
        for emoji, replacement in emoji_map.items():
            text = text.replace(emoji, replacement)
        
        # 写入文本（自动换页）
        try:
            tw = fitz.TextWriter(page)
            font = fitz.Font(fontname)
            # 计算文本所需高度
            line_height = font_size * 1.5
            # 简单自动换行
            max_width = page_w - margin_l - margin_r
            lines = []
            for para_line in text.split("\n"):
                if not para_line.strip():
                    lines.append("")
                    continue
                # 粗略估算每行字符数
                avg_char_width = font_size * 0.55  # 中文字符更宽
                max_chars = int(max_width / avg_char_width)
                if len(para_line) <= max_chars:
                    lines.append(para_line)
                else:
                    # 手动换行
                    current_line = ""
                    for ch in para_line:
                        test_width = font.text_length(current_line + ch, fontsize=font_size)
                        if test_width > max_width:
                            lines.append(current_line)
                            current_line = ch
                        else:
                            current_line += ch
                    if current_line:
                        lines.append(current_line)
            
            needed_height = len(lines) * line_height
            
            # 检查是否需要换页
            if y + needed_height > page_h - margin_b:
                page = doc.new_page(width=page_w, height=page_h)
                add_watermark(page)
                y = margin_t
            
            for i, ln in enumerate(lines):
                if ln.strip():
                    page.insert_text(
                        (margin_l, y + font_size),
                        ln,
                        fontname=fontname,
                        fontsize=font_size,
                        color=color
                    )
                y += line_height
                
        except Exception as e:
            # Fallback: 使用基本写入
            if y + font_size * 2 > page_h - margin_b:
                page = doc.new_page(width=page_w, height=page_h)
                add_watermark(page)
                y = margin_t
            try:
                page.insert_text(
                    (margin_l, y + font_size),
                    text[:200],  # 截断防溢出
                    fontname="helv",
                    fontsize=font_size,
                    color=color
                )
            except:
                pass
            y += font_size * 1.5
    
    # 保存
    doc.save(pdf_path, deflate=True, garbage=4)
    doc.close()
    return pdf_path


def create_briefing_pdf(title, content_text, output_path):
    """
    直接从文本内容生成PDF简报（不依赖中间Markdown文件）
    content_text: 完整的简报文本
    """
    import fitz
    
    doc = fitz.open()
    
    # A4尺寸
    pw, ph = 595.27, 841.89
    ml, mr, mt, mb = 50, 50, 55, 50
    
    # 颜色
    C_TITLE = (0.11, 0.22, 0.45)
    C_H2 = (0.15, 0.35, 0.58)
    C_H3 = (0.20, 0.40, 0.60)
    C_BODY = (0.15, 0.15, 0.15)
    C_ACCENT = (0.85, 0.32, 0.10)
    C_MUTED = (0.50, 0.50, 0.50)
    C_WATERMARK = (0.88, 0.88, 0.88)
    
    WATERMARK = "BLIIOT x Hermes"
    
    def new_page_with_watermark():
        p = doc.new_page(width=pw, height=ph)
        p.insert_text((pw - 170, ph - 28), WATERMARK, fontname="helv", fontsize=8, color=C_WATERMARK)
        # 页面底部横线
        p.draw_line((ml, ph - 45), (pw - mr, ph - 45), color=(0.80, 0.80, 0.80), width=0.5)
        return p
    
    page = new_page_with_watermark()
    y = mt
    
    # 解析内容
    lines = content_text.split("\n")
    
    def needs_new_page(needed_height):
        nonlocal page, y
        if y + needed_height > ph - mb:
            page = new_page_with_watermark()
            y = mt
            return True
        return False
    
    def write_line(text, fontname="china-ss", fontsize=10.5, color=C_BODY, indent=0, line_mult=1.4):
        nonlocal page, y
        if not text.strip():
            y += fontsize * 0.6
            return
        
        max_w = pw - ml - mr - indent
        font = fitz.Font(fontname)
        
        # 手动换行
        result_lines = []
        cur = ""
        for ch in text:
            test = cur + ch
            tw = font.text_length(test, fontsize=fontsize)
            if tw > max_w:
                result_lines.append(cur)
                cur = ch
            else:
                cur = test
        if cur:
            result_lines.append(cur)
        
        lh = fontsize * line_mult
        
        for rl in result_lines:
            needs_new_page(lh)
            page.insert_text(
                (ml + indent, y + fontsize),
                rl,
                fontname=fontname,
                fontsize=fontsize,
                color=color
            )
            y += lh
    
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        # 清理emoji
        emoji_replacements = {
            "🔥": "", "🧠": "", "🎷": "", "🎮": "", "🎵": "", "🌌": "",
            "💰": "", "🏛️": "", "🌍": "", "🛡️": "", "📄": "", "🔬": "",
            "⚠️": "", "🔍": "", "📋": "", "🚀": "^", "📉": "v", "✅": "V",
            "🐴✨": "", "➡️": "->", "▸": ">", "→": "->",
        }
        display = stripped
        for em, rep in emoji_replacements.items():
            display = display.replace(em, rep)
        
        # 移除Markdown粗体标记
        display = display.replace("**", "")
        
        if not display:
            y += 4
            i += 1
            continue
        
        if display == "---":
            needs_new_page(20)
            page.draw_line((ml, y + 5), (pw - mr, y + 5), color=(0.75, 0.75, 0.75), width=0.8)
            y += 15
            i += 1
            continue
        
        if display.startswith("## "):
            display = display[3:]
            y += 12
            needs_new_page(30)
            write_line(display, fontname="helv", fontsize=15, color=C_TITLE)
            y += 6
            i += 1
            continue
        
        if display.startswith("### "):
            display = display[4:]
            y += 10
            needs_new_page(25)
            write_line(display, fontname="helv", fontsize=12.5, color=C_H2)
            y += 4
            i += 1
            continue
        
        # 缩进行
        if display.startswith("  ") or display.startswith("> "):
            display = display.lstrip("> ").lstrip()
            write_line(display, fontsize=9.5, color=C_MUTED, indent=20)
            i += 1
            continue
        
        # 普通行
        write_line(display, fontsize=10.5, color=C_BODY)
        i += 1
    
    doc.save(output_path, deflate=True, garbage=4)
    doc.close()
    return output_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python daily_briefing_pdf.py <markdown文件或--direct>")
        print("  --direct: 从标准输入读取内容")
        sys.exit(1)
    
    if sys.argv[1] == "--direct":
        # 从stdin读取
        content = sys.stdin.read()
        out = sys.argv[2] if len(sys.argv) > 2 else None
        if not out:
            today = datetime.now().strftime("%Y-%m-%d")
            out = os.path.join(os.path.expanduser("~/Desktop"), f"Hermes_简报_{today}.pdf")
        result = create_briefing_pdf("简报", content, out)
    else:
        md_file = sys.argv[1]
        out = sys.argv[2] if len(sys.argv) > 2 else None
        if not out:
            out = os.path.splitext(md_file)[0] + ".pdf"
        result = md_to_pdf(md_file, out)
    
    print(f"PDF已保存: {result}")
    print(f"文件大小: {os.path.getsize(result) / 1024:.1f} KB")