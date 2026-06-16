# Vortex `mode: direct` 配置陷阱

## 核心问题

Vortex (Clash) 代理的 `~/.config/com.vortex.helper/config.yaml` 中 `mode` 字段控制流量路由：

| mode | 行为 | 风险 |
|------|------|------|
| `rule` | 按规则分流（GFW域名走代理，国内直连） | ✅ 正常 |
| `global` | 全部流量走代理 | 慢但能用 |
| `direct` | **全部流量直连，忽略所有代理规则** | ❌ GFW域名全部超时 |

`mode: direct` 是**静默的**——代理进程不报错、端口正常LISTENING、`netstat`显示一切正常。但所有需要翻墙的HTTPS请求全部连接超时。

## 症状识别

1. 所有HTTPS API报 `Connection error` / `Max retries exhausted`
2. 代理端口 7897 正常 LISTENING
3. `curl -x http://127.0.0.1:7897 https://api.openai.com` → 超时
4. `curl --noproxy "*" https://api.openai.com` → 也超时（GFW封锁）
5. 代理返回 HTTP 400（端口活着但不转发）

**关键对比：** 代理返回超时 + 直连也超时 → 不是代理故障，是代理**没在转发**（mode=direct）。

## 诊断命令

```bash
# 1. 检查当前mode
grep "^mode:" ~/.config/com.vortex.helper/config.yaml

# 2. 对比测试（代理 vs 直连）
curl -s -o NUL -w "proxy: %{http_code}\n" -x http://127.0.0.1:7897 --connect-timeout 10 https://api.openai.com/v1/models
curl -s -o NUL -w "direct: %{http_code}\n" --noproxy "*" --connect-timeout 10 https://api.openai.com/v1/models

# 3. 结果解读
# proxy=401 + direct=000 → 代理正常转发(GFW域名走代理)，401=需要认证说明API可达
# proxy=000 + direct=000 → mode可能是direct(代理没转发)
# proxy=200 + direct=200 → 不需要代理的域名(非GFW封锁)
```

## 修复步骤

```bash
# 1. 改配置
sed -i 's/^mode: direct/mode: rule/' ~/.config/com.vortex.helper/config.yaml

# 2a. Vortex API重载（如果external-controller可达）
curl -X PUT http://127.0.0.1:39797/configs -H "Content-Type: application/json" -d '{"path": ""}'

# 2b. 或者杀进程让Vortex自动重启（需要管理员权限）
# ShellExecuteW(0, 'runas', 'taskkill', '/F /IM com.vortex.helper.exe', None, 0)
# Vortex是系统服务，杀掉后会自动重启

# 3. 验证修复
grep "^mode:" ~/.config/com.vortex.helper/config.yaml  # 应显示 mode: rule
curl -s -o NUL -w "%{http_code}" -x http://127.0.0.1:7897 --connect-timeout 10 https://api.openai.com/v1/models
# 期望: 401(可达) 不是 000(超时)
```

## 跨机器诊断

当另一台机器上的bot报告API连接超时时，先检查共享网络环境中的Vortex配置：

1. 本机 `curl -x proxy https://blocked-api` → 如果也超时 → 检查本机Vortex mode
2. 两台机器共用同一网络出口，Vortex配置错误会影响所有依赖代理的设备
3. 通过Bot Relay通知对方修复步骤

## 历史案例

- **2026-06-16:** 小马(Mac)报告 `⏳ Retrying... ❌ API failed after 3 retries — Connection error`，切换fallback模型也失败。根因：Vortex `mode: direct`，修复后立即恢复。