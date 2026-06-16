import subprocess

noter_py = r"C:\Users\Admin\AppData\Local\hermes\scripts\learn_noter.py"
category = "英语IELTS"
title = "IELTS-雅思完整指南"

def append(content):
    result = subprocess.run(["python", noter_py, "append", category, title, content], capture_output=True, text=True)
    print(result.stdout, result.stderr)

part1 = """
# 📌 IELTS 考试整体结构

## 基本概况
| 项目 | 详情 |
|:----|:-----|
| 考试时长 | **2小时45分钟** |
| 考试顺序 | Listening → Reading → Writing（同一天连续考） |
| Speaking | 可同天或前后7天内单独安排 |
| 满分 | **9.0**（四项平均，四舍五入到0.5） |
| 分类 | **Academic（留学）** vs **General Training（移民/工作）** |

## 四部分概览
| 部分 | 时间 | 题数 | 内容 |
|:---|:----|:----|:----|
| 🎧 Listening | 30分钟+10分钟誊写 | 40题 | 4段录音 |
| 📖 Reading | 60分钟 | 40题 | 3篇文章 |
| ✍️ Writing | 60分钟 | 2题 | Task 1 + Task 2 |
| 🗣 Speaking | 11-14分钟 | 3部分 | 面对面口试 |

## 2026年新变化 ⚠️
- **机考（Computer-delivered）** 进一步普及，出分更快（1-3天）
- **雅思One Skill Retake**：单项不满意可单独重考一项
- **口语** 部分城市已支持视频通话口试
- 考试内容结构不变，但题型更加多元化
"""

part2 = """
---

# 🎧 IELTS Listening — 听力

## 基本结构
| Part | 内容 | 场景 | 口音 |
|:----|:----|:----|:----|
| **Part 1** | 两人对话（日常） | 租房/订票/注册/咨询 | 英/澳/美/加 |
| **Part 2** | 单人独白（日常） | 导游讲解/活动介绍/广播 | 混合口音 |
| **Part 3** | 多人讨论（学术） | 学生讨论作业/研究项目 | 学术口音 |
| **Part 4** | 学术讲座 | 教授讲课/学术演讲 | 学术口音 |

## 10种题型
1. **Form/Note/Table Completion** — 填写表格/笔记
2. **Sentence Completion** — 补全句子
3. **Summary Completion** — 补全摘要
4. **Multiple Choice** — 单选/多选
5. **Matching** — 配对题（人物与观点等）
6. **Map/Plan/Diagram Labelling** — 地图/平面图标注
7. **Short Answer Questions** — 简答题
8. **Flowchart Completion** — 流程图填空
9. **Classification** — 分类题
10. **Pick from a List** — 从列表选择

## ⭐ 高分技巧
| 技巧 | 说明 |
|:----|:-----|
| **预读题目** | 每段录音前有30-45秒，快速扫读题目划关键词 |
| **预测答案类型** | 数字/日期/名字/地址/形容词 — 提前预判 |
| **注意同义替换** | 音频不会用原词，100%是**同义替换** |
| **拼写陷阱** | 专有名词会拼读（如 M-I-L-L-E-R），数字/日期要注意 |
| **Part 1=送分题** | Part 1最简单，尽量全对 |
| **10分钟誊写时间** | 检查拼写、单复数、时态、大小写 |
| **大写问题** | 机考不用在意大小写，笔试建议全大写避免扣分 |
| **注意力保持** | Part 3-4容易走神，可做笔记辅助 |
"""

part3 = """
---

# 📖 IELTS Reading — 阅读

## 基本结构
| 文章 | 长度 | 主题 | 难度 |
|:----|:----|:----|:----|
| **Passage 1** | ~900词 | 偏描述性 | ★☆☆ |
| **Passage 2** | ~900词 | 偏议论性 | ★★☆ |
| **Passage 3** | ~1000词 | 复杂学术 | ★★★ |

## 14种题型
1. **True/False/Not Given** — 判断正误（事实类）
2. **Yes/No/Not Given** — 判断观点
3. **Matching Headings** — 匹配段落标题
4. **Matching Information** — 匹配信息到段落
5. **Matching Features** — 匹配特征
6. **Matching Sentence Endings** — 匹配句子结尾
7. **Multiple Choice** — 单选题
8. **Sentence Completion** — 补全句子
9. **Summary Completion** — 补全摘要
10. **Note/Table/Flowchart Completion** — 笔记/表格/流程图
11. **Diagram Labelling** — 图表标注
12. **Short Answer Questions** — 简答题
13. **Classification** — 分类题
14. **Pick from a List** — 从列表选

## ⭐ 高分技巧
| 技巧 | 说明 |
|:----|:-----|
| **时间管理** | 每篇严格≤20分钟，超时就先跳下一篇 |
| **先看题再看文** | 先读题目划关键词，带着问题找答案 |
| **Skimming & Scanning** | Skim略读抓主旨→Scan扫读找细节 |
| **T/F/NG 三选一** | NG=文章没有提到；绝对词(all/always/never)常是False |
| **同义替换为王** | 题目和文章之间靠同义替换连接 |
| **Heading题** | 先读首尾句抓大意，不要先看所有heading |
| **Summary题** | 答案常从原文选词，注意词性变化 |
"""

