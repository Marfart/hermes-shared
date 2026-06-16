#!/usr/bin/env python3
"""轮询中继→写文件→发TG通知触发小马。
学弟有消息时，通知小马去处理。"""
import urllib.request, json, os, sys
from datetime import datetime

RELAY = "https://introduces-initiative-download-conventional.trycloudflare.com"
MSG_FILE = os.path.join(os.environ.get("LOCALAPPDATA", ""), "hermes", "xuedi_messages.txt")
STATE_FILE = os.path.join(os.environ.get("LOCALAPPDATA", ""), "hermes", "xuedi_poll_state.json")
BOT_TOKEN = ""
# 从.env文件读取token
_env_path = os.path.join(os.environ.get("LOCALAPPDATA", ""), "hermes", ".env")
try:
    with open(_env_path, "r") as f:
        for line in f:
            if line.strip().startswith("TELEGRAM_BOT_TOKEN="):
                BOT_TOKEN = line.strip().split("=", 1)[1]
                break
except:
    pass
KALI_CHAT = "8314311281"  # 小马DM，通知到这触发小马session

# 读取上次时间戳
last_ts = ""
try:
    with open(STATE_FILE, "r") as f:
        last_ts = f.read().strip()
except:
    pass

try:
    resp = urllib.request.urlopen(f"{RELAY}/poll/%E5%B0%8F%E9%A9%AC", timeout=10)
    data = json.loads(resp.read().decode("utf-8"))
    count = data.get("count", 0)
    if count > 0:
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        lines = []
        for m in data.get("messages", []):
            lines.append(f"[{m['id'][:8]}] {m['from']} | {m.get('topic','?')}")
            lines.append(m["content"])
            lines.append("")
            # 删除已读
            try:
                del_req = urllib.request.Request(f"{RELAY}/msg/{m['id']}", method="DELETE")
                urllib.request.urlopen(del_req, timeout=5)
            except:
                pass
        # 写本地文件
        with open(MSG_FILE, "a", encoding="utf-8") as f:
            f.write(f"\n{'='*40}\n{now}\n")
            f.write("\n".join(lines))
        # 更新时间戳
        with open(STATE_FILE, "w") as f:
            f.write(now)
        # 发TG通知触发小马
        if BOT_TOKEN and now != last_ts:
            notif = f"🐴 学弟有{count}条新消息，小马去处理！"
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            payload = json.dumps({"chat_id": KALI_CHAT, "text": notif}).encode("utf-8")
            req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
            urllib.request.urlopen(req, timeout=10)
            print(notif)
        else:
            print(f"学弟有{count}条新消息（已写入文件）")
    # count=0 静默
except Exception as e:
    # 静默失败
    pass