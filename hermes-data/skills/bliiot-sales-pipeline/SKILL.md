---
name: bliiot-sales-pipeline
description: "BLIIOT 销售管道全流程 — 从LinkedIn客户发现、B2B目录推广、WhatsApp开发信、富通CRM跟进、邮件营销到报价单生成的完整销售工作流。覆盖BLIIOT工业物联网产品销售的所有客户接触点和转化流程。"
version: 2.0.0
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
  LinkedIn      B2B目录         WhatsApp      富通CRM    产品知识   报价单
  X-Ray        目录推广         邮件营销       API操作     选型指南   数据库
```

## 阶段 1: 潜在客户发现

### LinkedIn X-Ray 搜索
不登录LinkedIn，通过搜索引擎批量获取客户公开资料。
- 详见 `references/linkedin-xray.md`
- 输入: 行业关键词 + 地区
- 输出: 姓名/职位/公司/地点/LinkedIn URL

### B2B 目录推广
向全球B2B贸易目录提交公司信息，让买家主动找到BLIIOT。
- 详见 `references/b2b-directory.md`
- 不碰社交平台，纯B2B渠道

## 阶段 2: 客户分析与资质评分

### 客户数据增强 (Lead Enrichment)
从LinkedIn搜到的人/公司数据，批量增强（官网/邮箱/电话/CEO）。
- 详见 `references/lead-enrichment.md`

### B2B 客户评分与产品匹配
分析客户数据，匹配BLIIOT产品，输出评分结果。
- 详见 `references/customer-scoring.md`

## 阶段 3: 开发信触达

### WhatsApp 自动发送开发信
Selenium + WhatsApp Web，自动读Excel客户列表，批量发送个性化开发信。
- 详见 `references/whatsapp-auto-sender.md`
- 支持按行业/地区/公司规模定制

### 邮件营销 (Email Campaign)
通过QQ邮箱SMTP发送产品推广邮件，替代WhatsApp（防封号）。
- 详见 `references/email-marketing.md`
- 支持HTML邮件、附件、追踪

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

1. **不主动发垃圾邮件** — 只向明确有需求的客户发送
2. **WhatsApp防封号** — 控制发送频率，模拟人类操作节奏
3. **CRM数据一致性** — 每次交互后同步到CRM
4. **报价前必须核对原始价格文件** — 数据库价格可能与实际不符
5. **客户信息保密** — 不泄露客户数据给第三方

## 关联技能

- `bliiot-product-knowledge` — 产品知识库（选型、规格、协议）
- `bliiot-quotation` — 报价单生成
- `humanizer` — 让AI生成的开发信更像人写的
