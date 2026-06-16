#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Smart Watchdog v10 — 融合5大开源项目韧性模式

v9 → v10 升级:
1. Grace Period缓冲态 (Healthchecks.io) — UP→GRACE→DOWN 减少误报
2. TokenBucket限流 (Healthchecks.io) — 替代时间窗口，更精确
3. wait_chain前短后长 (Tenacity) — 前3次30秒后5分钟，替代纯指数退避
4. 优雅关机重试 (Litestream) — SIGTERM+30秒超时+可中断
5. 时钟回退保护 (Supervisor) — 检测系统时钟回退并修正

零风险改进：不改变重启流程核心，只增加更精确的状态判断。
"""

from __future__ import annotations

import json
import sqlite3
import ctypes
import ctypes.wintypes
import signal
import subprocess
import sys
import io
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from pathlib import Path
from typing import Optional

# ===== Windows cron 编码修复 =====
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='gbk')

# =====================================================================
# Supervisor进程状态机 (v10: 新增GRACE)
# =====================================================================
class ProcessState(Enum):
    STOPPED = 0
    STARTING = 10
    RUNNING = 20
    GRACE = 25         # [v10 NEW] Healthchecks.io Grace Period缓冲态
    BACKOFF = 30       # 退避中，等待重试
    STOPPING = 40
    EXITED = 100       # 正常退出
    FATAL = 200        # 熔断 — 超过重试上限

# =====================================================================
# 平台连接状态 (v10: 新增GRACE)
# =====================================================================
class PlatformHealth(Enum):
    """Healthchecks.io Flip事件模式: NEW → UP → GRACE → DOWN"""
    NEW = auto()       # 首次检测，未知状态
    UP = auto()        # 连接正常
    GRACE = auto()     # [v10 NEW] 缓冲期 — 断开后给N秒恢复窗口
    DOWN = auto()      # 确认断开

# =====================================================================
# 异常分类树
# =====================================================================
class WatchdogError(Exception): pass
class SubprocessError(WatchdogError): pass
class SubprocessTimeout(SubprocessError): pass
class SubprocessFailed(SubprocessError):
    def __init__(self, cmd: list[str], returncode: int, stderr: str):
        self.cmd = cmd; self.returncode = returncode; self.stderr = stderr
        super().__init__(f"cmd={cmd[0]} code={returncode}: {stderr[:80]}")
class ConfigError(WatchdogError): pass
class GatewayError(WatchdogError): pass
class GatewayRestartFailed(GatewayError): pass
class GatewayNotRecovered(GatewayError): pass
class CircuitBreakerOpen(WatchdogError):
    """熔断器已打开 — 超过最大重试次数"""
    pass

# =====================================================================
# 配置 (融合5大项目)
# =====================================================================
@dataclass
class Config:
    hermes_home: Path = Path.home() / "AppData" / "Local" / "hermes"
    state_file: Path = Path.home() / "AppData" / "Local" / "hermes" / "gateway_state.json"
    log_file: Path = Path.home() / "AppData" / "Local" / "hermes" / "logs" / "gateway.log"
    db_path: Path = Path.home() / "AppData" / "Local" / "hermes" / "scripts" / ".watchdog_v10.db"
    last_state_path: Path = Path.home() / "AppData" / "Local" / "hermes" / "scripts" / ".watchdog_last_state.json"
    proxy_url: str = "http://127.0.0.1:7897"
    # Supervisor参数
    startsecs: int = 10               # 进程必须存活N秒才算RUNNING
    startretries: int = 3             # 最大重试次数(熔断阈值)
    stop_timeout: int = 15             # 优雅停止等待秒数
    # [v10 NEW] Healthchecks.io Grace Period
    grace_period: int = 120           # 平台断开后等待120秒才确认DOWN（减少误报）
    # processWatchdog参数
    base_delay: int = 2               # 指数退避基础延迟(秒)
    max_delay: int = 3600             # 退避上限1小时
    heartbeat_timeout: int = 1800    # 心跳超时30分钟
    heartbeat_grace: int = 60         # 重启后宽限期60秒
    # AAF参数
    error_throttle_sec: int = 600    # 错误节流10分钟
    # [v10 NEW] TokenBucket限流
    throttle_capacity: int = 3       # 令牌桶容量（10分钟内最多3次报告）
    throttle_refill_sec: int = 300   # 每300秒补充1个令牌
    # 网络诊断
    reconnect_timeout: int = 90
    log_scan_lines: int = 80
    ping_target: str = "192.168.1.1"
    api_test_url: str = "https://www.baidu.com"

# =====================================================================
# TokenBucket限流 (v10 NEW — Healthchecks.io)
# =====================================================================
class TokenBucket:
    """令牌桶限流 — 比时间窗口更精确平滑
    
    先补充令牌(tokens += elapsed/refill_time)，再消耗。
    负数=限流。比v9的ErrorThrottle更精确：
    - 允许突发（3次快速报告后冷却）
    - 平滑恢复（每5分钟补1个令牌）
    """
    def __init__(self, capacity: int = 3, refill_sec: int = 300):
        self._capacity = capacity
        self._refill_sec = refill_sec
        self._tokens: float = float(capacity)
        self._last_refill: float = time.time()

    def consume(self) -> bool:
        """尝试消耗1个令牌。True=允许，False=限流"""
        now = time.time()
        elapsed = now - self._last_refill
        self._tokens = min(self._capacity, self._tokens + elapsed / self._refill_sec)
        self._last_refill = now
        if self._tokens >= 1.0:
            self._tokens -= 1.0
            return True
        return False

# =====================================================================
# SQLite 持久化 (v10: 新增platform_health表)
# =====================================================================
class JobStore:
    def __init__(self, db_path: Path):
        self.db_path = db_path; self._init_db()
    def _init_db(self):
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("""CREATE TABLE IF NOT EXISTS incidents (
            id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp REAL NOT NULL,
            platform TEXT, problem TEXT, diag_json TEXT, repair_actions TEXT,
            restarts INTEGER DEFAULT 0, resolved INTEGER DEFAULT 0)""")
        conn.execute("""CREATE TABLE IF NOT EXISTS diag_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp REAL NOT NULL,
            layer TEXT NOT NULL, ok INTEGER NOT NULL, detail TEXT)""")
        conn.execute("""CREATE TABLE IF NOT EXISTS circuit_breaker (
            id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp REAL NOT NULL,
            state TEXT NOT NULL, consecutive_failures INTEGER DEFAULT 0,
            last_failure_time REAL DEFAULT 0)""")
        conn.execute("""CREATE TABLE IF NOT EXISTS user_activity (
            id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp REAL NOT NULL,
            idle_seconds INTEGER NOT NULL, status TEXT NOT NULL)""")
        # [v10 NEW] 平台健康状态持久化（Grace Period需要跨检测周期）
        conn.execute("""CREATE TABLE IF NOT EXISTS platform_health (
            platform TEXT PRIMARY KEY, state TEXT NOT NULL,
            changed_at REAL NOT NULL, last_up_at REAL DEFAULT 0)""")
        conn.commit(); conn.close()
    def save_incident(self, platform: str, problem: str, diag: list[dict],
                      repairs: list[str], restarts: int):
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("INSERT INTO incidents (timestamp,platform,problem,diag_json,repair_actions,restarts) VALUES (?,?,?,?,?,?)",
                     (time.time(), platform, problem, json.dumps(diag, ensure_ascii=False),
                      json.dumps(repairs, ensure_ascii=False), restarts))
        conn.commit(); conn.close()
    def save_diag(self, layer: str, ok: bool, detail: str):
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("INSERT INTO diag_history (timestamp,layer,ok,detail) VALUES (?,?,?,?)",
                     (time.time(), layer, 1 if ok else 0, detail))
        conn.commit(); conn.close()
    def save_circuit_state(self, state: str, failures: int, last_failure: float):
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("INSERT INTO circuit_breaker (timestamp,state,consecutive_failures,last_failure_time) VALUES (?,?,?,?)",
                     (time.time(), state, failures, last_failure))
        conn.commit(); conn.close()
    def get_circuit_state(self) -> dict:
        conn = sqlite3.connect(str(self.db_path))
        row = conn.execute("SELECT consecutive_failures, last_failure_time FROM circuit_breaker ORDER BY id DESC LIMIT 1").fetchone()
        conn.close()
        if row: return {"failures": row[0], "last_failure": row[1]}
        return {"failures": 0, "last_failure": 0}
    def save_user_activity(self, idle_seconds: int, status: str):
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("INSERT INTO user_activity (timestamp,idle_seconds,status) VALUES (?,?,?)",
                     (time.time(), idle_seconds, status))
        conn.commit(); conn.close()
    # [v10 NEW] Grace Period需要跨检测周期记忆平台状态
    def get_platform_health(self, platform: str) -> dict:
        conn = sqlite3.connect(str(self.db_path))
        row = conn.execute("SELECT state, changed_at, last_up_at FROM platform_health WHERE platform=?",
                           (platform,)).fetchone()
        conn.close()
        if row: return {"state": row[0], "changed_at": row[1], "last_up_at": row[2]}
        return {"state": "NEW", "changed_at": 0, "last_up_at": 0}
    def save_platform_health(self, platform: str, state: str, last_up_at: float = 0):
        conn = sqlite3.connect(str(self.db_path))
        now = time.time()
        conn.execute("""INSERT OR REPLACE INTO platform_health (platform, state, changed_at, last_up_at)
                        VALUES (?,?,?,?)""", (platform, state, now, last_up_at or now))
        conn.commit(); conn.close()

# =====================================================================
# wait_chain前短后长 (v10 NEW — Tenacity)
# =====================================================================
def calculate_backoff(retry_count: int, base_delay: int = 2, max_delay: int = 3600) -> int:
    """v10: wait_chain模式 — 前3次短等(30秒)，之后指数退避
    
    Tenacity wait_chain: 前N次用短延迟，之后切换到长延迟。
    比纯指数退避更适合实战：刚断时可能快速恢复(短等)，
    反复失败说明问题持续(长等)。
    """
    # [v10] 前3次等30秒，之后指数退避
    if retry_count <= 3:
        return 30  # 前3次: 30秒
    # 第4次起: 60, 120, 240, 480... (2分钟起翻倍)
    delay = 60 * (1 << (retry_count - 4))
    return min(delay, max_delay)

# =====================================================================
# 指数退避 + 熔断器 (processWatchdog + Supervisor)
# =====================================================================
class CircuitBreaker:
    """Supervisor熔断器: 超过startretries次失败→FATAL"""
    def __init__(self, max_retries: int = 3, base_delay: int = 2):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self._consecutive_failures = 0
        self._last_failure_time = 0.0
        self._state = ProcessState.STOPPED
        self._open = False
        # [v10 NEW] 时钟回退保护 (Supervisor)
        self._last_known_time: float = time.time()

    @property
    def state(self) -> ProcessState: return self._state

    @property
    def is_open(self) -> bool: return self._open

    def should_restart(self) -> bool:
        """processWatchdog退避策略: 超过max_retries→熔断"""
        if self._open:
            return False
        if self._consecutive_failures >= self.max_retries:
            self._open = True
            return False
        # [v10 NEW] 时钟回退保护 — 如果当前时间早于上次失败，说明时钟回退了
        now = time.time()
        if now < self._last_failure_time - 1:  # 允许1秒抖动
            self._last_failure_time = now  # 修正为当前时间
        if self._last_failure_time > 0:
            delay = calculate_backoff(self._consecutive_failures + 1, self.base_delay)
            elapsed = now - self._last_failure_time
            if elapsed < delay:
                return False  # 退避中
        return True

    def record_success(self):
        """Supervisor: RUNNING→重置backoff+熔断器"""
        self._consecutive_failures = 0
        self._last_failure_time = 0
        self._state = ProcessState.RUNNING
        self._open = False
        self._last_known_time = time.time()

    def record_failure(self):
        """Supervisor: BACKOFF状态"""
        self._consecutive_failures += 1
        self._last_failure_time = time.time()
        self._state = ProcessState.BACKOFF
        if self._consecutive_failures >= self.max_retries:
            self._state = ProcessState.FATAL
            self._open = True

    def reset(self):
        """手动重置熔断器"""
        self._consecutive_failures = 0
        self._last_failure_time = 0
        self._state = ProcessState.STOPPED
        self._open = False

    def check_clock_rollback(self) -> bool:
        """[v10 NEW] Supervisor时钟回退保护
        
        检测系统时钟是否回退。如果当前时间比上次记录时间早超过5秒，
        说明时钟回退了，需要修正所有时间戳。
        """
        now = time.time()
        if self._last_known_time > 0 and now < self._last_known_time - 5:
            # 时钟回退了！修正时间戳
            rollback_seconds = self._last_known_time - now
            self._last_failure_time = max(0, self._last_failure_time - rollback_seconds)
            self._last_known_time = now
            return True
        self._last_known_time = now
        return False

# =====================================================================
# Grace Period检测器 (v10 NEW — Healthchecks.io)
# =====================================================================
class GracePeriodDetector:
    """Healthchecks.io Flip事件模式: NEW → UP → GRACE → DOWN
    
    核心思想：平台断开时不立即判为DOWN，先进入GRACE缓冲期。
    如果在grace_period秒内恢复，就不触发重启。
    这大幅减少误报——特别是Vortex代理短暂冻结（通常30-60秒恢复）。
    """
    def __init__(self, grace_period: int = 120, store: Optional[JobStore] = None):
        self.grace_period = grace_period
        self._store = store
        self._platform_states: dict[str, PlatformHealth] = {}

    def update(self, platform: str, is_connected: bool) -> PlatformHealth:
        """更新平台状态，返回当前健康状态
        
        Flip事件模式:
        - NEW → UP: 首次检测到连接
        - UP → GRACE: 连接断开，进入缓冲期
        - GRACE → UP: 缓冲期内恢复（误报！）
        - GRACE → DOWN: 缓冲期超时，确认断开
        - DOWN → GRACE: 断开后重新连接（恢复中）
        - GRACE → UP: 恢复确认
        """
        current = self._platform_states.get(platform, PlatformHealth.NEW)
        old_state = current
        
        if is_connected:
            if current in (PlatformHealth.NEW, PlatformHealth.GRACE, PlatformHealth.DOWN):
                current = PlatformHealth.UP
            # UP stays UP
        else:
            if current == PlatformHealth.UP:
                current = PlatformHealth.GRACE  # 不直接DOWN，先进缓冲期
            elif current == PlatformHealth.GRACE:
                # 检查是否超时
                changed_at = self._get_changed_at(platform)
                if changed_at and (time.time() - changed_at) > self.grace_period:
                    current = PlatformHealth.DOWN  # 缓冲期超时→确认DOWN
            elif current == PlatformHealth.NEW:
                current = PlatformHealth.GRACE  # 未知状态断开→先进缓冲期
            # DOWN stays DOWN
        
        self._platform_states[platform] = current
        if current != old_state and self._store:
            self._store.save_platform_health(platform, current.name, 
                                              time.time() if current == PlatformHealth.UP else 0)
        return current

    def _get_changed_at(self, platform: str) -> float:
        """从持久化存储获取状态变更时间"""
        if self._store:
            data = self._store.get_platform_health(platform)
            return data.get("changed_at", 0)
        return 0

    def any_confirmed_down(self) -> bool:
        """是否有任何平台确认DOWN（过了Grace Period）"""
        return any(s == PlatformHealth.DOWN for s in self._platform_states.values())

    def any_in_grace(self) -> bool:
        """是否有任何平台在Grace Period中"""
        return any(s == PlatformHealth.GRACE for s in self._platform_states.values())

# =====================================================================
# 子进程执行器 (v10: 优雅关机)
# =====================================================================
class SubprocessRunner:
    CMD_TIMEOUT = 10; CMD_TIMEOUT_LONG = 30
    @staticmethod
    def run(cmd: list[str], timeout: int = 10) -> tuple[int, str]:
        try:
            _flags = subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, errors="replace",
                               creationflags=_flags)
            if r.returncode != 0: raise SubprocessFailed(cmd, r.returncode, r.stderr[:80])
            return r.returncode, r.stdout.strip()
        except subprocess.TimeoutExpired: raise SubprocessTimeout(f"{cmd[0]} 超时 ({timeout}s)")
        except OSError as e: raise SubprocessError(f"{cmd[0]} 系统错误: {e}")
        except SubprocessFailed: raise
        except Exception as e: raise SubprocessError(f"{cmd[0]} 未知错误: {e}")

# =====================================================================
# 诊断函数
# =====================================================================
IDLE_THRESHOLD = 180

def get_idle_seconds() -> int:
    try:
        last_input = ctypes.wintypes.DWORD()
        ctypes.windll.user32.GetLastInputInfo(ctypes.byref(last_input))
        tick = ctypes.windll.kernel32.GetTickCount()
        return (tick - last_input.value) // 1000
    except: return 0

def layer0_user_idle(ctx: dict) -> tuple[int, str, str]:
    idle = get_idle_seconds()
    if idle < IDLE_THRESHOLD: return idle, "在线", ""
    elif idle < 1800: return idle, f"离开{idle//60}分钟", ""
    else: return idle, f"离开{idle//3600}小时{idle%3600//60}分钟", ""

def diag_layer1_nic(runner: SubprocessRunner) -> dict:
    try:
        _, out = runner.run(["netsh","interface","show","interface"])
        ok = "已连接" in out or "Connected" in out
        return {"layer":"NIC","ok":ok,"detail":"网卡已连接" if ok else "无连接"}
    except SubprocessError as e: return {"layer":"NIC","ok":False,"detail":str(e)}

def diag_layer2_gateway(runner: SubprocessRunner, cfg: Config) -> dict:
    try:
        _, out = runner.run(["ping","-n","1",cfg.ping_target])
        ok = "TTL=" in out
        return {"layer":"GATEWAY","ok":ok,"detail":"网关可达" if ok else "网关不可达"}
    except SubprocessError as e: return {"layer":"GATEWAY","ok":False,"detail":str(e)}

def diag_layer3_dns(runner: SubprocessRunner) -> dict:
    try:
        _, out = runner.run(["nslookup","www.baidu.com"])
        ok = "Address:" in out
        return {"layer":"DNS","ok":ok,"detail":"DNS正常" if ok else "DNS无结果"}
    except SubprocessError as e: return {"layer":"DNS","ok":False,"detail":str(e)}

def diag_layer4_proxy() -> dict:
    return {"layer":"PROXY","ok":True,"detail":"代理检测跳过（非必需）"}

def diag_layer5_target(runner: SubprocessRunner, cfg: Config) -> dict:
    try:
        _, out = runner.run(["curl","-s","--connect-timeout","5","-o","NUL","-w","%{http_code}",cfg.api_test_url], timeout=10)
        ok = out.rstrip() == "200"
        return {"layer":"TARGET","ok":ok,"detail":f"HTTP {out.strip()}" if not ok else "HTTP 200 ✓"}
    except SubprocessFailed as e:
        d = str(e); return {"layer":"TARGET","ok":"200" in d,"detail":d[:60]}
    except SubprocessError as e: return {"layer":"TARGET","ok":False,"detail":str(e)}

def diag_layer6_ssl(runner: SubprocessRunner) -> dict:
    try:
        _, out = runner.run(["curl","-s","--connect-timeout","5","-o","NUL","-w","%{ssl_verify_result}:%{http_code}","https://www.baidu.com"], timeout=8)
        parts = out.strip().split(":")
        ssl_ok = parts[0] == "0" if len(parts) >= 1 else False
        return {"layer":"SSL","ok":ssl_ok,"detail":"证书正常" if ssl_ok else f"证书验证={parts[0]}"}
    except SubprocessError as e: return {"layer":"SSL","ok":False,"detail":f"HTTPS握手失败: {str(e)[:50]}"}

def auto_repair(runner: SubprocessRunner, diag_results: list[dict]) -> list[str]:
    repairs = []
    for r in diag_results:
        if r["ok"]: continue
        if r["layer"] == "NIC":
            try:
                runner.run(["netsh","winsock","reset","category=all"], timeout=10); time.sleep(1)
                runner.run(["netsh","int","ip","reset"], timeout=10)
                repairs.append("[修复] Winsock + TCP/IP 重置完成")
            except SubprocessError as e: repairs.append(f"[错误] 网卡修复失败: {e}")
        elif r["layer"] == "GATEWAY":
            try: runner.run(["ipconfig","/renew"], timeout=15); repairs.append("[修复] DHCP 续租完成")
            except SubprocessError as e: repairs.append(f"[错误] DHCP 续租失败: {e}")
        elif r["layer"] == "DNS":
            try:
                runner.run(["ipconfig","/flushdns"], timeout=10); time.sleep(1)
                runner.run(["ipconfig","/registerdns"], timeout=10)
                repairs.append("[修复] DNS 缓存已刷新")
            except SubprocessError as e: repairs.append(f"[错误] DNS 刷新失败: {e}")
        elif r["layer"] == "SSL":
            try:
                runner.run(["pip","install","--upgrade","certifi"], timeout=30)
                runner.run(["ipconfig","/flushdns"], timeout=10)
                repairs.append("[安全] 证书升级 + DNS 刷新完成")
            except SubprocessError as e: repairs.append(f"[错误] SSL 修复失败: {e}")
    return repairs

# =====================================================================
# Gateway 操作 (v10: 优雅关机 Litestream模式)
# =====================================================================
def check_gateway_state(cfg: Config, runner: SubprocessRunner) -> tuple[Optional[bool], dict[str, str]]:
    """检查Gateway进程和平台状态"""
    gateway_alive = None
    platform_states = {}
    try:
        raw = json.loads(cfg.state_file.read_text(encoding="utf-8"))
        pid = raw.get("pid")
        if pid:
            _, out = runner.run(["tasklist","/FI",f"PID eq {pid}","/NH"])
            pid_exists = str(pid) in out
            updated_at_str = raw.get("updated_at","")
            heartbeat_ok = False
            if updated_at_str:
                try:
                    updated = datetime.fromisoformat(updated_at_str.replace("Z","+00:00"))
                    age = (datetime.now(timezone.utc) - updated).total_seconds()
                    heartbeat_ok = age < cfg.heartbeat_timeout
                except: heartbeat_ok = False
            if not pid_exists:
                gateway_alive = False
            elif not heartbeat_ok:
                gateway_alive = False
            else:
                gateway_alive = True
        else:
            gateway_alive = False
        for name in ("telegram", "weixin"):
            p = raw.get("platforms",{}).get(name,{})
            platform_states[name] = p.get("state","unknown")
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        gateway_alive = None
    return gateway_alive, platform_states

def graceful_stop(cfg: Config, timeout: int = 30) -> bool:
    """[v10 NEW] Litestream优雅关机: SIGTERM → 等待 → SIGKILL
    
    1. 发送 hermes gateway stop（相当于SIGTERM）
    2. 等待进程退出（轮询，每500ms检查一次）
    3. 超时后强杀（SIGKILL）
    4. 可通过 KeyboardInterrupt 提前中断
    """
    hermes_path = str(cfg.hermes_home / "hermes-agent" / "venv" / "Scripts" / "hermes")
    _flags = subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0

    # Step 1: 优雅停止请求
    try:
        subprocess.run([hermes_path, "gateway", "stop"],
                      capture_output=True, timeout=10, creationflags=_flags)
    except (subprocess.TimeoutExpired, OSError):
        pass

    # Step 2: Litestream模式 — 每500ms轮询，总共等timeout秒
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            raw = json.loads(cfg.state_file.read_text(encoding="utf-8"))
            pid = raw.get("pid")
            if not pid:
                return True  # 进程已退出
            _, out = SubprocessRunner.run(["tasklist","/FI",f"PID eq {pid}","/NH"])
            if str(pid) not in out:
                return True  # 进程已退出
        except (FileNotFoundError, json.JSONDecodeError):
            return True  # 状态文件不存在=进程已退出
        except SubprocessError:
            return True
        time.sleep(0.5)  # Litestream: 500ms间隔

    # Step 3: 超时 → 强杀（只杀Gateway PID，不杀其他hermes.exe实例）
    try:
        gateway_pid = None
        try:
            raw = json.loads(cfg.state_file.read_text(encoding="utf-8"))
            gateway_pid = raw.get("pid")
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            pass
        if gateway_pid:
            subprocess.run(["taskkill","/F","/PID",str(gateway_pid)],
                         capture_output=True, timeout=5, creationflags=_flags)
        else:
            # fallback: 无PID信息时才用/IM，但记录警告
            subprocess.run(["taskkill","/F","/IM","hermes.exe"],
                         capture_output=True, timeout=5, creationflags=_flags)
    except: pass
    return False

def restart_gateway_supervisor(cfg: Config, circuit: CircuitBreaker) -> tuple[bool, ProcessState]:
    """Supervisor 3步法 + v10优雅关机 + startsecs健康门"""
    # [v10] Step 1: 优雅关机（Litestream模式：30秒超时+500ms轮询）
    graceful_stop(cfg, timeout=cfg.stop_timeout)
    time.sleep(3)

    # Step 2: 启动新进程 (Supervisor: STARTING state)
    hermes_path = str(cfg.hermes_home / "hermes-agent" / "venv" / "Scripts" / "hermes")
    circuit._state = ProcessState.STARTING
    start_time = time.time()

    try:
        _flags = subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
        subprocess.Popen([hermes_path, "gateway", "run"],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                        creationflags=_flags)
    except OSError as e:
        circuit.record_failure()
        return False, ProcessState.BACKOFF

    # Step 3: startsecs健康门 (Supervisor核心设计)
    time.sleep(cfg.startsecs)

    # Step 4: 验证重启成功
    runner = SubprocessRunner()
    for attempt in range(3):
        try:
            raw = json.loads(cfg.state_file.read_text(encoding="utf-8"))
            tg = raw.get("platforms",{}).get("telegram",{}).get("state","")
            wx = raw.get("platforms",{}).get("weixin",{}).get("state","")
            if tg == "connected" and wx == "connected":
                circuit.record_success()
                return True, ProcessState.RUNNING
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        time.sleep(5)

    # startsecs健康门未通过 → BACKOFF
    circuit.record_failure()
    return False, ProcessState.BACKOFF

# =====================================================================
# 主看门狗 V10
# =====================================================================
class WatchdogV10:
    def __init__(self, cfg: Optional[Config] = None):
        self.cfg = cfg or Config()
        self.store = JobStore(self.cfg.db_path)
        self.circuit = CircuitBreaker(max_retries=self.cfg.startretries, base_delay=self.cfg.base_delay)
        self.throttle = TokenBucket(capacity=self.cfg.throttle_capacity, refill_sec=self.cfg.throttle_refill_sec)
        self.grace = GracePeriodDetector(grace_period=self.cfg.grace_period, store=self.store)
        self.messages: list[str] = []
        self.diag_results: list[dict] = []
        self.gateway_states: dict[str, str] = {}
        self.gateway_alive: Optional[bool] = None
        self.should_restart = False
        self.repair_actions: list[str] = []
        self._idle_seconds = 0
        self._idle_status = ""

    def add_msg(self, msg: str): self.messages.append(msg)

    def run(self):
        runner = SubprocessRunner()

        # [v10] 时钟回退保护
        if self.circuit.check_clock_rollback():
            self.add_msg("   [保护] 检测到系统时钟回退，已修正时间戳")

        # 用户状态
        self._idle_seconds, self._idle_status, _ = layer0_user_idle({})
        self.store.save_user_activity(self._idle_seconds, self._idle_status)

        # 进程+平台检查
        self.gateway_alive, self.gateway_states = check_gateway_state(self.cfg, runner)

        # [v10] Grace Period检测 — UP→GRACE→DOWN模式
        for platform, state in self.gateway_states.items():
            is_connected = (state == "connected")
            health = self.grace.update(platform, is_connected)
            if health == PlatformHealth.GRACE:
                self.add_msg(f"   [缓冲] {platform} 进入Grace Period ({self.cfg.grace_period}s)")
            elif health == PlatformHealth.DOWN:
                self.add_msg(f"   [确认] {platform} 确认断开 (Grace Period超时)")

        # 六层网络诊断
        self.diag_results = [
            diag_layer1_nic(runner),
            diag_layer2_gateway(runner, self.cfg),
            diag_layer3_dns(runner),
            diag_layer4_proxy(),
            diag_layer5_target(runner, self.cfg),
            diag_layer6_ssl(runner),
        ]

        # 自动修复
        self.repair_actions = auto_repair(runner, self.diag_results)

        # 判断是否需要重启 — [v10] 只有确认DOWN才重启，GRACE不重启
        need_restart = False
        if self.gateway_alive is False or self.grace.any_confirmed_down():
            # 心跳宽限期: 刚重启后60秒内不触发
            circuit_state = self.store.get_circuit_state()
            last_failure = circuit_state.get("last_failure", 0)
            if last_failure > 0 and (time.time() - last_failure) < self.cfg.heartbeat_grace:
                self.add_msg(f"   [宽限] 心跳宽限期内({self.cfg.heartbeat_grace}s)，跳过检测")
            else:
                need_restart = True
        elif self.grace.any_in_grace():
            # [v10] 在Grace Period中 — 不重启，等待恢复或超时
            self.add_msg(f"   [缓冲] 平台在Grace Period中，等待恢复或超时")

        # 熔断器检查
        if need_restart and self.circuit.is_open:
            self.add_msg("   [熔断] 熔断器已打开，停止重试(连续失败超过阈值)")
            self.store.save_incident(
                platform="+".join(k for k,s in self.gateway_states.items() if s != "connected"),
                problem=f"熔断器打开(连续{self.circuit.max_retries}次失败)",
                diag=self.diag_results, repairs=[], restarts=0)
        elif need_restart and self.circuit.should_restart():
            # Supervisor 3步法重启
            self.add_msg(f"   [重启] Supervisor 3步法重启 (第{self.circuit._consecutive_failures + 1}次)...")
            success, new_state = restart_gateway_supervisor(self.cfg, self.circuit)
            if success:
                self.add_msg("   [完成] Gateway 重启成功 — startsecs健康门通过")
                self.should_restart = True
                # 等待恢复
                deadline = time.time() + self.cfg.reconnect_timeout
                while time.time() < deadline:
                    try:
                        raw = json.loads(self.cfg.state_file.read_text(encoding="utf-8"))
                        tg = raw.get("platforms",{}).get("telegram",{}).get("state","")
                        wx = raw.get("platforms",{}).get("weixin",{}).get("state","")
                        if tg == "connected" and wx == "connected":
                            self.add_msg(f"   [恢复] Telegram {tg}, 微信 {wx}")
                            break
                    except: pass
                    time.sleep(3)
            else:
                backoff = calculate_backoff(self.circuit._consecutive_failures, self.cfg.base_delay)
                self.add_msg(f"   [退避] 重启失败，进入BACKOFF (下次重试至少{backoff}s后)")
        elif need_restart:
            # 退避中，不重启
            backoff = calculate_backoff(self.circuit._consecutive_failures + 1, self.cfg.base_delay)
            elapsed = time.time() - (self.circuit._last_failure_time or 0)
            remaining = max(0, backoff - elapsed)
            self.add_msg(f"   [退避] 退避中，还需等待{remaining:.0f}s")

        # 保存熔断器状态
        self.store.save_circuit_state(
            self.circuit.state.name,
            self.circuit._consecutive_failures,
            self.circuit._last_failure_time)

        # 记录事件
        problems = [k for k,s in self.gateway_states.items() if s != "connected"]
        if problems or self.should_restart:
            self.store.save_incident(
                platform="+".join(problems),
                problem=str(f"状态={self.circuit.state.name}"),
                diag=self.diag_results,
                repairs=self.repair_actions,
                restarts=1 if self.should_restart else 0)

        # [v10] TokenBucket限流: 替代旧的ErrorThrottle
        needs_report = bool(self.repair_actions) or self.should_restart or \
                       (self.circuit.state == ProcessState.FATAL) or \
                       (self.circuit.state == ProcessState.BACKOFF and self.circuit._consecutive_failures > 1) or \
                       self.grace.any_confirmed_down()
        if needs_report and self.throttle.consume():
            now = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")
            self.add_msg(f"\n[时间] {now}")
            plat = " + ".join(f"{k}={v}" for k,v in self.gateway_states.items())
            # [v10] 显示Grace Period状态
            grace_info = ""
            for platform in self.gateway_states:
                health = self.grace._platform_states.get(platform, PlatformHealth.NEW)
                grace_info += f" {platform}={health.name}"
            self.add_msg(f"[状态] 平台: {plat} | 熔断器: {self.circuit.state.name} | 连续失败: {self.circuit._consecutive_failures}")
            self.add_msg(f"[Grace] {grace_info.strip()}")
            self.add_msg("[诊断]")
            for r in self.diag_results:
                m = "[完成]" if r["ok"] else "[失败]"
                self.add_msg(f"   {m}  {r['layer']:8s}  {r['detail']}")
            if self.messages:
                print("\n".join(self.messages))

def main() -> None:
    try:
        watchdog = WatchdogV10()
        watchdog.run()
    except CircuitBreakerOpen:
        # 熔断器打开 — 静默，TokenBucket会处理
        pass
    except Exception:
        import traceback
        traceback.print_exc(file=sys.stderr)

if __name__ == "__main__":
    main()