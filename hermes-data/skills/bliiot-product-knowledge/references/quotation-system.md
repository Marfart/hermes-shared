# BLIIOT 报价体系

## 价格文件位置

```
C:\Users\AdminAdmin\Desktop\Working\1.报价文件\2026\
  ├── 202605 BLIIOT IIoT Gateways &BL116&BL118 Price List_Updated.xls  (BL116/BL118/BA系列)
  ├── 202605 BLIIOT IOy Series Edge IO Module Price List.xls            (IOy系列)
  ├── 202605 BLIIOT RTU&Router&Mxxx Price List(1).xls                   (RTU/路由器/M160E)
  ├── 202605 BLIIOT BL21x Series Distributed IO System Price List(1).xls (BL21x)
  ├── 202605 BLIIOT RTU&Router Price List.xls                            (RTU路由器)

C:\Users\AdminAdmin\Desktop\Working\1.报价文件\2025\
  ├── 202512 ARMxy Series Embedded Computer Price List(1).xlsx           (ARMxy全系列BL301-BL460)
  ├── 202512 IIoT Gateways Price List.xls                                (旧版网关)
  ├── 202511 BL118 Node-RED Edge Gateway Price List.xls                 (旧版BL118)
  ├── 202511 IOy Series Edge IO Module Price List.xls                    (旧版IOy)

C:\Users\AdminAdmin\Desktop\Working\1.报价文件\
  ├── BLIIoT BL16 Series Industrial Ethernet Switch Price List.xls       (交换机)
  ├── X板和Y板基本信息表（2025_04_23）.xlsx                              (X/Y板规格参考)
```

## 产品线 -> 价格文件映射

| 产品线 | 文件 | Sheet |
|--------|------|-------|
| BL460/BL440/BL350等 ARMxy | 202512 ARMxy...xlsx | 按型号分sheet |
| BL118B/BL118A/BL118 | 202605 IIoT Gateways...xls | BL118 sheet |
| BL116/BE116/BA116 | 202605 IIoT Gateways...xls | BL116 sheet |
| BA115/BA110/BL10x | 202605 IIoT Gateways...xls | IIoT Gateways sheet |
| BL120/BL121/BL122/BL123/BL124/BE120 | 202605 IIoT Gateways...xls | IIoT Gateways sheet |
| IOy (BL190~BL193/BE190/BA190) | 202605 IOy Series...xls | - |
| RTU5024/5025/5028E/5034 | 202605 RTU&Router...xls | - |
| M160E | 202605 RTU&Router&Mxxx...xls | - |
| R40/R40A/R40B | 202605 RTU&Router...xls | - |
| BL16x 交换机 | BLIIoT BL16 Series...xls | - |
| BL21x 分布式IO | 202605 BL21x Series...xls | - |

## 价格层级规则

1. **有Samples列的**: 小于下一层级阈值按Samples价算
2. **没有Samples列的**: 按文档上最低价格层级算
3. **IOy/ARMxy "Online Store & Quotation"** = 样品价
4. **Y板没有Sample价**: Online Store列写 "Refer to <100pcs"
5. **SOM335特殊价**: 文件写$62但实际420 RMB
6. **4G模块价格**: 文件价格 + 30 RMB (按最新汇率换算USD)

## 报价单格式

1. 每行: Model | Unit Price | Qty | Subtotal
2. Total行在底部
3. x1.03 surcharge: surcharge = round(subtotal * 0.03)
4. SOM335特殊价: 420 RMB, 单独标注
5. 含运费/不含运费分开显示

## 汇率查询方法
web_search("CNY to USD exchange rate today")
当前参考: 1 CNY ~ 0.148 USD (2026-06-17)
30 RMB ~ $4.44 USD

## 报价输出示例

```
======================================================================
BLIIoT Quotation -- BA115 Series
Customer: Example | Jakarta, Indonesia
Date: 2026-06-17
======================================================================
----------------------------------------------------------------------
Model                                  Unit Price  Qty   Subtotal
----------------------------------------------------------------------
BA115                                  $      63   12 $     756
BA115L 4G L-E (4G SE Asia)             $     102   12 $    1224
----------------------------------------------------------------------
Subtotal (before 3% surcharge)                         $    9552
3% surcharge                                           $     287
======================================================================
GRAND TOTAL (x1.03)                                 12 $    9839
======================================================================
```

## 常见陷阱

1. BL118B有2个Y板槽，型号里可能出现Y02-Y31这样的双Y板组合
2. ARMxy Y板是双列布局，左边Y01-Y37，右边Y41-Y96
3. BL118 X板和ARMxy X板型号和价格不同
4. SOM335文件价格$62但实际价格420 RMB
5. BA115不在ARMxy文件中，在IIoT Gateways文件的Building HVAC区域
6. 4G模块价格必须加30 RMB
7. M160E在RTU&Mxxx文件，Sample=$157
8. Y37(IEPE测量板)=$970，是异常高价不是打字错误
9. 4G和WiFi互斥
10. 运费不除以N，每个模型独立加
11. 运费也要乘以surcharge
