---
name: bliiot-sales-pipeline
description: "BLIIOT 销售管道全流程 — 从LinkedIn客户发现、B2B目录推广、WhatsApp开发信、富通CRM跟进、邮件营销到报价单生成的完整销售工作流。覆盖BLIIOT工业物联网产品销售的所有客户接触点和转化流程。"
version: 2.1.0
author: Kali / Tachikoma
tags: [bliiot, sales, crm, whatsapp, email-marketing, linkedin, customer-acquisition, quotation, b2b]
triggers:
  - "销售"
  - "客户开发"
  - "开发信"
  - "CRM跟进"
  - "报价"
  - "邮件营销"
  - "WhatsApp"
  - "LinkedIn"
  - "B2B推广"
  - "客户分析"
  - "sales pipeline"
---

# BLIIOT 销售管道全流程

> 从客户发现到成交的完整销售工作流。每个阶段有对应的详细子技能。

## 销售管道总览

```
潜在客户发现 → 客户分析/资质评分 → 开发信触达 → CRM跟进 → 技术调研 → 报价 → 成交
     ↓               ↓                ↓            ↓           ↓         ↓
  B2B目录/公开官网   邮件（默认）       CRM/邮件/跟进
```

## 阶段 1: 潜在客户发现

### 范围与渠道默认值
“客户开发/开发客户”指获客、潜客研究和销售流程，不是开发硬件、网关、固件或工业设备。对Kali默认优先B2B目录与公开公司官网研究，Email优先；她不使用LinkedIn，且认为WhatsApp批量外联封号风险高。不得自行把LinkedIn/X-Ray或WhatsApp发送设为默认渠道；只有Kali在当前任务明确要求时，才启用相应专门流程。

### LinkedIn X-Ray 搜索（本用户默认不使用）
仅作为其他用户或Kali当前明确授权时的可选方法，不得因旧流程文档而默认运行。
- 详见 `references/linkedin-xray.md`
- 输入: 行业关键词 + 地区
- 输出: 经来源核验的公开公司/联系人资料；不猜测个人或公司主页

### B2B 目录推广
向全球B2B贸易目录提交公司信息，让买家主动找到BLIIOT。
- 详见 `references/b2b-directory.md`
- 不碰社交平台，纯B2B渠道

### 批量潜客名单（Excel）
用户要求批量开发客户时，按 `references/lead-enrichment.md` 执行。名单至少包含公司名、公司领域方向、国家/地区、官网、公开联系邮箱（有则填）、信息来源与核验状态；不要求LinkedIn字段，除非用户当前明确要求。严格按用户要求的行数去重并回读验证。行业推断必须有依据，不足时标“待核实”；CRM公海池筛选结果不能说成全新网络发现或逐家已核验。用户只要求保存到桌面时，保存在指定文件名，不把含CRM联系人信息的文件上传到外部托管服务，除非用户明确授权。

## 阶段 2: 客户分析与资质评分

### 客户数据增强 (Lead Enrichment)
从用户当前授权的公开来源发现的公司数据中增强（优先官网、公开业务信息和可核验联系方式；不得默认使用LinkedIn）。
- 详见 `references/lead-enrichment.md`

### B2B 客户评分与产品匹配
分析客户数据，匹配BLIIOT产品，输出评分结果。
- 详见 `references/customer-scoring.md`

## 阶段 3: 开发信触达

### WhatsApp 自动发送开发信（仅当前明确授权时）
Kali默认不采用WhatsApp批量外联，Email优先；只有她在当前任务明确要求发送WhatsApp时，才加载专门流程并遵循去重、发送节奏和首条审阅要求。
- 详见 `references/whatsapp-auto-sender.md`
- 支持按行业/地区/公司规模定制

### 邮件营销 (Email Campaign)
通过QQ邮箱SMTP发送产品推广邮件，替代WhatsApp（防封号）。
- 详见 `references/email-marketing.md`
- 支持HTML邮件、附件、追踪
- Hermes自带MCP、插件、Cron和`--format stream-json`等编排能力，但不是完整的营销群发平台
- 推荐分工：Hermes负责客户筛选、去重查询、个性化草稿和发送队列；现有`bliit_mailer.py`负责SMTP发送、限速、去重日志与结果记录

## 阶段 4: CRM 跟进

### 富通CRM API 操作
直接HTTP调用富通CRM API，包括新增客户、修改资料、添加跟进。
- 详见 `references/joinf-crm-api.md`
- 认证: appKey + appSecret

### WhatsApp → 富通CRM 管道
从WhatsApp Web读取客户消息，提取联系人，查询/新增CRM跟进。
- 详见 `references/whatsapp-to-crm.md`
- 三字段匹配: contactName / linkman / company

### CRM 跟进记录工具
本地SQLite + 富通API双向同步，支持一键添加跟进、查客户。
- 详见 `references/crm-followup.md`

## 阶段 5: 技术调研与选型

详见 `bliiot-product-knowledge` 技能（产品知识库）。

## 阶段 6: 报价

详见 `bliiot-quotation` 技能（报价单生成全流程）。

## 多角色 Agent 编排

使用CrewAI/LangGraph风格的角色分离+状态机模式：
- 详见 `references/agent-orchestrator.md`
- 角色: 客户开发、技术调研、报价、跟进

## 铁律

1. **相关性与拒收控制** — 只向公开业务信息显示高度相关的B2B联系人发送；潜在需求必须标为推断，不得写成已确认需求；排除无效、退订和拒收联系人
2. **渠道选择与拒收控制** — 默认Email优先，不主动启用LinkedIn或WhatsApp批量外联；只有用户在当前任务明确指定时才进入对应发送流程。获授权发送时仍须去重、遵守发送节奏，并排除无效、退订和拒收联系人
3. **CRM数据一致性** — 每次交互后同步到CRM
4. **报价前必须核对原始价格文件** — 数据库价格可能与实际不符
5. **客户信息保密** — 不泄露客户数据给第三方
6. **首次试跑先审后发** — 新名单/市场/模板先处理1条；核验客户官网、产品匹配、CRM活动与适用发送日志；展示收件人核验状态和草稿。CRM与官网字段冲突时标记，不擅自覆盖；用户明确确认该收件人与正文后才发送
7. **潜客名单来源与完整性** — 标明CRM池、历史增强数据或实时公开来源；不把未验证邮箱说成可达，不猜LinkedIn公司页，不把个人主页填作公司主页。生成Excel后重新读取文件，核实指定行数、公司去重、邮箱去重及链接字段数量，再报告缺失/待核验比例

## 关联技能

- `bliiot-product-knowledge` — 产品知识库（选型、规格、协议）
- `bliiot-quotation` — 报价单生成
- `humanizer` — 让AI生成的开发信更像人写的
