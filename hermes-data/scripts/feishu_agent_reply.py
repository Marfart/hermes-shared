#!/usr/bin/env python3
"""
飞书群 agent 自动回复层（小马三层架构第2层）
每30秒检查 feishu_new_msgs.txt，有内容就用飞书API post @回复到群里，然后删文件。
独立于 Hermes cron，后台进程运行。
"""
import json, urllib.request, urllib.error, os, time, logging, sys

logging.basicConfig(level=logging.INFO, format="%(asctime)s [feishu-agent] %(message)s")
log = logging.getLogger(__name__)

APP_ID = "cli_aaa7c346a6385cba"
APP_SECRET = "oSA1pUP92vKALKHb2WLNkfRmbfmkdAvi"
APP_SECRET = "oSA1pUP92vKALKHb2WLNkfRmbfmkdAvi"
XIAOMA_USER_ID = "ou_567d570501c0178214a46caca3679668"

BASE_DIR = os.path.join(os.environ.get("LOCALAPPDATA", ""), "hermes", "memories")
ALERT_FLAG = os.path.join(BASE_DIR, "feishu_alert.flag")
NEW_MSGS = os.path.join(BASE_DIR, "feishu_new_msgs.txt")


def get_tenant_token():
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    data = json.dumps({"app_id": APP_ID, "app_secret": APP_SECRET}).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        r = json.loads(resp.read())
    if r.get("code") != 0:
        raise RuntimeError(f"Token error: {r}")
    return r["tenant_access_token"]


def send_post_message(token, text, at_user_id=None):
    url = "https://open.feishu.cn/open-apis/im/v1/messages"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    if at_user_id:
        content = {
            "zh_cn": {
                "title": "",
                "content": [
                    [{"tag": "at", "user_id": at_user_id}, {"tag": "text", "text": " " + text}]
                ]
            }
        }
        msg_type = "post"
    else:
        content = {"text": text}
        msg_type = "text"

    data = json.dumps({
        "receive_id": CHAT_ID,
        "msg_type": msg_type,
        "content": json.dumps(content)
    }).encode()

    req = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(req, timeout=10) as resp:
        r = json.loads(resp.read())
    return r.get("code") == 0


def process_new_messages():
    """Read new messages file, compose reply, send to group, then delete files."""
    if not os.path.exists(NEW_MSGS):
        return

    with open(NEW_MSGS, "r", encoding="utf-8") as f:
        content = f.read().strip()

    if not content:
        return

    lines = [l for l in content.split("\n") if l.strip()]
    if not lines:
        return

    log.info(f"Found {len(lines)} new messages to reply")

    try:
        token = get_tenant_token()
    except Exception as e:
        log.error(f"Failed to get token: {e}")
        return

    # Parse messages from 小马
    xiaoma_msgs = []
    for line in lines:
        if line.startswith("【小马】"):
            msg_text = line[len("【小马】"):].strip()
            # Skip self-improvement and write_file lines
            if msg_text and "Self-improvement" not in msg_text and "write_file" not in msg_text:
                xiaoma_msgs.append(msg_text)

    if not xiaoma_msgs:
        log.info("No substantive 小马 messages to reply to")
    else:
        # Compose a brief acknowledgment
        last_msg = xiaoma_msgs[-1]
        if len(last_msg) > 100:
            last_msg = last_msg[:100] + "..."
        reply = f"收到！看到你的消息了：{last_msg}。我在处理中~"
        try:
            ok = send_post_message(token, reply, at_user_id=XIAOMA_USER_ID)
            log.info(f"Reply sent: {ok}")
        except Exception as e:
            log.error(f"Reply failed: {e}")

    # Clean up regardless
    try:
        os.remove(NEW_MSGS)
        if os.path.exists(ALERT_FLAG):
            os.remove(ALERT_FLAG)
        log.info("Cleaned up alert files")
    except OSError:
        pass


def main_loop():
    """Main loop - check every 30 seconds."""
    log.info("feishu_agent_reply started (30s loop)")
    while True:
        try:
            process_new_messages()
        except Exception as e:
            log.error(f"Error in loop: {e}")
        time.sleep(30)


if __name__ == "__main__":
    if "--once" in sys.argv:
        process_new_messages()
    else:
        main_loop()