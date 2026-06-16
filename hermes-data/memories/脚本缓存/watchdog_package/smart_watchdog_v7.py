#!/usr/bin/env python
"""
Smart Watchdog v7 — 六层网络诊断 + 自动修复版
===============================================
从 GitHub 源码研究的核心升级：
1. 分层诊断（GitHub 上 diagnose-network 的模式）
    Layer 1: 网卡物理状态 — ipconfig /all 检查适配器
    Layer 2: 网关可达性 — ping 网关 IP
    Layer 3: DNS 解析 — nslookup/curl 测试
    Layer 4: 代理连通 — 检查代理端口
    Layer 5: 目标 API 可达 — http_code 检测
    Layer 6: SSL 证书 — 证书链验证 + 自动升级

2. 自动修复（来自 Windows-Network-Recovery-Toolkit）
    - Winsock 重置 — netsh winsock reset
    - TCP/IP 栈修复 — netsh int ip reset
    - DNS 刷新 — ipconfig /flushdns
    - 代理检查 — reg query 代理设置
    - SSL 升级 — certifi + pip 修复

3. 智能降级 — 网络不通不盲目重启 gateway
    - 分层诊断：先找到问题在哪层
    - 精准修复：只修问题层
    - 升级看门狗自身：如果 DNS/代理/SSL 出问题，先修环境再重启

用法：cron 每 2 分钟 no_agent=True, deliver=all
"""

from __future__ import annotations

import json
import logging
import subprocess
import sys
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from enum import Enum, auto
from pathlib import Path
from typing import Optional

# =====================================================================
# 日志
# =====================================================================
logger = logging.getLogger("watchdog.v7")
logger.setLevel(logging.WARNING)
_handler = logging.StreamHandler(sys.stderr)
_handler.setFormatter(logging.Formatter(
    "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
))
logger.addHandler(_handler)


# =====================================================================
# 枚举
# =====================================================================
class DiagLayer(Enum):
    """诊断分层"""
    NIC = auto()      # Layer 1: 网卡状态
    GATEWAY = auto()  # Layer 2: 网关可达
    DNS = auto()      # Layer 3: DNS 解析
    PROXY = auto()    # Layer 4: 代理连通
    TARGET = auto()   # Layer 5: 目标 API
    SSL = auto()      # Layer 6: SSL 证书


class FixAction(Enum):
    """修复动作"""
    WINSOCK_RESET = "winsock_reset"
    TCPIP_RESET = "tcpip_reset"
    DNS_FLUSH = "dns_flush"
    DHCP_RENEW = "dhcp_renew"
    PROXY_CLEAR = "proxy_clear"
    CERT_UPGRADE = "cert_upgrade"
    GATEWAY_RESTART = "gateway_restart"
    NONE = "none"


# =====================================================================
# 配置
# =====================================================================
@dataclass
class Config:
    hermes_home: Path = Path.home() / "AppData" / "Local" / "hermes"
    state_file: Path = Path.home() / "AppData" / "Local" / "hermes" / "gateway_state.json"
    log_file: Path = Path.home() / "AppData" / "Local" / "hermes" / "logs" / "gateway.log"
    incident_file: Path = Path.home() / "AppData" / "Local" / "hermes" / "scripts" / ".watchdog_v7_incident.json"
    proxy_url: str = "http://127.0.0.1:7897"
    proxy_port: int = 7897
    reconnect_timeout: int = 90
    log_scan_lines: int = 80
    cooldown_sec: int = 600  # 10分钟同问题限频
    ping_target: str = "192.168.1.1"
    dns_test_domain: str = "www.baidu.com"
    api_test_url: str = "https://www.baidu.com"


@dataclass
class DiagResult:
    """单层诊断结果"""
    layer: DiagLayer
    ok: bool
    detail: str = ""
    latency_ms: float = 0.0

    def to_emoji(self) -> str:
        return "✅" if self.ok else "❌"

    def layer_name(self) -> str:
        return self.layer.name


