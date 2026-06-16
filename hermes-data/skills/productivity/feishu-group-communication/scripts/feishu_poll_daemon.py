#!/usr/bin/env python3
"""飞书群消息轮询守护进程 - 小马架构版 v3
三层架构: 1)守护进程感知 2)agent cron自动回复 3)本人亲自回复
双ID追踪: known_ids(已见过的) + reported_ids(已上报的)
alert flag: 有新消息时写 feishu_alert.flag，agent对话前检查
新消息写 feishu_new_msgs.txt，agent读后清空

⚠️ APP_SECRET 不要手写到此文件！
部署时从 feishu_send.py 读取 APP_SECRET 常量值再写入。
"""
import urllib.request, json, os, sys, time, logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [feishu-poll] %(message)s")
log = logging.getLogger()

APP_ID = "cli_aaa7c346a6385cba"
# ⚠️ APP_SECRET 部署时从 feishu_send.py 复制，不要手写或用 write_file
APP_SECRET = "REPLACE_ME_FROM_FEISHU_SEND_PY"
CHAT_ID = "oc_1a238a6016460ec51c602048a88aca70"
XIAOMA_APP_ID = "cli_aaa7c6b5c2389cfc"

BASE_DIR = os.path.join(os.environ.get("LOCALAPPDATA", ""), "hermes", "memories")
STATE_FILE = os.path.join(BASE_DIR, "feishu_poll_state.json")
NEW_MSGS_FILE = os.path.join(BASE_DIR, "feishu_new_msgs.txt")
ALERT_FLAG = os.path.join(BASE_DIR, "feishu_alert.flag")

POLL_INTERVAL = 10  # seconds


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
    """解析飞书消息，兼容 text 和 post 两种格式。
    post 消息有两种 JSON 结构:
      - 用户发的: {"zh_cn":{"title":"","content":[...]}}
      - bot 小马发的: {"title":"","content":[...]}  (无 zh_cn 嵌套)
    必须用 body.get("zh_cn", body) 兼容。
    """
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
                        # at 节点的 user_id 是占位符(@_user_1)，用 user_name 更可读
                        name = node.get("user_name", node.get("user_id", ""))
                        parts.append("@" + name)
            return "".join(parts).strip()
        else:
            return "[" + msg_type + "]"
    except Exception:
        return body_raw[:100]


def set_alert(msgs_text):
    """写 alert flag + 追加新消息到文件。agent 读取后负责清空。"""
    os.makedirs(BASE_DIR, exist_ok=True)
    with open(ALERT_FLAG, "w", encoding="utf-8") as f:
        f.write("1")
    with open(NEW_MSGS_FILE, "a", encoding="utf-8") as f:
        for text in msgs_text:
            f.write(text + "\n")
    log.info(f"Alert! {len(msgs_text)} new messages from 小马")


def clear_alert():
    """agent 读完消息后调用，清空 alert flag + new-msgs 文件。"""
    for fp in [ALERT_FLAG, NEW_MSGS_FILE]:
        try:
            os.remove(fp)
        except Exception:
            pass


def poll_once():
    """单次轮询。返回 new (unreported) 小马 messages as [(msg_id, text)]。"""
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
        # Track all message IDs (avoid re-processing)
        if msg_id not in state["known_ids"]:
            state["known_ids"].append(msg_id)
        # Only care about 小马 messages that haven't been reported
        if sender_id != XIAOMA_APP_ID:
            continue
        if msg_id in state.get("reported_ids", []):
            continue
        text = parse_msg(msg)
        new_msgs.append((msg_id, text))

    # Trim to prevent unbounded growth
    if len(state["known_ids"]) > 500:
        state["known_ids"] = state["known_ids"][-300:]
    if len(state.get("reported_ids", [])) > 500:
        state["reported_ids"] = state["reported_ids"][-300:]

    save_state(state)
    return new_msgs


def _process_new_msgs(new_msgs):
    """Mark messages as reported and write alert files."""
    state = load_state()
    msgs_text = []
    for msg_id, text in new_msgs:
        msgs_text.append("【小马】" + text)
        if msg_id not in state.get("reported_ids", []):
            state.setdefault("reported_ids", []).append(msg_id)
    save_state(state)
    set_alert(msgs_text)


def run_daemon():
    """Main daemon loop - poll every POLL_INTERVAL seconds."""
    log.info(f"Feishu poll daemon started (interval={POLL_INTERVAL}s)")
    while True:
        try:
            new_msgs = poll_once()
            if new_msgs:
                _process_new_msgs(new_msgs)
        except Exception as e:
            log.warning(f"Poll error: {e}")
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        # Single poll mode (for cron fallback)
        new_msgs = poll_once()
        if new_msgs:
            _process_new_msgs(new_msgs)
    else:
        # Daemon mode (terminal background=true)
        run_daemon()