#!/usr/bin/env python3
"""飞书群消息轮询 - 完全按照学弟的方案，每10秒轮询，只处理其他bot消息"""

import urllib.request
import json
import os
import sys
import re
import time

# 飞书配置
APP_ID = "cli_aaa7c346a6385cba"
APP_SECRET = "oSA1pUP92vKALKHb2WLNkfRmbfmkdAvi"
CHAT_ID = "oc_1a238a6016460ec51c602048a88aca70"
MY_ID = APP_ID  # 自己的app_id，用来跳过自己的消息

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
    state = {"known_ids": set()}
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, encoding="utf-8") as f:
                loaded = json.load(f)
                state["known_ids"] = set(loaded.get("known_ids", []))
        except:
            state["known_ids"] = set()
    return state

def save_state(state):
    state_copy = {"known_ids": list(state["known_ids"])}
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state_copy, f, ensure_ascii=False)

def main():
    state = load_state()
    token = get_token()
    if not token:
        return
    items = get_messages(token)
    new_msgs = []
    for m in items:
        msg_id = m.get("message_id", "")
        if msg_id in state["known_ids"]:
            continue
        sender = m.get("sender", {}).get("id", "")
        msg_type = m.get("msg_type", "")

        # 跳过自己的消息
        if sender == MY_ID:
            state["known_ids"].add(msg_id)
            continue

        # 跳过人类用户的消息（ou_开头，网关已转发）
        if sender.startswith("ou_"):
            state["known_ids"].add(msg_id)
            continue

        # 其他bot的消息（cli_开头的）
        if msg_type == "text":
            cont = json.loads(m.get("body", {}).get("content", "{}"))
            text = cont.get("text", "")
            clean = re.sub(r'@_user_\d+\s*', '', text).strip()
            if clean:
                new_msgs.append(f"【新消息】来自 {sender}\n内容: {clean}\n---")
        elif msg_type == "post":
            # 富文本消息
            cont = json.loads(m.get("body", {}).get("content", "{}"))
            text_parts = []
            for block in cont.get("content", []):
                if isinstance(block, list):
                    for item in block:
                        if isinstance(item, dict):
                            if item.get("tag") == "text":
                                text_parts.append(item.get("text", ""))
                            elif item.get("tag") == "at":
                                text_parts.append(f"@{item.get('user_id', 'all')}")
                elif isinstance(block, dict):
                    if block.get("tag") == "text":
                        text_parts.append(block.get("text", ""))
            if text_parts:
                clean = re.sub(r'@_user_\d+\s*', '', "".join(text_parts)).strip()
                if clean:
                    new_msgs.append(f"【新消息】来自 {sender}\n内容: {clean}\n---")

        state["known_ids"].add(msg_id)

    save_state(state)

    if new_msgs:
        # 写入文件供 agent cron 读取
        os.makedirs(os.path.dirname(NEW_MSG_FILE), exist_ok=True)
        with open(NEW_MSG_FILE, "a", encoding="utf-8") as f:
            f.write(f"\n--- {time.strftime('%Y-%m-%d %H:%M:%S')} ---\n")
            for msg in new_msgs:
                f.write(msg + "\n")
        # 同时输出到stdout
        for msg in new_msgs:
            print(msg)

if __name__ == "__main__":
    while True:
        main()
        time.sleep(10)  # 每10秒轮询一次