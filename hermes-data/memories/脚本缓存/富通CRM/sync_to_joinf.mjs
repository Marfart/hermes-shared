/**
 * sync_to_joinf.mjs - Sync pending follow-up records to JoinF CRM via CDP
 * Usage: node sync_to_joinf.mjs
 */
import { readFileSync } from 'fs';

const CDP_URL = 'ws://127.0.0.1:9226/devtools/page/7829F8F43F458721D9637BA8A9CBE8C8';

async function connectCDP() {
  const WebSocket = (await import('ws')).default;
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
        if (resp.id === msg.id) { ws.removeListener('message', handler); resolve(resp); }
      };
      ws.on('message', handler);
      ws.send(JSON.stringify(msg));
    });
  }
  return { ws, send };
}

// Color/type mappings
const COLOR_MAP = { '邮件': '"2B579A"', '报价': '"E67E22"', 'WhatsApp': '"27AE60"', '电话': '"E74C3C"' };
const METHOD_MAP = { '邮件': '"邮件"', 'WhatsApp': '"WhatsApp"', '电话': '"电话"', '报价': '"跟进"' };

function buildExpression(rec) {
  const cid = rec.customer_id;
  const content = JSON.stringify(`[${rec.type}] ${rec.content}`);
  const created = JSON.stringify(rec.created_at || new Date().toISOString());
  const color = COLOR_MAP[rec.type] || '"fe4145"';
  const method = METHOD_MAP[rec.type] || '""';
  
  return `
    (async () => {
      try {
        const resp = await fetch('/rapi/m/follow/add', {
          method: 'POST',
          headers: { 'X-Cid': '71376', 'X-User': '183006', 'Content-Type': 'application/json', 'Accept': 'application/json' },
          body: JSON.stringify({
            id: "", attachmentList: [], businessStep: 0, customerStep: 0,
            completeNoRemind: 0, cycleEndDay: "", cycleStartDay: "", cycleId: "",
            dataType: 0, currentDoneFlag: 0,
            models: [
              { columnDisplayName: "Customer Name", columnName: "dataName", dict: false, displayOriginalValue: ${cid}, displayValue: "", originalValue: "", value: ${cid} },
              { columnDisplayName: "Contact Name", columnName: "dataContactName", dict: false, displayOriginalValue: "", displayValue: "", originalValue: "", value: null },
              { columnDisplayName: "Content", columnName: "contactContent", dict: false, displayOriginalValue: "", displayValue: "", originalValue: "", value: ${content} },
              { columnDisplayName: "Attachment", columnName: "annex", dict: false, displayOriginalValue: "", displayValue: "", originalValue: "", value: null },
              { columnDisplayName: "Color", columnName: "bgColor", dict: false, displayOriginalValue: "", displayValue: "", originalValue: "", value: ${color} },
              { columnDisplayName: "Follow Method", columnName: "method", dict: true, displayOriginalValue: "", displayValue: "", originalValue: "", value: ${method} },
              { columnDisplayName: "Planning Time", columnName: "planningTime", dict: false, displayOriginalValue: "", displayValue: "", originalValue: "", value: ${created} },
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
        return JSON.stringify({ ok: json.success, data: json.data, msg: json.errMsg });
      } catch(e) { return JSON.stringify({ ok: false, error: e.message }); }
    })()
  `;
}

async function markSynced(rec) {
  // Update the JSON file to mark as synced
  const filePath = 'C:/Users/Admin/AppData/Local/hermes/memories/脚本缓存/富通CRM/pending_sync.json';
  const all = JSON.parse(readFileSync(filePath, 'utf-8'));
  for (const r of all) {
    if (r.id === rec.id) r.synced = 1;
  }
  // Write back
  const { writeFileSync } = await import('fs');
  writeFileSync(filePath, JSON.stringify(all, null, 2), 'utf-8');
}

async function main() {
  // Read pending records
  const records = JSON.parse(readFileSync('C:/Users/Admin/AppData/Local/hermes/memories/脚本缓存/富通CRM/pending_sync.json', 'utf-8'))
    .filter(r => r.synced === 0);
  
  if (records.length === 0) {
    console.log('✅ 没有待同步的记录');
    return;
  }
  
  console.log(`📤 准备同步 ${records.length} 条记录到富通CRM...`);
  
  // Connect CDP
  console.log('📡 连接CDP浏览器...');
  const { ws, send } = await connectCDP();
  
  // Navigate to establish session
  await send({ method: 'Page.navigate', params: { url: 'https://trade.joinf.com/tms/customer/customers?type=search&tab=0' } });
  await new Promise(r => setTimeout(r, 4000));
  
  let success = 0, fail = 0;
  
  for (const rec of records) {
    process.stdout.write(`  📝 #${rec.id} [${rec.type}] ${(rec.content || '').substring(0, 40)}... `);
    
    try {
      const result = await send({
        method: 'Runtime.evaluate',
        params: { expression: buildExpression(rec), returnByValue: true, awaitPromise: true }
      });
      const res = JSON.parse(result.result.result.value);
      
      if (res.ok) {
        await markSynced(rec);
        console.log('✅');
        success++;
      } else {
        console.log(`❌ ${res.msg || res.error}`);
        fail++;
      }
    } catch(e) {
      console.log(`❌ ${e.message.substring(0, 60)}`);
      fail++;
    }
    
    await new Promise(r => setTimeout(r, 500));
  }
  
  console.log(`\n📊 同步完成: ${success} ✅ 成功, ${fail} ❌ 失败`);
  ws.close();
}

main().catch(e => { console.error('FATAL:', e); process.exit(1); });