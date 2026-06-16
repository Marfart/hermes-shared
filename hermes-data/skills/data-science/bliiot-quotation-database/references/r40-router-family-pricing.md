# R40 / R40A / R40B — 4G LTE 工业路由器价格参考

来源文件：`202605 BLIIOT RTU&Router Price List.xls`，Sheet: `Price List`

## 产品族概述

R40 系列是 BLIIOT 的 4G LTE 工业 VPN 路由器，共三个型号：

| 型号 | 核心差异 | 价格区间 (Sample~≥500pcs) |
|:----|---------|:-----------------------:|
| **R40** | 2DI+2DO, Modbus RTU/TCP Slave | $102~$135 |
| **R40A** | 2DI+2DO, Modbus RTU/TCP **Master** (主站) | $111~$145 |
| **R40B** | 4AI+2DI+2DO, Modbus Master+Slave, **边缘计算** | $150~$200 |

## 区域版本

每个型号都有 5 种区域版本（Col 3 = Version）：

| 版本 | 适用区域 | R40 价格范围 | R40A 价格范围 | R40B 价格范围 |
|:---|:-------|:----------:|:----------:|:----------:|
| **4G (E version)** | 欧洲/通用 | $103~$126 | $111~$136 | $154~$190 |
| **4G (CE version)** | 欧洲 (CE认证) | $100~$122 | $108~$132 | $150~$185 |
| **4G (AU version)** | 澳大利亚 | $107~$131 | $115~$141 | $159~$196 |
| **4G (A version)** | 北美 (AT&T) | $110~$135 | $118~$145 | $163~$200 |
| **4G (J version)** | 日本 | $108~$133 | $117~$144 | $161~$198 |

## 选配件

| 配件 | Model列值 | Sample | <50pcs | ≥50pcs | ≥100pcs | ≥500pcs |
|:---|:---------|:-----:|:------:|:------:|:-------:|:-------:|
| **GPS** | R40/A/B GPS | $3 | $3 | $3 | $3 | $2 |
| **PoE PSE** | R40/A/B PoE | $11 | $9 | $9 | $8 | $8 |

## 文件结构关键点

### 子行模式 (Sub-row Version Pattern)

R40 系列在 Excel 中的布局是 **一个型号 + 多行版本子行**：

```
Row 6:  R40 | [Description...] | [Spec...] | 4G (E version) | 126 | 120 | 114 | 108 | 103
Row 7:  (空) | (空) | (空) | 4G (CE version) | 122 | 116 | 110 | 105 | 100
Row 8:  (空) | (空) | (空) | 4G (AU version) | 131 | 124 | 118 | 112 | 107
Row 9:  (空) | (空) | (空) | 4G (A version)  | 135 | 128 | 122 | 115 | 110
Row 10: (空) | (空) | (空) | 4G (J version)  | 133 | 126 | 120 | 114 | 108
```

- 第一行 (Row 6): 完整的 Model + Desc + Spec + Version + 5个价格
- 后续子行 (Row 7-10): 只有 Version (Col 3) 和价格列有值，Model/Desc/Spec 为空
- **必须继承上一行的 Model 值** 给子行

### 解析代码参考

```python
current_model = None
current_desc = None
for r in range(data_start, data_end):
    model = str(ws.cell_value(r, 0)).strip()
    if model:
        current_model = model  # 新Model行
        current_desc = str(ws.cell_value(r, 1)).strip()
    else:
        model = current_model  # 继承上一行的Model
    
    version = str(ws.cell_value(r, 3)).strip()  # 必填
    # Sample=Col4, <50Pcs=Col5, >50Pcs=Col6, >100Pcs=Col7, >500Pcs=Col8
    prices = [round(float(ws.cell_value(r, c))) for c in range(4, 9)]
```

## 查询示例

用户问 "R40多少钱"：
1. 确定产品线 → RTU & Router
2. 打开 `202605 BLIIOT RTU&Router Price List.xls`
3. 找 R40 行 (Row 6-10)
4. 按版本展示所有子行价格
5. 如果需要：清除 Excel 浮点精度 (round to int)

用户问 "R40A多少钱"：
1. 同文件，找 R40A 行 (Row 11-15)
2. 注意 R40A = Modbus Master，比 R40 贵约 $10
