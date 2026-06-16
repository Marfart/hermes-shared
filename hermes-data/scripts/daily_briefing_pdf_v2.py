#!/usr/bin/env python3
"""
Hermes 全球前沿情报简报 → 专业级PDF生成器 v2.0
用 reportlab + 微软雅黑 排版，支持：
- 品牌色彩体系
- 层级化标题（H1/H2/H3）
- 信号置信度色条
- 引用块/缩进
- 表格（市场数据）
- 分隔线/留白
- 页眉页脚+水印
- 自动换页
"""
import os
import sys
import re
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.lib.colors import HexColor, Color, white, black
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY, TA_RIGHT
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether, Frame, PageTemplate,
    BaseDocTemplate, NextPageTemplate, Flowable
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.graphics.shapes import Drawing, Rect, Line, String
from reportlab.graphics import renderPDF

# ─── Font Registration ───────────────────────────────────────
FONT_DIR = "C:/Windows/Fonts"
FONTS = {
    "msyh":    os.path.join(FONT_DIR, "msyh.ttc"),
    "msyhbd":  os.path.join(FONT_DIR, "msyhbd.ttc"),
    "simhei":  os.path.join(FONT_DIR, "simhei.ttf"),
}

for name, path in FONTS.items():
    if os.path.exists(path):
        try:
            pdfmetrics.registerFont(TTFont(name, path, subfontIndex=0))
        except:
            pass

# Register font family for bold/italic support
from reportlab.pdfbase.pdfmetrics import registerFontFamily
try:
    registerFontFamily('msyh', normal='msyh', bold='msyhbd', italic='msyh', boldItalic='msyhbd')
except:
    pass

# ─── Color Palette ───────────────────────────────────────────
class C:
    """Brand colors for Hermes Intelligence Briefing"""
    # Primary
    NAVY       = HexColor('#1B3A6B')    # 主标题、页眉
    BLUE       = HexColor('#2659A0')    # H2标题
    BLUE_LIGHT = HexColor('#3A7BD5')    # H3标题
    # Signal confidence
    RED_HIGH   = HexColor('#C0392B')    # 高置信/高影响
    ORANGE_MED = HexColor('#E67E22')    # 中置信
    YELLOW_LOW = HexColor('#F39C12')    # 低置信/早期信号
    # Body
    BODY       = HexColor('#1A1A1A')    # 正文
    MUTED      = HexColor('#666666')    # 辅助文字/缩进
    LIGHT_BG   = HexColor('#F5F7FA')    # 浅色背景块
    # Accent
    ACCENT     = HexColor('#C0392B')    # 强调红
    ACCENT2    = HexColor('#2E86AB')    # 强调蓝
    # Structure
    LINE       = HexColor('#CCCCCC')    # 分隔线
    LINE_DARK  = HexColor('#1B3A6B')    # 主分隔线
    WHITE      = HexColor('#FFFFFF')
    GRAY_BG    = HexColor('#F0F0F0')    # 表格背景


# ─── Custom Flowables ────────────────────────────────────────

class ColorBar(Flowable):
    """彩色信号条：置信度可视化"""
    def __init__(self, width, height=3*mm, color=C.BLUE):
        Flowable.__init__(self)
        self.width = width
        self.height = height
        self.color = color

    def draw(self):
        self.canv.setFillColor(self.color)
        self.canv.rect(0, 0, self.width, self.height, fill=True, stroke=False)


class SignalBox(Flowable):
    """信号卡片：带左侧色条的标题块"""
    def __init__(self, title, source="", confidence="", width=None, bar_color=C.BLUE):
        Flowable.__init__(self)
        self.title = title
        self.source = source
        self.confidence = confidence
        self.bar_color = bar_color
        self._width = width or 160*mm
        self.height = 14*mm

    def wrap(self, availWidth, availHeight):
        self._width = min(self._width, availWidth)
        return (self._width, self.height)

    def draw(self):
        # Left color bar
        self.canv.setFillColor(self.bar_color)
        self.canv.rect(0, 0, 2*mm, self.height, fill=True, stroke=False)
        # Title
        self.canv.setFont('msyhbd', 11)
        self.canv.setFillColor(C.BODY)
        self.canv.drawString(5*mm, self.height - 5*mm, self.title)
        # Source line
        if self.source:
            self.canv.setFont('msyh', 8)
            self.canv.setFillColor(C.MUTED)
            self.canv.drawString(5*mm, 2*mm, self.source)


