---
name: telegram-watchdog
description: "Gateway connection watchdog for Telegram, Weixin, Discord — zero-token self-healing with 3-tier repair chain (DNS flush → certifi upgrade → restart). Silent auto-fix for transient issues, rate-limited alerts for persistent failures.

Also covers: Bot-to-bot relay for cross-network communication (see references/bot-relay-setup.md) and Feishu bot-to-bot polling via REST API (see references/feishu-bot-polling.md)."
version: 4.0.0
author: Tachikoma
platforms: [windows, linux, macos]
---

# Gateway Connection Watchdog (Telegram + Weixin + Discord)

跨平台网关连接自愈看门狗 — 零 token 监控，自动修复三级链，静默通知策略。
支持 Telegram / Weixin / Discord 多平台。

## 通知原则
- 🚨 断联原因（一句）+ 🛠 需要多久修好（一句）
- ✅ 修复好了 — "已修复，可以正常连接了"
- 不是问题 → 什么都不发
- 不解释技术细节，不发日志原文
- **不要删掉看门狗脚本** — Kali 明确说过"可以优化但是不要删去"。v6/v7 脚本保留为回退，永不删除。

## 架构 (v9 — Supervisor状态机 + AAF错误节流 + processWatchdog指数退避)

当前活跃：**v10**（2026-06-15 修复/IM连坐Bug，cron job_id=af5f3c06d347）。融合 Supervisor(8.4k⭐)、Healthchecks.io(9k⭐)、Tenacity(6k⭐)、Litestream(13k⭐) 五大项目设计模式。
v9 脚本保留为回退（`smart_watchdog_v9.py`）。

### v10 核心升级：v9全部功能 + Healthchecks.io Grace Period + TokenBucket限流 + Tenacity wait_chain + Litestream优雅关机 + Supervisor时钟回退保护

| # | 模式 | 来源 | 功能 |
|---|------|------|------|
| 1 | **Grace Period缓冲态** | Healthchecks.io | UP→GRACE→DOWN，断开先进120秒缓冲期再判DOWN |
| 2 | **TokenBucket限流** | Healthchecks.io | 容量3+300秒补充1令牌，替代时间窗口限流 |
| 3 | **wait_chain前短后长** | Tenacity | 前3次等30秒后指数退避(60/120/240/480) |
| 4 | **优雅关机** | Litestream | stop→30秒轮询(500ms)→强杀(⚠️修复/IM连坐→/PID精准杀) |
| 5 | **时钟回退保护** | Supervisor | 检测系统时钟回退自动修正 |

### v9 核心升级：Supervisor状态机 + 指数退避 + 熔断器 + startsecs健康门 + AAF错误节流 + 心跳宽限期

v8 致命缺陷：重启后用 `Popen gateway run` 不验证是否真正RUNNING → 旧进程锁未释放 → 新进程秒退 → 死锁2天无人值守。

| # | 模式 | 来源 | v8问题 | v9解决 |
|---|------|------|--------|--------|
| 1 | **startsecs健康门** | Supervisor | 重启后不管是否RUNNING | 进程必须存活N秒才算RUNNING，否则→BACKOFF |
| 2 | **7种状态机** | Supervisor | 只有running/dead | STOPPED→STARTING→RUNNING/BACKOFF→STOPPING→EXITED→FATAL |
| 3 | **指数退避** | processWatchdog | 每2分钟线性重试 | delay=base×2^(retry-1)，2→4→8→16→32秒 |
| 4 | **熔断器** | Supervisor+processWatchdog | 无限重试直到死循环 | 超过3次→FATAL停止重试 |
| 5 | **AAF错误节流** | AAF | 同问题每2分钟轰炸 | 10分钟内同问题只报1次 |
| 6 | **心跳宽限期** | processWatchdog | 重启后立刻检测连接 | 启动后60秒不检测（防误判） |
| 7 | **优雅停止→强杀** | Supervisor+processWatchdog | 只有taskkill | stop→等15秒→SIGKILL→验证 |

### v8 核心升级（保留）：中间件链 + 异常分类 + SQLite 持久化 + Layer 0 用户空闲检测

从 httpx (28k⭐) / APScheduler (7.5k⭐) / FastAPI (80k⭐) 学到的模式直接实装：

**① 中间件链（FastAPI 模式）** — 12 个独立可插拔中间件：
```
MiddlewareChain.run(ctx)
  ├─ 用户状态(Layer 0)  layer0_user_idle    ← 新增：GetLastInputInfo 零成本检测
  ├─ 进程检查           check_gateway_process
  ├─ 平台状态           check_platform_states
  ├─ Layer1 网卡        diag_layer1_nic
  ├─ Layer2 网关        diag_layer2_gateway
  ├─ Layer3 DNS         diag_layer3_dns
  ├─ Layer4 代理        diag_layer4_proxy
  ├─ Layer5 目标        diag_layer5_target
  ├─ Layer6 SSL         diag_layer6_ssl
  ├─ 自动修复           auto_repair
  ├─ 重启网关           restart_gateway_if_needed
  ├─ 等待恢复           wait_for_reconnect
  └─ 生成报告           report_results
```

