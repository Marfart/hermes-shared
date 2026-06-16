#!/usr/bin/env python3
"""
旧文件清理工具 — 扫描用户目录下超过3年未使用的文件
安全策略：跳过系统目录 / 只读文件 / 受保护目录
用法：
  python file_cleanup_3y.py --dry-run     # 仅扫描预览（默认）
  python file_cleanup_3y.py --delete      # 扫描 + 删除到回收站
  python file_cleanup_3y.py --move <dir>  # 扫描 + 移动到指定目录
"""

import os
import sys
import time
import stat
import json
import logging

from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator, Optional
from enum import Enum, auto

# ── 日志配置 ──────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("cleanup")

# ── 常量（默认3年） ──────────────────────────────────────────
NOW = time.time()
DEFAULT_YEARS = 3
ONE_YEAR_SEC = 365 * 24 * 3600  # 基础单位
SCAN_YEARS = DEFAULT_YEARS
CUTOFF = NOW - SCAN_YEARS * ONE_YEAR_SEC
CUTOFF_STR = datetime.fromtimestamp(CUTOFF).strftime("%Y-%m-%d")

# 系统保护目录（永远不碰）
PROTECTED_DIRS = {
    "C:\\Windows",
    "C:\\Program Files",
    "C:\\Program Files (x86)",
    "C:\\ProgramData",
    "C:\\System32",
    "C:\\Users\\Admin\\AppData",
    "C:\\Users\\Admin\\ntuser*",
    "C:\\$Recycle.Bin",
    "C:\\Recovery",
    "C:\\System Volume Information",
}

# 用户目录下要跳过的子路径
SKIP_SUFFIXES = {
    "AppData",           # 应用数据
    "ntuser.dat",        # 用户配置
    "NTUSER.DAT",
    "ntuser.dat.LOG*",
    "NTUSER.DAT.LOG*",
    "_restore*",         # 系统还原
}

# 跳过system/hidden属性的文件
SKIP_ATTRIBUTES = stat.FILE_ATTRIBUTE_SYSTEM | stat.FILE_ATTRIBUTE_HIDDEN | stat.FILE_ATTRIBUTE_REPARSE_POINT

# ── 枚举 ──────────────────────────────────────────────────
class FileCategory(Enum):
    """文件分类"""
    DOCUMENT = auto()       # 文档 .doc .pdf .txt .xlsx
    IMAGE = auto()          # 图片 .jpg .png .gif
    VIDEO = auto()          # 视频 .mp4 .avi .mkv
    AUDIO = auto()          # 音频 .mp3 .wav .flac
    ARCHIVE = auto()        # 压缩包 .zip .rar .7z
    CODE = auto()           # 代码 .py .js .html .json
    EXECUTABLE = auto()     # 可执行 .exe .msi .bat
    TEMP = auto()           # 临时文件 .tmp .log .cache
    OTHER = auto()          # 其他


@dataclass(frozen=True)
class FileInfo:
    """扫描到的旧文件信息"""
    path: str
    size_bytes: int
    last_access: float
    last_modified: float
    created: float
    is_readonly: bool
    category: FileCategory
    accessible: bool = True


@dataclass
class ScanResult:
    """扫描结果集合"""
    total_scanned: int = 0
    old_files: list[FileInfo] = field(default_factory=list)
    skipped_dirs: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    scan_time_sec: float = 0.0

    @property
    def total_size(self) -> int:
        return sum(f.size_bytes for f in self.old_files)

    @property
    def count(self) -> int:
        return len(self.old_files)

    def summary(self) -> dict:
        return {
            "scanned_files": self.total_scanned,
            "old_files_found": self.count,
            "total_size_mb": round(self.total_size / 1024 / 1024, 2),
            "skipped_dirs": len(self.skipped_dirs),
            "errors": len(self.errors),
            "cutoff_date": CUTOFF_STR,
        }


