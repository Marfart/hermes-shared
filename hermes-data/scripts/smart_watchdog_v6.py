#!/usr/bin/env python
"""
Smart Watchdog v6 — 会说话的看门狗
===================================
核心改进：
1. ❌ 不再静默自愈 — 修好了就告诉用户
2. ❌ 不再等3次再报 — 第一次出问题就汇报（按类型限频）
3. ✅ 双通道投递 — 输出所有异常/修复到 stdout（cron 帮投递）
4. ✅ 实时状态文件 — 当前会话也能读到问题记录
5. ✅ 升级 certifi 证书 + 刷新 DNS 后自动重试
6. ✅ Telegram/微信任一恢复即可送达消息

用法：cron 每 2 分钟 no_agent=True, deliver=all
  正常 → 静默（empty stdout）
  异常/修复 → 输出 → cron 投递到所有渠道
"""

from __future__ import annotations

import json
import logging
import subprocess
import sys
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# =====================================================================
# 日志
# =====================================================================
logger = logging.getLogger("watchdog.v6")
logger.setLevel(logging.WARNING)
_handler = logging.StreamHandler(sys.stderr)
_handler.setFormatter(logging.Formatter(
    "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
))
logger.addHandler(_handler)


# =====================================================================
# 配置
# =====================================================================
@dataclass
class Config:
    hermes_home: Path = Path.home() / "AppData" / "Local" / "hermes"
    state_file: Path = Path.home() / "AppData" / "Local" / "hermes" / "gateway_state.json"
    log_file: Path = Path.home() / "AppData" / "Local" / "hermes" / "logs" / "gateway.log"
    incident_file: Path = Path.home() / "AppData" / "Local" / "hermes" / "scripts" / ".watchdog_incident.json"
    health_state_file: Path = Path.home() / "AppData" / "Local" / "hermes" / "memories" / "脚本缓存" / "weixin_health_state.json"
    last_ok_file: Path = Path.home() / "AppData" / "Local" / "hermes" / "scripts" / ".watchdog_last_ok.txt"
    proxy_url: str = "http://127.0.0.1:7897"
    reconnect_timeout: int = 60
    log_scan_lines: int = 60
    cooldown_sec: int = 600  # 相同问题10分钟内不重复通知


@dataclass
class IncidentState:
    """持久化的事故状态"""
    last_broken: dict[str, float]  # platform -> timestamp
    last_fixed: dict[str, float]   # platform -> timestamp
    total_restarts: int
    last_restart_time: float
    last_sentinel: str  # 上次输出的消息指纹，用于去重

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
        )


# =====================================================================
# 工具函数
# =====================================================================
class Tools:
    @staticmethod
    def read_json(path: Path) -> Optional[dict]:
        try:
            raw = path.read_text(encoding="utf-8")
            return json.loads(raw)
        except (FileNotFoundError, json.JSONDecodeError, PermissionError, OSError):
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
    def read_tail(path: Path, lines: int) -> Optional[list[str]]:
        if not path.exists():
            return None
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
            parts = text.splitlines()
            return parts[-lines:] if len(parts) > lines else parts
        except OSError:
            return None

    @staticmethod
    def run(cmd: list[str], timeout: int = 10) -> tuple[int, str]:
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            return r.returncode, r.stdout.strip()
        except (subprocess.TimeoutExpired, OSError) as e:
            return -1, str(e)

    @staticmethod
    def now() -> float:
        return time.time()

    @staticmethod
    def ts() -> str:
        return datetime.now(timezone.utc).strftime("%H:%M:%S UTC")

    @staticmethod
    def beijing_time() -> str:
        return datetime.now(timezone.utc).strftime("%H:%M UTC")


