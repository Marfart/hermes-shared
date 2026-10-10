# Email Marketing 邮件营销

## SMTP 配置
- **主力**: QQ个人邮箱 `kali_foever@qq.com`
- **SMTP**: `smtp.qq.com:465` SSL
- **Display Name**: `Kali | BLIIOT Technology`
- **Auth**: 授权码保存在 `.smtp_password`
- **Contact in body**: Email: `bl42@bliiot.com`, WhatsApp: `+86 17704014518`

## 脚本
- `bliit_mailer.py` — 主力邮件引擎（多模板HTML+文本）
- `send_selected5.py` — CRM老客户召回

## 工作流 A: CRM老客户召回
1. 从CRM选目标客户 (2024年前 + 有邮箱)
2. 拟人模式发送 (60-150s随机间隔)
3. 写CRM跟进记录到本地SQLite

## 防重复发送（零容忍）
1. 先确认当前发送脚本使用哪份发送日志（如 `.sent_log.json` 或 `.sent_log_v4.json`）；不同脚本的日志不一定互相覆盖，不能假设查一份就包含全部历史
2. 发送前按客户ID、邮箱、公司名/联系人查 CRM，并检查“最近活动”和所有适用的发送日志
3. CRM“最近活动”为空只表示该字段没有记录，不能单独证明从未联系
4. 每封发送成功后，立即按原格式写回当前 campaign 的发送日志
5. 不能依赖子进程stdout；按当前脚本的可靠执行方式运行，并以发送日志/CRM回读确认结果

## 筛选条件
- 只发2024年前老客户
- 有邮箱
- 未发过邮件或WhatsApp

## Anti-SPAM参数
- 邮件间隔: 60-150s
- 每批5封后休息10min
- 日上限50封

## 邮件模板
Subject: `Following up | BLIIOT Industrial IoT Solutions`
风格: soft-touch, 非spammy, 个人化, 低压力CTA

## Hermes 集成方案（学习整理）

### 能力边界
- Hermes CLI 已内置 Cron、MCP 客户端、插件机制和 `--format stream-json` 结构化输出；这些能力可编排工作流，但不等于内置营销活动/批量邮件管理器。
- Hermes Email Gateway/Himalaya 适合收件箱读取、搜索和邮件线程回复；不替代本流程的 SMTP 群发引擎。
- CRM（Joinf）连接、群发策略、发送状态/退订/抑制名单和批次管理，需要由现有脚本或单独的 MCP Server/插件提供。

### 推荐工作流
1. 先读取客户来源与字段，再用客户官网/可靠公开资料确认公司业务；同时依据BLIIOT官网和规格书核对产品能力，无法确认的联系人或需求留空，不编造。
2. 通过只读 CRM/MCP 按客户ID、邮箱、公司名/联系人查重；检查CRM最近活动及当前 campaign 对应的全部发送日志。官网联系邮箱与CRM邮箱冲突时，保留并展示两者及来源，不静默替换CRM地址。
3. 新名单、市场或模板先做单客户试跑：展示CRM记录、公开业务证据、产品匹配理由、邮箱核验差异和个性化草稿；CRM空白活动不能当作未触达证明。首次试跑只生成草稿，用户明确批准具体收件人和正文后才发。
4. Hermes为审核后的客户生成结构化队列；需要脚本消费时先验证本机CLI的 `--format stream-json`，不可仅依据发布说明推定本机支持。
5. 现有 `bliit_mailer.py` 保持为唯一SMTP发送器；发送前检查该campaign的发送日志，每封成功后立即写回，保留每日50封上限与当前节奏控制，不让Hermes直连SMTP绕过约束。
6. 发送结果再进入CRM；失败、退信、拒收和退订地址写入抑制名单。Windows端先完成小批次端到端验证（预览→审批→发送→日志→CRM回读），未经验证，不交给无人值守Cron。

### 集成实现选择
- **首选**：用现有 `bliit_mailer.py` 发送，Hermes输出通过JSON/JSONL队列交接，保留现有SMTP凭据与去重机制。
- **后续可选**：做一个最小MCP Server/插件，只暴露“查CRM/查重/生成草稿/提交已审批队列/写发送结果”等窄工具；凭据放环境变量，默认先只读，发送操作必须有显式队列与硬上限。
- **不要误用**：新增Email Gateway或AgentMail接入不是批量营销功能，也不应替换公司的发件域名/当前QQ SMTP配置。

### 验证与来源
- 发布说明：`https://github.com/NousResearch/hermes-agent/releases`
- Email Gateway：`https://hermes-agent.nousresearch.com/docs/user-guide/messaging/email/`
- MCP：`https://hermes-agent.nousresearch.com/docs/user-guide/features/mcp`
- 使用前在本机运行 `hermes --help` 或 `hermes chat --help` 验证具体CLI flag；发布说明不等于本机每个子命令已实测。
