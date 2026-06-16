#!/usr/bin/env python3
"""
Hermes 跨目录同步脚本 v1.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
用途：将 %LOCALAPPDATA%/hermes/ 的核心数据增量同步到
      Desktop/Working/Hermes/（Google Drive备份目录）

同步内容:
  ✓ config.yaml + .env + auth.json     （配置/凭证）
  ✓ skills/ 全量                        （技能知识库）
  ✓ scripts/ 全量                       （工具脚本）
  ✓ memories/ 全量                      （记忆/用户档案/脚本缓存）
  ✓ cron/ 任务定义                      （定时任务）
  ✓ weixin/ 账号信息                    （微信连接数据）
  ✗ logs/                              （日志量太大不同步）
  ✗ state.db + state.db-wal + state.db-shm（会话DB太大）
  ✗ cache/, image_cache/, audio_cache/ （缓存不必要）
  ✗ hermes-agent/ 源码                  （代码仓库单独管理）
  ✗ sessions/                          （会话记录量大）

运行模式: cron no_agent=True → 仅同步时有输出，否则静默
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import hashlib
import json
import os
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path

# ─── 路径 ───────────────────────────────────────────────
_local = os.environ.get("LOCALAPPDATA",
    os.path.join(os.environ["USERPROFILE"], "AppData", "Local"))
SRC = Path(os.environ.get("HERMES_HOME", os.path.join(_local, "hermes")))
DST = Path(os.environ["USERPROFILE"]) / "Desktop" / "Working" / "Hermes"

STATE_FILE = SRC / "memories" / "脚本缓存" / "hermes_sync_state.json"

# ─── 哪些目录/文件要同步 ──────────────────────────────
SYNC_DIRS = {
    "skills":       {"desc": "技能知识库", "skip_hidden": False},
    "scripts":      {"desc": "工具脚本", "skip_hidden": False},
    "cron":         {"desc": "定时任务定义", "skip_hidden": False},
    "weixin":       {"desc": "微信账号信息", "skip_hidden": False},
    "plugins":      {"desc": "插件", "skip_hidden": False},
}

# 这些目录的内容按文件同步到 DST/memories/ 下
SYNC_MEMORY_SUBDIRS = {
    "脚本缓存":     {"desc": "脚本缓存"},
    "product-knowledge": {"desc": "产品知识"},
    "buyer-development": {"desc": "客户开发数据"},
    "joinf-crm-edm":     {"desc": "富通CRM数据"},
}

# 顶层文件（key=文件名, value=描述）
SYNC_TOP_FILES = {
    "config.yaml":     "配置文件",
    ".env":            "环境变量(API密钥)",
    "auth.json":       "OAuth凭证",
    "MEMORY.md":       "记忆库",
    "USER.md":         "用户档案",
}

# 一级子目录下的特定文件
SYNC_CHILD_FILES = {
    "SOUL.md":         None,   # src根目录下
}

# 不需要同步的文件/目录模式
EXCLUDE_PATTERNS = {
    ".pyc", "__pycache__", ".git", ".DS_Store",
    "state.db", "state.db-wal", "state.db-shm",
    "node_modules", ".npm", ".cache",
    "venv", ".venv", ".gitattributes", ".gitignore",
}

# 超过此大小的文件跳过MD5直接同步（太大不缓存hash）
LARGE_FILE_BYTES = 5 * 1024 * 1024  # 5MB

def _should_exclude(name: str) -> bool:
    """检查文件名是否需要排除"""
    if name in EXCLUDE_PATTERNS:
        return True
    if name.endswith(".pyc"):
        return True
    if name.startswith(".") and name not in {".env", ".claude"}:
        return True
    return False

def _md5(path: Path) -> str:
    """快速文件MD5"""
    try:
        h = hashlib.md5()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return ""

def _safe_copy(src_path: Path, dst_path: Path) -> bool:
    """安全复制文件，确保目标目录存在"""
    try:
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_path, dst_path)
        return True
    except Exception as e:
        return False

# ─── 状态管理 ──────────────────────────────────────────

def _load_state() -> dict:
    defaults = {
        "last_sync": 0.0,
        "file_hashes": {},      # rel_path → md5
        "total_syncs": 0,
        "total_bytes": 0,
    }
    if STATE_FILE.exists():
        try:
            data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
            for k, v in defaults.items():
                data.setdefault(k, v)
            return data
        except Exception:
            pass
    return defaults

def _save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(
        json.dumps(state, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

# ─── 核心同步逻辑 ──────────────────────────────────────

def _sync_top_files(state: dict) -> tuple:
    """同步顶层配置文件"""
    copied = 0
    bytes_copied = 0
    
    for fname, desc in SYNC_TOP_FILES.items():
        src_path = SRC / fname
        dst_path = DST / fname
        if not src_path.exists():
            continue
        
        src_hash = _md5(src_path)
        cached = state["file_hashes"].get(fname)
        
        if src_hash == cached:
            continue
        
        if _safe_copy(src_path, dst_path):
            state["file_hashes"][fname] = src_hash
            copied += 1
            bytes_copied += src_path.stat().st_size
    
    return copied, bytes_copied

def _sync_dir(src_dir: Path, dst_dir: Path, state: dict, prefix: str = "") -> tuple:
    """递归同步一个目录"""
    copied = 0
    bytes_copied = 0
    
    if not src_dir.exists():
        return copied, bytes_copied
    
    dst_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        for entry in src_dir.iterdir():
            if _should_exclude(entry.name):
                continue
            
            rel_path = f"{prefix}/{entry.name}" if prefix else entry.name
            
            if entry.is_dir():
                sub_copied, sub_bytes = _sync_dir(entry, dst_dir / entry.name, state, rel_path)
                copied += sub_copied
                bytes_copied += sub_bytes
            elif entry.is_file():
                dst_path = dst_dir / entry.name
                src_hash = _md5(entry)
                cached = state["file_hashes"].get(rel_path)
                
                if src_hash == cached:
                    continue
                
                if _safe_copy(entry, dst_path):
                    state["file_hashes"][rel_path] = src_hash
                    copied += 1
                    bytes_copied += entry.stat().st_size
    except PermissionError:
        pass  # 某些系统目录不可读
    
    return copied, bytes_copied

def _clean_removed(src_dir: Path, dst_dir: Path) -> int:
    """删除目标中已经不存在的文件（清理残留）"""
    removed = 0
    if not dst_dir.exists():
        return removed
    
    for entry in dst_dir.iterdir():
        if _should_exclude(entry.name):
            continue
        src_path = src_dir / entry.name
        
        if not src_path.exists():
            try:
                if entry.is_dir():
                    shutil.rmtree(entry)
                else:
                    entry.unlink()
                removed += 1
            except Exception:
                pass
        elif entry.is_dir() and src_path.is_dir():
            removed += _clean_removed(src_path, entry)
    
    return removed

# ─── 主函数 ─────────────────────────────────────────────

def main():
    state = _load_state()
    total_copied = 0
    total_bytes = 0
    
    # 确保目标存在
    DST.mkdir(parents=True, exist_ok=True)
    
    # 1. 同步顶层配置文件
    c, b = _sync_top_files(state)
    total_copied += c
    total_bytes += b
    
    # 2. 同步一级子目录（skills, scripts, cron, weixin）
    for dirname, info in SYNC_DIRS.items():
        src_dir = SRC / dirname
        dst_dir = DST / dirname
        c, b = _sync_dir(src_dir, dst_dir, state, dirname)
        total_copied += c
        total_bytes += b
    
    # 3. 同步 memories 下的子目录
    for subdir, info in SYNC_MEMORY_SUBDIRS.items():
        src_dir = SRC / "memories" / subdir
        dst_dir = DST / "memories" / subdir
        c, b = _sync_dir(src_dir, dst_dir, state, f"memories/{subdir}")
        total_copied += c
        total_bytes += b
    
    # 4. 同步 memories 根目录的 MD 文件
    for fname in ["MEMORY.md", "USER.md"]:
        src_path = SRC / "memories" / fname
        dst_path = DST / "memories" / fname
        if src_path.exists():
            src_hash = _md5(src_path)
            cached = state["file_hashes"].get(f"memories/{fname}")
            if src_hash != cached:
                _safe_copy(src_path, dst_path)
                state["file_hashes"][f"memories/{fname}"] = src_hash
                total_copied += 1
                total_bytes += src_path.stat().st_size
    
    # 5. 清理目标中已删除的残留文件（skills/, scripts/ 目录）
    for dirname in SYNC_DIRS:
        _clean_removed(SRC / dirname, DST / dirname)
    
    # 6. 更新状态
    state["last_sync"] = time.time()
    state["total_syncs"] = state.get("total_syncs", 0) + (1 if total_copied > 0 else 0)
    state["total_bytes"] = state.get("total_bytes", 0) + total_bytes
    _save_state(state)
    
    # 7. 只在有变化时输出（cron no_agent 接收到变化才会通知）
    if total_copied > 0:
        print(f"[Hermes Sync] 📋 {datetime.now().strftime('%H:%M:%S')} "
              f"已同步 {total_copied} 个文件 ({total_bytes/1024:.1f} KB)")
        print(f"              {SRC} → {DST}")
    else:
        # 静默：无变化不输出
        pass

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # 同步脚本自身异常也静默，不污染 cron 输出
        sys.stderr.write(f"hermes_sync error: {e}\n")