---
name: blit-email-campaign
category: sales
description: "BLIIOT email outreach campaign — filter CRM customers, send personalized emails via QQ SMTP, log follow-ups to local SQLite, sync to JoinF CRM. Supports random sampling, country filtering, and date-based segmentation."
version: 1.2.0
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
| `scripts/send_selected5.py` | Main campaign script — filter, random sample, send, log, optional sync |
| `scripts/batch_email_v4.py` | 分批执行版 v4 — 从66K公海JSON筛选+随机化发送+每日状态跟踪 (2026-06-19) |
| *(external)* `memories/脚本缓存/产品推广/.sent_log_v4.json` | v4发送去重日志 (合并旧.sent_log.json) |
| *(external)* `memories/脚本缓存/产品推广/.daily_state_v4.json` | 每日发送状态 {date, count, sent_ids} |
| *(external)* `~/Desktop/Working/富通CRM_公海客户_全量.json` | 66K公海客户全量数据 (2026-06-19爬取) |
| `scripts/blit_mailer.py` | SMTP mail engine (smtplib, retry, HTML/attachment support) |
| `references/joinf-sync-via-browser.md` | JoinF CRM sync via Hermes browser_console technique |
| *(external)* `memories/脚本缓存/富通CRM/bliiot_crm.py` | CRM tools — query customers, log follow-ups, sync to JoinF |

## Quick Start

### Method A: Full Auto (Recommended — 2026-06-19+)

Uses the 66K公海客户 JSON + randomized templates + daily state tracking:

```bash
cd memories/脚本缓存/产品推广
python batch_email_v4.py [batch_size]
```

- `batch_size` defaults to 5 (use 37 for large batches, 5 for cron)
- Automatically filters: `displayCreateTime < 2024` + `contactEmail` not empty
- Randomly shuffles targets each run (never same order)
- Daily limit: 50 (tracked in `.daily_state_v4.json`, resets at midnight)
- Anti-dup: `.sent_log_v4.json` (merges old `.sent_log.json` on load)

### Method B: Legacy (SQLite-based)

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

## ⚠️ Critical Pitfalls

### 1. ALWAYS load `bliiot-crm-followup` skill before CRM sync
Do NOT hand-craft fetch calls to JoinF API. The `bliiot-crm-followup` skill has the correct payload structure (displayValue for customer name, color mapping, planningTime format), the dual-write pattern (SQLite + pending_sync.json), and both sync methods (Hermes browser_console + CDP sync_all_pending.mjs). Loading it first is **mandatory** — the user explicitly corrected this.

### 2. Dual-write after sync
After pushing to JoinF CRM, update **BOTH** SQLite (`UPDATE followups SET synced=1`) AND `pending_sync.json`. One without the other is a half-sync.

### 3. NEVER kill a running email process and restart
Killing `batch_email_v4.py` mid-run and restarting causes **duplicate sends** — the sent_log only saves after each send, and the new process reads the old log. If you must stop, let the current email finish, then stop. Do NOT restart the same script.

### 4. Windows git-bash stdout buffering
Python stdout is heavily buffered on Windows git-bash even with `-u` flag. Background process output may appear empty. Use `execute_code` for inline execution with real-time output, or check `.sent_log_v4.json` after completion to verify results.

### 5. sent_log_v4.json merges old sent_log.json
On load, `batch_email_v4.py` merges both `.sent_log_v4.json` and `.sent_log.json`. This ensures the 10 customers sent via the old script are never re-sent via the new one.

## Key Rules
1. **Human-like delays**: 60-180s random delay between sends — never burst
2. **No duplicate sending**: `.sent_log_v4.json` is the sole source of truth. Check before send, save immediately after. Merges old `.sent_log.json` on load.
3. **CRM sync is MANDATORY**: Every send → logged to SQLite → **must sync to JoinF CRM** (user explicitly requires this). See "Syncing to JoinF CRM" below.
4. **SMTP auth code**: Stored at `memories/脚本缓存/产品推广/.smtp_password`, never commit to git
5. **QQ rate limits**: ~50 sends/day max for personal QQ; space campaigns accordingly
6. **Timezone awareness**: Consider recipient's business hours when scheduling
7. **Randomize content**: 3 body templates × 4 subjects × 4 greetings = 48 combos. Never send identical emails.
8. **Daily state tracking**: `.daily_state_v4.json` tracks `{date, count, sent_ids}`. Resets at midnight.

## ⚠️ CRITICAL: Sync Verification Trap

**Never trust API `success: true` alone.** Hermes browser sessions expire silently. When kicked back to `cloud.joinf.com/login`, fetch calls hit login page HTML which gets misparsed as `{success: true}`.

**Before sync** — verify you're logged in:
```javascript
window.location.href
// Must be "https://trade.joinf.com/tms/customer/customers?tab=0"
```

**After sync** — verify the record was written:
```javascript
let r = await fetch('/rapi/d/customers?num=0&paging=true&size=50&searchText=客户名称', {headers:{'Accept':'application/json'}});
let j = await r.json();
let v = j.data?.values;
let t = v.find(x => x.id === 客户ID);
// If displayLastFollowTime is unchanged (e.g. 1773365475000 = March 2026), sync FAILED
console.log({lastFollow: t?.displayLastFollowTime, recentlyFollow: t?.recentlyFollowTime});
```

**bgColor/method values**: Must be plain strings like `"2B579A"`, NOT `'"2B579A"'` (extra quotes cause API to accept but not display the record).

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

## Syncing to JoinF CRM (Mandatory After Sending)

