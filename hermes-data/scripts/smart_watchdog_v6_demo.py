#!/usr/bin/env python3
"""watchdog_v6.py — 展示从顶级项目中偷师的高级模式"""

from __future__ import annotations

import json
import logging
import subprocess
import sys
import time
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, replace
from datetime import datetime
from enum import Enum, auto
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Optional, Protocol, runtime_checkable

# =====================================================================
# 🎯 模式1: Sentinel 值（从 Rich 偷师）
#    替代 `Optional[None]` 避免歧义
# =====================================================================
class _Unset:
    """Sentinel: 表示"未设置"，区别于 None"""
    def __repr__(self): return "UNSET"
UNSET = _Unset()


# =====================================================================
# 🎯 模式2: 自定义异常用于控制流（从 yt-dlp 偷师）
# =====================================================================
class RepairFailed(Exception):
    """修复失败 — 可被上层捕获做不同处理"""
class NeedsUserAction(RepairFailed):
    """需要用户介入"""
class TransientError(RepairFailed):
    """临时性错误，可重试"""


# =====================================================================
# 🎯 模式3: RetryManager — 迭代器式重试（从 yt-dlp 偷师）
#   用法:
#     for attempt in RetryManager(max_retries=3, sleep_func=backoff):
#         try:
#             do_something()
#         except TransientError as err:
#             attempt.error = err
#             continue
# =====================================================================
class RetryManager:
    """迭代器式重试 — 比函数包装更灵活"""
    attempt: int = 0
    _error: Any = UNSET

    def __init__(self, max_retries: int = 3,
                 sleep_func: Callable[[int], float] | None = None,
                 on_retry: Callable[[Any, int], None] | None = None):
        self.max_retries = max_retries
        self.sleep_func = sleep_func or (lambda n: min(1 * 2 ** n, 10))
        self.on_retry = on_retry

    @property
    def error(self) -> Any:
        return None if self._error is UNSET else self._error

    @error.setter
    def error(self, value: Any):
        self._error = value

    def _should_retry(self) -> bool:
        return self._error is not UNSET and self.attempt <= self.max_retries

    def __iter__(self):
        while self._should_retry():
            self._error = UNSET
            self.attempt += 1
            yield self
            if self.error:
                delay = self.sleep_func(self.attempt - 1)
                if self.on_retry:
                    self.on_retry(self.error, self.attempt)
                if delay > 0:
                    time.sleep(delay)


# =====================================================================
# 🎯 模式4: Protocol 接口 — 插件式架构（从 Rich 偷师）
#   任何对象只要有 check() 方法，就能作为健康检查器
# =====================================================================
@runtime_checkable
class HealthChecker(Protocol):
    """健康检查协议 — 任何实现它的对象都能被看门狗使用"""
    def check(self) -> tuple[bool, str]:
        """返回 (是否健康, 描述信息)"""


# =====================================================================
# 🎯 模式5: Immutable Dataclass — 安全的值传递（从 Rich 偷师）
# =====================================================================
@dataclass(frozen=True)
class GatewayState:
    """不可变状态快照 — 修改时返回新实例"""
    telegram: str
    weixin: str
    pid: int | None
    gateway_alive: bool
    updated_at: float

    def is_all_connected(self) -> bool:
        return self.telegram == "connected" and self.weixin == "connected"

    def with_update(self, **kwargs) -> "GatewayState":
        """返回修改后的新实例（不可变模式）"""
        return replace(self, **kwargs)

    @classmethod
    def from_dict(cls, raw: dict | None) -> Optional["GatewayState"]:
        if raw is None:
            return None
        tg = raw.get("platforms", {}).get("telegram", {}).get("state", "unknown")
        wx = raw.get("platforms", {}).get("weixin", {}).get("state", "unknown")
        pid = raw.get("pid")
        return cls(
            telegram=tg, weixin=wx, pid=pid,
            gateway_alive=ProcessUtil.is_alive(pid) if pid else False,
            updated_at=time.time(),
        )


# =====================================================================
# 🎯 模式6: 工具函数泛化（从 yt-dlp 偷师）
# =====================================================================
def shell(cmd: list[str], timeout: int = 10,
          max_retries: int = 2) -> subprocess.CompletedProcess | None:
    """泛化 shell 调用，支持重试"""
    for attempt in RetryManager(max_retries=max_retries):
        try:
            return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired as err:
            attempt.error = err
            continue
        except OSError:
            return None  # OS错误不重试
    return None


# =====================================================================
# 🎯 模式7: threading.local 线程隔离（从 Rich 偷师）
# =====================================================================
class WatchdogContext(threading.local):
    """线程安全上下文 — 每个线程独立"""
    consecutive_failures: int = 0
    last_error: str = ""

    def reset(self):
        self.consecutive_failures = 0
        self.last_error = ""


