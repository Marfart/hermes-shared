---
name: chinese-pdf-mastery
description: "英文PDF→中文翻译 — redact+insert原位替换，保留所有截图/布局/文字层。不用像素渲染，不用白块遮盖。在原始PDF上操作"
version: 5.0.0
author: Hermes Agent
license: MIT
platforms: [windows, macos, linux]
trigger: "用户要求将英文PDF翻译为中文并保留所有截图/布局；或任何PDF文本替换任务"
metadata:
  hermes:
    tags: [pdf, translation, chinese, pymupdf, redaction, document-processing]
    related_skills: [ocr-and-documents, playwright-advanced]
---

# 中文PDF翻译 — 实战指南 v5

将**英文PDF翻译为中文**，保留所有截图、图表、颜色、布局，并且中文文字是可选中可复制的。

## 核心方法：redact+insert 原位替换（唯一正确的方法）

```mermaid
flowchart LR
    A[原始PDF] --> B[get_text\"dict\"<br/>提取所有span]
    B --> C[翻译映射表<br/>en→cn dict]
    C --> D[add_redact_annot<br/>标记每段英文]
    D --> E[apply_redactions<br/>真正删除原文]
    E --> F[insert_text<br/>写中文 china-ss]
    F --> G[save garbage=4]
```

### 为什么这是唯一正确的方法

| 方法 | 结果 | 原因 |
|------|------|------|
| ✅ **redact+insert 原位替换** | 完美 | 官方PyMuPDF维护者JorjMcKie推荐。`add_redact_annot`真正删除原文文字层，`insert_text`写入新文字。截图/图表不受影响 |
| ❌ 像素渲染+白块遮盖 | 错误 | draw_rect只在视觉上遮盖，原文文字层还在（可选中）。PDF变成位图不可搜索。文件膨胀至5-10倍 |
| ❌ insert_htmlbox逐span | xref损坏 | 每span调一次insert_htmlbox导致xref索引损坏。坐标匹配脆弱 |
| ❌ 手算坐标redact | 英文残留 | 摘除框永远不准，英文会残留 |

### 标准代码模板

```python
import pymupdf, os

SRC = "input.pdf"
OUT = "output_cn.pdf"

# 翻译映射：按原文精确匹配
T = {
    "TAIS Platform": "TAIS 平台",
    "Transformer Anti-Intrusion System": "变压器防入侵系统",
    # ... 按需扩展，多达数百条
}

doc = pymupdf.open(SRC)

for pn in range(doc.page_count):
    page = doc[pn]
    blocks = page.get_text("dict")["blocks"]
    todo = []
    
    for b in blocks:
        if b["type"] != 0:  # skip images
            continue
        for line in b["lines"]:
            for s in line["spans"]:
                text = s["text"].strip()
                if not text:
                    continue
                cn = T.get(text)
                if cn and cn != text:
                    rect = pymupdf.Rect(s["bbox"])
                    todo.append((rect, cn, s["size"]))
    
    if not todo:
        continue
    
    # 1) 标记所有区域
    for rect, cn, size in todo:
        page.add_redact_annot(rect, fill=(1, 1, 1))
    
    # 2) 执行删除（保留截图）
    page.apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_NONE)
    
    # 3) 写中文
    for rect, cn, size in todo:
        page.insert_text(
            (rect.x0, rect.y1 - 1),  # 基准线在矩形底部
            cn,
            fontname='china-ss',     # 内置CJK字体
            fontsize=size,           # 保持原字号
            color=(0, 0, 0)          # 黑色
        )

doc.save(OUT, garbage=4, deflate=True)
doc.close()
```

### 关键参数

| 参数 | 值 | 说明 |
|------|-----|------|
| `fontname` | `'china-ss'` | PyMuPDF内置CJK无衬线字体，**无需安装**，支持中日韩字符 |
| `images` | `pymupdf.PDF_REDACT_IMAGE_NONE` | **必须**——否则redact会删除所有图片 |
| `fill` | `(1, 1, 1)` | 白底填充被摘除的区域 |
| `color` | `(0, 0, 0)` | 中文文字颜色（黑色） |
| `save` | `garbage=4, deflate=True` | 压缩+清理，文件大小≈原文 |

## 数据组织：翻译映射表

### 方式A：精确文本匹配（推荐）

```python
T = {
    "原文完整的字符串": "中文翻译",
    "另一段原文": "对应的中文",
}
```

**优点**：不需要坐标，不受布局变化影响，可复用。
**缺点**：需要原文和译文完全匹配。PDF有时会把长文本截断（`...`）或跨多个span分割。

### 方式B：原文做key做截断匹配

PDF文本经常被排版引擎截断为近似值。对于这些情况，需要分两轮处理：

```python
# 第一轮：精确匹配
T1 = { "完整英文句": "中文" }

# 第二轮：对第一轮没匹配到的片段手动补
T2 = { "The Overview is the primary command screen. It displays the live national map...": "概览是主要指挥界面。显示全国...", }
```

### 方式C：原文做key做不等长处理

当同一文本有轻微前后空白/标点差异时（例如末尾的`。`），直接包含两种变体在字典中即可。

## `apply_redactions` 图片保留关键

```python
# ❌ 错误——删除了所有图片
page.apply_redactions()

# ✅ 正确——只删除文字，保留图片
page.apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_NONE)
```

如果不加 `PDF_REDACT_IMAGE_NONE`，页面上的所有截图/图表会被**删除**，只剩文字。

## 多轮修复策略

PDF翻译很少一次到位。采用迭代逼近法：

```
第一轮: 所有精确匹配的文本 → 翻译
第二次: 检查输出 → 找出残留英文
第三次: 补查截断文本和变体的精确字符串
```

