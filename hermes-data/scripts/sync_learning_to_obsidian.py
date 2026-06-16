#!/usr/bin/env python3
"""
sync_learning_to_obsidian.py v2 — 三柱体系支持
同步 memories/自学习系统/知识库/ → Obsidian Vault
"""
import os
import shutil
import hashlib
import json
from datetime import datetime

HERMES_HOME = os.path.expanduser("~/AppData/Local/hermes")
KNOWLEDGE_DIR = os.path.join(HERMES_HOME, "memories", "自学习系统", "知识库")
OBSIDIAN_BASE = os.path.expanduser("~/Documents/Obsidian Vault/01-学习笔记/自学习系统")
SYNC_STATE = os.path.join(HERMES_HOME, "memories", "自学习系统", "sync_state.json")

# 主线 → Obsidian文件夹映射
PILLAR_MAP = {
    "赛博脚本小子": "脚本小子",
    "机器人制造师": "机器人制造师",
    "黑客": "黑客"
}

def md5_file(path):
    if not os.path.exists(path):
        return ""
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()

def sync_file(src_path, dest_path):
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    src_md5 = md5_file(src_path)
    dest_md5 = md5_file(dest_path)
    if src_md5 and src_md5 != dest_md5:
        shutil.copy2(src_path, dest_path)
        return "updated"
    elif src_md5 and not dest_md5:
        shutil.copy2(src_path, dest_path)
        return "created"
    return "unchanged"

def load_state():
    if os.path.exists(SYNC_STATE):
        with open(SYNC_STATE, "r") as f:
            return json.load(f)
    return {"version": 2, "last_sync": None}

def save_state(state):
    with open(SYNC_STATE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def main():
    state = load_state()
    results = {"updated": 0, "created": 0}
    
    for pillar_name, folder in PILLAR_MAP.items():
        src = os.path.join(KNOWLEDGE_DIR, f"{pillar_name}.md")
        if not os.path.exists(src):
            continue
        dest = os.path.join(OBSIDIAN_BASE, folder, f"{pillar_name}.md")
        status = sync_file(src, dest)
        if status in ("updated", "created"):
            results[status] += 1
        
        # 也同步话题子目录
        obs_dir = os.path.join(OBSIDIAN_BASE, folder)
        for fname in os.listdir(obs_dir):
            if not fname.endswith(".md") or fname.startswith("_"):
                continue
            # 每个独立话题文件直接存在，不需要额外同步
            pass
    
    total = results["updated"] + results["created"]
    
    state["last_sync"] = datetime.now().isoformat()
    save_state(state)
    
    if total > 0:
        print(f"✅ Obsidian同步: {results['created']}新建 / {results['updated']}更新")

if __name__ == "__main__":
    main()