---
name: system-devops
description: "系统运维自动化 — Windows桌面监控、自维护健康检查、代理诊断、看板编排、韧性架构、Webhook订阅。覆盖Hermes Agent自身维护和Windows系统监控的完整工具集。"
version: 2.0.0
author: Hermes Agent (Kali)
tags: [devops, self-maintenance, watchdog, proxy, kanban, resilience, webhook, windows, monitoring]
triggers:
  - "自维护"
  - "健康检查"
  - "桌面监控"
  - "代理诊断"
  - "看板"
  - "韧性"
  - "webhook"
  - "system maintenance"
---

# 系统运维自动化

> Hermes Agent自身维护 + Windows系统监控的完整运维工具集。

## 自维护 (Self-Maintenance)

完整的Agent自维护工作流，设计为cron驱动:

### Phase 1: 版本与更新检查
```bash
hermes --version
hermes doctor
hermes doctor --fix
git fetch origin && git log --oneline HEAD..origin/main
git pull --ff-only
```

### Phase 2: 技能与工具审计
```bash
hermes skills list
hermes skills check
hermes tools list
hermes config check
```

### Phase 3: 自主趋势学习
- 多搜索引擎策略: ddgs → web_search → browser
- 本地库存对比
- 记录到memory或文件

### Phase 4: 主动改进
- 代码更新、技能补丁、memory更新
- 配置检查
- 外部工具更新 (cua-driver等)

### Phase 5: 模型健康与回退监控
- 主模型: ollama-cloud/deepseek-v4-flash
- 回退: ollama-cloud/glm-5.1
- 自动回退脚本: model_fallback_monitor.py
- 提供商模型存活性验证: see `references/provider-model-verification.md`

### Phase 6: 网关进程健康 — 多层看门狗
- Layer 1: Windows Task Scheduler (独立于Hermes)
- Layer 2: Hermes cron脚本 (运行在网关内)
- Layer 3: 网关内部重试逻辑

### Phase 7: 跨目录备份同步
- 实时: watchdog-based live sync
- 定时: cron-based md5 incremental sync
- 排除: state.db, logs/, cache/, sessions/

### 关键陷阱
1. **子Agent新闻造假** — 永远不要委托子Agent做新闻研究
2. **Windows CRLF噪音** — git pull前检查 `git diff -w --stat`
3. **版本检测混乱** — 先git fetch再检查commit差
4. **Cron环境限制** — 用纯Python脚本，不用bash→PowerShell桥接
5. **Discord资源陷阱** — 不用就禁用，每天浪费13.5分钟

## 桌面监控 (Desktop Watchdog)

检测7种事件类型:
1. 系统重启
2. 新用户登录
3. 屏幕解锁
4. USB存储设备插入
5. RDP远程桌面
6. 远程软件运行 (TeamViewer/AnyDesk/向日葵等)
7. 系统从睡眠唤醒

### 架构
- 纯Python (不用bash→PowerShell桥接)
- cron每2分钟执行
- guard_state.json状态文件
- 通过配置的渠道(WeChat/Telegram)报警

### 布防/撤防
- "我走了" → arm
- "我来了" → disarm
- 3分钟空闲确认 (防止误触发)

## 代理诊断 (Proxy API Diagnostics)

诊断系统HTTP代理(Vortex/Clash/V2Ray)导致的API连接问题。

### 诊断流程
1. 检查代理路由日志
2. 对比代理vs直连
3. 检查代理配置结构
4. 添加DIRECT规则
5. 重启代理服务
6. 验证修复

### 最常见原因
- `mode: direct` 会静默禁用所有代理路由
- DNS污染 (GFW)
- fake-ip DNS破坏DIRECT连接

## 关联技能

- `hermes-agent` — Hermes配置与扩展
- `systematic-debugging` — 系统性调试方法论
- `windows-security-audit` — Windows安全审计
