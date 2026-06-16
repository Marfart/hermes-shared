# BLIIOT Multi-Agent Orchestrator

## 创建时间：2026-06-04
## 文件位置：`%LOCALAPPDATA%/hermes/scripts/buyer-development/agent_orchestrator.mjs`

## 概述
受 CrewAI 角色分离 + LangGraph 状态机启发，将扁平的客户开发管道拆分为 6 个专业 Agent，每个有独立 role 和 goal。

## 6 个 Agent 角色

| 角色 | 职责 | 执行脚本 |
|:----|:-----|:---------|
| 🕵️ **Scout** 侦查员 | 搜索客户线索 | `fetch_joinf_business_search.mjs` / `scrape_google_maps_fresh_seeds.mjs` |
| 📊 **Analyst** 分析员 | 增强数据 + 产品匹配评分 | `enrich_joinf_business_search.mjs` / `enrich_google_maps_leads.mjs` |
| 📋 **Followup** 跟进文檔 | 生成客户跟进文档 | `build_followup_document.mjs` |
| 📝 **Queue** 队列员 | 构建发送优先级队列 | `build_whatsapp_queue.mjs` |
| 💬 **Messenger** 渲染师 | 渲染个性化消息 | `render_whatsapp_messages.mjs` |
| 📤 **Sender** 发送员 | 通过 WhatsApp 发送 | `whatsapp_bulk_sender_cdp.mjs` |

## 核心命令

```bash
# 双管道（富通 + Maps 并行，推荐）
node agent_orchestrator.mjs dual

# 单管道
node agent_orchestrator.mjs joinf
node agent_orchestrator.mjs google-maps

# 状态管理
node agent_orchestrator.mjs status    # 查看当前进度
node agent_orchestrator.mjs reset     # 重置状态
node agent_orchestrator.mjs resume send  # 从发送阶段断点续跑

# 预览模式
node agent_orchestrator.mjs dual --dry-run
```

## 设计要点
- **状态持久化**：`orchestrator_state.json` 保存进度，支持断点续跑
- **并行分析**：analyst stage 两种来源并行增强（joinf + maps）
- **回滚点**：每个 stage 标记上游 stage，失败时告知回滚位置
- **错误追踪**：记录最近的错误到状态文件

## 技能
完整的技能定义在 `skills/sales/bliiot-agent-orchestrator/SKILL.md`
