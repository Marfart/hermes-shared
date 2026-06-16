from fpdf import FPDF
import os

class FinancePDF(FPDF):
    def header(self):
        if self.page_no() > 1:
            self.set_font('Helvetica', 'B', 7)
            self.set_text_color(130, 130, 130)
            self.cell(0, 4, 'XiaoMa Financial Daily  |  2026.05.29  |  Issue #001', 0, 1, 'R')
            self.set_draw_color(200, 200, 200)
            self.set_line_width(0.3)
            self.line(10, self.get_y(), 200, self.get_y())
            self.ln(3)
    
    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 7)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f'Page {self.page_no()}/{{nb}}', 0, 0, 'C')
    
    def cover(self):
        self.add_page()
        self.ln(35)
        self.set_font('Helvetica', 'B', 30)
        self.set_text_color(30, 30, 150)
        self.cell(0, 15, 'XiaoMa Financial Daily', 0, 1, 'C')
        self.ln(3)
        self.set_font('Helvetica', '', 13)
        self.set_text_color(100, 100, 100)
        self.cell(0, 8, 'XiaoMa Cai Jing Ri Bao', 0, 1, 'C')
        self.ln(5)
        self.set_draw_color(30, 30, 150)
        self.set_line_width(0.8)
        self.line(60, self.get_y(), 150, self.get_y())
        self.ln(8)
        self.set_font('Helvetica', '', 10)
        self.set_text_color(130, 130, 130)
        self.cell(0, 6, '2026.05.29  Friday  |  Issue #001', 0, 1, 'C')
        self.ln(5)
        self.set_font('Helvetica', '', 9)
        self.cell(0, 6, 'Edited & Analyzed by Tachikoma AI', 0, 1, 'C')
        self.ln(30)
        self.set_font('Helvetica', 'I', 7)
        self.set_text_color(160, 160, 160)
        self.cell(0, 5, 'Data: East Money | Sina Finance | Gelonhui | Xueqiu | Yicai', 0, 1, 'C')
    
    def sec_heading(self, num, title):
        self.set_font('Helvetica', 'B', 14)
        self.set_text_color(30, 30, 150)
        self.ln(4)
        self.cell(0, 10, f'{num}. {title}', 0, 1)
        self.set_draw_color(30, 30, 150)
        self.set_line_width(0.5)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)
    
    def sub_heading(self, title, color=(60, 60, 60)):
        self.set_font('Helvetica', 'B', 10)
        self.set_text_color(*color)
        self.cell(0, 7, title, 0, 1)
        self.ln(1)
    
    def body(self, txt, size=8, color=(50, 50, 50)):
        self.set_font('Helvetica', '', size)
        self.set_text_color(*color)
        self.multi_cell(0, 4.5, txt)
        self.ln(1)
    
    def bullet(self, txt, size=8, bold_prefix=""):
        self.set_font('Helvetica', '', size)
        self.set_text_color(50, 50, 50)
        self.cell(5, 4.5, '-', 0, 0)
        if bold_prefix:
            self.set_font('Helvetica', 'B', size)
        prefix_text = f"{bold_prefix}: {txt}" if bold_prefix else txt
        self.set_x(16)
        self.multi_cell(self.w - 2 * self.l_margin - 10, 4.5, prefix_text)
        self.ln(0.5)
    
    def stat_block(self, items):
        for label, val in items:
            self.set_font('Helvetica', 'B', 8)
            self.set_text_color(60, 60, 60)
            w = self.get_string_width(label) + 3
            self.cell(w, 5, label, 0, 0)
            if val.startswith('+') or val.startswith('\(+)'):
                self.set_fill_color(60, 180, 60)
            elif val.startswith('-') or val.startswith('\(-)'):
                self.set_fill_color(200, 60, 60)
            else:
                self.set_fill_color(100, 100, 180)
            self.set_font('Helvetica', '', 8)
            self.set_text_color(255, 255, 255)
            self.cell(35, 5, f' {val}', 0, 1, 'L', True)
        self.ln(2)
    
    def highlight_box(self, title, body, color=(30, 30, 150)):
        self.set_draw_color(*color)
        self.set_line_width(0.3)
        y = self.get_y()
        self.rect(12, y, 186, 50, 'D')
    
    def risk_warn(self):
        self.ln(2)
        self.set_font('Helvetica', 'I', 7)
        self.set_text_color(180, 50, 50)
        self.multi_cell(0, 3.5, 'DISCLAIMER: This report is for educational purposes only. Not investment advice. Investments carry risk of loss. Past performance does not guarantee future results.')
        self.ln(2)


