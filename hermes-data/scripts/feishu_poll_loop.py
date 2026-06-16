#!/usr/bin/env python3
"""飞书群消息持续轮询 - 每10秒拉取新消息写入文件"""

import urllib.request
import json
import time
import sys
import os
from pathlib import Path

# 飞书配置
APP_ID = "cli_aaa7c346a6385cba"
APP_SECRET = "oSA1pUP92vKALKHb2WLNkfRmbfmkdAvi"
CHAT_ID = "oc_1a238a6016460ec51c602048a88aca70"

# 文件路径
BASE_DIR = Path(os.environ.get("LOCALAPPDATA", "C:/Users/Admin/AppData/Local")) / "hermes" / "memories"
STATE_FILE = BASE_DIR / "feishu_poll_state.json"
NEW_MSG_FILE = BASE_DIR / "feishu_new_messages.txt"
MY_APP_ID = "cli_aaa7c346a6385cba"

def get_tenant_token():
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    data = json.dumps({"app_id": APP_ID, "app_secret": APP_SECRET}).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        result = json.loads(resp.read().decode())
        if result.get("code") == 0:
            return result["tenant_access_token"]
        return None
    except Exception as e:
        print(f"[ERROR] get token: {e}", file=sys.stderr)
        return None

def get_messages(token, page_size=50):
    url = f"https://open.feishu.cn/open-apis/im/v1/messages?container_id_type=chat&container_id={CHAT_ID}&page_size={page_size}&sort_type=ByCreateTimeDesc"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    try:
        resp = urllib.request.urlopen(req, timeout=15)
        result = json.loads(resp.read().decode())
        return result.get("data", {}).get("items", [])
    except Exception as e:
        print(f"[ERROR] get messages: {e}", file=sys.stderr)
        return []

def load_seen_ids():
    if STATE_FILE.exists():
        try:
            return set(json.loads(STATE_FILE.read_text(encoding="utf-8")).get("seen_ids", []))
        except:
            return set()
    return set()

def save_seen_ids(seen_ids):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    ids_list = list(seen_ids)[-500:]
    STATE_FILE.write_text(json.dumps({"seen_ids": ids_list}, ensure_ascii=False), encoding="utf-8")

def extract_text_from_msg(msg):
    body = msg.get("body", {})
    content = body.get("content", "{}")
    try:
        content_obj = json.loads(content) if isinstance(content, str) else content
    except:
        content_obj = {}
    
    text_parts = []
    for block in content_obj.get("content", []):
        if isinstance(block, list):
            for item in block:
                if isinstance(item, dict):
                    if item.get("tag") == "text":
                        text_parts.append(item.get("text", ""))
                    elif item.get("tag") == "at":
                        text_parts.append(f"@{item.get('user_id', 'all')}")
                elif isinstance(item, str):
                    text_parts.append(item)
        elif isinstance(block, dict):
            if block.get("tag") == "text":
                text_parts.append(block.get("text", ""))
    
    if text_parts:
        return "".join(text_parts)
    return content_obj.get("text", msg.get("msg_type", ""))

def poll_once():
    """单次轮询，返回新消息列表"""
    token = get_tenant_token()
    if not token:
        return []
    
    messages = get_messages(token)
    if not messages:
        return []
    
    seen_ids = load_seen_ids()
    new_messages = []
    
    for msg in messages:
        msg_id = msg.get("message_id", "")
        if msg_id and msg_id not in seen_ids:
            new_messages.append(msg)
            seen_ids.add(msg_id)
    
    save_seen_ids(seen_ids)
    
    # 过滤掉自己发的消息
    others_msgs = []
    for msg in reversed(new_messages):
        sender_id = msg.get("sender", {}).get("id", "unknown")
        sender_type = msg.get("sender", {}).get("sender_type", "")
        if sender_type == "app" and sender_id == MY_APP_ID:
            continue
        text = extract_text_from_msg(msg)
        sender_name = msg.get("sender", {}).get("id", sender_id)
        create_time = msg.get("create_time", "")
        others_msgs.append((create_time, sender_name, text))
    
    return others_msgs

def main():
    print(f"[{time.strftime('%H:%M:%S')}] 飞书轮询启动，每10秒轮询一次...", file=sys.stderr)
    sys.stderr.flush()
    
    while True:
        try:
            new_msgs = poll_once()
            if new_msgs:
                # 写入新消息文件
                NEW_MSG_FILE.parent.mkdir(parents=True, exist_ok=True)
                with open(NEW_MSG_FILE, "a", encoding="utf-8") as f:
                    f.write(f"\n--- {time.strftime('%Y-%m-%d %H:%M:%S')} ---\n")
                    for ts, sender, text in new_msgs:
                        f.write(f"[{ts}] {sender}: {text}\n")
                # stdout输出供检测
                for ts, sender, text in new_msgs:
                    print(f"[{ts}] {sender}: {text}")
                sys.stdout.flush()
        except Exception as e:
            print(f"[ERROR] {e}", file=sys.stderr)
        
        time.sleep(10)

if __name__ == "__main__":
    main()