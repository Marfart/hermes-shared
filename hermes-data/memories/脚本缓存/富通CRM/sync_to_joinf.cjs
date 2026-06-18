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

const CDP_URL = 'ws://127.0.0.1:9226/devtools/page/7829F8F43F458721D9637BA8A9CBE8C8';
const PAGE_URL = 'https://trade.joinf.com/tms/customer/customers?type=search&tab=0';

const COLOR_MAP = { '邮件': '2B579A', 'WhatsApp': '27AE60', '报价': 'E67E22', '电话': '8E44AD', '会议': '9B59B6' };
const METHOD_MAP = { '邮件': '邮件', 'WhatsApp': 'WhatsApp', '电话': '电话', '会议': '会议' };

function connectCDP() {
  return new Promise((resolve, reject) => {
    const ws = new WebSocket(CDP_URL);
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
               displayOriginalValue:${customer_id},displayValue:${JSON.stringify(record.customer_name || '')},originalValue:"",value:${customer_id}},
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
      const ws = await connectCDP();
      const cdp = createCDPSender(ws);
      const url = await cdp.eval('window.location.href');
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
  
  // Read records from stdin (one JSON per line)
  let records = [];
  
  if (args.includes('--batch')) {
    const fs = require('fs');
    const batchFile = args[args.indexOf('--batch') + 1];
    const raw = fs.readFileSync(batchFile, 'utf-8');
    records = JSON.parse(raw);
  } else {
    // Read stdin
    const stdin = fs.readFileSync(0, 'utf-8').trim();
    if (!stdin) {
      console.error('❌ 请在stdin传入JSON数据');
      process.exit(1);
    }
    // Try parsing as array or single object
    try { records = JSON.parse(stdin); } catch(e) { records = [JSON.parse(stdin)]; }
    if (!Array.isArray(records)) records = [records];
  }
  
  if (records.length === 0) {
    console.log(JSON.stringify({ status: 'no_data' }));
    return;
  }
  
  // Check CDP first
  let ws, cdp;
  try {
    ws = await connectCDP();
    cdp = createCDPSender(ws);
  } catch(e) {
    console.log(JSON.stringify({ status: 'cdp_error', error: e.message }));
    process.exit(1);
  }
  
  // Navigate to ensure session is fresh
  await cdp.send('Page.navigate', { url: PAGE_URL });
  await new Promise(r => setTimeout(r, 3000));
  
  const results = [];
  for (const record of records) {
    const result = await syncOne(cdp, record);
    
    if (result.ok) {
      results.push({ id: record.id, status: 'ok' });
    } else {
      results.push({ id: record.id, status: 'failed', error: result.msg || result.error });
    }
    
    if (records.length > 1) await new Promise(r => setTimeout(r, 300));
  }
  
  ws.close();
  
  // Output JSON result
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