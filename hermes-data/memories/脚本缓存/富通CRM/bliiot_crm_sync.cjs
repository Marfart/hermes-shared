/**
 * BLIIOT CRM → JoinF CRM Sync Tool (Node.js via CDP)
 * 
 * Reads pending follow-up records from local SQLite DB
 * and syncs them to JoinF CRM via CDP browser JavaScript evaluation.
 * 
 * Prerequisites: CDP browser must be running on port 9226 with joinf.com logged in
 */

const Database = require('better-sqlite3');
const WebSocket = require('ws');

const args = process.argv.slice(2);
const flag = args[0] || 'sync';

const DB_PATH = process.env.LOCALAPPDATA + '/hermes/memories/脚本缓存/富通CRM/crm_followups.db';
const CDP_URL = 'ws://127.0.0.1:9226/devtools/page/7829F8F43F458721D9637BA8A9CBE8C8';

let db;
try {
  db = new Database(DB_PATH);
} catch(e) {
  console.error('❌ 无法打开数据库:', e.message);
  console.error('   路径:', DB_PATH);
  process.exit(1);
}

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
  
  return { ws, send };
}

async function evalInPage(send, expression) {
  const result = await send({
    method: 'Runtime.evaluate',
    params: { expression, returnByValue: true, awaitPromise: true }
  });
  return result.result.result.value;
}

async function syncRecord(send, record) {
  const { id, customer_id, content, type, created_at } = record;
  const fullContent = `[${type}] ${content}`;
  
  // Color mapping
  const colorMap = { '邮件': '"2B579A"', 'WhatsApp': '"27AE60"', '报价': '"E67E22"', '电话': '"8E44AD"', '会议': '"9B59B6"' };
  const defaultColor = '"fe4145"';
  const bgColor = colorMap[type] || defaultColor;
  
  // Method mapping
  const methodMap = { '邮件': '"邮件"', 'WhatsApp': '"WhatsApp"', '电话': '"电话"', '会议': '"会议"' };
  const method = methodMap[type] || '""';
  
  const expr = `
    (async () => {
      try {
        const resp = await fetch('/rapi/m/follow/add', {
          method: 'POST',
          headers: { 
            'X-Cid': '71376', 'X-User': '183006', 
            'Content-Type': 'application/json', 'Accept': 'application/json'
          },
          body: JSON.stringify({
            id: "", attachmentList: [], businessStep: 0, customerStep: 0,
            completeNoRemind: 0, cycleEndDay: "", cycleStartDay: "", cycleId: "",
            dataType: 0, currentDoneFlag: 0,
            models: [
              { columnDisplayName: "Customer Name", columnName: "dataName", dict: false, displayOriginalValue: ${customer_id}, displayValue: "", originalValue: "", value: ${customer_id} },
              { columnDisplayName: "Contact Name", columnName: "dataContactName", dict: false, displayOriginalValue: "", displayValue: "", originalValue: "", value: null },
              { columnDisplayName: "Content", columnName: "contactContent", dict: false, displayOriginalValue: "", displayValue: "", originalValue: "", value: ${JSON.stringify(fullContent)} },
              { columnDisplayName: "Attachment", columnName: "annex", dict: false, displayOriginalValue: "", displayValue: "", originalValue: "", value: null },
              { columnDisplayName: "Color", columnName: "bgColor", dict: false, displayOriginalValue: "", displayValue: "", originalValue: "", value: ${bgColor} },
              { columnDisplayName: "Follow Method", columnName: "method", dict: true, displayOriginalValue: "", displayValue: "", originalValue: "", value: ${method} },
              { columnDisplayName: "Planning Time", columnName: "planningTime", dict: false, displayOriginalValue: "", displayValue: "", originalValue: "", value: ${JSON.stringify(created_at)} },
              { columnDisplayName: "Step", columnName: "step", dict: true, displayOriginalValue: "", displayValue: "", originalValue: "", value: null },
              { columnDisplayName: "Next Remind Time", columnName: "nextRemindTime", dict: false, displayOriginalValue: "", displayValue: "", originalValue: "", value: null },
              { columnDisplayName: "Repeat Cycle", columnName: "repeatCycle", dict: false, displayOriginalValue: "", displayValue: "", originalValue: "", value: null },
              { columnDisplayName: "Relevant", columnName: "relevant", dict: false, displayOriginalValue: "", displayValue: "", originalValue: "", value: null },
              { columnDisplayName: "Operator", columnName: "operatorName", dict: false, displayOriginalValue: "", displayValue: "", originalValue: "", value: null },
              { columnDisplayName: "Feedback Operator", columnName: "feedbackOperator", dict: false, displayOriginalValue: "", displayValue: "", originalValue: "", value: "183006" }
            ],
            relevantList: [{ relevantId: "", relevant: "" }],
            flowStep: "", forceRefresh: true, followType: "", followObject: ""
          })
        });
        const json = await resp.json();
        return JSON.stringify({ ok: json.success || json.code === 0, data: json.data, msg: json.errMsg });
      } catch(e) { return JSON.stringify({ ok: false, error: e.message }); }
    })()
  `;
  
  const raw = await evalInPage(send, expr);
  return JSON.parse(raw);
}

