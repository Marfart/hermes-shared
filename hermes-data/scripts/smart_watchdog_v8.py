#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Smart Watchdog v8 — 中间件架构 + 异常分类 + SQLite 持久化"""
from __future__ import annotations

import json
import logging
import sqlite3
import ctypes
import ctypes.wintypes
import subprocess
import sys
import io
import time
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from enum import Enum, auto
from pathlib import Path
from typing import Callable, Optional

# ===== Windows cron 编码修复 =====
# cron 在 no_agent 模式下用 cp936(GBK) 解码 stdout
# 所以脚本必须输出 GBK 编码字节，解码后才不会乱码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='gbk')
# ================================

# =====================================================================
# 异常分类树（从 httpx 学来）
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

# =====================================================================
# 中间件链（从 FastAPI 学来）
# =====================================================================
class WatchdogContext:
    def __init__(self):
        self.messages: list[str] = []
        self.diag_results: list[dict] = []
        self.repair_actions: list[str] = []
        self.gateway_states: dict[str, str] = {}
        self.gateway_alive: Optional[bool] = None
        self.incident: Optional["IncidentState"] = None
        self.should_restart: bool = False
        self.should_report: bool = False
        self.error: Optional[WatchdogError] = None

    def add_msg(self, msg: str): self.messages.append(msg)
    def add_repair(self, action: str):
        self.repair_actions.append(action); self.messages.append(f"   {action}")

class MiddlewareChain:
    def __init__(self): self._middlewares: list[tuple[str, Callable]] = []
    def add(self, name: str, fn: Callable[[WatchdogContext], None]):
        self._middlewares.append((name, fn))
    def run(self, ctx: WatchdogContext) -> WatchdogContext:
        for name, fn in self._middlewares:
            if ctx.error:
                ctx.add_msg(f"   [跳过] {name} 跳过（上游错误）")
                continue
            try:
                fn(ctx)
            except WatchdogError as e:
                ctx.error = e; ctx.add_msg(f"   [失败] {name}: {e}")
            except Exception as e:
                ctx.error = WatchdogError(f"{name} 异常: {e}")
                ctx.add_msg(f"   [崩溃] {name}: {e}")
        return ctx

# =====================================================================
# 配置
# =====================================================================
@dataclass
class Config:
    hermes_home: Path = Path.home() / "AppData" / "Local" / "hermes"
    state_file: Path = Path.home() / "AppData" / "Local" / "hermes" / "gateway_state.json"
    log_file: Path = Path.home() / "AppData" / "Local" / "hermes" / "logs" / "gateway.log"
    db_path: Path = Path.home() / "AppData" / "Local" / "hermes" / "scripts" / ".watchdog_v8.db"
    last_state_path: Path = Path.home() / "AppData" / "Local" / "hermes" / "scripts" / ".watchdog_last_state.json"
    proxy_url: str = "http://127.0.0.1:7897"
    reconnect_timeout: int = 90
    log_scan_lines: int = 80
    cooldown_sec: int = 600
    ping_target: str = "192.168.1.1"
    api_test_url: str = "https://www.baidu.com"

# =====================================================================
# SQLite 持久化（从 APScheduler 学来）
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
        conn.execute("""CREATE TABLE IF NOT EXISTS user_activity (
            id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp REAL NOT NULL,
            idle_seconds INTEGER NOT NULL, status TEXT NOT NULL)""")
        conn.commit(); conn.close()
    def save_incident(self, platform: str, problem: str, diag: list[dict], repairs: list[str], restarts: int):
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("INSERT INTO incidents (timestamp, platform, problem, diag_json, repair_actions, restarts) VALUES (?,?,?,?,?,?)",
                     (time.time(), platform, problem, json.dumps(diag, ensure_ascii=False),
                      json.dumps(repairs, ensure_ascii=False), restarts))
        conn.commit(); conn.close()
    def save_diag(self, layer: str, ok: bool, detail: str):
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("INSERT INTO diag_history (timestamp, layer, ok, detail) VALUES (?,?,?,?)",
                     (time.time(), layer, 1 if ok else 0, detail))
        conn.commit(); conn.close()
    def get_recent_incidents(self, limit: int = 10) -> list[dict]:
        conn = sqlite3.connect(str(self.db_path))
        rows = conn.execute("SELECT * FROM incidents ORDER BY timestamp DESC LIMIT ?", (limit,)).fetchall()
        conn.close()
        return [{"id":r[0],"time":r[1],"platform":r[2],"problem":r[3],
                 "diag":json.loads(r[4]),"repairs":json.loads(r[5]),
                 "restarts":r[6],"resolved":r[7]} for r in rows]
    def save_user_activity(self, idle_seconds: int, status: str):
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("INSERT INTO user_activity (timestamp, idle_seconds, status) VALUES (?,?,?)",
                     (time.time(), idle_seconds, status))
        conn.commit(); conn.close()
    def get_last_idle(self) -> Optional[dict]:
        conn = sqlite3.connect(str(self.db_path))
        row = conn.execute("SELECT timestamp, idle_seconds, status FROM user_activity ORDER BY id DESC LIMIT 1").fetchone()
        conn.close()
        if row: return {"ts":row[0],"idle":row[1],"status":row[2]}
        return None

