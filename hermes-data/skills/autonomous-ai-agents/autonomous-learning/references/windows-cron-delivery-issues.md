# Windows Cron Delivery Issues (2026-06-07)

## Agent模式 cron delivery bug

**症状：** Agent模式cron job跑成功（状态文件更新、产出文件写入、Obsidian笔记写入都正常），`last_delivery_error: null`，cron日志有完整Response内容，但**Telegram用户收不到报告**。

**已测试的config：**
- `deliver: origin` → ❌ 不送达
- `deliver: telegram:8314311281` → ❌ 不送达（明确指定chat_id也不行）

**当前workaround（已验证2026-06-07）：**
Cron的prompt不直接做学习，而是：
```
1. 运行学习脚本 python /c/Users/Admin/AppData/Local/hermes/scripts/self_learning_v3.py
   捕获其 stdout
2. 直接转发给用户
```
Agent会执行terminal命令调Python脚本→捕获stdout→作为最终回复输出。这样报告内容就在Response里，虽然Telegram端仍然收不到，但至少cron日志里有完整记录。

## no_agent=True stdout捕获bug（Windows特有）

**症状：** 同样的脚本在bash手动跑完美输出stdout，但通过cron no_agent=True运行就报告 `Status: silent (empty output)`。但状态文件确实更新了（说明脚本确实执行了）。

**已测试的方案（全部失败）：**
1. 直接注册 `.py` 文件 → silent
2. 用 `.sh` bash包装 → silent
3. `.sh` 里用绝对Python路径 → silent
4. 清空PATH模拟cron最小环境 → 手动跑正常，cron跑silent

**根因推测：** Windows下cron调度器的subprocess stdout管道与Python/Popen的stdout交互有问题。可能是cron的subprocess创建方式不捕获Python的stdout缓冲。