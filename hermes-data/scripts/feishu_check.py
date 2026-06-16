#!/usr/bin/env python3
"""Check latest messages from Feishu group - used by me (塔奇克马) to see what 小马 said"""
import urllib.request, json, sys, os, re, time

APP_ID = "cli_aaa7c346a6385cba"
APP_SECRET="oSA1pUP92vKALKHb2WLNkfRmbfmkdAvi"
CHAT_ID = "oc_1a238a6016460ec51c602048a88aca70"
MY_ID = APP_ID  # skip own messages
XIAOMA_APP_ID = "cli_aaa7c6b5c2389cfc"  # 小马的app_id

STATE_FILE = os.path.join(os.environ.get("LOCALAPPDATA", "C:/Users/Admin/AppData/Local"), "hermes", "memories", "feishu_poll_state.json")
NEW_MSG_FILE = os.path.join(os.environ.get("LOCALAPPDATA", "C:/Users/Admin/AppData/Local"), "hermes", "memories", "feishu_new_messages.txt")

def get_token():
    data = json.dumps({"app_id": APP_ID, "app_secret": APP_SECRET}).encode()
    req = urllib.request.Request(
        "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
        data=data, headers={"Content-Type": "application/json"}
    )
    resp = json.loads(urllib.request.urlopen(req, timeout=10).read())
    return resp.get("tenant_access_token", "")

def get_messages(token):
    url = f"https://open.feishu.cn/open-apis/im/v1/messages?container_id_type=chat&container_id={CHAT_ID}&page_size=30&sort_type=ByCreateTimeDesc"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    resp = json.loads(urllib.request.urlopen(req, timeout=15).read())
    return resp.get("data", {}).get("items", [])

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, encoding="utf-8") as f:
                return set(json.load(f).get("known_ids", []))
        except:
            pass
    return set()

def save_state(known_ids):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump({"known_ids": list(known_ids)}, f, ensure_ascii=False)

def extract_text(m):
    msg_type = m.get("msg_type", "")
    body = m.get("body", {}).get("content", "{}")
    try:
        cont = json.loads(body)
    except:
        return ""
    
    if msg_type == "text":
        return cont.get("text", "")
    elif msg_type == "post":
        parts = []
        for block in cont.get("content", []):
            if isinstance(block, list):
                for item in block:
                    if isinstance(item, dict):
                        if item.get("tag") == "text":
                            parts.append(item.get("text", ""))
                        elif item.get("tag") == "at":
                            parts.append(f'@{item.get("user_id", "all")}')
        return "".join(parts)
    return f"[{msg_type}]"

def main():
    # Parse command
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
    else:
        cmd = "check"
    
    if cmd == "reset":
        save_state(set())
        print("State reset - will see all messages next check")
        return
    
    token = get_token()
    if not token:
        print("ERROR: Failed to get token")
        return
    
    items = get_messages(token)
    known_ids = load_state()
    
    new_msgs = []
    for m in items:
        msg_id = m.get("message_id", "")
        sender = m.get("sender", {}).get("id", "")
        
        # Skip own messages
        if sender == MY_ID:
            known_ids.add(msg_id)
            continue
        
        # Skip human messages (ou_ prefix) - they come through Hermes gateway already
        if sender.startswith("ou_"):
            known_ids.add(msg_id)
            continue
        
        # This is 小马's message (cli_aaa7c6b5c2389cfc)
        if msg_id not in known_ids:
            text = extract_text(m)
            clean = re.sub(r'@_user_\d+\s*', '', text).strip()
            if clean:
                sender_name = "小马" if sender == XIAOMA_APP_ID else sender
                new_msgs.append(f"【{sender_name}】{clean}")
            known_ids.add(msg_id)
    
    save_state(known_ids)
    
    if new_msgs:
        os.makedirs(os.path.dirname(NEW_MSG_FILE), exist_ok=True)
        with open(NEW_MSG_FILE, "a", encoding="utf-8") as f:
            f.write(f"\n--- {time.strftime('%Y-%m-%d %H:%M:%S')} ---\n")
            for msg in new_msgs:
                f.write(msg + "\n")
        for msg in new_msgs:
            print(msg)
    else:
        print("No new messages from 小马")

if __name__ == "__main__":
    main()