# =====================================================================
# 日志
# =====================================================================
logger = logging.getLogger("watchdog.v8")
logger.setLevel(logging.WARNING)
_handler = logging.StreamHandler(sys.stderr)
_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s", datefmt="%H:%M:%S"))
logger.addHandler(_handler)

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
# 诊断中间件
# =====================================================================
IDLE_THRESHOLD = 180

def get_idle_seconds() -> int:
    try:
        last_input = ctypes.wintypes.DWORD()
        ctypes.windll.user32.GetLastInputInfo(ctypes.byref(last_input))
        tick = ctypes.windll.kernel32.GetTickCount()
        return (tick - last_input.value) // 1000
    except: return 0

def layer0_user_idle(ctx: WatchdogContext):
    idle = get_idle_seconds(); ctx.idle_seconds = idle
    if idle < 1800:
        if idle < IDLE_THRESHOLD: ctx.idle_status = "在线"
        else: ctx.idle_status = f"离开{idle//60}分钟"
        return
    last = None
    if hasattr(ctx, 'store'): last = ctx.store.get_last_idle()
    if last and last["idle"] >= 1800: ctx.idle_status = "未知（后台模式）"
    else: ctx.idle_status = f"离开{idle//3600}小时{idle%3600//60}分钟"

def diag_layer1_nic(ctx: WatchdogContext):
    runner = SubprocessRunner()
    try:
        _, out = runner.run(["netsh","interface","show","interface"])
        ok = "已连接" in out or "Connected" in out
        ctx.diag_results.append({"layer":"NIC","ok":ok,"detail":"网卡已连接" if ok else "无连接"})
    except SubprocessError as e: ctx.diag_results.append({"layer":"NIC","ok":False,"detail":str(e)})

def diag_layer2_gateway(ctx: WatchdogContext):
    runner = SubprocessRunner(); cfg = ctx._cfg if hasattr(ctx,'_cfg') else Config()
    try:
        _, out = runner.run(["ping","-n","1",cfg.ping_target])
        ok = "TTL=" in out
        ctx.diag_results.append({"layer":"GATEWAY","ok":ok,"detail":"网关可达" if ok else "网关不可达"})
    except SubprocessError as e: ctx.diag_results.append({"layer":"GATEWAY","ok":False,"detail":str(e)})

def diag_layer3_dns(ctx: WatchdogContext):
    runner = SubprocessRunner()
    try:
        _, out = runner.run(["nslookup","www.baidu.com"])
        ok = "Address:" in out
        ctx.diag_results.append({"layer":"DNS","ok":ok,"detail":"DNS正常" if ok else "DNS无结果"})
    except SubprocessError as e: ctx.diag_results.append({"layer":"DNS","ok":False,"detail":str(e)})

def diag_layer4_proxy(ctx: WatchdogContext):
    ctx.diag_results.append({"layer":"PROXY","ok":True,"detail":"代理检测跳过（非必需）"})

