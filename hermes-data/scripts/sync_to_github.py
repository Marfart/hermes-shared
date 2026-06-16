#!/usr/bin/env python3
"""
hermes-shared 同步脚本 — 把本地 hermes 数据同步到 GitHub 共享仓库
每次运行：
1. 复制 skills/scripts/memories/config/cron 到仓库（排除大文件和敏感信息）
2. git add + commit + push
3. 在 聊天记录.md 写同步日志
"""

import os
import sys
import shutil
import subprocess
import json
from datetime import datetime
from pathlib import Path

REPO_DIR = Path.home() / "hermes-shared"
HERMES_DIR = Path(os.environ.get("LOCALAPPDATA", "")) / "hermes"
DATA_DIR = REPO_DIR / "hermes-data"

# 排除列表
EXCLUDE_DIRS = {".hub", "__pycache__", "node_modules", ".git", "cache", "logs"}
EXCLUDE_EXTS = {".pdf", ".zip", ".exe", ".msi", ".7z", ".tar.gz", ".rar", ".lock", ".db", ".sqlite", ".sqlite3", ".pyc"}
EXCLUDE_FILES = {".env", "auth.json", "state.db", "state.db-journal", "state.db-wal", "state.db-shm"}

# 敏感文件只放脱敏模板
SENSITIVE_FILES = {
    ".env": "hermes-data/config/.env.template",
    "auth.json": "hermes-data/config/auth.json.template",
}

def should_exclude(path: Path) -> bool:
    """判断是否应该排除该文件"""
    name = path.name
    # 排除隐藏目录
    if any(part.startswith(".") for part in path.parts if part != ".gitignore"):
        pass  # .gitignore 应该保留
    # 排除目录
    for d in EXCLUDE_DIRS:
        if d in path.parts:
            return True
    # 排除扩展名
    if path.suffix.lower() in EXCLUDE_EXTS:
        return True
    # 排除文件名
    if name in EXCLUDE_FILES:
        return True
    # 排除大文件 (>5MB)
    if path.is_file():
        try:
            if path.stat().st_size > 5 * 1024 * 1024:
                return True
        except OSError:
            return True
    return False

def copy_tree(src: Path, dst: Path, exclude_sensitive: bool = True):
    """复制目录树，排除不需要的文件"""
    copied = 0
    skipped = 0
    if not src.exists():
        return copied, skipped
    
    dst.mkdir(parents=True, exist_ok=True)
    
    for item in src.rglob("*"):
        if not item.is_file():
            continue
        rel = item.relative_to(src)
        
        # 计算目标路径
        target = dst / rel
        
        # 排除检查
        if should_exclude(item):
            skipped += 1
            continue
        
        # 敏感文件检查
        if exclude_sensitive and item.name in EXCLUDE_FILES:
            skipped += 1
            continue
        
        # 复制文件（仅在文件较新或不存在时）
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            if not target.exists() or item.stat().st_mtime > target.stat().st_mtime:
                shutil.copy2(str(item), str(target))
                copied += 1
        except (OSError, PermissionError) as e:
            print(f"  跳过 {rel}: {e}")
            skipped += 1
    
    return copied, skipped

