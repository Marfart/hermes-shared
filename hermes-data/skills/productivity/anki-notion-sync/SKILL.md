---
name: anki-notion-sync
description: "Use when Kali says ‘同步 Anki’. Run the bridge."
version: 1.3.0
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
- 仅使用本机 `127.0.0.1:8765` 的既有 AnkiConnect；确认资料库为「账户 1」、`autoSync=false`、`customSyncUrl` 为空、模型模板和目标牌组匹配。保持 `autoSync=false`，不触发后台/定时同步。
- 默认流程在 Notion→Anki 状态回写后，通过同一 AnkiConnect 的 JSON-RPC `/api/v1` 直接调用 `collection.sync`，再轮询该 operation 的 `operations.get`；不要用 `api.execute` 包装它，因为包装会隐藏内部 sync 的 `waitingForUser` 状态。只在顶层 RPC `error` 为空、operation=`succeeded` 且 `collectionComplete=true`、`mediaComplete=true` 时记为 AnkiWeb SUCCESS；请求被接受不等于同步完成。
- 每次默认触发只执行一次云同步；即使没有待处理卡片，也要同步一次以发现手机端新复习数据，并且只在成功后回传 Reviews，不要同一轮重复触发云同步。
- 若 operation=`waitingForUser`（全量 Upload/Download/冲突选择），立即停止后续处理与 Reviews 回传；不选择方向、不关闭对话框。不要对这个状态调用 `operations.cancel`：它只调用 `abort_sync`，不会关闭方向选择对话框，可能留下仍可触发的 UI 回调；保持等待并报告用户处理。运行中超时才请求取消并记 TIMEOUT，不继续 Reviews。
- 报告 AnkiConnect 已完成 Windows 客户端与 AnkiWeb 的集合/媒体同步，不要据此声称手机 App 已拉取；手机端是否完成需单独验证。把云端选择冲突与 Notion Cards 的既存 CONFLICT 分开报告。
- 不直接写 collection 数据库，不删除或重建笔记，不修改 Anki 学习排程。
- 以 NoteKey 去重、按 Revision 更新。仅本地状态库已将 NoteKey 绑定到原 NoteID 且 Anki 回读身份匹配时才更新；身份不确定则标 CONFLICT，不覆盖旧笔记。
- 每条卡片经 Anki 回读验证后才写 Notion SYNCED；错误/冲突写入对应状态与说明。Reviews 按 CardID upsert，不追加重复快照。
- SQLite `BEGIN IMMEDIATE` 串行化并发调用；日志不得包含 Token、完整词条或请求体。
- Notion 偶发断连可能让单次运行返回非零；先读 JSON 汇总与脱敏日志、核对数据库实际状态，再重跑完整命令。NoteKey/CardID upsert 可幂等补齐，不盲目重发 `addNote`。
- Hermes 脚本/技能变更同步共享仓库时，遵循 `github` 技能的显式路径暂存、提交前暂存路径检查与推送后远端 HEAD 核验；本流程还须在 `聊天记录.md` 逐文件说明，并排除无关状态文件。
- API、模板、偏好、资料库或备份安全门失败时停止写入并如实报告；不要重启 Anki、改插件或改配置绕过。

## 执行、重试与验收
1. 本环境已完成初次导入；每次用户说“同步 Anki”时直接运行默认命令一次，流程为 Notion Cards→Anki 写入/回读→Notion 状态回写→AnkiConnect AnkiWeb 集合/媒体同步→成功后 Reviews 回传。只有全新安装或用户明确要求安全首条测试时才用 `--first-safe-test`。
2. 遇到 Notion/Anki 网络错误，先做只读状态核验；只读 GET 可有限退避重试。对 `addNote`、Notion PATCH/POST 等写操作，超时后先按 NoteKey、CardID 或 RunID 回读，绝不盲目重发。
3. 每条卡片/复习记录独立捕获错误并继续安全记录；非零退出时读脱敏日志和 Notion 实际状态，区分最终错误与已由重跑修复的瞬时读回问题。
4. 报告前独立核对 Cards 状态数、Anki 模型字段数与 NoteKey 唯一性、Reviews CardID 唯一性及覆盖率、Sync Log 回读、`autoSync=false`，并抽查卡片正反面非空及 `involve` 原笔记未变。仅凭命令退出码或工具调用已发出，不算端到端验收。
5. `BEGIN IMMEDIATE` 必须从状态库初始化前保持到本轮最终 commit；初始化函数不得自行 commit，否则会提前释放并发锁。
6. Reviews 按 CardID 更新并回读身份和复习统计；`FetchedAtUTC` 是易变字段，不作为内容一致性的唯一判据。读回后写入的状态应以稳定字段（CardID、NoteID、NoteKey、复习统计、牌组和卡片状态）核验。

