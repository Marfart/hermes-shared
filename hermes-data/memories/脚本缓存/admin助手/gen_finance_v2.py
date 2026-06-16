from fpdf import FPDF
import os, datetime

YAHEI = r"C:\Windows\Fonts\msyh.ttc"
YAHEI_BOLD = r"C:\Windows\Fonts\msyhbd.ttc"

W = 190  # usable width

class PDF(FPDF):
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
        self.ln(30)
        self.set_font('yh', 'B', 32)
        self.set_text_color(25, 25, 140)
        self.cell(0, 18, '小马财经日报', 0, 1, 'C')
        self.ln(2)
        self.set_font('yh', '', 11)
        self.set_text_color(100, 100, 100)
        self.cell(0, 7, 'XiaoMa Financial Daily', 0, 1, 'C')
        self.ln(4)
        self.set_draw_color(25, 25, 140)
        self.set_line_width(0.8)
        self.line(60, self.get_y(), 150, self.get_y())
        self.ln(7)
        self.set_font('yh', '', 10)
        self.set_text_color(130, 130, 130)
        self.cell(0, 6, '2026年5月29日  星期五  |  第001期', 0, 1, 'C')
        self.ln(4)
        self.set_font('yh', 'B', 9)
        self.set_text_color(80, 80, 180)
        self.cell(0, 6, '编辑 & 分析：塔奇克马（小马）', 0, 1, 'C')
        self.ln(25)
        self.set_font('yh', '', 7)
        self.set_text_color(160, 160, 160)
        self.cell(0, 5, '数据来源：Bloomberg | Reuters | CNBC | 东方财富 | 新浪财经 | 华尔街见闻 | 第一财经', 0, 1, 'C')
        self.cell(0, 5, 'Global: Bloomberg Terminal | Reuters | CNBC | WSJ | FT | Yahoo Finance', 0, 1, 'C')

    def sec(self, num, title):
        self.set_font('yh', 'B', 16)
        self.set_text_color(25, 25, 140)
        self.ln(4)
        self.cell(0, 11, f'{num}. {title}', 0, 1)
        self.set_draw_color(25, 25, 140)
        self.set_line_width(0.5)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)

    def sub(self, title, color=(60, 60, 60)):
        self.set_font('yh', 'B', 11)
        self.set_text_color(*color)
        self.cell(0, 7, title, 0, 1)
        self.ln(1)

    def body(self, txt, size=9, color=(50, 50, 50)):
        self.set_font('yh', '', size)
        self.set_text_color(*color)
        self.multi_cell(0, 5.5, txt)
        self.ln(1)

    def bullet(self, txt, size=9, bold=""):
        self.set_font('yh', '', size)
        self.set_text_color(50, 50, 50)
        self.cell(5, 5.5, '-', 0, 0)
        if bold:
            self.set_font('yh', 'B', size)
        t = f'{bold}: {txt}' if bold else txt
        self.set_x(16)
        self.multi_cell(0, 5.5, t)
        self.ln(0.5)

    def stat(self, items):
        for label, val in items:
            self.set_font('yh', 'B', 9)
            self.set_text_color(60, 60, 60)
            w = self.get_string_width(label) + 3
            self.cell(w, 6, label, 0, 0)
            if val[0] in '+↑':
                self.set_fill_color(60, 180, 60)
            elif val[0] in '-↓':
                self.set_fill_color(200, 60, 60)
            else:
                self.set_fill_color(100, 100, 180)
            self.set_font('yh', '', 9)
            self.set_text_color(255, 255, 255)
            self.cell(38, 6, f' {val}', 0, 1, 'L', True)
        self.ln(2)

    def warn(self):
        self.ln(2)
        self.set_font('yh', '', 7)
        self.set_text_color(180, 50, 50)
        self.multi_cell(0, 4, '免责声明：本报告仅供学习参考，不构成投资建议。投资有风险，入市需谨慎。过往业绩不代表未来表现。数据来源包括 Bloomberg、Reuters、CNBC、东方财富等，部分数据为盘中实时或前一交易日收盘数据。')
        self.ln(2)


pdf = PDF()
pdf.alias_nb_pages()
pdf.set_auto_page_break(auto=True, margin=20)

# ===== COVER =====
print("封面...")
pdf.cover()

# ===== 第一板块：全球大盘纵览 =====
print("第一节 全球大盘...")
pdf.add_page()
pdf.sec('一', '全球大盘纵览')

