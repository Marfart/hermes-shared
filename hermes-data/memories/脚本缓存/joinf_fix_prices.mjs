import { createJoinfClient } from "file:///C:/Users/Admin/AppData/Local/hermes/skills/sales/joinf-crm-api/references/joinf-api-client.mjs";

const COOKIE = "Qs_lvt_382761=1781631952; Hm_lvt_e76f42e145e722198c8bbc08c3b84314=1781631959; HMACCOUNT=7A7C7ADED95637BC; language=zh; Qs_pv_382761=3717785015376907300%2C898033854656484900; Hm_lpvt_e76f42e145e722198c8bbc08c3b84314=1781632366; releaseCenterLoginInfo=502662_786718; 5; sajssdk_2015_cross_new_user=1; sensorsdata2015jssdkcross=%7B%22distinct_id%22%3A%22786718%22%2C%22first_id%22%3A%2219ed1938aa2412-0a947dcaa26cbc-26061051-2073600-19ed1938aa3f6e%22%2C%22props%22%3A%7B%7D%2C%22%24device_id%22%3A%2219ed1938aa2412-0a947dcaa26cbc-26061051-2073600-19ed1938aa3f6e%22%7D; tgw_l7_route=a5f93c5498360a3e3582c320fcd2df2d; userLoginInfoSaas=%7B%22userName%22%3A%22bliiot03%22%7D; lname=bliiot03; releaseCenterToken=e0512e6c-2b3d-4545-bacb-7cd2d1bbfeaf; JOINF_SESSION=YWI5NjMzYzEtNDM4Ny00Zjc4LTkxNjEtN2VkNTNiZmM0Mzk0";

const client = createJoinfClient({
  cookie: COOKIE,
  xCid: 71376,
  xUser: 183006,
});

async function main() {
  const now = new Date();
  const ts = `${now.getFullYear()}-${String(now.getMonth()+1).padStart(2,"0")}-${String(now.getDate()).padStart(2,"0")} ${String(now.getHours()).padStart(2,"0")}:${String(now.getMinutes()).padStart(2,"0")}:${String(now.getSeconds()).padStart(2,"0")}`;

  // Fix Alvick (Energy Cloud SAC, ID: 229695718) - remove prices
  const r1 = await client.addFollowRecord({
    customerId: 229695718,
    content: "他叫Alvick Mallqui，从秘鲁联系我，说之前买过Jimmy Chen公司的设备，现在对CM5模块的网关感兴趣。他要了BL460W-CM5104032-X20（WiFi版）的样品报价，我报了样品价和运费，他给了邮箱amallqui@energycloud.tv和地址",
    planningTime: ts,
    feedbackOperator: 183006,
  });
  console.log("Alvick fix:", r1.json?.success ? "✅" : "❌");

  // Fix Zantar (not in CRM, skip for now)
  console.log("Zantar: not in CRM, skip");

  // Fix Víctor Camino (ID: 234664001) - already no prices, but let me check
  const r3 = await client.addFollowRecord({
    customerId: 234664001,
    content: "他确认收到付款了。他紧急通知我收货地址改了，从厄瓜多尔改到美国佛罗里达的货运代理地址。我确认了运费不变，发了图片给他确认地址是否正确，他说对的。我说下周一回办公室安排发货",
    planningTime: ts,
    feedbackOperator: 183006,
  });
  console.log("Víctor fix:", r3.json?.success ? "✅" : "❌");
}

main().catch(console.error);