async function main() {
  if (flag === '--status') {
    const pending = db.prepare("SELECT COUNT(*) as c FROM followups WHERE synced=0").get();
    const synced = db.prepare("SELECT COUNT(*) as c FROM followups WHERE synced=1").get();
    const total = db.prepare("SELECT COUNT(*) as c FROM followups").get();
    console.log(`总记录: ${total.c} | 已同步: ${synced.c} | 待同步: ${pending.c}`);
    db.close();
    return;
  }
  
  if (flag === '--latest') {
    const limit = parseInt(args[1] || '10');
    const rows = db.prepare(`SELECT f.*, c.customer_name, c.region 
      FROM followups f LEFT JOIN customer_cache c ON f.customer_id = c.customer_id 
      ORDER BY f.created_at DESC LIMIT ?`).all(limit);
    console.log(`\n📋 最近 ${rows.length} 条跟进记录:\n`);
    for (const r of rows) {
      console.log(`  [#${r.id}] ${r.created_at} | ${r.type} | ${r.customer_name || 'ID:'+r.customer_id}`);
      console.log(`         ${r.content.replace(/\n/g, ' ').substring(0, 150)}`);
      console.log(`         同步: ${r.synced ? '✅' : '⏳'} | 操作: ${r.operator}`);
      console.log();
    }
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
  let cdp;
  try {
    cdp = await connectCDP();
  } catch(e) {
    console.error('❌ CDP连接失败:', e.message);
    console.error('   请确保Chrome CDP 9226端口已打开且已登录富通');
    db.close();
    process.exit(1);
  }
  
  const { ws, send } = cdp;
  
  // First navigate to the customer list to refresh session
  await evalInPage(send, "window.location.href");
  
  let successCount = 0;
  let failCount = 0;
  
  for (const record of records) {
    const preview = record.content.replace(/\n/g, ' ').substring(0, 40);
    process.stdout.write(`  📝 #${record.id} [${record.type}] ${preview}... `);
    
    const result = await syncRecord(send, record);
    
    if (result.ok) {
      db.prepare("UPDATE followups SET synced=1, joinf_follow_id=? WHERE id=?").run(String(result.data || ''), record.id);
      db.prepare("INSERT INTO sync_log (followup_id, customer_id, action, status, message) VALUES (?, ?, 'sync', 'success', ?)")
        .run(record.id, record.customer_id, JSON.stringify(result));
      console.log('✅');
      successCount++;
    } else {
      db.prepare("INSERT INTO sync_log (followup_id, customer_id, action, status, message) VALUES (?, ?, 'sync', 'failed', ?)")
        .run(record.id, record.customer_id, result.error || result.msg || 'unknown');
      console.log(`❌ ${(result.error || result.msg || '').substring(0, 50)}`);
      failCount++;
    }
    
    await new Promise(r => setTimeout(r, 300));
  }
  
  console.log(`\n📊 同步完成: ${successCount} 成功, ${failCount} 失败`);
  
  ws.close();
  db.close();
}

main().catch(e => {
  console.error('FATAL:', e);
  process.exit(1);
});