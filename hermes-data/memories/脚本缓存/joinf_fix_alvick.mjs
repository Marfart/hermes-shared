import { createJoinfClient } from "file:///C:/Users/Admin/AppData/Local/hermes/skills/sales/joinf-crm-api/references/joinf-api-client.mjs";

const COOKIE = "Qs_lvt_382761=1781631952; Hm_lvt_e76f42e145e722198c8bbc08c3b84314=1781631959; HMACCOUNT=7A7C7ADED95637BC; language=zh; Qs_pv_382761=3717785015376907300%2C898033854656484900; Hm_lpvt_e76f42e145e722198c8bbc08c3b84314=1781632366; releaseCenterLoginInfo=502662_786718; 5; sajssdk_2015_cross_new_user=1; sensorsdata2015jssdkcross=%7B%22distinct_id%22%3A%22786718%22%2C%22first_id%22%3A%2219ed1938aa2412-0a947dcaa26cbc-26061051-2073600-19ed1938aa3f6e%22%2C%22props%22%3A%7B%7D%2C%22%24device_id%22%3A%2219ed1938aa2412-0a947dcaa26cbc-26061051-2073600-19ed1938aa3f6e%22%7D; tgw_l7_route=a5f93c5498360a3e3582c320fcd2df2d; userLoginInfoSaas=%7B%22userName%22%3A%22bliiot03%22%7D; lname=bliiot03; releaseCenterToken=e0512e6c-2b3d-4545-bacb-7cd2d1bbfeaf; JOINF_SESSION=YWI5NjMzYzEtNDM4Ny00Zjc4LTkxNjEtN2VkNTNiZmM0Mzk0";

const client = createJoinfClient({
  cookie: COOKIE,
  xCid: 71376,
  xUser: 183006,
});

async function main() {
  // 1. Alvick → Energy Cloud SAC (ID: 235578642? 需要查)
  // 先查Energy Cloud SAC的ID
  for (let page = 1; page <= 40; page++) {
    const url = `https://trade.joinf.com/rapi/d/customers?num=${page}&paging=true&size=50`;
    const res = await fetch(url, {
      headers: { Cookie: COOKIE, "X-Cid": "71376", "X-User": "183006" },
    });
    const data = await res.json();
    const values = data?.data?.values;
    if (!values || values.length === 0) break;
    for (const row of values) {
      const n = (row.name || row.customerName || "").toLowerCase();
      if (n.includes("energy cloud")) {
        console.log(`Found Energy Cloud SAC: ID=${row.id}, Name=${row.name}`);
        
        const now = new Date();
        const ts = `${now.getFullYear()}-${String(now.getMonth()+1).padStart(2,"0")}-${String(now.getDate()).padStart(2,"0")} ${String(now.getHours()).padStart(2,"0")}:${String(now.getMinutes()).padStart(2,"0")}:${String(now.getSeconds()).padStart(2,"0")}`;

        const r = await client.addFollowRecord({
          customerId: row.id,
          content: "他叫Alvick Mallqui，从秘鲁联系我，说之前买过Jimmy Chen公司的设备，现在对CM5模块的网关感兴趣。他要了BL460W-CM5104032-X20（WiFi版）的样品报价，我报了$256样品价+$44运费=$300，他给了邮箱amallqui@energycloud.tv和地址",
          planningTime: ts,
          feedbackOperator: 183006,
        });
        console.log("Follow-up result:", r.json?.success ? "✅" : "❌", JSON.stringify(r.json));
        return;
      }
    }
  }
  console.log("Energy Cloud SAC not found");
}

main().catch(console.error);
