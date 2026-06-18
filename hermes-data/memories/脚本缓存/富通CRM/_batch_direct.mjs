// 用跑通的方式：Node.js direct HTTP + Cookie header，不走CDP
// 同 joinf_batch_followup.mjs 的方式

const COOKIE = "5; tgw_l7_route=79f067c6ab5e8d3acd769edbed9afe09; language=zh; releaseCenterLoginInfo=502662_786718; 5; sensorsdata2015jssdkcross=%7B%22distinct_id%22%3A%22786718%22%2C%22first_id%22%3A%2219edb508fbc473-0af5b7f9d9b4518-26061051-2073600-19edb508fbd1237%22%2C%22props%22%3A%7B%22%24latest_traffic_source_type%22%3A%22%E7%9B%B4%E6%8E%A5%E6%B5%81%E9%87%8F%22%2C%22%24latest_search_keyword%22%3A%22%E6%9C%AA%E5%8F%96%E5%88%B0%E5%80%BC_%E7%9B%B4%E6%8E%A5%E6%89%93%E5%BC%80%22%2C%22%24latest_referrer%22%3A%22%22%7D%2C%22%24device_id%22%3A%2219edb508fbc473-0af5b7f9d9b4518-26061051-2073600-19edb508fbd1237%22%7D; userLoginInfoSaas=%7B%22userName%22%3A%22bliiot03%22%7D; lname=bliiot03; releaseCenterToken=1ba1a18e-49b4-42e0-86bf-abe6cb02e884; JOINF_SESSION=OWRiOTg2NjUtOWJlYi00YjNiLWI4ZjAtNjQ0MTA0NDM5MWQ0";

import { createJoinfClient } from "file:///C:/Users/Admin/AppData/Local/hermes/skills/sales/joinf-crm-api/references/joinf-api-client.mjs";

const client = createJoinfClient({
  cookie: COOKIE,
  xCid: 71376,
  xUser: 183006,
});

const NOW = new Date();
const TS = `${NOW.getFullYear()}-${String(NOW.getMonth()+1).padStart(2,"0")}-${String(NOW.getDate()).padStart(2,"0")} ${String(NOW.getHours()).padStart(2,"0")}:${String(NOW.getMinutes()).padStart(2,"0")}:${String(NOW.getSeconds()).padStart(2,"0")}`;

const RECORDS = [
  { id: 229629960, name: "Juan Carlos Martinez Quintero", text: "昨天（2026-06-18）给Juan Carlos（juancarlosmartinezq@hotmail.com）发送了一封跟进邮件，询问是否有新项目需求，并介绍了BLIIOT最新产品线。" },
  { id: 229679705, name: "Stephen Hudson / Valve Supplies (NZ) Ltd", text: "昨天（2026-06-18）给Stephen Hudson（Stephen@Home.co.nz）发送了一封跟进邮件，询问是否还记得BLIIOT及是否有新项目需求。" },
  { id: 229629827, name: "Richard Twite / Twite Instruments", text: "昨天（2026-06-18）给Richard Twite（richard@twite.com.au）发送了一封跟进邮件，介绍BLIIOT最新工业IoT产品方案。" },
  { id: 229623037, name: "Mr Basem Mohamed Ibrahim Elsayed Elmanzalawi.", text: "昨天（2026-06-18）给Basem（basemnani71077@gmail.com）发送了一封跟进邮件，询问是否有新项目需求。" },
  { id: 229649728, name: "Alex Elliot", text: "昨天（2026-06-18）给Alex Elliot（alex@the-elliots.us）发送了一封跟进邮件，询问是否有新项目合作机会。" },
];

async function main() {
  console.log(`=== 批量添加跟进记录 (${RECORDS.length}条) ===\n`);
  
  let ok = 0, fail = 0;
  
  for (const r of RECORDS) {
    const content = `[邮件] ${r.text}`;
    
    const result = await client.addFollowRecord({
      customerId: r.id,
      content: content,
      planningTime: TS,
      feedbackOperator: 183006,
      bgColor: "2B579A",
    });
    
    if (result.json?.success) {
      ok++;
      console.log(`✅ ${r.name} → ID: ${result.json.data?.[0] || 'OK'}`);
    } else {
      fail++;
      console.log(`❌ ${r.name} → ${result.json?.errMsg || result.status}`);
      if (!result.json?.success) {
        console.log(`   Status: ${result.status}`);
        console.log(`   Response: ${result.text?.substring(0,200)}`);
      }
    }
  }
  
  console.log(`\n=== 汇总: ✅ ${ok} | ❌ ${fail} ===`);
  
  // Verify by reading customer detail
  if (ok > 0) {
    console.log("\n=== 验证: 读取客户跟进时间 ===");
    for (const r of RECORDS.slice(0, 2)) {
      const detail = await client.readCustomerDetail({ customerId: r.id });
      if (detail.json?.success) {
        const displayLastFollowTime = detail.json.data?.[1]?.columnData?.displayLastFollowTime;
        console.log(`${r.name}: lastFollowTime = ${displayLastFollowTime?.value} (${displayLastFollowTime?.displayValue || 'N/A'})`);
      }
    }
  }
}

main().catch(console.error);