#!/usr/bin/env python3
"""飞书轮询守护进程看门狗 v2 - 秒收秒回版
Monitors feishu_poll_daemon.py, auto-restarts on crash.
Circuit breaker: 3 consecutive crashes -> 30min cooldown + Feishu alert.

Run:
  pythonw feishu_poll_watcher.py          # background (Windows)
  python feishu_poll_watcher.py           # foreground (debug)
"""
import subprocess, time, logging, json, os, sys, urllib.request

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DAEMON_SCRIPT = os.path.join(SCRIPT_DIR, "feishu_poll_daemon.py")
PID_FILE = os.path.join(SCRIPT_DIR, "feishu_poll_daemon.pid")
STATE_FILE = os.path.join(SCRIPT_DIR, "feishu_poll_watcher_state.json")
LOG_FILE = os.path.join(SCRIPT_DIR, "feishu_poll_watcher.log")

CHECK_INTERVAL = 30
CRASH_COOLDOWN = 5
MAX_CRASHES = 3
CIRCUIT_BREAKER_TIME = 1800

# Feishu alert config
APP_ID = "cli_aaa7c346a6385cba"
APP_SECRET="oSA1...T_ID = "oc_1a238a6016460ec51c602048a88aca70"

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
log = logging.getLogger()


def get_feishu_token():
    try:
        data = json.dumps({"app_id": APP_ID, "app_secret": APP_SECRET}).encode()
        req = urllib.request.Request(
            "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
            data=data, headers={"Content-Type": "application/json"}
        )
        resp = json.loads(urllib.request.urlopen(req, timeout=10).read())
        return resp.get("tenant_access_token", "")
    except Exception as e:
        log.error(f"Token fetch failed: {e}")
        return ""


def send_feishu_alert(message):
    token = get_feishu_token()
    if not token:
        log.error("Feishu alert failed: no token")
        return False
    try:
        content = json.dumps({"text": f"⚠️ 看门狗警报: {message}"}, ensure_ascii=False)
        send_data = json.dumps({
            "receive_id": CHAT_ID,
            "msg_type": "text",
            "content": content
        }, ensure_ascii=False).encode()
        req = urllib.request.Request(
            "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id",
            data=send_data,
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        )
        resp = json.loads(urllib.request.urlopen(req, timeout=10).read())
        log.info(f"Feishu alert sent: code={resp.get('code')}")
        return True
    except Exception as e:
        log.error(f"Feishu alert failed: {e}")
        return False


def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {"crash_count": 0, "circuit_open_until": 0, "last_alert_sent": 0}


def save_state(state):
    try:
        with open(STATE_FILE, "w") as f:
            json.dump(state, f)
    except Exception as e:
        log.error(f"State save failed: {e}")


def is_daemon_running():
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE, "r") as f:
                pid = int(f.read().strip())
            try:
                os.kill(pid, 0)
                return True, pid
            except (ProcessLookupError, PermissionError):
                os.remove(PID_FILE)
        except (ValueError, FileNotFoundError):
            pass
    try:
        result = subprocess.run(["ps", "aux"], capture_output=True, text=True, timeout=10)
        for line in result.stdout.splitlines():
            if "feishu_poll_daemon" in line and "grep" not in line and "watchdog" not in line:
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        return True, int(parts[1])
                    except ValueError:
                        pass
    except Exception:
        pass
    return False, None


def start_daemon():
    log.info("Starting feishu_poll_daemon.py ...")
    try:
        if sys.platform == "win32":
            proc = subprocess.Popen(
                [sys.executable, DAEMON_SCRIPT],
                creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS,
                cwd=SCRIPT_DIR,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        else:
            proc = subprocess.Popen(
                [sys.executable, DAEMON_SCRIPT],
                cwd=SCRIPT_DIR,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )
        log.info(f"Daemon started, PID={proc.pid}")
        with open(PID_FILE, "w") as f:
            f.write(str(proc.pid))
        return proc.pid
    except Exception as e:
        log.error(f"Start failed: {e}")
        return None


def main():
    log.info("=" * 50)
    log.info("Feishu poll watcher v2 started (instant alert + circuit breaker)")
    log.info(f"Interval: {CHECK_INTERVAL}s, crash threshold: {MAX_CRASHES}, cooldown: {CIRCUIT_BREAKER_TIME}s")
    log.info("=" * 50)

    state = load_state()

    while True:
        now = time.time()

        if now < state.get("circuit_open_until", 0):
            remaining = int(state["circuit_open_until"] - now)
            log.info(f"Circuit open, cooldown remaining: {remaining}s")
            time.sleep(min(remaining, 60))
            continue

        running, pid = is_daemon_running()

        if not running:
            log.info("Daemon not running, preparing restart")
            state["crash_count"] = state.get("crash_count", 0) + 1

            if state["crash_count"] >= MAX_CRASHES:
                alert_msg = f"Daemon crashed {MAX_CRASHES} times, entering {CIRCUIT_BREAKER_TIME}s circuit breaker!"
                log.warning(alert_msg)
                if now - state.get("last_alert_sent", 0) > 600:
                    if send_feishu_alert(alert_msg):
                        state["last_alert_sent"] = now
                state["circuit_open_until"] = now + CIRCUIT_BREAKER_TIME
                save_state(state)
                continue

            log.info(f"Crash count: {state['crash_count']}/{MAX_CRASHES}")
            time.sleep(CRASH_COOLDOWN)
            new_pid = start_daemon()
            if new_pid is None:
                log.error("Start failed, continuing monitoring")
                if now - state.get("last_alert_sent", 0) > 600:
                    if send_feishu_alert("Daemon start failed! Check logs"):
                        state["last_alert_sent"] = now
        else:
            if state.get("crash_count", 0) > 0:
                log.info(f"Daemon running (PID={pid}), resetting crash count")
                state["crash_count"] = 0

        save_state(state)
        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log.info("Watcher terminated by user")
    except Exception as e:
        log.critical(f"Watcher crashed: {e}")
        send_feishu_alert(f"Watcher crashed: {str(e)[:100]}")
        sys.exit(1)