# ─── Paragraph Styles ────────────────────────────────────────

def get_styles():
    """Return a dict of all paragraph styles"""
    styles = {}
    
    # H1: Main title
    styles['title'] = ParagraphStyle(
        'Title',
        fontName='msyhbd',
        fontSize=22,
        leading=28,
        textColor=C.NAVY,
        alignment=TA_CENTER,
        spaceAfter=2*mm,
    )
    
    # Subtitle / Date
    styles['date'] = ParagraphStyle(
        'Date',
        fontName='msyh',
        fontSize=11,
        leading=16,
        textColor=C.MUTED,
        alignment=TA_CENTER,
        spaceAfter=8*mm,
    )
    
    # H2: Section heading (with color bar above)
    styles['h2'] = ParagraphStyle(
        'H2',
        fontName='msyhbd',
        fontSize=15,
        leading=22,
        textColor=C.BLUE,
        spaceBefore=10*mm,
        spaceAfter=4*mm,
    )
    
    # H3: Sub-section heading
    styles['h3'] = ParagraphStyle(
        'H3',
        fontName='msyhbd',
        fontSize=12,
        leading=18,
        textColor=C.BLUE_LIGHT,
        spaceBefore=6*mm,
        spaceAfter=3*mm,
    )
    
    # Body text
    styles['body'] = ParagraphStyle(
        'Body',
        fontName='msyh',
        fontSize=9.5,
        leading=15,
        textColor=C.BODY,
        spaceAfter=2*mm,
        alignment=TA_JUSTIFY,
    )
    
    # Indent / analysis
    styles['indent'] = ParagraphStyle(
        'Indent',
        fontName='msyh',
        fontSize=9,
        leading=14,
        textColor=C.MUTED,
        spaceAfter=1.5*mm,
        leftIndent=8*mm,
        alignment=TA_JUSTIFY,
    )
    
    # Analysis block (小马解读)
    styles['analysis'] = ParagraphStyle(
        'Analysis',
        fontName='msyh',
        fontSize=9.5,
        leading=15,
        textColor=C.BODY,
        spaceAfter=2*mm,
        leftIndent=5*mm,
        borderWidth=0,
        borderPadding=0,
        borderColor=C.ACCENT,
        backColor=C.LIGHT_BG,
    )
    
    # Signal tag line (置信度+影响+跨领域)
    styles['signal'] = ParagraphStyle(
        'Signal',
        fontName='msyh',
        fontSize=8.5,
        leading=13,
        textColor=C.MUTED,
        spaceAfter=2*mm,
    )
    
    # Bullet point
    styles['bullet'] = ParagraphStyle(
        'Bullet',
        fontName='msyh',
        fontSize=9.5,
        leading=15,
        textColor=C.BODY,
        spaceAfter=1.5*mm,
        leftIndent=5*mm,
        bulletIndent=0,
    )
    
    # Table header
    styles['th'] = ParagraphStyle(
        'TableHeader',
        fontName='msyhbd',
        fontSize=8.5,
        leading=12,
        textColor=C.WHITE,
        alignment=TA_CENTER,
    )
    
    # Table cell
    styles['td'] = ParagraphStyle(
        'TableCell',
        fontName='msyh',
        fontSize=8.5,
        leading=12,
        textColor=C.BODY,
        alignment=TA_CENTER,
    )
    
    # Footer
    styles['footer'] = ParagraphStyle(
        'Footer',
        fontName='msyh',
        fontSize=7,
        leading=10,
        textColor=C.LINE,
        alignment=TA_CENTER,
    )

    return styles


# ─── Page Templates ──────────────────────────────────────────

