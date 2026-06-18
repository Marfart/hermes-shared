// 用完整headers直接HTTP調用，不走CDP
const https = require('https');

const COOKIE = "5; tgw_l7_route=79f067c6ab5e8d3acd769edbed9afe09; language=zh; releaseCenterLoginInfo=502662_786718; 5; sensorsdata2015jssdkcross=%7B%22distinct_id%22%3A%22786718%22%2C%22first_id%22%3A%2219edb508fbc473-0af5b7f9d9b4518-26061051-2073600-19edb508fbd1237%22%2C%22props%22%3A%7B%22%24latest_traffic_source_type%22%3A%22%E7%9B%B4%E6%8E%A5%E6%B5%81%E9%87%8F%22%2C%22%24latest_search_keyword%22%3A%22%E6%9C%AA%E5%8F%96%E5%88%B0%E5%80%BC_%E7%9B%B4%E6%8E%A5%E6%89%93%E5%BC%80%22%2C%22%24latest_referrer%22%3A%22%22%7D%2C%22%24device_id%22%3A%2219edb508fbc473-0af5b7f9d9b4518-26061051-2073600-19edb508fbd1237%22%7D; userLoginInfoSaas=%7B%22userName%22%3A%22bliiot03%22%7D; lname=bliiot03; releaseCenterToken=1ba1a18e-49b4-42e0-86bf-abe6cb02e884; JOINF_SESSION=OWRiOTg2NjUtOWJlYi00YjNiLWI4ZjAtNjQ0MTA0NDM5MWQ0";

const PAYLOAD = (cid, content) => ({
  id: "", attachmentList: [], businessStep: 0, customerStep: 0, completeNoRemind: 0,
  cycleEndDay: "", cycleStartDay: "", cycleId: "", dataType: 0, currentDoneFlag: 0,
  models: [
    { columnDisplayName: "Customer Name", columnName: "dataName", dict: false, displayOriginalValue: cid, displayValue: "", originalValue: "", value: cid },
    { columnDisplayName: "Contact Name", columnName: "dataContactName", dict: false, displayOriginalValue: "", displayValue: "", originalValue: "", value: null },
    { columnDisplayName: "Content", columnName: "contactContent", dict: false, displayOriginalValue: "", displayValue: "", originalValue: "", value: content },
    { columnDisplayName: "Attachment", columnName: "annex", dict: false, displayOriginalValue: "", displayValue: "", originalValue: "", value: null },
    { columnDisplayName: "Color", columnName: "bgColor", dict: false, displayOriginalValue: "", displayValue: "", originalValue: "", value: "2B579A" },
    { columnDisplayName: "Follow Method", columnName: "method", dict: true, displayOriginalValue: "", displayValue: "", originalValue: "", value: "邮件" },
    { columnDisplayName: "Planning Time", columnName: "planningTime", dict: false, displayOriginalValue: "", displayValue: "", originalValue: "", value: "2026-06-19 00:00:00" },
    { columnDisplayName: "Feedback Operator", columnName: "feedbackOperator", dict: false, displayOriginalValue: "", displayValue: "", originalValue: "", value: "183006" }
  ],
  relevantList: [{ relevantId: "", relevant: "" }],
  flowStep: "", forceRefresh: true, followType: "", followObject: ""
});

function request(method, path, body) {
  return new Promise((resolve, reject) => {
    const data = body ? JSON.stringify(body) : null;
    const options = {
      hostname: 'trade.joinf.com',
      path: path,
      method: method,
      headers: {
        'Host': 'trade.joinf.com',
        'Accept': 'application/json, text/plain, */*',
        'Cookie': COOKIE,
        'Origin': 'https://trade.joinf.com',
        'Referer': 'https://trade.joinf.com/tms/customer/customers?type=search&tab=0',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'X-Cid': '71376',
        'X-User': '183006',
        'Content-Type': 'application/json',
        'Content-Length': data ? Buffer.byteLength(data) : 0
      }
    };
    
    const req = https.request(options, (res) => {
      let d = '';
      res.on('data', c => d += c);
      res.on('end', () => {
        try {
          const j = JSON.parse(d);
          resolve({ status: res.statusCode, success: j.success, data: j.data, msg: j.errMsg, raw: d.substring(0,300) });
        } catch(e) {
          resolve({ status: res.statusCode, success: false, raw: d.substring(0,300), error: e.message });
        }
      });
    });
    req.on('error', reject);
    req.setTimeout(15000, () => { req.destroy(); reject(new Error('timeout')); });
    if (data) req.write(data);
    req.end();
  });
}

async function main() {
  // 1. Verify cookie first - read customer
  console.log("=== 驗證Cookie ===");
  const detail = await request('GET', '/rapi/d/customers/229629960/1');
  console.log(`Read: ${detail.success ? '✅' : '❌'} ${detail.status}`);
  
  if (!detail.success) {
    console.log(`Cookie可能已失效: ${detail.raw}`);
    return;
  }
  
  // 2. Push 5 follow-ups
  console.log("\n=== 推送跟進 ===");
  const records = [
    [229629960, "[邮件] 昨天（2026-06-18）给Juan Carlos Martinez发送了跟进邮件，询问新项目需求。"],
    [229679705, "[邮件] 昨天（2026-06-18）给Stephen Hudson发送了跟进邮件，询问新项目需求。"],
    [229629827, "[邮件] 昨天（2026-06-18）给Richard Twite发送了跟进邮件，介绍新产品。"],
    [229623037, "[邮件] 昨天（2026-06-18）给Basem发送了跟进邮件，询问新项目需求。"],
    [229649728, "[邮件] 昨天（2026-06-18）给Alex Elliot发送了跟进邮件，询问新项目合作机会。"],
  ];
  
  for (const [cid, content] of records) {
    const r = await request('POST', '/rapi/m/follow/add', PAYLOAD(cid, content));
    console.log(`${cid}: ${r.success ? '✅' : '❌'} data=${JSON.stringify(r.data)} msg=${r.msg || 'OK'}`);
  }
  
  // 3. Verify
  await new Promise(r => setTimeout(r, 2000));
  console.log("\n=== 驗證 ===");
  const verify = await request('GET', '/rapi/d/customers/229629960/1');
  if (verify.success && verify.data) {
    const info = verify.data[1]?.columnData;
    if (info) {
      console.log(`lastFollowTime: ${info.displayLastFollowTime?.value} (${info.displayLastFollowTime?.displayValue})`);
      console.log(`recentlyFollow: ${info.recentlyFollowTime?.value} (${info.recentlyFollowTime?.displayValue})`);
      console.log(`activityType: ${info.activityType?.value}`);
    } else {
      console.log(`無法提取info，原始響應前500字: ${JSON.stringify(verify).substring(0,500)}`);
    }
  }
}

main().catch(console.error);