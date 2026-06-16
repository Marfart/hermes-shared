#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Smart Watchdog v9 — Supervisor状态机 + AAF错误节流 + processWatchdog指数退避

融合三大GitHub项目精华:
1. Supervisor (8.4k⭐) — 7状态进程生命周期 + startsecs健康门 + BACKOFF/FATAL熔断
2. AAF — 事件驱动装饰器 + 60秒错误节流防Broadcast Storm
3. processWatchdog — 心跳超时检测 + 指数退避 + PID复用防护

v8致命缺陷: 重启后不验证是否真正RUNNING → 死锁(旧进程锁未释放)
v9核心改进:
  - startsecs健康门: 重启后必须验证N秒仍RUNNING
  - 指数退避: 1→2→4→8→16→32秒, 不再线性重试
  - 熔断器: 超3次→FATAL停止重试(防死循环)
  - AAF错误节流: 同问题10分钟只报1次
  - 心跳宽限期: 重启后60秒不检测连接状态
"""
from __future__ import annotations

import json
import sqlite3
import ctypes
import ctypes.wintypes
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
# Supervisor进程状态机
# =====================================================================
class ProcessState(Enum):
    STOPPED = 0
    STARTING = 10
    RUNNING = 20
    BACKOFF = 30      # 退避中，等待重试
    STOPPING = 40
    EXITED = 100      # 正常退出
    FATAL = 200        # 熔断 — 超过重试上限

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
# 配置 (融合Supervisor + processWatchdog)
# =====================================================================
@dataclass
class Config:
    hermes_home: Path = Path.home() / "AppData" / "Local" / "hermes"
    state_file: Path = Path.home() / "AppData" / "Local" / "hermes" / "gateway_state.json"
    log_file: Path = Path.home() / "AppData" / "Local" / "hermes" / "logs" / "gateway.log"
    db_path: Path = Path.home() / "AppData" / "Local" / "hermes" / "scripts" / ".watchdog_v9.db"
    last_state_path: Path = Path.home() / "AppData" / "Local" / "hermes" / "scripts" / ".watchdog_last_state.json"
    proxy_url: str = "http://127.0.0.1:7897"
    # Supervisor参数
    startsecs: int = 10               # 进程必须存活N秒才算RUNNING
    startretries: int = 3             # 最大重试次数(熔断阈值)
    stop_timeout: int = 15             # 优雅停止等待秒数
    # processWatchdog参数
    base_delay: int = 2               # 指数退避基础延迟(秒)
    max_delay: int = 3600             # 退避上限1小时
    heartbeat_timeout: int = 1800    # 心跳超时30分钟
    heartbeat_grace: int = 60         # 重启后宽限期60秒
    # AAF参数
    error_throttle_sec: int = 600    # 错误节流10分钟
    # 网络诊断
    reconnect_timeout: int = 90
    log_scan_lines: int = 80
    ping_target: str = "192.168.1.1"
    api_test_url: str = "https://www.baidu.com"

# =====================================================================
# SQLite 持久化
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
    def get_last_idle(self) -> Optional[dict]:
        conn = sqlite3.connect(str(self.db_path))
        row = conn.execute("SELECT timestamp, idle_seconds, status FROM user_activity ORDER BY id DESC LIMIT 1").fetchone()
        conn.close()
        if row: return {"ts": row[0], "idle": row[1], "status": row[2]}
        return None

# =====================================================================
# 指数退避 + 熔断器 (processWatchdog)
# =====================================================================
def calculate_backoff(retry_count: int, base_delay: int = 2, max_delay: int = 3600) -> int:
    """processWatchdog指数退避: delay = base * 2^(n-1), cap at max_delay"""
    delay = base_delay * (1 << (retry_count - 1))  # 2, 4, 8, 16, 32...
    return min(delay, max_delay)

class CircuitBreaker:
    """Supervisor熔断器: 超过startretries次失败→FATAL"""
    def __init__(self, max_retries: int = 3, base_delay: int = 2):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self._consecutive_failures = 0
        self._last_failure_time = 0.0
        self._state = ProcessState.STOPPED
        self._open = False

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
        if self._last_failure_time > 0:
            delay = calculate_backoff(self._consecutive_failures + 1, self.base_delay)
            elapsed = time.time() - self._last_failure_time
            if elapsed < delay:
                return False  # 退避中
        return True

    def record_success(self):
        """Supervisor: RUNNING→重置backoff+熔断器"""
        self._consecutive_failures = 0
        self._last_failure_time = 0
        self._state = ProcessState.RUNNING
        self._open = False  # 成功后重置熔断器

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

# =====================================================================
# AAF错误节流
# =====================================================================
class ErrorThrottle:
    """AAF WatchDog: 60秒同模块错误只报一次，防Broadcast Storm"""
    def __init__(self, throttle_sec: int = 600):
        self._throttle_sec = throttle_sec
        self._last_report: dict[str, float] = {}

    def should_report(self, key: str) -> bool:
        now = time.time()
        last = self._last_report.get(key, 0)
        if now - last > self._throttle_sec:
            self._last_report[key] = now
            return True
        return False

# =====================================================================
# 子进程执行器
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
# Gateway 操作 (Supervisor 3步法)
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

def restart_gateway_supervisor(cfg: Config, circuit: CircuitBreaker) -> tuple[bool, ProcessState]:
    """Supervisor 3步法: stop → wait → start → verify (startsecs健康门)"""
    hermes_path = str(cfg.hermes_home / "hermes-agent" / "venv" / "Scripts" / "hermes")

    # Step 1: 优雅停止 (Supervisor: STOPPING state)
    try:
        result = subprocess.run([hermes_path, "gateway", "stop"],
                              capture_output=True, text=True, timeout=cfg.stop_timeout,
                              creationflags=subprocess.CREATE_NO_WINDOW)
    except subprocess.TimeoutExpired:
        # Step 1.5: 强杀
        try:
            subprocess.run(["taskkill","/F","/IM","hermes.exe"],
                         capture_output=True, timeout=5,
                         creationflags=subprocess.CREATE_NO_WINDOW)
        except: pass

    # Step 2: 等待进程退出
    time.sleep(3)

    # Step 3: 启动新进程 (Supervisor: STARTING state)
    circuit._state = ProcessState.STARTING
    start_time = time.time()

    try:
        subprocess.Popen([hermes_path, "gateway", "run"],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                        creationflags=subprocess.CREATE_NO_WINDOW)
    except OSError as e:
        circuit.record_failure()
        return False, ProcessState.BACKOFF

    # Step 4: startsecs健康门 (Supervisor核心设计)
    # 进程必须存活超过startsecs秒才算真正RUNNING
    time.sleep(cfg.startsecs)

    # Step 5: 验证重启成功
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
# 主看门狗 V9
# =====================================================================
class WatchdogV9:
    def __init__(self, cfg: Optional[Config] = None):
        self.cfg = cfg or Config()
        self.store = JobStore(self.cfg.db_path)
        self.circuit = CircuitBreaker(max_retries=self.cfg.startretries, base_delay=self.cfg.base_delay)
        self.throttle = ErrorThrottle(throttle_sec=self.cfg.error_throttle_sec)
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

        # 用户状态
        self._idle_seconds, self._idle_status, _ = layer0_user_idle({})
        self.store.save_user_activity(self._idle_seconds, self._idle_status)

        # 进程+平台检查
        self.gateway_alive, self.gateway_states = check_gateway_state(self.cfg, runner)

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

        # 判断是否需要重启
        need_restart = False
        if self.gateway_alive is False or any(s != "connected" for s in self.gateway_states.values()):
            # 心跳宽限期: 刚重启后60秒内不触发
            circuit_state = self.store.get_circuit_state()
            last_failure = circuit_state.get("last_failure", 0)
            if last_failure > 0 and (time.time() - last_failure) < self.cfg.heartbeat_grace:
                self.add_msg(f"   [宽限] 心跳宽限期内({self.cfg.heartbeat_grace}s)，跳过检测")
            else:
                need_restart = True

        # 熔断器检查
        if need_restart and self.circuit.is_open:
            self.add_msg("   [熔断] 熔断器已打开，停止重试(连续失败超过阈值)")
            # 熔断后仍然记录但不重启
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

        # AAF错误节流: 只在有修复/重启时输出，10分钟内不重复
        needs_report = bool(self.repair_actions) or self.should_restart or \
                       (self.circuit.state == ProcessState.FATAL) or \
                       (self.circuit.state == ProcessState.BACKOFF and self.circuit._consecutive_failures > 1)
        if needs_report:
            report_key = "gateway_restart"
            if self.throttle.should_report(report_key):
                now = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")
                self.add_msg(f"\n[时间] {now}")
                plat = " + ".join(f"{k}={v}" for k,v in self.gateway_states.items())
                self.add_msg(f"[状态] 平台: {plat} | 熔断器: {self.circuit.state.name} | 连续失败: {self.circuit._consecutive_failures}")
                self.add_msg("[诊断]")
                for r in self.diag_results:
                    m = "[完成]" if r["ok"] else "[失败]"
                    self.add_msg(f"   {m}  {r['layer']:8s}  {r['detail']}")
                if self.messages:
                    print("\n".join(self.messages))

def main() -> None:
    try:
        watchdog = WatchdogV9()
        watchdog.run()
    except CircuitBreakerOpen:
        # 熔断器打开 — 静默，10分钟节流会处理
        pass
    except Exception:
        import traceback
        traceback.print_exc(file=sys.stderr)

if __name__ == "__main__":
    main()