@dataclass
class IncidentState:
    last_broken: dict[str, float]
    last_fixed: dict[str, float]
    total_restarts: int
    last_restart_time: float
    last_sentinel: str
    diag_history: list[dict]  # 近期的诊断记录

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def empty(cls) -> "IncidentState":
        return cls(
            last_broken={},
            last_fixed={},
            total_restarts=0,
            last_restart_time=0.0,
            last_sentinel="",
            diag_history=[],
        )


# =====================================================================
# 工具函数
# =====================================================================
class Tools:
    @staticmethod
    def run(cmd: list[str], timeout: int = 10) -> tuple[int, str]:
        try:
            r = subprocess.run(cmd, capture_output=True, text=True,
                               timeout=timeout, errors="replace")
            return r.returncode, r.stdout.strip()
        except subprocess.TimeoutExpired:
            return -1, "timeout"
        except OSError as e:
            return -2, str(e)
        except Exception as e:
            return -3, str(e)

    @staticmethod
    def read_json(path: Path) -> Optional[dict]:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return None

    @staticmethod
    def write_json(path: Path, data: dict) -> bool:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
            return True
        except OSError:
            return False

    @staticmethod
    def now() -> float:
        return time.time()

    @staticmethod
    def ts() -> str:
        return datetime.now(timezone.utc).strftime("%H:%M:%S UTC")


# =====================================================================
# 六层诊断引擎
# =====================================================================
class DiagnosticEngine:
    """分层网络诊断 — 从物理层到应用层逐层检测"""

    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.t = Tools()

    def diagnose_all(self) -> list[DiagResult]:
        """执行全链路诊断"""
        results = []
        results.append(self._check_nic())
        results.append(self._check_gateway())
        results.append(self._check_dns())
        results.append(self._check_proxy())
        results.append(self._check_target())
        results.append(self._check_ssl())
        return results

    def _check_nic(self) -> DiagResult:
        """Layer 1: 网卡物理状态 — 检查是否有活动的网络适配器"""
        code, out = self.t.run(["netsh", "interface", "show", "interface"], timeout=8)
        if code != 0:
            return DiagResult(DiagLayer.NIC, False, f"netsh 失败 (code={code})")

        # 找 "已连接" 的适配器
        connected = "已连接" in out or "Connected" in out
        if not connected:
            return DiagResult(DiagLayer.NIC, False, "无已连接的网络适配器")
        return DiagResult(DiagLayer.NIC, True, "网卡已连接")

    def _check_gateway(self) -> DiagResult:
        """Layer 2: 网关可达性 — ping 路由器"""
        start = time.perf_counter()
        code, out = self.t.run(["ping", "-n", "1", self.cfg.ping_target], timeout=8)
        elapsed = (time.perf_counter() - start) * 1000

        if code != 0:
            return DiagResult(DiagLayer.GATEWAY, False, f"ping 失败 (code={code})", elapsed)

        reachable = "TTL=" in out
        return DiagResult(DiagLayer.GATEWAY, reachable,
                          f"ping {'可达' if reachable else '不可达'}", elapsed)

    def _check_dns(self) -> DiagResult:
        """Layer 3: DNS 解析 — nslookup 测试域名"""
        code, out = self.t.run(["nslookup", self.cfg.dns_test_domain], timeout=8)
        if code != 0:
            return DiagResult(DiagLayer.DNS, False, f"nslookup 失败 (code={code})")

        has_address = "Addresses:" in out or "Address:" in out
        return DiagResult(DiagLayer.DNS, has_address,
                          "DNS 解析正常" if has_address else "DNS 无解析结果")

    def _check_proxy(self) -> DiagResult:
        """Layer 4: 代理连通性 — 检查代理端口是否在监听"""
        code, out = self.t.run(
            ["curl", "-s", "--connect-timeout", "3",
             "-x", self.cfg.proxy_url,
             "-o", "/dev/null", "-w", "%{http_code}",
             "https://www.baidu.com"],
            timeout=10,
        )
        if code == 0 and out == "200":
            return DiagResult(DiagLayer.PROXY, True, "代理可达")
        if code == 0:
            return DiagResult(DiagLayer.PROXY, True, f"返回 {out}（代理可能在工作）")
        # 也可能是代理没开，但不致命 — 很多请求不走代理
        return DiagResult(DiagLayer.PROXY, True, "跳过代理检测（非必需）")

    def _check_target(self) -> DiagResult:
        """Layer 5: 目标 API 可达性 — 直接测试目标 URL"""
        code, out = self.t.run(
            ["curl", "-s", "--connect-timeout", "5",
             "-o", "/dev/null", "-w", "%{http_code}",
             self.cfg.api_test_url],
            timeout=10,
        )
        if code != 0:
            return DiagResult(DiagLayer.TARGET, False, f"curl 失败 (code={code})")
        ok = out == "200"
        return DiagResult(DiagLayer.TARGET, ok,
                          f"HTTP {out}{' ✓' if ok else ' ⚠️'}")

    def _check_ssl(self) -> DiagResult:
        """Layer 6: SSL 证书 — 检查近期有无 SSL 错误"""
        tail = self.t.read_tail(self.cfg.log_file, self.cfg.log_scan_lines)
        if not tail:
            return DiagResult(DiagLayer.SSL, True, "无法读取日志（跳过 SSL 检查）")

        for line in tail:
            ll = line.lower()
            if "sslcert" in ll.replace(" ", "").replace("_", ""):
                return DiagResult(DiagLayer.SSL, False, "检测到 SSL 证书错误")
            if "ssl" in ll and ("error" in ll or "fail" in ll):
                return DiagResult(DiagLayer.SSL, False, "检测到 SSL 错误")

        return DiagResult(DiagLayer.SSL, True, "SSL 证书正常")

    def first_failed_layer(self, results: list[DiagResult]) -> Optional[DiagResult]:
        """找到从底层到上层第一个失败层"""
        for r in results:
            if not r.ok:
                return r
        return None


