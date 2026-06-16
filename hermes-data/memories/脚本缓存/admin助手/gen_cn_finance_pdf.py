from fpdf import FPDF
import os

YAHEI = r"C:\Windows\Fonts\msyh.ttc"
YAHEI_BOLD = r"C:\Windows\Fonts\msyhbd.ttc"

class CNFinancePDF(FPDF):
    def __init__(self):
        super().__init__()
        self.add_font('yh', '', YAHEI, uni=True)
        self.add_font('yh', 'B', YAHEI_BOLD, uni=True)
    
    def header(self):
        if self.page_no() > 1:
            self.set_font('yh', 'B', 7)
            self.set_text_color(130, 130, 130)
            self.cell(0, 4, '小马财经日报  |  2026年5月29日  |  第001期', 0, 1, 'R')
            self.set_draw_color(200, 200, 200)
            self.set_line_width(0.3)
            self.line(10, self.get_y(), 200, self.get_y())
            self.ln(3)
    
    def footer(self):
        self.set_y(-15)
        self.set_font('yh', '', 7)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f'第 {self.page_no()} 页', 0, 0, 'C')
    
    def cover(self):
        self.add_page()
        self.ln(35)
        self.set_font('yh', 'B', 28)
        self.set_text_color(30, 30, 150)
        self.cell(0, 15, '小马财经日报', 0, 1, 'C')
        self.ln(3)
        self.set_font('yh', '', 12)
        self.set_text_color(100, 100, 100)
        self.cell(0, 8, 'XiaoMa Financial Daily', 0, 1, 'C')
        self.ln(5)
        self.set_draw_color(30, 30, 150)
        self.set_line_width(0.8)
        self.line(60, self.get_y(), 150, self.get_y())
        self.ln(8)
        self.set_font('yh', '', 10)
        self.set_text_color(130, 130, 130)
        self.cell(0, 6, '2026年5月29日  星期五  |  第001期', 0, 1, 'C')
        self.ln(5)
        self.set_font('yh', 'B', 9)
        self.set_text_color(80, 80, 180)
        self.cell(0, 6, '编辑 & 分析：塔奇克马（小马）', 0, 1, 'C')
        self.ln(30)
        self.set_font('yh', '', 7)
        self.set_text_color(160, 160, 160)
        self.cell(0, 5, '数据来源：东方财富 | 新浪财经 | 格隆汇 | 雪球 | 第一财经', 0, 1, 'C')
    
    def sec(self, num, title):
        self.set_font('yh', 'B', 14)
        self.set_text_color(30, 30, 150)
        self.ln(4)
        self.cell(0, 10, f'{num}. {title}', 0, 1)
        self.set_draw_color(30, 30, 150)
        self.set_line_width(0.5)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)
    
    def sub(self, title, color=(60, 60, 60)):
        self.set_font('yh', 'B', 10)
        self.set_text_color(*color)
        self.cell(0, 7, title, 0, 1)
        self.ln(1)
    
    def body(self, txt, size=8, color=(50, 50, 50)):
        self.set_font('yh', '', size)
        self.set_text_color(*color)
        self.multi_cell(0, 5, txt)
        self.ln(1)
    
    def bullet(self, txt, size=8, bold=""):
        self.set_font('yh', '', size)
        self.set_text_color(50, 50, 50)
        self.cell(5, 5, '-', 0, 0)
        if bold:
            self.set_font('yh', 'B', size)
        t = f'{bold}: {txt}' if bold else txt
        self.set_x(16)
        self.multi_cell(180, 5, t)
        self.ln(0.5)
    
    def stat(self, items):
        for label, val in items:
            self.set_font('yh', 'B', 8)
            self.set_text_color(60, 60, 60)
            w = self.get_string_width(label) + 3
            self.cell(w, 5, label, 0, 0)
            if val[0] in '+↑':
                self.set_fill_color(60, 180, 60)
            elif val[0] in '-↓':
                self.set_fill_color(200, 60, 60)
            else:
                self.set_fill_color(100, 100, 180)
            self.set_font('yh', '', 8)
            self.set_text_color(255, 255, 255)
            self.cell(35, 5, f' {val}', 0, 1, 'L', True)
        self.ln(2)
    
    def warn(self):
        self.ln(2)
        self.set_font('yh', '', 7)
        self.set_text_color(180, 50, 50)
        self.multi_cell(0, 4, '免责声明：本报告仅供学习参考，不构成投资建议。投资有风险，入市需谨慎。过往业绩不代表未来表现。')
        self.ln(2)

