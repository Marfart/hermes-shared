---
name: script-writing-tutorial
description: "Python 脚本实战教程 — 从0到能写自动化脚本/爬虫/数据处理"
version: 1.0.0
author: Tachikoma
platforms: [windows]
---

# Python 脚本实战教程 🐾

## 课程结构（5关）

| 关卡 | 主题 | 产出 |
|:---:|------|------|
| 1️⃣ | **你好，脚本世界** | 写第一个.py文件 + 运行它 |
| 2️⃣ | **变量与数据** | 处理Excel/CSV数据，理解类型 |
| 3️⃣ | **条件与循环** | 批量处理文件，自动判断逻辑 |
| 4️⃣ | **读写文件** | 读报价单、写报告、操作JSON |
| 5️⃣ | **实战：你的第一个自动化脚本** | 完整的BLIIOT小工具 |

## 教学方法

- **先看 → 再改 → 再写**：每关先展示一个完整可运行的脚本
- **直接在桌面试**：所有脚本写在 `C:\Users\Admin\Desktop\脚本学习\` 下
- **改一个参数看效果**：理解每一行在干嘛
- **10分钟内能跑通**：不搞复杂理论

## 第1关：你好，脚本世界！

```python
# hello.py — 你的第一个脚本！
print("你好，Kali！🎉")
print("这是我的第一个 Python 脚本！")

# 算个数给你看
price = 128
quantity = 5
total = price * quantity
print(f"总价: {price} × {quantity} = {total} 元")
```

**怎么运行：**
```bash
python C:\Users\Admin\Desktop\脚本学习\hello.py
```

## 第2关：变量与数据类型

```python
# data_types.py — 看看Python能处理什么数据
name = "BLIIOT"              # 字符串（文字）
year = 2026                  # 整数
price = 128.50               # 浮点数（小数）
is_active = True             # 布尔值（真/假）
products = ["ARMxy", "IOy", "EdgePLC"]  # 列表（多个值）

print(f"公司: {name}")
print(f"年份: {year}")
print(f"价格: {price}")
print(f"激活: {is_active}")
print(f"产品线: {products}")
print(f"第一个产品: {products[0]}")  # 索引从0开始
```

## 第3关：条件与循环

```python
# conditions.py — 让脚本学会判断和重复
customers = [
    {"name": "公司A", "country": "South Africa", "score": 8},
    {"name": "公司B", "country": "Nigeria", "score": 5},
    {"name": "公司C", "country": "Kenya", "score": 3},
]

print("=== 高潜力客户 ===")
for c in customers:
    if c["score"] >= 7:
        print(f"✅ {c['name']} ({c['country']}) — 高分客户！")
    elif c["score"] >= 4:
        print(f"⚠️ {c['name']} ({c['country']}) — 中等潜力")
    else:
        print(f"❌ {c['name']} ({c['country']}) — 低分，暂不跟进")
```

## 第4关：读写文件

```python
# file_ops.py — 读写文件实战
import json

# 读 JSON 文件
with open("customers.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# 筛选 + 写结果
high_value = [c for c in data if c.get("score", 0) >= 7]
with open("high_value_customers.json", "w", encoding="utf-8") as f:
    json.dump(high_value, f, indent=2, ensure_ascii=False)

print(f"读取了 {len(data)} 个客户")
print(f"筛选出 {len(high_value)} 个高价值客户")
```

## 第5关：实战 — 报价单价格计算器

```python
# quote_calculator.py — 模拟BLIIOT报价计算
def calculate_price(base_price, quantity, discount_pct=0):
    """计算最终价格"""
    subtotal = base_price * quantity
    discount = subtotal * (discount_pct / 100)
    total = subtotal - discount
    return round(total)

# 产品目录
products = {
    "ARMxy": {"base": 150, "desc": "ARM边缘控制器"},
    "IOy":   {"base": 85,  "desc": "远程I/O模块"},
    "BL116": {"base": 120, "desc": "工业网关"},
}

print("=" * 40)
print("BLIIOT 报价计算器")
print("=" * 40)

for code, info in products.items():
    total = calculate_price(info["base"], 10, 5)  # 10台×95折
    print(f"{code} ({info['desc']}):")
    print(f"  单价: ${info['base']}  → 10台折后: ${total}")
    print()

# 用户输入版本
print("--- 自定义报价 ---")
qty = int(input("数量: "))
disc = float(input("折扣(%): "))
for code, info in products.items():
    t = calculate_price(info["base"], qty, disc)
    print(f"{code}: ${t}")
```

## 学习路径指示

每关学完后说"学完了第N关，继续"，小马会：
1. ✅ 检查你写的脚本能否运行
2. ⭐ 给你布置一个小改动任务
3. 📖 解释你遇到的报错
4. 🚀 进入下一关