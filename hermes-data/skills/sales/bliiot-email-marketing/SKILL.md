---
name: bliiot-email-marketing
description: "BLIIOT Email营销 — 安全可靠的SMTP邮件推广，替代WhatsApp（防封号）。通过QQ邮箱发产品开发信，支持CRM老客户召回+多模板+防SPAM延迟+发送队列+日志回查"
version: 2.0.0
author: Tachikoma
platforms: [windows]
trigger: "发邮件/邮件营销/发开发信/WhatsApp怕封/CRM老客户召回/旧客户跟进/邮件召回/quali 说Email可以/邮件推广/安全渠道推广/不想被封号"
tags: [email, marketing, smtp, outreach, sales, b2b, crm-recall]
related_skills: [whatsapp-auto-sender, bliiot-b2b-directory-promotion, bliiot-crm-followup]
---

# BLIIOT Email Marketing Engine

## Overview

Email is the **safest outreach channel** — no ban risk, professional B2B standard.

### Current SMTP Configuration

| Item | Value |
|------|-------|
| **Channel** | ⭐ QQ个人邮箱（当前主力，2026-06-18启用） |
| **SMTP** | `smtp.qq.com:465` SSL |
| **Sender** | `kali_foever@qq.com` |
| **Display Name** | `Kali \| BLIIOT Technology` |
| **Auth** | 授权码已保存在 `.smtp_password` |
| **Contact in body** | Email: `bl42@bliiot.com`, WhatsApp: `+86 17704014518` |

| Backup Channel | SMTP | Sender | Status |
|----------------|------|--------|--------|
| QQ Enterprise Mail | `smtp.exmail.qq.com:465` | `bl42@bliiot.com` | ⏳ 授权码待获取 |

### When to Use Email

