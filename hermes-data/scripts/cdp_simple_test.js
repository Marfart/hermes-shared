const WebSocket = require('ws');
const fs = require('fs');
const ws = new WebSocket('ws://127.0.0.1:9223/devtools/page/B3F8DF7A128D390FFDD0095560E37D7F');
let msgId = 0;
const pending = new Map();

function send(method, params) {
  return new Promise((resolve) => {
    const id = ++msgId;
    pending.set(id, resolve);
    ws.send(JSON.stringify({id, method, params}));
  });
}

ws.on('message', (data) => {
  const r = JSON.parse(data);
  if (r.id && pending.has(r.id)) {
    pending.get(r.id)(r);
    pending.delete(r.id);
  }
});

ws.on('open', async () => {
  try {
    // 简单测试：读取客户
    console.log('=== Test: Simple read ===');
    const expr = [
      '(async function(){',
      'try{',
      'var r=await fetch("/rapi/d/customers/238855638/1",{credentials:"include",headers:{"X-Cid":"71376","X-User":"183006"}});',
      'var j=await r.json();',
      'return "success="+j.success+" code="+j.code;',
      '}catch(e){return "error:"+e.message;}',
      '})()'
    ].join('');
    
    const r1 = await send('Runtime.evaluate', {
      expression: expr,
      awaitPromise: true,
      returnByValue: true,
      timeout: 10000
    });
    console.log('Result:', JSON.stringify(r1.result?.result));

  } catch(e) { console.error(e); }
  ws.close();
});
ws.on('error', e => { console.error(e.message); process.exit(1); });
setTimeout(() => { process.exit(0); }, 15000);