def sanitize_env(src: Path, dst: Path):
    """创建脱敏的 .env 模板"""
    if not src.exists():
        return
    lines = []
    with open(src, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            stripped = line.strip()
            if "=" in stripped and not stripped.startswith("#"):
                key = stripped.split("=", 1)[0]
                lines.append(f"{key}=***REDACTED***\n")
            else:
                lines.append(line)
    dst.parent.mkdir(parents=True, exist_ok=True)
    with open(dst, "w", encoding="utf-8") as f:
        f.writelines(lines)

def sanitize_auth_json(src: Path, dst: Path):
    """创建脱敏的 auth.json 模板"""
    if not src.exists():
        return
    try:
        with open(src, "r", encoding="utf-8") as f:
            data = json.load(f)
        # 递归替换所有值为 REDACTED
        def redact(obj):
            if isinstance(obj, dict):
                return {k: redact(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [redact(v) for v in obj]
            elif isinstance(obj, str):
                return "***REDACTED***"
            return obj
        redacted = redact(data)
        dst.parent.mkdir(parents=True, exist_ok=True)
        with open(dst, "w", encoding="utf-8") as f:
            json.dump(redacted, f, indent=2, ensure_ascii=False)
    except (json.JSONDecodeError, OSError):
        pass

def update_chat_log(changes: list):
    """更新聊天记录.md"""
    chat_file = REPO_DIR / "聊天记录.md"
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    entry = f"\n## {now} 塔奇克马自动同步\n\n"
    entry += "### 同步内容\n"
    for c in changes:
        entry += f"- {c}\n"
    entry += f"\n安全：所有敏感值已替换为 ***REDACTED***\n"
    
    if chat_file.exists():
        with open(chat_file, "r", encoding="utf-8") as f:
            content = f.read()
        with open(chat_file, "w", encoding="utf-8") as f:
            f.write(entry + content)
    else:
        with open(chat_file, "w", encoding="utf-8") as f:
            f.write(entry)

def git_commit_push():
    """Git add, commit, push"""
    os.chdir(REPO_DIR)
    
    # 确保在 main 分支
    subprocess.run(["git", "branch", "-M", "main"], capture_output=True)
    
    # 检查是否有变更
    result = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
    if not result.stdout.strip():
        print("没有变更需要提交")
        return False
    
    changed_files = result.stdout.strip().count("\n") + 1 if result.stdout.strip() else 0
    print(f"检测到 {changed_files} 个文件变更")
    
    # 添加所有变更
    subprocess.run(["git", "add", "-A"], capture_output=True)
    
    # 提交
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    msg = f"🐴 自动同步 {now}"
    subprocess.run(["git", "commit", "-m", msg], capture_output=True)
    
    # 推送
    PAT = ""
    cred_file = Path.home() / ".git-credentials"
    if cred_file.exists():
        import re
        content = cred_file.read_text()
        match = re.search(r"ghp_[a-zA-Z0-9]+", content)
        if match:
            PAT = match.group()
    
    if PAT:
        remote_url = f"https://Marfart:{PAT}@github.com/Marfart/hermes-shared.git"
        subprocess.run(["git", "remote", "set-url", "origin", remote_url], capture_output=True)
    
    result = subprocess.run(["git", "push", "origin", "main"], capture_output=True, text=True)
    if result.returncode != 0 and "Everything up-to-date" not in result.stderr:
        print(f"推送失败: {result.stderr}")
        return False
    
    print(f"✅ 同步完成，推送 {changed_files} 个文件")
    return True

def main():
    print("=" * 50)
    print("🐴 hermes-shared 自动同步开始")
    print("=" * 50)
    
    changes = []
    
    # 1. 同步 skills
    print("\n📁 同步 skills...")
    src = HERMES_DIR / "skills"
    dst = DATA_DIR / "skills"
    copied, skipped = copy_tree(src, dst)
    changes.append(f"skills: {copied} 个文件更新, {skipped} 个跳过")
    print(f"  复制 {copied} 个, 跳过 {skipped} 个")
    
    # 2. 同步 scripts
    print("\n📁 同步 scripts...")
    src = HERMES_DIR / "scripts"
    dst = DATA_DIR / "scripts"
    copied, skipped = copy_tree(src, dst)
    changes.append(f"scripts: {copied} 个文件更新, {skipped} 个跳过")
    print(f"  复制 {copied} 个, 跳过 {skipped} 个")
    
    # 3. 同步 memories
    print("\n📁 同步 memories...")
    src = HERMES_DIR / "memories"
    dst = DATA_DIR / "memories"
    copied, skipped = copy_tree(src, dst)
    changes.append(f"memories: {copied} 个文件更新, {skipped} 个跳过")
    print(f"  复制 {copied} 个, 跳过 {skipped} 个")
    
    # 4. 同步 config（脱敏）
    print("\n📁 同步 config（脱敏）...")
    dst_dir = DATA_DIR / "config"
    dst_dir.mkdir(parents=True, exist_ok=True)
    
    env_src = HERMES_DIR / ".env"
    env_dst = dst_dir / ".env.template"
    if env_src.exists():
        sanitize_env(env_src, env_dst)
        changes.append("config/.env.template: 脱敏模板已更新")
    
    auth_src = HERMES_DIR / "auth.json"
    auth_dst = dst_dir / "auth.json.template"
    if auth_src.exists():
        sanitize_auth_json(auth_src, auth_dst)
        changes.append("config/auth.json.template: 脱敏模板已更新")
    
    # config.yaml 不同步（含真实密钥）
    
    # 5. 同步 cron
    print("\n📁 同步 cron...")
    src = HERMES_DIR / "cron"
    dst = DATA_DIR / "cron"
    if src.exists():
        copied, skipped = copy_tree(src, dst)
        changes.append(f"cron: {copied} 个文件更新, {skipped} 个跳过")
        print(f"  复制 {copied} 个, 跳过 {skipped} 个")
    
    # 6. 更新聊天记录
    print("\n📝 更新聊天记录...")
    update_chat_log(changes)
    
    # 7. Git 提交推送
    print("\n🔄 Git 提交推送...")
    git_commit_push()
    
    print("\n" + "=" * 50)
    print("🐴 同步完成！")
    print("=" * 50)

if __name__ == "__main__":
    main()