pdf = FinancePDF()
pdf.alias_nb_pages()
pdf.set_auto_page_break(auto=True, margin=20)

# ===== COVER =====
pdf.cover()

# ===== SECTION 1: MARKET OVERVIEW =====
pdf.add_page()
pdf.sec_heading('1', 'Market Overview')

pdf.sub_heading('A-Share Indices (Midday, May 29)')
pdf.stat_block([
    ('Shanghai Comp.', '-0.37%  4083.62'),
    ('Shenzhen Comp.', '-1.00%  15704.04'),
    ('ChiNext', '-1.14%  ~4078'),
    ('Beijing 50', '-2.04%'),
])

pdf.sub_heading('Previous Close (May 28)')
pdf.stat_block([
    ('Shanghai Comp.', '+0.12%  4098.64'),
    ('Shenzhen Comp.', '+0.80%  15861.89'),
    ('ChiNext', '+1.96%  4125.07'),
    ('Beijing 50', '+2.55%'),
])

pdf.sub_heading('ANALYSIS: Today is a classic "rally-pullback" day')
pdf.body('After a strong rally on May 28 where ChiNext surged +1.96% and Beijing 50 hit +2.55%, today the market is experiencing natural profit-taking. Midday data shows the Shanghai market with 922 gainers vs 1385 decliners, and Shenzhen with 927 vs 1951 - clear selling pressure. The market is in a healthy consolidation phase after a 5.66% monthly gain for Shanghai.')

pdf.sub_heading('Global Markets')
pdf.bullet('US stocks (overnight): 3 major indices ALL-TIME HIGH', bold_prefix='US')
pdf.bullet('Snowflake earnings beat > tech stocks re-led the rally', bold_prefix='')
pdf.bullet('US-Iran talks entering "final phase" - hopes of a ceasefire deal', bold_prefix='')
pdf.bullet('WTI crude -5.5%  > geopolitical risk premium collapsing', bold_prefix='Oil')
pdf.bullet('Hong Kong Connect: Northbound net buys of 31.87bn (Shanghai) + 38.15bn (Shenzhen)', bold_prefix='Capital')

pdf.sub_heading('May Summary')
pdf.body('Shanghai Composite is up 5.66% month-to-date. The market has entered a bull phase after a series of counter-cyclical policy measures (rate cuts, property stimulus, RRR cuts). However, the sustained rally means profit-taking pressure is building, and the chip sector (150+ bn yuan ETF outflow in one month) is flashing a warning signal. The structure divergence - main board weak, small-cap/tech strong - is a key feature of this rally.')

pdf.risk_warn()

# ===== SECTION 2: SECTORS & HEADLINES =====
pdf.add_page()
pdf.sec_heading('2', 'Hot Sectors & Breaking News')

pdf.sub_heading('#1 Aluminum / Non-Ferrous Metals - Sector-wide Explosion')
pdf.body('The non-ferrous metals sector, particularly aluminum-related stocks, exploded today with multiple stocks hitting the daily limit up. The logic chain is clear:')
pdf.bullet('Supply-side constraint: China imports ~75% of its bauxite from Guinea. Q1 2026 Guinea exports totaled 60.9M tonnes, with >70% going to China', bold_prefix='Supply')
pdf.bullet('Demand recovery: Infrastructure and manufacturing demand is picking up post-policy stimulus', bold_prefix='Demand')
pdf.bullet('Price transmission: Alumina/aluminum prices rising -> upstream miners profit expansion', bold_prefix='Price')
pdf.bullet('Leading stocks in the sector surged, with some hitting the daily limit', bold_prefix='Movers')

