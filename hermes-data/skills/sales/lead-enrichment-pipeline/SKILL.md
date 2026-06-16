---
name: lead-enrichment-pipeline
description: 从LinkedIn X-Ray搜到的人/公司数据，批量增强（官网/邮箱电话/CEO）
---

# Lead Enrichment Pipeline v4

从DDG X-Ray拿到的客户名单，增强企业联系信息。

## 运行方式

```python
from hermes_tools import web_search
import re, json, time
```

**每家公司只搜1个复合query：** `f'"{company}" official website email contact'`

## 缓存 + 清洗策略

1. CACHE FIRST — 预填已知大公司数据，只搜缺失的
2. GOOD_NAMES — 字典匹配已知公司名
3. 每公司只搜1个query（复合搜索），1.2s间隔
4. execute_code 每次最多跑8家（防超时）

## 解析器（单文本提取全部）

```python
def extract(text):
    we = re.search(r'https?://...', text)  # 网站URL
    em = re.findall(r'[\w.+-]+@...', text) # 邮箱（跳过gmail/yahoo）
    ph = re.findall(r'\+27...', text)      # 南非/非洲电话
    ce = re.search(r'CEO...', text)        # CEO姓名
    return we, em, ph, ce
```

## 历史版本对比

| 版本 | 策略 | 21家耗时 | 成功率 |
|---|---|---|---|
| v1 (串行web_search) | 3 query/company ×1.5s | ~95s | 3-5 email |
| v2 (DDGS库直接) | 元搜索引擎 | ❌ 反爬 | 0 |
| v3 (ThreadPool+DDGS) | 并发5线程 | ❌ 反爬 | 0 |
| **v4 (缓存+复合query)** | 预填12家+搜9家×1 query | **<20s** | 5 email+2网站 |

## 关键教训

- 简单>复杂：先缓存再搜，不搞并发膨胀
- 已验证的 `web_search` 比任何新库库都可靠
- 10家需要手动查的小公司 → 直接去它们官网Contact Us页面