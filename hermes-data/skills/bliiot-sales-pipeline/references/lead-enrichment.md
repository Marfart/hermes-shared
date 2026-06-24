# Lead Enrichment Pipeline

从LinkedIn搜到的公司，批量增强联系信息。

## 策略: 缓存 + 复合query

1. **CACHE FIRST** — 预填已知大公司数据，只搜缺失的
2. 每公司只搜1个复合query: `"{company}" official website email contact`
3. 1.2s间隔
4. execute_code每次最多跑8家

## 解析器

从单文本提取: URL, 邮箱(跳过gmail/yahoo), 电话, CEO姓名

## 版本对比

| 版本 | 策略 | 耗时 | 成功率 |
|------|------|------|--------|
| v1 串行 | 3 query/company | ~95s | 3-5 email |
| v4 缓存+复合 | 预填+1 query | <20s | 5 email+2网站 |

## 关键教训
- 简单>复杂：先缓存再搜
- web_search比任何新库都可靠
- 10家小公司 → 直接去官网Contact Us
