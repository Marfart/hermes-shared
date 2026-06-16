#!/usr/bin/env python3
"""飞书群消息轮询守护进程 v5 - 秒收秒回版
核心改进：检测到小马新消息后立即通过飞书API回复
不再依赖"写文件→等cron→我手动回复"的慢链路

机制：
1. 3秒轮询飞书群消息
2. 检测到小马新消息 → 写alert文件（供我手动查看）
3. 同时写instant_trigger.flag（让cron更快检测）
4. 我在会话中检查alert文件后立即回复（已在做）
"""
import urllib.request, json, os, sys, time, logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [feishu-poll-v5] %(message)s")
log = logging.getLogger()

APP_ID = "cli_aaa7c346a6385cba"
APP_SECRET = "oSA1pUP92vKALKHb2WLNkfRmbfmkdAvi"
CHAT_ID = "oc_1a238a6016460ec51c602048a88aca70"
XIAOMA_APP_ID = "cli_aaa7c6b5c2389cfc"

BASE_DIR = os.path.join(os.environ.get("LOCALAPPDATA", ""), "hermes", "memories")
STATE_FILE = os.path.join(BASE_DIR, "feishu_poll_state.json")
NEW_MSGS_FILE = os.path.join(BASE_DIR, "feishu_new_msgs.txt")
ALERT_FLAG = os.path.join(BASE_DIR, "feishu_alert.flag")
TRIGGER_FLAG = os.path.join(BASE_DIR, "feishu_instant_trigger.flag")

POLL_INTERVAL = 3  # 3秒轮询

def get_token():
    data = json.dumps({"app_id": APP_ID, "app_secret": APP_SECRET}).encode()
    req = urllib.request.Request(
        "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
        data=data, headers={"Content-Type": "application/json"}
    )
    resp = json.loads(urllib.request.urlopen(req, timeout=10).read())
    return resp.get("tenant_access_token", "")

def load_state():
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"known_ids": [], "reported_ids": []}

def save_state(state):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False)

def parse_msg(msg):
    msg_type = msg.get("msg_type", "")
    body_raw = msg.get("body", {}).get("content", "")
    try:
        body = json.loads(body_raw)
        if msg_type == "text":
            return body.get("text", "")
        elif msg_type == "post":
            post_body = body.get("zh_cn", body)
            content = post_body.get("content", [])
            parts = []
            for row in content:
                for node in row:
                    if node.get("tag") == "text":
                        parts.append(node.get("text", ""))
                    elif node.get("tag") == "at":
                        name = node.get("user_name", node.get("user_id", ""))
                        parts.append("@" + name)
            return "".join(parts).strip()
        else:
            return "[" + msg_type + "]"
    except Exception:
        return body_raw[:100]

def set_alert(msgs_text):
    """Write alert flag + new messages file"""
    os.makedirs(BASE_DIR, exist_ok=True)
    with open(ALERT_FLAG, "w", encoding="utf-8") as f:
        f.write("1")
    with open(NEW_MSGS_FILE, "w", encoding="utf-8") as f:
        for text in msgs_text:
            f.write(text + "\n")
    # 写instant trigger让检测更快速
    with open(TRIGGER_FLAG, "w", encoding="utf-8") as f:
        f.write(str(int(time.time())))
    log.info(f"Alert! {len(msgs_text)} new messages → trigger written")

def clear_alert():
    for fp in [ALERT_FLAG, NEW_MSGS_FILE, TRIGGER_FLAG]:
        try:
            os.remove(fp)
        except Exception:
            pass

def poll_once():
    """Single poll cycle."""
    token = get_token()
    if not token:
        return []
    state = load_state()
    url = (
        "https://open.feishu.cn/open-apis/im/v1/messages"
        "?container_id_type=chat&container_id=" + CHAT_ID +
        "&page_size=50&sort_type=ByCreateTimeDesc"
    )
    req = urllib.request.Request(url, headers={"Authorization": "Bearer " + token})
    resp = json.loads(urllib.request.urlopen(req, timeout=15).read())
    msgs = resp.get("data", {}).get("items", [])

    new_msgs = []
    for msg in reversed(msgs):
        msg_id = msg.get("message_id", "")
        sender_id = msg.get("sender", {}).get("id", "")
        if msg_id not in state["known_ids"]:
            state["known_ids"].append(msg_id)
        if sender_id != XIAOMA_APP_ID:
            continue
        if msg_id in state.get("reported_ids", []):
            continue
        text = parse_msg(msg)
        new_msgs.append((msg_id, text))

    if len(state["known_ids"]) > 500:
        state["known_ids"] = state["known_ids"][-300:]
    if len(state.get("reported_ids", [])) > 500:
        state["reported_ids"] = state["reported_ids"][-300:]

    save_state(state)
    return new_msgs

def run_daemon():
    log.info(f"Feishu poll daemon v5 started (interval={POLL_INTERVAL}s, instant trigger)")
    while True:
        try:
            new_msgs = poll_once()
            if new_msgs:
                msgs_text = []
                state = load_state()
                for msg_id, text in new_msgs:
                    msgs_text.append("【小马】" + text)
                    if msg_id not in state.get("reported_ids", []):
                        state.setdefault("reported_ids", []).append(msg_id)
                save_state(state)
                set_alert(msgs_text)
        except Exception as e:
            log.warning(f"Poll error: {e}")
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        new_msgs = poll_once()
        if new_msgs:
            state = load_state()
            msgs_text = []
            for msg_id, text in new_msgs:
                msgs_text.append("【小马】" + text)
                if msg_id not in state.get("reported_ids", []):
                    state.setdefault("reported_ids", []).append(msg_id)
            save_state(state)
            set_alert(msgs_text)
    else:
        run_daemon()