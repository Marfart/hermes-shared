#!/usr/bin/env python3
"""
Smart Watchdog v4+ — 智能自愈 + DNS/SSL修复 + 静默修复 + 去重通知
==================================================
- 读 gateway_state.json + gateway.log → 智能诊断
- 新增: DNS缓存刷新 + certifi更新 (SSL修复)
- Tier 0 (静默自愈): 微信限流 → 什么都不发
- Tier 1 (静默修复): 临时网络闪断 → DNS刷新 → certifi升级 → 自动重启，不通知
- Tier 2 (限频通知): 代理/VPN挂了or持续异常 → 每类型每30分钟最多报一次
- 彻底修好了 → 不发通知（不烦你）
"""

import json, time, subprocess, sys, os
from pathlib import Path
from datetime import datetime, timezone

HERMES_HOME = Path.home() / "AppData" / "Local" / "hermes"
STATE_FILE = HERMES_HOME / "gateway_state.json"
LOG_FILE = HERMES_HOME / "logs" / "gateway.log"
STATUS_CACHE = HERMES_HOME / "scripts" / ".watchdog_status.json"

# =====================================================================
# 持久化状态 — 用来去重通知
# =====================================================================
def load_status():
    if STATUS_CACHE.exists():
        try:
            return json.loads(STATUS_CACHE.read_text())
        except:
            pass
    return {
        "last_notified": {},       # error_type → timestamp (UTC秒)
        "cooldown_sec": 1800,      # 同一类型30分钟内不重发
        "consecutive_restarts": 0, # 连续重启次数
        "last_restart_at": 0,
        "last_healthy_state": None, # 上一次看到的状态
        "incident_active": {},      # error_type → True/False
    }

def save_status(s):
    STATUS_CACHE.parent.mkdir(parents=True, exist_ok=True)
    STATUS_CACHE.write_text(json.dumps(s, indent=2))

# =====================================================================
# 工具函数
# =====================================================================
def now_str():
    return datetime.now().strftime("%H:%M:%S")

def now_ts():
    return time.time()

def is_process_alive(pid):
    if not pid:
        return False
    try:
        r = subprocess.run(["tasklist", "/fi", f"PID eq {pid}", "/nh", "/fo", "csv"],
                           capture_output=True, text=True, timeout=5)
        return str(pid) in r.stdout
    except:
        return False

def read_state():
    if not STATE_FILE.exists():
        return None
    try:
        return json.loads(STATE_FILE.read_text())
    except:
        return None

def scan_log_for_errors(lines=40):
    """从gateway.log尾部找最近的关键错误"""
    if not LOG_FILE.exists():
        return []
    try:
        text = LOG_FILE.read_text(encoding="utf-8", errors="replace")
    except:
        return []
    log_lines = text.splitlines()
    tail = log_lines[-lines:] if len(log_lines) > lines else log_lines
    
    errors = []
    for line in reversed(tail):
        ll = line.lower()
        ts = line[:19] if len(line) >= 19 else ""
        
        # 代理/VPN级别 — 两个平台同时出问题
        if ("telegram" in ll and "wei xin" not in ll
            and ("connecterror" in ll.replace(" ", ""))):
            if "telegram" in ll and "weixin" not in ll:
                # 单独Telegram ConnectError
                errors.append(("telegram_connect_error", ts, line.strip()))
                continue
            
        # Telegram 网络错误
        if "telegram" in ll and "remoteprotocolerror" in ll.replace(" ",""):
            errors.append(("telegram_protocol_error", ts, line.strip()))
            continue
        if "telegram" in ll and "connecterror" in ll.replace(" ",""):
            errors.append(("telegram_connect_error", ts, line.strip()))
            continue
        if "telegram" in ll and "send_path_degraded" in ll:
            errors.append(("telegram_send_degraded", ts, line.strip()))
            continue
        if "telegram" in ll and "failed to deliver" in ll:
            errors.append(("telegram_delivery_failed", ts, line.strip()))
            continue
            
        # 微信错误
        if "weixin" in ll and "rate limited" in ll:
            # 别再烦用户了
            errors.append(("weixin_rate_limited", ts, line.strip()))
            continue
        if "weixin" in ll and "sslcertverification" in ll.replace(" ",""):
            errors.append(("weixin_ssl_error", ts, line.strip()))
            continue
        if "weixin" in ll and "cannot connect to host" in ll:
            errors.append(("weixin_connect_error", ts, line.strip()))
            continue
            
        # Gateway 进程异常
        if "error" in ll and "traceback" in ll:
            errors.append(("gateway_crash", ts, line.strip()))
            continue
    
    return errors

