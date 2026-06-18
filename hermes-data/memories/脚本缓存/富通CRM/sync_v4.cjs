const WebSocket = require('ws');
const http = require('http');

function findLoginPage() {
  return new Promise((resolve, reject) => {
    http.get('http://127.0.0.1:9226/json', (res) => {
      let d = '';
      res.on('data', c => d += c);
      res.on('end', () => {
        const pages = JSON.parse(d);
        // Find a login page
        let p = pages.find(x => x.url.includes('cloud.joinf.com/login'));
        if (!p) p = pages.find(x => x.url.includes('trade.joinf.com'));
        if (!p) p = pages[0];
        console.error(`📡 Target: ${(p.id||'').substring(0,20)} | ${(p.url||'').substring(0,80)}`);
        resolve({ wsUrl: p.webSocketDebuggerUrl, url: p.url });
      });
    }).on('error', reject);
  });
}

async function main() {
  const { wsUrl, url } = await findLoginPage();
  
  const ws = new WebSocket(wsUrl);
  await new Promise((res, rej) => { ws.on('open', res); ws.on('error', rej); setTimeout(() => rej('timeout'), 10000); });
  
  let mid = 0;
  const pending = {};
  ws.on('message', (d) => {
    const r = JSON.parse(d.toString());
    if (r.id && pending[r.id]) { pending[r.id](r); delete pending[r.id]; }
  });
  const send = (m, p) => new Promise(r => { const id = ++mid; pending[id] = r; ws.send(JSON.stringify({ id, method: m, params: p })); });
  const js = async (e) => { const r = await send('Runtime.evaluate', { expression: e, returnByValue: true, awaitPromise: true }); return r.result?.result?.value; };
  
  let curUrl = url;
  
  // STEP 1: Login if needed
  if (curUrl.includes('/login')) {
    console.error('🔑 Logging in...');
    await send('Page.navigate', { url: 'https://cloud.joinf.com/login?service=https%3A%2F%2Ftrade.joinf.com%2Ftms%2Fcustomer%2Fcustomers%3Ftab%3D0' });
    await new Promise(r => setTimeout(r, 3000));
    await js("document.getElementById('loginID').value='bliiot03'");
    await js("document.getElementById('loginPassword').value='Kali1314520!'");
    await js("document.getElementById('loginBtn').click()");
    await new Promise(r => setTimeout(r, 5000));
    curUrl = await js("window.location.href");
    console.error(`📍 After login: ${(curUrl||'').substring(0,80)}`);
  }
  
  // STEP 2: Verify we're on customers page
  if (!curUrl || curUrl.includes('/login')) {
    console.error('❌ Login failed');
    ws.close();
    return;
  }
  
  console.error(`✅ On: ${curUrl.substring(0,100)}`);
  
  // STEP 3: The records (same content for all since we're verifying)
  const records = [
    [229629960, "Juan Carlos Martinez Quintero", "[邮件] 昨天给Juan Carlos发送了跟进邮件，询问新项目需求。"],
    [229679705, "Stephen Hudson / Valve Supplies (NZ) Ltd", "[邮件] 昨天给Stephen Hudson发送了跟进邮件，询问新项目需求。"],
    [229629827, "Richard Twite / Twite Instruments", "[邮件] 昨天给Richard Twite发送了跟进邮件，介绍新产品。"],
    [229623037, "Mr Basem Mohamed Ibrahim Elsayed Elmanzalawi.", "[邮件] 昨天给Basem发送了跟进邮件，询问新项目需求。"],
    [229649728, "Alex Elliot", "[邮件] 昨天给Alex Elliot发送了跟进邮件，询问新项目合作机会。"],
  ];
  
  for (let i = 0; i < records.length; i++) {
    const [cid, name, content] = records[i];
    const payload = JSON.stringify({
      id:"", attachmentList:[], businessStep:0, customerStep:0, completeNoRemind:0,
      cycleEndDay:"", cycleStartDay:"", cycleId:"", dataType:0, currentDoneFlag:0,
      models: [
        {columnDisplayName:"Customer Name", columnName:"dataName", dict:false, displayOriginalValue:cid, displayValue:name, originalValue:"", value:cid},
        {columnDisplayName:"Contact Name", columnName:"dataContactName", dict:false, displayOriginalValue:"", displayValue:"", originalValue:"", value:null},
        {columnDisplayName:"Content", columnName:"contactContent", dict:false, displayOriginalValue:"", displayValue:"", originalValue:"", value:content},
        {columnDisplayName:"Attachment", columnName:"annex", dict:false, displayOriginalValue:"", displayValue:"", originalValue:"", value:null},
        {columnDisplayName:"Color", columnName:"bgColor", dict:false, displayOriginalValue:"", displayValue:"", originalValue:"", value:"2B579A"},
        {columnDisplayName:"Follow Method", columnName:"method", dict:true, displayOriginalValue:"", displayValue:"", originalValue:"", value:"邮件"},
        {columnDisplayName:"Planning Time", columnName:"planningTime", dict:false, displayOriginalValue:"", displayValue:"", originalValue:"", value:"2026-06-19 00:00:00"},
        {columnDisplayName:"Feedback Operator", columnName:"feedbackOperator", dict:false, displayOriginalValue:"", displayValue:"", originalValue:"", value:"183006"}
      ],
      relevantList: [{relevantId:"", relevant:""}],
      flowStep:"", forceRefresh:true, followType:"", followObject:""
    });
    
    const result = await js(`
      (async() => {
        const r = await fetch('/rapi/m/follow/add', {
          method: 'POST',
          headers: {'Content-Type':'application/json'},
          body: ${JSON.stringify(payload)}
        });
        const j = await r.json();
        return JSON.stringify({ok: j.success, msg: j.errMsg, data: j.data, status: r.status});
      })()
    `);
    console.error(`${i+1}/${records.length} ${name}: ${result}`);
  }
  
  // STEP 4: Verify
  console.error("\n--- VERIFY ---");
  for (let i = 0; i < records.length; i++) {
    const [cid, name] = records[i];
    const search = `searchText=${cid}`;
    const v = await js(`
      (async() => {
        const r = await fetch('/rapi/d/customers?num=0&paging=true&size=200&${search}', {
          headers: {'Accept':'application/json'}
        });
        const j = await r.json();
        const v = j.data?.values;
        if (v && v[0]) return JSON.stringify({lf: v[0].displayLastFollowTime, act: v[0].activity || ''});
        return 'not found';
      })()
    `);
    console.error(`${name.substring(0,20)}: ${v}`);
  }
  
  ws.close();
}

main().catch(e => { console.error('ERROR:', e.message); process.exit(1); });