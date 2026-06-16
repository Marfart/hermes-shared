# Gateway 完全停止诊断（2026-06-15 实战案例）

## 症状
- 用户报告 Telegram 断联
- `gateway_state.json` 显示 `gateway_state: stopped`, `restart_requested: true`
- 没有 gateway 进程在运行（`tasklist | findstr hermes` 找不到 `gateway run`）
- `gateway.log` 最后一条停在很久以前（本案例停在 2026-06-13 23:50）

## 根因
看门狗标记了 `restart_requested: true` 但没有实际执行重启。Gateway 进程在 6月13日被看门狗正常停止（`Shutdown phase: all adapters disconnected`），之后看门狗尝试重启但遇到了 "Another gateway instance is already running (PID 2788)" 错误（errors.log 中有记录）。之后反复尝试启动新实例都失败了（exit_nonzero），最终 gateway 就一直停在 stopped 状态。

## 快速修复
```bash
# 1. 确认没有 gateway 进程
tasklist | grep -i hermes

# 2. 检查权威 state 文件（只用 %LOCALAPPDATA% 的）
cat "$LOCALAPPDATA/hermes/gateway_state.json"

# 3. 重启 gateway
cd "$LOCALAPPDATA/hermes/hermes-agent/venv/Scripts" && ./hermes.exe gateway restart

# 4. 等 10-15 秒后验证
cat "$LOCALAPPDATA/hermes/gateway_state.json"
# 确认 telegram.state = "connected"
```

## 多 state 文件混淆问题

系统中存在多个 `gateway_state.json`：
- `%LOCALAPPDATA%/hermes/gateway_state.json` — **权威**
- `Desktop/hermes/gateway_state.json` — 实时同步备份（可能延迟）
- `Desktop/Working/Hermes/gateway_state.json` — 实时同步备份（可能延迟）

诊断时只看 `%LOCALAPPDATA%` 的。其他位置的 `updated_at` 可能停在几天前（本案例中 Desktop 版停在 6月2日），容易误判。

## Discord 持续重试问题

Discord 自 2026-06-03 起每次 gateway 启动都会尝试连接，30s 超时后失败，每 5 分钟重试。每天约 27 次重试，浪费约 13.5 分钟连接时间。如果不用 Discord，建议从配置中禁用以减少资源消耗。

## WeChat 断联后恢复

Gateway 重启后 WeChat 显示 `disconnected`，需要 ilinkai 扫码重新连接。Telegram 通常自动恢复（`connecting → connected`）。