每次轮次都在上一轮的输出上操作，只修复新的残留。

```python
# 输出文件 → 检查残留 → 补翻译 → 再次输出
T2 = {
    "上一轮残留的精确字符串": "中文翻译",
    # 用 find_untranslated.py 找出这些字符串
}
```

## Pitfalls

### 1. 不要在原文件上 save[→save原文件]
`doc.save(SRC)` 会覆盖原文件，出错了无法恢复。总用临时文件再 rename：

```python
import os
TMP = SRC + ".tmp"
doc.save(TMP, garbage=4, deflate=True)
doc.close()
os.replace(TMP, SRC)
```

### 2. xref warnings 可以忽略
```
MuPDF error: format error: cannot find object in xref (217 0 R)
```
这些是 redact 操作后正常的 xref 清理警告。文件本身是有效的。如果担心，可以 `insert_pdf()` 复制到新文档后再操作。

### 3. `apply_redactions` 增加了图片计数
每次 redact 后 `get_images()` 计数会增加（因为图片被重新编码）。这是正常的——原图还在，只是内部引用号变了。

### 4. 长文本截断问题
PDF排版引擎常常把长文本截断为近似值（不一定是完整字符串）。翻译字典里的 key 如果用了省略号 `...`，就不会匹配到实际 text。要用实际精确字符串来匹配。

**调试方法**：先输出所有残留英文的 `repr()`，再用精确字符串补翻译。

### 5. 数字和专有名词不必翻译
保留：
- 型号和编码：`ZS0035-SS2124`, `02287dfdd811c7c3`
- 公司和品牌：`ZODSAT`, `ZETDC`, `Powertel`
- 权限码：`VIEW_USERS`, `LOCK_USER`
- URL：`https://www.google.com/maps?q=...`
- 版权声明：`Designed & Maintained by...`
- 统计数字：`51,847`, `287`

### 6. 字体限制
- `china-ss` = 内置CJK无衬线字体，类似 SimHei/微软雅黑
- `china-s` = 内置CJK衬线字体，类似 SimSun
- 不支持的 fontname → `Exception: need font file or buffer`
- 自定义字体需要 `page.insert_font(fontfile=path)` 先注册

### 7. 多页文档获取翻译映射
先提取所有页面的文本，一次性生成翻译表，再统一处理：

```python
# 提取
data = {}
for pn in range(doc.page_count):
    page = doc[pn]
    spans = []
    for b in page.get_text("dict")["blocks"]:
        if b["type"] != 0: continue
        for line in b["lines"]:
            for s in line["spans"]:
                text = s["text"].strip()
                if text:
                    spans.append({"text": text, "bbox": s["bbox"], "origin": s["origin"], "size": round(s["size"],1)})
    data[pn] = spans

# 生成所有unique文本
all_texts = set()
for pn, spans in data.items():
    for s in spans:
        all_texts.add(s["text"])

# 翻译unique文本 → 写字典
```

## 验证方法

```python
def verify(doc_path, kept_patterns, excluded=["Designed & Maintained", ...]):
    doc = pymupdf.open(doc_path)
    remaining = []
    for pn in range(doc.page_count):
        for line in doc[pn].get_text().split('\n'):
            l = line.strip()
            if len(l) > 3 and all(c.isascii() for c in l) and any(c.isalpha() for c in l):
                if not any(k in l for k in excluded):
                    remaining.append(f"P{pn+1}| {l[:100]}")
    doc.close()
    print(f"{'✅ ALL TRANSLATED' if not remaining else f'⚠️ {len(remaining)} remaining:'}")
    for r in remaining: print(f"  {r}")
```

## 相关资源

### 第三方工具
- [PDFMathTranslate (pdf2zh)](https://github.com/PDFMathTranslate/PDFMathTranslate) — ⭐34.5k，EMNLP 2025论文，专做科学PDF格式保留翻译。内部使用PyMuPDF+DocLayout-YOLO布局分析。有CLI/GUI/MCP/Docker，支持 `--mcp` 模式直接做MCP服务器
- [BabelDOC](https://babeldoc.com) — pdf2zh使用的实验性后端
- [Stirling PDF](https://github.com/Stirling-Tools/stirling-pdf) — 开源PDF编辑平台（30M+下载）

### 官方文档
- [PyMuPDF Redaction docs](https://pymupdf.readthedocs.io/en/latest/page.html#Page.add_redact_annot)
- [Artifex Blog: Search and Replace Text](https://artifex.com/blog/how-to-search-and-replace-text-in-pdfs-using-pymupdf) — 2025年7月发布的官方教程，展示redact+replace模式
- [PyMuPDF Discussion #3499](https://github.com/pymupdf/PyMuPDF/discussions/3499) — 官方维护者JorjMcKie确认redaction是标准方式
- [PyMuPDF Discussion #3396](https://github.com/pymupdf/PyMuPDF/discussions/3396) — 自定义字体在redact中使用的陷阱

## 筛查列表

- [ ] 使用 `get_text("dict")` 提取span的精确bbox，不要手算坐标
- [ ] 用 `span["bbox"]` 做redact rect，不要手算
- [ ] `apply_redactions(images=PDF_REDACT_IMAGE_NONE)` 保留图片
- [ ] 用 `fontname='china-ss'` 写中文
- [ ] 用 `save(garbage=4, deflate=True)` 压缩输出
- [ ] 先保存到临时文件再 `os.replace` 覆盖
- [ ] 三轮迭代：精确匹配→补残留→补截断文本
- [ ] 检查残留英文，用 `repr()` 获取精确字符串
- [ ] 数字/型号/权限码/公司名故意保留英文