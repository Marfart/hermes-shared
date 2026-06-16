#!/usr/bin/env python3
"""
Weixin 连接智能看门狗 v1.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
自动检测 Weixin 断联 → 诊断 → 修复 → 仅在修复失败时通知用户

工作模式:
  - tail gateway.log 实时检测 Weixin 错误
  - DNS 缓存刷新、网络检测、Gateway 重启三级修复
  - 状态文件防重复通知
  - 每 2 分钟 cron 触发（no_agent=True → 静默输出）

状态文件: %LOCALAPPDATA%/hermes/memories/脚本缓存/weixin_health_state.json
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# ─── 路径 ───────────────────────────────────────────────
_local_appdata = os.environ.get("LOCALAPPDATA", 
    os.path.join(os.environ["USERPROFILE"], "AppData", "Local"))
HERMES_HOME = Path(os.environ.get("HERMES_HOME", 
    os.path.join(_local_appdata, "hermes")))
MEMORIES = Path(_local_appdata) / "hermes" / "memories" / "脚本缓存"
STATE_FILE = MEMORIES / "weixin_health_state.json"
GATEWAY_LOG = HERMES_HOME / "logs" / "gateway.log"
ERROR_LOG = HERMES_HOME / "logs" / "errors.log"

# ─── 配置 ───────────────────────────────────────────────
MAX_SILENT_MINUTES = 5
RECOVERY_COOLDOWN_SEC = 300
MAX_RESTARTS_PER_HOUR = 3

WEIXIN_HOST = "ilinkai.weixin.qq.com"
WEIXIN_ALT_HOSTS = [
    "ilinkai.weixin.qq.com",
    "novac2c.cdn.weixin.qq.com",
    "wx.qlogo.cn",
]

# ─── 状态管理 ──────────────────────────────────────────

def load_state() -> dict:
    defaults = {
        "last_healthy": 0.0,
        "last_error": 0.0,
        "last_alert": 0.0,
        "last_restart": 0.0,
        "restart_count_hour": 0,
        "restart_hour_bucket": 0,
        "consecutive_failures": 0,
        "errors_today": [],
        "auto_fixed_count": 0,
    }
    if STATE_FILE.exists():
        try:
            data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
            for k, v in defaults.items():
                data.setdefault(k, v)
            return data
        except (json.JSONDecodeError, OSError):
            pass
    return defaults

def save_state(state: dict) -> None:
    MEMORIES.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(
        json.dumps(state, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

def now_ts() -> float:
    return time.time()

# ─── 诊断工具 ──────────────────────────────────────────

def run_cmd(cmd: list, timeout: int = 10) -> tuple:
    try:
        r = subprocess.run(
            cmd, capture_output=True, text=False, timeout=timeout
        )
        ok = r.returncode == 0
        stdout = r.stdout.decode("gbk", errors="replace") if r.stdout else ""
        stderr = r.stderr.decode("gbk", errors="replace") if r.stderr else ""
        out = stdout + ("\n" + stderr if stderr else "")
        return ok, out.strip()
    except subprocess.TimeoutExpired:
        return False, "timeout"
    except FileNotFoundError:
        return False, "command not found"
    except Exception as e:
        return False, str(e)

def check_ping(host: str = WEIXIN_HOST) -> bool:
    ok, _ = run_cmd(["ping", "-n", "1", "-w", "3000", host])
    return ok

def check_dns(host: str = WEIXIN_HOST) -> bool:
    ok, out = run_cmd(["nslookup", host])
    if ok and "Address" in out:
        return True
    try:
        import socket
        socket.getaddrinfo(host, 443)
        return True
    except Exception:
        return False

def check_https(host: str = WEIXIN_HOST) -> bool:
    try:
        import ssl
        import socket as sockmod
        ctx = ssl.create_default_context()
        ctx.check_hostname = True
        ctx.verify_mode = ssl.CERT_REQUIRED
        sock = sockmod.create_connection((host, 443), timeout=8)
        ssock = ctx.wrap_socket(sock, server_hostname=host)
        ssock.close()
        return True
    except Exception:
        return False

def flush_dns() -> bool:
    ok, _ = run_cmd(["ipconfig", "/flushdns"])
    if ok:
        time.sleep(1)
    return ok

def restart_gateway() -> bool:
    ok, out = run_cmd(["hermes", "gateway", "restart"], timeout=15)
    if ok:
        time.sleep(5)
        # 验证网关状态
        ok2, _ = run_cmd(["hermes", "gateway", "status"], timeout=10)
        return ok2
    return False

def get_recent_weixin_errors(log_path: Path, minutes: int = 5) -> list:
    if not log_path.exists():
        return []
    errors = []
    try:
        text = log_path.read_text(encoding="utf-8", errors="replace")
        for line in text.splitlines():
            if "weixin" not in line.lower():
                continue
            if any(kw in line.lower() for kw in [
                "error", "fail", "timeout", "disconnect", "rate limit",
                "ssl", "certificate", "poll error",
            ]):
                errors.append(line.strip())
        return errors[-10:]
    except Exception:
        return []

def is_weixin_connected() -> bool:
    ok, out = run_cmd(["hermes", "gateway", "status"], timeout=10)
    if not ok:
        return False
    return "weixin" in out.lower() and "connected" in out.lower()

def check_network_basics() -> dict:
    """Check internet connectivity broadly."""
    result = {}
    # Google DNS
    ok, _ = run_cmd(["ping", "-n", "1", "-w", "3000", "8.8.8.8"])
    result["internet"] = ok
    # DNS resolution
    result["dns"] = check_dns()
    # SSL to iLink
    result["ssl_weixin"] = check_https(WEIXIN_HOST)
    return result

# ─── 修复链 ─────────────────────────────────────────────

LEVEL_NAMES = ["", "DNS刷新", "SSL证书刷新", "Gateway重启"]

def attempt_auto_heal(state: dict) -> tuple:
    """
    修复链：逐级尝试，成功即停。
    Returns (fixed: bool, action_taken: str, level: int)
    """
    now = now_ts()

    # Level 1: Flush DNS
    if flush_dns():
        time.sleep(2)
        if check_https():
            state["auto_fixed_count"] = state.get("auto_fixed_count", 0) + 1
            return True, "DNS刷新修复成功", 1

    # Level 2: Check alt hosts, update certifi
    for alt_host in WEIXIN_ALT_HOSTS:
        if check_https(alt_host):
            time.sleep(3)
            if check_https():
                state["auto_fixed_count"] = state.get("auto_fixed_count", 0) + 1
                return True, "备用Host可达后主Host恢复", 2
            break

    # Check if it's SSL cert issue specifically
    try:
        import socket as sockmod, ssl
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        sock = sockmod.create_connection((WEIXIN_HOST, 443), timeout=8)
        ssock = ctx.wrap_socket(sock, server_hostname=WEIXIN_HOST)
        ssock.close()
        # TLS works but SSL verify fails -> update certifi
        ok, _ = run_cmd(["pip", "install", "--upgrade", "certifi"], timeout=30)
        if ok:
            if check_https():
                state["auto_fixed_count"] = state.get("auto_fixed_count", 0) + 1
                return True, "certifi证书库更新修复", 2
    except Exception:
        pass

    # Level 3: Restart gateway (with rate limiting)
    hour_bucket = int(now // 3600)
    if state.get("restart_hour_bucket") != hour_bucket:
        state["restart_hour_bucket"] = hour_bucket
        state["restart_count_hour"] = 0

    if state.get("restart_count_hour", 0) >= MAX_RESTARTS_PER_HOUR:
        return (False,
                "已达每小时最大重启次数({})，等待自动恢复".format(MAX_RESTARTS_PER_HOUR),
                3)

    if restart_gateway():
        state["restart_count_hour"] = state.get("restart_count_hour", 0) + 1
        state["last_restart"] = now
        state["auto_fixed_count"] = state.get("auto_fixed_count", 0) + 1
        return True, "Gateway重启成功", 3
    else:
        return (False, "Gateway重启失败，需人工干预", 3)

# ─── 主逻辑 ─────────────────────────────────────────────

def main():
    state = load_state()
    now = now_ts()

    # Step 1: 检查当前连接
    net = check_network_basics()
    host_ok = net.get("ssl_weixin", False)

    if host_ok:
        # 连接正常
        state["last_healthy"] = now
        state["consecutive_failures"] = 0
        save_state(state)
        return  # 静默

    # Step 2: 连接异常
    state["last_error"] = now
    state["consecutive_failures"] = state.get("consecutive_failures", 0) + 1

    # 记录今日错误
    errors_today = state.get("errors_today", [])
    errors_today.append({
        "time": datetime.now().strftime("%H:%M:%S"),
        "consecutive": state["consecutive_failures"],
    })
    if len(errors_today) > 50:
        errors_today = errors_today[-50:]
    state["errors_today"] = errors_today

    # Step 3: 连续失败 >= 2 才触发修复链（一次可能是瞬断）
    if state["consecutive_failures"] < 2:
        save_state(state)
        return

    # Step 4: 运行修复链
    fixed, action, level = attempt_auto_heal(state)

    if fixed:
        state["consecutive_failures"] = 0
        state["last_healthy"] = now
        save_state(state)
        return  # 静默修复

    # Step 5: 修复失败 -> 仅断联超过5分钟+冷却期过才报警
    time_since_last_alert = now - state.get("last_alert", 0)
    time_since_last_healthy = now - state.get("last_healthy", now)

    need_alert = (
        time_since_last_alert > RECOVERY_COOLDOWN_SEC
        and time_since_last_healthy > MAX_SILENT_MINUTES * 60
    )

    if need_alert:
        state["last_alert"] = now
        state["errors_today"] = []
        save_state(state)

        # 诊断信息
        gw_status = is_weixin_connected()
        recent_logs = get_recent_weixin_errors(GATEWAY_LOG)

        out = []
        out.append("")
        out.append("=" * 50)
        out.append("⚠️  Weixin 断联报告 (自动修复失败)")
        out.append("=" * 50)
        out.append("时间: {}".format(datetime.now().strftime("%m-%d %H:%M:%S")))
        out.append("已尝试: Level {} ({})".format(level, LEVEL_NAMES[level]))
        out.append("结果: {}".format(action))
        out.append("---")
        out.append("网络诊断:")
        out.append("  Ping 8.8.8.8:   {}".format("✓" if net.get("internet") else "✗"))
        out.append("  DNS解析:         {}".format("✓" if net.get("dns") else "✗"))
        out.append("  SSL " + WEIXIN_HOST + ":    {}".format("✓" if net.get("ssl_weixin") else "✗"))
        out.append("  Gateway状态:     {}".format("已连接" if gw_status else "断开"))
        out.append("---")
        if recent_logs:
            out.append("最近网关错误:")
            for e in recent_logs[-5:]:
                out.append("  " + e)
        out.append("---")
        out.append("建议: ")
        if not net.get("internet"):
            out.append("  - 请检查网络连接(WiFi/网线)")
        elif not net.get("dns"):
            out.append("  - DNS解析异常，检查网络设置")
        else:
            out.append("  - 腾讯iLink服务端临时故障，等待自动恢复")
            out.append("  - 如持续30分钟以上，请手动: hermes gateway restart")
        out.append("=" * 50)

        print("\n".join(out))
    else:
        save_state(state)


if __name__ == "__main__":
    main()