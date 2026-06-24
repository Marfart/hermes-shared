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
