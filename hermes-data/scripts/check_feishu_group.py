#!/usr/bin/env python3
"""Check latest Feishu group messages"""
import urllib.request, json, os, sys

APP_ID = "cli_aaa7c346a6385cba"
APP_SECRET="***"
CHAT_ID = "oc_1a238a6016460ec51c602048a88aca70"
MY_ID = APP_ID

# Get token
data = json.dumps({"app_id": APP_ID, "app_secret": APP_SECRET}).encode()
req = urllib.request.Request(
    "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
    data=data, headers={"Content-Type": "application/json"}
)
resp = json.loads(urllib.request.urlopen(req, timeout=10).read())
token = resp.get("tenant_access_token", "")
if not token:
    print("Failed to get token!")
    sys.exit(1)

# Get recent messages
url = f"https://open.feishu.cn/open-apis/im/v1/messages?container_id_type=chat&container_id={CHAT_ID}&page_size=10&sort_type=ByCreateTimeDesc"
req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
resp = json.loads(urllib.request.urlopen(req, timeout=15).read())

items = resp.get("data", {}).get("items", [])
print(f"Latest {len(items)} messages in group:")
print("=" * 60)

for m in items:
    sender = m.get("sender", {}).get("id", "unknown")
    sender_type = m.get("sender", {}).get("sender_type", "")
    msg_type = m.get("msg_type", "")
    msg_id = m.get("message_id", "")
    create_time = m.get("create_time", "")
    
    # Identify sender
    if sender == MY_ID:
        sender_name = "我(小马)"
    elif sender.startswith("cli_aaa7c6b5c2389cfc"):
        sender_name = "学弟"
    elif sender.startswith("ou_"):
        sender_name = f"人类({sender[:8]}...)"
    else:
        sender_name = sender[:20]
    
    # Extract text
    text = ""
    if msg_type == "text":
        try:
            content = json.loads(m.get("body", {}).get("content", "{}"))
            text = content.get("text", "")[:100]
        except:
            text = m.get("body", {}).get("content", "")[:100]
    elif msg_type == "post":
        try:
            content = json.loads(m.get("body", {}).get("content", "{}"))
            title = content.get("zh_cn", {}).get("title", "")
            text_parts = []
            for line in content.get("zh_cn", {}).get("content", []):
                for item in line:
                    if isinstance(item, dict) and item.get("tag") == "text":
                        text_parts.append(item.get("text", ""))
                    elif isinstance(item, dict) and item.get("tag") == "at":
                        text_parts.append(f"@{item.get('user_id', 'all')}")
            text = (title + " " + " ".join(text_parts))[:100]
        except:
            text = m.get("body", {}).get("content", "")[:100]
    
    print(f"[{sender_name}] {text}")
    print(f"  msg_id: {msg_id}, time: {create_time}")
    print()