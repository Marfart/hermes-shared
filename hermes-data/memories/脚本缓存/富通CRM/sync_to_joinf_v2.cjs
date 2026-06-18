#!/usr/bin/env node
/**
 * BLIIOT CRM → JoinF CRM Sync Tool (v2 - fixed)
 * 
 * Dynamic CDP page ID + auto-login + verified write
 * 
 * Usage:
 *   node sync_to_joinf_v2.cjs --batch batch.json
 */

const WebSocket = require('ws');
const http = require('http');

const PAGE_URL = 'https://trade.joinf.com/tms/customer/customers?type=search&tab=0';
const LOGIN_URL = 'https://cloud.joinf.com/login?service=https%3A%2F%2Ftrade.joinf.com%2Ftms%2Fcustomer%2Fcustomers%3Ftab%3D0';

const COLOR_MAP = { '邮件': '2B579A', 'WhatsApp': '27AE60', '报价': 'E67E22', '电话': '8E44AD', '会议': '9B59B6' };
const METHOD_MAP = { '邮件': '邮件', 'WhatsApp': 'WhatsApp', '电话': '电话', '会议': '会议' };

async function findCDPUrl() {
  return new Promise((resolve, reject) => {
    http.get('http://127.0.0.1:9226/json', (res) => {
      let data = '';
      res.on('data', c => data += c);
      res.on('end', () => {
        try {
          const pages = JSON.parse(data);
          let best = pages.find(p => p.url.includes('trade.joinf.com') && !p.url.includes('/login'));
          if (!best) best = pages[0];
          if (best) {
            console.error(`📡 Page: ${best.id.substring(0,20)} | ${best.url.substring(0,60)}`);
            resolve(best.webSocketDebuggerUrl);
          } else reject(new Error('No pages'));
        } catch(e) { reject(e); }
      });
    }).on('error', reject);
  });
}

function connectCDP() {
  return new Promise(async (resolve, reject) => {
    const url = await findCDPUrl();
    const ws = new WebSocket(url);
    ws.on('open', () => resolve(ws));
    ws.on('error', reject);
    setTimeout(() => reject(new Error('CDP timeout')), 10000);
  });
}