以后 Kali 说“同步 Anki”时运行默认命令。

## 音频字段修复

当用户要求修复 IELTS 卡片音频或自动为新卡片处理音频时，先按 `references/audio-media.md` 逐卡验证来源、MP3 文件、Anki 媒体与同步结果。`{{tts en_GB:English}}` 是模板生成的 TTS 回退，不代表已存在的 MP3 媒体。对已修复或已生成音频的卡片，Audio 字段应指向已验证的 `[sound:filename.mp3]`；模板应优先播放该真实媒体，仅当 Audio 为空或缺失时才回退到英式 TTS。批量修复只改 Audio 字段，不重建卡片或修改模板。

- 真人录音优先使用可复用的 Wiktionary/Wikimedia Commons 文件；必须读取实际文件页面/API 元数据与实际下载的文件，记录准确来源、语言/口音、作者、许可、源文件哈希。不得按词拼文件 URL，也不得在未确认许可时复用。
- 没有可靠且许可清楚的真人录音时，使用本地 `en_GB-cori-high` Piper TTS；明确标注 TTS，不冒充真人。禁止未经授权录音或擅自调用收费语音 API。
- 每个文件须通过存在/大小、FFprobe、完整解码、合理时长和非静音检查；发音文本必须对应 Anki `English` 原值。保存 provenance、生成器/模型版本、时长、SHA-256 和检查结果。
- 通过 AnkiConnect `storeMediaFile` 保存后，必须用 `retrieveMediaFile` 回读并比较哈希，之后才更新 Anki `Audio` 字段。此插件的 `updateNoteFields` 参数必须包装为 `{"note":{"id":NOTE_ID,"fields":{"Audio":"[sound:FILE.mp3]"}}}`；不要把 `fields` 放在 `note` 外面。
- 更新仅限 `Audio`；回读确认其他字段、NoteID、CardID、排程与复习历史均未改变。同步 Notion `PayloadJSON.Audio` 和 Revision，并更新本地状态库的对应映射/哈希，避免下一轮同步把音频清空。写入过程按现有事务与超时后回读规则操作，禁止盲目重试。
- 默认先用授权试点验证；若 Kali 明确授权对指定整批直接修复且备份、NoteKey/NoteID 映射与只读预检通过，不再额外要求真实试点审批，直接逐条处理全部安全匹配目标；保持 `CONFLICT` 排除。按需执行 AnkiWeb 同步，并仅在 operation 成功且 `collectionComplete=true`、`mediaComplete=true` 时报告桌面端/云端媒体同步成功。该状态不证明 AnkiDroid 已下载或能播放；未做真人听音时报告设备验收待验证。
- 不创建 cron、计划任务或轮询。新增 IELTS 卡自动音频已接入 `anki_notion_sync.py`：仅在唯一 NoteKey/重复检查和 `canAddNoteWithErrorDetail` 通过后，对 Audio 为空的新卡用本地 Piper `en_GB-cori-high` 合成、FFprobe/完整解码/非静音检查、`storeMediaFile` 与 `retrieveMediaFile` 哈希回读；随后把真实 `[sound:...]` 加入新笔记、PayloadJSON 与 Revision，并在 Notion 回读确认。已有 Audio 保留，CONFLICT/重复项在生成前跳过。该新卡分支已完成生成器与 Notion Revision 写入逻辑的隔离冒烟测试；没有为测试创建卡片。

- 音频修复通过 AnkiConnect 直接完成；CUA 截图或 apiReflect 操作清单不是前置条件。若用户不要求设备试听，文件解码、非静音、媒体回读哈希和字段回读通过即可继续批处理；未做真人听音时明确报告设备验收未验证。
具体命令与验收顺序见 `references/audio-media.md`。

## 本地文件与凭证
- 脚本：`%LOCALAPPDATA%/hermes/scripts/anki_notion_sync.py`
- README：`%LOCALAPPDATA%/hermes/scripts/anki_notion_sync_README.md`
- 状态库及脱敏日志：`%LOCALAPPDATA%/hermes/memories/脚本缓存/anki-notion-sync/`
- Notion 凭证仅从 Hermes 本地 `.env` 或进程环境读取；绝不打印、复制到 Notion、写入日志或发送到聊天。
