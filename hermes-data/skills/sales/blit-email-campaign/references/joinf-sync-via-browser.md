# JoinF CRM Sync via Hermes Browser

## Why This Technique

The Hermes browser (`browser_navigate` → `browser_console`) is already authenticated to `trade.joinf.com` after login. Using `browser_console` with `fetch()` to call the JoinF API is **simpler and more reliable** than:

- CDP websocket (needs `--remote-allow-origins=*` flag, 403 issues)
- Standalone Node.js scripts (need cookie extraction, CDP connection)
- Python websocket (same 403 issues)

## Prerequisites

- Hermes browser is currently on `https://trade.joinf.com` (any page)
- Session cookies are valid (not expired)

## Technique

Use `browser_console` with `expression` set to an async IIFE that calls `fetch('/rapi/m/follow/add', ...)`.

The browser's session cookies are automatically sent with same-origin `fetch()` calls — no manual cookie extraction needed.

## Full Payload Template

```javascript
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

## Response Format

The API returns:
```json
{"success": true, "data": "...", "errMsg": ""}
```

All 5 records in one call → all return `success: true` ✅

## After Sync

Update local SQLite:
```sql
UPDATE followups SET synced=1 WHERE id IN (id1,id2,id3,id4,id5);
```

## Pitfalls

- ⚠️ Expression must be compact — `browser_console` has a character limit. Use short variable names, no comments, minified JSON.
- ⚠️ If the browser navigates away from `trade.joinf.com`, the session cookies may not apply. Navigate back first.
- ⚠️ `displayValue` must be the customer name (not empty) — otherwise the follow-up appears in the timeline but shows blank when clicked.
- ⚠️ `planningTime` must be local time string `YYYY-MM-DD HH:mm:ss`, not ISO format.