- ✅ WhatsApp ban risk is a concern (Kali's explicit preference — 安全第一)
- ✅ CRM已有邮箱的老客户召回（2024年前客户有1600+有邮箱）
- ✅ B2B professional standard in Europe, Americas, Oceania
- ✅ Scalable daily up to 50/day with proper delays
- ❌ NOT for urgent/time-sensitive commercial offers
- ❌ NOT when you need real-time back-and-forth

## Scripts

| Script | Path | Purpose |
|--------|------|---------|
| `bliit_mailer.py` | `memories/脚本缓存/产品推广/bliit_mailer.py` | 主力邮件引擎（多模板HTML+文本） |
| `send_selected5.py` | `memories/脚本缓存/产品推广/send_selected5.py` | **CRM老客户召回** — 选客户→发邮件→记跟进 |

## Workflow A: CRM 老客户召回（本会话的实战方法）

### Step 1: 从CRM选取目标客户

```bash
python -c "
import json, random
from datetime import datetime, timezone, timedelta

with open(r'CRM客户数据路径/all_customers_raw.json') as f:
    customers = json.load(f)

# 过滤：2024年前创建 + 有邮箱
cutoff = int(datetime(2024,1,1,tzinfo=timezone(timedelta(hours=8))).timestamp() * 1000)
old = [c for c in customers if c.get('displayCreateTime') and c['displayCreateTime'] < cutoff and c.get('contactEmail')]

# 随机抽取N个
selected = random.sample(old, 5)

# 保存为JSON
with open('产品推广/_selected5.json', 'w') as f:
    json.dump(selected, f, ensure_ascii=False, indent=2)

# 打印预览
for c in selected:
    print(f'{c.get(\"name\",\"\")} | {c.get(\"contactEmail\",\"\")} | {c.get(\"displayRegion\",\"\")}')
"
```

### Step 2: 发送邮件（拟人模式）

```bash
cd memories/脚本缓存/产品推广
python send_selected5.py
```

脚本自动：
- 读取 `_selected5.json` 中的客户
- 用QQ邮箱 `kali_foever@qq.com` 发送
- **拟人延迟**: 每封之间 60-150s 随机间隔
- 写入CRM跟进记录到本地SQLite

### Step 3: 检查结果

```bash
# 查看CRM跟进记录（最近1小时内的邮件记录）
python -c "
import sqlite3
conn = sqlite3.connect('crm_followups.db')
rows = conn.execute('''SELECT id, customer_id, type, content, created_at
    FROM followups WHERE source=\"email\"
    AND created_at >= datetime(\"now\", \"-1 hour\")
    ORDER BY id DESC''').fetchall()
for r in rows:
    print(f'  #{r[0]} | cust={r[1]} | [{r[2]}] | {r[3][:60]}... | {r[4]}')
conn.close()
"
```

## Workflow B: 批量模板邮件（bliit_mailer.py）

```bash
cd memories/脚本缓存/产品推广

# 1. Set password
python bliit_mailer.py --set-password

# 2. Preview
python bliit_mailer.py --dry-run

# 3. Send
python bliit_mailer.py --send
```

## 邮件模板

### CRM老客户召回模板（本会话实战验证）

**Subject**: `Following up | BLIIOT Industrial IoT Solutions`

**Body**:
```
Hi {first_name},

Hope this email finds you well.

I hope you don't mind me reaching out. I'm Kali from BLIIOT (www.bliiot.com)— we previously discussed our industrial IoT gateways and remote monitoring solutions, which are widely used in solar energy, building automation, transformer monitoring, and industrial control applications.

I was wondering if you still remember us, and whether you're still interested in our products? Do you have any upcoming projects where our solutions might be a good fit?

We've also released several new products recently. If you'd like to learn more, please feel free to reach out anytime.

You can contact me directly at
Email: bl42@bliiot.com
WhatsApp: +86 17704014518.

Looking forward to hearing from you.

Best regards,
Kali
BLIIOT
```

**Design rationale**: This template is intentionally:
- **Soft-touch**: "I hope you don't mind me reaching out" + "I was wondering if you still remember us" — not aggressive sales
- **Non-spammy**: No bold, no large fonts, no multiple exclamation marks
- **Personal**: Uses customer's first name, references past discussions
- **Low-commitment CTA**: "If you'd like to learn more, feel free to reach out anytime" — no pressure
- **Multiple contact options**: Both email and WhatsApp in the footer

### 产品模板（bliit_mailer.py）
- ARMxy嵌入式控制器
- 工业物联网网关
- R40工业路由器
- 全产品综合

## Anti-SPAM Parameters

| Parameter | CRM召回模式 | 批量模板模式 |
|-----------|------------|-------------|
| Delay between emails | 60-150s | 45-90s |
| Batch size before rest | 5 | 5 |
| Rest duration | 10 min | 3-5 min |
| Daily cap | 50 | 50 |

## CRM Integration

After sending each email, a follow-up record is **automatically written** to the local CRM SQLite database:

```
Table: followups
Fields: customer_id, type='邮件', content='发送了跟进邮件给{name}({email})', 
        operator='Kali Marfa', source='email', synced=1
```

No CDP needed for CRM write — it's a direct SQLite INSERT. Records marked `synced=1` won't be re-synced to JoinF (they're already there as a manual record).

## Pitfalls

- ⚠️ **授权码 ≠ 登录密码**。QQ邮箱的授权码获取：登录QQ邮箱 → 设置 → 账户 → 「POP3/SMTP服务」→ 开启 → 短信验证 → 获取16位授权码
- ⚠️ **Kali已配置好`kali_foever@qq.com`的授权码** `reoefbstemklbdcd`，保存在 `.smtp_password`
- ⚠️ 本轮会话实战已发送5封CRM老客户邮件（Juan Carlos/Stephen Hudson/Richard Twite/Basem Mohamed/Alex Elliot），标记好已发送名单避免重复
- ⚠️ 不要硬编码密码到Python脚本中。永远从 `.smtp_password` 文件读取
- ⚠️ `.sent_log.json` 记录已发送历史。重置需 `--reset-log`
- ⚠️ 选客户时要随机抽样，不要每次都选同样的客户
- ⚠️ 2024年前客户有1600+有邮箱的，足够多发几轮

## See Also

- `whatsapp-auto-sender` — WhatsApp channel（风险：封号）
- `bliiot-crm-followup` — CRM跟进记录工具（邮件记录自动写入这里）
- `bliiot-b2b-directory-promotion` — B2B目录推广（风险：无）