# =====================================================================
# 🛠️ 看门狗核心（v6 示范版）
# =====================================================================
class ProcessUtil:
    @staticmethod
    def is_alive(pid: int | None) -> bool:
        if not pid:
            return False
        result = shell(["tasklist", "/fi", f"PID eq {pid}", "/nh", "/fo", "csv"])
        return result is not None and str(pid) in result.stdout

    @staticmethod
    def kill_all_gateways():
        result = shell(["tasklist", "/fo", "csv", "/nh"])
        if not result:
            return
        for line in result.stdout.split("\n"):
            if "gateway" not in line.lower():
                continue
            parts = line.split(",")
            if len(parts) >= 2:
                pid = parts[1].strip().strip('"')
                if pid.isdigit():
                    subprocess.run(["taskkill", "/f", "/pid", pid],
                                   capture_output=True, timeout=5)


class GatewayManager:
    def __init__(self, hermes_home: Path):
        self.hermes_home = hermes_home

    def restart(self) -> bool:
        ProcessUtil.kill_all_gateways()
        time.sleep(2)
        hermes_bin = str(self.hermes_home / "hermes-agent" / "venv" / "Scripts" / "hermes")
        if not Path(hermes_bin).exists():
            hermes_bin = "hermes"
        try:
            subprocess.Popen(
                [hermes_bin, "gateway", "run"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            return True
        except OSError:
            return False


class LogWatcher(HealthChecker):
    """实现 HealthChecker 协议的日志监控器"""
    def __init__(self, log_path: Path):
        self.log_path = log_path

    def check(self) -> tuple[bool, str]:
        if not self.log_path.exists():
            return False, "日志文件不存在"
        try:
            size = self.log_path.stat().st_size
            return True, f"日志 {size / 1024:.0f}KB"
        except OSError as err:
            return False, str(err)


# =====================================================================
# 🎯 模式8: 装饰器 — 计时/错误兜底（从 Rich 偷师）
# =====================================================================
def timed(func):
    """计时装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        logger = logging.getLogger("watchdog.v6")
        logger.debug("%s took %.2fs", func.__name__, elapsed)
        return result
    return wrapper


def safe_run(func):
    """安全执行装饰器 — 任何异常转成 RepaireFailed"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except RepairFailed:
            raise
        except Exception as err:
            raise RepairFailed(f"{func.__name__}: {err}") from err
    return wrapper


# =====================================================================
# 🚀 v6 主循环 — 用 yt-dlp 式 RetryManager 修复
# =====================================================================
class SmartWatchdogV6:
    def __init__(self, config_path: Path = None):
        config_path = config_path or Path.home() / "AppData" / "Local" / "hermes"
        self.state_file = config_path / "gateway_state.json"
        self.log_file = config_path / "logs" / "gateway.log"
        self.gateway = GatewayManager(config_path)
        self.ctx = WatchdogContext()
        self._setup_logging()

    def _setup_logging(self):
        logger = logging.getLogger("watchdog.v6")
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            h = logging.StreamHandler(sys.stderr)
            h.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
            logger.addHandler(h)

    def get_state(self) -> GatewayState | None:
        raw = self._read_state_file()
        return GatewayState.from_dict(raw)

    @safe_run
    def _read_state_file(self) -> dict | None:
        path = self.state_file
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    @safe_run
    def attempt_repair(self) -> bool:
        """使用 yt-dlp 式 RetryManager 进行修复"""
        logger = logging.getLogger("watchdog.v6")

        for attempt in RetryManager(
            max_retries=3,
            sleep_func=lambda n: min(2 * 2 ** n, 15),
            on_retry=lambda err, n: logger.warning("修复尝试 %d 失败: %s", n, err),
        ):
            try:
                if not self.gateway.restart():
                    raise TransientError("Gateway 启动失败")
                # 等待恢复
                for _ in range(15):
                    state = self.get_state()
                    if state and state.is_all_connected():
                        return True
                    time.sleep(3)
                raise TransientError("等待恢复超时")

            except TransientError as err:
                attempt.error = err
                continue

        raise RepairFailed("所有修复尝试均失败")

    def run(self) -> None:
        state = self.get_state()
        if state is None:
            # 用 RetryManager 尝试修复
            try:
                if self.attempt_repair():
                    return  # 静默
            except RepairFailed:
                print("🚨 Gateway 状态文件丢失，自动修复失败")
            return

        if state.is_all_connected():
            if self.ctx.consecutive_failures > 0:
                self.ctx.reset()
            return  # 静默

        # 有问题 — 用 RetryManager 修复
        try:
            if self.attempt_repair():
                self.ctx.consecutive_failures = 0
                return  # 静默修好
        except RepairFailed as err:
            self.ctx.consecutive_failures += 1
            self.ctx.last_error = str(err)
            if self.ctx.consecutive_failures >= 3:
                print(f"🚨 连续 {self.ctx.consecutive_failures} 次修复失败: {err}")
                print(f"   ⚡ 需检查代理或 Gateway")


if __name__ == "__main__":
    SmartWatchdogV6().run()