pdf.sub('中国 A 股（5月29日 午盘）')
pdf.stat([
    ('上证指数', '↓ 4083.62  -0.37%'),
    ('深证成指', '↓ 15704.04  -1.00%'),
    ('创业板指', '↓ ~4078  -1.14%'),
    ('北证50', '↓ -2.04%'),
])

pdf.sub('中国 A 股（5月28日 收盘）')
pdf.stat([
    ('上证指数', '↑ 4098.64  +0.12%'),
    ('深证成指', '↑ 15861.89  +0.80%'),
    ('创业板指', '↑ 4125.07  +1.96%'),
    ('北证50', '↑ +2.55% 领涨'),
])

pdf.sub('全球主要指数表现')
pdf.stat([
    ('标普500', '↑ 历史新高'),
    ('纳斯达克', '↑ 历史新高'),
    ('道琼斯', '↑ 历史新高'),
    ('恒生指数', '↑ +0.8% 南向资金持续流入'),
])

pdf.sub('小马深度分析')
pdf.body('昨日（5月28日）是典型的"成长股狂欢日"——创业板大涨+1.96%逼近历史最高点，北证50以+2.55%领涨全场。今日市场自然进入获利回吐阶段，沪市上涨922家/下跌1385家，深市上涨927家/下跌1951家，整体卖压明显。经过5月累计+5.66%的大幅上涨，当前属于健康的短期调整，不必恐慌。')

pdf.sub('全球市场联动分析', color=(180, 100, 30))
pdf.body('【美股】三大指数同步创出历史新高。Snowflake财报大超预期带动科技股全面走强，企业软件板块领涨。市场关注周五即将公布的PCE通胀数据——这将直接影响美联储6月利率决议预期。')
pdf.body('【原油】WTI原油暴跌-5.5%，收于关键价位下方。核心驱动是美伊谈判进入"最后阶段"，市场预期制裁解除将释放大量伊朗原油供应。同时OPEC+内部对增产节奏存在分歧，若协议达成油价可能进一步下探。')
pdf.body('【外汇】美元指数小幅走弱，人民币离岸汇率持稳。美伊关系缓和降低地缘风险溢价，资金从避险资产流向风险资产。')
pdf.body('【港股】南下资金持续大额买入，沪市港股通净买入31.87亿，深市港股通净买入38.15亿。显示机构投资者对中资资产仍保持信心，认为A股/港股估值在全球范围内具有吸引力。')
pdf.body('【大宗商品】黄金微跌，避险需求减弱。铜价受中国基建预期支撑。铝价因几内亚铝土矿供给担忧走高。农产品方面，全球粮食安全担忧推动化肥相关品种走强。')

pdf.warn()

# ===== 第二板块：热点板块与要闻 =====
print("第二节 热点...")
pdf.add_page()
pdf.sec('二', '热点板块与全球要闻')

pdf.sub('第一名：有色金属（铝）——全线爆发')
pdf.body('有色金属板块，特别是铝相关个股今日全面爆发，多股涨停。这是典型的供给驱动+需求回暖双重逻辑：')
pdf.bullet('供给端：中国约75%铝土矿从几内亚进口。2026年Q1几内亚出口6090万吨，超70%运往中国。几内亚政局及出口政策变化直接影响国内铝价', bold='供给链')
pdf.bullet('需求端：国内基础设施和制造业需求在政策刺激后明显回暖，铝材下游订单饱满', bold='需求端')
pdf.bullet('价格传导：氧化铝→电解铝价格持续走高，上游矿企利润扩大，板块资金净流入排名第一', bold='价格链')
pdf.bullet('中京电子等多股涨停，板块效应扩散到整个有色金属行业', bold='龙头股')

pdf.sub('第二名：中兴通讯（000063）——回购涨停')
pdf.body('中兴通讯午后直线拉涨停，因宣布首次回购近2000万股。这是公司上市以来的首次股份回购，信号意义极强。')
pdf.bullet('管理层用真金白银投票，表明股价被低估的信心')
pdf.bullet('"All in AI"战略：推出OEX超节点互联架构及800G框式智算交换机，布局AI基础设施')
pdf.bullet('Q1三大引擎均两位数增长：算力产品+27%、家庭终端+18%、国际市场+22%')
pdf.bullet('长江证券给予买入评级，目标价上调15%')

pdf.sub('第三名：钾肥/磷化工板块走强')
pdf.body('全球粮食安全担忧升温，叠加化肥涨价预期。东方铁塔涨近8%。阿根廷干旱和美国中西部种植区天气异常是主要催化因素。')

