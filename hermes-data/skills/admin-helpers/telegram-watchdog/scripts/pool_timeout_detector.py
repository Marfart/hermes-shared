#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
连接池超时检测器 — 扫描 gateway.log 最近的 Pool timeout 错误
超过阈值(5次)时重启 Gateway，修复 Vortex 代理冻结导致的连接池耗尽

原理：Vortex 代理 HTTPS 转发冻结时，端口开着但无法实际转发数据，
导致 Telegram 的 httpx 连接池被占满（Discord 重试也消耗连接），
出现 "Pool timeout: All connections in the connection pool are occupied"

级联路径：Vortex 冻结 → Discord 重试占满连接池 → Telegram 发送也超时 → 全平台断联

检测逻辑：扫描 gateway.log 最近 SCAN_MINUTES 分钟内的 Pool timeout 行数，
超过 THRESHOLD 次则重启 Gateway，冷却 COOLDOWN_SECONDS 秒防止重复触发。

Cron: every 3m, no_agent=True, deliver=local, job_id=de31a0c4a9b2
"""
from __future__ import annotations

import io
import json
import logging
import subprocess
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Windows cron 编码修复
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='gbk')

logger = logging.getLogger("pool_detector")
logger.setLevel(logging.WARNING)

# ===== 配置 =====
THRESHOLD = 5           # Pool timeout 超过5次触发重启
SCAN_MINUTES = 10      # 只扫描最近10分钟的日志
COOLDOWN_SECONDS = 300 # 重启后5分钟内不再重复触发

LOG_FILE = Path.home() / "AppData" / "Local" / "hermes" / "logs" / "gateway.log"
STATE_FILE = Path.home() / "AppData" / "Local" / "hermes" / "scripts" / ".pool_timeout_state.json"
GATEWAY_STATE = Path.home() / "AppData" / "Local" / "hermes" / "gateway_state.json"
HERMES_BIN = Path.home() / "AppData" / "Local" / "hermes" / "hermes-agent" / "venv" / "Scripts" / "hermes"


def load_state() -> dict:
    try:
        if STATE_FILE.exists():
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        pass
    return {"last_restart_time": 0}


def save_state(state: dict):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")


def count_recent_pool_timeouts() -> int:
    if not LOG_FILE.exists():
        return 0

    cutoff = datetime.now(timezone.utc) - timedelta(minutes=SCAN_MINUTES)
    count = 0

    try:
        with open(LOG_FILE, 'r', encoding='utf-8', errors='replace') as f:
            f.seek(0, 2)
            size = f.tell()
            start = max(0, size - 512000)  # Only read last 500KB
            f.seek(start)
            for line in f:
                if 'Pool timeout' not in line:
                    continue
                try:
                    ts_str = line[:23].strip()
                    ts = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S,%f")
                    ts = ts.replace(tzinfo=timezone.utc)
                    if ts >= cutoff:
                        count += 1
                except (ValueError, IndexError):
                    count += 1  # Can't parse timestamp, count conservatively
    except OSError:
        pass

    return count


def restart_gateway():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 连接池超时达到阈值，正在重启 Gateway...")
    try:
        _flags = subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
        subprocess.Popen(
            [str(HERMES_BIN), "gateway", "run"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            creationflags=_flags
        )
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Gateway 重启命令已发送")
        return True
    except OSError as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Gateway 重启失败: {e}")
        return False


def main():
    state = load_state()
    now = time.time()

    # 冷却期检查
    if now - state.get("last_restart_time", 0) < COOLDOWN_SECONDS:
        return  # 冷却期内，静默退出

    pool_timeout_count = count_recent_pool_timeouts()

    if pool_timeout_count >= THRESHOLD:
        print(f"[检测] 最近{SCAN_MINUTES}分钟内 Pool timeout 共 {pool_timeout_count} 次（阈值 {THRESHOLD}）")
        print(f"[诊断] Vortex 代理连接池耗尽，Telegram 消息无法发送")

        success = restart_gateway()
        if success:
            state["last_restart_time"] = now
            state["last_restart_count"] = state.get("last_restart_count", 0) + 1
            save_state(state)
            print(f"[完成] Gateway 重启成功，冷却 {COOLDOWN_SECONDS}s 防止重复触发")
    # 阈值未达到，静默退出


if __name__ == "__main__":
    main()