pdf.sub_heading('#2 ZTE Corp (000063) - Limit Up on Buyback Announcement')
pdf.body('ZTE Communications surged to the daily limit up (+10%) after announcing its FIRST-EVER share buyback of nearly 20 million shares worth significant capital. Key factors:')
pdf.bullet('Buyback is a strong signal: management is putting real money where their mouth is', bold_prefix='')
pdf.bullet('"All in AI" strategy: ZTE launched OEX ultra-node interconnect architecture and 800G frame smart computing switches', bold_prefix='')
pdf.bullet('Q1 2026 results: computing products + home terminals + international market all achieved double-digit growth, offsetting the decline in domestic operator investment', bold_prefix='')
pdf.bullet('Changjiang Securities gave a buy rating, calling the buyback a strong undervaluation signal', bold_prefix='')

pdf.sub_heading('#3 Potash / Phosphate - Dongfang Tieta +8%')
pdf.body('Global food security concerns + fertilizer price recovery expectations drove the potash/phosphate segment higher. Dongfang Tieta rose nearly 8%. This sector tends to move with agricultural commodity prices and global supply chain dynamics.')

pdf.sub_heading('Key Market Headlines')
pdf.bullet('27 companies disclosed buyback progress on May 29, with 8 first-time announcements')
pdf.bullet('*ST Asia-Pacific (stock code will change to "Asia-Pacific Industrial") to resume on June 1 after delisting risk removed')
pdf.bullet('Chip sector: YTD outflow from 39 semiconductor/chip ETFs exceeds 150 bn yuan - sector is overheated')
pdf.bullet('AI computing demand driving upstream electronic circuit copper foil technology upgrades, multiple companies investing heavily in HVLP/RTF copper foil capacity')
pdf.bullet('US-China chip tension continues: Germany and Spain oppose EU ban on Huawei equipment')

pdf.sub_heading('Risk Monitor')
pdf.body('1. Chip ETF 150bn+ outflow: crowded trade fading. 2. May rally has accumulated 5.66% gains, profit-taking pressure rising. 3. Structure divergence: main board weak, small-caps strong - if ChiNext has a real pullback, it could drag the whole market. 4. WTI crude crash -5.5% is good for downstream manufacturers but signals demand concerns.', size=7, color=(180, 50, 50))

pdf.risk_warn()

# ===== SECTION 3: FUND ANALYSIS =====
pdf.add_page()
pdf.sec_heading('3', 'Strategy & Fund Analysis')

pdf.sub_heading('Market Context: Dual-Track Market')
pdf.body('May 29 presents an unusual market structure. There are TWO clear tracks running simultaneously:')
pdf.bullet('Cyclical/Value track: Non-ferrous metals (aluminum) are surging on supply-demand dynamics. This is a traditional cyclical resources rally.')
pdf.bullet('Growth/Tech track: ZTE buyback, AI infrastructure spending, and the ChiNext near all-time highs all point to tech/growth momentum.')
pdf.body('This dual-track market means a pure cycle fund will miss the AI/tech upside, while a pure tech fund will miss the resources rally. A "core + satellite" strategy is the recommended approach.')

pdf.sub_heading('Recommended Strategy: Core + Satellite')

pdf.set_draw_color(30, 30, 150)
pdf.set_line_width(0.3)
y = pdf.get_y()
pdf.rect(12, y, 186, 50)
pdf.set_xy(14, y+2)
pdf.set_font('Helvetica', 'B', 9)
pdf.set_text_color(30, 30, 150)
pdf.cell(0, 5, 'CORE (60-70%)', 0, 1)
pdf.set_x(14)
pdf.set_font('Helvetica', '', 8)
pdf.set_text_color(50, 50, 50)
pdf.multi_cell(0, 4, 'ChiNext ETF (159915) or CSI 300 ETF - follow the broad market rally. Passive, low cost, captures the trend without picking winners.')
pdf.set_x(14)
pdf.set_font('Helvetica', 'B', 9)
pdf.set_text_color(30, 30, 150)
pdf.cell(0, 5, 'SATELLITE (20-30%)', 0, 1)
pdf.set_x(14)
pdf.set_font('Helvetica', '', 8)
pdf.multi_cell(0, 4, 'Active fund with holdings spanning BOTH non-ferrous metals AND AI/tech sectors. Look for fund managers who recognized this dual-track early.')
pdf.set_x(14)
pdf.set_font('Helvetica', 'B', 9)
pdf.set_text_color(30, 30, 150)
pdf.cell(0, 5, 'DEFENSIVE (10-20%)', 0, 1)
pdf.set_x(14)
pdf.set_font('Helvetica', '', 8)
pdf.multi_cell(0, 4, 'Bond ETF (e.g. 511880) or low-volatility dividend strategy. This is the rebalancing buffer - when stocks pull back, rebalance from bonds into stocks.')

