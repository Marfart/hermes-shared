# Windows IELTS Notion ↔ Anki 同步

- 入口脚本：`%LOCALAPPDATA%\hermes\scripts\anki_notion_sync.py`
- Hermes 触发语：**同步 Anki**（按需执行，不创建定时任务）
- 执行命令：`python "C:/Users/Admin/AppData/Local/hermes/scripts/anki_notion_sync.py"`
- 初次安全试运行：同一命令加 `--first-safe-test`，只处理首条无冲突 PENDING 记录；验证通过后再运行默认命令处理其余安全记录。
- Python 仅使用标准库，无需安装依赖。
- Notion Token 从 `%LOCALAPPDATA%\hermes\.env` 的 `NOTION_API_KEY` 读取；不写入脚本、日志、Notion 或聊天。
- AnkiConnect 固定访问 `127.0.0.1:8765`。脚本先检查资料库、API、`autoSync=false`、空 `customSyncUrl`、模型模板和牌组。
- 每次只处理 Notion Cards 的 PENDING 项，以及本地状态已知且 Revision 增大的 SYNCED 项；按 NoteKey 去重。身份不确定的旧笔记标记 CONFLICT，不覆盖。
- Reviews 按 CardID upsert；Anki 复习日志、卡片排程只读，不调用 AnkiWeb 同步。
- 并发调用由 SQLite 写事务锁串行化；运行状态库和脱敏日志位于 `%LOCALAPPDATA%\hermes\memories\脚本缓存\anki-notion-sync\`。
- 不创建定时任务，不创建重复的 Notion 数据库。
