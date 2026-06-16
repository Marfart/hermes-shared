---
name: bliiot-email-marketing
description: "BLIIOT Email营销 — 安全可靠的SMTP邮件推广，替代WhatsApp（防封号）。通过QQ企业邮发产品开发信，支持多模板+防SPAM延迟+发送队列+日志回查"
version: 1.0.0
author: Tachikoma
platforms: [windows]
trigger: "用户说Email可以/邮件营销/发邮件推广/安全渠道推广/不想被封号/WhatsApp怕封选邮件"
metadata:
  hermes:
    tags: [email, marketing, smtp, outreach, sales, b2b]
    related_skills: [whatsapp-auto-sender, bliiot-b2b-directory-promotion]
---

# BLIIOT Email Marketing Engine

## Overview

Email is the **safest outreach channel** — no ban risk, no rate-limiting from platforms, professional B2B standard. The Python SMTP engine connects through QQ Enterprise Mail (腾讯企业邮, `smtp.exmail.qq.com`) using `bl42@bliiot.com`.

This is the **recommended channel** for markets where WhatsApp might get flagged. Use email when:
- WhatsApp ban risk is a concern (Kali's explicit preference)
- Targeting regions where email is the professional standard (Europe, Americas)
- Need to reach contacts where only email is available
- Want scalable outreach without daily send limits (within reason)

## Script Location

```
C:\Users\Admin\AppData\Local\hermes\memories\脚本缓存\产品推广\bliit_mailer.py
```

## Quick Start

```bash
cd "C:\Users\Admin\AppData\Local\hermes\memories\脚本缓存\产品推广"

# 1. Set QQ Enterprise Mail SMTP authorization code (first time only)
python bliit_mailer.py --set-password

# 2. Test that SMTP works
python bliit_mailer.py --test

# 3. See all customer emails ready to send
python bliit_mailer.py --list

# 4. Preview who gets what (dry run)
python bliit_mailer.py --dry-run

# 5. Send!
python bliit_mailer.py --send
```

## Features

| Feature | Detail |
|---------|--------|
| **SMTP Channel** | QQ Enterprise Mail (smtp.exmail.qq.com:465 SSL) |
| **Sender** | bl42@bliiot.com — BLIIOT official email |
| **Templates** | 3 product-focused HTML templates (ARMxy, IoT Gateways, R40 Router) |
| **Anti-SPAM** | 45-90s random delay between emails, 3-5min rest every 5 emails |
| **Daily Cap** | 50 emails/day (configurable) |
| **Deduplication** | Auto-skips already-sent emails via .sent_log.json |
| **Crash Recovery** | Log saved after each send — resume from where it left off |
| **Data Source** | Auto-scans buyer-development `*followup*.json` files for emails |

## Anti-SPAM Safety Measures

These are critical for deliverability — Gmail/Outlook will flag bulk sends without them:

1. **Ramp-up**: Start with 10/day, increase gradually. Don't blast all 31 at once.
2. **Delay**: Every email has 45-90s random gap between sends
3. **Batch rest**: Every 5 emails = 3-5 minute pause
4. **Random templates**: Each email picks a random product template (not all same)
5. **HTML + Text**: Multipart MIME with both HTML and plaintext fallback
6. **Unsubscribe**: Footer includes "Reply Unsubscribe to opt out"
7. **Daily cap**: Hard limit of 50/day

## Data Source

Script auto-discovers customer emails from:

```
C:\Users\Admin\AppData\Local\hermes\memories\buyer-development\
  *followup*.json
```

Current count: ~31 valid emails across 9 countries.

## Adding More Emails

To add more email targets:
1. Get new customer data (Google Maps, JoinF, etc.)
2. Enrich and build followup document (see `bliiot-customer-acquisition` pipeline)
3. The mailer script auto-discovers new `*followup*.json` files
4. Run `--list` to verify new emails appeared
5. Run `--send` to send

## Manager Commands

```bash
python bliit_mailer.py --set-password   # Set/update SMTP auth code
python bliit_mailer.py --status         # Show stats + unsent list
python bliit_mailer.py --list           # List all email targets
python bliit_mailer.py --send           # Execute sending
python bliit_mailer.py --dry-run        # Preview without sending
python bliit_mailer.py --test           # Test to self
python bliit_mailer.py --reset-log      # Reset sent history
```

## Pitfalls

- ⚠️ **QQ Enterprise Mail requires an "authorization code" (授权码)**, not the login password. Generate it at: QQ邮箱 → 设置 → 账户 → POP3/SMTP服务 → 生成授权码
- ⚠️ First time setup requires interactive password entry via `--set-password`. Password stored in plaintext at `.smtp_password` in the script directory.
- ⚠️ Daily cap is 50 — if you hit the limit, run again the next day
- ⚠️ Some emails in the followup JSON are garbage (image filenames, garbled text) — the script auto-filters these
- ⚠️ Do NOT set delay to 0. That will trigger Gmail SPAM filters immediately
- ⚠️ `.sent_log.json` tracks what's been sent — if you need to resend, run `--reset-log` first

## See Also

- `whatsapp-auto-sender` — WhatsApp channel (risk: ban)
- `bliiot-b2b-directory-promotion` — Inbound B2B directory listings (risk: none)