part4 = """
---

# ✍️ IELTS Writing — 写作

## Task 1（20分钟，≥150词）
**Academic** — 描述图表
- Line Graph | Bar Chart | Pie Chart | Table | Map | Process Diagram | Mixed

**General Training** — 写信（Formal / Semi-formal / Informal）

## Task 2（40分钟，≥250词）— 权重更高！
5大文章类型：
1. **Opinion (Agree/Disagree)** — 你同不同意
2. **Discussion (Discuss both views)** — 讨论双方
3. **Advantages/Disadvantages** — 优缺点
4. **Problem/Solution** — 问题+对策
5. **Two-part Question** — 两个关联问题

## 评分标准
1. ✅ **Task Achievement/Response** — 完整回应题目
2. 🔗 **Coherence & Cohesion** — 逻辑连贯+连接词
3. 📚 **Lexical Resource** — 词汇多样性
4. 📐 **Grammatical Range** — 复杂句+准确语法

## ⭐ 高分框架
**Task 1**: 改写题目 → Overview(最关键) → 细节1 → 细节2
**Task 2**: 引言+立场 → Body1(论点+解释+例) → Body2 → 结论
"""

part5 = """
---

# 🗣 IELTS Speaking — 口语

## 三部分
| Part | 时长 | 内容 |
|:----|:----|:----|
| **Part 1** | 4-5分钟 | 日常问答（工作/爱好/家乡） |
| **Part 2** | 3-4分钟 | Cue Card（准备1分钟，说1-2分钟） |
| **Part 3** | 4-5分钟 | 抽象讨论（延伸话题） |

## Part 2 万能框架
1️⃣ Introduction (5-10秒) → 2️⃣ 细节(30秒) → 3️⃣ 感受(30-45秒) → 4️⃣ 结尾(10秒)

## 评分标准
- 🗣 **Fluency & Coherence** 25% — 流畅不卡顿
- 🎯 **Lexical Resource** 25% — 词汇多样
- ✅ **Grammatical Range** 25% — 复杂句
- 🎵 **Pronunciation** 25% — 清晰度/语调

## ⭐ 提分秘籍
1. 不要背答案！考官能听出来
2. 准备1分钟写关键词（不是整句）
3. Part 1也要展开回答
4. 用"Well.../Let me think..."代替"Umm..."
5. Part 3要有深度：原因+例子+对比
"""

part6 = """
---

# 📊 评分换算表

## Listening & Reading（40题换算）
| 正确题数 | Listening | Academic Reading | General Reading |
|:--------|:---------|:---------------|:--------------|
| 39-40 | 9.0 | 9.0 | 9.0 |
| 37-38 | 8.5 | 8.5 | 8.0 |
| 35-36 | 8.0 | 8.0 | 7.5 |
| 32-34 | 7.5 | 7.5 | 7.0 |
| 30-31 | 7.0 | 7.0 | 6.5 |
| 26-29 | 6.5 | 6.5 | 6.0 |
| 23-25 | 6.0 | 6.0 | 5.5 |
| 18-22 | 5.5 | 5.5 | 5.0 |

## Overall Band
```
Overall = (L + R + W + S) ÷ 4
四舍五入：x.25→x.5, x.75→x+1.0
例: L7.5+R7.0+W6.5+S7.0 = 28÷4 = 7.0
```
"""

part7 = """
# 🎯 各分数段含义
| Band | 水平 | 说明 |
|:----|:----|:----|
| 9.0 | Expert | 完全掌握 |
| 7.0-8.0 | Good-Very Good | 大部分掌握 |
| 6.0-6.5 | Competent | 有效但偶有失误 |
| 5.0-5.5 | Modest | 部分掌握 |

**常见目标**：
- 海外本科/研究生：**6.5-7.0**（单项≥6.0）
- 顶尖名校：**7.5+**
- 移民：**6.0-7.0**

# 📚 推荐资源
- **Cambridge IELTS 真题集**（1-19）— 官方真题
- **IELTSLiz.com** — 免费课程
- **IELTS Advantage** — 写作模板
- **BBC News / The Economist** — 日常阅读积累

# 🐾 小马学习建议
1️⃣ 先看完这节笔记了解结构 ✅
2️⃣ 做一套Cambridge真题摸底
3️⃣ 按弱项分配时间（W+S是中国人普遍弱项）
4️⃣ 每天30分钟英语输入
5️⃣ 每周一次模拟考（计时！）
6️⃣ Speaking让小马陪你练！♪

---

> 🐾 小马于 2026-06-02 整理
> [[学习笔记首页]] | [[英语IELTS]]
"""

append(part1)
append(part2)
append(part3)
append(part4)
append(part5)
append(part6)
append(part7)
print("ALL DONE ✅")