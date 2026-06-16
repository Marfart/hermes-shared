# Bug: 硬编码板块缺少详情页（detail-page）

## 发现时间
2026-06-12，用户报告政治安全和太空科学板块点不进去。

## 症状
- 点击政治与安全板块（s4）的卡片、太空与科学板块（s5）的卡片 → 无反应
- 其他板块（通过 `detail_pages` 循环生成的）点击正常
- DevTools 检查发现 `onclick="showDetail('amd')"` 存在，但 DOM 中没有 `id="detail-amd"` 的 `<div>`

## 根因
构建脚本 `build_v7_final.py` 中，**s4 和 s5 板块的 HTML 是硬编码写在模板字符串里的**，不走循环生成逻辑：

```python
# ❌ 问题代码（build_v7_final.py 约 598-604 行）
<div class="sec" id="s4">...
  <div class="sec-card" onclick="showDetail('amd')"><!-- 有 onclick 但无对应 detail-page --></div>
  <div class="sec-card" onclick="showDetail('canada')"><!-- 同上 --></div>
</div>
<div class="sec" id="s5">...
  <div class="sec-card" onclick="showDetail('katalyst')"><!-- 同上 --></div>
  <div class="sec-card" onclick="showDetail('parker')"><!-- 同上 --></div>
</div>
```

而其他板块（story_cards、sec_cards、cult_cards、sci_cards、fund_cards）都是：
1. 在数据数组（`hero_stories`、`secondary`、`cult_stories` 等）中定义数据
2. 用循环生成卡片 HTML（含 `onclick`）
3. 用循环生成详情页 HTML（含 `id="detail-xxx"`）

s4/s5 只做了步骤 2（硬编码卡片），跳过了步骤 3（生成详情页）。

## 修复方案
在 `detail_pages` 拼接完成后、CSS 之前，添加硬编码详情页数据：

```python
hardcoded_details = [
    {
        "id": "amd",
        "tag": "安全",
        "tc": "red",
        "title": "AMD拒绝修复AutoUpdate RCE漏洞",
        "img_key": "amd_vuln",
        "text": """多段文本内容..."""
    },
    # ... canada, katalyst, parker
]

for s in hardcoded_details:
    paragraphs = s["text"].split("\n\n")
    paras_html = "</p>\n        <p style=\"margin-top:16px\">".join(
        p.strip() for p in paragraphs if p.strip())
    detail_pages += f'''
    <div class="detail-page" id="detail-{s["id"]}">
      <div class="detail-hero">
        <img src="{img(s['img_key'])}" alt="{s['title']}">
        ...
      </div>
      <div class="detail-content">
        <div class="detail-section">{paras_html}</div>
        ...
      </div>
    </div>'''
```

## 验证方法
构建 HTML 后，运行：
```python
import re
with open('output.html', 'r') as f:
    html = f.read()
onclick_ids = set(re.findall(r"showDetail\('([^']+)'\)", html))
detail_ids = set(re.findall(r'id="detail-([^"]+)"', html))
missing = onclick_ids - detail_ids
assert not missing, f"Missing detail pages: {missing}"
```

## 预防措施
- 任何时候添加新的 `sec-card` 到模板中，必须同时为它创建 `detail-page`
- 建议将所有板块的数据定义统一到数组（就像其他板块那样），彻底消除硬编码 HTML
- 生成 HTML 后必须跑验证脚本，确保 `onclick` 数量 == `detail-page` 数量
