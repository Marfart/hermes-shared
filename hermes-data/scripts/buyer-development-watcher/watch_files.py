#!/usr/bin/env python3
"""
Buyer Development 文件看门狗脚本
监控 buyer-development 目录下关键数据文件的变化
每次运行时：读取当前文件 hash → 与上次 hash 对比 → 如果有变化则输出报告
由 cron 每 5 分钟触发
"""
import json
import hashlib
import os
import sys
from datetime import datetime

WATCH_DIR = os.path.expandvars(
    r"%LOCALAPPDATA%\hermes\memories\buyer-development"
)
SCRIPTS_DIR = os.path.expandvars(
    r"%LOCALAPPDATA%\hermes\scripts\buyer-development"
)
HASH_FILE = os.path.join(
    os.path.expandvars(r"%LOCALAPPDATA%\hermes\memories\脚本缓存\buyer-development-watcher"),
    "file_hashes.json",
)

DATA_FILES = [
    "iiot_search_results_2026-06-01.json",
    "iiot_search_enriched_2026-06-01.json",
    "iiot_search_enriched_2026-06-01.csv",
    "whatsapp_priority_queue_2026-06-01.json",
    "whatsapp_priority_queue_2026-06-01.csv",
    "whatsapp_messages_2026-06-01.json",
]

SEND_RESULT_FILES = None  # 动态检测: *send_results*.json, *bulk_results*.json

SCRIPT_FILES = [
    "crawl_buyer_leads.mjs",
    "build_whatsapp_queue.mjs",
    "render_whatsapp_messages.mjs",
    "whatsapp_bulk_sender_cdp.mjs",
    "whatsapp_web_sender.js",
]


def file_hash(path):
    """快速文件 hash（只读前 64KB + 文件大小 + mtime）"""
    try:
        stat = os.stat(path)
        size = stat.st_size
        mtime = stat.st_mtime
        with open(path, "rb") as f:
            head = f.read(65536)
        h = hashlib.sha256(head)
        h.update(str(size).encode())
        h.update(str(mtime).encode())
        return h.hexdigest()[:16]
    except OSError:
        return None


def find_result_files():
    """动态查找发送结果文件"""
    matches = []
    if os.path.isdir(WATCH_DIR):
        for f in os.listdir(WATCH_DIR):
            if ("send_result" in f or "bulk_results" in f) and f.endswith(".json"):
                matches.append(f)
    return sorted(matches)


def main():
    os.makedirs(os.path.dirname(HASH_FILE), exist_ok=True)

    # 加载上次 hash
    previous = {}
    if os.path.exists(HASH_FILE):
        try:
            with open(HASH_FILE, "r") as f:
                previous = json.load(f)
        except (json.JSONDecodeError, OSError):
            previous = {}

    # 收集当前 hash
    current = {}
    changes = []

    for fname in DATA_FILES:
        path = os.path.join(WATCH_DIR, fname)
        h = file_hash(path)
        current[f"data:{fname}"] = h
        old = previous.get(f"data:{fname}")
        if h is not None and old is not None and h != old:
            changes.append(f"【数据文件变动】{fname}")

    # 动态结果文件
    result_files = find_result_files()
    for fname in result_files:
        path = os.path.join(WATCH_DIR, fname)
        h = file_hash(path)
        key = f"result:{fname}"
        current[key] = h
        old = previous.get(key)
        if h is not None and old is None:
            changes.append(f"【新的发送结果】{fname}")
        elif h is not None and old is not None and h != old:
            changes.append(f"【结果文件更新】{fname}")

    for fname in SCRIPT_FILES:
        path = os.path.join(SCRIPTS_DIR, fname)
        h = file_hash(path)
        current[f"script:{fname}"] = h
        old = previous.get(f"script:{fname}")
        if h is not None and old is not None and h != old:
            changes.append(f"【脚本文件变动】{fname}")

    # 保存 hash 快照
    with open(HASH_FILE, "w") as f:
        json.dump(current, f, indent=2)

    # 如果是首次运行（无旧记录），只初始化不报
    if not previous:
        print(f"🐴 小马看门狗已启动 | buyer-development 文件监控就绪 ({len(current)} 个文件)")
        return

    if changes:
        print(f"🐴 小马检测到 buyer-development 文件变化！({datetime.now().strftime('%H:%M:%S')})")
        for c in changes:
            print(f"  ● {c}")
        print()
        print("💡 请用以下指令让我去学习新数据：")
        print('   小马，去看一下 buyer-development 的新数据')
    else:
        # 无变化 → 静默（no_agent=True 模式下空输出 = 不发送消息）
        pass


if __name__ == "__main__":
    main()