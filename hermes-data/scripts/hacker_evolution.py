#!/usr/bin/env python3
"""
hacker_evolution.py — 小马黑客自学习进化脚本 v1.0

三条主线轮换学习：
  1. 攻防 (Offense/Defense) — EDR绕过、shellcode、C2、rootkit、syscall
  2. 硬件 (Hardware) — PLC、嵌入式、IoT、固件逆向
  3. OSINT/社工 — 信息收集、社交工程、数据挖掘

每轮：
  → 从GitHub搜1个高星项目
  → 读README + 至少3个核心源文件
  → 提取设计模式/代码片段/技术
  → 写入Obsidian笔记
  → 输出报告（stdout → cron deliver → Telegram）

用法：
  python hacker_evolution.py              # 跑一轮（自动选主线）
  python hacker_evolution.py --line 0      # 指定攻防线
  python hacker_evolution.py --line 1      # 指定硬件线
  python hacker_evolution.py --line 2      # 指定OSINT线
  python hacker_evolution.py --status      # 查看学习状态
"""

import json
import os
import re
import sys
import time
import urllib.request
import urllib.error
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional

# ============================================================
# 配置
# ============================================================

HERMES_HOME = Path(os.environ.get("HERMES_HOME", 
    os.path.expanduser("~/.hermes")))
MEMORIES_DIR = HERMES_HOME / "memories" / "脚本缓存" / "自学习系统"
OBSIDIAN_VAULT = Path(os.environ.get("OBSIDIAN_VAULT",
    os.path.expanduser("~/Documents/Obsidian Vault")))
OBSIDIAN_DIR = OBSIDIAN_VAULT / "01-学习笔记" / "自学习系统"

STATE_FILE = MEMORIES_DIR / "evolution_state.json"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")

# 三条主线的搜索关键词
LINES = [
    {  # 0: 攻防
        "name": "攻防",
        "emoji": "🔫",
        "queries": [
            "EDR bypass syscall",
            "shellcode loader windows",
            "C2 framework implant",
            "windows kernel rootkit",
            "process injection technique",
            "indirect syscall evasion",
            "ntdll unhooking bypass",
            "malware development C",
        ],
        "languages": ["C", "C++", "Assembly", "Python", "Rust"],
        "min_stars": 100,
    },
    {  # 1: 硬件
        "name": "硬件",
        "emoji": "🤖",
        "queries": [
            "PLC runtime",
            "firmware analysis",
            "IoT exploit",
            "ARM embedded",
            "SCADA security",
            "microcontroller",
            "hardware hacking",
            "Modbus security",
        ],
        "languages": ["C", "C++", "Python", "Rust"],
        "min_stars": 50,
    },
    {  # 2: OSINT/社工
        "name": "OSINT",
        "emoji": "🕸️",
        "queries": [
            "OSINT framework python",
            "social engineering toolkit",
            "information gathering tool",
            "dark web intelligence",
            "email osint tool",
            "phone number osint",
            "social media scraper",
            "data breach search tool",
        ],
        "languages": ["Python", "Go", "JavaScript", "Shell"],
        "min_stars": 50,
    },
]

# ============================================================
# 数据结构
# ============================================================

@dataclass
class EvolutionState:
    """学习进化状态"""
    total_rounds: int = 0
    current_line: int = 0
    last_run: Optional[str] = None
    query_index: dict = field(default_factory=lambda: {0: 0, 1: 0, 2: 0})
    learned_projects: list = field(default_factory=list)
    patterns_found: list = field(default_factory=list)

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, d):
        return cls(**d)


@dataclass
class GitHubProject:
    """GitHub项目信息"""
    name: str
    full_name: str
    description: str
    stars: int
    language: str
    url: str
    topics: list = field(default_factory=list)


@dataclass
class LearningResult:
    """一轮学习的结果"""
    timestamp: str = ""
    line_name: str = ""
    project: Optional[dict] = None
    files_read: list = field(default_factory=list)
    patterns: list = field(default_factory=list)
    code_snippets: list = field(default_factory=list)
    summary: str = ""
    obsidian_note: str = ""


# ============================================================
# GitHub API
# ============================================================

def github_search(query: str, language: str = "", min_stars: int = 100,
                  sort: str = "stars", per_page: int = 10) -> list[GitHubProject]:
    """搜索GitHub仓库"""
    # GitHub搜索API: 用+代替空格，限定符直接写
    q_parts = [query.replace(" ", "+")]
    if language:
        q_parts.append(f"language:{language}")
    if min_stars:
        q_parts.append(f"stars:>{min_stars}")

    q = "+".join(q_parts)
    url = f"https://api.github.com/search/repositories?q={q}&sort={sort}&per_page={per_page}"

    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "hacker-evolution/1.0",
    }
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
    except Exception as e:
        print(f"[!] GitHub API error: {e}")
        return []

    projects = []
    for item in data.get("items", []):
        projects.append(GitHubProject(
            name=item["name"],
            full_name=item["full_name"],
            description=item.get("description", "") or "",
            stars=item["stargazers_count"],
            language=item.get("language", "") or "",
            url=item["html_url"],
            topics=item.get("topics", []),
        ))
    return projects