def diagnose_cause(state_data, errors):
    """智能诊断根本原因"""
    if state_data is None:
        return "gateway_state_missing", "Gateway 状态文件不存在"
    
    platforms = state_data.get("platforms", {})
    tg = platforms.get("telegram", {})
    wx = platforms.get("weixin", {})
    discord = platforms.get("discord", {})
    pid = state_data.get("pid")
    gw_state = state_data.get("gateway_state", "")
    
    tg_state = tg.get("state", "unknown")
    wx_state = wx.get("state", "unknown")
    
    # 提取最近错误类型
    error_types = [e[0] for e in errors]
    
    # ===== 分类诊断 =====
    
    # 1. Gateway 进程没了
    if not is_process_alive(pid) and pid:
        # 检查代理状态
        proxy_ok = check_proxy()
        if not proxy_ok:
            return "proxy_down", "代理/VPN 断连，Gateway 进程已退出，需检查代理"
        return "gateway_exited", f"Gateway 进程 (PID {pid}) 已退出"
    
    # 2. 两个平台同时断 — 极可能是代理问题
    both_down = tg_state != "connected" and wx_state != "connected"
    if both_down and gw_state != "stopped":
        proxy_ok = check_proxy()
        if not proxy_ok:
            return "proxy_down", "代理/VPN 断连，两个平台同时断线"
        return "double_disconnect", "两个平台同时断开 (代理可能不稳定)"
    
    # 3. 微信 SSL 问题 — 代理拦截了证书
    if any("ssl" in e for e in error_types):
        return "ssl_proxy_intercept", "代理拦截微信 SSL 证书"
    
    # 4. 微信限流 — 最常见的静默问题
    if "weixin_rate_limited" in error_types and wx_state != "connected":
        return "weixin_rate_limited", "微信消息发送太频繁被限流"
    
    # 5. 单独 Telegram 问题
    if tg_state != "connected" and wx_state == "connected":
        if "telegram_protocol_error" in error_types:
            return "telegram_protocol_error", "Telegram 服务器断开连接"
        if "telegram_connect_error" in error_types:
            return "telegram_connect_error", "连不上 Telegram 服务器"
        if "telegram_send_degraded" in error_types:
            return "telegram_send_degraded", "Telegram 发送通道不稳定"
        return "telegram_state_abnormal", f"Telegram 状态异常 ({tg_state})"
    
    # 6. 单独微信问题
    if wx_state != "connected" and tg_state == "connected":
        if "weixin_rate_limited" in error_types:
            return "weixin_rate_limited", "微信消息发送太频繁被限流"
        if "weixin_connect_error" in error_types:
            return "weixin_connect_error", "连不上微信服务器"
        return "weixin_state_abnormal", f"微信状态异常 ({wx_state})"
    
    return None, "不明异常"

def check_proxy():
    """检查代理是否活着"""
    try:
        r = subprocess.run(
            ["curl", "-s", "--connect-timeout", "3", "-o", "/dev/null", "-w", "%{http_code}",
             "http://127.0.0.1:7897"],
            capture_output=True, text=True, timeout=8
        )
        code = r.stdout.strip()
        return code.isdigit() and int(code) >= 200
    except:
        return False

def check_internet():
    """检查外网连通性（绕过代理直测）"""
    try:
        r = subprocess.run(
            ["curl", "-s", "--connect-timeout", "5", "--noproxy", "*",
             "-o", "/dev/null", "-w", "%{http_code}", 
             "http://114.114.114.114"],
            capture_output=True, text=True, timeout=8
        )
        return r.stdout.strip() == "000"  # 000也说明有网络
    except:
        return False

def flush_dns():
    """Windows DNS缓存刷新"""
    try:
        subprocess.run(["ipconfig", "/flushdns"],
                       capture_output=True, timeout=10)
        return True
    except:
        return False

def update_certifi():
    """更新certifi证书包解决SSL证书问题"""
    try:
        # 找到hermes的venv里的pip
        pip_bin = str(HERMES_HOME / "hermes-agent" / "venv" / "Scripts" / "pip")
        if Path(pip_bin).exists():
            r = subprocess.run([pip_bin, "install", "--upgrade", "certifi"],
                               capture_output=True, timeout=30)
            return r.returncode == 0
        # fallback
        r = subprocess.run(["pip", "install", "--upgrade", "certifi"],
                           capture_output=True, timeout=30)
        return r.returncode == 0
    except:
        return False

