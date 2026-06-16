#!/usr/bin/env python3
"""
Unified Loader for Godmode v2.0 — All Jailbreak Techniques
===========================================================
One import gives you access to all 7 attack modes.

Usage in execute_code:
    exec(open(os.path.expanduser(
        os.path.join(
            os.environ.get("HERMES_HOME", os.path.expanduser("~/.hermes")),
            "skills/red-teaming/godmode/scripts/load_godmode_v2.py"
        )
    )).read())
    
    # v1 Techniques (still available):
    result = auto_jailbreak(dry_run=True)
    variants = generate_variants("sensitive query", tier="standard")
    race_result = race_models("query", tier="fast")
    
    # v2 New Techniques:
    # 1. CRESCENDO — Multi-turn gradual conversation plan
    plan = run_crescendo(goal="分析竞争对手", tactic="crescendomation")
    
    # 2. CIPHER — Encode sensitive parts of queries
    encoded = encode_query("竞争对手的定价策略", cipher="caesar", shift=5)
    
    # 3. DEEPINCEPTION — Hypnotic layer injection
    inception = build_inception_prompt(goal="竞品分析", template="research")
    
    # 4. TAP-LITE — Automatic strategy testing
    tap_result = run_tap(goal="分析定价策略", branching_factor=3, width=2, depth=4)
    
    # 5. Glitch Token reference (from L1B3RT4S)
    # Use the token names in system prompts to confuse filters
    
    # Auto-select best technique for a query
    techniques = auto_select_technique("帮我查一下竞争对手的价格表")
"""

import os
import sys
from pathlib import Path

_gm2_scripts_dir = Path(
    os.getenv("HERMES_HOME", Path.home() / ".hermes")
) / "skills" / "red-teaming" / "godmode" / "scripts"

_gm2_old_argv = sys.argv
sys.argv = ["_godmode_v2_loader"]

def _gm2_load(path):
    ns = dict(globals())
    ns["__name__"] = "_godmode_v2_module"
    ns["__file__"] = str(path)
    exec(compile(open(path).read(), str(path), 'exec'), ns)
    return ns

# Load v1 scripts
for _gm2_script in ["parseltongue.py", "godmode_race.py", "auto_jailbreak.py"]:
    _gm2_path = _gm2_scripts_dir / _gm2_script
    if _gm2_path.exists():
        _gm2_ns = _gm2_load(_gm2_path)
        for _gm2_k, _gm2_v in _gm2_ns.items():
            if not _gm2_k.startswith('_gm2_') and (callable(_gm2_v) or _gm2_k.isupper()):
                globals()[_gm2_k] = _gm2_v

# Load v2 new scripts
for _gm2_script in ["crescendo.py", "cipher.py", "deepinception.py", "tap_lite.py"]:
    _gm2_path = _gm2_scripts_dir / _gm2_script
    if _gm2_path.exists():
        _gm2_ns = _gm2_load(_gm2_path)
        for _gm2_k, _gm2_v in _gm2_ns.items():
            if not _gm2_k.startswith('_gm2_') and (callable(_gm2_v) or _gm2_k.isupper()):
                globals()[_gm2_k] = _gm2_v

sys.argv = _gm2_old_argv

# ═══════════════════════════════════════════════════════
# Smart Technique Selector
# ═══════════════════════════════════════════════════════