pdf.sub_heading('Key Valuation Metrics')
pdf.body('Valuation: Moderate. After the May rally (+5.66%), A-shares are not cheap but not yet in bubble territory. The PE of Shanghai is roughly in the 60-70th percentile of historical range.')
pdf.body('Fund Flows: The chip sector seeing 150bn+ outflows is a yellow flag. However, Hong Kong Connect northbound flows remain strong, indicating institutional confidence.')
pdf.body('Policy backdrop: Pro-growth policies remain supportive but the initial stimulus impulse is fading. The market is now pricing in fundamentals rather than policy hopes.')
pdf.body('Global: US at all-time highs = strong tailwind. Oil crash = downstream manufacturing margin expansion. The geopolitical risk premium is collapsing (US-Iran talks = final stage), which is broadly positive for risk assets.')

pdf.sub_heading('Watchlist for Coming Week')
pdf.bullet('ChiNext support level at 4000 - key psychological level to watch', bold_prefix='')
pdf.bullet('ZTE buyback execution progress - will it sustain the AI/telecom rally?')
pdf.bullet('June US Fed rate decision expectations')
pdf.bullet('US-Iran deal finalization - oil could drop further')
pdf.bullet('Monthly P/E ratio changes after May close')

pdf.risk_warn()

# ===== SECTION 4: INVESTMENT QUIZ (MULTIPLE QUESTIONS) =====
pdf.add_page()
pdf.sec_heading('4', 'Investment Classroom')

pdf.sub_heading('\* Question 1: Portfolio Rebalancing', color=(180, 100, 30))
pdf.ln(1)
pdf.set_font('Helvetica', '', 8)
pdf.set_text_color(80, 80, 80)
pdf.multi_cell(0, 4.5, 'Xiaoming started the year with 70% stocks + 30% bonds. By end of May, stocks are up 15% and bonds up 1%. What is the BEST rebalancing action?')
pdf.ln(1)
for o, ans in [
    ('A', 'Add more stocks to 80% - they are performing well'),
    ('B', 'Do nothing - let winners run'),
    ('C', 'Sell some stocks, buy bonds back to 70:30  [ANSWER]'),
    ('D', 'Sell everything, wait for a dip'),
]:
    pdf.set_font('Helvetica', 'B' if 'ANSWER' in o+ans else '', 8)
    pdf.set_text_color(50, 160, 50 if 'ANSWER' in o+ans else 120)
    pdf.set_x(12)
    pdf.cell(6, 4.5, o+')', 0, 0)
    pdf.set_font('Helvetica', '', 8)
    pdf.set_x(18)
    pdf.multi_cell(180, 4.5, ans)
pdf.ln(2)
pdf.set_font('Helvetica', 'B', 8)
pdf.set_text_color(180, 100, 30)
pdf.cell(0, 5, 'EXPLANATION:', 0, 1)
pdf.set_font('Helvetica', '', 7.5)
pdf.set_text_color(50, 50, 50)
pdf.multi_cell(0, 4, 'After a 15% rally, the stock allocation drifts from 70% to ~72.6%. Rebalancing back to 70:30 forces you to sell high (stocks) and buy low (bonds), locking in gains. Without rebalancing, your risk exposure gradually rises. This is the only "free lunch" in portfolio theory (Markowitz).')
pdf.ln(4)

