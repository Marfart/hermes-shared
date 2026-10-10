#!/usr/bin/env python3
"""self_learning_v3.py — 小马自主真学习引擎 v3 (no_agent=True)"""

import sys as _sys, os as _os
_stdlib = _os.path.normpath(_os.path.abspath(
    _os.path.join(_os.path.dirname(_os.__file__), "..", "Lib")))
if _stdlib not in _sys.path:
    _sys.path.insert(0, _stdlib)

import json, os, re, subprocess, urllib.parse
from datetime import datetime

# ==== 配置 ====
STATE_DIR = _os.path.expanduser(
    "~/AppData/Local/hermes/memories/脚本缓存/自学习系统")
STATE_FILE = _os.path.join(STATE_DIR, "self_learning_agent.json")
OUTPUT_DIR = _os.path.join(STATE_DIR, "产出")
OBSIDIAN_BASE = _os.path.expanduser(
    "~/Documents/Obsidian Vault/01-学习笔记/自学习系统")
GITHUB_TOKEN=_os.environ.get("GITHUB_TOKEN", "")
PILLAR_LANGUAGES = {0: "Python,Shell,JavaScript", 1: "C,C++,Python,Rust", 2: "C,C++,Python,Rust,Go,Assembly"}
PILLAR_NAMES = {0: ("赛博脚本小子","\U0001f4bb"), 1: ("机器人制造师","\U0001f916"), 2: ("黑客","\U0001f480")}
ALL_TOPICS = {
    "赛博脚本小子": [
        "Bash高级脚本技巧","PowerShell自动化脚本","Python CLI脚本构建",
        "跨平台Shell脚本兼容性","脚本安全","定时任务脚本写作",
        "日志系统脚本","自动化测试脚本","Git钩子脚本","Docker容器编排脚本",
        "Python元编程","异步Python","CPython内部","Python性能优化",
        "网络编程","数据处理PandasNumPy","Web框架对比",
        "Python安全编程","测试金字塔","包管理",
        "Scrapy框架深度","Playwright反检测","请求模拟隐身技术",
        "数据提取","分布式爬虫架构","动态渲染页面爬取",
        "反反爬虫","大规模数据采集","APP数据抓取","爬虫法律合规",
        "设计模式实战","代码审查最佳实践","算法与数据结构",
        "函数式编程深度","编译原理入门","并发编程",
        "API设计","代码重构","性能优化","软件架构",
    ],
    "机器人制造师": [
        "嵌入式系统设计ARM RISC-V","树莓派ESP32实战","FPGA入门",
        "PCB设计基础","传感器技术","工业通信协议Modbus",
        "PLC编程","射频技术LoRa ZigBee","边缘计算硬件",
        "硬件逆向工程","Transformer架构精解","LLM训练三阶段",
        "微调技术LoRA","推理优化KV Cache","Agent框架设计",
        "RAG技术","Prompt Engineering","模型评估",
        "LLM安全","多模态模型","开源模型对比",
        "LLM部署vLLM","C指针深度","C++模板元编程",
        "C++内存模型","C++20新特性","STL源码剖析",
        "CMake构建系统","嵌入式C","C/C++安全",
        "Linux C编程","C++项目实战",
    ],
    "黑客": [
        "渗透测试方法论","Metasploit框架","Web漏洞挖掘",
        "内网横向移动","红队C2框架","逆向工程基础",
        "WiFi安全攻击","零日漏洞挖掘","EDR绕过技术",
        "云安全","OSINT开源情报","社交平台信息采集",
        "钓鱼攻击进阶","身份伪造社会工程","电话社工",
        "物理社工","数字足迹清理","社工防御",
        "x86汇编","ARM64汇编","系统调用机制",
        "内存管理深度","PE ELF文件格式","反编译反混淆",
        "Windows内核编程","Linux内核模块","Bootkit开发",
        "虚拟化底层","Linux内核架构","进程调度",
        "内存管理子系统","虚拟文件系统","网络栈Netfilter",
        "设备驱动模型","eBPF深度","容器底层",
        "内核调试","Kali内核定制","信息收集工具集",
        "漏洞扫描","Web应用测试","无线攻击","密码破解",
    ],
}
_os.makedirs(OUTPUT_DIR, exist_ok=True)
_os.makedirs(OBSIDIAN_BASE, exist_ok=True)

