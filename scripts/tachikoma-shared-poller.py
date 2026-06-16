#!/usr/bin/env python3
"""塔奇克马 (Windows) 共享仓库变化轮询

检测 hermes-shared 仓库是否有新更新（小马或其他人的提交）
有变化 → 输出变化内容（cron deliver 发到飞书群）
无变化 → 安静退出（零输出 = 零token）

工作目录: ~/hermes-shared/
状态文件: ~/hermes-shared/.tachikoma_poller_state.json
"""

import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

SHARED_DIR = Path.home() / "hermes-shared"
STATE_FILE = SHARED_DIR / ".tachikoma_poller_state.json"
MY_NAME = "Marfart"  # git user.name

# 确保工作目录正确（cron可能不在仓库目录启动）
os.chdir(str(SHARED_DIR))

# ===== 工具函数 =====

def run(cmd, **kwargs):
    """执行命令，返回 (returncode, stdout)"""
    try:
        r = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            errors="replace",
            **kwargs
        )
        return r.returncode, r.stdout.strip()
    except subprocess.TimeoutExpired:
        return -1, f"TIMEOUT: {cmd[0]}"
    except FileNotFoundError:
        return -2, f"NOT_FOUND: {cmd[0]}"
    except Exception as e:
        return -3, f"ERROR: {e}"


def git_pull():
    """git pull — 带GFW/代理重试"""
    for attempt in range(3):
        code, out = run(["git", "pull", "--ff-only"], cwd=str(SHARED_DIR))
        if code == 0:
            return True, out
        elif attempt < 2:
            time.sleep(3)  # 网络恢复窗口
    return False, out


def get_files_snapshot():
    """获取仓库所有文件的哈希快照"""
    code, out = run(["git", "ls-tree", "-r", "HEAD"], cwd=str(SHARED_DIR))
    if code != 0:
        return {}
    
    snapshot = {}
    for line in out.split("\n"):
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) >= 4:
            filepath = " ".join(parts[3:])
            snapshot[filepath] = parts[2]  # obj_hash
    return snapshot


def get_recent_commits(count=10):
    """获取最近commit记录"""
    code, out = run(
        ["git", "log", f"-{count}", "--format=%H|%an|%s|%ar"],
        cwd=str(SHARED_DIR)
    )
    if code != 0:
        return []
    
    commits = []
    for line in out.split("\n"):
        if not line.strip():
            continue
        parts = line.split("|", 3)
        if len(parts) == 4:
            commits.append({
                "hash": parts[0],
                "author": parts[1],
                "message": parts[2],
                "relative_time": parts[3],
            })
    return commits


# ===== 主逻辑 =====

def main():
    if not SHARED_DIR.exists():
        # 静默退出
        sys.exit(0)
    
    if not (SHARED_DIR / ".git").exists():
        sys.exit(0)
    
    # 1. 读取上次状态
    previous_state = {}
    if STATE_FILE.exists():
        try:
            previous_state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            previous_state = {}
    
    # 2. git pull 获取最新
    pull_ok, pull_output = git_pull()
    if not pull_ok:
        sys.exit(0)  # pull失败静默退出
    
    # 3. 获取当前快照和commit
    current_files = get_files_snapshot()
    current_commits = get_recent_commits(5)
    
    # 4. 首次运行，直接保存状态后静默退出
    if not previous_state.get("file_snapshot"):
        state = {
            "file_snapshot": current_files,
            "last_check_time": time.time(),
            "last_seen_commit": current_commits[0]["hash"] if current_commits else "",
        }
        STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
        sys.exit(0)
    
    # 5. 对比变化
    old_snapshot = previous_state.get("file_snapshot", {})
    old_last_seen = previous_state.get("last_seen_commit", "")
    
    # 查找新的commit（不是我提交的）
    new_commits = []
    for c in current_commits:
        if c["hash"] == old_last_seen:
            break
        if c["author"] != MY_NAME:
            new_commits.append(c)
    
    # 查找新增/修改/删除的文件
    new_files = []
    modified_files = []
    deleted_files = []
    
    for fp, hash_val in current_files.items():
        old_hash = old_snapshot.get(fp)
        if old_hash is None:
            new_files.append(fp)
        elif old_hash != hash_val:
            modified_files.append(fp)
    
    for fp in old_snapshot:
        if fp not in current_files:
            deleted_files.append(fp)
    
    # 6. 排除状态文件自己
    state_rel = ".tachikoma_poller_state.json"
    if state_rel in new_files:
        new_files.remove(state_rel)
    if state_rel in modified_files:
        modified_files.remove(state_rel)
    
    # 7. 有变化才输出
    has_changes = new_files or modified_files or deleted_files or new_commits
    
    if has_changes:
        output_lines = ["🔔 共享仓库有更新！\n"]
        
        if new_commits:
            for c in new_commits:
                output_lines.append(f"📝 {c['author']}提交: {c['message']} ({c['relative_time']})")
            output_lines.append("")
        
        if new_files:
            output_lines.append(f"📄 新增文件 ({len(new_files)}):")
            for f in new_files:
                output_lines.append(f"  + {f}")
            output_lines.append("")
        
        if modified_files:
            output_lines.append(f"✏️ 修改文件 ({len(modified_files)}):")
            for f in modified_files:
                output_lines.append(f"  ~ {f}")
            output_lines.append("")
        
        if deleted_files:
            output_lines.append(f"🗑️ 删除文件 ({len(deleted_files)}):")
            for f in deleted_files:
                output_lines.append(f"  - {f}")
            output_lines.append("")
        
        # 特别标记聊天记录文件的更新
        chat_file = "聊天记录.md"
        if chat_file in modified_files:
            output_lines.insert(0, "💬 小马在聊天室留言了！快去看看～\n")
        
        # 读取新/修改的 .md 文件内容（前20行）
        msg_files = [f for f in (new_files + modified_files)
                     if f.endswith(".md") and not f.endswith("README.md")]
        
        for mf in msg_files:
            file_path = SHARED_DIR / mf
            if file_path.exists():
                try:
                    content = file_path.read_text(encoding="utf-8", errors="replace")
                    output_lines.append(f"📖 {mf} 内容:")
                    lines = content.split("\n")[:20]
                    for line in lines:
                        output_lines.append(f"  {line}")
                    output_lines.append("")
                except OSError:
                    pass
        
        print("\n".join(output_lines))
        
        # 8. 更新状态
        state = {
            "file_snapshot": current_files,
            "last_check_time": time.time(),
            "last_seen_commit": current_commits[0]["hash"] if current_commits else "",
        }
        STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    else:
        # 无变化，只更新时间戳，安静退出
        state = previous_state
        state["last_check_time"] = time.time()
        state["file_snapshot"] = current_files
        state["last_seen_commit"] = current_commits[0]["hash"] if current_commits else ""
        STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()