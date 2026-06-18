# Hermes Browser Sync — JoinF CRM Follow-up Records

## When to Use

After sending emails/WhatsApp messages, you need to push follow-up records to JoinF CRM. Use this method when:

- Hermes browser is already logged into `trade.joinf.com` (from a prior `browser_navigate`)
- CDP WebSocket gives 403 (missing `--remote-allow-origins=*`)
- CDP Chrome is stuck on the login page

## Prerequisites

Hermes browser must be on `https://trade.joinf.com/tms/customer/customers?tab=0` and show the CRM sidebar (logged in). Verify with `browser_console`:

```javascript
window.location.href
// → "https://trade.joinf.com/tms/customer/customers?tab=0"
```

If it shows `https://cloud.joinf.com/login`, you need to re-login:
1. `browser_navigate('https://cloud.joinf.com/login')`
2. Fill `bliiot03` / `Kali1314520!`
3. Click 安全登录
4. Click 客户 menu item to navigate back to customer page
5. Verify again with `window.location.href`

## 🚨 CRITICAL: Copy the template, don't re-invent

**Do NOT write your own fetch payload.** Copy the template below verbatim and only change:
- The `records` array (customer IDs, names, content text)
- The `planningTime` value

Reasons to not re-invent:
- The `models[]` format with all those seemingly-redundant fields (`displayOriginalValue`, `displayValue`, `originalValue` for every column) is what the JoinF Vue backend actually requires. Simplified payloads return `success: true` but the record is invisible.
- Writing a one-liner `fetch(...)` without `async()=>{...}()` wrapper gets truncated in `browser_console` (~500 char expression limit).
- This exact template was verified working on 2026-06-18 at 22:50 (returned real follow-up IDs 70942761-70942765 with `ok: true`).

## Sync Template

Call `browser_console` with this expression:

```javascript
(async()=>{
  let records = [
    {cid: 229629960, name: 'Juan Carlos Martinez Quintero', content: '[邮件] 我昨天（2026-06-18）给Juan Carlos（juancarlosmartinezq@hotmail.com）发送了一封跟进邮件，询问是否有新项目需求，并介绍了BLIIOT最新产品线。'},
    {cid: 229679705, name: 'Stephen Hudson / Valve Supplies (NZ) Ltd', content: '[邮件] 我昨天（2026-06-18）给Stephen Hudson（Stephen@Home.co.nz）发送了一封跟进邮件，询问是否还记得BLIIOT及是否有新项目需求。'},
    // ... add more records
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
          {columnDisplayName: "Content", columnName: "contactContent", dict: false,
           displayOriginalValue: "", displayValue: "", originalValue: "", value: x.content},
          {columnDisplayName: "Color", columnName: "bgColor", dict: false,
           displayOriginalValue: "", displayValue: "", originalValue: "", value: "2B579A"},
          {columnDisplayName: "Follow Method", columnName: "method", dict: true,
           displayOriginalValue: "", displayValue: "", originalValue: "", value: "邮件"},
          {columnDisplayName: "Planning Time", columnName: "planningTime", dict: false,
           displayOriginalValue: "", displayValue: "", originalValue: "", value: "2026-06-18 22:00:00"},
          {columnDisplayName: "Feedback Operator", columnName: "feedbackOperator", dict: false,
           displayOriginalValue: "", displayValue: "", originalValue: "", value: "183006"}
        ],
        relevantList: [{relevantId: "", relevant: ""}],
        flowStep: "", forceRefresh: true, followType: "", followObject: ""
      })
    });
    let j = await p.json();
    res.push({name: x.name, ok: j.success, msg: j.errMsg || 'OK', data: j.data});
  }
  return JSON.stringify(res);
})()
```

### ⚠️ Expression length warning

The entire expression must fit in ~4000 characters or `browser_console` will truncate it with `SyntaxError: Unexpected end of input`. If you have more than ~10 records, split into batches:
1. First batch: records 0-9
2. Second batch: records 10-19

### ✅ Expected success response

```json
[
  {"name": "Juan Carlos Martinez Quintero", "ok": true, "msg": "OK", "data": [70942761]},
  {"name": "Stephen Hudson / Valve Supplies", "ok": true, "msg": "OK", "data": [70942762]},
  ...
]
```

Each record returns its new follow-up ID in `data` — this is proof the record was actually created (not a false positive from being on the login page).

## After Sync — Dual Write

After all records return `ok: true`, update BOTH stores:

### SQLite
```python
import sqlite3
conn = sqlite3.connect('memories/脚本缓存/富通CRM/crm_followups.db')
# Mark unsynced email followups as synced
rows = conn.execute('SELECT id FROM followups WHERE type="邮件" AND synced=0').fetchall()
for r in rows:
    conn.execute('UPDATE followups SET synced=1 WHERE id=?', (r[0],))
conn.commit()
conn.close()
```

### pending_sync.json
```python
import json
with open('memories/脚本缓存/富通CRM/pending_sync.json') as f:
    pending = json.load(f)
for r in pending:
    if r.get('type') == '邮件' and r.get('synced') == 0:
        r['synced'] = 1
with open('memories/脚本缓存/富通CRM/pending_sync.json', 'w') as f:
    json.dump(pending, f, ensure_ascii=False, indent=2)
```

## Color Mapping

| Type | bgColor | Method Value |
|------|---------|-------------|
| 邮件 | 2B579A | "邮件" |
| WhatsApp | 27AE60 | "WhatsApp" |
| 报价 | E67E22 | "跟进" |
| 电话 | E74C3C | "电话" |
| 跟进/其他 | fe4145 | "" |

## ⚠️ CRITICAL: Verify After Sync — Don't Trust API `success: true`

**Hermes browser sessions expire silently.** When the browser gets kicked back to `cloud.joinf.com/login`, fetch calls hit the login page HTML instead of the API. The HTML `<!DOCTYPE html>` gets parsed as JSON and returns `{success: true}` — a **false positive**.

### Before Sync — Verify You're Logged In

```javascript
// Must return "https://trade.joinf.com/tms/customer/customers?tab=0"
// If it returns "https://cloud.joinf.com/login", you need to re-login
window.location.href
```

### After Sync — Verify the Record Was Written

Don't trust the API response. Check the customer's `displayLastFollowTime`:

```javascript
let r = await fetch('/rapi/d/customers?num=0&paging=true&size=50&searchText=客户名称', {headers:{'Accept':'application/json'}});
let j = await r.json();
let v = j.data?.values;
let t = v.find(x => x.id === 客户ID);
// displayLastFollowTime is Unix ms timestamp — if unchanged, the follow-up was NOT written
console.log({lastFollow: t?.displayLastFollowTime, recentlyFollow: t?.recentlyFollowTime});
```

If `displayLastFollowTime` is still the old value (e.g. 1773365475000 = March 2026), the sync **failed silently** — re-login and retry.

## Re-login Quick Reference

When the session expires (most common blocker), this is the fastest way back in:

```javascript
// Step 1: Navigate to login
// browser_navigate('https://cloud.joinf.com/login')

// Step 2: Fill credentials  
// browser_type(@e16, 'bliiot03')  — username
// browser_type(@e17, 'Kali1314520!')  — password

// Step 3: Click login
// browser_click(@e13)  — 安全登录

// Step 4: Wait for redirect, then click 客户 menu
// browser_click customer menu item (ref changes each session, look for menuitem "客户")

// Step 5: Verify
// browser_console: window.location.href
```