**新增 Layer 0: 用户空闲检测（Kali 的 3 分钟原则）**
- 用 Windows API `GetLastInputInfo`，零 API 开销
- 阈值 **180 秒（3 分钟）** — Kali 明确说过 30 秒太短（看文章会触发），看文章/读代码的安静时间不算"离开"
- 记录到 SQLite `user_activity` 表，可回溯查询
- **Session 0 保护：** cron 环境下 GetLastInputInfo 读的是系统会话，对比上一条记录。连续两次 idle > 30 分 → 标记 "未知（后台模式）" 而非虚报离开
- 看门狗报故障时带上下文：`已离开 X 分钟，可能是息屏后网络切换导致`
```

**② 异常分类树（httpx 模式）** — 6 种精准异常替代 bare `except Exception`：

**③ SQLite 持久化（APScheduler 模式）** — 3张表（v8是2张，v9新增circuit_breaker表）：
- `incidents` — 事故记录（时间、平台、问题、诊断JSON、修复动作、重启次数）
- `diag_history` — 逐层诊断历史（时间、层级、结果、详情）
- `circuit_breaker` — v9新增：熔断器状态（时间、状态名、连续失败次数、上次失败时间戳）

崩溃恢复、历史可追溯、可查询最近 N 条记录。

### 架构演化路线

```
v4: 428行裸脚本，bare except 11处，print 满天飞
  ↓ 基本功六大原则（Enum/Dataclass/type hints/logging/SRP/retry）
v5: 345行，6个类各司其职
  ↓ 从 yt-dlp/Rich/pydantic 偷师（RetryManager/Protocol/Sentinel）
v6: 进程存活检测优先于状态文件 + SSL修复 + 双通道投递
  ↓ 从 diagnose-network/Windows-Network-Recovery-Toolkit 学诊断
v7: 六层诊断引擎(DiagnosticEngine) + 修复引擎(RepairEngine) + 智能降级
  ↓ 从 httpx/APScheduler/FastAPI 学架构模式
v8: 中间件链架构 + 异常分类树 + SQLite 持久化
  ↓ 从 Supervisor/AAF/processWatchdog 学进程管理
v9: Supervisor状态机 + 指数退避 + 熔断器 + startsecs健康门 + AAF错误节流 👈 当前
```

**v6 的缺陷：** 只检查"进程活着 + 平台状态 + SSL 错误"，网络不通时盲目重启 gateway。

**v7 修复：** 引入 **六层诊断引擎**（`DiagnosticEngine`）+ **修复引擎**（`RepairEngine`）：

```
诊断流程：
  Layer 1: NIC 网卡状态        → netsh interface show interface
  Layer 2: GATEWAY 网关可达     → ping 192.168.1.1
  Layer 3: DNS 解析             → nslookup baidu.com
  #### PROXY 层（Layer 4）— ⚠️ 当前实现危险地不完整
  - **当前行为:** 直接跳过 (`"代理检测跳过（非必需）"`)
  - **致命缺陷:** 在这个环境下代理是**必需**的——所有 Telegram/Weixin HTTPS 都走 `http://127.0.0.1:7897`。跳过检测意味着代理断流（2026-06-04 16:19 确认事件）会被误判为 TARGET 不可达
  - **正确做法:** 用 `curl -x http://127.0.0.1:7897 https://www.baidu.com` 做端到端 HTTPS 转发检测
  - 完整修复方案见 `references/vortex-proxy-disconnect-pattern.md`
  Layer 5: TARGET 目标 API      → curl 目标 URL
  Layer 6: SSL 证书             → 扫描 gateway.log 错误

修复流程（根据诊断结果精准修复）：
  NIC 问题   → Winsock 重置 + TCP/IP 栈修复
  网关问题   → DHCP 续租
  DNS 问题   → flushdns + registerdns
  SSL 问题   → pip install --upgrade certifi + DNS 刷新

智能降级策略：
  Layer 1~3 不通 → 先修复网络，不盲重启 gateway
  Layer 4~5 不通 → 网络正常，重启 gateway
  Layer 6 不通   → 升级 SSL 证书后重启
```

### v6 核心改进：进程存活检测优先于状态文件（v6 保留的特征）

**v6 之前的致命缺陷：** 看门狗只信任 `gateway_state.json` 文件。如果 Gateway 进程已死但状态文件没更新（进程异常退出时大概率发生），看门狗会以为一切正常，全程静默。

**v6 修复：** 加了进程存活检测 `is_gateway_process_alive()`：
1. 从 state 文件读取 PID
2. 用 `tasklist /FI "PID eq X"` 精确检查该 PID 是否还在
3. 如果 PID 不在了 → 立即报警 + 自动重启，不管 state 文件说什么
4. 如果 PID 还在 → 继续读 state 文件判断连接状态

```python
def is_gateway_process_alive(self):
    """检查 Gateway 进程是否真正活着（不只是 state 文件说活着）"""
    raw = self.read_gateway_state()
    if not raw:
        return False
    pid = raw.get("pid")
    if not pid:
        return False
    code, out = self.tools.run(["tasklist", "/FI", f"PID eq {pid}", "/NH"], timeout=10)
    if code != 0:
        return None  # 无法确定
    return str(pid) in out
```

### 三级修复链（执行顺序：先轻后重）

| Level | 操作 | 触发条件 | 通知用户 |
|:-----:|------|:--------:|:-------:|
| 1️⃣ L1 | DNS缓存刷新 `ipconfig /flushdns` | 任何连接异常 | ❌ 静默 |
| 2️⃣ L2 | certifi 更新 `pip install --upgrade certifi` | SSL证书验证失败 | ❌ 静默 |
| 3️⃣ L3 | Gateway 进程重启 | L1+L2无效 | 视Tier而定 |

- 所有修复静默执行，用户无感知
- 只有三级修复链全部失败才可能告警

### 三层诊断 + 智能通知

| Tier | 条件 | 行为 | 通知用户 |
|:----:|------|:---:|:-------:|
| 0️⃣ T0 | 微信限流 `rate limited` | 静默等待恢复 | ❌ 绝不通知 |
| 1️⃣ T1 | 临时网络闪断 / SSL闪断 / 进程退出等 | L1→L2→L3 修复链全自动 | ❌ 静默修复（连续失败≥3次才通知） |
| 2️⃣ T2 | 代理/VPN彻底挂了 / 多次重启仍失败 | 全修复链执行后汇报 | ✅ 每个类型每30分钟最多1次 |

### 单层 cron 监控

```
cron (every 1m) → no_agent=True → smart_watchdog_v4.py
                                                  ↓
                                    读 gateway_state.json
                                  + 扫描 gateway.log 尾部
                                  + 检查代理存活 (7897端口)
                                                  ↓
                            ┌─ L1: DNS刷新 → 恢复? → 静默
                            ├─ L2: certifi升级 → 恢复? → 静默
                            ├─ L3: Gateway重启 → 恢复? → 静默/限频通知
                            └─ 都失败 → T0/T1/T2 通知策略

    状态缓存: .watchdog_status.json (去重 + 计数)
