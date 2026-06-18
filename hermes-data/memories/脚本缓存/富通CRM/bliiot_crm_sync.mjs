/**
 * BLIIOT CRM → JoinF CRM Sync Tool
 * 
 * Reads pending follow-up records from local SQLite DB
 * and syncs them to JoinF CRM via CDP browser API.
 * 
 * Usage:
 *   node bliiot_crm_sync.mjs                          # Sync all pending
 *   node bliiot_crm_sync.mjs --customer 235327923      # Sync specific customer
 *   node bliiot_crm_sync.mjs --watch                   # Watch mode
 *   node bliiot_crm_sync.mjs --status                  # Show sync status
 */

import { createRequire } from 'module';
import Database from 'better-sqlite3';
import WebSocket from 'ws';
import { readFileSync, existsSync } from 'fs';

const DB_PATH = process.env.LOCALAPPDATA + '/hermes/memories/脚本缓存/富通CRM/crm_followups.db';
const CDP_URL = 'ws://127.0.0.1:9226/devtools/page/7829F8F43F458721D9637BA8A9CBE8C8';

let CDP_SEND = null;

async function connectCDP() {
  const ws = new WebSocket(CDP_URL);
  await new Promise((resolve, reject) => {
    ws.on('open', resolve);
    ws.on('error', reject);
  });
  
  let msgId = 0;
  function send(msg) {
    return new Promise((resolve) => {
      msg.id = ++msgId;
      const handler = (data) => {
        const resp = JSON.parse(data.toString());
        if (resp.id === msg.id) {
          ws.removeListener('message', handler);
          resolve(resp);
        }
      };
      ws.on('message', handler);
      ws.send(JSON.stringify(msg));
    });
  }
  
  // Navigate to customer page first to establish session
  await send({ method: 'Page.navigate', params: { url: 'https://trade.joinf.com/tms/customer/customers?type=search&tab=0' } });
  await new Promise(r => setTimeout(r, 4000));
  
  return { ws, send };
}

async function syncFollowupToJoinf(send, followup) {
  const { customer_id, content, type, id, created_at } = followup;
  
  // Format content with type prefix
  const fullContent = `[${type}] ${content}`;
  
  try {
    const result = await send({
      method: 'Runtime.evaluate',
      params: {
        expression: `
          (async () => {
            try {
              const resp = await fetch('/rapi/m/follow/add', {
                method: 'POST',
                headers: { 
                  'X-Cid': '71376', 
                  'X-User': '183006', 
                  'Content-Type': 'application/json',
                  'Accept': 'application/json'
                },
                body: JSON.stringify({
                  id: "",
                  attachmentList: [],
                  businessStep: 0,
                  customerStep: 0,
                  completeNoRemind: 0,
                  cycleEndDay: "",
                  cycleStartDay: "",
                  cycleId: "",
                  dataType: 0,
                  currentDoneFlag: 0,
                  models: [
                    { columnDisplayName: "Customer Name", columnName: "dataName", dict: false, displayOriginalValue: ${customer_id}, displayValue: ${JSON.stringify(followup.customer_name || '')}, originalValue: "", value: ${customer_id} },
                    { columnDisplayName: "Contact Name", columnName: "dataContactName", dict: false, displayOriginalValue: "", displayValue: "", originalValue: "", value: null },
                    { columnDisplayName: "Content", columnName: "contactContent", dict: false, displayOriginalValue: "", displayValue: "", originalValue: "", value: ${JSON.stringify(fullContent)} },
                    { columnDisplayName: "Attachment", columnName: "annex", dict: false, displayOriginalValue: "", displayValue: "", originalValue: "", value: null },
                    { columnDisplayName: "Color", columnName: "bgColor", dict: false, displayOriginalValue: "", displayValue: "", originalValue: "", value: ${type === '邮件' ? '"2B579A"' : type === '报价' ? '"E67E22"' : type === 'WhatsApp' ? '"27AE60"' : '"fe4145"'} },
                    { columnDisplayName: "Follow Method", columnName: "method", dict: true, displayOriginalValue: "", displayValue: "", originalValue: "", value: ${type === '邮件' ? '"邮件"' : type === 'WhatsApp' ? '"WhatsApp"' : type === '电话' ? '"电话"' : '""'} },
                    { columnDisplayName: "Planning Time", columnName: "planningTime", dict: false, displayOriginalValue: "", displayValue: "", originalValue: "", value: ${JSON.stringify(created_at)} },
                    { columnDisplayName: "Step", columnName: "step", dict: true, displayOriginalValue: "", displayValue: "", originalValue: "", value: null },
                    { columnDisplayName: "Next Remind Time", columnName: "nextRemindTime", dict: false, displayOriginalValue: "", displayValue: "", originalValue: "", value: null },
                    { columnDisplayName: "Repeat Cycle", columnName: "repeatCycle", dict: false, displayOriginalValue: "", displayValue: "", originalValue: "", value: null },
                    { columnDisplayName: "Relevant", columnName: "relevant", dict: false, displayOriginalValue: "", displayValue: "", originalValue: "", value: null },
                    { columnDisplayName: "Operator", columnName: "operatorName", dict: false, displayOriginalValue: "", displayValue: "", originalValue: "", value: null },
                    { columnDisplayName: "Feedback Operator", columnName: "feedbackOperator", dict: false, displayOriginalValue: "", displayValue: "", originalValue: "", value: "183006" }
                  ],
                  relevantList: [{ relevantId: "", relevant: "" }],
                  flowStep: "",
                  forceRefresh: true,
                  followType: "",
                  followObject: ""
                })
              });
              const json = await resp.json();
              return JSON.stringify({ ok: json.success, data: json.data, msg: json.errMsg });
            } catch(e) { return JSON.stringify({ ok: false, error: e.message }); }
          })()
        `,
        returnByValue: true,
        awaitPromise: true
      }
    });
    
    const response = JSON.parse(result.result.result.value);
    return response;
  } catch (e) {
    return { ok: false, error: e.message };
  }
}

