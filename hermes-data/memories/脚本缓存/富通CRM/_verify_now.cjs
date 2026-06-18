const WebSocket = require('ws');
const http = require('http');

function findPage() {
  return new Promise((resolve, reject) => {
    http.get('http://127.0.0.1:9226/json', (res) => {
      let d = '';
      res.on('data', c => d += c);
      res.on('end', () => {
        const pages = JSON.parse(d);
        let p = pages.find(x => x.url.includes('trade.joinf.com') && !x.url.includes('/login'));
        if (!p) p = pages[0];
        resolve({ wsUrl: p.webSocketDebuggerUrl, url: p.url });
      });
    }).on('error', reject);
  });
}

async function main() {
  const { wsUrl } = await findPage();
  const ws = new WebSocket(wsUrl);
  await new Promise((res, rej) => { ws.on('open', res); ws.on('error', rej); setTimeout(() => rej('timeout'),10000); });
  
  let mid = 0;
  const pending = {};
  ws.on('message', (d) => { const r = JSON.parse(d.toString()); if (r.id && pending[r.id]) { pending[r.id](r); delete pending[r.id]; } });
  const send = (m, p) => new Promise(r => { const id = ++mid; pending[id] = r; ws.send(JSON.stringify({ id, method: m, params: p })); });
  const js = async (e) => { const r = await send('Runtime.evaluate', { expression: e, returnByValue: true, awaitPromise: true }); return r.result?.result?.value; };
  
  // Check detail API for each customer
  const ids = [229629960, 229679705, 229629827, 229623037, 229649728];
  const names = ['Juan Carlos', 'Stephen', 'Richard', 'Basem', 'Alex'];
  
  for (let i = 0; i < ids.length; i++) {
    const r = await js(`(async()=>{const r=await fetch('/rapi/d/customers/${ids[i]}/1',{headers:{'Accept':'application/json'}});const j=await r.json();const info=j.data?.find(c=>c.categoryName==='主要信息');if(info?.columnData){const lf=info.columnData.displayLastFollowTime;return JSON.stringify({lfv:lf?.value,lfd:lf?.displayValue,rfv:info.columnData.recentlyFollowTime?.value});}return JSON.stringify({cats:(j.data||[]).map(c=>c.categoryName)});})()`);
    console.error(`${names[i]}(${ids[i]}): ${r}`);
  }
  
  ws.close();
}

main().catch(e => { console.error('ERROR:', e.message); process.exit(1); });