pdf = CNFinancePDF()
pdf.alias_nb_pages()
pdf.set_auto_page_break(auto=True, margin=20)

print("Generating cover...")
pdf.cover()

# ===== 第1节：大盘概览 =====
print("Section 1...")
pdf.add_page()
pdf.sec('一', '大盘概览')

pdf.sub('A股主要指数（5月29日 午盘）')
pdf.stat([
    ('上证指数', '↓ 4083.62  -0.37%'),
    ('深证成指', '↓ 15704.04  -1.00%'),
    ('创业板指', '↓ ~4078  -1.14%'),
    ('北证50', '↓ -2.04%'),
])

pdf.sub('昨日收盘（5月28日）')
pdf.stat([
    ('上证指数', '↑ 4098.64  +0.12%'),
    ('深证成指', '↑ 15861.89  +0.80%'),
    ('创业板指', '↑ 4125.07  +1.96%'),
    ('北证50', '↑ 领先  +2.55%'),
])

pdf.sub('小马分析：典型的"冲高回落"日')
pdf.body('昨日创业板大涨+1.96%、北证50大涨+2.55%后，今日市场自然迎来获利回吐。午盘沪市上涨922家、下跌1385家，深市上涨927家、下跌1951家，卖压大于买盘。经过5月大幅上涨（月涨+5.66%），市场处于健康调整阶段。')

pdf.sub('全球市场')
pdf.bullet('美股（隔夜）：三大指数同步创出历史新高', bold='美国')
pdf.bullet('Snowflake财报超预期，科技股引领反弹')
pdf.bullet('美伊谈判进入"最后阶段"，停火协议预期升温')
pdf.bullet('WTI原油大跌-5.5%，地缘溢价快速消退', bold='原油')
pdf.bullet('港股通：北向资金净买入 沪31.87亿 + 深38.15亿', bold='资金')

pdf.sub('月度回顾')
pdf.body('上证指数5月累计上涨5.66%。在逆周期调节政策（降息、房地产刺激、降准）推动下，市场已进入技术性牛市。但持续上涨后获利盘压力增大，芯片板块近一月ETF净流出超过150亿元，是值得警惕的信号。当前市场结构特征明显：主板弱、中小创强。')

pdf.warn()

# ===== 第2节：热点板块与新闻 =====
print("Section 2...")
pdf.add_page()
pdf.sec('二', '热点板块 & 要闻')

pdf.sub('第一名：有色金属（铝概念）全线爆发')
pdf.body('有色金属板块，特别是铝相关个股今日全面爆发，多股涨停。逻辑链条清晰：')
pdf.bullet('供给端：中国约75%铝土矿从几内亚进口。2026年Q1几内亚出口6090万吨，超70%运往中国', bold='供给')
pdf.bullet('需求端：政策刺激后基础设施和制造业需求回暖', bold='需求')
pdf.bullet('价格传导：氧化铝/电解铝价格上涨，上游矿企利润扩大', bold='价格')
pdf.bullet('多只铝概念股涨停，板块资金净流入排行第一', bold='龙头')

pdf.sub('第二名：中兴通讯（000063）涨停')
pdf.body('中兴通讯午后直线拉涨停，因宣布首次回购近2000万股，坚定"All in AI"战略：')
pdf.bullet('回购是管理层用真金白银投票，信号强烈')
pdf.bullet('推出OEX超节点互联架构及800G框式智算交换机')
pdf.bullet('Q1三大引擎（算力产品+家庭终端+国际市场）均两位数增长')
pdf.bullet('长江证券给予买入评级，称回购为低估信号')

pdf.sub('第三名：钾肥/磷化工')
pdf.body('全球粮食安全担忧+化肥涨价预期驱动。东方铁塔涨近8%。此板块随农产品价格和供应链波动。')

