---
name: blit-email-campaign
category: sales
description: "BLIIOT email outreach campaign — filter CRM customers, send personalized emails via QQ SMTP, log follow-ups to local SQLite, sync to JoinF CRM. Supports random sampling, country filtering, and date-based segmentation."
version: 1.0.0
author: Tachikoma
---

# BLIIOT Email Campaign Skill

## Overview
Automated email outreach pipeline for BLIIOT — filter JoinF (富通) CRM customers by criteria → send personalized emails via QQ SMTP (kali_foever@qq.com) → log follow-up records to SQLite → optionally sync back to JoinF CRM.

## Prerequisites
- **CRM Data**: Full customer JSON exported from JoinF CRM (`all_customers_raw.json`)
- **Local DB**: `crm_followups.db` (SQLite) with `customers` and `followups` tables
- **SMTP**: QQ个人邮箱 (kali_foever@qq.com), 授权码已存 `.smtp_password`
- **Scripts dir**: `memories/脚本缓存/富通CRM/`

## Key Files
| File | Purpose |
|------|---------|
| `scripts/send_selected5.py` | Main campaign script — filter, random sample, send, log |
| `scripts/blit_mailer.py` | SMTP mail engine (smtplib, retry, HTML/attachment support) |
| `scripts/bliiot_crm.py` | CRM tools — query customers, log follow-ups, sync to JoinF |
| `crm_followups.db` | SQLite database with customers + followups tables |
| `.smtp_password` | SMTP authorization code (text file, gitignored) |

## Steps

### 1. Export CRM Data (first time only)
Connect via CDP to Chrome profile with JoinF CRM logged in:
```bash
# Start Chrome with remote debugging
"/c/Program Files/Google/Chrome/Application/chrome.exe" --remote-debugging-port=9226 --user-data-dir="C:/Users/Admin/AppData/Local/Google/Chrome/User Data/Profile 2"
```
Navigate to https://trade.joinf.com → login → browse customer list.
Use CDP to extract cookies + xCid + xUser → call API:
```python
GET /rapi/d/customers?num={page}&paging=true&size=50
```
Headers: `Cookie`, `xCid(71376)`, `xUser(183006)`, `displayType(236496)`

### 2. Initialize SQLite Database
```bash
python blit_crm.py
```
This creates `crm_followups.db` and imports all customers from JSON.

### 3. Configure SMTP (one-time)
Edit `blit_mailer.py`:
- `SMTP_SERVER = smtp.qq.com`
- `SMTP_PORT = 465`
- `SENDER_EMAIL = kali_foever@qq.com`
- `SENDER_NAME = Kali | BLIIOT Technology`
- Password file: `.smtp_password` (do NOT commit to git)

Test: `python -c "from blit_mailer import send_email; send_email('test@example.com', 'Test', 'Hello')"`

### 4. Run Email Campaign
```bash
python send_selected5.py
```

This script:
1. Connects to SQLite DB
2. Filters customers by condition (e.g. `createDate < '2024-01-01'`)
3. Randomly samples N customers (default: 5)
4. Checks each has a valid email
5. Sends personalized email with human-like delays (1-3 min between sends)
6. Logs each follow-up to `followups` table
7. Notes which customers need CRM sync

### 5. Verify Delivery
Check QQ mail sent folder, or query:
```bash
sqlite3 crm_followups.db "SELECT * FROM followups WHERE type='email' ORDER BY created_at DESC LIMIT 5;"
```

### 6. Sync to JoinF CRM (optional)
```bash
# Sync all pending follow-ups
python blit_crm.py --sync-followups
```

## Campaign Script Template (`send_selected5.py`)

```python
"""
BLIIOT Email Campaign — filter, sample, send, log
"""
import sqlite3, json, random, time, logging
from datetime import datetime
from blit_mailer import send_email
from blit_crm import add_followup

DB_PATH = r"C:\Users\Admin\AppData\Local\hermes\memories\脚本缓存\富通CRM\crm_followups.db"
SMTP_PASSWORD_PATH = r"C:\Users\Admin\AppData\Local\hermes\memories\脚本缓存\富通CRM\.smtp_password"
EMAIL_TEMPLATE = """Hi {name},
...
"""

def load_password():
    with open(SMTP_PASSWORD_PATH) as f:
        return f.read().strip()

def get_customers_before_date(cursor, date_str='2024-01-01', limit=None, country=None):
    query = "SELECT * FROM customers WHERE createDate < ?"
    params = [date_str]
    if country:
        query += " AND country = ?"
        params.append(country)
    cursor.execute(query, params)
    rows = cursor.fetchall()
    cols = [d[0] for d in cursor.description]
    customers = [dict(zip(cols, row)) for row in rows]
    if limit:
        customers = random.sample(customers, min(limit, len(customers)))
    return customers

def run_campaign(num=5, date_before='2024-01-01', country=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    customers = get_customers_before_date(cursor, date_before, limit=num, country=country)
    password = load_password()
    
    results = []
    for i, c in enumerate(customers):
        email = c.get('email', '') or c.get('contacts', '[]')
        # extract email logic...
        if not email:
            logging.warning(f"{c['name']} has no email, skipping")
            continue
        
        body = EMAIL_TEMPLATE.format(name=c.get('contactName', c.get('name', 'Customer')))
        success, status = send_email(
            to=email, 
            subject="Partnership Inquiry - BLIIOT Technology", 
            body=body,
            sender_pass=password
        )
        
        if success:
            add_followup(c['id'], f"Sent email to {email}", type='email')
            logging.info(f"✓ Sent to {c['name']} <{email}>")
        else:
            logging.error(f"✗ Failed to {c['name']} <{email}>: {status}")
        
        results.append({'name': c['name'], 'email': email, 'country': c.get('country'), 'success': success})
        
        if i < len(customers) - 1:
            delay = random.randint(60, 150)
            logging.info(f"Waiting {delay}s before next send...")
            time.sleep(delay)
    
    conn.close()
    return results
```

## Email Template
The standard outreach email template is defined in the user's request. Current version (en):
```
Subject: Partnership Inquiry - BLIIOT Technology

Hi {name},
... (user provided content)
Best regards,
Kali
BLIIOT Technology
```

## Key Rules
1. **Human-like delays**: Always 1-3 minutes between sends for natural pacing
2. **Language match**: If customer name appears non-English (Russian/Cyrillic etc.), default to English
3. **No duplicate sending**: Check followups table before sending to same email
4. **CRM sync**: Log every send; batch-sync to JoinF CRM after campaign
5. **SMTP auth code**: Store in `.smtp_password`, never commit to git
6. **QQ rate limits**: Max ~50 sends/day for personal QQ; space campaigns accordingly
7. **Consider timezone**: Send during business hours in recipient's country

## Troubleshooting

| Issue | Fix |
|-------|-----|
| SMTP auth failed | Re-extract QQ authorization code from QQ mail -> Settings -> Account |
| CDP connection refused | Restart Chrome with `--remote-debugging-port=9226` |
| `displayValue=""` blank followup | Pass customer name in contacts[0].contactName field |
| Proxy blocking SMTP | Use `--noproxy "*"` or disable Vortex proxy temporarily |