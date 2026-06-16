#!/usr/bin/env python
"""
GitHub Shared Repo Auto-Sync
监听 hermes 关键目录变化 → 自动同步到 Marfart/hermes-shared 仓库
"""

import hashlib
import json
import logging
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

# ── 配置 ──────────────────────────────────────────────
HERMES_HOME = Path(os.environ.get("HERMES_HOME", Path.home() / "AppData" / "Local" / "hermes"))
SHARED_REPO = Path.home() / "hermes-shared"
SYNC_INTERVAL = 60  # 秒，检查间隔

# 源 → 目标映射
SYNC_MAP = {
    "skills": HERMES_HOME / "skills",
    "scripts": HERMES_HOME / "scripts",
    "memories": HERMES_HOME / "memories",
    "cron": HERMES_HOME / "cron",
}

# 排除规则
EXCLUDE_DIRS = {".hub", "__pycache__", "node_modules", ".git", "cache", "logs",
                   "buyer-development", "joinf-crm-edm", "product-knowledge",
                   "buyer-development-watcher"}
EXCLUDE_EXT = {".pdf", ".zip", ".exe", ".msi", ".7z", ".tar.gz", ".rar",
               ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico",
               ".db", ".sqlite", ".sqlite3", ".pyc", ".lock",
               ".mp3", ".mp4", ".wav", ".ogg", ".webm"}
EXCLUDE_FILES = {".env", "auth.json", "state.db", "gateway_state.json"}

# 日志
LOG_FILE = HERMES_HOME / "scripts" / "github_shared_sync.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(str(LOG_FILE), encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("github-sync")


def run_git(*args, cwd: Path = SHARED_REPO, timeout: int = 30) -> tuple[int, str]:
    """执行 git 命令"""
    try:
        r = subprocess.run(
            ["git"] + list(args),
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace",
        )
        return r.returncode, (r.stdout + r.stderr).strip()
    except subprocess.TimeoutExpired:
        return -1, "TIMEOUT"
    except Exception as e:
        return -2, str(e)


def should_skip(path: Path) -> bool:
    """判断文件是否应跳过"""
    name = path.name
    if name in EXCLUDE_FILES:
        return True
    if path.suffix.lower() in EXCLUDE_EXT:
        return True
    for part in path.parts:
        if part in EXCLUDE_DIRS:
            return True
    return False


def sync_directory(src: Path, dst: Path) -> tuple[int, int, int]:
    """同步目录，返回 (copied, skipped, deleted)"""
    copied = skipped = deleted_count = 0

    if not src.exists():
        return 0, 0, 0

    # 复制新/修改的文件
    for item in src.rglob("*"):
        if not item.is_file():
            continue
        if should_skip(item):
            skipped += 1
            continue

        rel = item.relative_to(src)
        target = dst / rel

        # 只在源比目标新时复制
        if target.exists():
            src_mtime = item.stat().st_mtime
            dst_mtime = target.stat().st_mtime
            if src_mtime <= dst_mtime:
                continue

        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copy2(str(item), str(target))
            copied += 1
        except (OSError, PermissionError) as e:
            log.warning(f"复制失败: {item} → {e}")
            skipped += 1

    # 删除目标中源已不存在的文件（反向扫描）
    if dst.exists():
        for item in dst.rglob("*"):
            if not item.is_file():
                continue
            rel = item.relative_to(dst)
            source = src / rel
            if not source.exists():
                try:
                    item.unlink()
                    deleted_count += 1
                except (OSError, PermissionError):
                    pass

    return copied, skipped, deleted_count


def sync_config_files() -> int:
    """同步脱敏后的配置模板"""
    config_dst = SHARED_REPO / "hermes-data" / "config"
    config_dst.mkdir(parents=True, exist_ok=True)
    copied = 0

    # .env 脱敏
    env_src = HERMES_HOME / ".env"
    env_dst = config_dst / ".env.template"
    if env_src.exists():
        try:
            with open(env_src, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
            sanitized = []
            for line in lines:
                stripped = line.strip()
                if stripped and not stripped.startswith("#") and "=" in stripped:
                    key = line.split("=", 1)[0]
                    sanitized.append(f"{key}=***REDACTED***\n")
                else:
                    sanitized.append(line)
            with open(env_dst, "w", encoding="utf-8") as f:
                f.writelines(sanitized)
            copied += 1
        except Exception as e:
            log.warning(f".env脱敏失败: {e}")

    # auth.json 脱敏
    auth_src = HERMES_HOME / "auth.json"
    auth_dst = config_dst / "auth.json.template"
    if auth_src.exists():
        try:
            with open(auth_src, "r", encoding="utf-8") as f:
                data = json.load(f)
            redacted = json.dumps(_redact_dict(data), indent=2, ensure_ascii=False)
            with open(auth_dst, "w", encoding="utf-8") as f:
                f.write(redacted)
            copied += 1
        except Exception as e:
            log.warning(f"auth.json脱敏失败: {e}")

    return copied


def _redact_dict(d: dict) -> dict:
    """递归脱敏字典值"""
    out = {}
    for k, v in d.items():
        if isinstance(v, dict):
            out[k] = _redact_dict(v)
        elif isinstance(v, str) and len(v) > 8:
            out[k] = "***REDACTED***"
        else:
            out[k] = v
    return out


def git_commit_and_push() -> bool:
    """检查变更 → commit → push"""
    # git add
    code, out = run_git("add", "-A")
    if code != 0:
        log.error(f"git add 失败: {out}")
        return False

    # 检查是否有变更
    code, out = run_git("status", "--porcelain")
    if not out.strip():
        log.debug("无变更需要提交")
        return True

    changed = len(out.strip().split("\n"))
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    msg = f"🔄 自动同步 hermes-data ({changed} files) [{timestamp}]"

    # commit
    code, out = run_git("commit", "-m", msg)
    if code != 0 and "nothing to commit" not in out:
        log.error(f"git commit 失败: {out}")
        return False

    # push
    code, out = run_git("push", "origin", "main", timeout=60)
    if code != 0:
        log.error(f"git push 失败: {out}")
        return False

    log.info(f"✅ 推送成功: {changed} 个文件变更")
    return True


def full_sync() -> bool:
    """执行完整同步"""
    total_copied = 0
    total_skipped = 0

    for name, src in SYNC_MAP.items():
        dst = SHARED_REPO / "hermes-data" / name
        if not src.exists():
            continue
        copied, skipped, deleted = sync_directory(src, dst)
        total_copied += copied
        total_skipped += skipped
        if copied or deleted:
            log.info(f"  {name}: +{copied} 复制, -{deleted} 删除, {skipped} 跳过")

    # 配置文件脱敏
    cfg_copied = sync_config_files()
    total_copied += cfg_copied

    if total_copied > 0:
        log.info(f"同步总计: {total_copied} 文件复制, {total_skipped} 跳过")
        return git_commit_and_push()
    else:
        log.debug("无文件变更")
        return True


def main():
    """主循环"""
    if not SHARED_REPO.exists():
        log.error(f"仓库不存在: {SHARED_REPO}")
        sys.exit(1)

    # 确保在 main 分支
    run_git("checkout", "main")

    log.info("🐴 GitHub共享仓库自动同步启动")
    log.info(f"  仓库: {SHARED_REPO}")
    log.info(f"  检查间隔: {SYNC_INTERVAL}s")

    while True:
        try:
            full_sync()
        except Exception as e:
            log.error(f"同步异常: {e}")

        time.sleep(SYNC_INTERVAL)


if __name__ == "__main__":
    if "--once" in sys.argv:
        full_sync()
    else:
        main()