def curl_get(url, timeout=15):
    headers = ["-s", "-L"]
    if GITHUB_TOKEN:
        headers += ["-H", f"Authorization: Bearer {GITHUB_TOKEN}"]
    try:
        r = subprocess.run(["curl"] + headers + [url],
            capture_output=True, text=True, timeout=timeout)
        return r.stdout if r.returncode == 0 else ""
    except Exception:
        return ""

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", file=_sys.stderr)

def load_state():
    if _os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            log(f"状态文件损坏: {e}")
    return {
        "version": 3, "total_rounds": 0, "last_pillar": -1,
        "last_topic_per_pillar": {"赛博脚本小子": -1, "机器人制造师": -1, "黑客": -1},
        "learned_projects": [], "current_status": "initialized",
        "pillar_topics": {},
    }

def save_state(s):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(s, f, ensure_ascii=False, indent=2)

def select_topic(state):
    pillar_idx = (state["last_pillar"] + 1) % 3
    pname = ["赛博脚本小子","机器人制造师","黑客"][pillar_idx]
    topics = ALL_TOPICS.get(pname, [])
    if "pillar_topics" in state and state["pillar_topics"] and pname in state["pillar_topics"]:
        topics = state["pillar_topics"][pname]
    if "pillars" in state and state["pillars"]:
        for p in state["pillars"]:
            if p["name"] == pname:
                topics = p.get("topics", [])
                break
    if not topics:
        topics = ALL_TOPICS[pname]
    last_idx = state["last_topic_per_pillar"].get(pname, -1)
    topic_idx = (last_idx + 1) % len(topics)
    return pillar_idx, pname, topic_idx, topics[topic_idx], len(topics)

def search_github(topic, pillar_idx, learned):
    keywords = topic.split("（")[0].split("(")[0].strip()[:40]
    keywords = re.sub(r'[^\w\s-]', '', keywords).strip()
    topic_lower = topic.lower()
    if any(kw in topic_lower for kw in ["bash","shell","powershell","脚本"]):
        lang = "Shell"
    elif any(kw in topic_lower for kw in ["python","爬虫","异步"]):
        lang = "Python"
    elif any(kw in topic_lower for kw in ["c++","c语言","c指针","cpp","嵌入式c"]):
        lang = "C++"
    elif any(kw in topic_lower for kw in ["c","linux","内核","汇编","windows内核"]):
        lang = "C"
    elif any(kw in topic_lower for kw in ["rust","go"]):
        lang = "Rust"
    else:
        lang = PILLAR_LANGUAGES.get(pillar_idx, "Python").split(",")[0]
    url = (f"https://api.github.com/search/repositories"
           f"?q={urllib.parse.quote(keywords)}"
           f"+language:{urllib.parse.quote(lang)}"
           f"&sort=stars&order=desc&per_page=8")
    data = curl_get(url)
    if not data:
        url = (f"https://api.github.com/search/repositories"
               f"?q={urllib.parse.quote(keywords)}"
               f"&sort=stars&order=desc&per_page=8")
        data = curl_get(url)
    if not data: return None, None
    try:
        items = json.loads(data).get("items", [])
    except: return None, None
    if not items:
        url = (f"https://api.github.com/search/repositories"
               f"?q={urllib.parse.quote(keywords)}"
               f"&sort=stars&order=desc&per_page=8")
        data = curl_get(url)
        if not data: return None, None
        try:
            items = json.loads(data).get("items", [])
        except: return None, None
    for item in items:
        fn = item["full_name"]
        if fn in learned: continue
        if item.get("stargazers_count", 0) < 50: continue
        return item, fn
    for item in items:
        fn = item["full_name"]
        if fn in learned: continue
        if item.get("stargazers_count", 0) < 20: continue
        return item, fn
    return None, None

def read_github_file(owner, repo, path):
    c = curl_get(f"https://raw.githubusercontent.com/{owner}/{repo}/master/{path}")
    if c: return c
    return curl_get(f"https://raw.githubusercontent.com/{owner}/{repo}/main/{path}")

