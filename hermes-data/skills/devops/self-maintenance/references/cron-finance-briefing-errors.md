# 财经简报 Cron 错误记录

**Cron ID**: 01837ee19638
**Name**: 每日财经简报+基金推荐+财经问答
**Schedule**: 30 8 * * 1-5 (工作日 08:30)
**Model**: Codex (OpenAI Responses API)
**Skills**: (none)
**Deliver**: weixin

## 错误记录

### 2026-05-29 错误
```
error: RuntimeError: Codex stream produced no bytes within 12s (TTFB threshold: 12s)
Delivery failed: Weixin send failed: iLink sendmessage rate limited: ret=-2 errcode=None errmsg=rate limited
```

**错误链分析：**

1. **Codex TTFB 超时 (12s)** — 模型12秒内未返回任何字节
   - 可能原因：Codex API 高峰时段响应慢，或网络抖动
   - TTFB threshold 是 Hermes 内置保护机制（12秒无响应即超时）

2. **微信限流** — 发送频次超过微信接口限制
   - `ret=-2` 是 iLink 的速率限制错误码
   - 可能财经简报内容较长，或同时有其他消息导致触限

## 修复方案参考

- **换模型**：改用其他 provider（如 deepseek 或 ollama-cloud）避免 Codex 超时
- **加重试**：在 cron prompt 中增加重试逻辑
- **分批发送**：如果内容过长，分两段发送
- **微信限流缓解**：调整 cron 时间避开高峰，或缩短内容

## 当前状态

- Cron 仍为 [active]，下次运行 2026-06-01 08:30
- 未采取修复措施，等待用户指示