After sending emails, you **must** sync the follow-up records to JoinF CRM. The user explicitly requires this.

### Method A: Via Hermes Browser (Recommended — No CDP Setup Needed)

If Hermes browser is already logged into `trade.joinf.com` (e.g. from a previous `browser_navigate`), use `browser_console` to call the JoinF API directly.

**⚠️ CRITICAL: Before pushing, verify you're actually logged in:**
```javascript
window.location.href
// Must return "https://trade.joinf.com/tms/customer/customers?tab=0"
// If it returns "https://cloud.joinf.com/login", re-login first!
```

**⚠️ CRITICAL: After pushing, verify the record was actually written:**
```javascript
let r = await fetch('/rapi/d/customers?num=0&paging=true&size=50&searchText=客户名称', {headers:{'Accept':'application/json'}});
let j = await r.json();
let v = j.data?.values;
let t = v.find(x => x.id === 客户ID);
// If displayLastFollowTime is unchanged, sync FAILED silently
console.log({lastFollow: t?.displayLastFollowTime, recentlyFollow: t?.recentlyFollowTime});
```

Template — replace cid, name, content with actual values:
// Template — replace cid, name, content with actual values
(async() => {
  const records = [
    {cid: 229629960, name: 'Customer Name', content: '[邮件] 发送跟进邮件给...'}
  ];
  let res = [];
  for (let x of records) {
    let p = await fetch('/rapi/m/follow/add', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        id: "", attachmentList: [], businessStep: 0, customerStep: 0,
        completeNoRemind: 0, cycleEndDay: "", cycleStartDay: "", cycleId: "",
        dataType: 0, currentDoneFlag: 0,
        models: [
          {columnDisplayName: "Customer Name", columnName: "dataName", dict: false,
           displayOriginalValue: x.cid, displayValue: x.name, originalValue: "", value: x.cid},
          {columnDisplayName: "Contact Name", columnName: "dataContactName", dict: false,
           displayOriginalValue: "", displayValue: "", originalValue: "", value: null},
          {columnDisplayName: "Content", columnName: "contactContent", dict: false,
           displayOriginalValue: "", displayValue: "", originalValue: "", value: x.content},
          {columnDisplayName: "Attachment", columnName: "annex", dict: false,
           displayOriginalValue: "", displayValue: "", originalValue: "", value: null},
          {columnDisplayName: "Color", columnName: "bgColor", dict: false,
           displayOriginalValue: "", displayValue: "", originalValue: "", value: '"2B579A"'},
          {columnDisplayName: "Follow Method", columnName: "method", dict: true,
           displayOriginalValue: "", displayValue: "", originalValue: "", value: '"邮件"'},
          {columnDisplayName: "Planning Time", columnName: "planningTime", dict: false,
           displayOriginalValue: "", displayValue: "", originalValue: "", value: "2026-06-18 19:22:42"},
          {columnDisplayName: "Step", columnName: "step", dict: true,
           displayOriginalValue: "", displayValue: "", originalValue: "", value: null},
          {columnDisplayName: "Next Remind Time", columnName: "nextRemindTime", dict: false,
           displayOriginalValue: "", displayValue: "", originalValue: "", value: null},
          {columnDisplayName: "Repeat Cycle", columnName: "repeatCycle", dict: false,
           displayOriginalValue: "", displayValue: "", originalValue: "", value: null},
          {columnDisplayName: "Relevant", columnName: "relevant", dict: false,
           displayOriginalValue: "", displayValue: "", originalValue: "", value: null},
          {columnDisplayName: "Operator", columnName: "operatorName", dict: false,
           displayOriginalValue: "", displayValue: "", originalValue: "", value: null},
          {columnDisplayName: "Feedback Operator", columnName: "feedbackOperator", dict: false,
           displayOriginalValue: "", displayValue: "", originalValue: "", value: "183006"}
        ],
        relevantList: [{relevantId: "", relevant: ""}],
        flowStep: "", forceRefresh: true, followType: "", followObject: ""
      })
    });
    let j = await p.json();
    res.push({name: x.name, ok: j.success, msg: j.errMsg || 'OK'});
  }
  return JSON.stringify(res);
})()
```

**Advantages**: No CDP websocket needed, no `--remote-allow-origins` flag, no 403 issues. Just use the browser that's already authenticated.

### Method B: Via CDP Websocket (Standalone)

```bash
# Start Chrome with CDP
"/c/Program Files/Google/Chrome/Application/chrome.exe" \
  --remote-debugging-port=9226 \
  --remote-allow-origins=* \
  --user-data-dir="C:/Users/Admin/AppData/Local/Google/Chrome/User Data/Profile 2"

# Then run sync script
cd "memories/脚本缓存/富通CRM"
node sync_all_pending.mjs
```

### After Syncing

Update the local SQLite database to mark records as synced:

```bash
cd "memories/脚本缓存/富通CRM"
python -c "
import sqlite3
conn = sqlite3.connect('crm_followups.db')
conn.execute('UPDATE followups SET synced=1 WHERE id IN (id1,id2,id3,id4,id5)')
conn.commit()
conn.close()
print('Marked as synced')
"
```

## Troubleshooting

| Issue | Fix |
|-------|-----|
| SMTP auth failed | Re-extract QQ authorization code from QQ mail → Settings → Account |
| CDP connection refused | Restart Chrome with `--remote-debugging-port=9226` |
| "No customers matched" | Check the `createDate` format in crm_followups.db (could be `null` for old records) |
| Proxy blocking SMTP | Add `os.environ['NO_PROXY']='*'` before SMTP call, or disable Vortex proxy |