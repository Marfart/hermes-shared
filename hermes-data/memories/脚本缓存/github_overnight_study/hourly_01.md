# 第1轮｜B2B获客漏斗中的CRM线索捕获与同意管理

- 实际研究时段：2026-10-21 约11:40–11:44（北京时间），不足一小时；不把失败的后台等待时间计作研究。
- 方向：只研究客户开发/获客。此前 Node-RED 设备运行时研究是范围误解，本报告不把它计入成果。
- 项目：`espocrm/espocrm`，公开上游克隆到独立目录 `Desktop/Working/GitHub_Overnight_Study/espocrm`。浅克隆 HEAD `6526c05`，提交时间 `2026-10-20T21:25:13+03:00`（依赖更新）。
- 许可与运行要求：仓库 `composer.json` 标为 `AGPL-3.0-or-later`；README 要求 PHP 8.3–8.5、MySQL 8+/MariaDB 10.6+ 或 PostgreSQL 15+。如果作为网络服务部署并修改，需由法务/许可证负责人复核 AGPL 义务；本轮未部署。

## 实读源码与设计原因
1. `application/Espo/Modules/Crm/Resources/metadata/entityDefs/Lead.json`：线索实体含阶段 `New → Assigned → In Process → Converted/Recycled/Dead`、来源、行业、网站等字段；邮箱/电话/地址/name 明确标注 personal data，`doNotCall` 有审计。这样把销售过程与敏感联系人字段放在同一数据模型，但需要权限、保留和抑制规则治理。
2. `application/Espo/Modules/Crm/Resources/metadata/scopes/Lead.json`：允许 ACL、导入及 Stream；重复检查字段配置为 name/emailAddress。为客户名单导入与操作留有入口，但不代表可直接导入真实名单；需先做 CRM 对账和用户权限控制。
3. `application/Espo/Tools/LeadCapture/Api/PostForm.php` 与 `CaptureService.php`：公开表单 API 把表单ID、解析后的提交体和 `X-Captcha-Token` 交给捕获服务；启用验证码时先校验，再按表单配置筛选/净化字段。设计意图是将网站入站表单限制为显式允许字段并降低垃圾提交。
4. `CaptureService.php`（`capture`、`findLeadDuplicates`、`confirmOptIn`）：线索捕获可配置重复检查，按邮箱或电话找既有 Lead/Contact；可记录重复提交而非盲目新建；双重确认路径创建有到期时间的 token，确认后处理并标记 `isProcessed`，避免同一 token 重复入库。
5. `ConfirmationSender.php` 与 `Jobs/OptInConfirmation.php`：确认邮件由后台 Job 发送，依赖指定模板与 SMTP 帐户；说明客户同意流程和发送可靠性依赖后台队列与邮件配置，不是提交表单即代表已同意营销。
6. `tests/integration/Espo/LeadCapture/LeadCaptureTest.php`：集成测试验证表单捕获会创建 Lead、写入来源、关联团队与目标名单。

## 实测与限制
- 原创静态验证脚本：`espocrm_lead_capture_probe.py`；断言许可标记、线索阶段、PII 标记、重复字段、验证码/API调用及双重确认链路，结果 **8/8 PASS**。
- 未运行 PHP/PHPUnit 集成测试：当前终端没有 `php`（`php: command not found`）。依照任务边界，没有安装 PHP 或其他系统组件；因此不能声称项目运行测试通过。
- `git status --short` 空，克隆上游无改动。

## 对 BLIIOT 客户开发的价值与边界
- 有用部分：适合研究“官网询盘进入CRM→字段验证/验证码→重复线索识别→销售阶段→授权后邮件确认”的入站获客闭环；Lead 有行业、来源、网站等字段，可支持后续筛选。
- 不足部分：它不是公开公司发现或外部 B2B 名录抓取工具，也不自动证明某家公司需要 BLIIOT；用户的外呼名单、官网证据画像、产品匹配评分还需独立流程。
- 隐私/合规边界：本项目把 email/phone/name 标为个人数据，并提供 doNotCall 与 opt-in 处理概念；实际采用时需保留来源/同意/退订证据，且不能将导入的联系人自动当成营销许可。
- 未触碰 Joinf 或任何真实 CRM/客户数据；未发送邮件、WhatsApp；未在外部或公司环境部署。

## 自动汇报状态
8轮小时自动任务的手动触发失败：`HTTP 404: No endpoints found for owl-alpha`，所以后台第1轮没有执行；为避免后续空跑已暂停。当前这份是我在当前会话亲自完成的短时研究记录（不足一小时）。在不更改 Hermes 模型配置的任务边界下，自动小时报告尚无法恢复。

## 下一步
继续评估一个真正面向公开公司网站研究/证据化画像的开源项目，再比较 Twenty CRM/n8n 的线索导入、去重与跟进能力；先核许可证/维护，再读源码并做隔离验证。
