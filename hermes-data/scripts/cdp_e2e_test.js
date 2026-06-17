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
    // Step 1: 读取客户详情获取当前值（作为模板基础）
    console.log('=== Step 1: Read customer for template ===');
    const r1 = await send('Runtime.evaluate', {
      expression: '(async(){const r=await fetch("/rapi/d/customers/238855638/1",{credentials:"include",headers:{"X-Cid":"71376","X-User":"183006"}});const j=await r.json();return JSON.stringify({name:j.data["1"].columnData.name,desc:j.data["1"].columnData.description,shortName:j.data["1"].columnData.shortName,webSite:j.data["1"].columnData.webSite,displayType:j.data["1"].columnData.displayType})})()',
      awaitPromise: true, returnByValue: true
    });
    console.log('Current values:', r1.result?.result?.value);
    const current = JSON.parse(r1.result?.result?.value || '{}');

    // Step 2: 用Codex的模板结构构建PATCH请求
    console.log('\n=== Step 2: PATCH update description ===');
    const patchPayload = {
      id: 238855638,
      models: [
        {columnName:"name",value:current.name?.value||"",displayValue:current.name?.value||"",originalValue:current.name?.originalValue||"",displayOriginalValue:current.name?.originalValue||""},
        {columnName:"shortName",value:current.shortName?.value||"",displayValue:current.shortName?.value||"",originalValue:current.shortName?.originalValue||"",displayOriginalValue:current.shortName?.originalValue||""},
        {columnName:"description",value:"HERMES_E2E_PATCH_TEST_20260617",displayValue:"HERMES_E2E_PATCH_TEST_20260617",originalValue:current.desc?.originalValue||"",displayOriginalValue:current.desc?.originalValue||""},
        {columnName:"webSite",value:current.webSite?.value||"",displayValue:current.webSite?.value||"",originalValue:current.webSite?.originalValue||"",displayOriginalValue:current.webSite?.originalValue||""},
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

    const r2 = await send('Runtime.evaluate', {
      expression: `(async(){
        const body = ${JSON.stringify(patchPayload)};
        const r = await fetch("/rapi/d/customer", {
          method: "PATCH",
          credentials: "include",
          headers: {"Content-Type":"application/json","X-Cid":"71376","X-User":"183006"},
          body: JSON.stringify(body)
        });
        const j = await r.json();
        return JSON.stringify({success:j.success,code:j.code,data:j.data,errMsg:j.errMsg});
      })()`,
      awaitPromise: true, returnByValue: true
    });
    console.log('PATCH result:', r2.result?.result?.value);

    // Step 3: 如果PATCH成功，恢复原始值
    const patchResult = JSON.parse(r2.result?.result?.value || '{}');
    if (patchResult.success) {
      console.log('\n=== Step 3: Restore original value ===');
      patchPayload.models[2].value = current.desc?.value||"";
      patchPayload.models[2].displayValue = current.desc?.value||"";
      patchPayload.models[2].originalValue = current.desc?.value||"";
      patchPayload.models[2].displayOriginalValue = current.desc?.value||"";
      
      const r3 = await send('Runtime.evaluate', {
        expression: `(async(){
          const body = ${JSON.stringify(patchPayload)};
          const r = await fetch("/rapi/d/customer", {
            method: "PATCH",
            credentials: "include",
            headers: {"Content-Type":"application/json","X-Cid":"71376","X-User":"183006"},
            body: JSON.stringify(body)
          });
          const j = await r.json();
          return JSON.stringify({success:j.success,code:j.code,errMsg:j.errMsg});
        })()`,
        awaitPromise: true, returnByValue: true
      });
      console.log('Restore result:', r3.result?.result?.value);
    }

    // Step 4: 添加跟进记录
    console.log('\n=== Step 4: Add follow record ===');
    const followPayload = {
      id:"",attachmentList:[],businessStep:0,customerStep:0,completeNoRemind:0,
      cycleEndDay:"",cycleStartDay:"",cycleId:"",dataType:0,currentDoneFlag:0,
      models:[
        {columnDisplayName:"Customer Name",columnName:"dataName",dict:false,displayOriginalValue:"238855638",displayValue:"",originalValue:"",value:"238855638"},
        {columnDisplayName:"Contact Name",columnName:"dataContactName",dict:false,displayOriginalValue:"",displayValue:"",originalValue:"",value:null},
        {columnDisplayName:"Content",columnName:"contactContent",dict:false,displayOriginalValue:"",displayValue:"",originalValue:"",value:"HERMES_E2E_FOLLOW_TEST_20260617"},
        {columnDisplayName:"Attachment",columnName:"annex",dict:false,displayOriginalValue:"",displayValue:"",originalValue:"",value:null},
        {columnDisplayName:"Color",columnName:"bgColor",dict:false,displayOriginalValue:"",displayValue:"",originalValue:"",value:"fe4145"},
        {columnDisplayName:"Follow Method",columnName:"method",dict:true,displayOriginalValue:"",displayValue:"",originalValue:"",value:""},
        {columnDisplayName:"Planning Time",columnName:"planningTime",dict:false,displayOriginalValue:"",displayValue:"",originalValue:"",value:"2026-06-17 12:30:00"},
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

    const r4 = await send('Runtime.evaluate', {
      expression: `(async(){
        const body = ${JSON.stringify(followPayload)};
        const r = await fetch("/rapi/m/follow/add", {
          method: "POST",
          credentials: "include",
          headers: {"Content-Type":"application/json","X-Cid":"71376","X-User":"183006"},
          body: JSON.stringify(body)
        });
        const j = await r.json();
        return JSON.stringify({success:j.success,code:j.code,data:j.data,errMsg:j.errMsg});
      })()`,
      awaitPromise: true, returnByValue: true
    });
    console.log('Follow result:', r4.result?.result?.value);

    // 保存结果
    const results = {
      read: r1.result?.result?.value,
      patch: r2.result?.result?.value,
      follow: r4.result?.result?.value,
      timestamp: new Date().toISOString()
    };
    fs.writeFileSync('C:/Users/Admin/Desktop/api_test_results.json', JSON.stringify(results, null, 2));
    console.log('\nResults saved to Desktop/api_test_results.json');

  } catch(e) { console.error(e); }
  ws.close();
});
ws.on('error', e => { console.error(e.message); process.exit(1); });
setTimeout(() => { process.exit(0); }, 25000);