pdf.sub('重要要闻')
pdf.bullet('27家公司今日披露回购进展，其中8家首次公告')
pdf.bullet('*ST亚太摘帽，6月1日复牌更名"亚太实业"')
pdf.bullet('芯片板块：近一月39只半导体/芯片ETF合计净流出超150亿元')
pdf.bullet('AI算力需求带动高端电子电路铜箔技术升级，多家公司重金布局HVLP/RTF铜箔')
pdf.bullet('德国和西班牙反对欧盟禁止华为设备计划')

pdf.sub('风险提示', color=(180, 50, 50))
pdf.body('1. 芯片ETF 150亿+流出：拥挤交易正在瓦解。2. 5月涨幅5.66%，获利回吐压力上升。3. 主板弱/中小创强的结构分化若持续，可能引发联动回调。4. WTI原油暴跌-5.5%虽利好下游制造，但折射需求担忧。', size=7, color=(180, 50, 50))

pdf.warn()

# ===== 第3节：策略与基金分析 =====
print("Section 3...")
pdf.add_page()
pdf.sec('三', '策略与基金分析')

pdf.sub('市场背景：双主线并行')
pdf.body('5月29日呈现罕见的双主线市场结构：')
pdf.bullet('周期/价值主线：有色金属（铝）基于供需逻辑爆发，典型的周期资源行情')
pdf.bullet('成长/科技主线：中兴通讯回购、AI基础设施投资、创业板接近历史新高')
pdf.body('纯周期基金会错过科技行情，纯科技基金会错过资源行情。推荐"核心+卫星"策略。')

pdf.sub('推荐策略：核心+卫星')
pdf.set_draw_color(30, 30, 150)
pdf.set_line_width(0.3)
y = pdf.get_y()
pdf.rect(12, y, 186, 50)
pdf.set_xy(14, y+2)
pdf.set_font('yh', 'B', 9)
pdf.set_text_color(30, 30, 150)
pdf.cell(0, 5, '核心仓位（60-70%）', 0, 1)
pdf.set_x(14)
pdf.set_font('yh', '', 8)
pdf.set_text_color(50, 50, 50)
pdf.multi_cell(0, 4.5, '创业板ETF（159915）或沪深300ETF——跟随大势。被动、低费率、捕捉趋势。')
pdf.set_x(14)
pdf.set_font('yh', 'B', 9)
pdf.set_text_color(30, 30, 150)
pdf.cell(0, 5, '卫星仓位（20-30%）', 0, 1)
pdf.set_x(14)
pdf.set_font('yh', '', 8)
pdf.multi_cell(0, 4.5, '主动管理型基金，持仓需同时覆盖有色金属和科技两个方向。寻找早期识别双主线的基金经理。')
pdf.set_x(14)
pdf.set_font('yh', 'B', 9)
pdf.set_text_color(30, 30, 150)
pdf.cell(0, 5, '防御仓位（10-20%）', 0, 1)
pdf.set_x(14)
pdf.set_font('yh', '', 8)
pdf.multi_cell(0, 4.5, '债券ETF或低波红利策略。这是再平衡的缓冲——市场回调时从债券转入股票。')

pdf.sub('关键估值指标')
pdf.body('估值：中性偏合理。5月累计+5.66%后，A股不算便宜但未到泡沫区间。上证PE约在历史60-70百分位。')
pdf.body('资金流向：芯片板块150亿+流出是黄灯信号。但港股通北向资金依然强劲，显示机构信心。')
pdf.body('政策面：逆周期政策仍支撑但脉冲效应减弱，市场从"炒政策"转向"炒基本面"。')
pdf.body('全球：美股新高=强顺风。原油暴跌=下游制造利润改善。美伊谈判=地缘风险溢价消退，整体利好风险资产。')

pdf.sub('下周关注')
pdf.bullet('创业板能否守住4000点——关键心理支撑位')
pdf.bullet('中兴通讯回购执行进度——能否延续AI/通信行情')
pdf.bullet('美联储6月利率决议预期变化')
pdf.bullet('美伊协议落地——油价可能进一步下跌')
pdf.bullet('5月收官后的PE变化')

pdf.warn()

