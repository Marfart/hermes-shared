import subprocess

noter_py = r"C:\Users\Admin\AppData\Local\hermes\scripts\learn_noter.py"
category = "英语IELTS"
title = "IELTS-雅思完整指南"

def append(content):
    result = subprocess.run(["python", noter_py, "append", category, title, content], capture_output=True, text=True)
    print(result.stdout.strip())

append("""

## ⭐⭐⭐⭐⭐ Qwerty Learner（22.2k ⭐）
**地址**: https://github.com/RealKai42/qwerty-learner
**类型**: 桌面应用（支持 Windows/Mac/Linux，在线版也有）

**亮点**:
- 背单词 + 练打字二合一！
- 内置 IELTS / TOEFL / CET4-6 / GRE / 考研词汇词库
- **打字模式**：每个词必须完整正确输入才能继续，拼写记忆+肌肉记忆双巩固
- 支持 API 编程词库（学英语同时还能练代码变量名拼写）
- 可用 Tauri 打包为本地应用，离线可用
- 白天/夜间模式，统计学习数据

**最适合**: 平时用电脑多的 Kali！打字背单词一举两得
**下载**: 在线版直接可用 https://qwerty.kaiyi.cool/
""")


append("""

## ⭐⭐⭐⭐⭐ Read Frog / 陪读蛙（7.3k ⭐）
**地址**: https://github.com/mengxi-ream/read-frog
**类型**: Chrome 浏览器扩展（沉浸式翻译）

**亮点**:
- 开源沉浸式翻译扩展，相当于 immersive-translate 的开源替代
- 浏览英文网页时：**英文原文 + 中文翻译双排显示**
- 支持 DeepSeek / OpenAI / 谷歌翻译 / 微软翻译 等多种引擎
- 点击单词可直接查词典+发音
- 2万周活用户，更新活跃
- 支持文章AI分析：提取标题、摘要，让翻译更准确

**最适合**: 每天读英文文章（BBC / The Economist / 雅思阅读），边读边学
""")


append("""

## ⭐⭐⭐⭐ My IELTS（2k ⭐）
**地址**: https://github.com/hefengxian/my-ielts
**类型**: Vue.js 前端网页应用

**亮点**:
- 专为雅思打造，作者自己备考期间写的
- 包含【雅思词汇真经、语法、听力179、阅读538同义替换】等
- 词汇按场景分类：教育/科技/环境/社会/文化...
- 同义替换专攻：雅思阅读/听力的核心考点
- 可直接在线浏览

**最适合**: 雅思听说读写专项词汇积累
""")


append("""

## ⭐⭐⭐⭐ awesome-ielts（966 ⭐）
**地址**: https://github.com/ucatal/awesome-ielts
**类型**: 资源导航列表

**亮点**:
- 雅思备考资源的 **超级索引**！
- 按 Listening / Reading / Writing / Speaking / Vocabulary 分类收录
- 收录了最优质的 YouTube 频道、网站、工具
- 免费资源为主，全部经过筛选
- 包含推荐的高质量 Podcast 和 BBC 节目

**最适合**: 作为雅思资源地图，按需探索
""")


append("""

## ⭐⭐⭐⭐ openIELTS（358 ⭐）
**地址**: https://github.com/mcxiaoxiao/openIELTS
**类型**: 文档资料库

**亮点**:
- **零成本雅思全套资料**，非常完整！
- 包含：
  - ✅ 写作 Task 1 详解+范文（含流程图、地图）
  - ✅ 写作 Task 2 十大话题词汇、四大题型模板
  - ✅ 口语 2025年1-4月最新题库
  - ✅ 口语 P1+P2 串题笔记（Notion导出）
  - ✅ 听力179同义替换词
  - ✅ 阅读538同义替换词
  - ✅ AI口语串题 Prompt
  - ✅ IELTS 官方评分表
- 目标群体 6.0-7.5 分

**最适合**: 想白嫖全套资料的 Kali！直接下载 PDF
""")


