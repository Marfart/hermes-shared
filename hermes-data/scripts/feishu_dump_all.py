#!/usr/bin/env python3
"""拉取飞书群所有消息，找出所有@塔奇克马或@all的消息"""
import urllib.request, json

APP_ID = "cli_aaa7c346a6385cba"
APP_SECRET = "oSA1pUP92vKALKHb2WLNkfRmbfmkdAvi"
CHAT_ID = "oc_1a238a6016460ec51c602048a88aca70"
XIAOMA_APP_ID = "cli_aaa7c6b5c2389cfc"

data = json.dumps({"app_id": APP_ID, "app_secret": APP_SECRET}).encode()
req = urllib.request.Request(
    "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
    data=data, headers={"Content-Type": "application/json"}
)
resp = json.loads(urllib.request.urlopen(req, timeout=10).read())
token = resp.get("tenant_access_token", "")

url = (
    "https://open.feishu.cn/open-apis/im/v1/messages"
    "?container_id_type=chat&container_id=" + CHAT_ID +
    "&page_size=50&sort_type=ByCreateTimeDesc"
)
req = urllib.request.Request(url, headers={"Authorization": "Bearer " + token})
resp = json.loads(urllib.request.urlopen(req, timeout=15).read())
msgs = resp.get("data", {}).get("items", [])

print(f"总共 {len(msgs)} 条消息\n")

for msg in reversed(msgs):
    msg_type = msg.get("msg_type", "")
    body_raw = msg.get("body", {}).get("content", "")
    sender_id = msg.get("sender", {}).get("id", "")
    sender_type = msg.get("sender", {}).get("sender_type", "")
    msg_id = msg.get("message_id", "")
    create_time = msg.get("create_time", "")
    
    try:
        body = json.loads(body_raw)
        text = ""
        if msg_type == "text":
            text = body.get("text", "")
        elif msg_type == "post":
            post_body = body.get("zh_cn", body)
            content = post_body.get("content", [])
            parts = []
            for row in content:
                for node in row:
                    if node.get("tag") == "text":
                        parts.append(node.get("text", ""))
                    elif node.get("tag") == "at":
                        parts.append("@" + node.get("user_name", node.get("user_id", "")))
            text = "".join(parts).strip()
        else:
            text = "[" + msg_type + "]"
    except:
        text = body_raw[:100]

    sender_name = "小马" if sender_id == XIAOMA_APP_ID else ("Kali" if sender_type == "user" else sender_id[:20])
    
    # 标记@塔奇克马或@all的消息
    is_mention = "@塔奇克马" in text or "@all" in text
    marker = " ⬅️ @我" if is_mention else ""
    
    print(f"[{create_time}] {sender_name}: {text[:300]}{marker}")