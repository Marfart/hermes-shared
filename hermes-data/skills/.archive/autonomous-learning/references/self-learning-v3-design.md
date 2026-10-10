# self_learning_v3.py 设计决策

## 为什么要有这个独立脚本

Agent模式cron需要LLM运行每一轮，消耗token。当Telegram delivery不工作导致报告送不到时，可以用这个纯Python脚本替代agent模式，通过 `no_agent=True cron` 零token运行。

但Windows上no_agent脚本的stdout捕获有bug（见 `windows-cron-delivery-issues.md`），所以当前实际方案是**agent模式cron调用这个脚本**：agent跑 `python self_learning_v3.py`，捕获stdout作为报告输出。

## 关键设计

### sys.path 修复（第4-8行）
cron环境清空 `sys.path`，所以脚本在import处静默崩溃。修复：
```python
import sys as _sys, os as _os
_stdlib = _os.path.normpath(_os.path.abspath(
    _os.path.join(_os.path.dirname(_os.__file__), "..", "Lib")))
if _stdlib not in _sys.path:
    _sys.path.insert(0, _stdlib)
```
注意：用 `_sys` / `_os` 别名避免被后续import同名覆盖。

### 搜索关键词智能语言检测
```python
# 从topic名判断搜索语言
if any(kw in topic_lower for kw in ["bash", "shell", "powershell", "脚本"]):
    lang = "Shell"
elif any(kw in topic_lower for kw in ["c++", "c语言", "c指针"]):
    lang = "C++"
elif any(kw in topic_lower for kw in ["c", "linux", "内核", "汇编"]):
    lang = "C"
...
```
之前硬编码 pillar 0 = Python，导致搜 Bash话题找到不相关项目。

### 星数过滤逻辑
```python
# 优先50⭐以上
for item in items:
    if item.get("stargazers_count", 0) < 50: continue
    return item, full_name
# 降级到20⭐
for item in items:
    if item.get("stargazers_count", 0) < 20: continue
    return item, full_name
```

### 搜索降级
1. 带语言限制搜 GitHub API
2. 如果空结果 → 去掉语言限制重搜
3. 如果还空 → 返回 None（本轮跳过）

## 已知局限

1. **不读源码** — 只读README（约7000字符），不分析核心文件
2. **不提取设计模式** — README直接dump到笔记
3. **不产出代码** — 产出只是README文本摘要
4. **可能搜到不相关项目** — "Bash高级脚本技巧"搜到PDF电子书合集
   → 这本质上是搜索词的问题，中文topic对应的英文GitHub项目不直接

## 改进方向（Kali评估中）

如果Kali说"学得太浅"，应该：
1. 读README + 至少3个核心源文件
2. 提取≥3个设计模式/架构决策
3. 产出可运行的Python/C代码
4. 降低频率（每小时 vs 每15分钟）给源码阅读留足时间