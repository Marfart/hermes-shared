# B2B 客户评分与产品匹配

## 7大产品族

1. **工业网关** (BL116/BL118/BE116/BA116) — PLC协议转换
2. **ARMxy边缘控制器** — 边缘计算, Linux/Node-RED
3. **远程IO/RTU** (IOy系列) — DI/DO/AI/AO, Modbus RTU
4. **R40路由器** — 4G/5G, VPN
5. **RTU50xx** — SCADA遥测
6. **信号隔离器** (BL15x) — 4-20mA
7. **软件** (BLIoTLink/BLRAT) — PLC远程访问

## 评分算法

- 关键词命中: +2 per match
- 用例重叠: +1 if >=2 words
- 行业对齐: +1
- 场景奖励: +3 (PLC/SCADA → gateway)

## 9大行业分类
SCADA/PLC, 系统集成, 能源, 水处理, 工业自动化, IIoT, 油气/矿业, 楼宇自动化, 交通

## 工具
- `bliiot_product_knowledge.py` — 产品知识库
- `customer_analysis.py` — 分析管道
- `bliiot_pro_spider.py` — 网站爬取

## 原则
- 不编造数据
- 应用memo自动生成
- WhatsApp是非洲/发展中国家优先渠道
