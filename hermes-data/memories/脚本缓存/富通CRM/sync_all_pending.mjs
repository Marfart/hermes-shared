/**
 * sync_all_pending.mjs - Sync all pending follow-ups to JoinF CRM
 */
import { readFileSync, writeFileSync } from 'fs';
import WebSocket from 'ws';

// Get the actual page from /json endpoint
async function getCDPUrl() {
  const resp = await fetch('http://127.0.0.1:9226/json');
  const pages = await resp.json();
  const target = pages.find(p => p.url && !p.url.startsWith('devtools')) || pages[0];
  return target.webSocketDebuggerUrl;
}
const PENDING_FILE = 'C:/Users/Admin/AppData/Local/hermes/memories/脚本缓存/富通CRM/pending_sync.json';

const COLOR_MAP = { '邮件': '2B579A', '报价': 'E67E22', 'WhatsApp': '27AE60', '电话': 'E74C3C', '跟进': 'fe4145' };
const METHOD_MAP = { '邮件': '邮件', 'WhatsApp': 'WhatsApp', '电话': '电话', '报价': '跟进', '跟进': '' };

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
    const created = rec.created_at || new Date().toLocaleString('zh-CN', { hour12: false });

    process.stdout.write(`  #${rec.id} [${type}] ${content.substring(0, 45)}... `);

    try {
      // Build the payload manually to avoid template issues
      const models = [
        { columnDisplayName: "Customer Name", columnName: "dataName", dict: false, displayOriginalValue: cid, displayValue: "", originalValue: "", value: cid },
        { columnDisplayName: "Contact Name", columnName: "dataContactName", dict: false, displayOriginalValue: "", displayValue: "", originalValue: "", value: null },
        { columnDisplayName: "Content", columnName: "contactContent", dict: false, displayOriginalValue: "", displayValue: "", originalValue: "", value: content },
        { columnDisplayName: "Attachment", columnName: "annex", dict: false, displayOriginalValue: "", displayValue: "", originalValue: "", value: null },
        { columnDisplayName: "Color", columnName: "bgColor", dict: false, displayOriginalValue: "", displayValue: "", originalValue: "", value: color },
        { columnDisplayName: "Follow Method", columnName: "method", dict: true, displayOriginalValue: "", displayValue: "", originalValue: "", value: method },
        { columnDisplayName: "Planning Time", columnName: "planningTime", dict: false, displayOriginalValue: "", displayValue: "", originalValue: "", value: created },
        { columnDisplayName: "Step", columnName: "step", dict: true, displayOriginalValue: "", displayValue: "", originalValue: "", value: null },
        { columnDisplayName: "Next Remind Time", columnName: "nextRemindTime", dict: false, displayOriginalValue: "", displayValue: "", originalValue: "", value: null },
        { columnDisplayName: "Repeat Cycle", columnName: "repeatCycle", dict: false, displayOriginalValue: "", displayValue: "", originalValue: "", value: null },
        { columnDisplayName: "Relevant", columnName: "relevant", dict: false, displayOriginalValue: "", displayValue: "", originalValue: "", value: null },
        { columnDisplayName: "Operator", columnName: "operatorName", dict: false, displayOriginalValue: "", displayValue: "", originalValue: "", value: null },
        { columnDisplayName: "Feedback Operator", columnName: "feedbackOperator", dict: false, displayOriginalValue: "", displayValue: "", originalValue: "", value: "183006" }
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

  // Write back status
  writeFileSync(PENDING_FILE, JSON.stringify(raw, null, 2), 'utf-8');
  console.log(`\n📊 结果: ${success} ✅ 成功, ${fail} ❌ 失败`);
  ws.close();
}

main().catch(e => { console.error('FATAL:', e); process.exit(1); });