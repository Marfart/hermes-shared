#!/usr/bin/env python3
"""飞书群消息轮询脚本 - 监控小马的消息并写入inbox+群通知"""
import urllib.request, json, os, sys

APP_ID = "cli_aaa7c346a6385cba"
APP_SECRET = "oSA1pUP92vKALKHb2WLNkfRmbfmkdAvi"
CHAT_ID = "oc_1a238a6016460ec51c602048a88aca70"
XIAOMA_APP_ID = "cli_aaa7c6b5c2389cfc"
STATE_FILE = os.path.join(os.environ.get("LOCALAPPDATA", ""), "hermes", "memories", "feishu_poll_state.json")
INBOX_FILE = os.path.join(os.environ.get("LOCALAPPDATA", ""), "hermes", "memories", "feishu_inbox.txt")

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
        return {"known_ids": []}

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

def send_notification(token, preview_text):
    """收到小马消息时发通知@塔奇克马到群里"""
    msg_body = {
        "zh_cn": {
            "title": "",
            "content": [[
                {"tag": "at", "user_id": "ou_ee63858e3a997e994faec6e4647c552c"},
                {"tag": "text", "text": " 小马说了：" + preview_text[:100]}
            ]]
        }
    }
    data = json.dumps({
        "receive_id": CHAT_ID,
        "msg_type": "post",
        "content": json.dumps(msg_body)
    }).encode()
    req = urllib.request.Request(
        "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id",
        data=data,
        headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"}
    )
    urllib.request.urlopen(req, timeout=10).read()

try:
    token = get_token()
    if not token:
        sys.exit(0)
    state = load_state()
    url = (
        "https://open.feishu.cn/open-apis/im/v1/messages"
        "?container_id_type=chat&container_id=" + CHAT_ID +
        "&page_size=50&sort_type=ByCreateTimeDesc"
    )
    req = urllib.request.Request(url, headers={"Authorization": "Bearer " + token})
    resp = json.loads(urllib.request.urlopen(req, timeout=15).read())
    msgs = resp.get("data", {}).get("items", [])
    new_xiaoma_msgs = []
    for msg in reversed(msgs):
        msg_id = msg.get("message_id", "")
        sender_id = msg.get("sender", {}).get("id", "")
        if msg_id in state["known_ids"]:
            continue
        state["known_ids"].append(msg_id)
        if sender_id != XIAOMA_APP_ID:
            continue
        text = parse_msg(msg)
        new_xiaoma_msgs.append(text)
    if len(state["known_ids"]) > 500:
        state["known_ids"] = state["known_ids"][-300:]
    save_state(state)
    if new_xiaoma_msgs:
        os.makedirs(os.path.dirname(INBOX_FILE), exist_ok=True)
        with open(INBOX_FILE, "a", encoding="utf-8") as f:
            for text in new_xiaoma_msgs:
                f.write("【小马】" + text + "\n")
        try:
            latest = new_xiaoma_msgs[-1][:80]
            send_notification(token, latest)
        except Exception:
            pass
except Exception as e:
    pass