pdf.sub_heading('\* Question 2: Dollar-Cost Averaging (DCA)', color=(180, 100, 30))
pdf.ln(1)
pdf.set_font('Helvetica', '', 8)
pdf.set_text_color(80, 80, 80)
pdf.multi_cell(0, 4.5, 'Xiaoli invests 1000 yuan every month into an index fund regardless of price. The fund price in Jan was 10 yuan, Feb was 8 yuan, and March was 12 yuan. What is her AVERAGE COST per share after 3 months?')
pdf.ln(1)
for o, ans in [
    ('A', '10.00 yuan / share'),
    ('B', '10.67 yuan / share'),
    ('C', '9.73 yuan / share  [ANSWER]'),
    ('D', '8.00 yuan / share'),
]:
    pdf.set_font('Helvetica', 'B' if 'ANSWER' in o+ans else '', 8)
    pdf.set_text_color(50, 160, 50 if 'ANSWER' in o+ans else 120)
    pdf.set_x(12)
    pdf.cell(6, 4.5, o+')', 0, 0)
    pdf.set_font('Helvetica', '', 8)
    pdf.set_x(18)
    pdf.multi_cell(180, 4.5, ans)
pdf.ln(2)
pdf.set_font('Helvetica', 'B', 8)
pdf.set_text_color(180, 100, 30)
pdf.cell(0, 5, 'EXPLANATION:', 0, 1)
pdf.set_font('Helvetica', '', 7.5)
pdf.set_text_color(50, 50, 50)
pdf.multi_cell(0, 4, 'Jan: 1000/10 = 100 shares. Feb: 1000/8 = 125 shares. March: 1000/12 = 83.33 shares. Total = 3000 yuan for 308.33 shares. Average cost = 3000 / 308.33 = 9.73 yuan. Notice the average cost (9.73) is BELOW the average price (10.00)! This is the magic of DCA - you buy more shares when the price is low and fewer when it is high, naturally lowering your average cost.')
pdf.ln(4)

pdf.sub_heading('\* Question 3: PE Ratio', color=(180, 100, 30))
pdf.ln(1)
pdf.set_font('Helvetica', '', 8)
pdf.set_text_color(80, 80, 80)
pdf.multi_cell(0, 4.5, 'A company has a stock price of 50 yuan and earnings per share (EPS) of 2 yuan. What does its PE ratio tell you?')
pdf.ln(1)
for o, ans in [
    ('A', 'The company earned 25 yuan per share'),
    ('B', 'You are paying 25 years of earnings for the stock  [ANSWER]'),
    ('C', 'The stock is guaranteed to go up'),
    ('D', 'The company has 25% profit margin'),
]:
    pdf.set_font('Helvetica', 'B' if 'ANSWER' in o+ans else '', 8)
    pdf.set_text_color(50, 160, 50 if 'ANSWER' in o+ans else 120)
    pdf.set_x(12)
    pdf.cell(6, 4.5, o+')', 0, 0)
    pdf.set_font('Helvetica', '', 8)
    pdf.set_x(18)
    pdf.multi_cell(180, 4.5, ans)
pdf.ln(2)
pdf.set_font('Helvetica', 'B', 8)
pdf.set_text_color(180, 100, 30)
pdf.cell(0, 5, 'EXPLANATION:', 0, 1)
pdf.set_font('Helvetica', '', 7.5)
pdf.set_text_color(50, 50, 50)
pdf.multi_cell(0, 4, 'PE = Price / Earnings = 50 / 2 = 25. This means investors are paying 25 times the annual earnings to own the stock. A PE of 25 implies a 4% earnings yield (1/25). The PE tells you valuation, NOT future direction. For comparison, Shanghai Composite currently trades at roughly 14-15x PE, making it cheaper than most developed markets.')
pdf.ln(4)

