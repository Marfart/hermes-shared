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
1. `.sent_log.json` 是唯一去重依据
2. 发一条保存一条
3. 不能依赖子进程stdout
4. 用execute_code内联执行

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
1. Hermes 从来源中发现并补全潜在客户，按地区、行业、公司类型和产品匹配度评分；缺失的联系人字段保持空白，不编造。
2. 通过只读 CRM/MCP 查询联系人姓名、公司名、邮箱等字段，做多字段查重；先从有效邮箱、业务相关客户和未触达名单构建待发送队列。
3. Hermes 为每个客户生成可审核的个性化邮件草稿（主题、正文、产品切入点和CTA），输出JSON/JSONL；需要脚本消费时优先验证本机CLI的 `--format stream-json`。
4. 现有 `bliit_mailer.py` 保持为唯一SMTP发送器；发送前检查 `sent_log`，每封成功后立即写日志，保留每日50封上限和当前节奏控制。不要让Hermes直连SMTP绕过这些约束。
5. 发送结果再进入CRM跟进记录；失败、退信、拒收和退订地址写入抑制名单，后续批次必须排除。
6. Windows上先做小批次端到端验证（预览→审批→发送→日志→CRM回写）；未经验证，不把批量发送交给无人值守Cron。

### 集成实现选择
- **首选**：用现有 `bliit_mailer.py` 发送，Hermes输出通过JSON/JSONL队列交接，保留现有SMTP凭据与去重机制。
- **后续可选**：做一个最小MCP Server/插件，只暴露“查CRM/查重/生成草稿/提交已审批队列/写发送结果”等窄工具；凭据放环境变量，默认先只读，发送操作必须有显式队列与硬上限。
- **不要误用**：新增Email Gateway或AgentMail接入不是批量营销功能，也不应替换公司的发件域名/当前QQ SMTP配置。

### 验证与来源
- 发布说明：`https://github.com/NousResearch/hermes-agent/releases`
- Email Gateway：`https://hermes-agent.nousresearch.com/docs/user-guide/messaging/email/`
- MCP：`https://hermes-agent.nousresearch.com/docs/user-guide/features/mcp`
- 使用前在本机运行 `hermes --help` 或 `hermes chat --help` 验证具体CLI flag；发布说明不等于本机每个子命令已实测。