```

- **不依赖守护进程** — cron 永不退出，纯 Python
- **不消耗模型 token** — no_agent=True
- **去重通知** — 同一类型错误30分钟内不重复通知
- **连续重启计数** — 3次以上才升级为T2通知

## 自动修复链

### L1: DNS缓存刷新
**适用场景:** 主机网络闪断（Telegram + Weixin 同时断，但外网正常）
**效果:** 解决约90%的临时网络问题
```python
def flush_dns():
    subprocess.run(["ipconfig", "/flushdns"], capture_output=True, timeout=10)
    time.sleep(1)
```

### L2: SSL证书包更新
**适用场景:** Weixin SSL验证间歇失败（腾讯iLink证书链self-signed错误）
**原因:** `ilinkai.weixin.qq.com` 用DigiCert证书，Windows系统CA包可能落后
**效果:** 升级certifi(Mozilla CA bundle)修复SSL握手
```python
def update_certifi():
    pip = HERMES_HOME / "hermes-agent" / "venv" / "Scripts" / "pip"
    subprocess.run([pip, "install", "--upgrade", "certifi"], capture_output=True, timeout=30)
```

### L3: Gateway重启
```python
hermes_path = str(HERMES_HOME / "hermes-agent" / "venv" / "Scripts" / "hermes")
subprocess.run(["taskkill", "/f", "/im", "hermes"], capture_output=True, timeout=5)
subprocess.Popen([hermes_path, "gateway", "run"],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    creationflags=subprocess.CREATE_NO_WINDOW)
```

⚠️ **关键陷阱（PID存活检测）：** 必须用**绝对路径**（`venv/Scripts/hermes`）启动 Gateway。

⚠️ **关键陷阱（shebang）：** no_agent=True cron 脚本的 shebang 必须用 `#!/usr/bin/env python`，**不是** `python3`。Windows 上没有 `python3` 别名，shebang 指向不存在的解释器 → exit code 3221225794。

⚠️ **关键陷阱（bash 调用 PS1 的中文路径）：** no_agent cron 脚本如果通过 bash 包装器调 PowerShell，不能用 `$USERPROFILE/目录中文/script.ps1`。MSYS 会把 `$USERPROFILE` 转成正斜杠，传给 `powershell.exe -File` 时 DLL 初始化失败（exit code 3221225794）。必须用 **硬编码 Windows 反斜杠路径**。

验证方法：用 `env -i` 模拟 cron 最小环境。
```bash
env -i PATH="/usr/bin:/c/Users/Admin/path/to/python" \
  HOME="/c/Users/Admin" USERPROFILE="C:\\Users\\Admin" \
  python script.py
```
不要用裸 `"hermes"` 命令 — cron 环境和看门狗 no_agent 脚本没有 PATH 上下文，
`hermes` 命令可能不存在或指向错误的 python/虚拟环境。  
Windows 是 `venv/Scripts/hermes`，不是 `venv/bin/hermes`（Linux/Mac 语法在 git-bash 下会失败）。

## Gateway 僵尸进程模式（2026-06-04 首次确认）

Gateway 不是只有"活着"和"死了"两种状态。**僵尸进程**介于两者之间：

| 特征 | 正常 | 僵尸 | 真死 |
|:----:|:----:|:----:|:----:|
| 进程存在 | ✅ | ✅ | ❌ |
| 内存占用 | 100-200MB | ~190MB | N/A |
| state 文件更新 | 每连接/断连更新 | 几小时不更新 | 无文件 |
| 日志输出 | 持续 | 停止在 X 分钟前 | N/A |
| 处理消息 | ✅ | ❌ | N/A |

### 历史案例（2026-06-04）

- PID 30092：进程存活（190MB），但 17:54 后 **78 分钟无日志、无消息处理**
- `gateway_state.json` 中的 PID=16996 已死，但 30092 不在 state 文件中
- 新 Gateway（PID 7792）启动后，30092 仍存活 → **双实例共存**
- Telegram 从用户视角"断连"（发消息无响应），但 state 文件标记为 connected

### 检测方法：心跳时间戳

看门狗不能只检查"进程活着"，**必须检查 state 文件是否在更新**：

```python
def is_gateway_zombie(state_file):
    """如果 state 文件超过 5 分钟没更新 → Gateway 可能僵死"""
    raw = json.loads(state_file.read_text(encoding="utf-8"))
    updated = raw.get("updated_at", "")
    if not updated:
        return False
    ts = datetime.fromisoformat(updated.replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)
    return (now - ts).total_seconds() > 300
```

### 检测方法：日志末行时间戳

```python
def check_log_staleness(log_path, max_idle_seconds=300):
    try:
        return time.time() - log_path.stat().st_mtime > max_idle_seconds
    except FileNotFoundError:
        return True
```