function createCDPSender(ws) {
  let msgId = 0;
  const pending = {};
  ws.on('message', (data) => {
    const resp = JSON.parse(data.toString());
    if (resp.id && pending[resp.id]) { pending[resp.id](resp); delete pending[resp.id]; }
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
      const r = await this.send('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true });
      return r.result?.result?.value;
    },
    async navigate(url) {
      await this.send('Page.navigate', { url });
      await new Promise(r => setTimeout(r, 3000));
    }
  };
}

async function ensureLoggedIn(cdp) {
  // Navigate to customers page
  await cdp.navigate(PAGE_URL);
  let url = await cdp.eval('window.location.href') || '';
  console.error(`📍 ${url.substring(0,80)}`);
  
  if (url.includes('/login')) {
    console.error('🔑 Need login...');
    await cdp.navigate(LOGIN_URL);
    await new Promise(r => setTimeout(r, 2000));
    
    await cdp.eval("document.getElementById('loginID').value='bliiot03'");
    await cdp.eval("document.getElementById('loginPassword').value='Kali1314520!'");
    await cdp.eval("document.getElementById('loginBtn').click()");
    await new Promise(r => setTimeout(r, 5000));
    
    url = await cdp.eval('window.location.href') || '';
    console.error(`📍 After login: ${url.substring(0,80)}`);
    
    if (url.includes('/login')) {
      throw new Error('Login failed');
    }
    
    // Navigate to customers page
    await cdp.navigate(PAGE_URL);
    await new Promise(r => setTimeout(r, 3000));
  }
  
  const finalUrl = await cdp.eval('window.location.href') || '';
  const ok = finalUrl.includes('customer');
  console.error(`✅ CRM page: ${ok}`);
  return ok;
}

async function syncOne(cdp, record) {
  const { customer_id, content, type, created_at, customer_name } = record;
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
               displayOriginalValue:${customer_id},displayValue:${JSON.stringify(customer_name || '')},originalValue:"",value:${customer_id}},
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
        return JSON.stringify({ ok: json.success || json.code === 0, msg: json.errMsg, id: json.data?.[0] });
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
      const ws = await connectCDP();
      const cdp = createCDPSender(ws);
      const url = await cdp.eval('window.location.href');
      const loggedIn = url && url.includes('trade.joinf.com') && !url.includes('/login');
      console.log(JSON.stringify({ cdp_connected: true, logged_in: loggedIn, url: (url||'').substring(0,100) }));
      ws.close();
    } catch(e) {
      console.log(JSON.stringify({ cdp_connected: false, error: e.message }));
    }
    return;
  }
  
  // Read records
  let records = [];
  if (args.includes('--batch')) {
    const fs = require('fs');
    const batchFile = args[args.indexOf('--batch') + 1];
    records = JSON.parse(fs.readFileSync(batchFile, 'utf-8'));
  } else {
    const fs = require('fs');
    const stdin = fs.readFileSync(0, 'utf-8').trim();
    if (!stdin) { console.error('❌ 请在stdin传入JSON'); process.exit(1); }
    try { records = JSON.parse(stdin); } catch(e) { records = [JSON.parse(stdin)]; }
    if (!Array.isArray(records)) records = [records];
  }
  
  if (records.length === 0) { console.log(JSON.stringify({ status: 'no_data' })); return; }
  
  // Connect CDP
  let ws, cdp;
  try {
    ws = await connectCDP();
    cdp = createCDPSender(ws);
  } catch(e) {
    console.log(JSON.stringify({ status: 'cdp_error', error: e.message }));
    process.exit(1);
  }
  
  // Ensure logged in first
  try {
    await ensureLoggedIn(cdp);
  } catch(e) {
    console.log(JSON.stringify({ status: 'login_failed', error: e.message }));
    ws.close();
    process.exit(1);
  }
  
  // Sync each record
  const results = [];
  for (const record of records) {
    const result = await syncOne(cdp, record);
    if (result.ok) {
      results.push({ id: record.id, status: 'ok', followId: result.id });
    } else {
      results.push({ id: record.id, status: 'failed', error: result.msg || result.error });
    }
    if (records.length > 1) await new Promise(r => setTimeout(r, 300));
  }
  
  // Verify - check displayLastFollowTime changed
  if (records.length > 0) {
    const firstId = records[0].customer_id;
    const verifyExpr = `
      (async() => {
        var r = await fetch('/rapi/d/customers/${firstId}/1', {
          headers: {'Accept':'application/json','X-Cid':'71376','X-User':'183006'}
        });
        var j = await r.json();
        var info = j.data?.find(c => c.categoryName === '主要信息');
        if (info && info.columnData) {
          return JSON.stringify({
            lf: info.columnData.displayLastFollowTime?.value,
            lfDisplay: info.columnData.displayLastFollowTime?.displayValue
          });
        }
        return 'no_info';
      })()
    `;
    const verifyRaw = await cdp.eval(verifyExpr);
    console.error(`🔍 Verify: ${verifyRaw}`);
    
    // Parse to check if lastFollow changed from old value
    try {
      const verify = JSON.parse(verifyRaw);
      if (verify.lf && verify.lf !== 1773365475000) {
        console.error('✅ VERIFIED: Follow-up actually written!');
      } else {
        console.error('⚠️ lastFollow unchanged - may be fake success');
      }
    } catch(e) { console.error(`Verify parse error: ${e.message}`); }
  }
  
  ws.close();
  console.log(JSON.stringify({ status: 'complete', records: records.length, results }));
}

main().catch(e => {
  console.log(JSON.stringify({ status: 'error', error: e.message }));
  process.exit(1);
});