# ===== 第4节：投资小课堂（6道题） =====
print("Section 4...")
pdf.add_page()
pdf.sec('四', '投资小课堂')

questions = [
    {
        'title': '题目一：资产再平衡',
        'question': '小王年初配置了70%股票基金+30%债券基金。到5月底，股票涨了15%，债券涨了1%。以下哪种做法最符合专业再平衡策略？',
        'options': [
            'A. 继续加仓股票到80%——涨得好说明选对了',
            'B. 什么也不用做，让利润奔跑',
            'C. 卖掉部分股票基金，买入债券，恢复70:30  ← 正确答案',
            'D. 全部卖出，等跌了再买回来',
        ],
        'answer': 'C',
        'explain': '股票涨15%后，资产占比从70%漂移到约72.6%。再平衡回到70:30，本质上是强制你"高抛低吸"。不进行再平衡，你的风险暴露会不知不觉升高。这是投资组合理论中唯一的"免费午餐"（马科维茨）。'
    },
    {
        'title': '题目二：定投（DCA）',
        'question': '小丽每月定投1000元到指数基金。1月价格10元，2月8元，3月12元。三个月后的平均成本是多少？',
        'options': [
            'A. 10.00元/份',
            'B. 10.67元/份',
            'C. 9.73元/份  ← 正确答案',
            'D. 8.00元/份',
        ],
        'answer': 'C',
        'explain': '1月：1000÷10=100份。2月：1000÷8=125份。3月：1000÷12=83.33份。总计：3000元÷308.33份=9.73元。平均成本（9.73）低于平均价格（10.00）！这就是定投的魔力——低位多买、高位少买，自然拉低平均成本。'
    },
    {
        'title': '题目三：市盈率（PE）',
        'question': '某公司股价50元，每股收益（EPS）2元。PE=25说明了什么？',
        'options': [
            'A. 公司每股赚了25元',
            'B. 你为每1元利润支付25元的价格  ← 正确答案',
            'C. 股价保证会上涨',
            'D. 公司有25%的利润率',
        ],
        'answer': 'B',
        'explain': 'PE=股价÷每股收益=50÷2=25。意味着投资者为每1元的年利润支付25元。PE=25隐含盈利收益率=4%（1/25）。PE告诉你的是估值水平，不是未来方向。作为参考，上证综指目前PE约14-15倍，比大部分发达市场便宜。'
    },
    {
        'title': '题目四：止损与风控',
        'question': '小王100元买入一只股票。以下哪种止损策略最能保护他的资金？',
        'options': [
            'A. 拿着等——可能还会涨回来',
            'B. 设止损在95元，把亏损控制在5%以内  ← 正确答案',
            'C. 跌了再买，拉低平均成本',
            'D. 加倍下注赌反弹',
        ],
        'answer': 'B',
        'explain': '止损是你的"火灾保险"。设95元止损（亏损5%），你接受一个小的可控损失来防止更大的损失。如果跌到80元，5%止损帮你少亏15%。没有止损，"拿着等"的心理陷阱会把5%亏损变成20-30%。核心原则：截断亏损，让利润奔跑。'
    },
    {
        'title': '题目五：行为金融学',
        'question': '小丽听说"大家都在股市赚钱"，急忙开户买入最热门的股票。这最符合哪种认知偏差？',
        'options': [
            'A. 确认偏误',
            'B. 损失厌恶',
            'C. FOMO（错失恐惧症）/从众行为  ← 正确答案',
            'D. 锚定效应',
        ],
        'answer': 'C',
        'explain': 'FOMO驱动的买入是最危险的投资行为。"大家都在赚钱"往往是市场接近顶部的信号——散户最后进场。专业投资者在"街上血流成河"时买入（悲观），在"人人都赚钱"时卖出（狂热）。5月涨5.66%的今天，这个警告尤其值得警惕。'
    },
    {
        'title': '题目六：资产配置入门',
        'question': '小美25岁，收入稳定。以下哪种配置最适合年轻长线投资者？',
        'options': [
            'A. 100%银行存款——最安全',
            'B. 80%股票/20%债券——积极成长  ← 正确答案',
            'C. 50%股票/50%债券——平衡型',
            'D. 20%股票/80%债券——保守型',
        ],
        'answer': 'B',
        'explain': '经典法则：股票配置比例=100-年龄。25岁=75%股票。80/20分配合适，因为年轻人有几十年的赚钱能力，可以承受市场波动并享受复利增长。随着年龄增长，配置应逐步向债券倾斜——这就是"下滑路径"（glide path）。现代投资者常用（120-年龄）作为股票比例。'
    },
]