# =====================================================================
# 看门狗 v6
# =====================================================================
class WatchdogV6:
    def __init__(self, config: Optional[Config] = None):
        self.cfg = config or Config()
        self.tools = Tools()

    # ----------------------------------------------------------------
    # 状态读取
    # ----------------------------------------------------------------
    def read_gateway_state(self) -> Optional[dict]:
        return self.tools.read_json(self.cfg.state_file)

    def is_gateway_process_alive(self):
            """检查 Gateway 进程是否真正活着（不只是 state 文件说活着）
            方法：读 state 文件中的 PID，用 tasklist /FI 精确检查该进程
            """
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

    def load_incident(self) -> IncidentState:
        data = self.tools.read_json(self.cfg.incident_file)
        if data:
            return IncidentState(**data)
        return IncidentState.empty()

    def save_incident(self, state: IncidentState) -> None:
        self.tools.write_json(self.cfg.incident_file, state.to_dict())

    # ----------------------------------------------------------------
    # 平台状态提取
    # ----------------------------------------------------------------
    def extract_platforms(self, raw: dict) -> dict[str, str]:
        """返回 {telegram: state, weixin: state}"""
        p = raw.get("platforms", {})
        return {
            "telegram": p.get("telegram", {}).get("state", "unknown"),
            "weixin": p.get("weixin", {}).get("state", "unknown"),
        }

    # ----------------------------------------------------------------
    # 诊断
    # ----------------------------------------------------------------
    def scan_log_for_trouble(self) -> Optional[list[str]]:
        """扫日志找最近的错误"""
        tail = self.tools.read_tail(self.cfg.log_file, self.cfg.log_scan_lines)
        if not tail:
            return None
        errors = []
        for line in reversed(tail):
            ll = line.lower()
            if "error" in ll and any(kw in ll for kw in ["weixin", "telegram"]):
                errors.append(line.strip())
            elif "sslcert" in ll.replace(" ", "").replace("_", ""):
                errors.append(line.strip())
        return errors[:10] if errors else None

    def check_network(self) -> bool:
        """简单网络连通性检查"""
        code, _ = self.tools.run(
            ["curl", "-s", "--connect-timeout", "3", "-o", "/dev/null",
             "-w", "%{http_code}", "https://www.baidu.com"],
            timeout=8,
        )
        if code == 0:
            return False
        return code >= 200

    def is_ssl_error(self) -> bool:
        """判断近期是否有 SSL 错误"""
        tail = self.tools.read_tail(self.cfg.log_file, self.cfg.log_scan_lines)
        if not tail:
            return False
        for line in tail:
            if "sslcert" in line.lower().replace(" ", "").replace("_", ""):
                return True
        return False

    # ----------------------------------------------------------------
    # 修复
    # ----------------------------------------------------------------
    def fix_ssl(self) -> bool:
        """修复 SSL 证书"""
        ok = True
        # 刷新 DNS
        code, _ = self.tools.run(["ipconfig", "/flushdns"], timeout=10)
        if code != 0:
            ok = False
            logger.warning("DNS flush failed")
        time.sleep(1)

        # 升级 certifi
        code, out = self.tools.run(
            ["pip", "install", "--upgrade", "certifi"],
            timeout=30,
        )
        if code != 0:
            ok = False
            logger.warning("certifi upgrade failed: %s", out)
        time.sleep(1)

        return ok

    def restart_gateway(self) -> bool:
        """重启 Gateway"""
        # 先查旧 gateway 的 PID
        raw = self.read_gateway_state()
        old_pid = raw.get("pid") if raw else None

        # 杀旧的
        if old_pid:
            self.tools.run(["taskkill", "/f", "/pid", str(old_pid)], timeout=5)
            time.sleep(2)

        # 再杀所有残余 gateway
        code, out = self.tools.run(["tasklist", "/fo", "csv", "/nh"], timeout=10)
        if code == 0:
            for line in out.split("\n"):
                if "gateway" in line.lower():
                    parts = line.split(",")
                    if len(parts) >= 2:
                        pid = parts[1].strip().strip('"')
                        if pid.isdigit():
                            self.tools.run(["taskkill", "/f", "/pid", pid], timeout=5)

        time.sleep(2)

        # 启动新的
        hermes_path = str(Path.home() / "AppData" / "Local" / "hermes" / "hermes-agent" / "venv" / "Scripts" / "hermes")
        try:
            subprocess.Popen(
                [hermes_path, "gateway", "run"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            return True
        except OSError as e:
            logger.error("Failed to start gateway: %s", e)
            return False

    def wait_for_reconnect(self, timeout_sec: int = 60) -> tuple[bool, dict[str, str]]:
        """等待恢复连接"""
        deadline = self.tools.now() + timeout_sec
        while self.tools.now() < deadline:
            raw = self.read_gateway_state()
            if raw:
                states = self.extract_platforms(raw)
                all_ok = all(s == "connected" for s in states.values())
                if all_ok:
                    return True, states
                if states.get("telegram") == "connected" or states.get("weixin") == "connected":
                    pass  # 继续等，直到两个都恢复
            time.sleep(3)
        # 超时，返回当前状态
        raw = self.read_gateway_state()
        states = self.extract_platforms(raw) if raw else {"telegram": "unknown", "weixin": "unknown"}
        return False, states

    # ----------------------------------------------------------------
    # 主逻辑
    # ----------------------------------------------------------------
    def run(self) -> None:
        """主入口 — 输出到 stdout = 通知用户，空 = 静默"""
        # 先检查进程是否活着（state 文件可能是过期的）
        alive = self.is_gateway_process_alive()
        if alive is False:
            print(f"⚠️ [{self.tools.ts()}] Gateway 进程已消失（state 文件过期）！正在自动重启...")
            restart_ok = self.restart_gateway()
            if not restart_ok:
                print(f"❌ [{self.tools.ts()}] Gateway 启动失败！请手动重启")
                return
            ok, states = self.wait_for_reconnect()
            if ok:
                print(f"✅ [{self.tools.ts()}] Gateway 已恢复 — Telegram: {states['telegram']}, 微信: {states['weixin']}")
            else:
                print(f"🚨 [{self.tools.ts()}] Gateway 重启后仍未连接 — Telegram: {states['telegram']}, 微信: {states['weixin']}")
            return

        raw = self.read_gateway_state()
        if raw is None:
            print(f"⚠️ [{self.tools.ts()}] Gateway 状态文件丢失！正在自动重启...")
            self.restart_gateway()
            ok, states = self.wait_for_reconnect()
            if ok:
                print(f"✅ [{self.tools.ts()}] Gateway 已恢复 — Telegram: {states['telegram']}, 微信: {states['weixin']}")
            else:
                print(f"🚨 [{self.tools.ts()}] Gateway 重启后仍未连接 — Telegram: {states['telegram']}, 微信: {states['weixin']}")
            return

        states = self.extract_platforms(raw)
        incident = self.load_incident()
        now = self.tools.now()

        tg_ok = states["telegram"] == "connected"
        wx_ok = states["weixin"] == "connected"
        all_ok = tg_ok and wx_ok

        # === 情况1：一切正常 ===
        if all_ok:
            # 如果之前有未解决的 incident，标记为已恢复
            if incident.last_broken:
                sentinel = f"recovered_{int(now)}"
                if sentinel != incident.last_sentinel:
                    incident.last_broken = {}
                    incident.last_fixed["telegram"] = now
                    incident.last_fixed["weixin"] = now
                    incident.last_sentinel = sentinel
                    self.save_incident(incident)
                    print(f"✅ [{self.tools.ts()}] 全部恢复 — Telegram ✓ 微信 ✓ "
                          f"(已自动重启 {incident.total_restarts} 次)")
            return  # 正常 = 静默

        # === 情况2：有异常 ===
        now_str = self.tools.ts()
        broken_platforms = [p for p, s in states.items() if s != "connected"]
        problems = " + ".join(f"{p}({states[p]})" for p in broken_platforms)

        # 检查是否近期已经报告过相同问题
        sentinel = f"broken_{problems}_{int(now / 60)}"  # 按分钟去重
        if sentinel == incident.last_sentinel:
            return  # 相同问题刚报告过，不重复
        incident.last_sentinel = sentinel

        # 记录 broken 时间
        for p in broken_platforms:
            incident.last_broken[p] = now

        # 诊断
        has_ssl = self.is_ssl_error()
        network_ok = self.check_network()

        messages = []
        messages.append(f"⚠️ [{now_str}] 通道断开：{problems}")

        if not network_ok:
            messages.append("   📡 网络不通 — 可能本地网络/代理出了问题")
            messages.append("   ⚡ 请检查代理/VPN 状态")
            # 不需要重启，网络问题重启也没用
            incident.last_sentinel = sentinel
            self.save_incident(incident)
            print("\n".join(messages))
            return

        if has_ssl:
            messages.append("   🔐 SSL 证书问题 — 正在自动修复...")
            ssl_ok = self.fix_ssl()
            if ssl_ok:
                messages.append("   ✅ SSL 证书已升级，DNS 已刷新")
            else:
                messages.append("   ⚠️ SSL 修复部分失败，继续尝试")

        # 重启 Gateway
        messages.append(f"   🔄 正在重启 Gateway...")
        restart_ok = self.restart_gateway()
        if not restart_ok:
            messages.append("   ❌ Gateway 启动失败！")
            print("\n".join(messages))
            return

        incident.total_restarts += 1
        incident.last_restart_time = now

        # 等待恢复
        recovered, final_states = self.wait_for_reconnect(self.cfg.reconnect_timeout)
        if recovered:
            messages.append(f"   ✅ 自动恢复成功！Telegram: {final_states['telegram']}, 微信: {final_states['weixin']}")
            incident.last_broken = {}
            incident.last_fixed["telegram"] = now
            incident.last_fixed["weixin"] = now
        else:
            messages.append(f"   ⏳ 等待超时 — Telegram: {final_states['telegram']}, 微信: {final_states['weixin']}")
            messages.append(f"   ⚡ 小马会继续尝试修复，如果持续异常请联系 Kali")

        self.save_incident(incident)
        print("\n".join(messages))


# =====================================================================
# 入口
# =====================================================================
def main() -> None:
    watchdog = WatchdogV6()
    try:
        watchdog.run()
    except Exception:
        logger.exception("Watchdog v6 自身异常")
        # 看门狗自己崩了也有通知
        print(f"⚠️ 看门狗 v6 自身发生异常，请检查日志")


if __name__ == "__main__":
    main()