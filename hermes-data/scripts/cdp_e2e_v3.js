const WebSocket = require('ws');
const fs = require('fs');

const PAGE_ID = 'B3F8DF7A128D390FFDD0095560E37D7F';
const ws = new WebSocket(`ws://127.0.0.1:9223/devtools/page/${PAGE_ID}`);

let msgId = 0;
const pending = new Map();

function send(method, params) {
  return new Promise((resolve, reject) => {
    const id = ++msgId;
    const timer = setTimeout(() => {
      pending.delete(id);
      reject(new Error('timeout for ' + method));
    }, 15000);
    pending.set(id, (r) => { clearTimeout(timer); resolve(r); });
    ws.send(JSON.stringify({id, method, params}));
  });
}

ws.on('message', (data) => {
  try {
    const r = JSON.parse(data);
    if (r.id && pending.has(r.id)) {
      pending.get(r.id)(r);
      pending.delete(r.id);
    }
  } catch(e) {}
});

ws.on('error', (e) => { console.error('WS Error:', e.message); process.exit(1); });

async function run() {
  // Step 1: 导航到工作台（干净页面）
  console.log('Step 1: Navigate to dashboard');
  await send('Page.navigate', {url: 'https://trade.joinf.com/tms/system/index'});
  await new Promise(r => setTimeout(r, 3000));
  
  // Step 2: 简单eval测试
  console.log('Step 2: Simple eval test');
  const t2 = await send('Runtime.evaluate', {expression: 'document.title', returnByValue: true});
  console.log('Title:', t2.result?.result?.value);
  
  // Step 3: 测试fetch（在工作台页面）
  console.log('Step 3: Test fetch from dashboard');
  const t3 = await send('Runtime.evaluate', {
    expression: '(async function(){ try{ var r = await fetch("/rapi/d/customers/238855638/1", {credentials:"include", headers:{"X-Cid":"71376","X-User":"183006"}}); var j = await r.json(); return "success="+j.success+" code="+j.code; }catch(e){ return "ERR:"+e.message; } })()',
    awaitPromise: true,
    returnByValue: true,
    timeout: 12000
  });
  console.log('Fetch:', t3.result?.result?.value);
  
  // Step 4: 导航到客户列表
  console.log('\nStep 4: Navigate to customer list');
  await send('Page.navigate', {url: 'https://trade.joinf.com/tms/customer/customers'});
  await new Promise(r => setTimeout(r, 4000));
  
  const t4 = await send('Runtime.evaluate', {expression: 'document.title + " | " + document.querySelectorAll(".el-table__row").length + " rows"', returnByValue: true});
  console.log('Page:', t4.result?.result?.value);
  
  // Step 5: 从列表页测试fetch
  console.log('Step 5: Fetch from list page');
  const t5 = await send('Runtime.evaluate', {
    expression: '(async function(){ try{ var r = await fetch("/rapi/d/customers/238855638/1", {credentials:"include", headers:{"X-Cid":"71376","X-User":"183006"}}); var j = await r.json(); return "success="+j.success+" code="+j.code; }catch(e){ return "ERR:"+e.message; } })()',
    awaitPromise: true,
    returnByValue: true,
    timeout: 12000
  });
  console.log('Fetch:', t5.result?.result?.value);

  // Save
  fs.writeFileSync('C:/Users/Admin/Desktop/e2e_v2.json', JSON.stringify({
    title: t2.result?.result?.value,
    fetch1: t3.result?.result?.value,
    listPage: t4.result?.result?.value,
    fetch2: t5.result?.result?.value,
    time: new Date().toISOString()
  }, null, 2));
  
  ws.close();
}

ws.on('open', () => {
  run().then(() => { console.log('\nDone!'); process.exit(0); }).catch(e => { console.error(e); process.exit(1); });
});
setTimeout(() => { console.log('Global timeout'); process.exit(1); }, 60000);
