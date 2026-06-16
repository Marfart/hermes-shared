#!/usr/bin/env python3
"""
自学习系统 v2 — 快速脚本 (no_agent=True)
单次DDGS会话，3条主线各1话题，省去提取URL内容（用snippet代替）
必须控制在30秒内完成
"""
import json
import os, sys, re, ssl, urllib.request, urllib.parse
from datetime import datetime
# ddgs可能不在标准路径
import sys as _sys
import os as _os
_hermes_venv = _os.path.expanduser("~/AppData/Local/hermes/hermes-agent/venv/Lib/site-packages")
if _hermes_venv not in _sys.path:
    _sys.path.insert(0, _hermes_venv)
# cron环境可能清空sys.path，补回标准库路径
_stdlib = _os.path.join(_os.path.dirname(_os.__file__), "..", "Lib")
_stdlib = _os.path.normpath(_os.path.abspath(_stdlib))
if _stdlib not in _sys.path:
    _sys.path.insert(0, _stdlib)
import logging
from ddgs import DDGS

STATE_FILE = os.path.expanduser("~/AppData/Local/hermes/memories/自学习系统/self_learning_state.json")
KNOWLEDGE_DIR  = os.path.expanduser("~/AppData/Local/hermes/memories/自学习系统/知识库/")
OBSIDIAN_BASE  = os.path.expanduser("~/Documents/Obsidian Vault/01-学习笔记/自学习系统/")
os.makedirs(KNOWLEDGE_DIR, exist_ok=True)

PILLAR_EMOJIS  = {"赛博脚本小子":"💻", "机器人制造师":"🤖", "黑客":"💀"}
PILLAR_FOLDERS = {"赛博脚本小子":"脚本小子", "机器人制造师":"机器人制造师", "黑客":"黑客"}
PILLAR_NAMES   = ["赛博脚本小子", "机器人制造师", "黑客"]

def load_state():
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)
def save_state(s):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(s, f, ensure_ascii=False, indent=2)

def main():
    state = load_state()
    state["total_cycles"] += 1
    now = datetime.now()
    state["last_run"] = now.isoformat()
    pillars = state["pillars"]
    
    # 单次DDGS会话
    ddgs = DDGS()
    
    lines = [f"🔥 **三柱自学习报告 — 第{state['total_cycles']}轮**",
             f"⏰ {now.strftime('%Y-%m-%d %H:%M')}\n"]
    
    for pn in PILLAR_NAMES:
        p = pillars[pn]
        ti = p["current_topic"]
        topic = p["topics"][ti]
        folder = PILLAR_FOLDERS[pn]
        kfile  = os.path.join(KNOWLEDGE_DIR, f"{pn}.md")
        obsdir = os.path.join(OBSIDIAN_BASE, folder)
        os.makedirs(obsdir, exist_ok=True)
        
        # 1个查询，3条结果
        results = []
        try:
            for r in ddgs.text(f"{topic} 2026 tutorial", max_results=5):
                if len(results) < 4:
                    results.append(r)
        except:
            pass
        # 再试一个英文查询
        if not results:
            try:
                for r in ddgs.text(f"{topic.split('（')[0]} guide", max_results=4):
                    if len(results) < 3:
                        results.append(r)
            except:
                pass
        
        # 构建笔记
        safe = re.sub(r'[\s/\\:*?"<>|]', '', topic)[:35]
        note = [f"\n## {topic}\n> {now.strftime('%H:%M')} 轮{state['total_cycles']}\n"]
        if results:
            note.append(f"### 资源 ({len(results)}条)\n")
            for r in results:
                t = r.get("title","")[:60]
                u = r.get("href","")
                b = r.get("body","")[:150]
                note.append(f"- [{t}]({u})")
                if b: note.append(f"  {b}")
        else:
            note.append("*搜索暂无结果*\n")
        
        nc = "\n".join(note)
        with open(kfile, "a", encoding="utf-8") as f:
            f.write(nc + "\n---\n")
        
        obs = f"""---
topic: {topic}
pillar: {pn}
date: {now.strftime('%Y-%m-%d')}
cycle: {state['total_cycles']}
---
# {topic}
{nc}
"""
        with open(os.path.join(obsdir, f"{safe}.md"), "w", encoding="utf-8") as f:
            f.write(obs)
        
        # 报告
        brief = topic.split("（")[0][:20]
        sni = results[0].get("body","")[:100] if results else ""
        lines.append(f"\n{PILLAR_EMOJIS[pn]} **{pn}** — {brief}")
        if sni: lines.append(f"  {sni}")
        
        p["current_topic"] = (ti + 1) % p["total"]
    
    # 下轮
    nxt = []
    for pn in PILLAR_NAMES:
        nt = pillars[pn]["topics"][pillars[pn]["current_topic"]][:25]
        nxt.append(f"{PILLAR_EMOJIS[pn]}{nt}")
    
    lines.append(f"\n---\n📊 3篇笔记 | 下轮: {' | '.join(nxt)}")
    
    save_state(state)
    print("\n".join(lines), flush=True)

if __name__ == "__main__":
    main()