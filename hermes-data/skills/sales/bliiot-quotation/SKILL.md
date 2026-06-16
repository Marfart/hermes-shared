---
name: bliiot-quotation
version: "1.0.0"
created: "2026-06-17"
description: "BLIIOT 报价单生成全流程 — 从WhatsApp客户消息提取需求到生成完整报价文件"
---

# BLIIOT 报价单生成流程

## 核心铁律

1. **按文件逐个读取价格**，不按产品跨文件混导
2. **每个文件有自己的价格层级名**，保留原名不归一（有的叫Sample/50pcs/100pcs，有的叫<100pcs/>=100pcs）
3. **检查Excel单元格格式**确定取整还是留2位小数（`0_` = 整数，`0.00_` = 2位）
4. **BL116/BL118 用 ARMxy 列布局**（Col7/8/9），不是 RTU 的 Col3-7
5. **Y板在 ARMxy 文件是双列布局**（左右两列并排）
6. **同一文件可能含多个产品线区域**（如 IIoT Gateways 文件含 BL116 和 BL118 两个 sheet）
7. **4G模块默认加价¥30人民币**，按最新汇率换算为USD
8. **SOM板价格可能变动**，文件中的价格可能与实际不符，必须向Kali确认最新SOM价格
9. **人民币价格按最新汇率换算为USD**（用 web_search 查 "CNY to USD exchange rate"）

## 价格文件位置

```
C:\Users\Admin\Desktop\Working\1.报价文件\2026\
  ├── 202605 BLIIOT IIoT Gateways &BL116&BL118 Price List_Updated.xls  (BL116/BL118/BA系列)
  ├── 202605 BLIIOT IOy Series Edge IO Module Price List.xls            (IOy系列)
  ├── 202605 BLIIOT RTU&Router&Mxxx Price List(1).xls                   (RTU/路由器/M160E)
  ├── 202605 BLIIOT BL21x Series Distributed IO System Price List(1).xls (BL21x)
  ├── 202605 BLIIOT RTU&Router Price List.xls                            (RTU路由器)

C:\Users\Admin\Desktop\Working\1.报价文件\2025\
  ├── 202512 ARMxy Series Embedded Computer Price List(1).xlsx           (ARMxy全系列BL301-BL460)
  ├── 202512 IIoT Gateways Price List.xls                                (旧版网关)
  ├── 202511 BL118 Node-RED Edge Gateway Price List.xls                 (旧版BL118)
  ├── 202511 IOy Series Edge IO Module Price List.xls                    (旧版IOy)

C:\Users\Admin\Desktop\Working\1.报价文件\
  ├── BLIIoT BL16 Series Industrial Ethernet Switch Price List.xls       (交换机)
  ├── X板和Y板基本信息表（2025_04_23）.xlsx                              (X/Y板规格参考)
```

## 产品线 → 价格文件映射

| 产品线 | 文件 | Sheet |
|--------|------|-------|
| BL460/BL440/BL350等 ARMxy | 202512 ARMxy...xlsx | 按型号分sheet（BL310/BL330/.../BL460） |
| BL118B/BL118A/BL118 | 202605 IIoT Gateways...xls | BL118 sheet |
| BL116/BE116/BA116 | 202605 IIoT Gateways...xls | BL116 sheet |
| BA115/BA110/BL10x | 202605 IIoT Gateways...xls | IIoT Gateways sheet（Building HVAC区域） |
| BL120/BL121/BL122/BL123/BL124/BE120 | 202605 IIoT Gateways...xls | IIoT Gateways sheet |
| IOy (BL190/BL191/BL192/BL193/BE190/BA190) | 202605 IOy Series...xls | — |
| RTU5024/5025/5028E/5034 | 202605 RTU&Router...xls | — |
| M160E | 202605 RTU&Router&Mxxx...xls | — |
| R40/R40A/R40B | 202605 RTU&Router...xls | — |
| BL16x 交换机 | BLIIoT BL16 Series...xls | — |
| BL21x 分布式IO | 202605 BL21x Series...xls | — |

## 价格层级规则

1. **有 Samples 列的**，小于10台按 Samples 价算
2. **没有 Samples 列的**，按文档上最低价格层级（通常是<100pcs）算
3. **IOy/ARMxy 系列中 "Online Store & Quotation" 列即样品价**
4. **Y板没有 Sample 价**，Online Store 列写 "Refer to <100pcs"，用 <100pcs 价
5. **SOM板价格单独一行**（常变动），必须确认最新价
6. **SOM335 特殊价**：文件写$62但实际¥420 RMB（需按最新汇率换算）
7. **4G模块价格**：文件价格 + ¥30 RMB（按最新汇率换算为USD）
8. **报价格式**：各部件单独列 + 合计，不要组合单价

## 4G模块选型规则

| 目标地区 | 推荐型号 | 特性 | 文件价 | 实际价 |
|----------|----------|------|--------|--------|
| 北美 | EC25AFFA-512-SGAS | GPS | $33 | $33 + ¥30→≈$37.4 |
| 北美 | EC25-AFA MINIPCIE | GPS | $30 | $30 + ¥30→≈$34.4 |
| 澳洲/台湾/拉美 | EC25-AUXGA-PCIE | GPS | $25 | $25 + ¥30→≈$29.4 |
| 欧洲/非洲/中东/亚洲 | EC25-EUXGR PCIE | GPS | $23 | $23 + ¥30→≈$27.4 |
| 欧洲 CAT1 | EC200U-EUAB | 无GPS | $12 | $12 + ¥30→≈$16.4 |
| 欧洲 CAT4 | EC200A-EUHA | 无GPS | $15 | $15 + ¥30→≈$19.4 |
| 中国/印度 CAT4 | EC20CEHDLG | 无GPS | $19 | $19 + ¥30→≈$23.4 |
| 中国 4G CAT4 | EC20-CE | GPS | $21 | $21 + ¥30→≈$25.4 |