# ── 辅助函数 ──────────────────────────────────────────────
def classify_file(path: Path) -> FileCategory:
    """根据扩展名分类文件"""
    ext = path.suffix.lower()
    doc_exts = {".doc", ".docx", ".pdf", ".txt", ".md", ".xls", ".xlsx", ".ppt", ".pptx", ".csv", ".rtf", ".odt"}
    img_exts = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg", ".ico", ".tiff"}
    vid_exts = {".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm", ".m4v"}
    aud_exts = {".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma", ".m4a"}
    arc_exts = {".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz"}
    code_exts = {".py", ".js", ".ts", ".html", ".css", ".json", ".xml", ".yaml", ".yml", ".sh", ".bat", ".ps1", ".sql"}
    exe_exts = {".exe", ".msi", ".bat", ".cmd", ".com", ".dll"}
    tmp_exts = {".tmp", ".temp", ".log", ".cache", ".bak", ".old", ".dmp"}

    if ext in doc_exts: return FileCategory.DOCUMENT
    if ext in img_exts: return FileCategory.IMAGE
    if ext in vid_exts: return FileCategory.VIDEO
    if ext in aud_exts: return FileCategory.AUDIO
    if ext in arc_exts: return FileCategory.ARCHIVE
    if ext in code_exts: return FileCategory.CODE
    if ext in exe_exts: return FileCategory.EXECUTABLE
    if ext in tmp_exts: return FileCategory.TEMP
    return FileCategory.OTHER


def is_system_path(path: Path) -> bool:
    """检查路径是否在受保护的系统目录下"""
    abs_path = str(path.resolve())
    for protected in PROTECTED_DIRS:
        if abs_path.startswith(protected):
            return True
    # 检查路径中是否有要跳过的子目录
    parts = path.resolve().parts
    for skip in SKIP_SUFFIXES:
        if skip in parts:
            return True
    # 检查是否是系统根目录下的文件
    if len(parts) <= 2 and parts[0] in ("C:\\", "C:"):
        return True
    return False


def has_protected_attribute(path: Path) -> bool:
    """检查文件是否有系统/隐藏属性"""
    try:
        attrs = os.stat(str(path)).st_file_attributes
        return bool(attrs & SKIP_ATTRIBUTES)
    except (AttributeError, OSError):
        return False


def format_size(bytes_: int) -> str:
    """人性化显示文件大小"""
    if bytes_ < 1024:
        return f"{bytes_} B"
    elif bytes_ < 1024 ** 2:
        return f"{bytes_ / 1024:.1f} KB"
    elif bytes_ < 1024 ** 3:
        return f"{bytes_ / 1024 ** 2:.1f} MB"
    else:
        return f"{bytes_ / 1024 ** 3:.2f} GB"


def format_time(ts: float) -> str:
    """时间戳转可读格式"""
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d")


# ── 核心扫描器 ────────────────────────────────────────────
def scan_old_files(root_dirs: list[str], dry_run: bool = True) -> ScanResult:
    """
    扫描指定目录下超过3年未访问的文件

    Args:
        root_dirs: 要扫描的根目录列表
        dry_run: 仅扫描不删除
    Returns:
        ScanResult 对象
    """
    result = ScanResult()
    start = time.time()

    for root in root_dirs:
        root_path = Path(root)
        if not root_path.exists():
            result.errors.append(f"目录不存在: {root}")
            continue
        if is_system_path(root_path):
            log.warning(f"⚠️ 跳过系统保护目录: {root}")
            result.skipped_dirs.append(root)
            continue

        log.info(f"🔍 扫描: {root}")

        for entry in root_path.rglob("*"):
            try:
                # 跳过目录本身，只处理文件
                if not entry.is_file():
                    continue

                # 安全检查：是否在系统路径下
                if is_system_path(entry):
                    continue

                # 安全检查：是否有系统/隐藏属性
                if has_protected_attribute(entry):
                    continue

                result.total_scanned += 1

                # 获取文件时间信息
                stat_info = entry.stat()
                last_access = stat_info.st_atime
                last_modified = stat_info.st_mtime
                created = stat_info.st_ctime

                # 判断是否超过3年未使用（取最近一次访问或修改）
                last_used = max(last_access, last_modified)
                if last_used < CUTOFF:
                    info = FileInfo(
                        path=str(entry),
                        size_bytes=stat_info.st_size,
                        last_access=last_access,
                        last_modified=last_modified,
                        created=created,
                        is_readonly=bool(stat_info.st_mode & stat.S_IREAD == 0),
                        category=classify_file(entry),
                    )
                    # 过滤掉0字节的临时文件（系统常驻锁文件）
                    if info.size_bytes > 0 or info.category not in (FileCategory.TEMP, FileCategory.OTHER):
                        result.old_files.append(info)

                # 每5000个文件报告一次进度
                if result.total_scanned % 5000 == 0:
                    elapsed = time.time() - start
                    log.info(f"⏳ 已扫描 {result.total_scanned} 个文件，耗时 {elapsed:.0f}s...")

            except PermissionError:
                # 权限不足的路径正常跳过
                try:
                    parent = str(entry.parent) if entry.parent else "?"
                except Exception:
                    parent = "?"
                result.errors.append(f"权限不足: {parent}/...")
            except OSError as e:
                # 其他IO错误
                result.errors.append(f"IO错误: {str(e)[:100]}")
            except Exception as e:
                # 兜底
                result.errors.append(f"未知错误({entry.name}): {str(e)[:100]}")

    result.scan_time_sec = time.time() - start
    return result


