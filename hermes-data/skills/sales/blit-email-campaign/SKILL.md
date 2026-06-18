---
name: blit-email-campaign
category: sales
description: "BLIIOT email outreach campaign — filter CRM customers, send personalized emails via QQ SMTP, log follow-ups to local SQLite, sync to JoinF CRM. Supports random sampling, country filtering, and date-based segmentation."
version: 1.1.0
author: Tachikoma
---

# BLIIOT Email Campaign Skill

## Overview
Automated email outreach pipeline for BLIIOT — filter JoinF (富通) CRM customers by criteria → send personalized emails via QQ SMTP (kali_foever@qq.com) → log follow-up records to SQLite → optionally sync back to JoinF CRM.

## Prerequisites
- **CRM Data**: Full customer JSON exported from JoinF CRM (`all_customers_raw.json`)
- **Local DB**: `crm_followups.db` (SQLite with `customers` + `followups` tables) under `memories/脚本缓存/富通CRM/`
- **SMTP**: QQ personal email `kali_foever@qq.com`, authorization code stored at `memories/脚本缓存/产品推广/.smtp_password`
- **Scripts dir**: `skills/sales/blit-email-campaign/scripts/`

## Key Files
| File | Purpose |
|------|---------|
| `scripts/send_selected5.py` | Main campaign script — filter, random sample, send, log |
| `scripts/blit_mailer.py` | SMTP mail engine (smtplib, retry, HTML/attachment support) |
| *(external)* `memories/脚本缓存/富通CRM/bliiot_crm.py` | CRM tools — query customers, log follow-ups, sync to JoinF |

## Quick Start
```bash
cd skills/sales/blit-email-campaign/scripts
python send_selected5.py --count 5 --before 2024-01-01
```

Parameters:
| Flag | Default | Description |
|------|---------|-------------|
| `--count` | 5 | Number of customers to email |
| `--before` | 2024-01-01 | Filter: createDate < this date |
| `--country` | (all) | Filter: specific country code (e.g. ZA, NG) |

## Email Template (current)
```text
Subject: Partnership Inquiry - BLIIOT Technology

Greetings {name} and the {company} team,

Hope this message finds you well.

I'm reaching out from BLIIOT Technology based in Shenzhen, a professional
manufacturer of industrial IoT hardware with over 10 years of experience
empowering clients across energy, automation, and industrial communication.

I noticed {company} is involved in {industry} — a domain where reliable
and cost-effective hardware is critical.

We specialize in a comprehensive range of products designed for demanding
industrial environments:
• Industrial gateways and protocol converters
• ARM-based edge computing controllers
• Remote I/O modules and data acquisition devices
• Industrial 4G/5G routers
• IoT data terminal units

Our products are trusted by system integrators and industrial partners
in over 120 countries for their stability, flexibility, and competitive pricing.

Would you be open to a quick chat about how our solutions might support
your ongoing projects? I'm happy to share more details or product
documentation that aligns with your needs.

Looking forward to hearing from you.

Warm regards,
Kali
International Sales | BLIIOT Technology
Email: kalifoever@bliiot.com
Web: www.bliiot.com
```

## Script Behavior

`send_selected5.py` does:
1. Connects to SQLite DB (`crm_followups.db`)
2. Filters customers by `createDate < BEFORE_DATE` (optionally + country)
3. Randomly samples N from filtered set
4. Extracts email from each customer:
   - Tries `email` column first
   - Falls back to `contacts` JSON field (parse array, find `email` key)
5. Sends via QQ SMTP with 1-2.5 min random delay between sends (human-like pacing)
6. Logs each follow-up to `followups` table in SQLite
7. Returns summary table

### Email Extraction from CRM Customer
```python
def extract_email(customer):
    if customer.get("email"):
        return customer["email"].strip()
    contacts_raw = customer.get("contacts", "[]")
    if isinstance(contacts_raw, str):
        try:
            contacts = json.loads(contacts_raw)
            for c in contacts:
                if c.get("email"):
                    return c["email"].strip()
        except json.JSONDecodeError:
            pass
    return None
```

## Key Rules
1. **Human-like delays**: 60-150s random delay between sends — never burst
2. **No duplicate sending**: Check `followups` table before re-sending to same email
3. **CRM sync**: Every send → logged to SQLite; batch-sync to JoinF CRM after campaign
4. **SMTP auth code**: Stored at `memories/脚本缓存/产品推广/.smtp_password`, never commit to git
5. **QQ rate limits**: ~50 sends/day max for personal QQ; space campaigns accordingly
6. **Timezone awareness**: Consider recipient's business hours when scheduling

## Full Pipeline (first-time setup)

### Step 1: Export CRM Data
Connect via CDP to Chrome with JoinF CRM logged in:
```bash
"/c/Program Files/Google/Chrome/Application/chrome.exe" \
  --remote-debugging-port=9226 \
  --user-data-dir="C:/Users/Admin/AppData/Local/Google/Chrome/User Data/Profile 2"
```
Navigate to https://trade.joinf.com → login → extract auth (cookie, xCid=71376, xUser=183006 from localStorage).
Call API with pagination (size=200 per page, works reliably).

See `sales/joinf-crm-api` skill for full API details.

### Step 2: Initialize SQLite Database
```bash
python "memories/脚本缓存/富通CRM/bliiot_crm.py"
```
Creates `crm_followups.db` and imports all customers from JSON.

### Step 3: Test SMTP
```bash
cd skills/sales/blit-email-campaign/scripts
python -c "from blit_mailer import test_connection; ok,msg=test_connection(); print('OK' if ok else 'FAIL:', msg)"
```

### Step 4: Run Campaign
```bash
python send_selected5.py --count 5 --before 2024-01-01
```

### Step 5: Verify & Sync
```bash
# Check sent records
sqlite3 "memories/脚本缓存/富通CRM/crm_followups.db" \
  "SELECT * FROM followups WHERE type='email' ORDER BY created_at DESC LIMIT 5;"

# Sync to JoinF CRM
python "memories/脚本缓存/富通CRM/bliiot_crm.py" --sync-followups
```

## Troubleshooting

| Issue | Fix |
|-------|-----|
| SMTP auth failed | Re-extract QQ authorization code from QQ mail → Settings → Account |
| CDP connection refused | Restart Chrome with `--remote-debugging-port=9226` |
| "No customers matched" | Check the `createDate` format in crm_followups.db (could be `null` for old records) |
| Proxy blocking SMTP | Add `os.environ['NO_PROXY']='*'` before SMTP call, or disable Vortex proxy |