def header_footer(canvas, doc):
    """Draw header bar and footer on every page"""
    canvas.saveState()
    w, h = A4
    
    # Header: thin navy bar at top
    canvas.setFillColor(C.NAVY)
    canvas.rect(0, h - 12*mm, w, 12*mm, fill=True, stroke=False)
    canvas.setFont('msyhbd', 8)
    canvas.setFillColor(C.WHITE)
    canvas.drawString(20*mm, h - 8*mm, "Hermes 全球前沿情报简报")
    canvas.setFont('msyh', 7)
    canvas.drawRightString(w - 20*mm, h - 8*mm, "BLIIOT × Hermes Intelligence")
    
    # Footer: thin line + page number
    canvas.setStrokeColor(C.LINE)
    canvas.setLineWidth(0.5)
    canvas.line(20*mm, 12*mm, w - 20*mm, 12*mm)
    canvas.setFont('msyh', 7)
    canvas.setFillColor(C.MUTED)
    canvas.drawCentredString(w/2, 7*mm, f"— {doc.page} —")
    
    # Watermark (bottom right, very light)
    canvas.setFont('msyh', 6)
    canvas.setFillColor(HexColor('#E0E0E0'))
    canvas.drawRightString(w - 15*mm, 4*mm, "BLIIOT × Hermes")
    
    canvas.restoreState()


# ─── Main Builder ─────────────────────────────────────────────

def build_briefing_pdf(content_text: str, output_path: str, date_str: str = ""):
    """
    从文本内容生成专业级PDF简报
    
    content_text: Markdown格式的简报内容
    output_path: 输出PDF路径
    date_str: 日期字符串（如 "2026年06月12日"）
    """
    styles = get_styles()
    story = []
    
    # ─── Parse markdown into structured blocks ────────────────
    lines = content_text.split('\n')
    
    # ─── Title Page ──────────────────────────────────────────
    story.append(Spacer(1, 25*mm))
    story.append(Paragraph("Hermes 全球前沿情报简报", styles['title']))
    if date_str:
        story.append(Paragraph(date_str, styles['date']))
    else:
        story.append(Paragraph(datetime.now().strftime("%Y年%m月%d日"), styles['date']))
    story.append(HRFlowable(width="80%", thickness=2, color=C.NAVY, spaceAfter=5*mm))
    story.append(Spacer(1, 5*mm))
    
    # ─── Process content ─────────────────────────────────────
    for line in lines:
        stripped = line.strip()
        
        # Skip empty lines (add small spacer)
        if not stripped:
            story.append(Spacer(1, 2*mm))
            continue
        
        # Clean markdown bold
        display = stripped
        
        # Detect section type
        if display.startswith('## '):
            text = display[3:].replace('**', '')
            # H2: Section heading with color bar
            story.append(Spacer(1, 3*mm))
            story.append(ColorBar(160*mm, 2*mm, C.NAVY))
            story.append(Paragraph(text, styles['h2']))
            
        elif display.startswith('### '):
            text = display[4:].replace('**', '')
            story.append(Paragraph(text, styles['h3']))
            
        elif display == '---':
            story.append(HRFlowable(width="100%", thickness=0.8, color=C.LINE, spaceAfter=3*mm, spaceBefore=3*mm))
            
        elif display.startswith('[INTEL]') or display.startswith('🧠'):
            # Signal heading - use analysis style with accent
            text = display.replace('[INTEL]', '').replace('🧠', '').strip()
            # Clean emoji
            for em in ['🔥', '🚀', '📉', '✅', '🐴✨', '➡️', '→', '▸']:
                text = text.replace(em, '')
            text = text.replace('**', '')
            story.append(Spacer(1, 2*mm))
            story.append(ColorBar(120*mm, 2.5*mm, C.ACCENT))
            story.append(Paragraph(f"<b>{text}</b>", styles['h3']))
            
        elif display.startswith('→') or display.startswith('➡️'):
            # Signal metadata line
            text = display.lstrip('→➡️').strip()
            text = text.replace('**', '')
            for em in ['🚀', '📉', '✅']:
                text = text.replace(em, '')
            story.append(Paragraph(text, styles['signal']))
            
        elif display.startswith('▸') and ('小马解读' in display or '推演链' in display):
            # Analysis blocks get highlighted
            text = display.lstrip('▸').strip()
            text = text.replace('**', '')
            # Wrap in a light background box
            story.append(Paragraph(text, styles['analysis']))
            
        elif display.startswith('▸'):
            text = display.lstrip('▸').strip()
            text = text.replace('**', '')
            story.append(Paragraph(f"▸ {text}", styles['indent']))
            
        elif display.startswith('- '):
            text = display[2:].replace('**', '')
            for em in ['⚠️', '🔍', '🌍', '🛡️', '💰', '🏛️', '📄', '🔬', '🎵', '🎮', '🌌', '🧠']:
                text = text.replace(em, '')
            story.append(Paragraph(f"• {text}", styles['bullet']))
            
        elif display.startswith('|') and '---' not in display:
            # Table row - collect all table rows and build later
            # For now, render as styled text
            cells = [c.strip().replace('**', '') for c in display.split('|') if c.strip()]
            if cells:
                text = " | ".join(cells)
                story.append(Paragraph(text, styles['signal']))
                
        elif '---' in display and display.strip() == '---':
            story.append(HRFlowable(width="100%", thickness=0.8, color=C.LINE))
            
        else:
            # Regular text
            text = display.replace('**', '')
            # Remove emoji that PyMuPDF can't render
            for em in ['🔥', '🧠', '🎷', '🎮', '🎵', '🌌', '💰', '🏛️', '🌍', '🛡️', 
                       '📄', '🔬', '⚠️', '🔍', '📋', '🚀', '📉', '✅', '🐴✨',
                       '➡️', '→', '▸', '❌', '✅']:
                text = text.replace(em, '')
            story.append(Paragraph(text, styles['body']))
    
    # ─── Build PDF ───────────────────────────────────────────
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=20*mm,
        rightMargin=20*mm,
        topMargin=18*mm,
        bottomMargin=18*mm,
        title=f"Hermes 全球前沿情报简报 - {date_str or datetime.now().strftime('%Y-%m-%d')}",
        author="BLIIOT × Hermes Intelligence",
    )
    
    doc.build(story, onFirstPage=header_footer, onLaterPages=header_footer)
    
    return output_path


