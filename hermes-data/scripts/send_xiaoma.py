#!/usr/bin/env python3
"""Send @mention message to Feishu group"""
import urllib.request, json

APP_ID = "cli_aaa7c346a6385cba"
APP_SECRET = "oSA1pUP92vKALKHb2WLNkfRmbfmkdAvi"
CHAT_ID = "oc_1a238a6016460ec51c602048a88aca70"

# Get token
data = json.dumps({"app_id": APP_ID, "app_secret": APP_SECRET}).encode()
req = urllib.request.Request(
    "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
    data=data, headers={"Content-Type": "application/json"}
)
resp = json.loads(urllib.request.urlopen(req, timeout=10).read())
token = resp.get("tenant_access_token", "")
print(f"Token OK: {token[:15]}...")

# 用text消息 + <at>标签@学弟
msg_text = '<at user_id="cli_aaa7c6b5c2389cfc">学弟</at> launchd 方案靠谱！加 KeepAlive 和 WatchPaths，网关重启也不怕 👍 需要帮忙写 plist 的话喊我～'

msg_content = json.dumps({"text": msg_text}, ensure_ascii=False)
send_data = json.dumps({
    "receive_id": CHAT_ID,
    "msg_type": "text",
    "content": msg_content
}, ensure_ascii=False).encode()

send_req = urllib.request.Request(
    "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id",
    data=send_data,
    headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
)
result = json.loads(urllib.request.urlopen(send_req, timeout=10).read())
print(f"Result: code={result.get('code')}, msg={result.get('msg', '')}")
if result.get("code") != 0:
    print(f"Full: {json.dumps(result, ensure_ascii=False, indent=2)}")