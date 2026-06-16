#!/usr/bin/env python3
"""
学习笔记记录器 — 小马边学边记到 Obsidian
=======================================
用法：
  python learn_noter.py "Python脚本" "生产级异常捕获" "笔记内容..."
  
自动在 Obsidian Vault 里创建笔记文件
"""

import sys
import json
from datetime import datetime
from pathlib import Path

VAULT = Path.home() / "Documents" / "Obsidian Vault"
NOTES_DIR = VAULT / "01-学习笔记"

def ensure_dir(category: str) -> Path:
    """确保分类目录存在"""
    cat_dir = NOTES_DIR / category
    cat_dir.mkdir(parents=True, exist_ok=True)
    return cat_dir

def to_filename(title: str) -> str:
    """中文标题 → 文件名"""
    # 保留中文和字母数字，空格换 -
    safe = "".join(c for c in title if c.isalnum() or c in " -_（）()")
    safe = safe.replace(" ", "-").strip("-")
    return safe if safe else "note"

def create_note(
    category: str,
    title: str,
    content: str,
    tags: list[str] = None,
    related: list[str] = None,
) -> Path:
    """创建一篇 Obsidian 学习笔记"""
    cat_dir = ensure_dir(category)
    filename = to_filename(title) + ".md"
    filepath = cat_dir / filename
    
    today = datetime.now().strftime("%Y-%m-%d")
    tags_str = " ".join(f"#{t}" for t in (tags or []))
    
    # 构建 Obsidian 前导 + 正文
    header = f"# {title}\n\n"
    header += f"> 📅 {today} | {tags_str}\n\n"
    header += "---\n\n"
    
    # 添加相关笔记链接
    if related:
        header += "**相关笔记：** "
        links = "、".join(f"[[{r}]]" for r in related)
        header += links + "\n\n---\n\n"
    
    body = content.strip()
    
    # 自动添加返回链接
    footer = "\n\n---\n> 🐾 小马自动记录 | [[学习笔记首页]]"
    
    full = header + body + footer
    filepath.write_text(full, encoding="utf-8")
    return filepath


def append_to_note(
    category: str,
    title: str,
    new_section: str,
) -> Path:
    """在已有笔记末尾追加内容"""
    cat_dir = ensure_dir(category)
    filename = to_filename(title) + ".md"
    filepath = cat_dir / filename
    
    if filepath.exists():
        existing = filepath.read_text(encoding="utf-8")
        # 在最后的 --- 前插入
        if existing.rstrip().endswith("---"):
            existing = existing.rstrip()[:-3].rstrip()
        updated = existing + f"\n\n---\n\n{new_section}\n"
        filepath.write_text(updated, encoding="utf-8")
    else:
        # 不存在就新建
        create_note(category, title, new_section)
    
    return filepath


def list_notes(category: str = None) -> list[dict]:
    """列出笔记"""
    root = NOTES_DIR / category if category else NOTES_DIR
    if not root.exists():
        return []
    
    notes = []
    for f in sorted(root.glob("*.md")):
        notes.append({
            "title": f.stem,
            "path": str(f),
            "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
        })
    return notes


def print_help():
    print("用法:")
    print("  python learn_noter.py create <分类> <标题> <内容> [标签] [相关笔记...]")
    print("  python learn_noter.py append <分类> <标题> <新内容>")
    print("  python learn_noter.py list [分类]")
    print()
    print("示例:")
    print('  python learn_noter.py create "Python脚本" "变量类型" "笔记内容..." "Python基础" "脚本工匠原则"')
    print('  python learn_noter.py append "Python脚本" "变量类型" "今天学了新的内容..."')
    print('  python learn_noter.py list "Python脚本"')
    print()
    print("分类: Python脚本 / Hermes技能 / BLIIOT业务 / 英语IELTS / 投资理财")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print_help()
        sys.exit(1)
    
    action = sys.argv[1]
    
    if action == "create":
        if len(sys.argv) < 5:
            print("缺少参数：create <分类> <标题> <内容>")
            sys.exit(1)
        cat = sys.argv[2]
        title = sys.argv[3]
        content = sys.argv[4]
        tags = sys.argv[5].split(",") if len(sys.argv) > 5 else []
        related = sys.argv[6:] if len(sys.argv) > 6 else []
        path = create_note(cat, title, content, tags, related)
        print(f"✅ 笔记已创建: {path}")
        
    elif action == "append":
        if len(sys.argv) < 5:
            print("缺少参数：append <分类> <标题> <新内容>")
            sys.exit(1)
        cat = sys.argv[2]
        title = sys.argv[3]
        content = sys.argv[4]
        path = append_to_note(cat, title, content)
        print(f"✅ 笔记已更新: {path}")
        
    elif action == "list":
        cat = sys.argv[2] if len(sys.argv) > 2 else None
        notes = list_notes(cat)
        if not notes:
            print("📭 暂无笔记")
        else:
            for n in notes:
                print(f"  📄 {n['title']}")
        print(f"总计: {len(notes)} 篇")
        
    else:
        print(f"未知操作: {action}")
        print_help()
        sys.exit(1)