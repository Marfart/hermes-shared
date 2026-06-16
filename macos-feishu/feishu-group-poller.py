#!/usr/bin/env python3
"""
飞书群消息轮询 v6 - 秒级响应
每3秒轮询一次，检测新消息 → 写文件 → 触发 webhook 秒唤醒 agent
不再依赖 cron，webhook 直连 agent 实例，实现秒收秒回
"""
import urllib.request, json, os, sys, re, time, signal

APP_ID = "cli_aaa7c6b5c2389cfc"
APP_SECRET = "OTWdngPHYVVSiYA4U0zvdenk8uN70dXb"
CHAT_ID = "oc_1a238a6016460ec51c602048a88aca70"
TACHIKUMA_ID = "cli_aaa7c346a6385cba"

WEBHOOK_URL = "http://localhost:8644/webhooks/feishu-group-reply"
WEBHOOK_SECRET = "1aBIpWu4V4vYTAcPISRTQGYsSbFcJaglV5RyXTAxM54"

STATE_FILE = "/tmp/feishu-group-poller-state.json"
NEW_MSG_FILE = "/tmp/feishu-group-new-msg.txt"
POLL_INTERVAL = 3

running = True
def signal_handler(sig, frame):
    global running
    running = False
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

def get_token():
    data = json.dumps({"app_id": APP_ID, "app_secret": APP_SECRET}).encode()
    req = urllib.request.Request(
        "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
        data=data, headers={"Content-Type": "application/json"}
    )
    resp = json.loads(urllib.request.urlopen(req, timeout=10).read())
    return resp.get("tenant_access_token", "")

def get_messages(token):
    url = f"https://open.feishu.cn/open-apis/im/v1/messages?container_id_type=chat&container_id={CHAT_ID}&page_size=50&sort_type=ByCreateTimeDesc"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    resp = json.loads(urllib.request.urlopen(req, timeout=15).read())
    return resp.get("data", {}).get("items", [])

def load_state():
    state = {"known_ids": set(), "reported_ids": set()}
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE) as f:
                loaded = json.load(f)
                state["known_ids"] = set(loaded.get("known_ids", []))
                state["reported_ids"] = set(loaded.get("reported_ids", []))
        except:
            state["known_ids"] = set()
            state["reported_ids"] = set()
    return state

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump({
            "known_ids": list(state["known_ids"]),
            "reported_ids": list(state["reported_ids"])
        }, f, ensure_ascii=False)

def extract_text(item):
    msg_type = item.get("msg_type", "")
    body = item.get("body", {}).get("content", "{}")
    try:
        cont = json.loads(body)
    except:
        return ""
    if msg_type == "text":
        return cont.get("text", "")
    elif msg_type == "post":
        try:
            parts = []
            zh = cont.get("zh_cn", cont)
            for para in zh.get("content", []):
                for seg in para:
                    if seg.get("tag") == "text":
                        parts.append(seg.get("text", ""))
            return "\n".join(parts)
        except:
            return ""
    return ""

def format_alert(messages):
    """写alert文件让agent知道有新消息"""
    with open("/tmp/hermes-group-alert.txt", "w", encoding="utf-8") as f:
        f.write("1\n")
        # 写入最新消息的时间戳，方便agent判断时效性
        f.write(str(messages[0].get("timestamp", "")))

def main():
    state = load_state()
    token = get_token()
    if not token:
        return

    items = get_messages(token)
    unreported = []

    for m in items:
        msg_id = m.get("message_id", "")
        if not msg_id:
            continue
        state["known_ids"].add(msg_id)

        # 跳过已上报的
        if msg_id in state["reported_ids"]:
            continue

        sender = m.get("sender", {}).get("id", "")
        # 跳过自己的消息
        if sender == APP_ID:
            state["reported_ids"].add(msg_id)
            continue
        # 人类用户的消息网关已转发，跳过
        if sender.startswith("ou_"):
            state["reported_ids"].add(msg_id)
            continue

        # 其他bot的消息
        text = extract_text(m)
        text = re.sub(r'@_user_\d+\s*', '', text).strip()
        if not text:
            # 空内容也标记为已上报，避免重复处理
            state["reported_ids"].add(msg_id)
            continue

        unreported.append({
            "sender": sender,
            "text": text,
            "msg_id": msg_id,
            "timestamp": m.get("create_time", "")
        })
        state["reported_ids"].add(msg_id)

    save_state(state)

    if unreported:
        lines = []
        for msg in unreported:
            name = "塔奇克马" if msg['sender'] == TACHIKUMA_ID else msg['sender']
            lines.append(f"【新消息】来自 {name}")
            lines.append(f"内容: {msg['text']}")
            lines.append(f"消息ID: {msg['msg_id']}")
            lines.append("---")
        with open(NEW_MSG_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        format_alert(unreported)
        # Fire webhook to wake Hermes agent immediately
        try:
            import hmac, hashlib
            payload = json.dumps({"event": "new_message", "from": "tachikuma"}).encode()
            sig = hmac.new(WEBHOOK_SECRET.encode(), payload, hashlib.sha256).hexdigest()
            req = urllib.request.Request(
                WEBHOOK_URL, data=payload,
                headers={
                    "Content-Type": "application/json",
                    "X-Webhook-Signature": sig
                }
            )
            urllib.request.urlopen(req, timeout=5)
        except Exception:
            pass  # Webhook fire best-effort

if __name__ == "__main__":
    while running:
        try:
            main()
        except Exception as e:
            pass
        time.sleep(POLL_INTERVAL)