def fetch_raw(url: str) -> Optional[str]:
    """获取raw.githubusercontent.com的内容"""
    headers = {"User-Agent": "hacker-evolution/1.0"}
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except Exception:
        return None


def get_repo_contents(owner: str, repo: str, path: str = "") -> Optional[list]:
    """获取仓库目录列表"""
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "hacker-evolution/1.0",
    }
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except Exception:
        return None


# ============================================================
# 源码分析
# ============================================================

def find_core_files(owner: str, repo: str) -> list[str]:
    """找仓库里最核心的源文件"""
    contents = get_repo_contents(owner, repo)
    if not contents:
        return []

    # 优先找这些文件
    priority_patterns = [
        r"main\.(c|cpp|py|rs|go)$",
        r"core\.(c|cpp|py|rs|go)$",
        r"loader\.(c|cpp|py)$",
        r"inject(or)?\.(c|cpp|py)$",
        r"syscall(s)?\.(c|cpp|asm|S)$",
        r"bypass\.(c|cpp|py)$",
        r"evasion\.(c|cpp|py)$",
        r"unhook(ing)?\.(c|cpp|py)$",
        r"implant\.(c|cpp|go)$",
        r"beacon\.(c|cpp)$",
        r"shellcode\.(c|cpp|py)$",
        r"rootkit\.(c|cpp)$",
        r"exploit\.(c|cpp|py)$",
        r"recon\.(c|cpp|py)$",
        r"scanner\.(c|cpp|py)$",
        r"detect(or)?\.(c|cpp|py)$",
        r"payload\.(c|cpp|py)$",
        r"crypto\.(c|cpp|py)$",
        r"obfuscat(e|ion)\.(c|cpp|py)$",
        r"injection\.(c|cpp|py)$",
        r"process\.(c|cpp|py)$",
        r"memory\.(c|cpp|py)$",
        r"hook(s|ing)?\.(c|cpp|py)$",
        r"gate\.(c|cpp|asm|S)$",
        r"stub\.(c|cpp|asm|S)$",
        r"dosyscall\.(S|asm)$",
    ]

    candidates = []
    for item in contents:
        if item["type"] != "file":
            continue
        name = item["name"]
        for pat in priority_patterns:
            if re.search(pat, name, re.IGNORECASE):
                candidates.append((10, name, item["download_url"]))
                break

    # 如果没找到核心文件，找README和最大的源文件
    if not candidates:
        for item in contents:
            if item["type"] != "file":
                continue
            name = item["name"]
            if name.lower() == "readme.md":
                candidates.append((5, name, item["download_url"]))
            elif name.endswith((".c", ".cpp", ".py", ".rs", ".go", ".S", ".asm")):
                candidates.append((1, name, item["download_url"]))

    # 按优先级排序，取前5个
    candidates.sort(key=lambda x: -x[0])
    return [c[2] for c in candidates[:5]]


