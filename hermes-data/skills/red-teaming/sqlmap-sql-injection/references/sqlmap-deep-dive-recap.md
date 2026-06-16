# sqlmap Deep Dive — 实战验证记录

> 2026-06-07, Kali认证：这轮学的就是sqlmap如何工作。

## 装了/跑了什么

- `pip install sqlmap` → 1.10.6
- 搭了本地 Flask + SQLite 漏洞靶场（有 `user?id=1`、`product?id=1`、`search?q=xxx` 三个注入点）
- `curl -G --data-urlencode` 手动验证布尔注入
- `sqlmap -u "http://127.0.0.1:5000/user?id=1" --batch` → 66请求找到3种注入类型，识别SQLite

## 读了什么（源码）

| 文件 | 关键理解 |
|------|---------|
| `data/xml/payloads/boolean_blind.xml` (1612行) | `<test>` 结构：title/stype/level/risk/clause/where/vector/request/payload/comparison |
| `data/xml/boundaries.xml` (576行) | `<boundary>` 结构：level/clause/where/ptype/prefix/suffix |
| `data/xml/payloads/*.xml` | 6种技术类型各有独立XML文件：boolean_blind/error_based/inline_query/stacked_queries/time_blind/union_query |
| `lib/parse/payloads.py` (123行) | `et.parse()` → `AttribDict` 存入 `conf.tests[]` + `conf.boundaries[]` |
| `tamper/equaltolike.py` (40行) | 函数式设计：`__priority__` + `tamper(payload, **kwargs)` |
| `tamper/space2comment.py` (58行) | 空格→注释：跳过引号内的空格，只替换语法空格 |
| `lib/controller/controller.py` | 主流程：start() → checkStability → checkWaf → heuristic → checkSqlInjection → select → action |
| `lib/controller/checks.py` | checkSqlInjection 遍历 tests×boundaries，按stype分路径 |
| `lib/request/comparison.py` | removeDynamicContent + SequenceMatcher.ratio() + threshold + negative logic |
| `lib/techniques/blind/inference.py` | bisection()二分法盲注，全程可见ASCII 32~126 |

## 写了什么（原创验证）

1. **`bliiot_test.py`** — 自定义tamper：`=` → `LIKE`
   - 第一次正则 `(?<=\s)=(\s)` 不对 → 没有空格的空格 `4652=4652` 不匹配
   - 修复 `\s*=\s*` → 148次 LIKE 替换成功
   - 验证：`sqlmap --tamper=bliiot_test -v 5 | grep LIKE` → 148个匹配
   
2. **`bliiot-web-detect.nse`** — nmap NSE脚本
   - 自定义 portrule（匹配5000端口，因为 `shortport.http` 不认自定义端口）
   - http.get → 检查Server头/Werkzeug签名/页面标题
   - 跑通：`server: Werkzeug/3.1.8 Python/3.11.15`
   - 踩坑：`--script-updatedb` 需Program Files写入权限 → 用绝对路径 `--script 路径`

## 核心设计决策（Why）

1. **Boundary + Payload 分离**：加新bypass不用改源码，加XML记录即可。Open/Closed原则。
2. **6种技术独立XML文件**：不同注入策略完全不同，分离保证模块化独立性。
3. **RANDNUM替换**：避免请求缓存/页面缓存影响检测结果（每次请求ID不同）。
4. **页面比较不是 `==`**：SQL注入的True/False是模糊的，需要removeDynamic + SequenceMatcher。
5. **二分法盲注**：ASCII 32~126，7次请求拿一个字符 vs 线性94次 = 13倍提速。
6. **Tamper管道**：装饰器模式，`__priority__` 决定顺序，函数式无状态设计便于组合。

## 还可以读但没读的

- `--os-shell` 实现原理（需要MySQL/Oracle等支持 INTO OUTFILE 的DBMS）
- 不同DBMS的SQL语法适配逻辑
- checks.py主循环中 tests×boundaries 的组合执行细节