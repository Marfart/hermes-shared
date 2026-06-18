// 用v2/v3跑通時的同一個cookie試
const COOKIE = "Qs_lvt_382761=1781631952; Hm_lvt_e76f42e145e722198c8bbc08c3b84314=1781631959; HMACCOUNT=7A7C7ADED95637BC; language=zh; Qs_pv_382761=3717785015376907300%2C898033854656484900; Hm_lpvt_e76f42e145e722198c8bbc08c3b84314=1781632366; releaseCenterLoginInfo=502662_786718; 5; sajssdk_2015_cross_new_user=1; sensorsdata2015jssdkcross=%7B%22distinct_id%22%3A%22786718%22%2C%22first_id%22%3A%2219ed1938aa2412-0a947dcaa26cbc-26061051-2073600-19ed1938aa3f6e%22%2C%22props%22%3A%7B%7D%2C%22%24device_id%22%3A%2219ed1938aa2412-0a947dcaa26cbc-26061051-2073600-19ed1938aa3f6e%22%7D; tgw_l7_route=a5f93c5498360a3e3582c320fcd2df2d; userLoginInfoSaas=%7B%22userName%22%3A%22bliiot03%22%7D; lname=bliiot03; releaseCenterToken=e0512e6c-2b3d-4545-bacb-7cd2d1bbfeaf; JOINF_SESSION=YWI5NjMzYzEtNDM4Ny00Zjc4LTkxNjEtN2VkNTNiZmM0Mzk0";

import { createJoinfClient } from "file:///C:/Users/Admin/AppData/Local/hermes/skills/sales/joinf-crm-api/references/joinf-api-client.mjs";

const client = createJoinfClient({
  cookie: COOKIE,
  xCid: 71376,
  xUser: 183006,
});

async function main() {
  // 1. Test read first - check if cookie still valid
  console.log("=== 測試Cookie是否有效 ===");
  const detail = await client.readCustomerDetail({ customerId: 229629960 });
  if (detail.json?.success) {
    const info = detail.json.data?.[1]?.columnData;
    if (info?.name) console.log(`✅ Cookie有效! 客戶: ${info.name.value}`);
    else console.log(`⚠️ Cookie有效但name不在index1`);
  } else {
    console.log(`❌ Cookie無效: ${detail.json?.errMsg || detail.text?.substring(0,100)}`);
    return;
  }

  // 2. Push just ONE follow-up
  console.log("\n=== 推進跟記錄 (1條) ===");
  const r = await client.addFollowRecord({
    customerId: 229629960,
    content: "[邮件] 用舊cookie測試寫入",
    planningTime: new Date().toISOString().replace('T',' ').substring(0,19),
    feedbackOperator: 183006,
    bgColor: "2B579A",
  });
  console.log(`Write: ${r.json?.success ? '✅' : '❌'} ID=${r.json?.data?.[0]} msg=${r.json?.errMsg || 'OK'}`);
  if (!r.json?.success) console.log(`完整響應: ${r.text?.substring(0,300)}`);

  // 3. Verify
  await new Promise(r => setTimeout(r, 2000));
  console.log("\n=== 驗證 ===");
  const verify = await client.readCustomerDetail({ customerId: 229629960 });
  if (verify.json?.success) {
    const info = verify.json.data?.[1]?.columnData;
    // Dump relevant fields
    const lf = info?.displayLastFollowTime;
    const rf = info?.recentlyFollowTime;
    const at = info?.activityType;
    console.log(`displayLastFollowTime: value=${lf?.value} display=${lf?.displayValue}`);
    console.log(`recentlyFollowTime: value=${rf?.value} display=${rf?.displayValue}`);
    console.log(`activityType: value=${at?.value}`);
    
    // Also show what activity looks like from list API
    const listResp = await fetch("https://trade.joinf.com/rapi/d/customers?num=0&paging=true&size=200&searchText=229629960", {
      headers: { Cookie: COOKIE, "X-Cid": "71376", "X-User": "183006" }
    });
    const list = await listResp.json();
    const v = list.data?.values?.find(x => x.id === 229629960);
    if (v) console.log(`List API: lastFollow=${v.displayLastFollowTime} activity=${v.activity} activityType=${v.activityType}`);
  }
}

main().catch(console.error);