async function main() {
  const args = process.argv.slice(2);
  const flag = args[0] || 'sync';
  
  const db = new Database(DB_PATH);
  
  if (flag === '--status') {
    const pending = db.prepare("SELECT COUNT(*) as c FROM followups WHERE synced=0").get();
    const synced = db.prepare("SELECT COUNT(*) as c FROM followups WHERE synced=1").get();
    const total = db.prepare("SELECT COUNT(*) as c FROM followups").get();
    console.log(JSON.stringify({ total: total.c, pending: pending.c, synced: synced.c }, null, 2));
    db.close();
    return;
  }
  
  // Get pending records
  let records;
  if (args.includes('--customer')) {
    const cid = parseInt(args[args.indexOf('--customer') + 1]);
    records = db.prepare("SELECT * FROM followups WHERE customer_id=? AND synced=0 ORDER BY created_at ASC").all(cid);
  } else {
    records = db.prepare("SELECT * FROM followups WHERE synced=0 ORDER BY created_at ASC").all();
  }
  
  if (records.length === 0) {
    console.log('✅ 没有待同步的记录');
    db.close();
    return;
  }
  
  console.log(`📤 准备同步 ${records.length} 条跟进记录到富通CRM...`);
  
  // Connect to CDP
  console.log('🔗 连接CDP浏览器...');
  const { ws, send } = await connectCDP();
  CDP_SEND = send;
  
  let successCount = 0;
  let failCount = 0;
  
  for (const record of records) {
    process.stdout.write(`  📝 同步记录 #${record.id} [${record.type}] ${record.content.substring(0, 40)}... `);
    
    const result = await syncFollowupToJoinf(send, record);
    
    if (result.ok) {
      // Mark as synced
      db.prepare("UPDATE followups SET synced=1, joinf_follow_id=? WHERE id=?").run(String(result.data || ''), record.id);
      db.prepare("INSERT INTO sync_log (followup_id, customer_id, action, status, message) VALUES (?, ?, 'synced', 'success', ?)")
        .run(record.id, record.customer_id, JSON.stringify(result));
      console.log('✅');
      successCount++;
    } else {
      db.prepare("INSERT INTO sync_log (followup_id, customer_id, action, status, message) VALUES (?, ?, 'sync_failed', 'failed', ?)")
        .run(record.id, record.customer_id, result.error || result.msg || 'unknown');
      console.log(`❌ ${result.error || result.msg}`);
      failCount++;
    }
    
    // Delay between records
    await new Promise(r => setTimeout(r, 500));
  }
  
  console.log(`\n📊 同步完成: ${successCount} 成功, ${failCount} 失败`);
  
  ws.close();
  db.close();
}

main().catch(e => {
  console.error('FATAL:', e);
  process.exit(1);
});