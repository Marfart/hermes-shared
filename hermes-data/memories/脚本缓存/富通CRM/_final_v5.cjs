const WebSocket = require('ws');
const http = require('http');
const fs = require('fs');

// This approach: login via CDP, stay on the SAME page with ticket, get cookie, use it for direct HTTP

async function main() {
  // Get login page from CDP
  const pages = JSON.parse(await new Promise((res, rej) => {
    http.get('http://127.0.0.1:9226/json', (r) => { let d = ''; r.on('data', c => d += c); r.on('end', () => res(d)); });
  }));
  let p = pages.find(x => x.url.includes('cloud.joinf.com/login'));
  if (!p) p = pages[0];

  // Connect and login
  const ws = new WebSocket(p.webSocketDebuggerUrl);
  await new Promise((r, rej) => { ws.on('open', r); ws.on('error', rej); setTimeout(() => rej('timeout'), 10000); });

  let mid = 0;
  const pending = {};
  ws.on('message', (d) => { const r = JSON.parse(d.toString()); if (r.id && pending[r.id]) { pending[r.id](r); delete pending[r.id]; } });
  const js = (e) => new Promise(res => { const id = ++mid; pending[id] = res; ws.send(JSON.stringify({ id, method: 'Runtime.evaluate', params: { expression: e, returnByValue: true, awaitPromise: true } })); });

  // Navigate to login with customer redirect
  console.error('🔑 Navigating to login...');
  await ws.send(JSON.stringify({ id: 0, method: 'Page.navigate', params: { url: 'https://cloud.joinf.com/login?service=https%3A%2F%2Ftrade.joinf.com%2Ftms%2Fcustomer%2Fcustomers%3Ftab%3D0' } }));
  await new Promise(r => setTimeout(r, 3000));

  // Login
  await js("document.getElementById('loginID').value='bliiot03'");
  await js("document.getElementById('loginPassword').value='Kali1314520!'");
  await js("document.getElementById('loginBtn').click()");
  await new Promise(r => setTimeout(r, 6000));  // Wait for CAS redirect

  const urlResult = await js("window.location.href");
    let url = typeof urlResult === 'string' ? urlResult : (urlResult?.value || '');
    console.error(`📍 URL: ${url.substring(0,100)}`);
  if (!url || url.includes('/login')) {
    console.error('❌ Login failed');
    ws.close();
    return;
  }

  // Now we're on the SAME tab WITH the ticket. Get the cookie.
  const cookie = await js("document.cookie");
  const xcid = await js("localStorage.getItem('joinf-compnayId')");
  const xuser = await js("localStorage.getItem('joinf-XUser')");

  console.error(`🔑 Cookie has JOINF_SESSION: ${(cookie||'').includes('JOINF_SESSION') ? '✅' : '❌'}`);
  console.error(`🔑 X-Cid: ${xcid}, X-User: ${xuser}`);

  // Now do direct HTTP fetch (NOT through CDP) using this cookie
  // The import won't work in eval, so inline the payload directly
  const followupPayload = (cid, content) => ({
    id: "", attachmentList: [], businessStep: 0, customerStep: 0, completeNoRemind: 0,
    cycleEndDay: "", cycleStartDay: "", cycleId: "", dataType: 0, currentDoneFlag: 0,
    models: [
      { columnDisplayName: "Customer Name", columnName: "dataName", dict: false, displayOriginalValue: cid, displayValue: "", originalValue: "", value: cid },
      { columnDisplayName: "Contact Name", columnName: "dataContactName", dict: false, displayOriginalValue: "", displayValue: "", originalValue: "", value: null },
      { columnDisplayName: "Content", columnName: "contactContent", dict: false, displayOriginalValue: "", displayValue: "", originalValue: "", value: content },
      { columnDisplayName: "Attachment", columnName: "annex", dict: false, displayOriginalValue: "", displayValue: "", originalValue: "", value: null },
      { columnDisplayName: "Color", columnName: "bgColor", dict: false, displayOriginalValue: "", displayValue: "", originalValue: "", value: "2B579A" },
      { columnDisplayName: "Follow Method", columnName: "method", dict: true, displayOriginalValue: "", displayValue: "", originalValue: "", value: "邮件" },
      { columnDisplayName: "Planning Time", columnName: "planningTime", dict: false, displayOriginalValue: "", displayValue: "", originalValue: "", value: "2026-06-19 00:00:00" },
      { columnDisplayName: "Feedback Operator", columnName: "feedbackOperator", dict: false, displayOriginalValue: "", displayValue: "", originalValue: "", value: "183006" }
    ],
    relevantList: [{ relevantId: "", relevant: "" }],
    flowStep: "", forceRefresh: true, followType: "", followObject: ""
  });

  const records = [
    [229629960, "[邮件] 昨天（2026-06-18）给Juan Carlos Martinez发送了跟进邮件，询问新项目需求。"],
    [229679705, "[邮件] 昨天（2026-06-18）给Stephen Hudson发送了跟进邮件，询问新项目需求。"],
    [229629827, "[邮件] 昨天（2026-06-18）给Richard Twite发送了跟进邮件，介绍新产品。"],
    [229623037, "[邮件] 昨天（2026-06-18）给Basem发送了跟进邮件，询问新项目需求。"],
    [229649728, "[邮件] 昨天（2026-06-18）给Alex Elliot发送了跟进邮件，询问新项目合作机会。"],
  ];

  const results = [];
  for (const [cid, content] of records) {
    // Use the page's own fetch (with the browser's cookie/session)
    const result = await js(`
      (async() => {
        const r = await fetch('/rapi/m/follow/add', {
          method: 'POST',
          headers: {'Content-Type':'application/json'},
          body: JSON.stringify(${JSON.stringify(followupPayload(cid, content))})
        });
        const j = await r.json();
        return JSON.stringify({ok: j.success, data: j.data, msg: j.errMsg, status: r.status});
      })()
    `);
    console.error(`  ${cid}: ${result}`);
    results.push(result);
  }

  // Verify: sleep 2s then check activityType
  await new Promise(r => setTimeout(r, 2000));
  console.error("\n--- Verify ---");
  for (const [cid, _] of records.slice(0, 1)) {
    const v = await js(`
      (async() => {
        const r = await fetch('/rapi/d/customers/${cid}/1', {headers: {'Accept':'application/json'}});
        const j = await r.json();
        const info = j.data?.find(c => c.categoryName === '主要信息');
        if (!info?.columnData) return 'no info';
        const lf = info.columnData.displayLastFollowTime;
        const rf = info.columnData.recentlyFollowTime;
        return JSON.stringify({lfv: lf?.value, lfd: lf?.displayValue, rfv: rf?.value, at: info.columnData.activityType?.value});
      })()
    `);
    console.error(`  ${cid}: follow status: ${v}`);
  }

  ws.close();
  console.error("\n✅ Done");
}

main().catch(e => { console.error('ERROR:', e.message); process.exit(1); });