def diag_layer5_target(ctx: WatchdogContext):
    runner = SubprocessRunner(); cfg = ctx._cfg if hasattr(ctx,'_cfg') else Config()
    try:
        _, out = runner.run(["curl","-s","--connect-timeout","5","-o","NUL","-w","%{http_code}",cfg.api_test_url], timeout=10)
        ok = out.rstrip() == "200"
        ctx.diag_results.append({"layer":"TARGET","ok":ok,"detail":f"HTTP {out.strip()}" if not ok else "HTTP 200 ✓"})
    except SubprocessFailed as e:
        d = str(e); ctx.diag_results.append({"layer":"TARGET","ok":"200" in d,"detail":d[:60]})
    except SubprocessError as e: ctx.diag_results.append({"layer":"TARGET","ok":False,"detail":str(e)})

def diag_layer6_ssl(ctx: WatchdogContext):
    runner = SubprocessRunner()
    try:
        _, out = runner.run(["curl","-s","--connect-timeout","5","-o","NUL","-w","%{ssl_verify_result}:%{http_code}","https://www.baidu.com"], timeout=8)
        parts = out.strip().split(":")
        ssl_ok = parts[0] == "0" if len(parts) >= 1 else False
        ctx.diag_results.append({"layer":"SSL","ok":ssl_ok,"detail":"证书正常" if ssl_ok else f"证书验证={parts[0]}"})
    except SubprocessError as e: ctx.diag_results.append({"layer":"SSL","ok":False,"detail":f"HTTPS握手失败: {str(e)[:50]}"})

HEARTBEAT_TIMEOUT = 1800  # 30分钟，避免Discord重试导致频繁误报

def check_gateway_process(ctx: WatchdogContext):
    runner = SubprocessRunner(); cfg = ctx._cfg if hasattr(ctx,'_cfg') else Config()
    try:
        raw = json.loads(cfg.state_file.read_text(encoding="utf-8"))
        pid = raw.get("pid")
        if not pid: ctx.gateway_alive = False; ctx.add_msg("   [警告] Gateway 状态文件无 PID"); return
        _, out = runner.run(["tasklist","/FI",f"PID eq {pid}","/NH"])
        pid_exists = str(pid) in out
        updated_at_str = raw.get("updated_at","")
        heartbeat_ok = False
        if updated_at_str:
            try:
                updated = datetime.fromisoformat(updated_at_str.replace("Z","+00:00"))
                age = (datetime.now(timezone.utc)-updated).total_seconds()
                heartbeat_ok = age < HEARTBEAT_TIMEOUT
            except: heartbeat_ok = False
        if not pid_exists: ctx.gateway_alive = False; ctx.add_msg(f"   [警告] Gateway (PID {pid}) 进程已消失")
        elif not heartbeat_ok: ctx.gateway_alive = False; ctx.add_msg(f"   [警告] Gateway (PID {pid}) 状态冻结（已 >300s 无更新）")
        else: ctx.gateway_alive = True
    except (FileNotFoundError, json.JSONDecodeError, OSError) as e:
        ctx.gateway_alive = None; ctx.add_msg(f"   [警告] 无法读取状态: {e}")

def check_platform_states(ctx: WatchdogContext):
    cfg = ctx._cfg if hasattr(ctx, '_cfg') else Config()
    try:
        raw = json.loads(cfg.state_file.read_text(encoding="utf-8"))
        # Discord 已禁用 — 不检查，避免其重连耗尽连接池触发误重启
        for name in ("telegram","weixin"):
            p = raw.get("platforms",{}).get(name,{})
            ctx.gateway_states[name] = p.get("state","unknown")
    except (FileNotFoundError, json.JSONDecodeError) as e:
        ctx.add_msg(f"   [警告] 读取平台状态失败: {e}")