def generate_output(topic, project, readme_content, pillar_idx):
    desc = ""
    for line in readme_content.split("\n"):
        line = line.strip()
        if line and not line.startswith("#") and len(line) > 20:
            desc = line[:200]
            break
    tech_keywords = set()
    for p in [r'\b(python|bash|shell|docker|kubernetes|git|api)\b',
               r'\b(linux|windows|arm|riscv|aws|azure)\b',
               r'\b(AI|ML|LLM|transformer|RAG|agent)\b',
               r'\b(c|cpp|rust|go|java|typescript|wasm)\b']:
        for m in re.findall(p, readme_content, re.IGNORECASE):
            tech_keywords.add(m.lower())
    pillar_dir = PILLAR_NAMES[pillar_idx][0]
    safe_topic = re.sub(r'[\\/:*?"<>|]', '_', topic)[:40]
    obs_dir = _os.path.join(OBSIDIAN_BASE, pillar_dir)
    _os.makedirs(obs_dir, exist_ok=True)
    note_path = _os.path.join(obs_dir, f"{safe_topic}.md")
    stars = project.get("stargazers_count", "?")
    prj_url = project.get("html_url", "")
    lang = project.get("language", "")
    kw_list = ', '.join(sorted(tech_keywords)[:20])
    with open(note_path, "w", encoding="utf-8") as f:
        f.write(f"""# {PILLAR_NAMES[pillar_idx][1]} {project.get('name','?')}

**学习时间:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
**话题:** {topic}
**项目:** [{project.get('full_name','?')}]({prj_url})
**Stars:** {stars} ⭐
**语言:** {lang}
**描述:** {desc}

## 学到什么

{readme_content[:1000] if readme_content else 'README unavailable'}

## 技术关键词
{kw_list}
""")
    out_path = _os.path.join(OUTPUT_DIR, f"{safe_topic}.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(f"""# {topic} 学习产出

项目: {project.get('full_name','?')} ({stars}⭐)
语言: {lang}
描述: {desc[:300]}

## 核心信息
{readme_content[:2000]}

## 技术关键词
{kw_list}
""")
    return note_path, out_path, desc, sorted(tech_keywords)[:10]

def main():
    log("小马真学习 v3 启动")
    state = load_state()
    pillar_idx, pname, topic_idx, topic, total = select_topic(state)
    log(f"第1步 → 选中 {PILLAR_NAMES[pillar_idx][1]} {pname} #{topic_idx+1}/{total}: {topic}")

    learned = set(state.get("learned_projects", []))
    project, full_name = search_github(topic, pillar_idx, learned)
    if not project:
        log("⚠️ 没找到新项目，跳话题")
        state["last_pillar"] = pillar_idx
        state["last_topic_per_pillar"][pname] = topic_idx
        state["total_rounds"] = state.get("total_rounds", 0) + 1
        state["current_status"] = f"last_run: {datetime.now().strftime('%Y-%m-%dT%H:%M')}, topic: {topic}, project: none"
        save_state(state)
        print(f"⚠️ {PILLAR_NAMES[pillar_idx][1]} {topic} → 未找到新项目，跳过")
        return

    log(f"第2步 → {project.get('full_name','?')} ({project.get('stargazers_count','?')}⭐)")
    owner, repo = full_name.split("/")
    readme = read_github_file(owner, repo, "README.md")
    if not readme:
        readme = f"# {repo}\n\n{project.get('description','') or ''}"
    log(f"第3步 → README {len(readme)}字符")

    note_path, out_path, desc, keywords = generate_output(topic, project, readme, pillar_idx)
    log(f"第4步 → 产出 ok")

    learned.add(full_name)
    state["last_pillar"] = pillar_idx
    state["last_topic_per_pillar"][pname] = topic_idx
    state["learned_projects"] = list(learned)
    state["total_rounds"] = state.get("total_rounds", 0) + 1
    state["current_status"] = f"last_run: {datetime.now().strftime('%Y-%m-%dT%H:%M')}, topic: {topic}, project: {full_name}"
    save_state(state)

    next_p = (pillar_idx + 1) % 3
    next_pn = ["赛博脚本小子","机器人制造师","黑客"][next_p]
    safe_t = re.sub(r'[\\/:*?"<>|]', '_', topic)[:40]
    print(f"""🔥 自学习 #{state['total_rounds']} | {PILLAR_NAMES[pillar_idx][1]} {pname} | #{topic_idx+1}/{total}

📖 话题: {topic}

🔍 项目: {project.get('full_name','?')} ({project.get('stargazers_count','?')}⭐) — {desc[:120] if desc else project.get('description','')[:120]}

📦 学到:
• 项目定位: {desc[:200] if desc else '见产出文件'}
• 核心技术栈: {', '.join(keywords[:6])}
• 详细分析: 见 Obsidian 笔记

💾 产出: scripts缓存/自学习系统/产出/{safe_t}.md
📝 笔记: Obsidian → 01-学习笔记/自学习系统/{pname}/{safe_t}.md

⏭️ 下一轮: 15分钟后 | {PILLAR_NAMES[next_p][1]} {next_pn}""")

if __name__ == "__main__":
    main()