const WebSocket = require('ws');
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
    // Test 1: 读取客户详情 (验证认证)
    console.log('=== Test 1: Read customer detail ===');
    const r1 = await send('Runtime.evaluate', {
      expression: '(async(){const r=await fetch("/rapi/d/customers/238855638/1",{credentials:"include",headers:{"X-Cid":"71376","X-User":"183006"}});const j=await r.json();return JSON.stringify({success:j.success,code:j.code,name:j.data["1"]?.columnData?.name?.value})})()',
      awaitPromise: true, returnByValue: true
    });
    console.log('Read:', r1.result?.result?.value);

    // Test 2: 添加跟进记录
    console.log('\n=== Test 2: Add follow record ===');
    const followPayload = {
      id: "",
      attachmentList: [],
      businessStep: 0,
      customerStep: 0,
      completeNoRemind: 0,
      cycleEndDay: "",
      cycleStartDay: "",
      cycleId: "",
      dataType: 0,
      currentDoneFlag: 0,
      models: [
        {columnDisplayName:"Customer Name",columnName:"dataName",dict:false,displayOriginalValue:"238855638",displayValue:"",originalValue:"",value:"238855638"},
        {columnDisplayName:"Contact Name",columnName:"dataContactName",dict:false,displayOriginalValue:"",displayValue:"",originalValue:"",value:null},
        {columnDisplayName:"Content",columnName:"contactContent",dict:false,displayOriginalValue:"",displayValue:"",originalValue:"",value:"HERMES_FOLLOW_TEST_20260617"},
        {columnDisplayName:"Attachment",columnName:"annex",dict:false,displayOriginalValue:"",displayValue:"",originalValue:"",value:null},
        {columnDisplayName:"Color",columnName:"bgColor",dict:false,displayOriginalValue:"",displayValue:"",originalValue:"",value:"fe4145"},
        {columnDisplayName:"Follow Method",columnName:"method",dict:true,displayOriginalValue:"",displayValue:"",originalValue:"",value:""},
        {columnDisplayName:"Planning Time",columnName:"planningTime",dict:false,displayOriginalValue:"",displayValue:"",originalValue:"",value:"2026-06-17 12:00:00"},
        {columnDisplayName:"Step",columnName:"step",dict:true,displayOriginalValue:"",displayValue:"",originalValue:"",value:null},
        {columnDisplayName:"Next Remind Time",columnName:"nextRemindTime",dict:false,displayOriginalValue:"",displayValue:"",originalValue:"",value:null},
        {columnDisplayName:"Repeat Cycle",columnName:"repeatCycle",dict:false,displayOriginalValue:"",displayValue:"",originalValue:"",value:null},
        {columnDisplayName:"Relevant",columnName:"relevant",dict:false,displayOriginalValue:"",displayValue:"",originalValue:"",value:null},
        {columnDisplayName:"Operator",columnName:"operatorName",dict:false,displayOriginalValue:"",displayValue:"",originalValue:"",value:null},
        {columnDisplayName:"Feedback Operator",columnName:"feedbackOperator",dict:false,displayOriginalValue:"",displayValue:"",originalValue:"",value:"183006"}
      ],
      relevantList: [{relevantId:"",relevant:""}],
      flowStep: "",
      forceRefresh: true,
      followType: "",
      followObject: ""
    };
    
    const r2 = await send('Runtime.evaluate', {
      expression: `(async(){
        const body = ${JSON.stringify(followPayload)};
        const r = await fetch("/rapi/m/follow/add", {
          method: "POST",
          credentials: "include",
          headers: {"Content-Type":"application/json","X-Cid":"71376","X-User":"183006"},
          body: JSON.stringify(body)
        });
        const j = await r.json();
        return JSON.stringify({success:j.success, code:j.code, data:j.data, errMsg:j.errMsg});
      })()`,
      awaitPromise: true, returnByValue: true
    });
    console.log('Follow:', r2.result?.result?.value);

    // Test 3: 新增客户
    console.log('\n=== Test 3: Create customer ===');
    const createPayload = {
      models: [
        {columnName:"name",value:"Hermes E2E Test",displayValue:"Hermes E2E Test",originalValue:"",displayOriginalValue:""},
        {columnName:"shortName",value:"HET",displayValue:"HET",originalValue:"",displayOriginalValue:""},
        {columnName:"description",value:"HERMES_E2E_CREATE_20260617",displayValue:"HERMES_E2E_CREATE_20260617",originalValue:"",displayOriginalValue:""},
        {columnName:"webSite",value:"https://example-e2e.test",displayValue:"https://example-e2e.test",originalValue:"",displayOriginalValue:""},
        {columnName:"displayType",value:"潜在工业客户",displayValue:"潜在工业客户",originalValue:"236496",displayOriginalValue:"236496"},
        {columnName:"code",value:"",displayValue:"",originalValue:"",displayOriginalValue:""},
        {columnName:"introduce",value:"",displayValue:"",originalValue:"",displayOriginalValue:""}
      ],
      contacts: [{
        models: [
          {columnName:"name",value:"Test Contact",displayValue:"Test Contact",originalValue:"",displayOriginalValue:""},
          {columnName:"email",value:"",displayValue:"",originalValue:"",displayOriginalValue:""},
          {columnName:"mobile",value:"",displayValue:"",originalValue:"",displayOriginalValue:""}
        ]
      }],
      banks: [],
      customerAttachmentDtoList: [],
      tagList: [],
      markModel: {customerId:0,isChanged:false,companyId:71376,operatorId:183006},
      displayType: {value:"236496",displayValue:"潜在工业客户",displayOriginalValue:"236496"}
    };

    const r3 = await send('Runtime.evaluate', {
      expression: `(async(){
        const body = ${JSON.stringify(createPayload)};
        const r = await fetch("/rapi/d/customer", {
          method: "POST",
          credentials: "include",
          headers: {"Content-Type":"application/json","X-Cid":"71376","X-User":"183006"},
          body: JSON.stringify(body)
        });
        const j = await r.json();
        return JSON.stringify({success:j.success, code:j.code, data:j.data, errMsg:j.errMsg});
      })()`,
      awaitPromise: true, returnByValue: true
    });
    console.log('Create:', r3.result?.result?.value);

  } catch(e) { console.error(e); }
  ws.close();
});
ws.on('error', e => { console.error(e.message); process.exit(1); });
setTimeout(() => { process.exit(0); }, 20000);