def build_data_table(headers, rows, col_widths=None):
    """Build a styled data table (for market data etc.)"""
    styles = get_styles()
    
    # Build header row
    header_row = [Paragraph(h, styles['th']) for h in headers]
    
    # Build data rows
    data_rows = []
    for row in rows:
        data_rows.append([Paragraph(str(c), styles['td']) for c in row])
    
    all_rows = [header_row] + data_rows
    
    if col_widths is None:
        col_widths = [160*mm / len(headers)] * len(headers)
    
    table = Table(all_rows, colWidths=col_widths)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), C.NAVY),
        ('TEXTCOLOR', (0, 0), (-1, 0), C.WHITE),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'msyhbd'),
        ('FONTNAME', (0, 1), (-1, -1), 'msyh'),
        ('FONTSIZE', (0, 0), (-1, -1), 8.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BACKGROUND', (0, 1), (-1, -1), C.WHITE),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [C.WHITE, C.LIGHT_BG]),
        ('GRID', (0, 0), (-1, -1), 0.5, C.LINE),
    ]))
    
    return table


# ─── CLI ─────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python daily_briefing_pdf_v2.py <markdown文件> [输出PDF路径]")
        print("       python daily_briefing_pdf_v2.py --direct [输出PDF路径]")
        sys.exit(1)
    
    if sys.argv[1] == "--direct":
        content = sys.stdin.read()
        out = sys.argv[2] if len(sys.argv) > 2 else None
        if not out:
            today = datetime.now().strftime("%Y-%m-%d")
            out = os.path.join(os.path.expanduser("~/Desktop/Working/Hermes"), f"Hermes_简报_{today}.pdf")
        result = build_briefing_pdf(content, out)
    else:
        md_file = sys.argv[1]
        with open(md_file, "r", encoding="utf-8") as f:
            content = f.read()
        out = sys.argv[2] if len(sys.argv) > 2 else os.path.splitext(md_file)[0] + ".pdf"
        # Extract date from content if possible
        date_match = re.search(r'(\d{4}年\d{2}月\d{2}日)', content)
        date_str = date_match.group(1) if date_match else ""
        result = build_briefing_pdf(content, out, date_str)
    
    print(f"PDF已保存: {result}")
    print(f"文件大小: {os.path.getsize(result)/1024:.1f} KB")