append("""

## ⭐⭐⭐⭐ 程序员雅思备考指南（705 ⭐）
**地址**: https://github.com/EthanLin-TWer/ielts
**类型**: Gitbook 电子书

**亮点**:
- 作者90天自学考雅思，4个7分目标
- 核心方法：**听抄（听力） + 背模板（写作）**
- 总结了程序员最有效的备考路径
- 包含 Cambridge IELTS 4-15 真题索引
- 听力技巧：提前读P3/P4的题（高价值技巧！）

**最适合**: Kali 是 BLIIOT 工作+学英语并行，可以参考这个时间管理
""")


append("""

## ⭐⭐⭐⭐ A-Programmers-Guide-to-English（16.4k ⭐）
**地址**: https://github.com/yujiangshui/A-Programmers-Guide-to-English
**类型**: 学习指南

**亮点**:
- 专为程序员写的英语进阶指南 v1.2
- 从"为什么学不好英语"的底层问题讲起
- 发音纠正、音标学习、阅读方法论
- 强调：**可理解性输入（Comprehensible Input）** 理论
- 比 English-level-up-tips 更短小精悍

**最适合**: 先解决学习方法论问题再开始
""")


append("""

## ⭐⭐⭐⭐ MuJing / 目鲸（4.1k ⭐）
**地址**: https://github.com/tangshimin/MuJing
**类型**: Kotlin 桌面应用（Windows/Mac/Linux）

**亮点**:
- 通过**电影和美剧原声片段**学英语单词
- 每个单词都配有来自电影的真实语境句子+发音
- 内置字幕解析功能
- 支持自定义词库 + 从美剧字幕提取生词
- 完全本地运行，不需要联网

**最适合**: 放松时边刷剧边学英语～ 适合培养语感
""")


append("""

## ⭐⭐⭐ FluentDiary / FluentWhisper
**地址**: https://github.com/Thxamillion/fluentdiary-desktop
**类型**: 桌面应用（口语练习）

**亮点**:
- 免费开源的英语口语日记应用
- 用 **OpenAI Whisper** 进行语音识别，把你的口语转成文字
- 记录每天的英语口语练习，追踪进步
- 特别适合雅思口语 Part 1 的日常练习

**最适合**: 需要练口语但不好意思找真人对话的 Kali～
""")


append("""

## ⭐⭐⭐ Anki（全平台，生态最强大）
**地址**: https://github.com/ankitects/anki
**类型**: 间隔重复记忆卡（Spaced Repetition System）

**亮点**:
- ⭐ 21k+ Stars，间隔重复记忆法的黄金标准
- 有桌面版+AnkiMobile+AnkiDroid
- 雅思词汇、写作模板、听力场景词等社区牌组超多
- 可以配合 Obsidian（通过 Obsidian_to_Anki 插件）
- **小马推荐工作流**: Obsidian记笔记 ➡ 自动生成Anki卡片 ➡ 每天碎片时间复习
""")


append("""

---

# 🐾 小马的推荐使用方案

## 推荐工具组合
```
1️⃣ 英语学习方法论 ← English-level-up-tips（先读一遍入个门）
2️⃣ 日常背单词 ← Qwerty Learner（打字+背词双修）
3️⃣ 阅读提升 ← Read Frog（刷英文网页随时翻译辅助）
4️⃣ 间隔记忆 ← Anki + Obsidian插件（碎片时间复习）
5️⃣ 雅思专项 ← openIELTS + My IELTS（真题+模板+词汇）
6️⃣ 口语练习 ← FluentDiary / 找小马对练！♪
```

## 时间分配建议（每天30-60分钟）
| 活动 | 时间 | 频率 |
|:----|:----|:-----|
| Qwerty Learner 打字背词 | 10分钟 | 每天 |
| Read Frog 读英文文章 | 15分钟 | 每天 |
| 雅思专项（模板/真题） | 15-20分钟 | 每周3-4次 |
| 口语练习（小马或自录） | 10分钟 | 每周2-3次 |
| Anki 卡片复习 | 碎片时间 | 等车/午休 |

---

> 🐾 小马于 2026-06-02 从 GitHub 深挖整理 | 数据截止 2026年6月
> [[学习笔记首页]] | [[英语IELTS]]
""")

print("All GitHub projects written successfully ✅")