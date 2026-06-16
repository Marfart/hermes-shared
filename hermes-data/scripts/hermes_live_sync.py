#!/usr/bin/env python3
"""
Hermes 实时同步守护进程 v1.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
用 watchdog 实时监听 %LOCALAPPDATA%/hermes/ 的核心目录，
文件一有变化就立刻同步到 Desktop/Working/Hermes/
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import hashlib
import json
import os
import shutil
import sys
import time
from pathlib import Path
from threading import Lock

# watchdog
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

# ─── 路径 ───────────────────────────────────────────────
_local = os.environ.get("LOCALAPPDATA",
    os.path.join(os.environ["USERPROFILE"], "AppData", "Local"))
SRC = Path(os.environ.get("HERMES_HOME", os.path.join(_local, "hermes")))
DST = Path(os.environ["USERPROFILE"]) / "Desktop" / "Working" / "Hermes"

STATE_FILE = SRC / "memories" / "脚本缓存" / "hermes_live_sync_state.json"
PID_FILE = SRC / ".hermes_live_sync.pid"

# 要监听的顶层文件
WATCH_TOP_FILES = {
    "config.yaml", ".env", "auth.json", "SOUL.md",
    "gateway_state.json", "channel_directory.json",
}

# 要监听的子目录（相对于 SRC）
WATCH_SUBDIRS = {
    "skills",
    "scripts",
    "memories/脚本缓存",
    "memories/product-knowledge",
    "memories/buyer-development",
    "memories/joinf-crm-edm",
    "cron",
    "weixin",
    "plugins",
}

# 不监听的模式
EXCLUDE_DIRS = {
    "__pycache__", ".git", ".svn", "node_modules",
    ".npm", ".cache", "venv", ".venv",
    "logs", "sessions", "audio_cache", "image_cache",
    "chrome-profiles", "sandboxes", "pastes",
    "lsp", "hooks", "gateway-service", "git",
    "state-snapshots", "pairing",
}
EXCLUDE_EXT = {".pyc", ".log", ".tmp", ".bak"}
EXCLUDE_FILES = {
    "state.db", "state.db-wal", "state.db-shm",
    "kanban.db", "kanban.db.init.lock",
    ".hermes_history",
}

# 去抖时间（秒）
DEBOUNCE_SEC = 0.5

# ─── 锁定 ───────────────────────────────────────────────
_sync_lock = Lock()
_recent_syncs: dict = {}  # path → timestamp

def _should_exclude(path_str: str) -> bool:
    p = path_str.replace("\\", "/")
    parts = p.split("/")

    for part in parts:
        if part in EXCLUDE_DIRS:
            return True

    fname = parts[-1] if parts else ""
    if fname in EXCLUDE_FILES:
        return True
    if fname.startswith(".") and fname not in WATCH_TOP_FILES:
        return True
    ext = os.path.splitext(fname)[1].lower()
    if ext in EXCLUDE_EXT:
        return True
    return False

def _is_src_watched(src_path: str) -> bool:
    """判断 src_path 是否在我们的监控范围内"""
    src_str = str(SRC).replace("\\", "/")
    path = src_path.replace("\\", "/")

    if not path.startswith(src_str):
        return False

    rel = path[len(src_str):].strip("/")
    if not rel:
        return False  # 忽略根目录本身

    # 顶层文件
    if "/" not in rel and rel in WATCH_TOP_FILES:
        return True

    # 子目录
    for sub in WATCH_SUBDIRS:
        if rel.startswith(sub):
            return True

    return False

def _compute_md5(path: str) -> str:
    try:
        h = hashlib.md5()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return ""

def _sync_file(src_path: str) -> bool:
    """同步单个文件，返回是否真正复制了"""
    with _sync_lock:
        now = time.time()
        last = _recent_syncs.get(src_path, 0)
        if now - last < DEBOUNCE_SEC:
            return False
        _recent_syncs[src_path] = now

    if _should_exclude(src_path):
        return False
    if not _is_src_watched(src_path):
        return False

    src = Path(src_path)
    if not src.exists() or not src.is_file():
        return False

    # 检查 md5 避免重复同步
    try:
        # 构造目标路径
        rel = src.relative_to(SRC)
        dst = DST / rel
    except ValueError:
        return False

    src_hash = _compute_md5(src_path)
    if dst.exists():
        dst_hash = _compute_md5(str(dst))
        if src_hash == dst_hash:
            return False  # 内容没变

    try:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_path, str(dst))
        return True
    except Exception as e:
        print(f"[live-sync] ⚠ 写入失败 {rel}: {e}", file=sys.stderr)
        return False

def _delete_sync(src_path: str) -> bool:
    """文件被删了，同步删除目标"""
    with _sync_lock:
        now = time.time()
        last = _recent_syncs.get(f"del:{src_path}", 0)
        if now - last < DEBOUNCE_SEC:
            return False
        _recent_syncs[f"del:{src_path}"] = now

    if _should_exclude(src_path):
        return False
    if not _is_src_watched(src_path):
        return False

    try:
        src = Path(src_path)
        rel = src.relative_to(SRC)
        dst = DST / rel
        if dst.exists():
            if dst.is_dir():
                shutil.rmtree(str(dst))
            else:
                dst.unlink()
            return True
    except Exception:
        pass
    return False

# ─── 事件处理器 ─────────────────────────────────────────

class HermesSyncHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return
        if _sync_file(event.src_path):
            rel = Path(event.src_path).relative_to(SRC)
            print(f"[live-sync] + {rel}")

    def on_modified(self, event):
        if event.is_directory:
            return
        if _sync_file(event.src_path):
            rel = Path(event.src_path).relative_to(SRC)
            print(f"[live-sync] ~ {rel}")

    def on_deleted(self, event):
        if event.is_directory:
            return
        if _delete_sync(event.src_path):
            rel = Path(event.src_path).relative_to(SRC)
            print(f"[live-sync] - {rel}")

    def on_moved(self, event):
        if event.is_directory:
            return
        # 先删旧的
        if _delete_sync(event.src_path):
            rel = Path(event.src_path).relative_to(SRC)
            print(f"[live-sync] - {rel} (moved)")
        # 再同步新的
        if _sync_file(event.dest_path):
            rel = Path(event.dest_path).relative_to(SRC)
            print(f"[live-sync] + {rel} (moved)")


def _load_persisted_syncs() -> set:
    """看看哪些文件已经同步过了（避免启动时全量遍历）"""
    synced = set()
    if STATE_FILE.exists():
        try:
            data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
            synced = set(data.get("synced_files", []))
        except Exception:
            pass
    return synced

def _save_persisted_syncs(synced: set) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        STATE_FILE.write_text(
            json.dumps({"synced_files": list(synced)[-2000:]}, ensure_ascii=False),
            encoding="utf-8",
        )
    except Exception:
        pass

def run_initial_sync() -> int:
    """启动时做一次全量同步（后续靠监听）"""
    count = 0
    synced = _load_persisted_syncs()

    # 顶层文件
    for fname in WATCH_TOP_FILES:
        src = SRC / fname
        if src.exists():
            if _sync_file(str(src)):
                count += 1
                synced.add(str(src))

    # 子目录
    for subdir in WATCH_SUBDIRS:
        src_dir = SRC / subdir
        if not src_dir.exists():
            continue
        for root, dirs, files in os.walk(str(src_dir)):
            for dname in list(dirs):
                if dname in EXCLUDE_DIRS:
                    dirs.remove(dname)
            for fname in files:
                fpath = os.path.join(root, fname)
                if _should_exclude(fpath):
                    continue
                if not _is_src_watched(fpath):
                    continue
                if fpath in synced:
                    continue
                if _sync_file(fpath):
                    count += 1
                    synced.add(fpath)

    _save_persisted_syncs(synced)
    return count


def is_running() -> bool:
    """检查是否已经在运行"""
    if PID_FILE.exists():
        try:
            pid = int(PID_FILE.read_text().strip())
            if os.name == "nt":
                import ctypes
                # Windows: 检查进程是否存在
                PROCESS_QUERY_INFORMATION = 0x0400
                handle = ctypes.windll.kernel32.OpenProcess(PROCESS_QUERY_INFORMATION, False, pid)
                if handle:
                    ctypes.windll.kernel32.CloseHandle(handle)
                    return True
                return False
            else:
                # Linux/Mac
                os.kill(pid, 0)
                return True
        except (OSError, ValueError, ImportError):
            pass
    return False


def main():
    if is_running():
        print("[live-sync] ⚠ 已在运行中（PID文件存在）", file=sys.stderr)
        return

    # 写 PID
    PID_FILE.write_text(str(os.getpid()))
    
    # 初始全量同步
    print("[live-sync] 🔄 初始全量同步...", end=" ", flush=True)
    count = run_initial_sync()
    print(f"{count} 个文件已同步")
    print(f"[live-sync] 👀 开始实时监听 {SRC}")
    print(f"[live-sync]    → 目标: {DST}")

    # 启动 observers
    observers = []
    handler = HermesSyncHandler()

    # 监听顶层目录（包含了所有子目录）
    observer = Observer()
    observer.schedule(handler, str(SRC), recursive=True)
    observer.daemon = True
    observer.start()
    observers.append(observer)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        for obs in observers:
            obs.stop()
        for obs in observers:
            obs.join()
        PID_FILE.unlink(missing_ok=True)
        print("[live-sync] 👋 已停止")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[live-sync] 💥 异常退出: {e}", file=sys.stderr)
        PID_FILE.unlink(missing_ok=True)
        sys.exit(1)