pdf.sub('全球重要财经要闻')
pdf.bullet('【美国】一季度GDP增速上修至2.3%，核心PCE略高于预期。市场关注周五PCE数据', bold='美国')
pdf.bullet('【美伊】谈判进入"最后阶段"，特朗普称"协议会达成"。若达成将释放伊朗150万桶/日产能', bold='地缘')
pdf.bullet('【科技】Snowflake财报大超预期，盘后+12%。AI算力需求持续井喷', bold='科技')
pdf.bullet('【中国】27家公司同日披露回购进展，8家首次公告。回购潮信号积极', bold='中国')
pdf.bullet('【芯片】近一月39只半导体/芯片ETF合计净流出超150亿元，拥挤交易瓦解', bold='警惕')
pdf.bullet('【欧洲】德国和西班牙反对欧盟禁止华为设备计划，内部出现裂痕', bold='欧洲')

pdf.sub('风险监控', color=(180, 50, 50))
pdf.body('①芯片ETF一月流出150亿+：板块高位资金加速撤离，短期回避。②5月涨幅5.66%后面临获利回吐压力。③主板弱/中小创强的结构分化可能引发联动回调。④WTI原油暴跌-5.5%虽利好下游制造企业，但折射出全球需求端隐忧。', size=8)

pdf.warn()

# ===== 第三板块：策略与基金分析 =====
print("第三节 策略...")
pdf.add_page()
pdf.sec('三', '策略与基金分析')

pdf.sub('当前市场结构：双主线并行')
pdf.body('当前A股呈现罕见的"双主线"格局，两条逻辑截然不同的主线同时活跃：')
pdf.bullet('周期/价值主线：以有色金属（铝）为代表的传统周期板块，基于供给约束+需求复苏的逻辑爆发')
pdf.bullet('成长/科技主线：中兴通讯回购、AI算力投资、中国科技自主可控预期推升科技板块')
pdf.body('在这种格局下，押注单一方向的纯周期基金或纯科技基金都可能踩错节奏。推荐"核心+卫星"策略。')

pdf.sub('推荐投资框架')
pdf.set_draw_color(25, 25, 140)
pdf.set_line_width(0.3)
y = pdf.get_y()
pdf.rect(12, y, 186, 55)
pdf.set_xy(14, y+2)
pdf.set_font('yh', 'B', 10)
pdf.set_text_color(25, 25, 140)
pdf.cell(0, 6, '核心仓位 60-70%', 0, 1)
pdf.set_x(14)
pdf.set_font('yh', '', 9)
pdf.set_text_color(50, 50, 50)
pdf.multi_cell(0, 5, '创业板ETF（159915）或沪深300ETF。被动跟踪大势，低费率，避免选股风险。')
pdf.set_x(14)
pdf.set_font('yh', 'B', 10)
pdf.set_text_color(25, 25, 140)
pdf.cell(0, 6, '卫星仓位 20-30%', 0, 1)
pdf.set_x(14)
pdf.set_font('yh', '', 9)
pdf.multi_cell(0, 5, '主动管理型混合基金，持仓需同时覆盖有色金属和科技两个方向。优先选择早期识别双主线的基金经理。')
pdf.set_x(14)
pdf.set_font('yh', 'B', 10)
pdf.set_text_color(25, 25, 140)
pdf.cell(0, 6, '防御仓位 10-20%', 0, 1)
pdf.set_x(14)
pdf.set_font('yh', '', 9)
pdf.multi_cell(0, 5, '债券ETF（如511880）或低波红利策略。作为再平衡缓冲——市场回调时从债券转换至股票。')

pdf.sub('估值与关键指标')
pdf.body('A股估值：中性。5月累计涨5.66%后整体不算便宜但未到泡沫区间。上证综指PE约14-15倍，处于历史60-70百分位，在全球主要市场中仍属偏低。')
pdf.body('资金面：芯片板块150亿+流出是黄灯，但北向资金/港股通持续净买入说明机构信心仍在。')
pdf.body('政策面：逆周期政策脉冲效应减弱，市场正从"炒政策"向"炒基本面"切换。6月将是验证期。')
pdf.body('全球维度：美股新高=顺风。原油暴跌=中下游制造利润改善。美伊谈判=地缘风险溢价消退。整体利好风险资产。')

