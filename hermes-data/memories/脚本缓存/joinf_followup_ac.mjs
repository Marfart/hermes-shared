import { createJoinfClient } from "file:///C:/Users/Admin/AppData/Local/hermes/skills/sales/joinf-crm-api/references/joinf-api-client.mjs";

const COOKIE = "Qs_lvt_382761=1781631952; Hm_lvt_e76f42e145e722198c8bbc08c3b84314=1781631959; HMACCOUNT=7A7C7ADED95637BC; language=zh; Qs_pv_382761=3717785015376907300%2C898033854656484900; Hm_lpvt_e76f42e145e722198c8bbc08c3b84314=1781632366; releaseCenterLoginInfo=502662_786718; 5; sajssdk_2015_cross_new_user=1; sensorsdata2015jssdkcross=%7B%22distinct_id%22%3A%22786718%22%2C%22first_id%22%3A%2219ed1938aa2412-0a947dcaa26cbc-26061051-2073600-19ed1938aa3f6e%22%2C%22props%22%3A%7B%7D%2C%22%24device_id%22%3A%2219ed1938aa2412-0a947dcaa26cbc-26061051-2073600-19ed1938aa3f6e%22%7D; tgw_l7_route=a5f93c5498360a3e3582c320fcd2df2d; userLoginInfoSaas=%7B%22userName%22%3A%22bliiot03%22%7D; lname=bliiot03; releaseCenterToken=e0512e6c-2b3d-4545-bacb-7cd2d1bbfeaf; JOINF_SESSION=YWI5NjMzYzEtNDM4Ny00Zjc4LTkxNjEtN2VkNTNiZmM0Mzk0";

const client = createJoinfClient({
  cookie: COOKIE,
  xCid: 71376,
  xUser: 183006,
});

async function main() {
  // AC company - correct customer
  const customerId = 235578642;
  const now = new Date();
  const ts = `${now.getFullYear()}-${String(now.getMonth()+1).padStart(2,"0")}-${String(now.getDate()).padStart(2,"0")} ${String(now.getHours()).padStart(2,"0")}:${String(now.getMinutes()).padStart(2,"0")}:${String(now.getSeconds()).padStart(2,"0")}`;

  console.log("Adding follow-up for AC company (ID: 235578642)...");
  console.log("Contact: Arnold Chimambo\n");

  const result = await client.addFollowRecord({
    customerId,
    content: "【WhatsApp跟进 2026-06-17】\n1. 客户确认外壳方案可接受（17:35）\n2. 客户询问付款确认进度（13:46），我方回复正在等待老板最终确认（14:13）\n3. 我方回复了老板的3个技术问题（20:18）：变压器油被盗→温度飙升→报警的完整流程说明\n4. 客户给了详细回复（21:25）：热力学分析+硬件联动机制\n5. 我方回复感谢（22:01）\n6. 我方进一步追问（22:45）：除了油温报警外，是否有其他触发机制（门磁、螺栓传感器等）\n\n状态：跟进中，客户对S275+PT100方案感兴趣，正在确认更多技术细节",
    planningTime: ts,
    feedbackOperator: 183006,
  });

  if (result.json?.success) {
    console.log("✅ Follow-up added successfully!");
    console.log("Follow ID:", JSON.stringify(result.json.data));
  } else {
    console.log("❌ Failed:", JSON.stringify(result.json || result.error));
  }
}

main().catch(console.error);