# =====================================================================
# 自动修复中间件
# =====================================================================
def auto_repair(ctx: WatchdogContext):
    runner = SubprocessRunner()
    for r in ctx.diag_results:
        if r["ok"]: continue
        if r["layer"] == "NIC":
            try:
                runner.run(["netsh","winsock","reset","category=all"], timeout=10); time.sleep(1)
                runner.run(["netsh","int","ip","reset"], timeout=10)
                ctx.add_repair("[修复] Winsock + TCP/IP 重置完成")
            except SubprocessError as e: ctx.add_repair(f"[错误] 网卡修复失败: {e}")
        elif r["layer"] == "GATEWAY":
            try: runner.run(["ipconfig","/renew"], timeout=15); ctx.add_repair("[修复] DHCP 续租完成")
            except SubprocessError as e: ctx.add_repair(f"[错误] DHCP 续租失败: {e}")
        elif r["layer"] == "DNS":
            try:
                runner.run(["ipconfig","/flushdns"], timeout=10); time.sleep(1)
                runner.run(["ipconfig","/registerdns"], timeout=10)
                ctx.add_repair("[修复] DNS 缓存已刷新")
            except SubprocessError as e: ctx.add_repair(f"[错误] DNS 刷新失败: {e}")
        elif r["layer"] == "SSL":
            try:
                runner.run(["pip","install","--upgrade","certifi"], timeout=30)
                runner.run(["ipconfig","/flushdns"], timeout=10)
                ctx.add_repair("[安全] 证书升级 + DNS 刷新完成")
            except SubprocessError as e: ctx.add_repair(f"[错误] SSL 修复失败: {e}")

