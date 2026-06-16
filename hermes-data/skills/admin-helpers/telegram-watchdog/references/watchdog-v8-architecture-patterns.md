# Watchdog v8 Architecture — Patterns from httpx / APScheduler / FastAPI

## 1️⃣ httpx (28k⭐) — 异常分类树

httpx 定义了 **15+ 种精准异常**，按层级组织：

```
HTTPError
 ├─ RequestError
 │   ├─ TransportError
 │   │   ├─ TimeoutException (Connect/Read/Write/PoolTimeout)
 │   │   ├─ NetworkError (Connect/Read/Write/CloseError)
 │   │   └─ ProtocolError (Local/RemoteProtocolError)
 │   ├─ DecodingError
 │   └─ TooManyRedirects
 └─ HTTPStatusError
```

**v8 实现：** `WatchdogError → SubprocessError(SubprocessTimeout/SubprocessFailed) → ConfigError → GatewayError(GatewayRestartFailed/GatewayNotRecovered)`

**关键设计：** `map_httpcore_exceptions()` 函数将底层 `httpcore` 异常映射到 `httpx` 异常层，做到内部底层库和外部 API 的异常隔离。v8 同理：子进程调用抛 `SubprocessError` → 上层中间件捕获转 `GatewayError`。

## 2️⃣ APScheduler (7.5k⭐) — SQLite 持久化

APScheduler 的 `JobStore` 抽象层让调度器可以跨重启恢复状态：
- `MemoryJobStore` — 进程内，重启丢失
- `SQLAlchemyJobStore` — SQLite/PostgreSQL 持久化，重启恢复

**v8 实现：** `JobStore(db_path)` 管理 2 张 SQLite 表：
- `incidents` — id/timestamp/platform/problem/diag_json/repair_actions/restarts/resolved
- `diag_history` — id/timestamp/layer/ok/detail

**核心代码：**
```python
conn.execute("""
    CREATE TABLE IF NOT EXISTS incidents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp REAL NOT NULL,
        platform TEXT,
        problem TEXT,
        diag_json TEXT,
        repair_actions TEXT,
        restarts INTEGER DEFAULT 0,
        resolved INTEGER DEFAULT 0
    )
""")
```

## 3️⃣ FastAPI (80k⭐) — 中间件链

FastAPI 的中间件系统本质是 **「请求→中间件链→路由→中间件链→响应」** 的洋葱模型。每个中间件决定继续或短路。

**v8 实现：** `MiddlewareChain` + `WatchdogContext`：
```python
class MiddlewareChain:
    def add(self, name: str, fn: Callable[[WatchdogContext], None]):
        self._middlewares.append((name, fn))

    def run(self, ctx) -> WatchdogContext:
        for name, fn in self._middlewares:
            if ctx.error:
                ctx.add_msg(f"   ⛔ {name} 跳过（上游错误）")
                continue
            try:
                fn(ctx)
            except WatchdogError as e:
                ctx.error = e
                ctx.add_msg(f"   ❌ {name}: {e}")
        return ctx
```

**关键设计：** `WatchdogContext` 是贯穿整个链的上下文对象，类似 FastAPI 的 `Request` 对象。所有中间件共享同一个 ctx，读/写诊断结果、修复动作、消息输出。

**优点：**
- 新增/删除/重排中间件只需改 `_build_chain()` 一行
- 每步独立，互不干扰
- 上游中间件失败自动跳过下游
- 可独立测试每个中间件

## 架构演化对照

| 版本 | 行数 | 类数 | 异常类型 | 持久化 | 架构模式 |
|:----|:----:|:----:|:--------:|:------|:---------|
| v4 | 428 | 0 | bare except 11处 | 无 | 裸脚本 |
| v5 | 345 | 6 | 精准捕获 | JSON文件 | 类结构 |
| v6 | 436 | 6+ | 精准捕获 | JSON文件 | +进程检测 |
| v7 | 639 | 2引擎 | 精准捕获 | JSON文件 | 分层诊断 |
| v8 | 580 | 3引擎+链 | 6种精准异常 | **SQLite** | 中间件链 |

## 参考文件
- `smart_watchdog_v8.py` — 当前活跃脚本
- `smart_watchdog_v7.py` — 回退脚本
- `python-script-craftsmanship` skill — 所有模式的详细文档