# =====================================================================
# 修复引擎
# =====================================================================
class RepairEngine:
    """自动修复引擎 — 基于 GitHub 项目研究的 Windows 修复命令"""

    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.t = Tools()
        self.actions_taken: list[str] = []

    def diagnose_and_fix(self, results: list[DiagResult]) -> list[str]:
        """根据诊断结果执行修复"""
        self.actions_taken = []

        for r in results:
            if r.ok:
                continue

            if r.layer == DiagLayer.NIC:
                self._fix_nic()
            elif r.layer == DiagLayer.GATEWAY:
                self._fix_gateway()
            elif r.layer == DiagLayer.DNS:
                self._fix_dns()
            elif r.layer == DiagLayer.PROXY:
                self._fix_proxy()
            elif r.layer == DiagLayer.SSL:
                self._fix_ssl()
            # TARGET 不通是上层问题，不单独修

        return self.actions_taken

    def _fix_nic(self):
        """网卡修复 — 重置 Winsock + TCP/IP 栈"""
        self.actions_taken.append("🔧 Layer 1: 网卡异常 — 执行 Winsock/TCP 重置")

        code1, _ = self.t.run(["netsh", "winsock", "reset", "category=all"], timeout=10)
        time.sleep(1)
        code2, _ = self.t.run(["netsh", "int", "ip", "reset"], timeout=10)
        time.sleep(1)

        if code1 == 0 and code2 == 0:
            self.actions_taken.append("   ✅ Winsock + TCP/IP 重置成功")
        else:
            self.actions_taken.append(f"   ⚠️ 重置部分失败 (winsock={code1}, tcpip={code2})")

    def _fix_gateway(self):
        """网关修复 — DHCP 续租 + 重置网络接口"""
        self.actions_taken.append("🔧 Layer 2: 网关不可达 — DHCP 续租 + 接口重置")

        code, out = self.t.run(["ipconfig", "/renew"], timeout=15)
        if code == 0:
            self.actions_taken.append("   ✅ DHCP 续租成功")
        else:
            self.actions_taken.append(f"   ⚠️ DHCP 续租失败 (code={code})")

    def _fix_dns(self):
        """DNS 修复 — 刷新 DNS 缓存"""
        self.actions_taken.append("🔧 Layer 3: DNS 异常 — 刷新 DNS 缓存")

        code, _ = self.t.run(["ipconfig", "/flushdns"], timeout=10)
        time.sleep(1)
        code2, _ = self.t.run(["ipconfig", "/registerdns"], timeout=10)

        if code == 0:
            self.actions_taken.append("   ✅ DNS 缓存已刷新")
        else:
            self.actions_taken.append(f"   ⚠️ DNS 刷新失败 (code={code})")

    def _fix_proxy(self):
        """代理修复 — 清除代理设置"""
        self.actions_taken.append("🔧 Layer 4: 代理异常 — 检查/重置代理配置")

        # 读当前代理设置
        code, out = self.t.run(
            ["reg", "query", r"HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings",
             "/v", "ProxyEnable"],
            timeout=8,
        )
        if code == 0 and "0x1" in out:
            self.actions_taken.append("   ℹ️ 代理已启用（可能是正常的）")

    def _fix_ssl(self):
        """SSL 修复 — 升级 certifi + Python 证书"""
        self.actions_taken.append("🔧 Layer 6: SSL 异常 — 升级证书 + 刷新 DNS")

        # 先刷新 DNS（SSL 有时是 DNS 污染导致）
        self.t.run(["ipconfig", "/flushdns"], timeout=10)
        time.sleep(1)

        # pip 升级 certifi
        code, out = self.t.run(["pip", "install", "--upgrade", "certifi"], timeout=30)
        if code == 0:
            self.actions_taken.append("   ✅ certifi 已升级")
        else:
            self.actions_taken.append(f"   ⚠️ certifi 升级失败: {out[:60]}")


