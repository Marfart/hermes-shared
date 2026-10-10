# sqlmap 核心架构参考 (v33k⭐)

读自 7 个源文件:
- sqlmap.py — 入口/异常体系
- lib/core/agent.py — Agent payload代理
- lib/core/option.py — 选项/XML查询加载
- lib/controller/controller.py — 主控制流程
- lib/controller/checks.py — 注入检测引擎
- lib/request/comparison.py — 页面比较引擎
- lib/techniques/blind/inference.py — 二分盲注

## 7 大核心设计

### 1. Boundary + Payload 分离
- Payload 定义在 xml/payloads/（注入语句本身）
- Boundary 定义在前缀/后缀/位置/WHERE模式
- 两者组合产生数千测试用例
- 加新 bypass = 加一条 XML 记录，不改源码

### 2. Injection Type 分层
checks.py 按 stype 分发:
- PAYLOAD.TECHNIQUE.BOOLEAN — AND/OR 条件真伪判据
- PAYLOAD.TECHNIQUE.ERROR — DBMS错误信息提取
- PAYLOAD.TECHNIQUE.UNION — UNION SELECT注入
- PAYLOAD.TECHNIQUE.TIME — SLEEP() 延迟检测
- PAYLOAD.TECHNIQUE.STACKED — 多语句执行

### 3. 页面比较引擎 (comparison.py)
不是相等比较！流程:
1. removeDynamicContent() — 用正则去掉 csrf_token、nonce、timestamp
2. 可选: --text-only (只比文字), --titles (只比 <title>)
3. SequenceMatcher.ratio() — 0.0 ~ 1.0
4. 阈值: >0.98=TRUE, <0.02=FALSE(可配置)
5. Negative logic: WHERE.NEGATIVE 模式反转比较逻辑
6. heavilyDynamic 模式: 按行分割比（面对动态页面）

### 4. 二分盲注推断 (inference.py)
bisection() 函数:
- ASCII 32~126, 二分法最多 7 次拿一个字符（线性 94 次）
- 多线程并行（多个字符同时二分）
- charset 优先（统计常见字符先猜）
- Good Samaritan: 上一轮猜到的字符类型加速下一轮
- hashDB 缓存部分结果（--repair 可以续猜）
- CHAR_INFERENCE_MARK / INFERENCE_UNKNOWN_CHAR 标记不确定字符

### 5. Agent Payload 代理
agent.py 的 payload() 统一处理:
1. cleanupPayload() — 清理和替换
2. kb.tamperFunctions 循环 — 每个 tamper 修改 payload
3. base64 encoding — 参数原样编码
4. prefix/suffix 拼接 — boundary 前缀后缀
5. 参数定位替换 — 正则找到原始参数位置并替换

### 6. 启发式预检测
先试注入字符 (', ", ), ;) 看页面是否变化。
没变化 = 直接跳过后续所有测试（节省大量时间）
有变化 = 据此选择针对性 payload 集（比如单引号触发用引号闭合payload)

### 7. Tamper 管道
kb.tamperFunctions 列表，每个 tamper 是 payload→payload 函数。
装饰器模式，可任意组合。已有 100+ tamper 脚本：
- space2comment — 空格转注释
- charencode — URL编码
- base64encode — Base64编码
- between — 用注释分割关键字
- 组合: uppercase → space2comment → between

## 控制流程 (controller.py)

```
start()
├── checkConnection()       — 目标可达性
├── checkStability()        — 页面稳定性(多次请求看变化率)
├── checkWaf()              — WAF检测(发恶意payload看被拦截)
├── heuristicCheckSqlInjection() — 快速启发式
├── checkSqlInjection()     — 逐个参数扫描
│   ├── Boolean-based       — 8种boundary × 20+ payloads
│   ├── Error-based         — DBMS错误信息提取
│   ├── Union query         — 列数试探 + 数据注入
│   ├── Time-based          — SLEEP() 延迟检测
│   └── Stacked queries     — 多语句执行
├── _selectInjection()      — 选择最佳注入点
├── _showInjections()       — 展示发现
└── action()                — 数据提取
```

## 异常体系
6种自定义异常，不混用标准 Exception:
- SqlmapBaseException — 基类
- SqlmapConnectionException — 网络连接类
- SqlmapDataException — 数据异常
- SqlmapNoneDataException — 无数据
- SqlmapUserQuitException — 用户中断
- SqlmapSilentQuitException — 静默退出

## 验证脚本
memories/脚本缓存/理解验证/sqlmap_understand.py