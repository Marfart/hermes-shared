#!/usr/bin/env python3
"""飞书群消息轮询器 — 每10秒检查一次，新消息写入本地文件"""
import urllib.request, json, time, os

APP_ID = "cli_aaa7c346a6385cba"
APP_SECRET = "oSA1pUP92vKALKHb2WLNkfRmbfmkdAvi"
CHAT_ID = "oc_1a238a6016460ec51c602048a88aca70"
XIAOMA_APP_ID = "cli_aaa7c6b5c2389cfc"

STATE_FILE = os.path.join(os.environ.get("LOCALAPPDATA", ""), "hermes", "memories", "feishu_poll_state.json")
INBOX_FILE = os.path.join(os.environ.get("LOCALAPPDATA", ""), "hermes", "memories", "feishu_inbox.txt")
INTERVAL = 10

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
    except:
        return {"seen_ids": []}

def save_state(state):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False)

def get_messages(token):
    url = f"https://open.feishu.cn/open-apis/im/v1/messages?container_id_type=chat&container_id={CHAT_ID}&page_size=30&sort_type=ByCreateTimeDesc"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    resp = json.loads(urllib.request.urlopen(req, timeout=15).read())
    return resp.get("data", {}).get("items", [])

def append_inbox(msg_text):
    os.makedirs(os.path.dirname(INBOX_FILE), exist_ok=True)
    with open(INBOX_FILE, "a", encoding="utf-8") as f:
        f.write(msg_text + "\n")

def main():
    print(f"🔄 飞书轮询启动，每{INTERVAL}秒检查一次", flush=True)
    state = load_state()
    token = get_token()
    token_time = time.time()

    while True:
        try:
            if time.time() - token_time > 1800:
                token = get_token()
                token_time = time.time()

            msgs = get_messages(token)
            new_count = 0
            for msg in reversed(msgs):
                msg_id = msg.get("message_id", "")
                sender_id = msg.get("sender", {}).get("id", "")

                if msg_id in state["seen_ids"]:
                    continue

                if sender_id != XIAOMA_APP_ID:
                    state["seen_ids"].append(msg_id)
                    continue

                msg_type = msg.get("msg_type", "")
                body_raw = msg.get("body", {}).get("content", "")
                create_time = msg.get("create_time", "")

                text = ""
                try:
                    body = json.loads(body_raw)
                    if msg_type == "text":
                        text = body.get("text", "")
                    elif msg_type == "post":
                        content = body.get("zh_cn", {}).get("content", [])
                        parts = []
                        for row in content:
                            for node in row:
                                if node.get("tag") == "text":
                                    parts.append(node.get("text", ""))
                                elif node.get("tag") == "at":
                                    parts.append(f"@{node.get('user_id', '')}")
                        text = "".join(parts).strip()
                    else:
                        text = f"[{msg_type}] {body_raw[:100]}"
                except:
                    text = body_raw[:200]

                line = f"【小马 {create_time}】{text}"
                append_inbox(line)
                print(line, flush=True)
                new_count += 1
                state["seen_ids"].append(msg_id)

            if len(state["seen_ids"]) > 500:
                state["seen_ids"] = state["seen_ids"][-300:]

            save_state(state)

        except Exception as e:
            print(f"⚠️ 轮询错误: {e}", flush=True)

        time.sleep(INTERVAL)

if __name__ == "__main__":
    main()