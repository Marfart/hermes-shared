/**
 * sync_all_pending.mjs - Sync all pending follow-ups to JoinF CRM
 * Now writes synced status BACK to SQLite after success
 */
import { readFileSync, writeFileSync } from 'fs';
import WebSocket from 'ws';
import Database from 'better-sqlite3';

const PENDING_FILE = 'C:/Users/Admin/AppData/Local/hermes/memories/脚本缓存/富通CRM/pending_sync.json';
const DB_PATH = process.env.LOCALAPPDATA + '/hermes/memories/脚本缓存/富通CRM/crm_followups.db';

async function getCDPUrl() {
  const resp = await fetch('http://127.0.0.1:9226/json');
  const pages = await resp.json();
  const target = pages.find(p => p.url && !p.url.startsWith('devtools')) || pages[0];
  return target.webSocketDebuggerUrl;
}

const COLOR_MAP = { '邮件': '2B579A', '报价': 'E67E22', 'WhatsApp': '27AE60', '电话': 'E74C3C', '跟进': 'fe4145' };
const METHOD_MAP = { '邮件': '邮件', 'WhatsApp': 'WhatsApp', '电话': '电话', '报价': '跟进', '跟进': '' };

async function markSyncedInDB(customerId, followupId) {
  const db = new Database(DB_PATH);
  try {
    db.prepare('UPDATE followups SET synced=1 WHERE id=?').run(followupId);
    console.log(`     📝 SQLite #${followupId} marked synced`);
  } catch(e) {
    console.error(`     ❌ DB error: ${e.message}`);
  } finally {
    db.close();
  }
}

async function main() {
  const cdpUrl = await getCDPUrl();
  console.log('CDP URL:', cdpUrl);

  const raw = JSON.parse(readFileSync(PENDING_FILE, 'utf-8'));
  const pending = raw.filter(r => r.synced === 0);
  console.log(`📤 待同步: ${pending.length} 条记录`);
  if (pending.length === 0) { console.log('✅ 全部已同步'); return; }

  const ws = new WebSocket(cdpUrl);
  await new Promise((resolve, reject) => { ws.on('open', resolve); ws.on('error', reject); });

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

  // Navigate to customer page to establish session
  console.log('📡 导航到客户列表...');
  await send({ method: 'Page.navigate', params: { url: 'https://trade.joinf.com/tms/customer/customers?type=search&tab=0' } });
  await new Promise(r => setTimeout(r, 5000));

  let success = 0, fail = 0;
  for (const rec of pending) {
      const cid = rec.customer_id;
      const type = rec.type || '跟进';
      const color = COLOR_MAP[type] || 'fe4145';
      const method = METHOD_MAP[type] || '';
      const content = `[${type}] ${rec.content || ''}`;
      const created = rec.created_at || new Date().toISOString().replace('T', ' ').substring(0, 19);

      process.stdout.write(`  #${rec.id} [${type}] ${content.substring(0, 45)}... `);

      try {
        const customerName = rec.customer_name || '';
        const models = [
          { columnDisplayName: "Customer Name", columnName: "dataName", dict: false,
            displayOriginalValue: cid, displayValue: customerName, originalValue: "", value: cid },
          { columnDisplayName: "Content", columnName: "contactContent", dict: false,
            displayOriginalValue: "", displayValue: "", originalValue: "", value: content },
          { columnDisplayName: "Color", columnName: "bgColor", dict: false,
            displayOriginalValue: "", displayValue: "", originalValue: "", value: color },
          { columnDisplayName: "Follow Method", columnName: "method", dict: true,
            displayOriginalValue: "", displayValue: "", originalValue: "", value: method },
          { columnDisplayName: "Planning Time", columnName: "planningTime", dict: false,
            displayOriginalValue: "", displayValue: "", originalValue: "", value: created },
          { columnDisplayName: "Feedback Operator", columnName: "feedbackOperator", dict: false,
            displayOriginalValue: "", displayValue: "", originalValue: "", value: "183006" }
        ];
        const payload = JSON.stringify({
          id: "", attachmentList: [], businessStep: 0, customerStep: 0, completeNoRemind: 0,
          cycleEndDay: "", cycleStartDay: "", cycleId: "", dataType: 0, currentDoneFlag: 0,
          models, relevantList: [{ relevantId: "", relevant: "" }],
          flowStep: "", forceRefresh: true, followType: "", followObject: ""
        });

        const expression = `(async () => { try { const r = await fetch('/rapi/m/follow/add', { method: 'POST', headers: { 'X-Cid': '71376', 'X-User': '183006', 'Content-Type': 'application/json', 'Accept': 'application/json' }, body: ${JSON.stringify(payload)} }); const j = await r.json(); return JSON.stringify({ ok: j.success, msg: j.errMsg }); } catch(e) { return JSON.stringify({ ok: false, error: e.message }); } })()`;

        const result = await send({ method: 'Runtime.evaluate', params: { expression, returnByValue: true, awaitPromise: true } });
        const res = JSON.parse(result.result.result.value);

        if (res.ok) {
          console.log('✅');
          rec.synced = 1;
          await markSyncedInDB(cid, rec.id);
          success++;
        } else {
          console.log(`❌ ${res.msg || res.error}`);
          fail++;
        }
      } catch(e) {
        console.log(`❌ ${e.message.substring(0, 60)}`);
        fail++;
      }
      await new Promise(r => setTimeout(r, 600));
  }

  // Write back status to JSON
  writeFileSync(PENDING_FILE, JSON.stringify(raw, null, 2), 'utf-8');
  console.log(`\n📊 结果: ${success} ✅ 成功, ${fail} ❌ 失败`);
  ws.close();
}

main().catch(e => { console.error('FATAL:', e); process.exit(1); });