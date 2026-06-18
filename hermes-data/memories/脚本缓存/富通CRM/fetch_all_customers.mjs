import { writeFileSync } from 'fs';
import WebSocket from 'ws';

const CDP_URL = 'ws://127.0.0.1:9226/devtools/page/7829F8F43F458721D9637BA8A9CBE8C8';
const OUTPUT_FILE = 'C:/Users/Admin/AppData/Local/hermes/memories/脚本缓存/富通CRM/all_customers_raw.json';
const PAGE_SIZE = 200;

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
        if (resp.id === msg.id) { ws.removeListener('message', handler); resolve(resp); }
      };
      ws.on('message', handler);
      ws.send(JSON.stringify(msg));
    });
  }
  return { ws, send };
}

async function evalPage(send, expr) {
  const r = await send({ method: 'Runtime.evaluate', params: { expression: expr, returnByValue: true, awaitPromise: true } });
  return r.result.result.value;
}

async function fetchPage(send, pageNum) {
  const raw = await evalPage(send, `
    (async () => {
      try {
        const resp = await fetch('/rapi/d/customers?num=${pageNum}&paging=true&size=${PAGE_SIZE}', {
          headers: { 'X-Cid': '71376', 'X-User': '183006', 'Accept': 'application/json' }
        });
        const json = await resp.json();
        const vals = json.data.values || [];
        return JSON.stringify({ ok: true, count: vals.length, data: vals });
      } catch(e) { return JSON.stringify({ ok: false, error: e.message }); }
    })()
  `);
  return JSON.parse(raw);
}

async function main() {
  console.log('Connecting to CDP...');
  const { ws, send } = await connectCDP();

  // Navigate to customer list
  console.log('Loading customer page...');
  await send({ method: 'Page.navigate', params: { url: 'https://trade.joinf.com/tms/customer/customers?type=search&tab=0' } });
  await new Promise(r => setTimeout(r, 4000));

  // Fetch all pages sequentially
  let allCustomers = [];
  let pageNum = 1;
  let emptyPages = 0;

  while (emptyPages < 3) {
    const result = await fetchPage(send, pageNum);
    if (result.ok && result.data && result.data.length > 0) {
      allCustomers.push(...result.data);
      console.log(`Page ${pageNum}: ${result.data.length} customers (total so far: ${allCustomers.length})`);
      pageNum++;
      emptyPages = 0;
      // Small delay
      await new Promise(r => setTimeout(r, 200));
    } else if (result.ok && result.data && result.data.length === 0) {
      console.log(`Page ${pageNum}: empty`);
      emptyPages++;
      pageNum++;
    } else {
      console.log(`Page ${pageNum}: error - ${result.error}`);
      emptyPages++;
      pageNum++;
    }

    if (pageNum > 100) break; // Safety limit
  }

  console.log(`\n=== COMPLETE: ${allCustomers.length} customers fetched ===`);

  // Save
  writeFileSync(OUTPUT_FILE, JSON.stringify(allCustomers, null, 2), 'utf-8');
  console.log(`Saved to ${OUTPUT_FILE}`);

  ws.close();
}

main().catch(e => { console.error('FATAL:', e); process.exit(1); });