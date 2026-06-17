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
  // Test 1: simple eval
  console.log('Test 1: simple eval');
  const t1 = await send('Runtime.evaluate', {expression: '1+1', returnByValue: true});
  console.log('1+1 =', t1.result?.result?.value);

  // Test 2: check URL
  console.log('\nTest 2: check URL');
  const t2 = await send('Runtime.evaluate', {expression: 'location.href', returnByValue: true});
  console.log('URL:', t2.result?.result?.value);

  // Test 3: async fetch
  console.log('\nTest 3: async fetch');
  const t3 = await send('Runtime.evaluate', {
    expression: '(async function(){ var r = await fetch("/rapi/d/customers/238855638/1", {credentials:"include", headers:{"X-Cid":"71376","X-User":"183006"}}); var j = await r.json(); return JSON.stringify({success:j.success, code:j.code}); })()',
    awaitPromise: true,
    returnByValue: true,
    timeout: 12000
  });
  console.log('Fetch result:', t3.result?.result?.value);
  
  if (t3.result?.result?.value) {
    const parsed = JSON.parse(t3.result.result.value);
    console.log('Parsed:', parsed);
    
    if (parsed.success) {
      // Test 4: PATCH
      console.log('\nTest 4: PATCH update');
      const patchBody = {
        id: 238855638,
        models: [
          {columnName:"name",value:"Test Customer XMA",displayValue:"Test Customer XMA",originalValue:"Test Customer XMA",displayOriginalValue:"Test Customer XMA"},
          {columnName:"description",value:"HERMES_PATCH_OK",displayValue:"HERMES_PATCH_OK",originalValue:"HERMES_API_TEST_20260617_090921",displayOriginalValue:"HERMES_API_TEST_20260617_090921"},
          {columnName:"displayType",value:"潜在工业客户",displayValue:"潜在工业客户",originalValue:"236496",displayOriginalValue:"236496"}
        ],
        contacts: [],
        banks: [],
        customerAttachmentDtoList: [],
        tagList: [],
        markModel: {isChanged:true,customerId:238855638,companyId:71376,operatorId:183006}
      };
      
      const t4 = await send('Runtime.evaluate', {
        expression: `(async function(){ var r = await fetch("/rapi/d/customer", {method:"PATCH",credentials:"include",headers:{"Content-Type":"application/json","X-Cid":"71376","X-User":"183006"},body:JSON.stringify(${JSON.stringify(patchBody)})}); var j = await r.json(); return JSON.stringify({success:j.success,code:j.code,errMsg:j.errMsg}); })()`,
        awaitPromise: true,
        returnByValue: true,
        timeout: 12000
      });
      console.log('PATCH result:', t4.result?.result?.value);
      
      // Test 5: restore
      console.log('\nTest 5: restore');
      patchBody.models[1].value = "HERMES_API_TEST_20260617_090921";
      patchBody.models[1].displayValue = "HERMES_API_TEST_20260617_090921";
      
      const t5 = await send('Runtime.evaluate', {
        expression: `(async function(){ var r = await fetch("/rapi/d/customer", {method:"PATCH",credentials:"include",headers:{"Content-Type":"application/json","X-Cid":"71376","X-User":"183006"},body:JSON.stringify(${JSON.stringify(patchBody)})}); var j = await r.json(); return JSON.stringify({success:j.success,code:j.code,errMsg:j.errMsg}); })()`,
        awaitPromise: true,
        returnByValue: true,
        timeout: 12000
      });
      console.log('Restore result:', t5.result?.result?.value);
    }
  }

  // Save results
  fs.writeFileSync('C:/Users/Admin/Desktop/e2e_results.json', JSON.stringify({
    t1: t1.result?.result?.value,
    t2: t2.result?.result?.value,
    t3: t3.result?.result?.value,
    time: new Date().toISOString()
  }, null, 2));
  
  ws.close();
}

ws.on('open', () => {
  run().then(() => {
    console.log('\nDone!');
    process.exit(0);
  }).catch(e => {
    console.error('Run error:', e);
    process.exit(1);
  });
});

setTimeout(() => { console.log('Global timeout'); process.exit(1); }, 60000);
