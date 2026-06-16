#!/usr/bin/env python3
"""每日财经简报 - no_agent 版本
脚本化爬取财经新闻 + 生成PDF，零token消耗
只在有数据时输出PDF路径"""
import urllib.request, urllib.error, json, re, os, textwrap
from datetime import datetime

OUTPUT_DIR = os.path.expanduser("~/Desktop")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def fetch_json(url):
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://finance.eastmoney.com/"
        })
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.read().decode("utf-8", errors="replace")
    except Exception as e:
        return None

def get_fund_data():
    """获取热门基金数据 - 天天基金API"""
    url = "https://fundgz.1234567.com.cn/js/000001.js"
    data = fetch_json(url)
    if not data:
        return []
    # 提取基金估值数据
    results = []
    funds = [
        ("110011", "易方达中小盘混合"),
        ("005827", "易方达蓝筹精选"),
        ("012414", "国泰国证食品饮料"),
        ("008087", "华夏中证5G"),
        ("161725", "招商中证白酒"),
        ("000751", "嘉实新兴产业"),
    ]
    for code, name in funds:
        url = f"https://fundgz.1234567.com.cn/js/{code}.js"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as r:
                raw = r.read().decode("utf-8", errors="replace")
                m = re.search(r'jsonpgz\((.+?)\);', raw)
                if m:
                    d = json.loads(m.group(1))
                    results.append((code, name, float(d.get("gszzl", 0))))
        except: pass
    return results

def get_market_index():
    """获取大盘指数"""
    codes = {
        "000001": "上证指数",
        "399001": "深证成指",
        "399006": "创业板指",
        "000688": "科创50",
    }
    results = []
    for code, name in codes.items():
        url = f"https://push2.eastmoney.com/api/qt/stock/get?secid=1.{code}&fields=f43,f44,f45,f46,f47,f48,f169,f170"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as r:
                d = json.loads(r.read())
                if d.get("data"):
                    data = d["data"]
                    price = data.get("f43", 0) / 100
                    change = data.get("f170", 0) / 100
                    change_pct = data.get("f169", 0) / 100
                    results.append((name, price, change, change_pct))
        except: pass
    return results