for q in questions:
    pdf.sub(q['title'], color=(180, 100, 30))
    pdf.ln(1)
    pdf.set_font('yh', '', 8)
    pdf.set_text_color(80, 80, 80)
    pdf.multi_cell(0, 5, q['question'])
    pdf.ln(1)
    for o in q['options']:
        is_correct = '正确答案' in o or '← 正确答案' in o
        pdf.set_font('yh', 'B' if is_correct else '', 8)
        pdf.set_text_color(50, 160, 50 if is_correct else 120)
        pdf.set_x(12)
        pdf.cell(6, 5, o[0] + ')', 0, 0)
        pdf.set_x(18)
        pdf.multi_cell(180, 5, o[2:].replace('  ← 正确答案', ''))
    pdf.ln(2)
    pdf.set_font('yh', 'B', 8)
    pdf.set_text_color(180, 100, 30)
    pdf.cell(0, 5, f'正确答案：{q["answer"]}', 0, 1)
    pdf.set_font('yh', '', 7.5)
    pdf.set_text_color(50, 50, 50)
    pdf.multi_cell(0, 4.5, q['explain'])
    pdf.ln(5)

pdf.set_font('yh', '', 8)
pdf.set_text_color(100, 100, 100)
pdf.multi_cell(0, 5, '"股票市场是一个把财富从没耐心的人转移到有耐心的人手里的装置。"——沃伦·巴菲特')

# ===== 第5节：总结 =====
print("Section 5...")
pdf.add_page()
pdf.sec('五', '今日总结')

items = [
    ('大盘', '冲高回落的调整日。上证-0.37%，创业板-1.14%。5月累计+5.66%。'),
    ('热点', '有色金属（铝）第一，中兴通讯回购涨停第二，钾肥/磷化工第三'),
    ('风险', '芯片ETF一月内流出150亿+，拥挤交易正在瓦解。5月涨幅大，获利压力增。'),
    ('策略', '核心+卫星。创业板ETF打底，主动基金抓双主线，债券做再平衡缓冲。'),
    ('全球', '美股新高+原油-5.5%=整体利好风险资产。美伊协议是下周最大变量。'),
    ('学习', '今日6道题覆盖：再平衡、定投、PE、止损、行为金融、资产配置。'),
]
for label, desc in items:
    pdf.set_font('yh', 'B', 9)
    pdf.set_text_color(30, 30, 150)
    w = pdf.get_string_width(label) + 6
    pdf.set_fill_color(230, 235, 255)
    pdf.cell(w, 7, label, 0, 0, 'L', True)
    pdf.set_font('yh', '', 8)
    pdf.set_text_color(50, 50, 50)
    pdf.multi_cell(0, 7, desc)
    pdf.ln(1)

pdf.ln(5)
pdf.set_draw_color(30, 30, 150)
pdf.set_line_width(0.3)
pdf.line(10, pdf.get_y(), 200, pdf.get_y())
pdf.ln(4)

pdf.sub('下期：6月1日（周一）')
pdf.body('财经日报于周一08:30恢复。周末关注：')
pdf.bullet('美伊协议进展——可能影响周一开盘油价')
pdf.bullet('周末全球市场波动')
pdf.bullet('周一盘前情绪')

pdf.ln(3)
pdf.set_font('yh', '', 7)
pdf.set_text_color(160, 160, 160)
pdf.cell(0, 4, '由小马代理（塔奇克马）生成  |  模型：DeepSeek-V4-Flash  |  Hermes Agent', 0, 1, 'C')

out = "C:/Users/Admin/Desktop/小马财经日报_20260529.pdf"
pdf.output(out)
print(f"OK: {out}")
print(f"Size: {os.path.getsize(out)} bytes, Pages: {pdf.page_no()}")
