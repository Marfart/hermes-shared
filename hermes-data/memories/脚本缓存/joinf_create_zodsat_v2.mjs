import { readFileSync } from "fs";

// Fresh cookie from browser
const COOKIE = "Qs_lvt_382761=1781631952; Hm_lvt_e76f42e145e722198c8bbc08c3b84314=1781631959; HMACCOUNT=7A7C7ADED95637BC; language=zh; Qs_pv_382761=3717785015376907300%2C898033854656484900; Hm_lpvt_e76f42e145e722198c8bbc08c3b84314=1781632366; releaseCenterLoginInfo=502662_786718; 5; sajssdk_2015_cross_new_user=1; sensorsdata2015jssdkcross=%7B%22distinct_id%22%3A%22786718%22%2C%22first_id%22%3A%2219ed1938aa2412-0a947dcaa26cbc-26061051-2073600-19ed1938aa3f6e%22%2C%22props%22%3A%7B%7D%2C%22%24device_id%22%3A%2219ed1938aa2412-0a947dcaa26cbc-26061051-2073600-19ed1938aa3f6e%22%7D; tgw_l7_route=a5f93c5498360a3e3582c320fcd2df2d; userLoginInfoSaas=%7B%22userName%22%3A%22bliiot03%22%7D; lname=bliiot03; releaseCenterToken=e0512e6c-2b3d-4545-bacb-7cd2d1bbfeaf; JOINF_SESSION=YWI5NjMzYzEtNDM4Ny00Zjc4LTkxNjEtN2VkNTNiZmM0Mzk0";

const HEADERS = {
  "Content-Type": "application/json",
  Cookie: COOKIE,
  "X-Cid": "71376",
  "X-User": "183006",
};

async function main() {
  // Step 1: Create customer
  const body = {
    models: [
      { columnName: "name", value: "ZODSAT Zimbabwe", displayValue: "ZODSAT Zimbabwe", originalValue: "", displayOriginalValue: "" },
      { columnName: "shortName", value: "ZODSAT", displayValue: "ZODSAT", originalValue: "", displayOriginalValue: "" },
      { columnName: "description", value: "Zimbabwe transformer anti-theft project. S275+PT100 LoRaWAN EU868 solution. Contact: Arnold Chimambo. 50,000 units planned over 6 years.", displayValue: "Zimbabwe transformer anti-theft project. S275+PT100 LoRaWAN EU868 solution. Contact: Arnold Chimambo. 50,000 units planned over 6 years.", originalValue: "", displayOriginalValue: "" },
      { columnName: "displayType", value: 236496, displayValue: "潜在工业客户", originalValue: 236496, displayOriginalValue: "潜在工业客户" },
      { columnName: "country", value: "Zimbabwe", displayValue: "Zimbabwe", originalValue: "", displayOriginalValue: "" },
    ],
    contacts: [{
      models: [
        { columnName: "name", value: "Arnold Chimambo", displayValue: "Arnold Chimambo", originalValue: "", displayOriginalValue: "" },
      ]
    }],
    banks: [],
    customerAttachmentDtoList: [],
    tagList: [],
    markModel: { customerId: 0, companyId: 71376, operatorId: 183006, isChanged: false },
  };

  console.log("Creating customer: ZODSAT Zimbabwe...");
  const res = await fetch("https://trade.joinf.com/rapi/d/customer", {
    method: "POST",
    headers: HEADERS,
    body: JSON.stringify(body),
  });

  const text = await res.text();
  console.log("Status:", res.status);
  console.log("Response:", text.substring(0, 500));

  let customerId;
  try {
    const json = JSON.parse(text);
    customerId = json.data;
    if (!customerId) {
      console.log("❌ Create failed:", json.errMsg || JSON.stringify(json));
      return;
    }
    console.log("\n✅ Customer created! ID:", customerId);
  } catch (e) {
    console.log("Could not parse response");
    return;
  }

  // Step 2: Add follow-up record
  const now = new Date();
  const ts = `${now.getFullYear()}-${String(now.getMonth()+1).padStart(2,"0")}-${String(now.getDate()).padStart(2,"0")} ${String(now.getHours()).padStart(2,"0")}:${String(now.getMinutes()).padStart(2,"0")}:${String(now.getSeconds()).padStart(2,"0")}`;

  const followBody = {
    customerId,
    content: `【WhatsApp跟进 2026-06-17】
1. 客户确认外壳方案可接受（17:35）
2. 客户询问付款确认进度（13:46），我方回复正在等待老板最终确认（14:13）
3. 我方回复了老板的3个技术问题（20:18）：变压器油被盗→温度飙升→报警的完整流程说明
4. 客户给了详细回复（21:25）：热力学分析+硬件联动机制
5. 我方回复感谢（22:01）
6. 我方进一步追问（22:45）：除了油温报警外，是否有其他触发机制（门磁、螺栓传感器等）
状态：跟进中，客户对S275+PT100方案感兴趣，正在确认更多技术细节`,
    planningTime: ts,
  };

  console.log("\nAdding follow-up record...");
  const followRes = await fetch("https://trade.joinf.com/rapi/m/follow/add", {
    method: "POST",
    headers: HEADERS,
    body: JSON.stringify(followBody),
  });

  const followText = await followRes.text();
  console.log("Follow-up Status:", followRes.status);
  console.log("Follow-up Response:", followText.substring(0, 500));
}

main().catch(console.error);
