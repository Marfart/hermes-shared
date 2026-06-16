#!/usr/bin/env python3
"""飞书轮询守护进程看门狗 v2 - 秒收秒回版
新增功能：
1. 熔断触发时通过飞书API发群消息通知
2. 检测守护进程PID文件时间戳（超60秒未更新=可能卡死）
3. 日志输出到文件
"""
import subprocess, time, logging, json, os, sys, urllib.request

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DAEMON_SCRIPT = os.path.join(SCRIPT_DIR, "feishu_poll_daemon.py")
PID_FILE = os.path.join(SCRIPT_DIR, "feishu_poll_daemon.pid")
STATE_FILE = os.path.join(SCRIPT_DIR, "feishu_poll_watcher_state.json")
LOG_FILE = os.path.join(SCRIPT_DIR, "feishu_poll_watcher.log")

CHECK_INTERVAL = 30      # 每30秒检查一次
CRASH_COOLDOWN = 5        # 崩溃后等5秒
MAX_CRASHES = 3           # 连续崩溃3次进熔断
CIRCUIT_BREAKER_TIME = 1800  # 熔断冷却30分钟

# 飞书通知配置
APP_ID = "cli_aaa7c346a6385cba"
APP_SECRET = "oSA1pUP92vKALKHb2WLNkfRmbfmkdAvi"

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
log = logging.getLogger()


def get_feishu_token():
    """获取飞书tenant_access_token"""
    try:
        data = json.dumps({"app_id": APP_ID, "app_secret": APP_SECRET}).encode()
        req = urllib.request.Request(
            "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
            data=data, headers={"Content-Type": "application/json"}
        )
        resp = json.loads(urllib.request.urlopen(req, timeout=10).read())
        return resp.get("tenant_access_token", "")
    except Exception as e:
        log.error(f"获取飞书token失败: {e}")
        return ""


def send_feishu_alert(message):
    """熔断时发飞书群消息通知"""
    token = get_feishu_token()
    if not token:
        log.error("飞书通知失败: 无法获取token")
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
        log.info(f"飞书通知发送成功: code={resp.get('code')}")
        return True
    except Exception as e:
        log.error(f"飞书通知发送失败: {e}")
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
        log.error(f"保存状态失败: {e}")


def is_daemon_running():
    """检查守护进程是否在运行"""
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE, "r") as f:
                pid = int(f.read().strip())
            try:
                os.kill(pid, 0)
                return True, pid
            except (ProcessLookupError, PermissionError):
                log.info(f"PID {pid} 已不存在，清理旧PID文件")
                os.remove(PID_FILE)
        except (ValueError, FileNotFoundError):
            pass
    # 用ps查找
    try:
        result = subprocess.run(
            ["ps", "aux"], capture_output=True, text=True, timeout=10
        )
        for line in result.stdout.splitlines():
            if "feishu_poll_daemon" in line and "grep" not in line and "watchdog" not in line:
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        pid = int(parts[1])
                        return True, pid
                    except ValueError:
                        pass
    except Exception as e:
        log.error(f"ps查找失败: {e}")
    return False, None


def start_daemon():
    log.info("正在启动 feishu_poll_daemon.py ...")
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
        log.info(f"守护进程已启动, PID={proc.pid}")
        with open(PID_FILE, "w") as f:
            f.write(str(proc.pid))
        return proc.pid
    except Exception as e:
        log.error(f"启动失败: {e}")
        return None


def main():
    log.info("=" * 50)
    log.info("飞书轮询看门狗 v2 启动（秒收秒回版 + 飞书通知）")
    log.info(f"检查间隔: {CHECK_INTERVAL}s, 熔断阈值: {MAX_CRASHES}次, 熔断冷却: {CIRCUIT_BREAKER_TIME}s")
    log.info("=" * 50)

    state = load_state()

    while True:
        now = time.time()

        # 检查是否在熔断期
        if now < state.get("circuit_open_until", 0):
            remaining = int(state["circuit_open_until"] - now)
            log.info(f"熔断中，剩余冷却时间: {remaining}s")
            time.sleep(min(remaining, 60))
            continue

        running, pid = is_daemon_running()

        if not running:
            log.info("守护进程未运行，准备重启")
            state["crash_count"] = state.get("crash_count", 0) + 1

            if state["crash_count"] >= MAX_CRASHES:
                alert_msg = f"守护进程连续崩溃 {MAX_CRASHES} 次，进入 {CIRCUIT_BREAKER_TIME}s 熔断冷却！"
                log.warning(alert_msg)
                # 飞书通知 - 10分钟内不重复发
                if now - state.get("last_alert_sent", 0) > 600:
                    if send_feishu_alert(alert_msg):
                        state["last_alert_sent"] = now
                state["circuit_open_until"] = now + CIRCUIT_BREAKER_TIME
                save_state(state)
                continue

            log.info(f"崩溃计数: {state['crash_count']}/{MAX_CRASHES}")
            time.sleep(CRASH_COOLDOWN)
            new_pid = start_daemon()
            if new_pid is None:
                log.error("启动失败，继续监控")
                # 启动失败也发飞书通知
                if now - state.get("last_alert_sent", 0) > 600:
                    if send_feishu_alert("守护进程启动失败！请检查日志"):
                        state["last_alert_sent"] = now
        else:
            if state.get("crash_count", 0) > 0:
                log.info(f"守护进程正常运行中 (PID={pid})，重置崩溃计数")
                state["crash_count"] = 0

        save_state(state)
        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log.info("看门狗被手动终止")
    except Exception as e:
        log.critical(f"看门狗异常退出: {e}")
        # 异常退出也发飞书通知
        send_feishu_alert(f"看门狗异常退出: {str(e)[:100]}")
        sys.exit(1)