# ── 删除/移动操作 ─────────────────────────────────────────
def delete_to_recycle_bin(file_paths: list[str]) -> tuple[int, list[str]]:
    """
    将文件移到回收站（Windows原生）
    返回 (成功数, 失败路径列表)
    """
    import subprocess
    success = 0
    failed: list[str] = []

    for fp in file_paths:
        try:
            # 使用PowerShell将文件移到回收站
            cmd = [
                "powershell", "-Command",
                f"Add-Type -AssemblyName Microsoft.VisualBase; "
                f"[Microsoft.VisualBasic.FileIO.FileSystem]::DeleteFile('{fp}', "
                f"'OnlyErrorDialogs', 'SendToRecycleBin')"
            ]
            subprocess.run(cmd, capture_output=True, timeout=30, check=True)
            success += 1
            log.info(f"🗑️ 已删除: {fp}")
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            failed.append(fp)
            log.error(f"❌ 删除失败: {fp} — {str(e)[:80]}")

    return success, failed


def move_to_quarantine(file_paths: list[str], dest_dir: str) -> tuple[int, list[str]]:
    """
    将文件移到隔离目录
    """
    import shutil
    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)
    success = 0
    failed: list[str] = []

    for fp in file_paths:
        try:
            src = Path(fp)
            # 保持目录结构
            rel = src.relative_to(src.anchor)  # 取相对根路径
            target = dest / rel.parent / src.name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(target))
            success += 1
            log.info(f"📦 已移走: {fp} → {target}")
        except Exception as e:
            failed.append(fp)
            log.error(f"❌ 移动失败: {fp} — {str(e)[:80]}")

    return success, failed


# ── 报告输出 ──────────────────────────────────────────────
def print_report(result: ScanResult):
    """打印扫描报告"""
    summary = result.summary()
    
    print("\n" + "=" * 60)
    print(f"📋 旧文件扫描报告 ({CUTOFF_STR} 前未使用)")
    print("=" * 60)
    print(f"📊 总计扫描: {summary['scanned_files']:,} 个文件")
    print(f"🔴 找到旧文件: {summary['old_files_found']:,} 个")
    print(f"💾 总大小: {summary['total_size_mb']} MB")
    print(f"⏱️ 耗时: {result.scan_time_sec:.1f} 秒")

    if summary['skipped_dirs'] > 0:
        print(f"⏭️  跳过系统目录: {summary['skipped_dirs']} 个")

    if summary['errors'] > 0:
        print(f"⚠️  扫描错误: {summary['errors']} 个")

    if not result.old_files:
        print("\n✅ 没有找到超3年未使用的文件！电脑很整洁~")
        return

    # 按分类统计
    cat_counts: dict[FileCategory, int] = {}
    cat_sizes: dict[FileCategory, int] = {}
    for f in result.old_files:
        cat_counts[f.category] = cat_counts.get(f.category, 0) + 1
        cat_sizes[f.category] = cat_sizes.get(f.category, 0) + f.size_bytes

    print(f"\n📂 分类统计:")
    print(f"   {'类别':<12} {'数量':>8} {'大小':>12}")
    print(f"   {'-'*34}")
    for cat in FileCategory:
        if cat in cat_counts:
            print(f"   {cat.name:<12} {cat_counts[cat]:>8} {format_size(cat_sizes[cat]):>12}")

    # 按大小排序的前20个文件
    sorted_files = sorted(result.old_files, key=lambda f: f.size_bytes, reverse=True)[:20]
    print(f"\n🏆 前20个大文件:")
    print(f"   {'大小':<12} {'上次使用':<14} {'分类':<10} {'路径'}")
    print(f"   {'-'*80}")
    for f in sorted_files:
        last_used = format_time(max(f.last_access, f.last_modified))
        print(f"   {format_size(f.size_bytes):<12} {last_used:<14} {f.category.name:<10} {f.path}")


