# Kali's Corrections & Guidance

## Zero-Token Principle
- **Cron no_agent=True 脚本不消耗 token** — Kali 非常在意这一点
- 任何新功能如果需要在 cron 里跑，确保是纯 Python 脚本，不调 LLM
- 如果对话中查询数据（如"我走了多久"），直接用本地 SQLite 查，不调模型

## Watchdog 脚本不可删除
- Kali 明确说过：**"不要删掉，可以优化但是不要删去"**
- v6/v7 脚本保留为回退，永不删除
- 升级只改 cron job 指向的新脚本，旧脚本保持文件完整性

## 空闲检测阈值
- Kali 认为 30 秒检测太短（看文章会触发）
- **3 分钟（180秒）** 是正确的阈值
- 看文章、读代码、想问题的安静时间不算"离开"

## Session 0 保护
- cron 任务在 Windows Session 0 运行
- GetLastInputInfo 在 Session 0 读不到用户的键盘/鼠标事件
- 判断方法：对比上一条记录，连续两次 idle > 30 分钟 → 标记为"未知（后台模式）"
- 只有对话中直接调用 GetLastInputInfo 才能读到真实空闲时间
