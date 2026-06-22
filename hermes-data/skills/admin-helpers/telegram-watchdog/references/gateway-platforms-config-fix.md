# Gateway Platforms 配置修复 (2026-06-22)

## 症状
Telegram/飞书在 `hermes status` 中显示 "✓ configured"，但实际没有连接。
`gateway_state.json` 中平台状态不是 `connected`。

## 根因
`config.yaml` 中 `gateway.platforms` 下平台配置为空对象 `{}`：
```yaml
gateway:
  platforms:
    telegram: {}   # ← 空对象 = 未真正启用
```

或者飞书完全不在 `gateway.platforms` 里。

注意：`platforms:` 和 `gateway.platforms:` 是两个不同的配置段：
- `platforms:` (顶层) — 平台应用凭证（app_id, app_secret, home_chat 等）
- `gateway.platforms:` — 网关连接启用开关

两者都需要正确配置才能连接。

## 修复步骤

### 1. 用 hermes config set 启用平台（不能直接 patch config.yaml）

```bash
# 启用 Telegram
hermes config set gateway.platforms.telegram.enabled true

# 启用飞书
hermes config set gateway.platforms.feishu.enabled true
```

⚠️ **不能直接编辑 config.yaml** — patch 工具会拒绝写入安全敏感配置。
必须用 `hermes config set` 命令。

### 2. 重启网关

```bash
hermes gateway restart
```

⚠️ **超时是正常的** — `hermes gateway restart` 在 Windows 上通常 30 秒后超时退出，
但网关实际上正在重启。等 10-15 秒后验证。

### 3. 验证连接

```bash
# 检查网关状态
hermes gateway status

# 检查平台连接（看日志）
hermes logs 2>&1 | grep -i "telegram\|feishu" | tail -10

# 检查 state 文件
cat %LOCALAPPDATA%/hermes/gateway_state.json
# 期望看到: "telegram": {"state": "connected", ...}
#           "feishu": {"state": "connected", ...}
```

## 验证成功的日志特征

重启后日志应出现：
```
INFO gateway.run: Sent shutdown notification to home channel telegram:8314311281
INFO gateway.platforms.feishu: [Feishu] Received raw message type=text ...
```

`gateway_state.json` 中：
```json
"platforms": {
  "telegram": {"state": "connected", "updated_at": "..."},
  "feishu": {"state": "connected", "updated_at": "..."}
}
```

## 常见陷阱

| 陷阱 | 说明 |
|------|------|
| 只配 `platforms:` 不配 `gateway.platforms:` | 有凭证但不连接 |
| `gateway.platforms.telegram: {}` | 空对象不等于启用，需要 `enabled: true` |
| 直接 patch config.yaml | 被安全机制拒绝，必须用 `hermes config set` |
| gateway restart 超时 = 失败 | 超时是正常的，等几秒后验证即可 |
| 多个 gateway_state.json | 只有 `%LOCALAPPDATA%/hermes/gateway_state.json` 是权威的 |
