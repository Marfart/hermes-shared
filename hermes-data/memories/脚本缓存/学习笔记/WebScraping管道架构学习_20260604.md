# 🏛️ Web Scraping Architecture — 从3个顶级项目偷师

日期: 2026-06-04
来源: [twscrape (vladkens)](https://github.com/vladkens/twscrape) | [Crawlee (Apify)](https://github.com/apify/crawlee-python) | [hs-net (x-haose)](https://github.com/x-haose/hs-net)

## 1. twscrape (vladkens, 3.9k⭐) — Twitter API Scraper

**架构分解** (3885行/12文件):

```
twscrape/
├── api.py          # 主API入口 (710行) — 统一接口 + 所有endpoint
├── queue_client.py # 队列客户端 (300行) — HTTP会话管理 + 自动账号切换
├── accounts_pool.py # 账号池 (395行) — SQLite持久化 + 限流/加锁
├── db.py           # SQLite异步工具 (156行)
├── models.py       # 数据模型 (903行) — 类型安全+解析器
├── login.py        # 登录流 (279行)
├── xclid.py        # X客户端ID生成 (318行)
├── utils.py        # 工具函数 (370行)
├── account.py      # 账号模型 (75行)
└── cli.py          # CLI入口 (229行)
```

### 学到的关键模式

**① 队列+账号池限流**
```python
# accounts_pool.py — 核心限流逻辑
class AccountsPool:
    async def get_for_queue(self, queue: str):
        # SQLite 记录每个账号每个队列的锁定时间
        # 被限流时锁15分钟，自动换账号
        # 所有账号都用完了 → 等待直到有账号解锁
        
    async def lock_until(self, username, queue, unlock_at):
        # UPDATE accounts SET locks = json_set(...)
        # 用JSON字段记录每个队列的解锁时间戳
```

**② 错误分类体系**
```python
# queue_client.py — 三层异常
class HandledError(Exception): ...   # 可重试（限流、临时错误）
class AbortReqError(Exception): ...  # 不可重试（封号、致命错误）

def _check_rep(self, rep):
    # 精确分类每个错误码：
    # 429 → 限流 → lock_until(reset_time) → 换账号
    # 403 → 封号 → mark_inactive()
    # 404 → 重试(换x-client-transaction-id)
    # (326) → 权限拒绝 → 标记无效
```

**③ async generator 分页**
```python
# api.py — 所有分页统一模式
async def _gql_items(self, op, kv, limit=-1):
    queue, cur, cnt = op.split("/")[-1], None, 0
    while active:
        rep = await client.get(f"{GQL_URL}/{op}", params=params)
        els = self._gql_entries(obj)  # 提取条目
        cur = self._get_cursor(obj)   # 翻页游标
        yield rep
```

---

## 2. Crawlee (Apify, 20k⭐) — 通用爬虫框架

### 学到的关键模式

**① 可插拔爬虫架构**
```
Crawler (abstract base)
├── HttpCrawler        # 纯HTTP
├── PlaywrightCrawler  # 浏览器渲染
├── BeautifulSoupCrawler # 结构化解析
└── ParselCrawler      # CSS/XPath选择器
```

**② Router系统**
```python
router = Router()
@router.default_handler
async def handler(context):
    # context包含 request, response, html, 存储
    pass
    
@router.handler("product")
async def product_handler(context):
    pass  # 按URL模式分派
```

**③ 自动反检测**
- 随机User-Agent/TLS指纹
- 浏览器视口/鼠标轨迹模拟
- 代理轮换池
- 请求间隔自适应

---

## 3. 对我们管道的具体改进

### 问题诊断：为什么之前这么慢？

| 问题 | 根因 | 解决方案 |
|---|---|---|
| `execute_code` 300s超时 | Hermes沙箱限制 | 分批跑，每批 ≤ 8 queries |
| DDGS库狂调10+后端 | ddgs是元搜索引擎，大部分后端被反爬 | 只用 `web_search`（已验证可靠） |
| 每公司3个query | 可以合并为1个复合query | `"{company}" official website email contact` |
| 公司名未清洗就搜索 | 脏数据搜不出结果 | 先用缓存+GOOD_NAMES清洗 |
| 已找到数据重复搜 | 无缓存 | SQLite缓存层 + 预填已知数据 |

### 新管道设计原则

```
Pipeline v4:
  1. CACHE FIRST — 预填已知数据，只搜缺失的
  2. COMPOUND QUERY — 1个query同时找官网+邮箱+CEO+电话
  3. BATCH EXECUTION — execute_code每次跑 ≤8 家
  4. FALLBACK STACK — DDG搜索 → 直接访问官网 → 人工提示
```

### 速度对比

| 版本 | 策略 | 21家耗时 | 成功率 |
|---|---|---|---|
| v1 (串行web_search) | 每公司3个query×1.5s | ~95s** | 3-5 email |
| v2 (DDGS库) | 元搜索引擎10+后端 | 超时+反爬 | 几乎0 |
| v3 (ThreadPool+DDGS) | 并发5线程 | 超时+反爬 | 几乎0 |
| **v4 (缓存+复合query)** | 预填12家+只搜9家×1个query | **<20s** | 5 email+2网站 |

**结论：简单>复杂。先缓存，再精准搜，不搞花架子。**

---

## 文档写作模板（对标顶级项目）

借鉴: twscrape/readme.md, Crawlee/README.md, httpx/README.md

```
# 项目名 — 一句话描述

[![PyPI](badge)] [![License](badge)] [![Downloads](badge)]

## 一句话价值主张
"帮你做X，不用Y，比Z快N倍"

## 快速开始
```python
pip install ... && python -c "..."
``` 30秒内跑通

## 核心概念（有图就有价值）
- 架构图（SVG/Mermaid）
- 数据流图
- 关键术语表

## 功能特性（用emoji分类）
✅ 功能A  — 一句话说明
✅ 功能B  — 一句话说明  
...

## 使用教程（由浅入深）
### 基础
### 进阶
### 高级

## 常见问题
Q: 为什么慢？
A: 因为...

## 贡献指南
- PR流程
- 代码风格
- 测试要求

## License
MIT
```

特点：
1. **1屏内回答 "这是什么"**
2. **30秒可跑通**
3. **问题导向**（不说废话）
4. **Badge信噪比高**（版本、兼容性、下载量）

---

## 记忆的关键

- **先停后想**：速度瓶颈后先诊断（对比v1→v4发现是"并发膨胀"而非"串行太慢"）
- **Copy不是偷**：twscrape的SQLite账号池+错误分类直接可复用
- **文档=销售**：用户的文档不是说明书，是"说服你用它"的销售文案