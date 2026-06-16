#!/usr/bin/env python3
"""
Smart Watchdog v5 — 生产级品质，零噪音自愈
========================================
v5 改进亮点：
  ✅ Enum + Dataclass — 类型安全，告别魔法字符串
  ✅ Type hints everywhere — 代码自文档化
  ✅ 抛弃 bare except — 每个异常精准捕获
  ✅ logging 代替 print — 结构化日志可追溯
  ✅ SRP 单一职责 — 每个函数只做一件事
  ✅ Retry + backoff — 子进程调用更健壮
  ✅ 配置集中化 — 不散落硬编码

用法：cron 每1分钟触发 no_agent=True
  正常 → 静默（empty stdout）
  自愈 → 静默
  需介入 → 限频通知
"""

from __future__ import annotations

import json
import logging
import subprocess
import sys
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum, auto
from pathlib import Path
from typing import Optional

# =====================================================================
# 日志系统 — 替代 print()
# =====================================================================
logger = logging.getLogger("watchdog.v5")
logger.setLevel(logging.WARNING)
_handler = logging.StreamHandler(sys.stderr)
_handler.setFormatter(logging.Formatter(
    "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
))
logger.addHandler(_handler)

# =====================================================================
# 错误类型枚举 — 告别魔法字符串
# =====================================================================
class ErrorType(Enum):
    """看门狗能识别的所有异常类型"""
    # --- 代理/VPN 级别 ---
    PROXY_DOWN = auto()
    DOUBLE_DISCONNECT = auto()

    # --- Telegram 问题 ---
    TELEGRAM_PROTOCOL_ERROR = auto()
    TELEGRAM_CONNECT_ERROR = auto()
    TELEGRAM_SEND_DEGRADED = auto()
    TELEGRAM_DELIVERY_FAILED = auto()
    TELEGRAM_STATE_ABNORMAL = auto()

    # --- 微信问题 ---
    WEIXIN_RATE_LIMITED = auto()
    WEIXIN_SSL_ERROR = auto()
    WEIXIN_CONNECT_ERROR = auto()
    WEIXIN_STATE_ABNORMAL = auto()

    # --- Gateway 自身 ---
    GATEWAY_EXITED = auto()
    SSL_PROXY_INTERCEPT = auto()
    STATE_MISSING = auto()


class NotifyTier(Enum):
    """通知等级"""
    T0_SILENT = "T0-静默自愈"         # 微信限流 → 绝不通知
    T1_SILENT_RESTART = "T1-静默重启"  # 临时性 → 静默修复
    T1_ESCALATED = "T1-升报"           # 3次以上 → 通知
    T2_USER_ACTION = "T2-需介入"       # 代理挂了 → 限频通知
    T2_COOLDOWN = "T2-限频中"          # 在冷却期 → 不通知


class PlatformState(Enum):
    """平台状态枚举"""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    RETRYING = "retrying"
    ERROR = "error"
    UNKNOWN = "unknown"

    @classmethod
    def from_str(cls, s: Optional[str]) -> "PlatformState":
        if not s:
            return cls.UNKNOWN
        for member in cls:
            if member.value == s:
                return member
        return cls.UNKNOWN


# =====================================================================
# 数据模型 — Dataclass 替代 dict
# =====================================================================
@dataclass
class Config:
    """所有配置集中管理"""
    hermes_home: Path = Path.home() / "AppData" / "Local" / "hermes"
    state_file: Path = Path.home() / "AppData" / "Local" / "hermes" / "gateway_state.json"
    log_file: Path = Path.home() / "AppData" / "Local" / "hermes" / "logs" / "gateway.log"
    status_cache: Path = Path.home() / "AppData" / "Local" / "hermes" / "scripts" / ".watchdog_status.json"
    proxy_url: str = "http://127.0.0.1:7897"
    reconnect_timeout: int = 50
    log_scan_lines: int = 40
    dns_test_target: str = "114.114.114.114"

    # 通知冷却
    cooldown_sec: int = 1800         # 30分钟
    escalation_threshold: int = 3    # 连续3次自愈失败才通知


@dataclass
class HealthSnapshot:
    """当前健康状态"""
    telegram: PlatformState
    weixin: PlatformState
    gateway_pid: Optional[int]
    gateway_alive: bool

    def all_ok(self) -> bool:
        return self.telegram == PlatformState.CONNECTED \
            and self.weixin == PlatformState.CONNECTED \
            and self.gateway_alive

    def __hash__(self) -> int:
        return hash((self.telegram, self.weixin, self.gateway_alive))


