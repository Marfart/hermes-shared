# Python 高级脚本模式 — 从顶级项目源码精炼

## 1️⃣ httpx (28k⭐) — 传输层抽象 + 异常分类

### 模式 1: 异常分类树
httpx 的 15+ 种精确异常按层级组织：
```
HTTPError
 ├─ RequestError
 │   ├─ TransportError
 │   │   ├─ TimeoutException
 │   │   │   ├─ ConnectTimeout
 │   │   │   ├─ ReadTimeout
 │   │   │   ├─ WriteTimeout
 │   │   │   └─ PoolTimeout
 │   │   ├─ NetworkError (ConnectError/ReadError/WriteError/CloseError)
 │   │   └─ ProtocolError (LocalProtocolError/RemoteProtocolError)
 │   ├─ DecodingError
 │   └─ TooManyRedirects
 └─ HTTPStatusError
```
**实战价值：** 看门狗不再用 `except Exception`，精准捕获每种错误

### 模式 2: 传输层挂载点
```python
mounts = {
    "all://": httpx.HTTPTransport(http2=True),
    "all://*example.org": httpx.HTTPTransport(retries=3),
}
client = httpx.Client(mounts=mounts)
```
**实战价值：** 不同 API provider 不同策略（DeepSeek 用 3 次重试，本地请求 0 次）

### 模式 3: Sentinel / UNSET 模式
```python
class UnsetType: pass
UNSET = UnsetType()

def configure(self, timeout=UNSET):
    if timeout is UNSET:
        timeout = self._default_timeout
```
**实战价值：** 区分「没传参」和「传了 None」，比 `Optional[T]` 更精确

---

## 2️⃣ APScheduler (7.5k⭐) — 插件式调度器

### 模式 4: Trigger / JobStore / Executor 三层分离
```
Scheduler
  ├─ Trigger     ← 何时执行 (IntervalTrigger/CronTrigger/DateTrigger)
  ├─ JobStore    ← 状态持久化 (MemoryJobStore/SQLAlchemyJobStore/MongoDBJobStore)
  └─ Executor    ← 如何执行 (ThreadPoolExecutor/ProcessPoolExecutor/AsyncIOExecutor)
```
**实战价值：** 看门狗可以拆成 Trigger(每2分) + JobStore(持久化状态) + Executor(执行诊断)

### 模式 5: 作业持久化 + 崩溃恢复
```python
jobstore = SQLAlchemyJobStore(url='sqlite:///watchdog.db')
scheduler.add_jobstore(jobstore)
# 重启后自动恢复未完成的作业
```
**实战价值：** 看门狗异常崩溃后重启，能恢复上次的诊断状态

---

## 3️⃣ FastAPI (80k+⭐) — 依赖注入 + 中间件

### 模式 6: 依赖注入容器
```python
class Container:
    _instances = {}
    
    def get(self, key, factory):
        if key not in self._instances:
            self._instances[key] = factory()
        return self._instances[key]

# 用法
container = Container()
diag = container.get("diagnostic_engine", DiagnosticEngine)
repair = container.get("repair_engine", RepairEngine)
```
**实战价值：** 看门狗的各引擎可以懒加载、单例共享、方便测试替换

### 模式 7: 中间件链
```python
class MiddlewareChain:
    def __init__(self):
        self._middlewares = []
    def add(self, fn):
        self._middlewares.append(fn)
    def run(self, ctx):
        result = ctx
        for m in reversed(self._middlewares):
            result = m(result)
        return result

# 看门狗中间件链
chain = MiddlewareChain()
chain.add(log_diagnostics)     # ① 记录诊断
chain.add(cache_check)         # ② 缓存检查（限频）
chain.add(auto_repair)         # ③ 自动修复
chain.add(notify_user)         # ④ 通知用户
```
**实战价值：** 看门狗 v7 的每步可以拆成独立中间件，方便增删改

---

## 应用到小马管道的升级方案

| 现有脚本 | 问题 | 升级模式 | 效果 |
|:---------|:-----|:---------|:-----|
| 看门狗 v7 | 异常处理是 bare `except` | 模式 1: 异常分类树 | 知道是哪层异常 |
| 看门狗 v7 | 状态文件用 JSON | 模式 5: 作业持久化 | 崩溃不丢数据 |
| 编排器 | 角色逻辑混在一起 | 模式 6: 依赖注入 | 可测试、可替换 |
| 所有脚本 | 配置和逻辑耦合 | 模式 3: UNSET Sentinel | 更精确的默认值 |