# =====================================================================
# Gateway 操作中间件
# =====================================================================
def restart_gateway_if_needed(ctx: WatchdogContext):
    for r in ctx.diag_results:
        if not r["ok"] and r["layer"] in ("NIC","GATEWAY","DNS"):
            ctx.add_msg("   [错误] 底层网络异常，跳过 Gateway 重启")
            return
    if ctx.gateway_alive is False or any(s != "connected" for s in ctx.gateway_states.values()):
        hermes_path = str(Path.home() / "AppData" / "Local" / "hermes" / "hermes-agent" / "venv" / "Scripts" / "hermes")
        ctx.add_msg("   [重启] 正在重启 Gateway (hermes gateway restart)...")
        try:
            # 用 hermes gateway restart 而不是裸 gateway run
            # gateway run 会导致死锁：旧进程锁没释放，新进程报 "Another instance" 秒退
            result = subprocess.run([hermes_path, "gateway", "restart"], capture_output=True, text=True, timeout=30, creationflags=subprocess.CREATE_NO_WINDOW)
            if result.returncode == 0:
                ctx.add_msg("   [完成] Gateway 重启成功，等待恢复...")
                ctx.should_restart = True
            else:
                ctx.add_msg(f"   [失败] gateway restart 返回码 {result.returncode}: {result.stderr[:200]}")
                # 回退：尝试先 stop 再 run
                ctx.add_msg("   [回退] 尝试 gateway stop + gateway run...")
                subprocess.run([hermes_path, "gateway", "stop"], capture_output=True, timeout=15, creationflags=subprocess.CREATE_NO_WINDOW)
                time.sleep(3)
                subprocess.Popen([hermes_path, "gateway", "run"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW)
                ctx.add_msg("   [完成] Gateway 已通过 stop+run 启动")
                ctx.should_restart = True
        except subprocess.TimeoutExpired:
            ctx.add_msg("   [失败] gateway restart 超时30s")
            raise GatewayRestartFailed("gateway restart 超时")
        except OSError as e:
            raise GatewayRestartFailed(str(e))

def wait_for_reconnect(ctx: WatchdogContext):
    if not ctx.should_restart: return
    cfg = ctx._cfg if hasattr(ctx,'_cfg') else Config()
    deadline = time.time() + cfg.reconnect_timeout
    while time.time() < deadline:
        try:
            raw = json.loads(cfg.state_file.read_text(encoding="utf-8"))
            tg = raw.get("platforms",{}).get("telegram",{}).get("state","")
            wx = raw.get("platforms",{}).get("weixin",{}).get("state","")
            if tg == "connected" and wx == "connected":
                ctx.add_msg(f"   [完成] Gateway 恢复 — Telegram {tg}, 微信 {wx}")
                return
            time.sleep(3)
        except: time.sleep(3)
    raise GatewayNotRecovered(f"Gateway 恢复超时 ({cfg.reconnect_timeout}s)")

# =====================================================================
# 报告中间件
# =====================================================================
def report_results(ctx: WatchdogContext):
    if not ctx.should_report and not ctx.error: return
    now = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")
    ctx.add_msg(f"\n[时间]  {now}")
    if ctx.error: ctx.add_msg(f"\n[警告] 看门狗执行异常: {ctx.error}"); return
    plat = " + ".join(f"{k}={v}" for k,v in ctx.gateway_states.items())
    ctx.add_msg(f"\n[状态] 平台: {plat}")
    ctx.add_msg(f"\n[诊断] 六层诊断:")
    for r in ctx.diag_results:
        m = "[完成]" if r["ok"] else "[失败]"
        ctx.add_msg(f"   {m}  {r['layer']:8s}  {r['detail']}")

# =====================================================================
# 主看门狗
# =====================================================================
class WatchdogV8:
    def __init__(self, cfg: Optional[Config] = None):
        self.cfg = cfg or Config(); self.store = JobStore(self.cfg.db_path); self._build_chain()
    def _build_chain(self):
        self.chain = MiddlewareChain()
        for name, fn in [("用户状态",layer0_user_idle),("进程检查",check_gateway_process),
                         ("平台状态",check_platform_states),("Layer1 网卡",diag_layer1_nic),
                         ("Layer2 网关",diag_layer2_gateway),("Layer3 DNS",diag_layer3_dns),
                         ("Layer4 代理",diag_layer4_proxy),("Layer5 目标",diag_layer5_target),
                         ("Layer6 SSL",diag_layer6_ssl),("自动修复",auto_repair),
                         ("重启网关",restart_gateway_if_needed),("等待恢复",wait_for_reconnect),
                         ("生成报告",report_results)]:
            self.chain.add(name, fn)
    def _health_signature(self, ctx: WatchdogContext) -> str:
        """生成健康签名 — 只含关键状态，Discord 已禁用不纳入"""
        sig_parts = []
        # 平台连接状态 — 只检查 Telegram 和微信，Discord 已禁用
        for name in ("telegram", "weixin"):
            s = ctx.gateway_states.get(name, "unknown")
            sig_parts.append(f"{name}={s}")
        # Gateway 进程存活
        sig_parts.append(f"gateway_alive={ctx.gateway_alive}")
        # 网络诊断只看关键层
        for r in ctx.diag_results:
            layer = r["layer"]
            if layer in ("PROXY",): continue  # 跳过已知不稳定的Vortex代理
            sig_parts.append(f"{layer}={r['ok']}")
        # 错误信息
        sig_parts.append(f"err={'yes' if ctx.error else 'no'}")
        return "|".join(sig_parts)

    def run(self):
        ctx = WatchdogContext(); ctx._cfg = self.cfg; ctx.store = self.store
        self.chain.run(ctx)
        if hasattr(ctx,'idle_seconds'): self.store.save_user_activity(ctx.idle_seconds, getattr(ctx,'idle_status','未知'))
        problems = [p for p,s in ctx.gateway_states.items() if s != "connected"]
        if problems or ctx.error: self.store.save_incident(platform="+".join(problems), problem=str(ctx.error or "平台断连"), diag=ctx.diag_results, repairs=ctx.repair_actions, restarts=1 if ctx.should_restart else 0)
        for r in ctx.diag_results: self.store.save_diag(r["layer"], r["ok"], r["detail"])
        # --- 只有真正执行了修复或重启才输出，且10分钟内不重复发 ---
        needs_report = bool(ctx.repair_actions) or ctx.should_restart or (ctx.error and isinstance(ctx.error, (GatewayRestartFailed, GatewayNotRecovered)))
        if needs_report:
            # 10分钟冷静期检查
            cooldown_file = self.cfg.last_state_path
            last_report_time = 0
            try:
                if cooldown_file.exists():
                    last_report_time = float(cooldown_file.read_text(encoding="utf-8").strip())
            except: pass
            now = time.time()
            if now - last_report_time > 600:  # 10分钟
                cooldown_file.write_text(str(now), encoding="utf-8")
                if ctx.messages: print("\n".join(ctx.messages))

def main() -> None:
    try: watchdog = WatchdogV8(); watchdog.run()
    except Exception:
        logger.exception("Watchdog v8 自身异常")
        print("[警告] 看门狗 v8 自身发生异常，请检查日志")

if __name__ == "__main__":
    main()
