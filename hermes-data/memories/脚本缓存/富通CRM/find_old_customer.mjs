import { writeFileSync } from 'fs';

async function getCDPUrl() {
  const resp = await fetch('http://127.0.0.1:9226/json');
  const pages = await resp.json();
  const target = pages.find(p => p.url && p.url.includes('trade.joinf.com')) || pages.find(p => p.url && !p.url.startsWith('devtools'));
  return target ? target.webSocketDebuggerUrl : pages[0].webSocketDebuggerUrl;
}

async function main() {
  const cdpUrl = await getCDPUrl();
  console.log('CDP URL:', cdpUrl);
  
  const WebSocket = (await import('ws')).default;
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
  
  async function evalPage(expr) {
    const r = await send({ method: 'Runtime.evaluate', params: { expression: expr, returnByValue: true, awaitPromise: true, timeout: 15000 } });
    if (r.result?.exceptionDetails) throw new Error(JSON.stringify(r.result.exceptionDetails));
    return r.result?.result?.value;
  }
  
  // 先搜索客户列表，按创建时间倒序找一个老一些的客户
  console.log('搜索老一些的客户...');
  const result = await evalPage(`
    (async () => {
      try {
        // 搜索所有条件，找到2022年左右的客户
        const resp = await fetch('/rapi/d/customers?num=1&paging=true&size=20', {
          headers: { 'X-Cid': '71376', 'X-User': '183006', 'Accept': 'application/json' }
        });
        const json = await resp.json();
        const vals = json.data.values || [];
        // 挑一个createTime在2021-2022年的客户
        const oldCustomers = vals.filter(v => {
          const ct = v.createTime || v.create_at || '';
          return ct.startsWith('2021') || ct.startsWith('2022');
        });
        if (oldCustomers.length > 0) {
          const pick = oldCustomers[0];
          return JSON.stringify({
            found: true,
            count: oldCustomers.length,
            customer: {
              id: pick.id || pick.customerId,
              name: pick.dataName || pick.companyName,
              contactName: pick.contactName || '',
              createTime: pick.createTime || '',
              country: pick.countryName || ''
            }
          });
        }
        // 没有找到就返回最早的一条
        const last = vals[vals.length - 1] || vals[0];
        return JSON.stringify({
          found: false,
          customer: last ? {
            id: last.id || last.customerId,
            name: last.dataName || last.companyName,
            contactName: last.contactName || '',
            createTime: last.createTime || '',
            country: last.countryName || ''
          } : null,
          totalCount: vals.length
        });
      } catch(e) {
        return JSON.stringify({ error: e.message });
      }
    })()
  `);
  console.log(result);
  
  ws.close();
}

main().catch(console.error);
