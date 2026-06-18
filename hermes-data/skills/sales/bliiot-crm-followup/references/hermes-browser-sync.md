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

## Sync Template

Call `browser_console` with this expression (compact one-liner to avoid truncation):

```javascript
(async()=>{
  let records = [
    {cid: 229629960, name: 'Juan Carlos Martinez Quintero', content: '[邮件] 发送跟进邮件给...'},
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
           displayOriginalValue: "", displayValue: "", originalValue: "", value: "2026-06-18 19:22:42"},
          {columnDisplayName: "Feedback Operator", columnName: "feedbackOperator", dict: false,
           displayOriginalValue: "", displayValue: "", originalValue: "", value: "183006"}
        ],
        relevantList: [{relevantId: "", relevant: ""}],
        flowStep: "", forceRefresh: true, followType: "", followObject: ""
      })
    });
    let j = await p.json();
    res.push({id: x.id, name: x.name, ok: j.success, msg: j.errMsg || 'OK'});
  }
  return JSON.stringify(res);
})()
```

## After Sync — Dual Write

After all records return `ok: true`, update BOTH stores:

### SQLite
```python
import sqlite3
conn = sqlite3.connect('memories/脚本缓存/富通CRM/crm_followups.db')
conn.execute('UPDATE followups SET synced=1 WHERE id IN (id1,id2,id3)')
conn.commit()
conn.close()
```

### pending_sync.json
```python
import json
with open('memories/脚本缓存/富通CRM/pending_sync.json') as f:
    pending = json.load(f)
for r in pending:
    if r['id'] in (id1,id2,id3) and r['synced'] == 0:
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

## Known Issues

- **Expression too long**: browser_console has a character limit. Keep the JS compact (no comments, short var names, single-line arrow functions). If it fails with "Unexpected end of input", the expression was truncated — split into batches.
- **Not logged in**: If fetch returns `<!DOCTYPE html>` (login page), navigate to `https://trade.joinf.com/tms/customer/customers?tab=0` first and verify the page shows the CRM sidebar.
- **bgColor/method values**: Must be plain strings like `"2B579A"`, NOT `'"2B579A"'` (extra quotes cause API to accept but not display the record).
