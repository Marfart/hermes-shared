#!/usr/bin/env node
/**
 * BLIIOT CRM → JoinF CRM Sync Tool
 * 
 * Receives follow-up data via stdin JSON and syncs to JoinF CRM via CDP.
 * 
 * Usage:
 *   echo '{"id":1,"customer_id":235327923,"content":"测试","type":"跟进","created_at":"..."}' | node sync_to_joinf.cjs
 *   node sync_to_joinf.cjs --batch < batch.json
 *   node sync_to_joinf.cjs --status
 */

const WebSocket = require('ws');
const http = require('http');

async function findCDPUrl() {
  return new Promise((resolve, reject) => {
    http.get('http://127.0.0.1:9226/json', (res) => {
      let data = '';
      res.on('data', c => data += c);
      res.on('end', () => {
        const pages = JSON.parse(data);
        let best = pages.find(p => p.url.includes('trade.joinf.com') && !p.url.includes('/login'));
        if (!best) best = pages.find(p => p.url.includes('cloud.joinf.com/login'));
        if (!best) best = pages[0];
        if (best) {
          resolve({ wsUrl: best.webSocketDebuggerUrl, url: best.url });
        } else reject(new Error('No pages'));
      });
    }).on('error', reject);
  });
}

const PAGE_URL = 'https://trade.joinf.com/tms/customer/customers?type=search&tab=0';

const COLOR_MAP = { '邮件': '2B579A', 'WhatsApp': '27AE60', '报价': 'E67E22', '电话': '8E44AD', '会议': '9B59B6' };
const METHOD_MAP = { '邮件': '邮件', 'WhatsApp': 'WhatsApp', '电话': '电话', '会议': '会议' };

async function connectCDP(wsUrl) {
  return new Promise((resolve, reject) => {
    const ws = new WebSocket(wsUrl);
    ws.on('open', () => resolve(ws));
    ws.on('error', reject);
    setTimeout(() => reject(new Error('CDP connection timeout')), 10000);
  });
}

function createCDPSender(ws) {
  let msgId = 0;
  const pending = {};
  
  ws.on('message', (data) => {
    const resp = JSON.parse(data.toString());
    if (resp.id && pending[resp.id]) {
      pending[resp.id](resp);
      delete pending[resp.id];
    }
  });
  
  return {
    send(method, params = {}) {
      return new Promise((resolve) => {
        const id = ++msgId;
        pending[id] = resolve;
        ws.send(JSON.stringify({ id, method, params }));
      });
    },
    async eval(expression) {
      const r = await this.send('Runtime.evaluate', {
        expression, returnByValue: true, awaitPromise: true
      });
      return r.result.result.value;
    }
  };
}

async function syncOne(cdp, record) {
  const { customer_id, content, type, created_at } = record;
  const fullContent = `[${type}] ${content}`;
  
  const bgColor = COLOR_MAP[type] || 'fe4145';
  const method = METHOD_MAP[type] || '';
  
  const expr = `
    (async () => {
      try {
        const resp = await fetch('/rapi/m/follow/add', {
          method: 'POST',
          headers: { 'X-Cid':'71376','X-User':'183006','Content-Type':'application/json','Accept':'application/json' },
          body: JSON.stringify({
            id:"",attachmentList:[],businessStep:0,customerStep:0,completeNoRemind:0,
            cycleEndDay:"",cycleStartDay:"",cycleId:"",dataType:0,currentDoneFlag:0,
            models:[
              {columnDisplayName:"Customer Name",columnName:"dataName",dict:false,
               displayOriginalValue:${customer_id},displayValue:"",originalValue:"",value:${customer_id}},
              {columnDisplayName:"Contact Name",columnName:"dataContactName",dict:false,
               displayOriginalValue:"",displayValue:"",originalValue:"",value:null},
              {columnDisplayName:"Content",columnName:"contactContent",dict:false,
               displayOriginalValue:"",displayValue:"",originalValue:"",value:${JSON.stringify(fullContent)}},
              {columnDisplayName:"Attachment",columnName:"annex",dict:false,
               displayOriginalValue:"",displayValue:"",originalValue:"",value:null},
              {columnDisplayName:"Color",columnName:"bgColor",dict:false,
               displayOriginalValue:"",displayValue:"",originalValue:"",value:"${bgColor}"},
              {columnDisplayName:"Follow Method",columnName:"method",dict:true,
               displayOriginalValue:"",displayValue:"",originalValue:"",value:"${method}"},
              {columnDisplayName:"Planning Time",columnName:"planningTime",dict:false,
               displayOriginalValue:"",displayValue:"",originalValue:"",value:${JSON.stringify(created_at)}},
              {columnDisplayName:"Step",columnName:"step",dict:true,
               displayOriginalValue:"",displayValue:"",originalValue:"",value:null},
              {columnDisplayName:"Next Remind Time",columnName:"nextRemindTime",dict:false,
               displayOriginalValue:"",displayValue:"",originalValue:"",value:null},
              {columnDisplayName:"Repeat Cycle",columnName:"repeatCycle",dict:false,
               displayOriginalValue:"",displayValue:"",originalValue:"",value:null},
              {columnDisplayName:"Relevant",columnName:"relevant",dict:false,
               displayOriginalValue:"",displayValue:"",originalValue:"",value:null},
              {columnDisplayName:"Operator",columnName:"operatorName",dict:false,
               displayOriginalValue:"",displayValue:"",originalValue:"",value:null},
              {columnDisplayName:"Feedback Operator",columnName:"feedbackOperator",dict:false,
               displayOriginalValue:"",displayValue:"",originalValue:"",value:"183006"}
            ],
            relevantList:[{relevantId:"",relevant:""}],
            flowStep:"",forceRefresh:true,followType:"",followObject:""
          })
        });
        const json = await resp.json();
        return JSON.stringify({ ok: json.success || json.code === 0, msg: json.errMsg });
      } catch(e) { return JSON.stringify({ ok: false, error: e.message }); }
    })()
  `;
  
  const raw = await cdp.eval(expr);
  return JSON.parse(raw);
}

