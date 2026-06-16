#!/usr/bin/env python3
"""
自学习系统 引导脚本 — 由cron每小时调用
读取状态文件 → 选3个领域 → 用stdout输出指令给agent执行

输出格式：agent会在下一轮读到stdout作为context
"""
import json
import os
from datetime import datetime

STATE_FILE = os.path.expanduser("~/AppData/Local/hermes/memories/自学习系统/self_learning_state.json")
KNOWLEDGE_DIR = os.path.expanduser("~/AppData/Local/hermes/memories/自学习系统/知识库/")
os.makedirs(KNOWLEDGE_DIR, exist_ok=True)

def load_state():
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def pick_domains(state):
    """循环选择3个领域，保证公平轮转"""
    domains = list(state["domains"].keys())
    last_idx = state.get("last_start_idx", 0)
    
    # 选出3个
    selected = []
    for i in range(3):
        idx = (last_idx + i) % len(domains)
        selected.append(domains[idx])
    
    state["last_start_idx"] = (last_idx + 1) % len(domains)
    return selected

def main():
    state = load_state()
    state["total_cycles"] += 1
    state["last_run"] = datetime.now().isoformat()
    
    selected = pick_domains(state)
    
    print("=" * 80)
    print(f"🔥 小马自学习系统 — 第 {state['total_cycles']} 轮")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    results = []
    for domain in selected:
        dom = state["domains"][domain]
        ti = dom["current_topic"]
        total = dom["total"]
        topic = dom["topics"][ti]
        kf = dom["knowledge_file"]
        kpath = os.path.join(KNOWLEDGE_DIR, kf)
        
        print(f"\n{'─' * 60}")
        print(f"📚 领域: {domain}")
        print(f"📖 当前话题 ({ti+1}/{total}): {topic}")
        print(f"📁 知识文件: {kpath}")
        print(f"{'─' * 60}")
        
        results.append({
            "domain": domain,
            "topic_index": ti,
            "total_topics": total,
            "topic": topic,
            "knowledge_file": kpath,
            "queries": [
                f"{topic} 教程 2026",
                f"{topic} 最佳实践 2026",
                f"{topic} GitHub项目",
                f"{topic} 高级技巧 2026"
            ]
        })
        
        # 更新状态（topic推进）
        dom["current_topic"] = (ti + 1) % total
    
    save_state(state)
    
    # 输出给agent的指令
    print("\n" + "=" * 80)
    print("🤖 AGENT 执行指令")
    print("=" * 80)
    print(json.dumps(results, ensure_ascii=False, indent=2))
    print("\n" + "=" * 80)
    print("📋 执行流程:")
    print("1. 读取以上JSON中的3个领域/话题")
    print("2. 对每个话题: web_search(4个query) → 提取内容 → 合成学习笔记")
    print("3. 保存学习笔记到knowledge_file路径")
    print("4. 输出学习总结报告（学到了什么/掌握了什么技能/能做什么新事情）")

if __name__ == "__main__":
    main()