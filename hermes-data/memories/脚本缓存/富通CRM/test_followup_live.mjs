import { writeFileSync, readFileSync } from 'fs';

async function getCDPUrl() {
  const resp = await fetch('http://127.0.0.1:9226/json');
  const pages = await resp.json();
  const target = pages.find(p => p.url && p.url.includes('trade.joinf.com')) || pages.find(p => p.url && !p.url.startsWith('devtools'));
  if (!target) throw new Error('No suitable CDP target found');
  return target.webSocketDebuggerUrl;
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
  
  async function evalPage(expr, timeout = 15000) {
    const r = await send({ method: 'Runtime.evaluate', params: { expression: expr, returnByValue: true, awaitPromise: true, timeout } });
    if (r.result?.exceptionDetails) throw new Error(JSON.stringify(r.result.exceptionDetails));
    return r.result?.result?.value;
  }
  
  const CUSTOMER_ID = 229678570;
  const CUSTOMER_NAME = 'SCI-Hálózat Távközlési és Hálózatintegrációs zRt.';
  
  // Step 1: 先读取当前详情，确认displayLastFollowTime
  console.log('=== Step 1: 读取客户当前详情 ===');
  const detailBefore = await evalPage(`
    (async () => {
      const resp = await fetch('/rapi/d/customers/${CUSTOMER_ID}/1', {
        headers: { 'X-Cid': '71376', 'X-User': '183006', 'Accept': 'application/json' }
      });
      const json = await resp.json();
      const cats = json.data || [];
      let lastFollowTime = null;
      let followCount = 0;
      for (const cat of cats) {
        if (cat.columnData?.displayLastFollowTime) {
          lastFollowTime = cat.columnData.displayLastFollowTime.value;
        }
        if (cat.columnData?.followRecordInfo) {
          try {
            const fi = JSON.parse(cat.columnData.followRecordInfo.value || '[]');
            followCount = fi.length;
          } catch(e) {}
        }
      }
      return JSON.stringify({ lastFollowTime, followCount, success: json.success });
    })()
  `);
  console.log('跟进前:', detailBefore);
  
  // Step 2: 用 addFollowRecord API 添加跟进
  console.log('\\n=== Step 2: API添加跟进 ===');
  const now = new Date();
  const pad = n => String(n).padStart(2, '0');
  const ts = `${now.getFullYear()}-${pad(now.getMonth()+1)}-${pad(now.getDate())} ${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(now.getSeconds())}`;
  
  const apiResult = await evalPage(`
    (async () => {
      const payload = {
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
          { columnDisplayName: "Customer Name", columnName: "dataName", dict: false, displayOriginalValue: ${CUSTOMER_ID}, displayValue: "", originalValue: "", value: ${CUSTOMER_ID} },
          { columnDisplayName: "Contact Name", columnName: "dataContactName", dict: false, displayOriginalValue: "", displayValue: "", originalValue: "", value: null },
          { columnDisplayName: "Content", columnName: "contactContent", dict: false, displayOriginalValue: "", displayValue: "", originalValue: "", value: "【WhatsApp跟进 2026-06-19】向Tamás介绍了BLIIOT工业网关产品，推荐了BL110和BL120系列用于匈牙利的网络集成项目，客户表示感兴趣，等待进一步技术讨论" },
          { columnDisplayName: "Attachment", columnName: "annex", dict: false, displayOriginalValue: "", displayValue: "", originalValue: "", value: null },
          { columnDisplayName: "Color", columnName: "bgColor", dict: false, displayOriginalValue: "", displayValue: "", originalValue: "", value: "27AE60" },
          { columnDisplayName: "Follow Method", columnName: "method", dict: true, displayOriginalValue: "", displayValue: "", originalValue: "", value: "" },
          { columnDisplayName: "Planning Time", columnName: "planningTime", dict: false, displayOriginalValue: "", displayValue: "", originalValue: "", value: "${ts}" },
          { columnDisplayName: "Step", columnName: "step", dict: true, displayOriginalValue: "", displayValue: "", originalValue: "", value: null },
          { columnDisplayName: "Next Remind Time", columnName: "nextRemindTime", dict: false, displayOriginalValue: "", displayValue: "", originalValue: "", value: null },
          { columnDisplayName: "Repeat Cycle", columnName: "repeatCycle", dict: false, displayOriginalValue: "", displayValue: "", originalValue: "", value: null },
          { columnDisplayName: "Relevant", columnName: "relevant", dict: false, displayOriginalValue: "", displayValue: "", originalValue: "", value: null },
          { columnDisplayName: "Operator", columnName: "operatorName", dict: false, displayOriginalValue: "", displayValue: "", originalValue: "", value: null },
          { columnDisplayName: "Feedback Operator", columnName: "feedbackOperator", dict: false, displayOriginalValue: "", displayValue: "", originalValue: "", value: "183006" }
        ],
        relevantList: [{ relevantId: "", relevant: "" }],
        flowStep: "",
        forceRefresh: true,
        followType: "",
        followObject: ""
      };
      
      const resp = await fetch('/rapi/m/follow/add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-Cid': '71376', 'X-User': '183006', 'Accept': 'application/json' },
        body: JSON.stringify(payload)
      });
      const json = await resp.json();
      return JSON.stringify(json);
    })()
  `);
  console.log('API结果:', apiResult);
  
  // Step 3: 等待2秒后重新读取详情
  console.log('\\n=== Step 3: 等待3秒后验证 ===');
  await new Promise(r => setTimeout(r, 3000));
  
  const detailAfter = await evalPage(`
    (async () => {
      const resp = await fetch('/rapi/d/customers/${CUSTOMER_ID}/1', {
        headers: { 'X-Cid': '71376', 'X-User': '183006', 'Accept': 'application/json' }
      });
      const json = await resp.json();
      const cats = json.data || [];
      let lastFollowTime = null;
      let followCount = 0;
      let latestFollow = null;
      for (const cat of cats) {
        if (cat.columnData?.displayLastFollowTime) {
          lastFollowTime = cat.columnData.displayLastFollowTime.value;
        }
        if (cat.columnData?.followRecordInfo) {
          try {
            const fi = JSON.parse(cat.columnData.followRecordInfo.value || '[]');
            followCount = fi.length;
            if (fi.length > 0) latestFollow = fi[fi.length - 1];
          } catch(e) {}
        }
      }
      return JSON.stringify({ lastFollowTime, followCount, latestFollow });
    })()
  `);
  console.log('跟进后:', detailAfter);
  
  ws.close();
}

main().catch(console.error);
