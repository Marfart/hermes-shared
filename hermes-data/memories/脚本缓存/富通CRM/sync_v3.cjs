// BLIIOT CRM → JoinF CRM Sync Tool v3
// 登錄後不重新導航，直接推

const WebSocket = require('ws');
const http = require('http');

async function findCDPUrl() {
  return new Promise((resolve, reject) => {
    http.get('http://127.0.0.1:9226/json', (res) => {
      let data = '';
      res.on('data', c => data += c);
      res.on('end', () => {
        const pages = JSON.parse(data);
        // Prefer a page already on trade.joinf.com (not login)
        let best = pages.find(p => p.url.includes('trade.joinf.com') && !p.url.includes('/login'));
        if (!best) best = pages[0];
        if (best) {
          console.error(`📡 Page: ${best.id.substring(0,20)} | ${(best.url || '').substring(0,80)}`);
          resolve({ wsUrl: best.webSocketDebuggerUrl, url: best.url || '' });
        } else reject(new Error('No pages'));
      });
    }).on('error', reject);
  });
}

function connect(wsUrl) {
  return new Promise((resolve, reject) => {
    const ws = new WebSocket(wsUrl);
    ws.on('open', () => resolve(ws));
    ws.on('error', reject);
    setTimeout(() => reject(new Error('CDP timeout')), 10000);
  });
}

function createCDP(ws) {
  let mid = 0;
  const pending = {};
  ws.on('message', (data) => {
    const r = JSON.parse(data.toString());
    if (r.id && pending[r.id]) { pending[r.id](r); delete pending[r.id]; }
  });
  return {
    send(m, p) { return new Promise(r => { const id = ++mid; pending[id] = r; ws.send(JSON.stringify({ id, method: m, params: p })); }); },
    async js(expr) {
      const r = await this.send('Runtime.evaluate', { expression: expr, returnByValue: true, awaitPromise: true });
      const exc = r.result?.exceptionDetails;
      if (exc) throw new Error(`JS Error: ${exc.text} ${exc.exception?.description?.substring(0,200) || ''}`);
      return r.result?.result?.value;
    }
  };
}

async function main() {
  const args = process.argv.slice(2);
  if (args.includes('--status')) {
    const { wsUrl, url } = await findCDPUrl();
    const ws = await connect(wsUrl);
    const cdp = createCDP(ws);
    const loggedIn = url.includes('trade.joinf.com') && !url.includes('/login');
    console.log(JSON.stringify({ cdp_connected: true, logged_in: loggedIn, url: url.substring(0,100) }));
    ws.close();
    return;
  }

  // Read batch file
  const batchIdx = args.indexOf('--batch');
  if (batchIdx === -1) { console.error('Need --batch <file>'); process.exit(1); }
  const batchFile = args[batchIdx + 1];
  const records = JSON.parse(require('fs').readFileSync(batchFile, 'utf-8'));

  // Connect
  const { wsUrl, url } = await findCDPUrl();
  const ws = await connect(wsUrl);
  const cdp = createCDP(ws);

  // Step 1: Check if we need to login
  let currentUrl = url;
  if (currentUrl.includes('/login')) {
    console.error('🔑 Need login...');
    // Navigate to service login URL
    await ws.send(JSON.stringify({ id: 0, method: 'Page.navigate', params: { url: 'https://cloud.joinf.com/login?service=https%3A%2F%2Ftrade.joinf.com%2Ftms%2Fcustomer%2Fcustomers%3Ftab%3D0' } }));
    await new Promise(r => setTimeout(r, 3000));
    await cdp.js("document.getElementById('loginID').value='bliiot03'");
    await cdp.js("document.getElementById('loginPassword').value='Kali1314520!'");
    await cdp.js("document.getElementById('loginBtn').click()");
    await new Promise(r => setTimeout(r, 5000));
    currentUrl = await cdp.js("window.location.href");
    console.error(`🔑 After login: ${(currentUrl||'').substring(0,80)}`);
  }

  // Step 2: Make sure we're on customers page WITH the ticket-carrying URL
  if (currentUrl && currentUrl.includes('/customer') && !currentUrl.includes('/login')) {
    console.error('✅ On customers page, pushing follow-ups...');
  } else {
    // Try navigating
    await ws.send(JSON.stringify({ id: 0, method: 'Page.navigate', params: { url: 'https://trade.joinf.com/tms/customer/customers?tab=0' } }));
    await new Promise(r => setTimeout(r, 4000));
    currentUrl = await cdp.js("window.location.href");
    if (currentUrl.includes('/login')) {
      // Need to login AGAIN from this URL
      console.error('🔑 Login required after navigation...');
      await cdp.js("document.getElementById('loginID').value='bliiot03'");
      await cdp.js("document.getElementById('loginPassword').value='Kali1314520!'");
      await cdp.js("document.getElementById('loginBtn').click()");
      await new Promise(r => setTimeout(r, 4000));
    }
  }

  // Step 3: Push follow-ups
  const results = [];
  for (const rec of records) {
    const { customer_id, customer_name, type, content, created_at } = rec;
    const fullContent = `[${type}] ${content}`;
    const bgColor = { '邮件': '2B579A', 'WhatsApp': '27AE60', '报价': 'E67E22', '电话': '8E44AD' }[type] || 'fe4145';

    try {
      const val = await cdp.js(`
        (async() => {
          const r = await fetch('/rapi/m/follow/add', {
            method: 'POST',
            headers: { 'Content-Type':'application/json', 'X-Cid':'71376', 'X-User':'183006' },
            body: JSON.stringify({
              models: [
                {columnName:"dataName", value:${customer_id}, displayValue:${JSON.stringify(customer_name)}, displayOriginalValue:${customer_id}},
                {columnName:"contactContent", value:${JSON.stringify(fullContent)}, displayValue:"", displayOriginalValue:""},
                {columnName:"bgColor", value:"${bgColor}", displayValue:"", displayOriginalValue:""},
                {columnName:"method", dict:true, value:"${type}", displayValue:"", displayOriginalValue:""},
                {columnName:"planningTime", value:${JSON.stringify(created_at || new Date().toISOString().replace('T',' ').substring(0,19))}, displayValue:"", displayOriginalValue:""},
                {columnName:"feedbackOperator", value:"183006", displayValue:"", displayOriginalValue:""}
              ]
            })
          });
          const j = await r.json();
          return JSON.stringify({ ok: j.success, data: j.data, msg: j.errMsg, status: r.status });
        })()
      `);
      const parsed = JSON.parse(val);
      results.push({ id: rec.id || 0, status: parsed.ok ? 'ok' : 'failed', msg: parsed.msg || 'OK', data: parsed.data });
      console.error(`${results.length}/${records.length} ${customer_name}: ${parsed.ok ? '✅' : '❌'} ${parsed.msg || 'OK'} data=${JSON.stringify(parsed.data)}`);
    } catch (e) {
      results.push({ id: rec.id || 0, status: 'error', msg: e.message });
      console.error(`${results.length}/${records.length} ${customer_name}: ❌ ${e.message}`);
    }

    if (records.length > 1) await new Promise(r => setTimeout(r, 200));
  }

  ws.close();
  console.log(JSON.stringify({ status: 'complete', records: records.length, results }));
}

main().catch(e => { console.error(e.message); process.exit(1); });