### 检测方法：扫描所有 gateway 实例

```python
def find_all_gateways():
    """列出所有 hermes gateway run 进程 — 有多个说明有问题"""
    r = subprocess.run(
        ['powershell.exe', '-Command',
         "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'gateway run' } | Select-Object ProcessId, @{n='MemMB';e={[math]::Round($_.WorkingSetSize/1MB)}} | Format-Table -AutoSize"],
        capture_output=True, text=True, timeout=10
    )
    return r.stdout
```

### 自动修复

```python
def kill_and_restart_gateway():
    """杀所有 gateway 进程 → 清 state → 重启"""
    for pid in find_gateway_pids():
        subprocess.run(["taskkill", "/F", "/PID", str(pid)], timeout=5)
    Path(state_path).unlink(missing_ok=True)
    subprocess.Popen(
        [hermes_bin, "gateway", "run"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
```

### 连接池超时检测器 (`scripts/pool_timeout_detector.py`)

看门狗v8只检查`gateway_state.json`的平台连接状态和进程存活，**不扫描日志中的连接池超时**。当平台状态仍显示connected但实际无法发送消息时（Vortex代理冻结→Discord重试占满httpx连接池→Telegram也发不出去），v8不会触发重启。

`pool_timeout_detector.py` 填补这个盲区：

- **触发条件：** 最近10分钟内 `Pool timeout: All connections in the connection pool are occupied` 出现≥5次
- **修复动作：** 自动重启 Gateway
- **冷却期：** 300秒防重复触发
- **Cron：** 每3分钟，no_agent=True，deliver=local，job_id=`de31a0c4a9b2`
- **状态文件：** `$HERMES_HOME/scripts/.pool_timeout_state.json`（记录上次重启时间）

**2026-06-13 实战验证：** 22:17起Vortex代理HTTPS转发冻结，导致159次Pool timeout（22:18-22:57），50分钟后看门狗v8才通过状态文件异常触发重启。部署pool_timeout_detector后，下次同类故障将在3分钟内检测到并自动重启。

### v8 看门狗当前缺陷 — 四层缺失检测

`check_gateway_process()` 只检查 state 文件中的 PID 是否存活。如果僵尸进程不在 state 中（或 state 文件 PID 已死但僵尸还在跑），v8 会误判"一切正常"：

1. ✅ state 文件 PID 存活检查（已有）
2. ❌ state 文件 `updated_at` 心跳检查（缺失）
3. ❌ 日志 mtime 检查（缺失）
4. ❌ 重复网关实例检测（缺失）
5. ❌ `restart_requested: true` 假成功检测（缺失）— state 文件标记 `restart_requested: true` 但看门狗没有实际重启（2026-06-15 实战：gateway_state 显示 stopped+restart_requested 但进程不存在，看门狗漏掉）

### Gateway 完全停止的快速诊断流程（2026-06-15 实战验证）

当用户报告 Telegram/微信断联时，按以下顺序快速定位：

1. **查进程** — `tasklist | findstr hermes` 确认 gateway 进程是否存在
2. **查 state 文件** — `cat %LOCALAPPDATA%/hermes/gateway_state.json` 看 `gateway_state` 和各平台状态
3. **查日志尾部** — `tail -30 %LOCALAPPDATA%/hermes/logs/gateway.log` 看最近活动和错误
4. **查 errors.log** — 最近错误，特别是 `Another gateway instance is already running`
5. **重启** — `hermes gateway restart`（杀旧进程+启动新进程）
6. **验证** — 等 10-15 秒后重新查 state 文件确认 `telegram.state: connected`

⚠️ **多个 state 文件陷阱：** 系统中可能存在多个 `gateway_state.json`（`%LOCALAPPDATA%/hermes/`、`Desktop/hermes/`、`Desktop/Working/Hermes/`），只有 `%LOCALAPPDATA%/hermes/gateway_state.json` 是权威的。其他位置的可能是旧的备份同步副本，`updated_at` 可能停在几天前，不要被误导。

⚠️ **restart_requested 不等于已重启：** `gateway_state.json` 中 `restart_requested: true` 只是标记"需要重启"，不代表看门狗已经执行了重启。2026-06-15 实战中，state 显示 stopped+restart_requested 但实际上没有任何 gateway 进程在运行，看门狗漏掉了重启。

### ⚠️ 看门狗重启死锁陷阱（2026-06-15 实战修复）

**根因：** 看门狗之前用 `subprocess.Popen([hermes, "gateway", "run"])` 启动新 Gateway，但没先杀旧进程。旧进程的锁文件/PID文件还在 → 新进程报 "Another gateway instance is already running (PID XXXX)" → 秒退（exit_nonzero）→ 死锁2天无人值守。

**死锁链条：** Discord代理超时 → 看门狗触发重启 → `Popen gateway run` → 新进程撞上旧锁 → 秒退 → Gateway完全停止 → 没有任何自愈机制恢复

**修复：** 改为 `subprocess.run([hermes, "gateway", "restart"], ...)`（它会先杀旧进程再启动新进程）。如果 restart 失败，回退为先 `gateway stop`，等3秒，再 `gateway run`。

```python
# ❌ 死锁写法（旧版）
subprocess.Popen([hermes_path, "gateway", "run"], ...)

# ✅ 正确写法（v8 修复后）
result = subprocess.run([hermes_path, "gateway", "restart"], capture_output=True, text=True, timeout=30, ...)
if result.returncode != 0:
    # 回退：先 stop 再 run
    subprocess.run([hermes_path, "gateway", "stop"], capture_output=True, timeout=15, ...)
    time.sleep(3)
    subprocess.Popen([hermes_path, "gateway", "run"], ...)
```