async function main() {
  const args = process.argv.slice(2);
  
  if (args.includes('--status')) {
    try {
      const { wsUrl, url } = await findCDPUrl();
      const ws = await connectCDP(wsUrl);
      const cdp = createCDPSender(ws);
      const loggedIn = url.includes('trade.joinf.com') && !url.includes('/login');
      console.log(JSON.stringify({
        cdp_connected: true,
        logged_in: loggedIn,
        url: url.substring(0, 100)
      }));
      ws.close();
    } catch(e) {
      console.log(JSON.stringify({ cdp_connected: false, error: e.message }));
    }
    return;
  }
  
  // Read batch file
  const batchIdx = args.indexOf('--batch');
  if (batchIdx === -1) { console.error('Need --batch <file>'); process.exit(1); }
  const batchFile = args[batchIdx + 1];
  const records = JSON.parse(require('fs').readFileSync(batchFile, 'utf-8'));
  
  // Connect
  const { wsUrl, url } = await findCDPUrl();
  console.error(`📡 ${url.substring(0,80)}`);
  
  // Login if needed
  let ws, cdp;
  try {
    ws = await connectCDP(wsUrl);
    cdp = createCDPSender(ws);
  } catch(e) {
    console.log(JSON.stringify({ status: 'cdp_error', error: e.message }));
    process.exit(1);
  }
  
  if (url.includes('/login')) {
    console.error('🔑 Login required...');
    await cdp.send('Page.navigate', { url: 'https://cloud.joinf.com/login?service=https%3A%2F%2Ftrade.joinf.com%2Ftms%2Fcustomer%2Fcustomers%3Ftab%3D0' });
    await new Promise(r => setTimeout(r, 4000));
    await cdp.eval("document.getElementById('loginID').value='bliiot03'");
    await cdp.eval("document.getElementById('loginPassword').value='Kali1314520!'");
    await cdp.eval("document.getElementById('loginBtn').click()");
    await new Promise(r => setTimeout(r, 6000));
    const newUrl = await cdp.eval('window.location.href');
    console.error(`📍 ${(newUrl||'').substring(0,80)}`);
  }
  
  // Navigate to customers page (only if not already there)
  const currentUrl = await cdp.eval('window.location.href');
  if (!currentUrl || !currentUrl.includes('/customer') || currentUrl.includes('/login')) {
    await cdp.send('Page.navigate', { url: PAGE_URL });
    await new Promise(r => setTimeout(r, 3000));
  }
  
  // Push records
  const results = [];
  for (const record of records) {
    const result = await syncOne(cdp, record);
    
    if (result.ok) {
      results.push({ id: record.id, status: 'ok' });
      console.error(`✅ ${record.customer_name || record.customer_id}`);
    } else {
      results.push({ id: record.id, status: 'failed', error: result.msg || result.error });
      console.error(`❌ ${record.customer_name || record.customer_id}: ${result.msg || result.error}`);
    }
    
    if (records.length > 1) await new Promise(r => setTimeout(r, 300));
  }
  
  ws.close();
  
  console.log(JSON.stringify({
    status: 'complete',
    records: records.length,
    results
  }));
}

const fs = require('fs');
main().catch(e => {
  console.log(JSON.stringify({ status: 'error', error: e.message }));
  process.exit(1);
});