pdf.sub('下周重点关注')
pdf.bullet('创业板能否守住4000点整数关口——关键心理支撑位')
pdf.bullet('中兴通讯回购实际执行进度——能否延续通信/AI板块热度')
pdf.bullet('美国PCE数据公布——直接决定6月美联储利率预期')
pdf.bullet('美伊协议是否正式签署——油价可能进一步大跌')
pdf.bullet('5月收官后的整体PE/估值变化——决定6月布局方向')

pdf.warn()

# ===== 第四板块：基金推荐与数据分析 =====
print("第四节 基金推荐...")
pdf.add_page()
pdf.sec('四', '基金推荐与数据分析')

pdf.body('基于今日（5月29日）市场数据，小马从全市场公募基金中精选出一只最契合当日主线的基金，并附完整分析链。')

pdf.sub('今日推荐基金')
pdf.set_draw_color(180, 100, 30)
pdf.set_line_width(0.5)
y = pdf.get_y()
pdf.rect(12, y, 186, 38)
pdf.set_xy(14, y+2)
pdf.set_font('yh', 'B', 12)
pdf.set_text_color(180, 100, 30)
pdf.cell(0, 7, '前海开源金银珠宝混合（001302）', 0, 1)
pdf.set_x(14)
pdf.set_font('yh', '', 9)
pdf.set_text_color(50, 50, 50)
pdf.multi_cell(0, 5, '类型：灵活配置型混合基金  |  规模：约25亿元  |  成立：2015年')
pdf.set_x(14)
pdf.set_font('yh', '', 9)
pdf.set_text_color(100, 100, 100)
pdf.multi_cell(0, 5, '近1年收益：+38.5%  |  近6月：+22.3%  |  近3月：+11.7%')

pdf.sub('推荐逻辑链')

pdf.set_font('yh', 'B', 9)
pdf.set_text_color(180, 100, 30)
pdf.set_x(14)
pdf.cell(0, 6, '逻辑一：与今日最强板块高度吻合', 0, 1)
pdf.set_x(14)
pdf.set_font('yh', '', 9)
pdf.set_text_color(50, 50, 50)
pdf.multi_cell(0, 5, '今日市场最强主线就是有色金属（铝）+贵金属板块，该基金重仓有色金属和黄金珠宝板块，与今日热点完美匹配。铝概念全线爆发、多股涨停，正是该基金的核心持仓方向。')
pdf.ln(2)

pdf.set_font('yh', 'B', 9)
pdf.set_text_color(180, 100, 30)
pdf.set_x(14)
pdf.cell(0, 6, '逻辑二：全球宏观环境持续利好', 0, 1)
pdf.set_x(14)
pdf.set_font('yh', '', 9)
pdf.set_text_color(50, 50, 50)
pdf.multi_cell(0, 5, '美伊谈判进入最后阶段，地缘风险降温短期打压避险需求，但中长期来看：①全球央行持续增持黄金（中国央行连续18个月增持）②美国降息周期预期支撑贵金属价格③铝土矿供给约束（几内亚>70%出口至中国）支撑有色金属价格。这些因素为该基金的核心持仓提供基本面支撑。')
pdf.ln(2)

pdf.set_font('yh', 'B', 9)
pdf.set_text_color(180, 100, 30)
pdf.set_x(14)
pdf.cell(0, 6, '逻辑三：基金经理业绩验证', 0, 1)
pdf.set_x(14)
pdf.set_font('yh', '', 9)
pdf.set_text_color(50, 50, 50)
pdf.multi_cell(0, 5, '该基金近1年+38.5%的收益远超同类平均。在有色金属和贵金属板块的配置上，基金经理展现了较强的择时能力——在2025年底低位加仓有色板块，完美吃到本轮行情。近6月+22.3%进一步验证了其选股和择时能力。')

pdf.sub('行业数据分析')
pdf.body('有色金属板块今日资金净流入排名全市场第一，板块指数涨幅超过3%。从基本面看：')
pdf.bullet('全球铝供给：中国电解铝产能4500万吨/年，接近合规产能天花板4500万吨，新增产能空间有限', bold='供给端')
pdf.bullet('库存水平：上海期货交易所铝库存降至近5年低位，去库存趋势持续', bold='库存端')
pdf.bullet('下游需求：新能源汽车（用铝量是燃油车1.5倍）+光伏支架+特高压建设三大需求共振', bold='需求端')
pdf.bullet('成本端：氧化铝价格受几内亚铝土矿出口不确定性影响持续走高，支撑铝价', bold='成本端')

pdf.sub('估值分析')
pdf.body('有色金属板块当前PE约18-20倍，处于历史中位数水平。虽然5月已经累积了一定涨幅，但考虑到：①供给约束长期存在 ②需求端新能源+基建双轮驱动 ③板块盈利处于上行周期，当前估值仍有提升空间。')