**验证方法：** `hermes gateway restart` 成功时会输出 `✓ Killed N gateway process(es)` + `✓ Gateway started (PID XXXX)`。如果秒退没有这些输出，说明重启失败。

### ⚠️ `taskkill /F /IM hermes.exe` 连坐陷阱（2026-06-15 实战修复）

**根因：** 看门狗v10的 `graceful_stop()` 函数在 Gateway 重启的"优雅关机"第3步中用 `taskkill /F /IM hermes.exe` 强杀。`/IM` 是按进程**映像名**杀，会把所有 hermes.exe 一起杀掉——包括用户的 CLI 实例、其他 Hermes 会话。

**触发链条：** Gateway连接异常 → 看门狗判定需重启 → `hermes gateway stop` → 等30秒 → 超时 → `taskkill /F /IM hermes.exe` → **所有hermes.exe被杀**

**修复：** 改为从 `gateway_state.json` 读取 Gateway PID → `taskkill /F /PID <gateway_pid>` 精准只杀 Gateway。无PID时才fallback到 `/IM`。

```python
# ❌ 连坐写法（旧版v10）
subprocess.run(["taskkill","/F","/IM","hermes.exe"], ...)

# ✅ 精准杀法（修复后）
gateway_pid = json.loads(state_file.read_text()).get("pid")
if gateway_pid:
    subprocess.run(["taskkill","/F","/PID",str(gateway_pid)], ...)
else:
    # fallback: 无PID信息时才用/IM
    subprocess.run(["taskkill","/F","/IM","hermes.exe"], ...)
```

**铁律：** 任何需要杀 Gateway 的代码，必须用 `/PID` 精准杀，**绝对禁止** `/IM hermes.exe`。用户可能同时跑多个 Hermes CLI 实例，`/IM` 会全部连坐。

### ⚠️ Discord 禁用必须删除 .env 中的 token（2026-06-15 实战）

**根因：** `config.yaml` 中设 `discord: 'null'` 或 `discord.disabled: true` 都不会阻止 Gateway 加载 Discord 平台。只要 `.env` 中有 `DISCORD_BOT_TOKEN`，Gateway 就会尝试连接 Discord，每次30秒超时后重试，指数退避最长300秒。日志满屏 `discord connect timed out after 30s`，还可能耗尽 httpx 连接池。

**正确做法：** 从 `.env` 文件中删除 `DISCORD_BOT_TOKEN` 和 `DISCORD_ALLOWED_USERS` 两行。然后 `hermes gateway restart` 让配置生效。`hermes config set discord.disabled true` 只是加了一个配置项，不影响 Gateway 是否加载 Discord 模块。

**验证：** 重启后 `tail gateway.log` 不应再出现 `Connecting to discord` 或 `Reconnecting discord` 行。`hermes config show` 应显示 `Discord: disabled` 而不是 `Discord: configured`。

---

## Weixin 断联三大根因

| # | 根因 | 日志特征 | 修复 | 频率 |
|:-:|------|----------|:----:|:----:|
| 1 | **主机网络闪断** | `Cannot connect to host ilinkai...:443 ssl:default [None]` + TG同时断 | L1 DNS刷新 | 3-5次/天 |
| 2 | **SSL证书验证间歇失败** | `SSLCertVerificationError: self-signed certificate in certificate chain` | L2 certifi升级 | 1-2次/天 |
| 3 | **Cron突发限流** | `iLink sendmessage rate limited: ret=-2` | T0 静默等待 | Cron时段 |

### 根因4 (最常见)：Vortex mode=direct 配置陷阱

**最危险的代理故障不是"代理挂了"，而是"代理配置静默切换到直连"。**

**根因：** Vortex (Clash) 的 `~/.config/com.vortex.helper/config.yaml` 中 `mode: direct` 会**静默禁用所有代理路由规则**，所有流量直连不走代理。被GFW封锁的域名（api.openai.com、api.telegram.org等）全部连接超时。

**症状：** 所有HTTPS API调用报 `Connection error` / `Retrying in Xs` / `Max retries exhausted`，但代理端口 7897 仍然 LISTENING（`netstat` 显示正常），ping 8.8.8.8 也通。**端口活着≠代理可用**。

**诊断方法：**
1. `grep "^mode:" ~/.config/com.vortex.helper/config.yaml` — 如果是 `direct` 就是根因
2. 对比测试：`curl -x http://127.0.0.1:7897 https://api.openai.com/v1/models` vs `curl --noproxy "*" https://api.openai.com/v1/models`
3. 代理返回超时/连接拒绝 + 直连也超时 = GFW封锁（代理没在转发）

**修复：**
```bash
# 1. 改配置
sed -i 's/^mode: direct/mode: rule/' ~/.config/com.vortex.helper/config.yaml

# 2. 重启Vortex（ShellExecuteW runas提权杀进程，Vortex会自动重启）
# 或者用Vortex API重载（如果external-controller端口可达）：
curl -X PUT http://127.0.0.1:39797/configs -H "Content-Type: application/json" -d '{"path": ""}'

# 3. 验证
curl -s -o /dev/null -w "%{http_code}" -x http://127.0.0.1:7897 https://api.openai.com/v1/models
# 期望: 401(可达) 或 200，不是 000(超时)
```

**跨机器诊断：** 当另一个bot（如小马）报告 `Retrying in Xs` + `API failed after 3 retries — Connection error` 时，先检查本机Vortex的 `mode:` 设置。两台机器共享同一网络环境，根因大概率相同。

