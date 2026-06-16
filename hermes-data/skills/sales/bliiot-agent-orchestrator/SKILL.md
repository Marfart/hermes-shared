---
name: bliiot-agent-orchestrator
description: "多角色 Agent 管道编排器 — 从 CrewAI/LangGraph 借鉴的角色分离+状态机模式，将扁平客户开发管道拆分为 6 个专业 Agent"
version: 1.0.0
author: Tachikoma
platforms: [windows]
trigger: "用户要跑客户开发管道 / 想用多Agent模式 / 说角色分离 / 跑joinf/maps双管道 / 跑xray / 搜领英"
---

# BLIIOT Multi-Agent Orchestrator

## 灵感来源
- **CrewAI 角色分离** — 每个 Agent 有独立 role/goal
- **LangGraph 状态机** — 明确 stage 转换 + 回滚点
- **检查点模式** — 支持断点续跑

## 6 个 Agent 角色

| 角色 | 职责 | 脚本 |
|:----|:-----|:-----|
| 🕵️ **Scout** 侦查员 | 搜索客户线索（富通/Google Maps/DDG LinkedIn X-Ray） | fetch_joinf / scrape_maps / ddg-linkedin-xray |
| 📊 **Analyst** 分析员 | 增强数据 + 产品匹配评分 | enrich_joinf / enrich_maps |
| 📋 **Followup** 跟进文檔 | 生成客户跟进文档 | build_followup_document.mjs |
| 📝 **Queue** 队列员 | 构建发送优先级队列 | build_whatsapp_queue.mjs |
| 💬 **Messenger** 渲染师 | 渲染个性化消息（4 style × 变体） | render_whatsapp_messages.mjs |
| 📤 **Sender** 发送员 | 通过 WhatsApp 发送 | whatsapp_bulk_sender_cdp.mjs |

## 用法

```bash
node agent_orchestrator.mjs dual          # 跑双管道（推荐）
node agent_orchestrator.mjs joinf         # 只跑富通
node agent_orchestrator.mjs google-maps   # 只跑 Maps
node agent_orchestrator.mjs status        # 查看当前状态
node agent_orchestrator.mjs reset         # 重置状态
node agent_orchestrator.mjs resume send   # 从发送阶段续跑
node agent_orchestrator.mjs joinf --dry-run  # 预览模式
```

## 核心设计
- **状态管理**：`orchestrator_state.json` 持久化进度
- **检查点续跑**：`--resume <stage>` 从失败阶段恢复
- **并行执行**：analyst stage 两种来源并行增强
- **回滚点**：每个 stage 标记上游 stage，失败时告知回滚位置
- **错误追踪**：记录最近的 3 个错误到状态文件

## 文件位置
脚本: `%LOCALAPPDATA%/hermes/scripts/buyer-development/agent_orchestrator.mjs`

## Pitfalls
- 要求 Node.js 环境（已有）
- CDP 端口 9223（WhatsApp）/ 9226（富通）必须已打开
- `--dry-run` 不执行任何脚本，只打印将要执行的
- 回滚后需要手动修问题再 resume

## Related skills
- `ddg-linkedin-xray` — Scout 的第三线索源：不登录领英，通过 DuckDuckGo X-Ray 搜索批量获取客户 LinkedIn 资料
- `bliiot-email-marketing` — 邮件推广管道（替代 WhatsApp）
- `bliiot-customer-analysis` — 客户数据分析 + 产品匹配
