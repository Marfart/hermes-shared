# IELTS Anki 音频文件与媒体工作流

## 适用范围

修复既有 IELTS 卡片，或为新卡建立音频。文件级音频验证、Anki 媒体写入、笔记更新、Notion 回写和云同步是不同验收阶段；不得把其中任一步的成功推断成端到端成功。

## 顺序

1. **建立回滚点并锁定身份。** 验证完整 `.colpkg`（ZIP CRC、`meta`/`collection.anki21b`/`media` 成员、解压后的 SQLite `quick_check`），记录 SHA-256。只读获取 Notion Cards 与 Anki `notesInfo`/卡片/复习记录；确认 NoteKey 唯一，Anki 的 NoteKey、English、NoteID、CardIDs 与 Notion 一致。保存 NoteID、CardIDs、字段快照及复习/排程指纹。状态为 `CONFLICT`、身份不全、重复键或 ID 不一致时跳过，不自行修复冲突。
2. **逐文件选声源。** 优先查 Wiktionary/Wikimedia Commons 的真实文件页面/API。读取实际文件的语言、口音、作者、许可、原始媒体 URL/格式和说明；只下载 API/文件页面给出的真实 URL，不根据单词拼接路径。记录许可与署名信息、原始文件哈希。音频文件名或搜索结果标题本身不能证明内容准确。
3. **无合格真人录音时本地 TTS。** 使用本地 Piper `en_GB-cori-high`，将卡片 `English` 原文作为合成输入；记明它是 TTS、语音模型/版本/哈希、语言与口音、许可来源，不标作真人录音或独立朗读。禁止收费 API 与未授权录音。已验证可产生英式英语 MP3 的本地流程：Piper CLI `2023.11.14-2` + `en_GB-cori-high` 生成 WAV，再由 FFmpeg 转码；这个验证只证明文件生成，不证明人耳发音验收。
4. **检查文件再发布。** 要求输出真实存在且非空；FFprobe 返回 MP3 codec/时长/采样率/声道；FFmpeg 完整解码无错误；测量 RMS/峰值或等价信号，排除静音；时长须与单词/短语长度相称。校验发音目标与卡片 English 字符串一致；真人文件以文件说明/来源证据作为文件级依据，无法独立试听或 ASR 时明确标记未独立听审。使用稳定且唯一的 MP3 文件名，并记录完整 SHA-256、字节数、时长、声源和所有检查结果。

   示例转码与验证命令：

   ```text
   ffmpeg -y -nostdin -v error -i input.wav -map 0:a:0 -vn -ac 1 -ar 44100 -c:a libmp3lame -b:a 128k output.mp3
   ffprobe -v error -show_entries format=duration,format_name,size:stream=codec_name,sample_rate,channels -of json output.mp3
   ffmpeg -v error -i output.mp3 -f null -
   ```

   Windows 上 Piper 若遇到非 ASCII 路径问题，将运行时、模型、配置、输入和输出临时复制到 Hermes 的 ASCII 临时目录执行；验证后再复制到持久任务目录并比较 SHA-256。不要把临时目录中的文件名直接写入 Anki。
5. **先存媒体，再改笔记。** 对每个经过验证的 MP3 调用 AnkiConnect `storeMediaFile`；随后 `retrieveMediaFile` 读回并解码，确认返回文件字节数与 SHA-256 完全一致。只有媒体读回通过后，才将 Anki `Audio` 更新为 `[sound:filename.mp3]`。通过 `updateNoteFields` 只写该字段，参数形状为 `{"note":{"id":NOTE_ID,"fields":{"Audio":"[sound:filename.mp3]"}}}`；回读所有字段与 `note_snapshot`，确认 NoteID、CardIDs、排程和 review fingerprint 与写入前一致。不要直接写 collection SQLite。
6. **回写 Notion 与本地同步状态。** 更新该页 `PayloadJSON` 内的 `Audio` 引用和 Revision；只改获授权的属性，保留其余字段。PATCH 后 GET 同一页面验证 Audio、NoteKey、Revision、NoteID、CardIDs。按现有 SQLite `BEGIN IMMEDIATE` 事务维护 NoteKey→NoteID/CardIDs、payload hash 和 revision；不要在状态库映射尚未确认时声称下一次同步不会覆空。若写操作结果不明，先读回精确目标，禁止盲目重发。
7. **分阶段云同步和批量。** 三张/用户指定试点均通过文件、Anki 媒体读回、笔记和 Notion 回读后，才进入批量阶段；保持 `CONFLICT` 行排除。每个媒体文件记录独立结果。按现有 `sync_ankiweb` 流程调用 `collection.sync`（`includeMedia=true`），直接轮询 operation；只在 RPC 无错误且 state=`succeeded`、`collectionComplete=true`、`mediaComplete=true` 时报告 Anki 桌面端与 AnkiWeb 集合/媒体同步成功。若 `waitingForUser`，停止并交给用户选择，不取消/替用户选方向。桌面端同步成功不证明 AnkiDroid 已下载；没有真实监听时标为“文件级通过，设备播放待验收”。

