# Self-Maintenance Session Report — 2026-05-29

Issues found during the autonomous evolution + self-maintenance run.

## 1. 财经简报 cron 错误 (job_id: 01837ee19638)

**错误信息：**
```
RuntimeError: Codex stream produced no bytes within 12s (TTFB threshold: 12s)
Delivery failed: Weixin send failed: iLink sendmessage rate limited
```

**原因分析：**
- Codex 模型 TTFB 超过12秒超时阈值
- 微信发送被速率限制（iLink rate limited）
- 两个错误叠加：模型超时 + 送达失败

**修复建议：**
1. 更换模型（当前用 Codex，可改 DeepSeek/Ollama Cloud 等响应更快的模型）
2. 在 cron prompt 中增加超时处理或简化任务降低 TTFT
3. Weixin 限流问题需检查消息内容长度或频率

## 2. Quarantine 记录残留

`hermes doctor` 报告 "1 skill(s) in quarantine (pending review)"，但 `skills/.quarantine/` 目录不存在。可能是：
- 旧版 quarantine 残留记录未清理
- 修复：检查 `~/.hermes/config.yaml` 中 quarantine 相关配置，或运行 `hermes doctor --fix`

## 3. Cua Driver 安装注意事项

- **锁文件问题**：安装若中断，需手动删除 `%USERPROFILE%\.cua-driver\install.lock`
- **Session 0 隔离**：Terminal 环境运行在 Session 0，`cua-driver doctor` 可能报 "session 1 desktop probe failed: 拒绝访问" — 这是正常行为（Session 0 不能访问桌面 Session 1 的 WindowStation），启动 `cua-driver serve` 后自动使用正确路径
- **Autostart via Scheduled Task 需要管理员权限**（schtasks 返回 "拒绝访问"），换用 Startup folder 快捷方式可行
- **启动文件夹方案**：通过 `WScript.Shell` COM 对象创建 `.lnk` 到 `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\`