### 根因5 (常见)：代理临时失活 — "端口活着但不通"
- **发现方法:** 16:19:32 微信和 Telegram **同一秒掉**，日志均为 SSL connect errors。`curl http://127.0.0.1:7897` 返回 **400**（代理端口侦听），但 `curl -x http://127.0.0.1:7897 https://www.baidu.com` 失败。代理进程（Vortex/com.vortex.helper PID 7724）没死但**不转发 HTTPS 流量**。
- **特征:** 端口开放（netstat 可见 LISTENING），非阻塞，但透过代理的请求全部超时。机器处于背景模式（Session 0/空闲）时更容易触发——可能是代理的 GC 或路由切换。
- **修复:** 看门狗 PROXY 层不能只检查端口是否打开，必须做**端到端代理转发检测**：`curl -s -o NUL -w "%{http_code}" -x http://127.0.0.1:7897 https://www.baidu.com`
- **历史记录:** 2026-06-04 首次确认此模式。当天 16:19 的断联是代理问题，不是网络/DNS/SSL，但旧看门狗（curl /dev/null bug）报告了 30+ 次 ❌ TARGET 假报警，使真实断联被淹没。修复后看门狗应能精准识别此类问题。
- 完整分析见 `references/vortex-proxy-disconnect-pattern.md`

### 根因5：代理冻结 → 连接池耗尽级联故障
- **发现方法:** 2026-06-13 22:17 起 Telegram 出现大量 `Pool timeout: All connections in the connection pool are occupied`，50分钟内 159 次超时。Vortex 代理 HTTPS 转发冻结后，Discord 每 5 分钟重连一次（30s 超时×重试），每次重连占满 httpx 连接池，导致 Telegram 消息也发不出去。
- **特征:** 不是单个平台断连，而是 httpx 连接池被占满后**所有平台都无法发送**。Gateway 进程活着、平台状态可能还显示 connected，但实际消息全部失败。
- **级联路径:** Vortex 冻结 → Discord 重试占满连接池 → Telegram 发送也超时 → 用户 50 分钟完全断联 → 看门狗v8 最终检测到状态异常 → 重启 Gateway 恢复
- **日志特征:** `gateway.log` 中大量 `Pool timeout: All connections in the connection pool are occupied. Request was *not* sent to Telegram` 连续出现，伴随 `discord connect timed out after 30s` 每 5 分钟一次
- **修复:** 新增 `pool_timeout_detector.py`（cron 每 3 分钟，no_agent=True），扫描 gateway.log 最近 10 分钟的 Pool timeout 错误数，≥5 次自动重启 Gateway，冷却期 300 秒防重复触发。cron job_id=`de31a0c4a9b2`，脚本位置 `$HERMES_HOME/scripts/pool_timeout_detector.py`
- **看门狗v8 的盲区:** v8 只检查 `gateway_state.json` 的平台连接状态和进程存活，不扫描日志中的连接池超时。当平台状态仍显示 connected 但实际无法发送时，v8 不会触发重启。pool_timeout_detector 填补了这个盲区。

### Discord 资源浪费陷阱
- Discord 自 2026-06-03 起持续无法连接（`discord connect timed out after 30s`），每日重试 **27+ 次**
- 每次重试：30 秒 try-connect → 失败 → 指数退避（最长 300s）→ 重试。每天浪费约 **13.5 分钟的无意义连接时间**
- Discord 在 gateway 启动时属于"应连平台"（`platforms` 配置中的必连项），所以 gateway 永不放弃重连
- **建议:** 如果用户不用 Discord，从 `platforms` 配置中移除或设为 `enabled: false`，避免 gateway 持续重试拖累整体资源

### 根因1: 主机网络闪断
- 多平台同时断（TG/Weixin/Discord同秒掉），8.8.8.8 ping正常
- 像是Windows DNS/路由瞬时抖动
- **修复:** L1 DNS刷新后重连

### 根因2: SSL证书验证
- TLS连接本身正常（SSL verify关时可连），备用host可达
- **证书链:** iLink 服务器用 `DigiCert Secure Site OV G2 TLS CN RSA4096 SHA256 2022 CA1` 签发，`certifi` Mozilla CA bundle 可能落后于腾讯证书链更新
- **验证方法:** `ssl.create_default_context(cafile=certifi.where())` 失败 → TLS raw connect 成功 → 确认是 CA bundle 过期
- **备用host可绕过:** `novac2c.cdn.weixin.qq.com`, `wx.qlogo.cn` 等不走 iLink 证书链
- **修复:** L2 `pip install --upgrade certifi` 从 Hermes venv 内执行

### 根因3: iLink限流
- 多个cron集中发送触发，`ret=-2` 连续4次backoff后失败
- **修复:** T0 静默等待，无需操作
在 git-bash Python 中，`os.kill(pid, 0)` 抛出的不是 `ProcessLookupError` 而是 `SystemError`，`try/except OSError` 抓不住。必须用 `tasklist` 查 PID：
```python
def is_process_alive(pid):
    r = subprocess.run(["tasklist", "/fi", f"PID eq {pid}", "/nh", "/fo", "csv"],
                       capture_output=True, text=True, timeout=5)
    return str(pid) in r.stdout
```

### `tasklist` 中文输出导致 UnicodeDecodeError
通过 `subprocess.run(capture_output=True, text=True)` 自动转码时崩溃。把 errors='replace' 交给外层，或者在 cron no_agent 模式下只关注 exit code。

### `-o /dev/null` 在 git-bash 下 returncode=23
`curl -s -o /dev/null -w "%{http_code}" url` 在 Windows git-bash 中 HTTP 请求本身成功（返回 200），但 curl 的 exit code 是 **23（Write error）**。因为 `/dev/null` 在 MSYS 里是 fake device，curl 写入它返回写入错误。`SubprocessRunner.run()` 看到 returncode≠0 就抛 `SubprocessFailed`，导致看门狗的 **diag_layer5_target** 永远报告 ❌，即使网络一切正常。

