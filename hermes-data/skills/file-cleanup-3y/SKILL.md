---
name: file-cleanup-3y
description: "扫描并清理超过3年未使用的文件 — 支持预览/回收站删除/移走三种模式，自动跳过系统目录"
version: 1.0.0
author: Tachikoma
platforms: [windows]
trigger: "清电脑|清理旧文件|3年未用|旧文件清理|磁盘清理"
---

# 旧文件清理工具

扫描用户目录下 **超过 N 年未使用** 的文件（默认3年），支持预览/删除到回收站/移走三种模式。

## 脚本位置

`memories/脚本缓存/系统维护/file_cleanup_3y.py`

## 用法

```bash
# 1. 只扫描预览（安全模式，默认3年）
python file_cleanup_3y.py --dry-run

# 2. 只看1年没用的
python file_cleanup_3y.py --years 1

# 3. 扫描 + 删除到回收站
python file_cleanup_3y.py --delete

# 4. 扫描 + 移动到隔离目录
python file_cleanup_3y.py --move D:\旧文件备份

# 5. 只看临时文件
python file_cleanup_3y.py --dry-run --category TEMP

# 6. 只看大于1MB的文件
python file_cleanup_3y.py --dry-run --min-size 1MB
```

## 安全机制

- ❌ 跳过 `C:\Windows`, `C:\Program Files`, `AppData` 等系统目录
- ❌ 跳过 System/Hidden 属性的文件（系统关键文件）
- ❌ 跳过 ntuser.dat 等用户配置
- ✅ 删除走回收站（`SendToRecycleBin`），不是永久删除
- ✅ 仅操作 `last_access` 和 `last_modified` 均超过3年的文件

## 参数

| 参数 | 说明 |
|------|------|
| `--years N` | 清理N年未使用的文件（默认: 3） |
| `--dry-run` | 仅扫描预览（默认） |
| `--delete` | 扫描并删除到回收站 |
| `--move <目录>` | 扫描并移动到指定目录 |
| `--json` | 输出JSON格式报告 |
| `--min-size` | 最小文件大小过滤（如 `1MB`, `500KB`） |
| `--category` | 只处理指定分类（DOCUMENT/IMAGE/VIDEO/AUDIO/ARCHIVE/CODE/EXECUTABLE/TEMP/OTHER） |