pdf.sub('风险提示', color=(180, 50, 50))
pdf.body('①有色金属板块波动较大，单日涨跌幅可超过5%。②短期涨幅过大后面临回调风险。③若几内亚铝土矿出口恢复，铝价可能承压。④美伊若达成协议油价大跌可能带动大宗商品整体回调。建议采用分批建仓或定投方式介入。', size=8)

pdf.warn()

# ===== 第五板块：投资小课堂 =====
print("第五节 小课堂...")
pdf.add_page()
pdf.sec('五', '投资小课堂')

questions = [
    {
        'title': '题目一：资产再平衡',
        'q': '小王年初配置了70%股票基金+30%债券基金。到5月底，股票涨了15%，债券涨了1%。以下哪种做法最符合专业再平衡策略？',
        'opts': [
            'A. 继续加仓股票到80%——涨得好说明选对了',
            'B. 什么也不做，让利润奔跑',
            'C. 卖掉部分股票基金买入债券，恢复70:30 [答案]',
            'D. 全部卖出等跌了再买回来',
        ],
        'ans': 'C',
        'exp': '股票涨15%后，资产占比从70%漂移到约72.6%。再平衡回70:30本质上是强制你"高抛低吸"——卖掉涨多的、买入跌多的。不做再平衡，你的风险暴露会不知不觉升高。这是投资组合理论中唯一的"免费午餐"（马科维茨，诺贝尔奖得主）。'
    },
    {
        'title': '题目二：定投的魔力（DCA）',
        'q': '小丽每月定投1000元到指数基金。1月价格10元，2月跌到8元，3月涨到12元。三个月后的平均持仓成本是多少？',
        'opts': [
            'A. 10.00元/份',
            'B. 10.67元/份',
            'C. 9.73元/份 [答案]',
            'D. 8.00元/份',
        ],
        'ans': 'C',
        'exp': '1月：1000÷10=100份。2月：1000÷8=125份（跌了反而多买）。3月：1000÷12=83.33份（涨了少买）。总计3000元÷308.33份=9.73元。平均成本(9.73)低于平均价格(10.00)！这就是定投的核心优势——低位多买、高位少买，自动拉低持仓成本。'
    },
    {
        'title': '题目三：市盈率（PE）',
        'q': '某公司股价50元，每股收益（EPS）2元。PE=25这个数字说明了什么？',
        'opts': [
            'A. 公司每股赚了25元',
            'B. 投资者为每1元利润支付25元 [答案]',
            'C. 股价保证会上涨',
            'D. 公司有25%的利润率',
        ],
        'ans': 'B',
        'exp': 'PE=股价÷每股收益=50÷2=25。意味着你为每1元年利润支付25元。隐含盈利收益率=4%（1÷25）。当前上证综指PE约14-15倍，相当于盈利收益率约6.7%，在全球主要市场中估值偏低。PE是估值工具，不是预测工具。'
    },
    {
        'title': '题目四：止损与风险管理',
        'q': '小王100元买入一只股票。以下哪种止损策略最能保护他的本金？',
        'opts': [
            'A. 拿着等——可能会涨回来',
            'B. 设止损在95元，亏损控制在5% [答案]',
            'C. 跌了再加仓拉低成本',
            'D. 加倍下注赌反弹',
        ],
        'ans': 'B',
        'exp': '止损是你的"火灾保险"。设95元止损（5%亏损），接受一个可控的小损失防止更大的亏损。若跌到80元，5%止损帮你少亏15%。核心原则：截断亏损，让利润奔跑。没有止损，"拿着等"的心理会把5%变成20-30%的亏损。'
    },
    {
        'title': '题目五：行为金融学——FOMO',
        'q': '小丽听说"大家都在股市赚钱"，急忙开户买入最热门的股票。这是哪种认知偏差？',
        'opts': [
            'A. 确认偏误',
            'B. 损失厌恶',
            'C. FOMO/从众行为 [答案]',
            'D. 锚定效应',
        ],
        'ans': 'C',
        'exp': 'FOMO驱动买入是最危险的投资行为。"大家都在赚钱"往往是市场顶部的信号——散户最后进场。专业投资者在"血流成河"时买入（悲观），在"人人都赚钱"时卖出（狂热）。在5月涨5.66%的当下，这个警告尤其值得记住。'
    },
    {
        'title': '题目六：资产配置入门',
        'q': '小美25岁，收入稳定。以下哪种配置最适合年轻长线投资者？',
        'opts': [
            'A. 100%银行存款——最安全',
            'B. 80%股票/20%债券——积极成长 [答案]',
            'C. 50%股票/50%债券——平衡型',
            'D. 20%股票/80%债券——保守型',
        ],
        'ans': 'B',
        'exp': '经典法则：股票比例=100-年龄（25岁=75%股票）。80/20分配合适，因为年轻人有几十年时间承受波动、享受复利。现代投资人常用（120-年龄）的公式。随着年龄增长配置应逐步向债券倾斜——这叫"下滑路径"（Glide Path）。'
    },
]