@dataclass
class ErrorEvent:
    """单条错误事件"""
    error_type: ErrorType
    timestamp: str
    raw_line: str

    def type_name(self) -> str:
        return self.error_type.name.lower()


@dataclass
class WatchdogState:
    """看门狗持久化状态"""
    last_notified: dict[str, float] = field(default_factory=dict)
    cooldown_sec: int = 1800
    consecutive_restarts: int = 0
    last_restart_at: float = 0.0
    last_healthy_state: Optional[tuple] = None
    incident_active: dict[str, bool] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


# =====================================================================
# I/O 层 — FileIO 封装所有文件操作
# =====================================================================
class FileIO:
    """文件读写，异常安全，返回 Optional"""

    @staticmethod
    def read_json(path: Path) -> Optional[dict]:
        try:
            raw = path.read_text(encoding="utf-8")
            return json.loads(raw)
        except FileNotFoundError:
            logger.debug("File not found: %s", path)
            return None
        except json.JSONDecodeError as exc:
            logger.warning("Invalid JSON in %s: %s", path, exc)
            return None
        except PermissionError as exc:
            logger.error("Permission denied: %s — %s", path, exc)
            return None
        except OSError as exc:
            logger.error("IO error reading %s: %s", path, exc)
            return None

    @staticmethod
    def write_json(path: Path, data: dict) -> bool:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                json.dumps(data, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            return True
        except OSError as exc:
            logger.error("Failed to write %s: %s", path, exc)
            return False

    @staticmethod
    def read_log_tail(path: Path, lines: int) -> Optional[list[str]]:
        """读日志尾部N行，异常安全"""
        if not path.exists():
            return None
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
            parts = text.splitlines()
            return parts[-lines:] if len(parts) > lines else parts
        except OSError as exc:
            logger.warning("Cannot read log %s: %s", path, exc)
            return None


# =====================================================================
# 进程工具 — ProcessUtil
# =====================================================================
class ProcessUtil:
    """进程操作，带重试 + 超时"""

    @staticmethod
    def is_alive(pid: Optional[int]) -> bool:
        if not pid:
            return False
        try:
            result = subprocess.run(
                ["tasklist", "/fi", f"PID eq {pid}", "/nh", "/fo", "csv"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return str(pid) in result.stdout
        except subprocess.TimeoutExpired:
            logger.warning("tasklist timed out for PID %s", pid)
            return False
        except (OSError, ValueError) as exc:
            logger.warning("tasklist failed: %s", exc)
            return False

    @staticmethod
    def run_with_retry(
        cmd: list[str],
        timeout: int = 10,
        max_retries: int = 2,
        retry_delay: float = 1.0,
    ) -> subprocess.CompletedProcess:
        """运行命令 + 指数退避重试"""
        last_exc: Optional[Exception] = None
        for attempt in range(1 + max_retries):
            try:
                return subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                )
            except subprocess.TimeoutExpired as exc:
                last_exc = exc
                if attempt < max_retries:
                    delay = retry_delay * (2 ** attempt)
                    logger.debug("cmd %s[0] timed out, retry %d/%d in %.1fs",
                                 cmd, attempt + 1, max_retries, delay)
                    time.sleep(delay)
            except OSError as exc:
                last_exc = exc
                break  # OS错误不可重试
        # 全部失败 — 返回假的失败结果
        logger.warning("cmd %s[0] failed after %d retries: %s",
                       cmd, max_retries, last_exc)
        return subprocess.CompletedProcess(
            args=cmd, returncode=-1,
            stdout="", stderr=str(last_exc or ""),
        )

    @staticmethod
    def kill_process(pid: int) -> bool:
        try:
            subprocess.run(
                ["taskkill", "/f", "/pid", str(pid)],
                capture_output=True,
                timeout=5,
            )
            return True
        except (subprocess.TimeoutExpired, OSError) as exc:
            logger.warning("Failed to kill PID %s: %s", pid, exc)
            return False

    @staticmethod
    def kill_all_gateways():
        """杀掉所有 gateway 进程"""
        result = ProcessUtil.run_with_retry(
            ["tasklist", "/fo", "csv", "/nh"],
            timeout=10, max_retries=1,
        )
        if result.returncode != 0:
            return
        for line in result.stdout.split("\n"):
            if "gateway" not in line.lower():
                continue
            parts = line.split(",")
            if len(parts) >= 2:
                pid_str = parts[1].strip().strip('"')
                if pid_str.isdigit():
                    ProcessUtil.kill_process(int(pid_str))


# =====================================================================
# 诊断引擎 — 单一职责：分析问题原因
# =====================================================================
class DiagnosticEngine:
    """日志 + 状态 → 错误诊断"""

    # 错误类型识别规则: (keywords, error_type)
    _RULES: list[tuple[list[str], ErrorType]] = [
        (["weixin", "rate limited"],                  ErrorType.WEIXIN_RATE_LIMITED),
        (["weixin", "sslcertverification"],            ErrorType.WEIXIN_SSL_ERROR),
        (["weixin", "cannot connect to host"],         ErrorType.WEIXIN_CONNECT_ERROR),
        (["telegram", "remoteprotocolerror"],          ErrorType.TELEGRAM_PROTOCOL_ERROR),
        (["telegram", "connecterror"],                 ErrorType.TELEGRAM_CONNECT_ERROR),
        (["telegram", "send_path_degraded"],           ErrorType.TELEGRAM_SEND_DEGRADED),
        (["telegram", "failed to deliver"],            ErrorType.TELEGRAM_DELIVERY_FAILED),
        (["error", "traceback"],                       ErrorType.GATEWAY_EXITED),
    ]

    def __init__(self, config: Config):
        self.config = config

    def scan_log(self) -> list[ErrorEvent]:
        """扫描日志尾部找错误事件"""
        tail = FileIO.read_log_tail(self.config.log_file, self.config.log_scan_lines)
        if not tail:
            return []

        events: list[ErrorEvent] = []
        for line in reversed(tail):
            ll = line.lower().replace(" ", "")
            ts = line[:19] if len(line) >= 19 else ""
            for keywords, error_type in self._RULES:
                all_keywords_present = all(kw in ll for kw in keywords)
                if all_keywords_present:
                    events.append(ErrorEvent(error_type, ts, line.strip()))
                    break  # 一行只匹配一个类型
        return events

    def diagnose(
        self,
        state: Optional[dict],
        events: list[ErrorEvent],
    ) -> tuple[Optional[ErrorType], str]:
        """智能诊断根本原因"""
        if state is None:
            return ErrorType.STATE_MISSING, "Gateway 状态文件不存在"

        tg_state = PlatformState.from_str(
            state.get("platforms", {}).get("telegram", {}).get("state")
        )
        wx_state = PlatformState.from_str(
            state.get("platforms", {}).get("weixin", {}).get("state")
        )
        pid = state.get("pid")
        gw_state = state.get("gateway_state", "")

        error_types = {e.error_type for e in events}

        # 1. 进程没了
        if pid and not ProcessUtil.is_alive(pid):
            ok = NetworkChecker.is_proxy_alive(self.config)
            if not ok:
                return ErrorType.PROXY_DOWN, "代理/VPN 断连，Gateway 进程已退出"
            return ErrorType.GATEWAY_EXITED, f"Gateway 进程 (PID {pid}) 已退出"

        # 2. 双平台同时断 → 代理问题
        both_down = tg_state != PlatformState.CONNECTED \
            and wx_state != PlatformState.CONNECTED
        if both_down and gw_state != "stopped":
            ok = NetworkChecker.is_proxy_alive(self.config)
            if not ok:
                return ErrorType.PROXY_DOWN, "代理/VPN 断连，两个平台同时断线"
            return ErrorType.DOUBLE_DISCONNECT, "两个平台同时断开 (代理不稳定)"

        # 3. SSL 问题
        if any(e in (ErrorType.WEIXIN_SSL_ERROR,) for e in error_types):
            return ErrorType.SSL_PROXY_INTERCEPT, "代理拦截微信 SSL 证书"

        # 4. 单独 Telegram 问题
        if tg_state != PlatformState.CONNECTED \
                and wx_state == PlatformState.CONNECTED:
            for et in [ErrorType.TELEGRAM_PROTOCOL_ERROR,
                       ErrorType.TELEGRAM_CONNECT_ERROR,
                       ErrorType.TELEGRAM_SEND_DEGRADED]:
                if et in error_types:
                    return et, self._error_description(et)
            return ErrorType.TELEGRAM_STATE_ABNORMAL, \
                f"Telegram 状态异常 ({tg_state.value})"

        # 5. 单独微信问题
        if wx_state != PlatformState.CONNECTED \
                and tg_state == PlatformState.CONNECTED:
            for et in [ErrorType.WEIXIN_RATE_LIMITED,
                       ErrorType.WEIXIN_CONNECT_ERROR]:
                if et in error_types:
                    return et, self._error_description(et)
            return ErrorType.WEIXIN_STATE_ABNORMAL, \
                f"微信状态异常 ({wx_state.value})"

        return None, "不明异常"

    @staticmethod
    def _error_description(et: ErrorType) -> str:
        descs = {
            ErrorType.TELEGRAM_PROTOCOL_ERROR: "Telegram 服务器断开连接",
            ErrorType.TELEGRAM_CONNECT_ERROR: "连不上 Telegram 服务器",
            ErrorType.TELEGRAM_SEND_DEGRADED: "Telegram 发送通道不稳定",
            ErrorType.WEIXIN_RATE_LIMITED: "微信消息发送太频繁被限流",
            ErrorType.WEIXIN_CONNECT_ERROR: "连不上微信服务器",
        }
        return descs.get(et, et.name.lower())


# =====================================================================
# 网络检查
# =====================================================================
class NetworkChecker:

    @staticmethod
    def is_proxy_alive(config: Config) -> bool:
        """检查代理端口是否响应"""
        result = ProcessUtil.run_with_retry(
            ["curl", "-s", "--connect-timeout", "3",
             "-o", "/dev/null", "-w", "%{http_code}",
             config.proxy_url],
            timeout=8, max_retries=1,
        )
        code = result.stdout.strip()
        return code.isdigit() and int(code) >= 200

    @staticmethod
    def flush_dns() -> bool:
        """Windows DNS 缓存刷新"""
        result = ProcessUtil.run_with_retry(
            ["ipconfig", "/flushdns"],
            timeout=10, max_retries=2, retry_delay=1.0,
        )
        return result.returncode == 0

    @staticmethod
    def _certifi_paths(config: Config) -> list[str]:
        """可能的 pip 路径"""
        venv_pip = str(
            config.hermes_home / "hermes-agent" / "venv" / "Scripts" / "pip"
        )
        return [venv_pip, "pip"]

    @staticmethod
    def update_certificates(config: Config) -> bool:
        """升级 certifi 证书包修复 SSL 问题"""
        for pip_bin in NetworkChecker._certifi_paths(config):
            if not Path(pip_bin).exists():
                continue
            result = ProcessUtil.run_with_retry(
                [pip_bin, "install", "--upgrade", "certifi"],
                timeout=30, max_retries=1, retry_delay=2.0,
            )
            if result.returncode == 0:
                logger.info("certifi upgraded via %s", pip_bin)
                return True
        return False


# =====================================================================
# Gateway 管理器
# =====================================================================
class GatewayManager:

    def __init__(self, config: Config):
        self.config = config

    def restart(self) -> bool:
        """重启 gateway"""
        # 1. 杀旧的
        ProcessUtil.kill_all_gateways()
        time.sleep(2)

        # 2. 找 hermes 命令
        hermes_bin = str(
            self.config.hermes_home / "hermes-agent" / "venv" / "Scripts" / "hermes"
        )
        if not Path(hermes_bin).exists():
            hermes_bin = "hermes"

        # 3. 启动新的
        try:
            subprocess.Popen(
                [hermes_bin, "gateway", "run"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            return True
        except OSError as exc:
            logger.error("Failed to start gateway: %s", exc)
            return False

    def wait_for_reconnect(self) -> tuple[bool, str]:
        """等待恢复连接"""
        deadline = time.time() + self.config.reconnect_timeout
        while time.time() < deadline:
            state = FileIO.read_json(self.config.state_file)
            if state:
                tg = PlatformState.from_str(
                    state.get("platforms", {}).get("telegram", {}).get("state")
                )
                wx = PlatformState.from_str(
                    state.get("platforms", {}).get("weixin", {}).get("state")
                )
                if tg == PlatformState.CONNECTED and wx == PlatformState.CONNECTED:
                    return True, "全部恢复"
                if tg == PlatformState.CONNECTED:
                    return True, f"Telegram已恢复，微信: {wx.value}"
                if wx == PlatformState.CONNECTED:
                    return True, f"微信已恢复，Telegram: {tg.value}"
            time.sleep(3)
        return False, "超时未恢复"


# =====================================================================
# 通知决策 — 通知去重 + 等级判定
# =====================================================================
class NotificationDecider:
    """判断是否应该通知用户"""

    def __init__(self, config: Config, state: WatchdogState):
        self.config = config
        self.state = state

    def decide(self, error_type: ErrorType) -> tuple[bool, NotifyTier]:
        """决定是否通知 + 什么等级"""
        # T0: 微信限流 → 绝不通知
        if error_type == ErrorType.WEIXIN_RATE_LIMITED:
            return False, NotifyTier.T0_SILENT

        now = time.time()

        # T1: 临时性问题 → 静默重启（3次内不通知）
        silent_types = {
            ErrorType.TELEGRAM_PROTOCOL_ERROR,
            ErrorType.TELEGRAM_SEND_DEGRADED,
            ErrorType.TELEGRAM_STATE_ABNORMAL,
            ErrorType.GATEWAY_EXITED,
            ErrorType.WEIXIN_STATE_ABNORMAL,
            ErrorType.SSL_PROXY_INTERCEPT,
            ErrorType.WEIXIN_CONNECT_ERROR,
            ErrorType.WEIXIN_SSL_ERROR,
            ErrorType.DOUBLE_DISCONNECT,
        }
        if error_type in silent_types:
            if self.state.consecutive_restarts >= self.config.escalation_threshold:
                last = self.state.last_notified.get(error_type.name, 0)
                if now - last > self.config.cooldown_sec:
                    return True, NotifyTier.T1_ESCALATED
                return False, NotifyTier.T2_COOLDOWN
            return False, NotifyTier.T1_SILENT_RESTART

        # T2: 需要介入的问题 → 限频通知
        last = self.state.last_notified.get(error_type.name, 0)
        if now - last > self.config.cooldown_sec:
            return True, NotifyTier.T2_USER_ACTION
        return False, NotifyTier.T2_COOLDOWN

    def mark_notified(self, error_type: ErrorType) -> None:
        self.state.last_notified[error_type.name] = time.time()


# =====================================================================
# 看门狗主循环
# =====================================================================
class SmartWatchdog:
    """主类 — 协调所有组件"""

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.diagnostician = DiagnosticEngine(self.config)
        self.gateway = GatewayManager(self.config)
        self.state = self._load_state()
        self.decider = NotificationDecider(self.config, self.state)

    def _load_state(self) -> WatchdogState:
        data = FileIO.read_json(self.config.status_cache)
        if data:
            return WatchdogState(
                last_notified=data.get("last_notified", {}),
                cooldown_sec=data.get("cooldown_sec", self.config.cooldown_sec),
                consecutive_restarts=data.get("consecutive_restarts", 0),
                last_restart_at=data.get("last_restart_at", 0.0),
                last_healthy_state=data.get("last_healthy_state"),
                incident_active=data.get("incident_active", {}),
            )
        return WatchdogState(cooldown_sec=self.config.cooldown_sec)

    def _save_state(self) -> None:
        FileIO.write_json(self.config.status_cache, self.state.to_dict())

    def run(self) -> None:
        """主入口"""
        raw_state = FileIO.read_json(self.config.state_file)

        if raw_state is None:
            self._handle_missing_state()
            return

        snapshot = self._take_snapshot(raw_state)

        # 一切正常 → 静默
        if snapshot.all_ok():
            self._reset_if_recovered()
            return

        # 没变化且健康 → 静默
        if self._state_unchanged_healthy(snapshot):
            return

        self.state.last_healthy_state = snapshot.to_tuple()

        # 诊断问题
        events = self.diagnostician.scan_log()
        cause_type, cause_msg = self.diagnostician.diagnose(raw_state, events)

        if cause_type is None:
            return  # 诊断不出等下次

        notify, tier = self.decider.decide(cause_type)

        # 修复前预处理
        self._pre_repair(cause_type)

        # 执行修复
        self.gateway.restart()
        self.state.consecutive_restarts += 1
        self.state.last_restart_at = time.time()

        recovered, recovery_msg = self.gateway.wait_for_reconnect()

        if recovered:
            self._handle_recovery(cause_type, cause_msg, recovery_msg, notify, tier)
        else:
            self._handle_failure(cause_type, cause_msg, notify)

        self._save_state()

    def _take_snapshot(self, raw_state: dict) -> HealthSnapshot:
        tg_state = PlatformState.from_str(
            raw_state.get("platforms", {}).get("telegram", {}).get("state")
        )
        wx_state = PlatformState.from_str(
            raw_state.get("platforms", {}).get("weixin", {}).get("state")
        )
        pid = raw_state.get("pid")
        return HealthSnapshot(
            telegram=tg_state,
            weixin=wx_state,
            gateway_pid=pid,
            gateway_alive=ProcessUtil.is_alive(pid) if pid else False,
        )

    def _state_unchanged_healthy(self, snapshot: HealthSnapshot) -> bool:
        if snapshot.to_tuple() == self.state.last_healthy_state:
            return snapshot.all_ok()
        return False

    def _reset_if_recovered(self) -> None:
        """恢复后重置计数器"""
        if self.state.consecutive_restarts > 0:
            self.state.consecutive_restarts = 0
            self.state.incident_active = {}
            self._save_state()

    def _handle_missing_state(self) -> None:
        """状态文件丢了 → 直接重启"""
        self.gateway.restart()
        recovered, _ = self.gateway.wait_for_reconnect()
        if recovered:
            self.state.consecutive_restarts = 0
            self.state.incident_active = {}
            self._save_state()
            return
        # 通知用户
        print("🚨 gateway_state.json 丢失，自动修复中")

    def _pre_repair(self, cause_type: ErrorType) -> None:
        """修复前尝试 DNS + SSL 修复"""
        dns_types = {
            ErrorType.WEIXIN_CONNECT_ERROR,
            ErrorType.WEIXIN_SSL_ERROR,
            ErrorType.TELEGRAM_CONNECT_ERROR,
            ErrorType.TELEGRAM_PROTOCOL_ERROR,
            ErrorType.DOUBLE_DISCONNECT,
            ErrorType.SSL_PROXY_INTERCEPT,
        }
        if cause_type in dns_types:
            NetworkChecker.flush_dns()
            time.sleep(1)
            if "ssl" in cause_type.name.lower():
                NetworkChecker.update_certificates(self.config)
                time.sleep(1)

    def _handle_recovery(
        self,
        cause_type: ErrorType,
        cause_msg: str,
        recovery_msg: str,
        notify: bool,
        tier: NotifyTier,
    ) -> None:
        """自愈成功"""
        if tier == NotifyTier.T2_USER_ACTION:
            if notify:
                print(f"🛠️ `{cause_msg}` — 已自动修复")
                print(f"   (`{cause_type.name.lower()}` → {recovery_msg})")
                self.decider.mark_notified(cause_type)
        self.state.consecutive_restarts = 0

    def _handle_failure(
        self,
        cause_type: ErrorType,
        cause_msg: str,
        notify: bool,
    ) -> None:
        """自愈失败"""
        if not notify:
            self.state.incident_active[cause_type.name] = True
            return

        print(f"🚨 `{cause_msg}`")
        if cause_type == ErrorType.PROXY_DOWN:
            print(f"   ⚡ 代理/VPN 可能需要检查一下")
        elif cause_type == ErrorType.TELEGRAM_CONNECT_ERROR:
            if self.state.consecutive_restarts >= self.config.escalation_threshold:
                print(f"   ⚡ 多次自动修复失败，可能需要检查代理")
            else:
                print(f"   ⚡ 下次 cron 再试自动修复")
        else:
            print(f"   ⚡ 下次 cron 再试自动修复")
        self.decider.mark_notified(cause_type)
        self.state.incident_active[cause_type.name] = True


# =====================================================================
# 添加 to_tuple 方法到 HealthSnapshot
# =====================================================================
def _snapshot_to_tuple(self: HealthSnapshot) -> tuple:
    return (self.telegram, self.weixin, self.gateway_alive)

HealthSnapshot.to_tuple = _snapshot_to_tuple


# =====================================================================
# 入口
# =====================================================================
def main() -> None:
    watchdog = SmartWatchdog()
    try:
        watchdog.run()
    except Exception:
        logger.exception("Watchdog v5 自身异常")
        # 不发通知 — 看门狗自身异常不能污染用户


if __name__ == "__main__":
    main()