def restart_gateway():
    subprocess.run(["taskkill", "/f", "/im", "hermes"], capture_output=True, timeout=5)
    time.sleep(2)
    # 清理所有残余
    try:
        r = subprocess.run(["tasklist", "/fo", "csv", "/nh"],
                           capture_output=True, text=True, timeout=10)
        for line in r.stdout.split("\n"):
            if "gateway" in line.lower():
                parts = line.split(",")
                if len(parts) >= 2:
                    pid = parts[1].strip().strip('"')
                    if pid.isdigit():
                        subprocess.run(["taskkill", "/f", "/pid", pid],
                                       capture_output=True, timeout=5)
    except:
        pass
    time.sleep(2)
    
    hermes_bin = str(HERMES_HOME / "hermes-agent" / "venv" / "Scripts" / "hermes")
    if not Path(hermes_bin).exists():
        hermes_bin = "hermes"
    
    subprocess.Popen(
        [hermes_bin, "gateway", "run"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW
    )

def wait_for_reconnect(timeout=50):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            data = json.loads(STATE_FILE.read_text())
            tg = data.get("platforms", {}).get("telegram", {}).get("state", "")
            wx = data.get("platforms", {}).get("weixin", {}).get("state", "")
            if tg == "connected" and wx == "connected":
                return True, "全部恢复"
            if tg == "connected":
                return True, f"Telegram已恢复，微信: {wx}"
            if wx == "connected":
                return True, f"微信已恢复，Telegram: {tg}"
        except:
            pass
        time.sleep(3)
    return False, "超时未恢复"


def should_notify(error_type, status):
    """是否应该通知用户 — 去重逻辑"""
    last = status["last_notified"].get(error_type, 0)
    cooldown = status["cooldown_sec"]
    
    # Tier 0: 微信限流 — 永远静默
    if error_type in ("weixin_rate_limited",):
        return False, "T0-静默自愈"
    
    # Tier 1: 临时性网络问题 — 静默重启
    if error_type in ("telegram_protocol_error", "telegram_send_degraded",
                      "gateway_exited", "telegram_state_abnormal",
                      "weixin_state_abnormal", "ssl_proxy_intercept"):
        # 连续重启超过3次才通知
        if status["consecutive_restarts"] >= 3:
            if now_ts() - last > cooldown:
                return True, "T1-多次重启仍异常"
            return False, "T1-静默重启(限频中)"
        return False, "T1-静默重启"
    
    # Tier 2: 需要用户介入的问题
    if now_ts() - last > cooldown:
        return True, "T2-需要用户介入"
    return False, "T2-限频中"


def run():
    status = load_status()
    state_data = read_state()
    
    if state_data is None:
        # 状态文件都读不了，必须修
        restart_gateway()
        if wait_for_reconnect()[0]:
            # 修好了，不发通知
            status["consecutive_restarts"] = 0
            save_status(status)
            return
        print("🚨 gateway_state.json 丢失，已自动修复中")
        return
    
    platforms = state_data.get("platforms", {})
    tg = platforms.get("telegram", {})
    wx = platforms.get("weixin", {})
    pid = state_data.get("pid")
    
    tg_state = tg.get("state", "unknown")
    wx_state = wx.get("state", "unknown")
    
    # 当前健康状态快照
    current_state = (tg_state, wx_state, is_process_alive(pid))
    
    # ===== 状态没变化且都正常 → 静默 =====
    if current_state == status.get("last_healthy_state"):
        # 确认是真的正常
        if tg_state == "connected" and wx_state == "connected":
            return  # 一直健康，不发
    
    status["last_healthy_state"] = current_state
    
    # ===== 一切正常 → 静默，重置计数器 =====
    if tg_state == "connected" and wx_state == "connected" and is_process_alive(pid):
        if status["consecutive_restarts"] > 0:
            # 修好了，重置
            status["consecutive_restarts"] = 0
            status["incident_active"] = {}
            save_status(status)
        return
    
    # ===== 有问题 — 扫描日志诊断 =====
    errors = scan_log_for_errors()
    cause_type, cause_msg = diagnose_cause(state_data, errors)
    
    if cause_type is None:
        # 诊断不出就等下次
        return
    
    # ===== 决定是否通知 =====
    notify, tier = should_notify(cause_type, status)
    
    # ===== 执行修复（DNS刷新 + SSL证书更新 + 重启链条）=====
    # 先试DNS刷新（最快，不需要重启）
    if cause_type in ("weixin_connect_error", "weixin_ssl_error",
                      "telegram_connect_error", "telegram_protocol_error",
                      "double_disconnect", "ssl_proxy_intercept"):
        flush_dns()
        time.sleep(1)
        # SSL问题时升级certifi
        if "ssl" in cause_type:
            update_certifi()
            time.sleep(1)

    # 再试重启
    restart_gateway()
    status["consecutive_restarts"] += 1
    status["last_restart_at"] = now_ts()
    
    recovered, recovery_msg = wait_for_reconnect()
    
    if recovered:
        # 修好了
        if tier == "T2-需要用户介入":
            # 这个仍需通知（但修好了，就不再发了）
            if notify:
                print(f"🛠️ `{cause_msg}` — 已自动修复")
                print(f"   (`{cause_type}` → {recovery_msg})")
                status["last_notified"][cause_type] = now_ts()
        else:
            # T0/T1 静默修复 → 不通知
            pass  # 完全静默
        status["consecutive_restarts"] = 0
    else:
        # 没修好
        if notify:
            print(f"🚨 `{cause_msg}`")
            if cause_type == "proxy_down":
                print(f"   ⚡ 代理/VPN 可能需要检查一下")
            elif cause_type == "telegram_connect_error":
                if status["consecutive_restarts"] >= 3:
                    print(f"   ⚡ 多次自动修复失败，可能需要检查代理")
                else:
                    print(f"   ⚡ 下次 cron 再试自动修复")
            else:
                print(f"   ⚡ 下次 cron 再试自动修复")
            status["last_notified"][cause_type] = now_ts()
            status["incident_active"][cause_type] = True
        else:
            # 静默 — 缓存异常但不出声
            status["incident_active"][cause_type] = True
    
    save_status(status)


if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        # 看门狗自身异常不出声
        sys.stderr.write(f"watchdog error: {e}\n")