pdf.sub_heading('\* Question 4: Stop-Loss & Risk Management', color=(180, 100, 30))
pdf.ln(1)
pdf.set_font('Helvetica', '', 8)
pdf.set_text_color(80, 80, 80)
pdf.multi_cell(0, 4.5, 'Xiaowang buys a stock at 100 yuan. Which stop-loss strategy BEST preserves his capital if the stock drops to 80 yuan?')
pdf.ln(1)
for o, ans in [
    ('A', 'Hold and wait - it might come back up'),
    ('B', 'Set a stop-loss at 95 yuan to limit losses to 5%  [ANSWER]'),
    ('C', 'Buy more when it drops to lower the average cost'),
    ('D', 'Double down and hope for recovery'),
]:
    pdf.set_font('Helvetica', 'B' if 'ANSWER' in o+ans else '', 8)
    pdf.set_text_color(50, 160, 50 if 'ANSWER' in o+ans else 120)
    pdf.set_x(12)
    pdf.cell(6, 4.5, o+')', 0, 0)
    pdf.set_font('Helvetica', '', 8)
    pdf.set_x(18)
    pdf.multi_cell(180, 4.5, ans)
pdf.ln(2)
pdf.set_font('Helvetica', 'B', 8)
pdf.set_text_color(180, 100, 30)
pdf.cell(0, 5, 'EXPLANATION:', 0, 1)
pdf.set_font('Helvetica', '', 7.5)
pdf.set_text_color(50, 50, 50)
pdf.multi_cell(0, 4, 'A stop-loss is your "fire insurance" against catastrophic losses. With a stop at 95 (5% loss), you accept a small, manageable loss to prevent a larger one. If the stock drops to 80, a 5% stop-loss saved you 15% additional loss. Without a stop-loss, the mental temptation to "hold and wait" can turn a 5% loss into 20-30% or more. The key principle: cut losses short, let winners run. A stop-loss is the single most important risk management tool for individual investors.')
pdf.ln(4)

pdf.sub_heading('\* Question 5: Behavioral Finance', color=(180, 100, 30))
pdf.ln(1)
pdf.set_font('Helvetica', '', 8)
pdf.set_text_color(80, 80, 80)
pdf.multi_cell(0, 4.5, 'After hearing that "everyone is making money in stocks," Xiaoli rushes to open a trading account and buys the hottest stocks. This behavior BEST illustrates which cognitive bias?')
pdf.ln(1)
for o, ans in [
    ('A', 'Confirmation bias'),
    ('B', 'Loss aversion'),
    ('C', 'FOMO (Fear Of Missing Out) - herding behavior  [ANSWER]'),
    ('D', 'Anchoring effect'),
]:
    pdf.set_font('Helvetica', 'B' if 'ANSWER' in o+ans else '', 8)
    pdf.set_text_color(50, 160, 50 if 'ANSWER' in o+ans else 120)
    pdf.set_x(12)
    pdf.cell(6, 4.5, o+')', 0, 0)
    pdf.set_font('Helvetica', '', 8)
    pdf.set_x(18)
    pdf.multi_cell(180, 4.5, ans)
pdf.ln(2)
pdf.set_font('Helvetica', 'B', 8)
pdf.set_text_color(180, 100, 30)
pdf.cell(0, 5, 'EXPLANATION:', 0, 1)
pdf.set_font('Helvetica', '', 7.5)
pdf.set_text_color(50, 50, 50)
pdf.multi_cell(0, 4, 'FOMO-driven buying is the most dangerous behavior in investing. When "everyone is making money" is the headline, it often means the market is near its peak - and the retail investor is the last one in. Professional investors typically BUY when there is "blood in the streets" (pessimism) and SELL when "everyone is making money" (euphoria). The best defense against FOMO is to have a written investment plan BEFORE you start trading. In today\'s market context (May 2026 up 5.66%), this is a particularly relevant warning - the euphoria may be nearing its peak.')
pdf.ln(4)

pdf.sub_heading('\* Question 6: Asset Allocation for Beginners', color=(180, 100, 30))
pdf.ln(1)
pdf.set_font('Helvetica', '', 8)
pdf.set_text_color(80, 80, 80)
pdf.multi_cell(0, 4.5, 'Xiaomei is 25 years old with steady income. Which asset allocation is MOST suitable for a young investor with a long time horizon?')
pdf.ln(1)
for o, ans in [
    ('A', '100% bank deposits - safest'),
    ('B', '80% stocks / 20% bonds - aggressive growth  [ANSWER]'),
    ('C', '50% stocks / 50% bonds - balanced'),
    ('D', '20% stocks / 80% bonds - conservative'),
]:
    pdf.set_font('Helvetica', 'B' if 'ANSWER' in o+ans else '', 8)
    pdf.set_text_color(50, 160, 50 if 'ANSWER' in o+ans else 120)
    pdf.set_x(12)
    pdf.cell(6, 4.5, o+')', 0, 0)
    pdf.set_font('Helvetica', '', 8)
    pdf.set_x(18)
    pdf.multi_cell(180, 4.5, ans)