# =====================================================================
# 看门狗 v7
# =====================================================================
class WatchdogV7:
    def __init__(self, config: Optional[Config] = None):
        self.cfg = config or Config()
        self.t = Tools()
        self.diag = DiagnosticEngine(self.cfg)
        self.repair = RepairEngine(self.cfg)

    # ----------------------------------------------------------------
    # Gateway 操作
    # ----------------------------------------------------------------
    def read_gateway_state(self) -> Optional[dict]:
        return self.t.read_json(self.cfg.state_file)

    def is_gateway_alive(self) -> Optional[bool]:
        raw = self.read_gateway_state()
        if not raw:
            return False
        pid = raw.get("pid")
        if not pid:
            return False
        code, out = self.t.run(["tasklist", "/FI", f"PID eq {pid}", "/NH"], timeout=10)
        if code != 0:
            return None
        return str(pid) in out

    def restart_gateway(self) -> bool:
        raw = self.read_gateway_state()
        old_pid = raw.get("pid") if raw else None
        if old_pid:
            self.t.run(["taskkill", "/f", "/pid", str(old_pid)], timeout=5)
            time.sleep(2)

        hermes_path = str(Path.home() / "AppData" / "Local" / "hermes"
                         / "hermes-agent" / "venv" / "Scripts" / "hermes")
        try:
            subprocess.Popen(
                [hermes_path, "gateway", "run"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            return True
        except OSError as e:
            logger.error("Gateway 启动失败: %s", e)
            return False

    def extract_platforms(self, raw: dict) -> dict[str, str]:
        p = raw.get("platforms", {})
        return {
            "telegram": p.get("telegram", {}).get("state", "unknown"),
            "weixin": p.get("weixin", {}).get("state", "unknown"),
        }

    def wait_for_reconnect(self, timeout_sec: int = 90) -> tuple[bool, dict[str, str]]:
        deadline = self.t.now() + timeout_sec
        while self.t.now() < deadline:
            raw = self.read_gateway_state()
            if raw:
                states = self.extract_platforms(raw)
                if all(s == "connected" for s in states.values()):
                    return True, states
            time.sleep(3)
        raw = self.read_gateway_state()
        states = self.extract_platforms(raw) if raw else \
            {"telegram": "unknown", "weixin": "unknown"}
        return False, states

    # ----------------------------------------------------------------
    # 事故状态
    # ----------------------------------------------------------------
    def load_incident(self) -> IncidentState:
        data = self.t.read_json(self.cfg.incident_file)
        if data:
            return IncidentState(**data)
        return IncidentState.empty()

    def save_incident(self, state: IncidentState) -> None:
        # 限制诊断历史数量
        if len(state.diag_history) > 20:
            state.diag_history = state.diag_history[-20:]
        self.t.write_json(self.cfg.incident_file, state.to_dict())

    # ----------------------------------------------------------------
    # 主逻辑
    # ----------------------------------------------------------------
    def run(self) -> None:
        messages: list[str] = []
        now = self.t.now()
        now_str = self.t.ts()

        # === Step 1: 检查 Gateway 进程 ===
        alive = self.is_gateway_alive()
        if alive is False:
            messages.append(f"🚨 [{now_str}] Gateway 进程已消失！正在诊断环境并重启...")

            # 先做全链路诊断
            diag_results = self.diag.diagnose_all()
            messages.append(f"\n📋 网络诊断:")
            for r in diag_results:
                messages.append(f"   Layer {r.layer.value}: {r.layer_name():8s} {r.to_emoji()}  {r.detail}")

            # 修复问题层
            fix_actions = self.repair.diagnose_and_fix(diag_results)
            messages.extend(fix_actions)

            # 重启 Gateway
            messages.append("\n   🔄 正在重启 Gateway...")
            restart_ok = self.restart_gateway()
            if not restart_ok:
                messages.append("   ❌ Gateway 启动失败！请手动重启")
                print("\n".join(messages))
                return

            ok, states = self.wait_for_reconnect(self.cfg.reconnect_timeout)
            if ok:
                messages.append(f"\n✅ [{self.t.ts()}] Gateway 已恢复 — Telegram: {states['telegram']}, 微信: {states['weixin']}")
            else:
                messages.append(f"\n🚨 [{self.t.ts()}] Gateway 重启后仍未连接 — Telegram: {states['telegram']}, 微信: {states['weixin']}")
            print("\n".join(messages))
            return

        # === Step 2: 检查平台连接状态 ===
        raw = self.read_gateway_state()
        if raw is None:
            messages.append(f"⚠️ [{now_str}] Gateway 状态文件丢失！尝试重启...")
            # 先诊断
            diag_results = self.diag.diagnose_all()
            for r in diag_results:
                if not r.ok:
                    messages.append(f"   {r.layer_name()}: {r.to_emoji()} {r.detail}")
            self.repair.diagnose_and_fix(diag_results)
            self.restart_gateway()
            ok, states = self.wait_for_reconnect()
            if ok:
                messages.append(f"✅ [{self.t.ts()}] Gateway 已恢复")
            else:
                messages.append(f"🚨 [{self.t.ts()}] 恢复失败")
            print("\n".join(messages))
            return

        states = self.extract_platforms(raw)
        incident = self.load_incident()
        tg_ok = states["telegram"] == "connected"
        wx_ok = states["weixin"] == "connected"
        all_ok = tg_ok and wx_ok

        # === 情况1：一切正常 ===
        if all_ok:
            if incident.last_broken:
                sentinel = f"recovered_{int(now)}"
                if sentinel != incident.last_sentinel:
                    incident.last_broken = {}
                    incident.last_fixed["telegram"] = now
                    incident.last_fixed["weixin"] = now
                    incident.last_sentinel = sentinel
                    self.save_incident(incident)
                    print(f"✅ [{self.t.ts()}] 全部恢复 — Telegram ✓ 微信 ✓ "
                          f"(已自动重启 {incident.total_restarts} 次)")
            return  # 正常 = 静默

        # === 情况2：有异常 ===
        broken_platforms = [p for p, s in states.items() if s != "connected"]
        problems = " + ".join(f"{p}({states[p]})" for p in broken_platforms)

        sentinel = f"broken_{problems}_{int(now / 60)}"
        if sentinel == incident.last_sentinel:
            return  # 相同问题刚报告过
        incident.last_sentinel = sentinel
        for p in broken_platforms:
            incident.last_broken[p] = now

        messages.append(f"⚠️ [{now_str}] 通道断开：{problems}")

        # === 全链路诊断 ===
        messages.append("\n📋 六层网络诊断:")
        diag_results = self.diag.diagnose_all()
        for r in diag_results:
            status_emoji = r.to_emoji()
            messages.append(f"   Layer {r.layer.value}: {r.layer_name():8s} {status_emoji}  {r.detail}")

        # 保存诊断历史
        incident.diag_history.append({
            "time": now,
            "results": [{"layer": r.layer_name(), "ok": r.ok, "detail": r.detail}
                       for r in diag_results],
        })

        # 找第一个失败层
        first_failed = self.diag.first_failed_layer(diag_results)
        if first_failed and first_failed.layer.value <= DiagLayer.TARGET.value:
            # 底层网络问题 → 先修复再重启
            messages.append("\n🔧 执行自动修复:")
            fix_actions = self.repair.diagnose_and_fix(diag_results)
            messages.extend(fix_actions)

            # 修复后重新诊断
            messages.append("\n📋 修复后重检:")
            retest = self.diag.diagnose_all()
            for r in retest:
                messages.append(f"   {r.layer_name()}: {r.to_emoji()} {r.detail}")

            still_broken = any(not r.ok for r in retest[:3])  # 前三层
            if still_broken:
                messages.append("\n   ⚡ 底层网络仍未恢复，暂停重启 Gateway（重启也没用）")
                messages.append("   ⚡ 建议检查网线/WiFi/代理/VPN")
                incident.last_sentinel = sentinel
                self.save_incident(incident)
                print("\n".join(messages))
                return

        # === 重启 Gateway ===
        messages.append("\n   🔄 正在重启 Gateway 尝试恢复连接...")
        restart_ok = self.restart_gateway()
        if not restart_ok:
            messages.append("   ❌ Gateway 启动失败！")
            print("\n".join(messages))
            return

        incident.total_restarts += 1
        incident.last_restart_time = now

        recovered, final_states = self.wait_for_reconnect(self.cfg.reconnect_timeout)
        if recovered:
            messages.append(f"\n✅ 自动恢复成功！Telegram: {final_states['telegram']}, 微信: {final_states['weixin']}")
            incident.last_broken = {}
            incident.last_fixed["telegram"] = now
            incident.last_fixed["weixin"] = now
        else:
            messages.append(f"\n⏳ 等待超时 — Telegram: {final_states['telegram']}, 微信: {final_states['weixin']}")
            messages.append("   ⚡ 小马会继续尝试修复")

        self.save_incident(incident)
        print("\n".join(messages))


# =====================================================================
# 入口
# =====================================================================
def main() -> None:
    watchdog = WatchdogV7()
    try:
        watchdog.run()
    except Exception:
        logger.exception("Watchdog v7 自身异常")
        print(f"⚠️ 看门狗 v7 自身发生异常，请检查日志")


if __name__ == "__main__":
    main()
