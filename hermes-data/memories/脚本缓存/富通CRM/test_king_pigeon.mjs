import { createJoinfClient } from "file:///C:/Users/Admin/AppData/Local/hermes/skills/sales/joinf-crm-api/references/joinf-api-client.mjs";

// Use the full cookie from the working batch_followup script
const COOKIE = "Qs_lvt_382761=1781631952; Hm_lvt_e76f42e145e722198c8bbc08c3b84314=1781631959; HMACCOUNT=7A7C7ADED95637BC; language=zh; Qs_pv_382761=3717785015376907300%2C898033854656484900; Hm_lpvt_e76f42e145e722198c8bbc08c3b84314=1781632366; releaseCenterLoginInfo=502662_786718; sajssdk_2015_cross_new_user=1; sensorsdata2015jssdkcross=%7B%22distinct_id%22%3A%22786718%22%2C%22first_id%22%3A%2219ed1938aa2412-0a947dcaa26cbc-26061051-2073600-19ed1938aa3f6e%22%2C%22props%22%3A%7B%7D%2C%22%24device_id%22%3A%2219ed1938aa2412-0a947dcaa26cbc-26061051-2073600-19ed1938aa3f6e%22%7D; tgw_l7_route=a5f93c5498360a3e3582c320fcd2df2d; userLoginInfoSaas=%7B%22userName%22%3A%22bliiot03%22%7D; lname=bliiot03; releaseCenterToken=e0512e6c-2b3d-4545-bacb-7cd2d1bbfeaf; JOINF_SESSION=YWI5NjMzYzEtNDM4Ny00Zjc4LTkxNjEtN2VkNTNiZmM0Mzk0";

const client = createJoinfClient({ cookie: COOKIE, xCid: 71376, xUser: 183006 });

async function main() {
  // Step 1: Check current detail for this customer (no follow-ups yet)
  console.log("🔍 Checking customer 229622670 KING PIGEON HI-TECH CAMEROON Ltd...");
  const detail = await client.readCustomerDetail({ customerId: 229622670 });
  console.log("Detail status:", detail.status);
  
  if (detail.json?.data) {
    const cats = detail.json.data;
    for (const cat of cats) {
      if (cat.columnData?.displayLastFollowTime) {
        console.log("  displayLastFollowTime:", cat.columnData.displayLastFollowTime.value);
      }
      if (cat.columnData?.followRecordInfo) {
        try {
          const followInfo = JSON.parse(cat.columnData.followRecordInfo.value || "[]");
          console.log("  Existing follow records:", followInfo.length);
        } catch(e) {
          console.log("  followRecordInfo:", String(cat.columnData.followRecordInfo.value).slice(0,100));
        }
      }
    }
  }
  
  // Step 2: Add a test follow-up
  console.log("\n📝 Adding test follow-up for King Pigeon Cameroon...");
  const ts = new Date();
  const formattedTs = `${ts.getFullYear()}-${String(ts.getMonth()+1).padStart(2,'0')}-${String(ts.getDate()).padStart(2,'0')} ${String(ts.getHours()).padStart(2,'0')}:${String(ts.getMinutes()).padStart(2,'0')}:${String(ts.getSeconds()).padStart(2,'0')}`;
  
  const result = await client.addFollowRecord({
    customerId: 229622670,
    content: "【WhatsApp跟进 2026-06-19】我发邮件介绍了BLIIOT工业网关产品给Luc，推荐了BL110和BL120系列用于喀麦隆的系统集成项目，等待回复",
    planningTime: formattedTs,
    feedbackOperator: 183006,
  });
  
  console.log("Follow-up add response:");
  console.log("  status:", result.status);
  console.log("  text:", result.text.slice(0,300));
  
  if (result.json?.success === true && result.json?.data) {
    console.log("✅ Success! Follow-up ID:", result.json.data);
  } else if (result.json?.success === true) {
    console.log("⚠️ Success=true but no data field");
  } else {
    console.log("❌ Failed:", JSON.stringify(result.json));
  }
  
  // Step 3: Verify - re-read detail to check if follow-up appears
  console.log("\n🔍 Verifying... checking detail again...");
  const detail2 = await client.readCustomerDetail({ customerId: 229622670 });
  if (detail2.json?.data) {
    for (const cat of detail2.json.data) {
      if (cat.columnData?.displayLastFollowTime) {
        console.log("  displayLastFollowTime:", cat.columnData.displayLastFollowTime.value);
      }
      if (cat.columnData?.followRecordInfo) {
        try {
          const followInfo = JSON.parse(cat.columnData.followRecordInfo.value || "[]");
          console.log("  Follow records count:", followInfo.length);
          if (followInfo.length > 0) {
            console.log("  Latest:", JSON.stringify(followInfo[followInfo.length-1]).slice(0,200));
          }
        } catch(e) {
          console.log("  followRecordInfo raw:", String(cat.columnData.followRecordInfo.value).slice(0,100));
        }
      }
    }
  }
}

main().catch(console.error);