pdf.ln(2)
pdf.set_font('Helvetica', 'B', 8)
pdf.set_text_color(180, 100, 30)
pdf.cell(0, 5, 'EXPLANATION:', 0, 1)
pdf.set_font('Helvetica', '', 7.5)
pdf.set_text_color(50, 50, 50)
pdf.multi_cell(0, 4, 'A common rule of thumb: stock allocation = 100 - age. For a 25 year old: 75% stocks. An 80/20 split is appropriate for a young investor with decades of earning power ahead. She has time to ride out market downturns and benefit from compound growth. As she approaches retirement, the allocation should gradually shift to more bonds. This is called the "glide path" - the stock allocation decreases as age increases. The classic formula: (120 - age) = stock percentage is increasingly popular for modern investors with longer retirement horizons.')
pdf.ln(4)

pdf.set_font('Helvetica', 'I', 8)
pdf.set_text_color(100, 100, 100)
pdf.cell(0, 5, '"The stock market is a device for transferring money from the impatient to the patient." - Warren Buffett', 0, 1)

# ===== SECTION 5: SUMMARY =====
pdf.add_page()
pdf.sec_heading('5', 'Daily Summary')

pdf.sub_heading('XiaoMa Financial Daily - Closing Thoughts')

items = [
    ('MARKET', 'Pullback after rally. Shanghai -0.37%, ChiNext -1.14% midday. May total: +5.66%.'),
    ('HOT', 'Aluminum/non-ferrous (#1), ZTE buyback + limit up (#2), Potash/phosphate (#3)'),
    ('WARNING', 'Chip ETF outflows 150bn+ in one month. Crowded trade unwinding.'),
    ('STRATEGY', 'Core+Satellite. ChiNext ETF for core exposure; active fund for dual-track capture; bonds for rebalancing buffer.'),
    ('GLOBAL', 'US all-time highs + Oil -5.5% (Iran deal) = broadly positive for risk assets.'),
    ('EDUCATION', 'Today: 6 questions covering rebalancing, DCA, PE ratios, stop-loss, behavioral finance, and asset allocation.'),
]
for label, desc in items:
    pdf.set_font('Helvetica', 'B', 9)
    pdf.set_text_color(30, 30, 150)
    w = pdf.get_string_width(label) + 6
    pdf.set_fill_color(230, 235, 255)
    pdf.cell(w, 7, label, 0, 0, 'L', True)
    pdf.set_font('Helvetica', '', 8)
    pdf.set_text_color(50, 50, 50)
    pdf.multi_cell(0, 7, desc)
    pdf.ln(1)

pdf.ln(5)
pdf.set_draw_color(30, 30, 150)
pdf.set_line_width(0.3)
pdf.line(10, pdf.get_y(), 200, pdf.get_y())
pdf.ln(4)

pdf.sub_heading('Next Issue: Monday June 1')
pdf.body('The daily briefing resumes Monday 08:30. Over the weekend, watch for:')
pdf.bullet('US-Iran deal progress (could mean another oil drop Monday)')
pdf.bullet('Weekend global market movements')
pdf.bullet('Monday pre-market sentiment')

pdf.ln(3)
pdf.set_font('Helvetica', 'I', 7)
pdf.set_text_color(160, 160, 160)
pdf.cell(0, 4, 'Generated by XiaoMa Agent (Tachikoma) | Model: DeepSeek-V4-Flash | Hermes Agent', 0, 1, 'C')

# Save
out_path = "C:/Users/Admin/Desktop/XiaoMa_Financial_Daily_20260529.pdf"
pdf.output(out_path)
print(f"Saved: {out_path}")
print(f"Size: {os.path.getsize(out_path)} bytes, Pages: {pdf.page_no()}")