# ── 主入口 ────────────────────────────────────────────────
def main():
    import argparse
    parser = argparse.ArgumentParser(description="清理超过 N 年未使用的旧文件")
    parser.add_argument("--years", type=int, default=3,
                        help="清理N年未使用的文件（默认: 3）")
    parser.add_argument("--dry-run", action="store_true", default=True,
                        help="仅扫描预览（默认）")
    parser.add_argument("--delete", action="store_true",
                        help="扫描并删除到回收站")
    parser.add_argument("--move", type=str, default=None,
                        help="扫描并移动到指定目录（不清除）")
    parser.add_argument("--json", action="store_true",
                        help="输出JSON格式报告")
    parser.add_argument("--min-size", type=str, default=None,
                        help="最小文件大小过滤，如 '1MB', '100KB'")
    parser.add_argument("--category", type=str, default=None,
                        help="只处理指定分类文件，如 'TEMP', 'ARCHIVE'")

    # 如果没传参数，默认 dry-run
    args = parser.parse_args()
    if not args.delete and not args.move:
        args.dry_run = True

    # 应用 --years 参数
    global SCAN_YEARS, CUTOFF, CUTOFF_STR
    SCAN_YEARS = args.years
    CUTOFF = NOW - SCAN_YEARS * ONE_YEAR_SEC
    CUTOFF_STR = datetime.fromtimestamp(CUTOFF).strftime("%Y-%m-%d")

    # 待扫描的目录（用户目录下，跳过系统目录）
    scan_dirs = [
        r"C:\Users\Admin\Desktop",
        r"C:\Users\Admin\Documents",
        r"C:\Users\Admin\Downloads",
        r"C:\Users\Admin\Pictures",
        r"C:\Users\Admin\Videos",
        r"C:\Users\Admin\Music",
        r"C:\Users\Admin\OneDrive" if Path(r"C:\Users\Admin\OneDrive").exists() else None,
    ]
    scan_dirs = [d for d in scan_dirs if d is not None]

    log.info(f"🚀 开始扫描... ({SCAN_YEARS}年未使用截止日: {CUTOFF_STR})")
    log.info(f"📂 扫描目录: {', '.join(scan_dirs)}")

    result = scan_old_files(scan_dirs, dry_run=args.dry_run)

    if args.json:
        print(json.dumps(result.summary(), ensure_ascii=False, indent=2))
    else:
        print_report(result)

    # 没有旧文件就结束
    if not result.old_files:
        return

    # 根据类别过滤
    files_to_process = result.old_files
    if args.category:
        try:
            target_cat = FileCategory[args.category.upper()]
            files_to_process = [f for f in files_to_process if f.category == target_cat]
            log.info(f"🎯 过滤分类 '{args.category}': {len(files_to_process)} 个文件")
        except KeyError:
            log.error(f"❌ 无效分类: {args.category}")
            sys.exit(1)

    # 最小大小过滤
    if args.min_size:
        units = {"B": 1, "KB": 1024, "MB": 1024**2, "GB": 1024**3}
        import re
        m = re.match(r"^(\d+(?:\.\d+)?)\s*(B|KB|MB|GB)$", args.min_size.upper())
        if m:
            min_bytes = float(m.group(1)) * units[m.group(2)]
            files_to_process = [f for f in files_to_process if f.size_bytes >= min_bytes]
            log.info(f"🎯 过滤最小大小 '{args.min_size}': {len(files_to_process)} 个文件")
        else:
            log.error(f"❌ 无效大小格式: {args.min_size} (示例: '1MB', '500KB')")
            sys.exit(1)

    # 执行操作
    file_paths = [f.path for f in files_to_process]

    if args.delete:
        log.warning(f"⚠️  开始删除 {len(file_paths)} 个文件到回收站...")
        success, failed = delete_to_recycle_bin(file_paths)
        print(f"\n✅ 删除完成: {success} 成功, {len(failed)} 失败")
        if failed:
            print(f"❌ 失败文件列表已记录到日志")

    elif args.move:
        dest = args.move
        log.warning(f"📦 移动 {len(file_paths)} 个文件到 {dest} ...")
        success, failed = move_to_quarantine(file_paths, dest)
        print(f"\n✅ 移动完成: {success} 成功, {len(failed)} 失败")
        if failed:
            print(f"❌ 失败文件列表已记录到日志")


if __name__ == "__main__":
    main()