def get_news():
    """获取财经头条新闻"""
    url = "https://push2.eastmoney.com/api/qt/ulist.np/get?fltt=2&fields=f12,f14,f2,f3&secids=1.000001,0.399001,0.399006,1.000688&ut=bd1d9ddb04089700cf9c27f6f7426281"
    # 另取新闻
    news_url = "https://push2.eastmoney.com/api/qt/ulist.np/get?fltt=2&fields=f12,f14,f2,f3,f4"
    results = []
    
    # 东财新闻头条
    try:
        req = urllib.request.Request(
            "https://newsapi.eastmoney.com/QQJR/GetNewsList?pageIndex=1&pageSize=10&deviceid=xxx",
            headers={"User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            raw = r.read().decode("utf-8", errors="replace")
            # 尝试找JSON
            m = re.search(r'\[.+?\]', raw, re.DOTALL)
            if m:
                items = json.loads(m.group(0))
                for item in items[:8]:
                    title = item.get("title", "")
                    date = item.get("date", "")[:10]
                    if title:
                        results.append((date, title))
    except: pass
    
    return results[:8]

def generate_report():
    indices = get_market_index()
    funds = get_fund_data()
    news = get_news()
    
    today = datetime.now().strftime("%Y-%m-%d")
    title = f"小马财经日报 #{datetime.now().strftime('%y%m%d')}"
    pdf_path = os.path.join(OUTPUT_DIR, f"XiaoMa_Financial_Daily_{datetime.now().strftime('%Y%m%d')}.pdf")
    
    # 用 reportlab 生成简洁PDF
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.lib.enums import TA_LEFT, TA_CENTER
        
        # 注册中文字体
        font_paths = [
            os.path.expanduser("~/AppData/Local/Microsoft/Windows/Fonts/msyh.ttf"),
            "C:/Windows/Fonts/msyh.ttc",
            "C:/Windows/Fonts/msyh.ttf",
            "C:/Windows/Fonts/simsun.ttc",
            "C:/Windows/Fonts/simsun.ttf",
        ]
        registered = False
        for fp in font_paths:
            if os.path.exists(fp):
                try:
                    pdfmetrics.registerFont(TTFont("CNFont", fp))
                    registered = True
                    break
                except: pass
        if not registered:
            # fallback - reportlab will still work with Helvetica
            cn_font = "Helvetica"
        else:
            cn_font = "CNFont"
        
        styles = getSampleStyleSheet()
        style_normal = ParagraphStyle("CN", fontName=cn_font, fontSize=10, leading=14)
        style_title = ParagraphStyle("CNT", fontName=cn_font, fontSize=18, leading=24, alignment=TA_CENTER, spaceAfter=6)
        style_h1 = ParagraphStyle("CNH1", fontName=cn_font, fontSize=14, leading=18, spaceBefore=12, spaceAfter=6, textColor=colors.HexColor("#1a1a2e"))
        style_small = ParagraphStyle("CNS", fontName=cn_font, fontSize=9, leading=12, textColor=colors.grey)
        style_green = ParagraphStyle("CNG", fontName=cn_font, fontSize=10, leading=14, textColor=colors.HexColor("#e74c3c"))
        style_red = ParagraphStyle("CNR", fontName=cn_font, fontSize=10, leading=14, textColor=colors.HexColor("#27ae60"))
        
        elements = []
        
        # 标题
        elements.append(Paragraph(title, style_title))
        elements.append(Paragraph(f"📅 {today} | 数据来源: 东方财富", style_small))
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#3498db")))
        elements.append(Spacer(1, 10))
        
        # 大盘指数
        elements.append(Paragraph("📊 大盘指数", style_h1))
        if indices:
            data = [["指数", "最新价", "涨跌", "涨跌幅"]]
            for name, price, change, pct in indices:
                arrow = "🔴" if change >= 0 else "🟢"
                pct_str = f"+{pct:.2f}%" if pct >= 0 else f"{pct:.2f}%"
                data.append([name, f"{price:.2f}", f"{arrow} {change:+.2f}", pct_str])
            
            t = Table(data, colWidths=[100, 80, 90, 70])
            t.setStyle(TableStyle([
                ("FONTNAME", (0,0), (-1,-1), cn_font),
                ("FONTSIZE", (0,0), (-1,-1), 10),
                ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#2980b9")),
                ("TEXTCOLOR", (0,0), (-1,0), colors.white),
                ("ALIGN", (0,0), (-1,-1), "CENTER"),
                ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#bdc3c7")),
                ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#f7f9fc")]),
            ]))
            elements.append(t)
        else:
            elements.append(Paragraph("⚠️ 未能获取指数数据", style_normal))
        
        elements.append(Spacer(1, 15))
        
        # 基金估值
        elements.append(Paragraph("💰 热门基金盘中估值", style_h1))
        if funds:
            fund_data = [["基金", "代码", "估值涨跌"]]
            for code, name, pct in funds:
                arrow = "📈" if pct >= 0 else "📉"
                pct_str = f"+{pct:.2f}%" if pct >= 0 else f"{pct:.2f}%"
                fund_data.append([name[:12], code, f"{arrow} {pct_str}"])
            
            t = Table(fund_data, colWidths=[150, 80, 100])
            t.setStyle(TableStyle([
                ("FONTNAME", (0,0), (-1,-1), cn_font),
                ("FONTSIZE", (0,0), (-1,-1), 9),
                ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#8e44ad")),
                ("TEXTCOLOR", (0,0), (-1,0), colors.white),
                ("ALIGN", (0,0), (-1,-1), "CENTER"),
                ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#bdc3c7")),
            ]))
            elements.append(t)
        else:
            elements.append(Paragraph("⚠️ 非交易时段或接口异常", style_small))
        
        elements.append(Spacer(1, 15))
        
        # 财经新闻
        elements.append(Paragraph("📰 财经头条", style_h1))
        if news:
            for date, title in news:
                elements.append(Paragraph(f"• {title}", style_normal))
            elements.append(Spacer(1, 5))
            elements.append(Paragraph("⚠️ 以上为机器采集摘要，仅供参考", style_small))
        else:
            elements.append(Paragraph("⚠️ 新闻接口暂不可用", style_normal))
        
        elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#ecf0f1")))
        elements.append(Spacer(1, 8))
        elements.append(Paragraph("🛡️ 风险提示：本报告仅供参考，不构成投资建议。数据来源东方财富/天天基金，可能存在延迟。", 
                                   ParagraphStyle("CNR", fontName=cn_font, fontSize=8, leading=10, textColor=colors.HexColor("#999"))))
        
        # 生成PDF
        doc = SimpleDocTemplate(pdf_path, pagesize=A4,
                                topMargin=20*mm, bottomMargin=15*mm,
                                leftMargin=15*mm, rightMargin=15*mm)
        doc.build(elements)
        return pdf_path
    except ImportError:
        # 没有 reportlab - 输出纯文本作为备选
        print("⚠️ 缺少 reportlab，输出纯文本报告")
        txt = f"{title}\n{'='*40}\n{today}\n\n"
        txt += "📊 大盘指数:\n"
        if indices:
            for name, price, change, pct in indices:
                txt += f"  {name}: {price:.2f} ({change:+.2f}, {pct:+.2f}%)\n"
        txt += "\n💰 基金估值:\n"
        if funds:
            for code, name, pct in funds:
                txt += f"  {name} ({code}): {pct:+.2f}%\n"
        txt += f"\n📰 财经头条:\n"
        if news:
            for date, title in news:
                txt += f"  • {title[:50]}...\n"
        txt_path = pdf_path.replace(".pdf", ".txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(txt)
        return txt_path
    except Exception as e:
        print(f"❌ PDF生成失败: {e}")
        return None

def main():
    path = generate_report()
    if path and os.path.exists(path):
        sz_kb = os.path.getsize(path) // 1024
        print(f"📄 小马财经日报已生成: {path}")
        print(f"文件大小: {sz_kb}KB")
    else:
        print("⚠️ 财经日报生成失败")

if __name__ == "__main__":
    main()