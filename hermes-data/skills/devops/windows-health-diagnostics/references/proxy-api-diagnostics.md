# Vortex Proxy HTTPS API 诊断

## 症状

LLM provider 连不上 / 返回 401 Unauthorized，但：
- 直接 curl（`--noproxy "*"`）到 API 是通的
- 走 `127.0.0.1:7897` 代理就报 401

## 根因

**Vortex（com.vortex.helper）代理的 HTTPS 转发不稳定。** 它可能保持 LISTENING 状态但实际上丢失了 HTTPS 转发能力——TLS 握手或 Authorization 头被代理损坏，导致远端服务返回 401 Unauthorized。

## 三步诊断法

```bash
# 1. 走代理测试（模拟 Hermes 系统环境）
curl -s -x http://127.0.0.1:7897 \
  "https://ollama.com/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OLLAMA_API_KEY" \
  -d '{"model":"deepseek-v4-flash","messages":[{"role":"user","content":"hi"}],"max_tokens":5}' \
  -w "\nHTTP:%{http_code}"

# 2. 不代理直连（隔离问题）
curl -s --noproxy "*" \
  "https://ollama.com/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OLLAMA_API_KEY" \
  -d '{"model":"deepseek-v4-flash","messages":[{"role":"user","content":"hi"}],"max_tokens":5}' \
  -w "\nHTTP:%{http_code}"

# 3. 对比结果
# 代理=401 + 直连=200 → 代理 HTTPS 转发损坏
# 两者都=200 → API 正常
# 两者都超时 → API 或网络有问题
```

> **⚠️ 重要：** .env 文件可能同时包含注释行和实际行（如 `# OLLAMA_API_KEY=your_key` 和 `OLLAMA_API_KEY=real_key`）。用 `grep "^OLLAMA_API_KEY"` 跳过注释行，否则 `head -1` 可能取到注释行导致 key 错误。

## 修复方案

| 方案 | 操作 | 效果 |
|:-----|:-----|:-----|
| **A. 切 provider** | `hermes config set model.provider deepseek` | 立即可用，绕过代理问题 |
| **B. 加 no_proxy** | 在系统环境变量加 `no_proxy=ollama.com` | 让 ollama 请求跳过代理 |
| **C. 重启 Vortex** | 任务管理器 → 结束 com.vortex.helper → 重新启动 | 临时恢复，但会复发 |
| **D. 完全绕过代理** | 设置 `HTTP_PROXY="" HTTPS_PROXY=""` | 全局不代理 |

## 关联问题

- 同一代理也导致 Telegram/微信同时断连（看门狗场景）
- 代理可能表面 LISTENING 但实际已死（端口通但不转发应用层数据）
- 只影响 POST 请求的 body/headers；GET /v1/models（无 body）有时能通过

## 预防

长期方案：`HERMES_HTTP_PROXY=""` 环境变量让 Hermes 完全不读系统代理设置。或升级至支持稳定 HTTPS MITM 的代理方案。
