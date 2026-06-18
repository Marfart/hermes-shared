# GitHub 共享仓库同步陷阱速查

两个独立防线可以阻止 CRM 数据库和客户数据上传到共享仓库。改一个不够，必须两个都改。

## 防线1：`.gitignore`

```
# 原始内容
*.db            # ← 阻止 crm_followups.db
*.sqlite
```

**修复**：在 `.gitignore` 末尾加 `!*.db` 和 `!*.sqlite`
```
*.db
*.sqlite
# CRM 数据库需要同步
!*.db
!*.sqlite
```

注意顺序！`*.db` 在前，`!*.db` 在后才生效。

## 防线2：`github_shared_sync.py` 的 `EXCLUDE_EXT`

```python
EXCLUDE_EXT = {".db", ".sqlite", ".sqlite3", ...}  # ← 阻止数据库
```

**修复**：从集合中移除 `.db`：

```python
EXCLUDE_EXT = {".sqlite", ".sqlite3", ...}  # .db 已移除
```

## 大文件强制追踪

`all_customers_raw.json`（6.4MB）不会被 `git add` 自动追踪（可能大小限制）。需要：

```bash
git add -f hermes-data/memories/脚本缓存/富通CRM/all_customers_raw.json
```

## 同步后验证清单

```bash
cd hermes-shared
git status --short                    # 检查是否所有变更已 staging
git diff --cached --stat             # 检查文件数量和大小
```

检查缺失文件：
- `.db` 文件是否出现在 `git ls-files` 中？
- 本地 CRM 脚本的 MD5 是否等于共享仓库版本？
- `find` 对比本地和 shared 的 `.py/.mjs/.cjs` 文件计数