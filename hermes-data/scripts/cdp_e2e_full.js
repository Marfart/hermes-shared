const WebSocket = require('ws');
const fs = require('fs');

const PAGE_ID = 'B3F8DF7A128D390FFDD0095560E37D7F';
const ws = new WebSocket(`ws://127.0.0.1:9223/devtools/page/${PAGE_ID}`);

let msgId = 0;
const pending = new Map();

function send(method, params) {
  return new Promise((resolve, reject) => {
    const id = ++msgId;
    const timer = setTimeout(() => { pending.delete(id); reject(new Error('timeout')); }, 15000);
    pending.set(id, (r) => { clearTimeout(timer); resolve(r); });
    ws.send(JSON.stringify({id, method, params}));
  });
}

ws.on('message', (data) => {
  try {
    const r = JSON.parse(data);
    if (r.id && pending.has(r.id)) { pending.get(r.id)(r); pending.delete(r.id); }
  } catch(e) {}
});

ws.on('error', (e) => { console.error('WS Error:', e.message); process.exit(1); });

async function run() {
  const results = {};
  
  // Step 1: 确保在工作台页面
  console.log('Step 1: Navigate to dashboard');
  await send('Page.navigate', {url: 'https://trade.joinf.com/tms/system/index'});
  await new Promise(r => setTimeout(r, 3000));

  // Step 2: 读取客户当前值
  console.log('Step 2: Read customer');
  const r2 = await send('Runtime.evaluate', {
    expression: '(async function(){ var r = await fetch("/rapi/d/customers/238855638/1", {credentials:"include", headers:{"X-Cid":"71376","X-User":"183006"}}); var j = await r.json(); var d = j.data["1"].columnData; return JSON.stringify({name:d.name.value, desc:d.description.value, shortName:d.shortName.value, webSite:d.webSite.value, displayType:d.displayType}); })()',
    awaitPromise: true, returnByValue: true, timeout: 12000
  });
  const current = JSON.parse(r2.result?.result?.value || '{}');
  console.log('Current:', JSON.stringify(current));
  results.read = current;

  // Step 3: PATCH - 用完整模板结构
  console.log('\nStep 3: PATCH test');
  const patchBody = {
    id: 238855638,
    models: [
      {columnName:"name",value:current.name||"",displayValue:current.name||"",originalValue:current.name||"",displayOriginalValue:current.name||""},
      {columnName:"shortName",value:current.shortName||"",displayValue:current.shortName||"",originalValue:current.shortName||"",displayOriginalValue:current.shortName||""},
      {columnName:"description",value:"HERMES_E2E_PATCH_OK",displayValue:"HERMES_E2E_PATCH_OK",originalValue:current.desc||"",displayOriginalValue:current.desc||""},
      {columnName:"webSite",value:current.webSite||"",displayValue:current.webSite||"",originalValue:current.webSite||"",displayOriginalValue:current.webSite||""},
      {columnName:"displayType",value:current.displayType?.value||"潜在工业客户",displayValue:current.displayType?.value||"潜在工业客户",originalValue:current.displayType?.originalValue||"236496",displayOriginalValue:current.displayType?.originalValue||"236496"},
      {columnName:"code",value:"",displayValue:"",originalValue:"",displayOriginalValue:""},
      {columnName:"introduce",value:"",displayValue:"",originalValue:"",displayOriginalValue:""}
    ],
    contacts: [],
    banks: [],
    customerAttachmentDtoList: [],
    tagList: [],
    markModel: {isChanged:true,customerId:238855638,companyId:71376,operatorId:183006}
  };
  
  const r3 = await send('Runtime.evaluate', {
    expression: `(async function(){ var r = await fetch("/rapi/d/customer", {method:"PATCH",credentials:"include",headers:{"Content-Type":"application/json","X-Cid":"71376","X-User":"183006"},body:JSON.stringify(${JSON.stringify(patchBody)})}); var j = await r.json(); return JSON.stringify({success:j.success,code:j.code,errMsg:j.errMsg}); })()`,
    awaitPromise: true, returnByValue: true, timeout: 12000
  });
  console.log('PATCH:', r3.result?.result?.value);
  results.patch = r3.result?.result?.value;

  // Step 4: 恢复原始值
  console.log('\nStep 4: Restore');
  patchBody.models[2].value = current.desc||"";
  patchBody.models[2].displayValue = current.desc||"";
  patchBody.models[2].originalValue = current.desc||"";
  patchBody.models[2].displayOriginalValue = current.desc||"";
  
  const r4 = await send('Runtime.evaluate', {
    expression: `(async function(){ var r = await fetch("/rapi/d/customer", {method:"PATCH",credentials:"include",headers:{"Content-Type":"application/json","X-Cid":"71376","X-User":"183006"},body:JSON.stringify(${JSON.stringify(patchBody)})}); var j = await r.json(); return JSON.stringify({success:j.success,code:j.code,errMsg:j.errMsg}); })()`,
    awaitPromise: true, returnByValue: true, timeout: 12000
  });
  console.log('Restore:', r4.result?.result?.value);
  results.restore = r4.result?.result?.value;

  // Step 5: 添加跟进记录
  console.log('\nStep 5: Add follow record');
  const followBody = {
    id:"",attachmentList:[],businessStep:0,customerStep:0,completeNoRemind:0,
    cycleEndDay:"",cycleStartDay:"",cycleId:"",dataType:0,currentDoneFlag:0,
    models:[
      {columnDisplayName:"Customer Name",columnName:"dataName",dict:false,displayOriginalValue:"238855638",displayValue:"",originalValue:"",value:"238855638"},
      {columnDisplayName:"Contact Name",columnName:"dataContactName",dict:false,displayOriginalValue:"",displayValue:"",originalValue:"",value:null},
      {columnDisplayName:"Content",columnName:"contactContent",dict:false,displayOriginalValue:"",displayValue:"",originalValue:"",value:"HERMES_E2E_FOLLOW_OK"},
      {columnDisplayName:"Attachment",columnName:"annex",dict:false,displayOriginalValue:"",displayValue:"",originalValue:"",value:null},
      {columnDisplayName:"Color",columnName:"bgColor",dict:false,displayOriginalValue:"",displayValue:"",originalValue:"",value:"fe4145"},
      {columnDisplayName:"Follow Method",columnName:"method",dict:true,displayOriginalValue:"",displayValue:"",originalValue:"",value:""},
      {columnDisplayName:"Planning Time",columnName:"planningTime",dict:false,displayOriginalValue:"",displayValue:"",originalValue:"",value:"2026-06-17 13:00:00"},
      {columnDisplayName:"Step",columnName:"step",dict:true,displayOriginalValue:"",displayValue:"",originalValue:"",value:null},
      {columnDisplayName:"Next Remind Time",columnName:"nextRemindTime",dict:false,displayOriginalValue:"",displayValue:"",originalValue:"",value:null},
      {columnDisplayName:"Repeat Cycle",columnName:"repeatCycle",dict:false,displayOriginalValue:"",displayValue:"",originalValue:"",value:null},
      {columnDisplayName:"Relevant",columnName:"relevant",dict:false,displayOriginalValue:"",displayValue:"",originalValue:"",value:null},
      {columnDisplayName:"Operator",columnName:"operatorName",dict:false,displayOriginalValue:"",displayValue:"",originalValue:"",value:null},
      {columnDisplayName:"Feedback Operator",columnName:"feedbackOperator",dict:false,displayOriginalValue:"",displayValue:"",originalValue:"",value:"183006"}
    ],
    relevantList:[{relevantId:"",relevant:""}],
    flowStep:"",forceRefresh:true,followType:"",followObject:""
  };

  const r5 = await send('Runtime.evaluate', {
    expression: `(async function(){ var r = await fetch("/rapi/m/follow/add", {method:"POST",credentials:"include",headers:{"Content-Type":"application/json","X-Cid":"71376","X-User":"183006"},body:JSON.stringify(${JSON.stringify(followBody)})}); var j = await r.json(); return JSON.stringify({success:j.success,code:j.code,data:j.data,errMsg:j.errMsg}); })()`,
    awaitPromise: true, returnByValue: true, timeout: 12000
  });
  console.log('Follow:', r5.result?.result?.value);
  results.follow = r5.result?.result?.value;

  // Step 6: 新增客户
  console.log('\nStep 6: Create customer');
  const createBody = {
    models: [
      {columnName:"name",value:"Hermes E2E Create",displayValue:"Hermes E2E Create",originalValue:"",displayOriginalValue:""},
      {columnName:"shortName",value:"HEC",displayValue:"HEC",originalValue:"",displayOriginalValue:""},
      {columnName:"description",value:"HERMES_E2E_CREATE_OK",displayValue:"HERMES_E2E_CREATE_OK",originalValue:"",displayOriginalValue:""},
      {columnName:"webSite",value:"",displayValue:"",originalValue:"",displayOriginalValue:""},
      {columnName:"displayType",value:"潜在工业客户",displayValue:"潜在工业客户",originalValue:"236496",displayOriginalValue:"236496"},
      {columnName:"code",value:"",displayValue:"",originalValue:"",displayOriginalValue:""},
      {columnName:"introduce",value:"",displayValue:"",originalValue:"",displayOriginalValue:""}
    ],
    contacts: [{models:[{columnName:"name",value:"Test Contact",displayValue:"Test Contact",originalValue:"",displayOriginalValue:""}]}],
    banks: [],
    customerAttachmentDtoList: [],
    tagList: [],
    markModel: {isChanged:false,customerId:0,companyId:71376,operatorId:183006},
    displayType: {value:"236496",displayValue:"潜在工业客户",displayOriginalValue:"236496"}
  };

  const r6 = await send('Runtime.evaluate', {
    expression: `(async function(){ var r = await fetch("/rapi/d/customer", {method:"POST",credentials:"include",headers:{"Content-Type":"application/json","X-Cid":"71376","X-User":"183006"},body:JSON.stringify(${JSON.stringify(createBody)})}); var j = await r.json(); return JSON.stringify({success:j.success,code:j.code,data:j.data,errMsg:j.errMsg}); })()`,
    awaitPromise: true, returnByValue: true, timeout: 12000
  });
  console.log('Create:', r6.result?.result?.value);
  results.create = r6.result?.result?.value;

  // Save all results
  results.timestamp = new Date().toISOString();
  fs.writeFileSync('C:/Users/Admin/Desktop/e2e_full_results.json', JSON.stringify(results, null, 2));
  console.log('\n=== ALL RESULTS SAVED ===');
  
  ws.close();
}

ws.on('open', () => {
  run().then(() => { console.log('Done!'); process.exit(0); }).catch(e => { console.error(e); process.exit(1); });
});
setTimeout(() => { console.log('Global timeout'); process.exit(1); }, 90000);