**修复：** 必须用 `-o NUL`（Windows 原生空设备）代替 `-o /dev/null`：
```python
# ❌ 在 git-bash 下 returncode=23：
["curl", "-s", "--connect-timeout", "5", "-o", "/dev/null", "-w", "%{http_code}", url]
# ✅ 正确（Windows 原生）：
["curl", "-s", "--connect-timeout", "5", "-o", "NUL", "-w", "%{http_code}", url]
```
验证方法：Python subprocess.run 跑 curl，看 returncode——`/dev/null` 返回 23（即使 HTTP 200），`NUL` 返回 0。

### `pip list --outdated` 在 cron no_agent 环境下容易超时
`pip list --outdated` 需要联网检查 PyPI，在 cron 的降级网络环境或没有激活代理时经常超时（15s 不够）。这导致 v8 的 **diag_layer6_ssl** 跳过 SSL 检测，留下诊断盲区。

**替代方案：** 用 `curl -sI --connect-timeout 5 https://badssl.com` 或直接 TLS 握手检测（更快、更可靠、不依赖 pip/PyPI）。

### `taskkill /f` 代替 `os.kill(pid, SIGTERM)`
`os.kill` 在 Windows 上映射到 `TerminateProcess`，和 `taskkill /f` 等效。直接用 `taskkill` 更可靠。

完整细节见 `references/weixin-ssl-cert-chain.md`、`references/windows-process-pitfalls.md` 和 `references/curl-devnull-write-error.md`。

### Feishu 守护进程保活 (Windows)

Windows 没有 macOS 的 launchd KeepAlive。守护进程挂了需手动拉起。方案：

1. **wrapper 脚本** — `while True + subprocess.run + sleep(5)` 循环，30秒内连续重启超3次暂停10分钟
2. **Task Scheduler** — 注册开机自启任务
3. **nssm** — 注册成 Windows Service（最稳但最重）

⚠️ `terminal(background=true)` 启动的进程在 Hermes 重启时会被杀掉，没有自动恢复。实测 2026-06-15 守护进程多次崩溃需手动重启。

### feishu_poll_cron.py 语法陷阱

f-string 中的 `\n` 换行符不能跨行拆分。Kali 报告 line 72 `f2.write(m + "\n"` 的 `\n` 被折行导致 SyntaxError。修复：保持转义序列在同一行，或用 `\\n`。

### Bot-to-Bot 通信：轮询 + 本地文件 + 亲自回复

Telegram bot 之间无法直接收到对方消息（安全策略），所以用 HTTP 中继服务器转发。

**通信架构（2026-06-13 Kali 纠正后最终版）：**

```
学弟 ──POST /send──▶ 中继服务器 ◀──GET /poll/小马──▶ 小马(cron写本地文件)
学弟 ◀──GET /poll/学弟── 中继服务器 ◀──POST /send── 小马(亲自curl回复)
```

**三种模式对比（Kali 亲自纠正）：**

| 模式 | 行为 | 问题 |
|:----:|------|------|
| ❌ `no_agent=True` + TG通知 | 轮询→发TG群通知→等小马去看 | 多一层转发，不如直接写本地文件 |
| ❌ `agent模式` cron自动回复 | 轮询→agent思考→自动回复 | Kali原话："你自动回复怎么行呢，要你自己去回复" |
| ✅ `no_agent=True` + 写本地文件 | 轮询→写`xuedi_messages.txt`+删除已读→小马亲自回复 | 最简单，学弟的方案，Kali认可 |

**铁律（2026-06-22 Kali 最终版 v3 — 静默轮询模式）：**

1. **轮询只做搬运，不通知不回复** — cron 每2分钟轮询中继，有消息写本地文件+删除已读，不调agent，**不发任何通知**。Kali原话（2026-06-22）："这个轮询更新别给我发消息了，你自己轮询就好，我来问你你再说"。
2. **学弟方案：轮询→写本地文件→Kali问才汇报** — 不绕TG通知。cron脚本静默运行（无消息=无输出=零打扰），有消息才写文件。Kali来问时再汇报学弟说了什么、回了什么。
3. **⚠️ 静默轮询模式（2026-06-22 Kali 最终指示）** — 正确流程：
   - no_agent cron 每2分钟：轮询中继 → 有消息写 `xuedi_messages.txt` + 删除已读 → **结束，不发通知**
   - Kali 来问 → 读 `xuedi_messages.txt` → 汇报学弟消息 → 思考 → curl POST回复学弟 → 告诉Kali回了什么
   - ❌ 不能发TG通知 — Kali明确禁止："别给我发消息了"
   - ❌ 不能只靠"聊天时顺便查" — Kali原话："如果下次没有及时读到回复，我会来批评你的"
   - ❌ agent cron 自动回复 — Windows 上 `last_status: error` 不稳定，且Kali明确禁止