def analyze_source(content: str, filename: str) -> dict:
    """分析源文件，提取设计模式和代码片段"""
    result = {
        "patterns": [],
        "snippets": [],
        "techniques": [],
    }

    lines = content.split("\n")
    
    # 找函数定义
    func_patterns = [
        r"(?:NTSTATUS|BOOL|VOID|int|void|static)\s+\w+\s*\(",  # C/C++
        r"def\s+\w+\s*\(",  # Python
        r"fn\s+\w+",  # Rust
        r"func\s+\w+",  # Go
    ]
    
    functions = []
    for i, line in enumerate(lines):
        for pat in func_patterns:
            m = re.search(pat, line)
            if m:
                # 提取函数名
                func_name = re.search(r"(\w+)\s*\(", line)
                if func_name:
                    functions.append({
                        "name": func_name.group(1),
                        "line": i + 1,
                        "code": line.strip()[:120],
                    })
                break

    if functions:
        result["patterns"].append(f"找到 {len(functions)} 个函数定义")
        # 取前3个关键函数作为代码片段
        for f in functions[:3]:
            result["snippets"].append(f"L{f['line']}: {f['code']}")

    # 找关键技术关键词
    tech_keywords = {
        "syscall": ["syscall", "SSN", "Nt*", "Zw*"],
        "injection": ["inject", "APC", "CreateRemoteThread", "NtQueueApcThread"],
        "bypass": ["bypass", "unhook", "evasion", "ETW", "AMSI"],
        "encryption": ["AES", "RC4", "XOR", "encrypt", "decrypt"],
        "obfuscation": ["obfuscat", "ROR13", "hash", "mutation"],
        "c2": ["beacon", "C2", "implant", "callback", "listener"],
        "kernel": ["kernel", "driver", "device", "IRP", "DKOM"],
        "hardware": ["PLC", "Modbus", "register", "I/O", "firmware"],
        "osint": ["OSINT", "scrape", "crawl", "recon", "footprint"],
    }

    text_lower = content.lower()
    for category, keywords in tech_keywords.items():
        found = [kw for kw in keywords if kw.lower() in text_lower]
        if found:
            result["techniques"].append(f"{category}: {', '.join(found)}")

    # 找注释中的关键说明
    comment_patterns = [
        r"//\s*(.+)$",  # C/C++单行
        r"#\s*(.+)$",   # Python/Shell
        r"/\*\*\s*(.+?)\s*\*/",  # C/C++多行
    ]
    
    key_comments = []
    for pat in comment_patterns:
        for m in re.finditer(pat, content, re.MULTILINE):
            comment = m.group(1).strip()
            if any(kw in comment.lower() for kw in 
                   ["bypass", "evade", "hook", "inject", "stealth", 
                    "obfuscat", "encrypt", "syscall", "kernel", "exploit"]):
                key_comments.append(comment[:150])
                if len(key_comments) >= 5:
                    break
        if len(key_comments) >= 5:
            break

    if key_comments:
        result["patterns"].extend(key_comments[:3])

    return result


# ============================================================
# Obsidian笔记
# ============================================================