## 审计记录最少字段

每条卡片记录：English、NoteKey、NoteID、CardIDs；来源类型（真人/TTS）、来源 URL/文件名、语言/口音、作者或语音模型、许可/署名、生成器版本与模型 SHA-256、原始文件 SHA-256、MP3 文件名/字节数/时长/MP3 SHA-256、FFprobe/完整解码/非静音/文本匹配状态、Anki store/retrieve 回读状态、Audio 字段回读状态、复习/排程指纹对比、Notion Audio/Revision 回读状态、AnkiWeb `collectionComplete`/`mediaComplete` 状态、设备试听状态。未执行的检查必须标 `not verified`，不可用命令退出码替代结果。

## 最近批量验收（2026-10-14）

- 99 条 `SYNCED` IELTS 词卡均已用本地 Piper `en_GB-cori-high` 生成英式英语 TTS MP3；许可未重新核实的 Commons 真人录音未使用。每条记录了发音文本、模型/版本、唯一文件名、SHA-256、时长、FFprobe、完整解码和非静音结果。
- 99 个文件均通过 `storeMediaFile`/`retrieveMediaFile` 哈希回读；99 个既有笔记 Audio 字段和 Notion `PayloadJSON.Audio` 均回读匹配，Revision 正确递增或保留，Status 仍为 `SYNCED`。
- NoteID、CardIDs、非音频字段、排程与复习指纹均保持不变；唯一 `CONFLICT` 的 `involve` 未修改。
- 正常 AnkiConnect `collection.sync(includeMedia=true)` 返回 `succeeded`，`collectionComplete=true`、`mediaComplete=true`。这仅证明 Anki 桌面端↔AnkiWeb 同步，不证明 AnkiDroid 已下载或实际播放；尚未进行人耳试听。
- 完整审计文件位于 `memories/脚本缓存/anki-audio-repair/audio_repair_reconciliation_audit_v2.json`；音频资产清单位于同目录 `batch_audio_repair_audit_attempt1.json`。

## 新卡自动音频实现

`anki_notion_sync.py` 在唯一 NoteKey/重复检测与 `canAddNoteWithErrorDetail` 通过后，才为 Audio 为空的新 IELTS 卡生成 Piper TTS MP3；在添加笔记前完成文件检查、`storeMediaFile`、`retrieveMediaFile` 哈希核验。随后新笔记保存真实 `[sound:...]`，Notion PayloadJSON.Audio 与 Revision 同步更新，状态页回读后写本地映射。CONFLICT、重复项和已有 Audio 字段不会进入自动生成分支。新增卡的自动分支经 Piper 生成器与 Notion PayloadJSON/Revision 逻辑冒烟测试；未创建测试卡片。

## 已验证边界

Piper CLI `2023.11.14-2` 与 `en_GB-cori-high` 已在本机对 `modern society`、`benefits and drawbacks` 合成 WAV、转 MP3，并通过 FFprobe、完整解码及非静音信号检查；Commons `En-GB-opportunity.ogg` 曾通过文件级检查，但本批次因授权未重新核实而未使用。批量任务执行中现已独立验证 Anki 媒体读回、字段回读、Notion Revision/Status、复习与排程不变，以及 AnkiWeb 媒体同步。用户尚未在人耳/AnkiDroid 完成播放验收。