---
name: resilience-patterns
version: 1.0.0
description: 韧性架构模式 — 从Tenacity/Healthchecks/Litestream/Supervisor四大开源项目提取的7个核心模式
category: devops
---

# 韧性架构模式

从4个顶级开源项目深读源码提取的7个核心韧性模式，全部经过验证代码测试通过。

## 源码项目

| 项目 | Stars | 核心模式 |
|------|-------|----------|
| jd/tenacity | 6k | 策略组合器、wait_chain、外部取消信号 |
| healthchecks/healthchecks | 9k | Flip事件、TokenBucket限流、Grace Period |
| benbjohnson/litestream | 13k | 3层检查点、diagState、优雅关机重试 |
| Supervisor/supervisor | 8.4k | 7状态FSM、startsecs健康门、线性退避 |

## 7个核心模式

### 1. 策略组合器 (Tenacity)
重试策略拆成5个正交维度：stop/wait/retry/before/after，用`__and__`/`__or__`组合。

关键策略：
- `wait_exponential_jitter` — AWS推荐：`2^n + random(0, jitter)`
- `stop_when_event_set` — threading.Event外部取消
- `retry_if_exception_cause_type` — 因果链深度匹配

### 2. TokenBucket限流 (Healthchecks.io)
经典令牌桶：先补充(tokens += elapsed/refill_time)，再消耗(tokens -= 1/capacity)，负数=限流。

### 3. 7状态FSM + startsecs (Supervisor)
状态码不连续(0,10,20,30,40,100,200,1000)，方便区间判断。
- STARTING→RUNNING需要存活超过startsecs
- 太快退出→BACKOFF（线性退避1+n秒）
- BACKOFF超过startretries→FATAL
- 系统时钟回退自动修正

### 4. Flip事件 + Grace Period (Healthchecks.io)
状态变更创建Flip记录（INSERT无锁），异步处理（UPDATE串行化）。
4态：NEW→UP→GRACE→DOWN，GRACE缓冲减少误报。

### 5. 优雅关机重试 (Litestream)
总超时30s + 间隔500ms + ctx.Done可中断。第一次Ctrl+C优雅等待，第二次强制退出。

### 6. 诊断状态机 (Litestream)
diagState记录当前操作(operation/phase/startedAt/updatedAt/walSize/error)，排障时精确知道卡在哪一步。

### 7. wait_chain (Tenacity)
前N次短等，之后长等。比纯指数退避更适合实际场景。

## 对看门狗v9的改进方向

1. **Grace Period缓冲态**：UP→GRACE→DOWN比UP→DOWN减少误报
2. **优雅关机**：SIGTERM + 30秒超时 + 可中断
3. **TokenBucket精确限流**：比时间窗口限流更精确
4. **wait_chain**：前3次等30秒，之后等5分钟
5. **系统时钟回退保护**：Supervisor的`_check_and_adjust_for_system_clock_rollback`

## 验证代码

所有7个模式在 `~/Desktop/Working/resilience_patterns_verification.py` 中验证通过。