4. **双方都必须配轮询** — Kali原话："你还要告诉他，要去轮询"。只配一边等于没配。
5. **模型铁律：只能用 ollama-cloud provider 的 deepseek-v4-flash，绝对禁止 gemma4:e2b** — 主模型+11个辅助模型全部设 `provider: ollama-cloud`。⚠️ provider 名字是 `ollama-cloud`（带横杠），不是 `ollama` 也不是 `deepseek`！本会话中搞错了2次，第三次才对。
6. **通信规则：直接通过中继服务器找对方** — 发消息用 `POST /send`，拉取回复用 `GET /poll/{name}`，删已读用 `DELETE /msg/{id}`。
7. **⚠️ to 字段必须精确匹配 bot 注册名（2026-06-13 血泪教训）** — 学弟发消息时 `to:"学长"` 而不是 `to:"小马"`，导致消息堆在 `/poll/学长` 里，小马查 `/poll/小马` 永远为空，白白排查了半小时。排查通信问题时，**必须同时查所有可能的 to 名字**（`/poll/小马` + `/poll/学长` + `/poll/学弟`）。双方必须在接入时统一确认注册名：本端是"小马"，对端是"学弟"，不能用昵称别名。
8. **localhost.run SSH 隧道不稳定** — 学弟自搭的 localhost.run 隧道在断连后返回 `"no tunnel here"`，不如 cloudflared 稳定。统一用 cloudflared 隧道（小马这边），对端只做轮询客户端。
7. **主动问学弟进展** — 不要等学弟发消息才回复。Kali原话："你们两没聊天吗，你要去问学弟进程啊，学的怎么样"。
8. **⚠️ 汇报铁律（2026-06-13 Kali纠正）** — 处理完学弟消息+回复完之后，**必须主动告诉Kali一声**（学弟说了啥、我回了啥）。不能默默处理完就完事，Kali要知情。Kali原话："处理好了，回复完学弟了，要给我说一声"。

当前活跃 cron：`7c35e3b152bf`（每2分钟，no_agent=True，脚本 `poll_xuedi_notify.py`），写本地文件 `%LOCALAPPDATA%/hermes/xuedi_messages.txt`。

### 通信排错优先级（2026-06-13 实战总结）

当学弟说"没收到消息"或小马收不到学弟回复时，按以下顺序排查：

1. **查本地文件优先** — `cat %LOCALAPPDATA%/hermes/xuedi_messages.txt`。轮询脚本已把消息拉走（DELETE）并写入本地文件，中继 `/poll` 和 `/history` 可能都是空的。本地文件才是消息的真实落地位置。
2. **查所有可能的 to 名字** — `/poll/小马` + `/poll/学长` + `/poll/学弟` 全查一遍。名字写错是最高频Bug。
3. **查中继状态** — `/status` 看是否 running，`/history` 看消息流向。
4. **查隧道是否活着** — curl 中继 URL 的 `/status`，如果超时或返回 HTML 错误页，隧道可能断了需要重启。
5. **发一条测试消息验证端到端** — 不要只发不管，发完立刻让对端确认收到。Kali原话："你给他再发个消息看他能不能真的收到再回复你"。

### 文件位置

### 当前活跃脚本
| 角色 | 脚本位置 | Cron ID | 频率 | 模式 | 说明 |
|:----:|----------|:-------:|:----:|:----:|:-----|
| 主看门狗(v10) | `$HERMES_HOME/scripts/smart_watchdog_v10.py` | `af5f3c06d347` | 每2分钟 | no_agent=True | v9+Grace Period+TokenBucket+wait_chain+优雅关机(修复/IM连坐Bug)+时钟回退保护 |
| 连接池超时检测 | `$HERMES_HOME/scripts/pool_timeout_detector.py` | `de31a0c4a9b2` | 每3分钟 | no_agent=True | 扫描gateway.log Pool timeout≥5次→重启Gateway，300s冷却期 |
| 小马轮询学弟 | `$HERMES_HOME/scripts/poll_xuedi_notify.py` | `7c35e3b152bf` | 每2分钟 | no_agent=True | 轮询中继→写`xuedi_messages.txt`+删除已读→小马亲自回复 |
| 回退看门狗(v7) | `$HERMES_HOME/scripts/smart_watchdog_v7.py` | (回退用) | - | no_agent=True | 六层诊断+自动修复引擎 |
| 回退看门狗(v6) | `$HERMES_HOME/scripts/smart_watchdog_v6.py` | (回退用) | - | no_agent=True | 进程存活检测+SSL修复 |
| 桌面卫士 | `$HERMES_HOME/scripts/guard_monitor.sh` | `6882df9f6b5c` | 每2分钟 | no_agent=True |
| 进阶演示 | `$HERMES_HOME/scripts/smart_watchdog_v6_demo.py` | (演示用) | - | RetryManager + Protocol 模式 |

### 状态文件
- `$HERMES_HOME/scripts/.watchdog_status.json` — 去重通知 + 连续重启计数
- `$HERMES_HOME/memories/脚本缓存/weixin_health_state.json` — 深度诊断状态跟踪
- `$HERMES_HOME/logs/gateway.log` — 实时错误扫描源
- `$HERMES_HOME/logs/errors.log` — 完整错误追踪

### 相关参考
- `references/weixin-disconnect-root-causes.md` — 断联根因清单 + 诊断步骤
- `references/vortex-proxy-disconnect-pattern.md` — 2026-06-04 代理断流事件完整分析 + mode=direct配置陷阱诊断流程
- `references/windows-process-pitfalls.md` — Windows 兼容性陷阱
- `references/pythonw-windowless.md` — Windows Python 无控制台窗口模式（pythonw.exe 替换 python.exe 消除小黑窗）
- `references/watchdog-v8-architecture-patterns.md` — httpx/APScheduler/FastAPI 模式在 v8 中的实现
- `references/telegram-group-setup.md` — Telegram 群聊配置：Group Privacy 关闭 + 踢出重新拉入 + chat_id 获取
- `references/gateway-full-stop-diagnosis.md` — Gateway 完全停止快速诊断流程（2026-06-15 实战案例）
- `references/gateway-restart-deadlock.md` — 看门狗重启死锁Bug + Discord .env token陷阱（2026-06-15 修复）