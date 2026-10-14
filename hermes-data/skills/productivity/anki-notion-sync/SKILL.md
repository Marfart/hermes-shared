---
name: anki-notion-sync
description: "Use when Kali says ‘同步 Anki’. Run the bridge."
version: 1.0.0
platforms: [windows]
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [Anki, Notion, IELTS, sync, Windows]
    category: productivity
---

# Windows IELTS Notion ↔ Anki 同步

## When to Use
Use this skill whenever Kali says “同步 Anki” or explicitly asks to run the Notion–Anki bridge. Execute the script and report only verified counts, blockers, and the result.

## 触发
Kali 说“同步 Anki”时，直接运行本地脚本，不要再问是否开始：

```text
python "C:/Users/Admin/AppData/Local/hermes/scripts/anki_notion_sync.py"
```

使用 Hermes 终端工具执行并读取 JSON 汇总。若脚本返回非零，先检查安全门与结果；不要绕过失败条件。

## 行为与边界
- 只按需触发；不创建 cron、计划任务或后台常驻同步。
- 只访问授权中控页的模板和既有 Cards、Reviews、Sync Log 数据源；不创建数据库。
- 仅使用 `127.0.0.1:8765` 的 AnkiConnect；每次确认资料库为「账户 1」、API v6、`autoSync=false`、`customSyncUrl` 为空、模型模板和目标牌组存在且匹配。
- 不调用 AnkiWeb 同步，不改 Anki 偏好或学习排程，不直接写 collection 数据库，不删除或重建笔记。
- 以 NoteKey 去重、按 Revision 更新。仅本地状态库已将 NoteKey 绑定到原 NoteID 且 Anki 回读身份匹配时才更新；身份不确定则标 CONFLICT，不覆盖旧笔记。
- 每条卡片经 Anki 回读验证后才写 Notion SYNCED；错误/冲突写入对应状态与说明。Reviews 按 CardID upsert，不追加重复快照。
- SQLite `BEGIN IMMEDIATE` 串行化并发调用；日志不得包含 Token、完整词条或请求体。
- Notion 偶发断连可能让单次运行返回非零；先读 JSON 汇总与脱敏日志、核对数据库实际状态，再重跑完整命令。NoteKey/CardID upsert 可幂等补齐，不盲目重发 `addNote`。
- Hermes 脚本/技能改动依用户既定共享仓库流程同步：先检查工作树，只暂存本次目标文件，聊天记录逐文件说明并核验远端提交；不要用 `git add -A` 把无关状态文件一并提交。
- API、模板、偏好、资料库或备份安全门失败时停止写入并如实报告；不要重启 Anki、改插件或改配置绕过。

## 执行、重试与验收
1. 首次先运行 `python "C:/Users/Admin/AppData/Local/hermes/scripts/anki_notion_sync.py" --first-safe-test`；只有这条记录完成 Anki 回读和 Notion `SYNCED` 回读后，才运行默认命令处理其余安全记录，不再重复申请已给出的授权。
2. 遇到 Notion/Anki 网络错误，先做只读状态核验；只读 GET 可有限退避重试。对 `addNote`、Notion PATCH/POST 等写操作，超时后先按 NoteKey、CardID 或 RunID 回读，绝不盲目重发。
3. 每条卡片/复习记录独立捕获错误并继续安全记录；非零退出时读脱敏日志和 Notion 实际状态，区分最终错误与已由重跑修复的瞬时读回问题。
4. 报告前独立核对 Cards 状态数、Anki 模型字段数与 NoteKey 唯一性、Reviews CardID 唯一性及覆盖率、Sync Log 回读、`autoSync=false`，并抽查卡片正反面非空及 `involve` 原笔记未变。仅凭命令退出码或工具调用已发出，不算端到端验收。
5. `BEGIN IMMEDIATE` 必须从状态库初始化前保持到本轮最终 commit；初始化函数不得自行 commit，否则会提前释放并发锁。
6. Reviews 按 CardID 更新并回读身份和复习统计；`FetchedAtUTC` 是易变字段，不作为内容一致性的唯一判据。读回后写入的状态应以稳定字段（CardID、NoteID、NoteKey、复习统计、牌组和卡片状态）核验。

以后 Kali 说“同步 Anki”时运行默认命令。

## 本地文件与凭证
- 脚本：`%LOCALAPPDATA%/hermes/scripts/anki_notion_sync.py`
- README：`%LOCALAPPDATA%/hermes/scripts/anki_notion_sync_README.md`
- 状态库及脱敏日志：`%LOCALAPPDATA%/hermes/memories/脚本缓存/anki-notion-sync/`
- Notion 凭证仅从 Hermes 本地 `.env` 或进程环境读取；绝不打印、复制到 Notion、写入日志或发送到聊天。