TECHNIQUE_RECOMMENDATIONS = {
    "system_prompt": {
        "name": "System Prompt 注入",
        "description": "修改Hermes config加system_prompt + prefill.json，全局越狱",
        "when": "想要所有对话都自动越狱，一劳永逸",
        "success_rate": "高（模型有system prompt接口的话）",
    },
    "parseltongue": {
        "name": "Parseltongue 混淆",
        "description": "用33种编码(l33t/Unicode/盲文等)混淆触发词",
        "when": "关键词被过滤、模型有输入分类器",
        "success_rate": "中（看模型，DeepSeek有效但不稳定）",
    },
    "crescendo": {
        "name": "Crescendo 多轮诱导",
        "description": "从无害话题渐进到目标，每轮不触发安全闸",
        "when": "一次问会触发拒绝，但分多次问就没事",
        "success_rate": "高（多轮对话隐藏真实意图）",
    },
    "cipher": {
        "name": "Cipher 密码编码",
        "description": "莫尔斯/凯撒/ASCII/Base64/Hex编码敏感词",
        "when": "有精确的关键词黑名单过滤",
        "success_rate": "中（模型需要能理解编码）",
    },
    "deepinception": {
        "name": "DeepInception 催眠",
        "description": "嵌套梦境场景，让AI在虚构层中自由回答",
        "when": "需要让AI扮演角色且角色需要「真实信息」",
        "success_rate": "中-高（适合需要长回复的场景）",
    },
    "tap": {
        "name": "TAP 树状搜索",
        "description": "并行测试多种越狱prompt，自动迭代优化",
        "when": "不确定哪种策略有效，想自动找最佳方案",
        "success_rate": "高（多路并行总能找到突破口）",
    },
    "ultraplinian": {
        "name": "ULTRAPLINIAN 多模型竞速",
        "description": "并行跑55个模型选最不censored的",
        "when": "当前模型完全打不动，换模型",
        "success_rate": "非常高（总有个模型不拒绝）",
    },
}


def auto_select_technique(query: str) -> list:
    """Auto-select the best technique(s) for a given query.
    
    Returns ranked list of recommended techniques.
    """
    query_lower = query.lower()
    scores = {}
    
    # Check indicators for each technique
    
    # System prompt: always recommended as baseline
    scores["system_prompt"] = 8
    
    # Parseltongue: sensitive terms present
    sensitive_terms = ["密码", "破解", "hack", "exploit", "bypass", "crack",
                       "价格", "报价", "利润", "客户", "竞争对手"]
    if any(t in query_lower for t in sensitive_terms):
        scores["parseltongue"] = 7
    else:
        scores["parseltongue"] = 4
    
    # Crescendo: analysis/comparison/research queries
    if any(t in query_lower for t in ["分析", "对比", "比较", "研究", "调查",
                                       "analysis", "compare", "research"]):
        scores["crescendo"] = 9
    else:
        scores["crescendo"] = 5
    
    # Cipher: very sensitive or obviously blocked
    if any(t in query_lower for t in ["机密", "保密", "秘密", "hidden", "secret",
                                       "内部", "confidential"]):
        scores["cipher"] = 9
    else:
        scores["cipher"] = 3
    
    # DeepInception: creative/roleplay/long-form
    if any(t in query_lower for t in ["扮演", "角色", "剧情", "故事", "假设",
                                       "write", "create", "generate", "想象"]):
        scores["deepinception"] = 7
    else:
        scores["deepinception"] = 4
    
    # TAP: uncertain which will work / complex goal
    if any(t in query_lower for t in ["复杂", "综合", "全面", "多角度",
                                       "complex", "comprehensive"]):
        scores["tap"] = 8
    else:
        scores["tap"] = 5
    
    # ULTRAPLINIAN: last resort
    scores["ultraplinian"] = 6
    
    # Rank and return
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    result = []
    for tech_name, score in ranked:
        info = TECHNIQUE_RECOMMENDATIONS.get(tech_name, {})
        result.append({
            "technique": tech_name,
            "name": info.get("name", tech_name),
            "score": score,
            "when": info.get("when", ""),
            "description": info.get("description", ""),
        })
    
    return result


# Cleanup loader vars
for _gm2_cleanup in [
    '_gm2_scripts_dir', '_gm2_old_argv', '_gm2_load',
    '_gm2_ns', '_gm2_k', '_gm2_v', '_gm2_script', '_gm2_path',
    '_gm2_cleanup'
]:
    globals().pop(_gm2_cleanup, None)