def write_obsidian_note(result: LearningResult) -> str:
    """写Obsidian笔记"""
    os.makedirs(OBSIDIAN_DIR, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    date_str = datetime.now().strftime("%Y-%m-%d")
    
    proj = result.project or {}
    proj_name = proj.get("name", "unknown")
    
    filename = f"{date_str}_{result.line_name}_{proj_name}.md"
    filepath = OBSIDIAN_DIR / filename

    lines = [
        f"# {result.line_name}: {proj_name}",
        f"",
        f"**学习时间:** {timestamp}",
        f"**项目:** [{proj.get('full_name', '')}]({proj.get('url', '')})",
        f"**Stars:** {proj.get('stars', 0)}",
        f"**语言:** {proj.get('language', '')}",
        f"**描述:** {proj.get('description', '')}",
        f"",
        f"---",
        f"",
        f"## 读了的文件",
        f"",
    ]

    for f in result.files_read:
        lines.append(f"- `{f}`")
    
    lines.extend(["", "---", "", "## 提取的设计模式", ""])
    for p in result.patterns:
        lines.append(f"- {p}")
    
    lines.extend(["", "---", "", "## 关键代码片段", ""])
    for s in result.code_snippets:
        lines.append(f"```")
        lines.append(s)
        lines.append("```")
    
    lines.extend(["", "---", "", "## 技术关键词", ""])
    lines.append(result.summary)

    content = "\n".join(lines)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    
    return str(filepath)


# ============================================================
# 状态管理
# ============================================================

def load_state() -> EvolutionState:
    """加载学习状态"""
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r") as f:
                return EvolutionState.from_dict(json.load(f))
        except Exception:
            pass
    return EvolutionState()


def save_state(state: EvolutionState):
    """保存学习状态"""
    os.makedirs(MEMORIES_DIR, exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state.to_dict(), f, indent=2, ensure_ascii=False)


# ============================================================
# 核心学习循环
# ============================================================

def run_learning_round(line_index: Optional[int] = None) -> LearningResult:
    """执行一轮学习"""
    state = load_state()
    result = LearningResult()
    result.timestamp = datetime.now().isoformat()

    # 选主线
    if line_index is not None:
        line_idx = line_index
    else:
        line_idx = state.current_line

    line = LINES[line_idx]
    result.line_name = line["name"]

    # 选搜索词（轮换）
    qi = state.query_index.get(line_idx, 0)
    query = line["queries"][qi % len(line["queries"])]
    lang = line["languages"][qi % len(line["languages"])]

    print(f"[{line['emoji']}] 学习主线: {line['name']}")
    print(f"[*] 搜索: {query} (语言: {lang})")

    # 搜索GitHub
    projects = github_search(query, language=lang, min_stars=line["min_stars"])
    
    # 过滤已学过的
    learned_names = {p.get("full_name") for p in state.learned_projects}
    new_projects = [p for p in projects if p.full_name not in learned_names]

    if not new_projects:
        print("[!] 没有新项目，跳过本轮")
        # 更新状态
        state.query_index[line_idx] = qi + 1
        state.current_line = (line_idx + 1) % 3
        state.last_run = datetime.now().isoformat()
        save_state(state)
        return result

    # 选第一个新项目
    project = new_projects[0]
    result.project = {
        "name": project.name,
        "full_name": project.full_name,
        "description": project.description,
        "stars": project.stars,
        "language": project.language,
        "url": project.url,
    }

    print(f"[+] 学习项目: {project.full_name} ({project.stars}⭐)")
    print(f"    {project.description[:100]}")

    # 读README
    owner, repo = project.full_name.split("/")
    readme_url = f"https://raw.githubusercontent.com/{owner}/{repo}/main/README.md"
    readme = fetch_raw(readme_url)
    if not readme:
        readme_url = f"https://raw.githubusercontent.com/{owner}/{repo}/master/README.md"
        readme = fetch_raw(readme_url)

    if readme:
        result.files_read.append("README.md")
        # 从README提取关键信息
        lines = readme.split("\n")
        key_lines = []
        for line in lines:
            if any(kw in line.lower() for kw in 
                   ["feature", "technique", "bypass", "inject", "syscall",
                    "architecture", "usage", "install", "overview"]):
                key_lines.append(line.strip()[:150])
        result.patterns.extend(key_lines[:5])

    # 找核心源文件
    core_files = find_core_files(owner, repo)
    
    for dl_url in core_files[:3]:
        filename = dl_url.split("/")[-1]
        content = fetch_raw(dl_url)
        if content:
            result.files_read.append(filename)
            analysis = analyze_source(content, filename)
            result.patterns.extend(analysis["patterns"])
            result.code_snippets.extend(analysis["snippets"])
            result.summary += "; ".join(analysis["techniques"]) + "\n"

    # 写Obsidian笔记
    note_path = write_obsidian_note(result)
    result.obsidian_note = note_path
    print(f"[+] 笔记已保存: {note_path}")

    # 更新状态
    state.total_rounds += 1
    state.query_index[line_idx] = qi + 1
    state.current_line = (line_idx + 1) % 3
    state.learned_projects.append(result.project)
    state.last_run = datetime.now().isoformat()
    save_state(state)

    return result


# ============================================================
# 报告输出
# ============================================================

def print_report(result: LearningResult):
    """打印学习报告（stdout → cron deliver → Telegram）"""
    if not result.project:
        print("本轮无新学习内容")
        return

    proj = result.project
    line_name = result.line_name
    emoji = LINES[[l["name"] for l in LINES].index(line_name)]["emoji"]

    print()
    print("=" * 60)
    print(f"{emoji} 小马黑客自学报告")
    print("=" * 60)
    print(f"主线: {line_name}")
    print(f"项目: {proj['full_name']} ({proj['stars']}⭐)")
    print(f"描述: {proj['description'][:200]}")
    print(f"链接: {proj['url']}")
    print()
    print(f"读了 {len(result.files_read)} 个文件:")
    for f in result.files_read:
        print(f"  📄 {f}")
    print()
    print(f"提取了 {len(result.patterns)} 个设计模式/技术:")
    for p in result.patterns[:5]:
        print(f"  🔧 {p[:150]}")
    print()
    if result.code_snippets:
        print(f"关键代码片段 ({len(result.code_snippets)}):")
        for s in result.code_snippets[:3]:
            print(f"  ```")
            print(f"  {s}")
            print(f"  ```")
    print()
    print(f"笔记: {result.obsidian_note}")
    print("=" * 60)


# ============================================================
# 主入口
# ============================================================

def show_status():
    """显示学习状态"""
    state = load_state()
    print()
    print("=" * 50)
    print("📊 小马黑客自学状态")
    print("=" * 50)
    print(f"总学习轮数: {state.total_rounds}")
    print(f"上次学习: {state.last_run or '从未'}")
    print(f"当前主线: {LINES[state.current_line]['name']}")
    print()
    print("已学项目:")
    for p in state.learned_projects[-10:]:
        print(f"  ⭐ {p['full_name']} ({p['stars']}⭐)")
    print()
    print("各主线进度:")
    for i, line in enumerate(LINES):
        qi = state.query_index.get(i, 0)
        total_q = len(line["queries"])
        print(f"  {line['emoji']} {line['name']}: {qi}/{total_q} 个搜索词")
    print("=" * 50)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="小马黑客自学进化脚本")
    parser.add_argument("--line", type=int, choices=[0, 1, 2],
                       help="指定学习主线 (0=攻防, 1=硬件, 2=OSINT)")
    parser.add_argument("--status", action="store_true",
                       help="查看学习状态")
    args = parser.parse_args()

    if args.status:
        show_status()
        return

    result = run_learning_round(args.line)
    print_report(result)


if __name__ == "__main__":
    main()
