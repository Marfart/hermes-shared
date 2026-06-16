---
name: ielts-writing-evaluation-tools
version: 1.0.0
category: teaching
description: IELTS写作AI评分工具集 — LLM驱动雅思作文自动评估+反馈
tags: [ielts, writing, essay, evaluation, ai, llm, feedback]
---

# ✍️ IELTS 写作 AI 评分工具集

> 用LLM自动评估雅思写作Task 1/Task 2，提供Band评分+详细反馈

---

## 🏆 IELTS 写作评分工具

| 项目 | ⭐ | 描述 | 技术栈 | 评分维度 |
|------|-----|------|--------|----------|
| [Logisx/DeepEssay](https://github.com/Logisx/DeepEssay) | 36 | 雅思作文AI评估+Band分估计+警告功能 | LLM | Task Response, CC, LR, GRA |
| [araloak/ieltsGPT](https://github.com/araloak/ieltsGPT) | 30 | ChatGPT驱动雅思写作评估+详细反馈 | Python+GPT | 全4维度+改进建议 |
| [chillestt/Automated-IELTS-essay-evaluation](https://github.com/chillestt/Automated-IELTS-essay-evaluation) | 9 | 微调LLM自动评分雅思Task 2 | LLM fine-tuning | Band分+反馈 |
| [hung20gg/ielts_w2](https://github.com/hung20gg/ielts_w2) | 9 | 多LLM支持雅思写作Task 1/2评分 | Python+多LLM | Task 1+2 |
| [Pouyaexe/IELTS-Writing-Examinier](https://github.com/Pouyaexe/IELTS-Writing-Examinier) | 3 | IELTSEvaL—AI写作评估器 | Python | Task Response+CC+LR+GRA |
| [dpupkov/digitalquill](https://github.com/dpupkov/digitalquill) | 1 | 浏览器端雅思写作练习+Gemini AI反馈 | Web+Gemini | General Training |

---

## 📊 IELTS写作评分4维度

1. **Task Response (TR)** — 任务完成度：是否回答了题目所有部分
2. **Coherence & Cohesion (CC)** — 连贯与衔接：段落逻辑+连接词
3. **Lexical Resource (LR)** — 词汇资源：词汇多样性+准确性
4. **Grammatical Range & Accuracy (GRA)** — 语法范围与准确性

---

## 🛠️ 推荐使用方式

### 最快上手：araloak/ieltsGPT
```bash
pip install openai
# 编辑 data/essay.txt 写入你的作文
python ieltsGPT.py
# 输出: data/feedback.md (详细反馈)
```

### 自托管版：Logisx/DeepEssay
- 支持Band分估计
- 有警告功能（字数不足等）
- 适合本地长期使用

### 多模型对比：hung20gg/ielts_w2
- 支持切换不同LLM
- Task 1和Task 2都支持
- 可以对比不同模型的评分差异

---

## 💡 使用建议

1. 先用 **ieltsGPT** 快速评估，看Band分+4维度反馈
2. 用 **DeepEssay** 做深度分析，看警告+改进点
3. 反复修改作文直到Band 7+的水平
4. 配合 **LanguageTool/Harper** 检查语法错误
5. 写作模板参考 awesome-IELTS 中的 248 Band 9 范文

---

## ⚠️ 注意
- AI评分仅供参考，不代表真实考试分数
- 建议定期找真人老师批改确认水平
- 不同LLM评分标准可能有偏差
- Task 1（图表描述）和Task 2（议论文）评分标准不同