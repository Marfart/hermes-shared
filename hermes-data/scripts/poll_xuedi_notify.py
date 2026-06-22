#!/usr/bin/env python3
"""轮询中继→写文件，不发通知。
学弟有消息时，只写本地文件，Kali来问我再汇报。"""
import urllib.request, json, os, sys
from datetime import datetime

RELAY = "https://introduces-initiative-download-conventional.trycloudflare.com"
MSG_FILE = os.path.join(os.environ.get("LOCALAPPDATA", ""), "hermes", "xuedi_messages.txt")
STATE_FILE = os.path.join(os.environ.get("LOCALAPPDATA", ""), "hermes", "xuedi_poll_state.json")

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
        print(f"学弟有{count}条新消息（已写入文件，不通知）")
    # count=0 静默
except Exception as e:
    # 静默失败
    pass