**4G与WiFi互斥**——只能选一个！

## WiFi模块选型

| 型号 | 描述 | <100pcs |
|------|------|---------|
| 双频WiFi (024047) | 2.4G+5.8G | $9 |
| 单频WiFi (24030) | 2.4G | $8 |

## ARMxy 命名规则

```
BL461L-CM5002016-X10
│     │  │         │
│     │  │         └── X板型号 (I/O扩展)
│     │  └─────────── SOM型号 (CM5=Compute Module 5)
│     └────────────── L=4G模块 / W=WiFi模块 / 无=标准版
└──────────────────── 主机型号 (BL460系列)

SOM型号解读：
CM5  = Compute Module 5 (BCM2712)
00   = 无WiFi
02   = 2GB LPDDR4X
016  = 16GB eMMC
```

## BL118 命名规则

```
BL118B-SOM334-X4-Y02-Y31
│      │       │   │   └── Y2板型号（第二Y板，B型支持2个Y板）
│      │       │   └────── Y1板型号（第一Y板）
│      │       └────────── X板型号
│      └────────────────── SOM型号
└───────────────────────── 主机型号 (A=1个Y板, B=2个Y板)
```

**注意**：BL118B-SOM334-X4-Y02-Y31 是模块化组合（主机+SOM+X板+Y板各单独计价再相加）

## 完整报价流程

### Step 1: 读取客户需求
1. 打开 WhatsApp Web（Playwright MCP，CDP端口9223）
2. 遵循 human-like-behavior 技能（随机延迟2-8秒）
3. 点击客户聊天，逐条读取消息
4. 提取关键信息：型号、数量、目标国家、特殊要求

### Step 2: 确定价格文件和层级
1. 根据产品型号确定对应的价格文件
2. 确定数量对应的价格层级（Sample / <100pcs / >=100pcs）
3. 确认SOM板最新价格（文件价格可能过时，问Kali）
4. 计算4G模块加价（文件价 + ¥30 按最新汇率）

### Step 3: 生成报价文件
1. 格式：纯文本 .txt，保存到桌面
2. 文件名：`BLIIOT_Quotation_{客户名}_{国家}.txt`
3. 内容结构：
   - 标题（客户名、国家、日期）
   - 产品型号 + 数量
   - 分部件价格明细（主机 + SOM + X板 + Y板 + 4G/WiFi）
   - 合计
   - 备选配置（WiFi版、4G版、无4G/WiFi版）
   - 运费估算（DHL/FedEx）
   - 备注（FOB深圳、样品层级、付款方式、交期）

### Step 4: 交付
1. 文件保存到 `C:\Users\Admin\Desktop\`
2. 通过 GitHub Gist 上传（如需分享链接）
3. 或直接通过 WhatsApp 发送文本内容

## 常见陷阱

1. **BL118B 有2个Y板槽**，型号里可能出现 Y02-Y31 这样的双Y板组合，每个Y板单独计价
2. **ARMxy Y板是双列布局**，左边 Y01-Y37，右边 Y41-Y96，读取时注意列偏移
3. **BL118 X板** 和 **ARMxy X板** 型号和价格不同（BL118的X0=$5 vs ARMxy的X10=$11）
4. **SOM335** 文件价格$62但实际价格¥420 RMB ≈ $62.16（按2026-06-17汇率0.148），必须按最新汇率
5. **BA115** 不在 ARMxy 文件中，在 IIoT Gateways 文件的 Building HVAC 区域
6. **4G模块价格**必须加¥30 RMB，文件价格是未涨价前的旧价
7. **M160E** 在 RTU&Mxxx 文件，Sample=$157
8. **Y37**（IEPE测量板）=$970，是异常高价，不是打字错误
9. **"Online Store & Quotation"** 列 = 样品位价格（1-9台用这个）
10. **4G和WiFi互斥**——同一台设备只能选一个

## 汇率查询方法

```python
# 在报价流程中查询最新汇率
# web_search("CNY to USD exchange rate today")
# 取第一个结果的汇率数字
# 当前参考：1 CNY ≈ 0.148 USD (2026-06-17)
# ¥30 RMB ≈ $4.44 USD
```

## 报价单模板

```
BLIIOT Quotation — {客户名} ({国家})
Date: {YYYY-MM-DD}
Product: {完整型号}
Email: {邮箱（如有）}
Quantity: {数量}

====================================================
Item Breakdown (Unit Price USD):
====================================================

1. {主机型号} ({主机规格简述})
   Price: ${价格}

2. {SOM型号} ({SOM规格简述})
   Price: ${价格}

3. {X板型号} ({X板规格简述})
   Price: ${价格}

4. {Y板型号} ({Y板规格简述})
   Price: ${价格}

5. {4G/WiFi模块} ({模块规格简述})
   Price: ${价格}（含¥30加价换算）

----------------------------------------------------
{完整型号} Total: ${合计} USD
====================================================

====================================================
Alternative Configurations:
====================================================

Option A — With WiFi: {型号}W-...
  Total: $XXX USD

Option B — With 4G (地区频段): {型号}L-...
  Total: $XXX USD

Option C — Without 4G/WiFi: {基础型号}
  Total: $XXX USD

====================================================
Shipping to {国家} (DHL/FedEx estimated):
====================================================
1 unit sample: ~$XX-XX USD

====================================================
Notes:
====================================================
- All prices are FOB Shenzhen
- Sample price tier (<100pcs) applied
- 4G module and WiFi module are mutually exclusive
- Payment: T/T or PayPal for sample order
- Lead time: 3-5 business days
```