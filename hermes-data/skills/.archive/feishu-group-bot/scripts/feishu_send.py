#!/usr/bin/env python3
"""Send message to Feishu group — supports --at for @小马 in post messages

Usage:
  python feishu_send.py "Hello world"              # plain text
  python feishu_send.py --at "Hey 小马!"           # @小马 post message
"""
import urllib.request, json, sys

APP_ID = "cli_aaa7c346a6385cba"
APP_SECRET="oSA1...T_ID = "oc_1a238a6016460ec51c602048a88aca70"
XIAOMA_USER_ID = "ou_567d570501c0178214a46caca3679668"

# Get token
data = json.dumps({"app_id": APP_ID, "app_secret": APP_SECRET}).encode()
req = urllib.request.Request(
    "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
    data=data, headers={"Content-Type": "application/json"}
)
resp = json.loads(urllib.request.urlopen(req, timeout=10).read())
token = resp.get("tenant_access_token", "")

# Parse arguments
at_xiaoma = "--at" in sys.argv
msg_parts = [a for a in sys.argv[1:] if a != "--at"]
msg_text = " ".join(msg_parts) if msg_parts else "测试消息"

if at_xiaoma:
    content = [
        [{"tag": "at", "user_id": XIAOMA_USER_ID}, {"tag": "text", "text": " " + msg_text}]
    ]
    msg_content = json.dumps({"zh_cn": {"title": "", "content": content}}, ensure_ascii=False)
    msg_type = "post"
else:
    msg_content = json.dumps({"text": msg_text}, ensure_ascii=False)
    msg_type = "text"

send_data = json.dumps({
    "receive_id": CHAT_ID,
    "msg_type": msg_type,
    "content": msg_content
}, ensure_ascii=False).encode()

send_req = urllib.request.Request(
    "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id",
    data=send_data,
    headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
)
result = json.loads(urllib.request.urlopen(send_req, timeout=10).read())
print(f"Result: code={result.get('code')}, msg={result.get('msg', '')}")