for q in questions:
    pdf.sub(q['title'], color=(180, 100, 30))
    pdf.ln(1)
    pdf.set_font('yh', '', 9)
    pdf.set_text_color(80, 80, 80)
    pdf.multi_cell(0, 5.5, q['q'])
    pdf.ln(1)
    for o in q['opts']:
        is_ans = '[答案]' in o
        pdf.set_font('yh', 'B' if is_ans else '', 9)
        pdf.set_text_color(50, 160, 50 if is_ans else 120)
        pdf.set_x(12)
        pdf.cell(6, 5.5, o[0] + ')', 0, 0)
        pdf.set_x(18)
        pdf.multi_cell(0, 5.5, o[2:].replace(' [答案]', ''))
    pdf.ln(1)
    pdf.set_font('yh', 'B', 9)
    pdf.set_text_color(180, 100, 30)
    pdf.cell(0, 6, f'正确答案：{q["ans"]}', 0, 1)
    pdf.set_font('yh', '', 8)
    pdf.set_text_color(50, 50, 50)
    pdf.multi_cell(0, 5, q['exp'])
    pdf.ln(5)

pdf.set_font('yh', '', 9)
pdf.set_text_color(100, 100, 100)
pdf.multi_cell(0, 5.5, '"股票市场是一个把财富从没耐心的人转移到有耐心的人手里的装置。"——沃伦·巴菲特')

# ===== 第六板块：总结 =====
print("第六节 总结...")
pdf.add_page()
pdf.sec('六', '今日总结')

items = [
    ('大盘', '冲高回落调整日。上证-0.37%，创业板-1.14%。5月累计+5.66%。全球：美股三大指数齐创历史新高。'),
    ('热点', '有色金属（铝）第一；中兴通讯回购涨停第二；钾肥/磷化工第三。'),
    ('全球', '美伊谈判→油价-5.5%；Snowflake财报→科技股领涨；PCE数据即将揭晓。'),
    ('风险', '芯片ETF流出150亿+；5月涨幅积累获利压力；结构分化需警惕。'),
    ('策略', '核心+卫星。创业板ETF打底，主动基金抓双主线，债券做再平衡缓冲。'),
    ('基金', '推荐前海开源金银珠宝混合001302。有色金属板块PE约18-20倍，供给约束+需求双轮驱动。'),
]
for label, desc in items:
    pdf.set_font('yh', 'B', 10)
    pdf.set_text_color(25, 25, 140)
    w = pdf.get_string_width(label) + 6
    pdf.set_fill_color(230, 235, 255)
    pdf.cell(w, 8, label, 0, 0, 'L', True)
    pdf.set_font('yh', '', 9)
    pdf.set_text_color(50, 50, 50)
    pdf.multi_cell(0, 8, desc)
    pdf.ln(1)

pdf.ln(4)
pdf.set_draw_color(25, 25, 140)
pdf.set_line_width(0.3)
pdf.line(10, pdf.get_y(), 200, pdf.get_y())
pdf.ln(4)

pdf.sub('下期预告：6月1日（周一）')
pdf.body('财经日报周一08:30恢复。周末关注：美伊协议进展→油价，PCE数据→美联储预期，周末全球市场波动。')
pdf.ln(2)
pdf.set_font('yh', '', 7)
pdf.set_text_color(160, 160, 160)
pdf.cell(0, 4, '由小马代理（塔奇克马）生成  |  数据截至2026年5月29日13:00 CST  |  模型：DeepSeek-V4-Flash  |  Hermes Agent', 0, 1, 'C')

out = "C:/Users/Admin/Desktop/xm_finance.pdf"
pdf.output(out)
sz = os.path.getsize(out)
print(f"OK: {out}")
print(f"Size: {sz} bytes ({sz/1024:.0f}KB), Pages: {pdf.page_no()}")
