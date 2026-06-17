import { createJoinfClient } from "file:///C:/Users/Admin/AppData/Local/hermes/skills/sales/joinf-crm-api/references/joinf-api-client.mjs";

const COOKIE = "Qs_lvt_382761=1781631952; Hm_lvt_e76f42e145e722198c8bbc08c3b84314=1781631959; HMACCOUNT=7A7C7ADED95637BC; language=zh; Qs_pv_382761=3717785015376907300%2C898033854656484900; Hm_lpvt_e76f42e145e722198c8bbc08c3b84314=1781632366; releaseCenterLoginInfo=502662_786718; 5; sajssdk_2015_cross_new_user=1; sensorsdata2015jssdkcross=%7B%22distinct_id%22%3A%22786718%22%2C%22first_id%22%3A%2219ed1938aa2412-0a947dcaa26cbc-26061051-2073600-19ed1938aa3f6e%22%2C%22props%22%3A%7B%7D%2C%22%24device_id%22%3A%2219ed1938aa2412-0a947dcaa26cbc-26061051-2073600-19ed1938aa3f6e%22%7D; tgw_l7_route=a5f93c5498360a3e3582c320fcd2df2d; userLoginInfoSaas=%7B%22userName%22%3A%22bliiot03%22%7D; lname=bliiot03; releaseCenterToken=e0512e6c-2b3d-4545-bacb-7cd2d1bbfeaf; JOINF_SESSION=YWI5NjMzYzEtNDM4Ny00Zjc4LTkxNjEtN2VkNTNiZmM0Mzk0";

const client = createJoinfClient({
  cookie: COOKIE,
  xCid: 71376,
  xUser: 183006,
});

// 需要修复跟进记录的客户（从WhatsApp翻到的真正内容）
const UPDATES = [
  // Alvick → Energy Cloud SAC (秘鲁客户，要买BL460W样品)
  { id: null, name: "Energy Cloud SAC", content: "他叫Alvick Mallqui，从秘鲁联系我，说之前买过Jimmy Chen公司的设备，现在对CM5模块的网关感兴趣。他要了BL460W-CM5104032-X20（WiFi版）的样品报价，我报了$256样品价+$44运费=$300，他给了邮箱amallqui@energycloud.tv和地址" },
  
  // Zantar Abdurab Segeir → 不在CRM
  { id: null, name: "Zantar Abdurab Segeir", content: "他来自印尼，问了BL118B+SOM335+X4+Y02+Y31的报价，还问了BA115 12台的折扣价。我解释了样品价和批量价的区别，他说感谢我给的大折扣。他问了运费$55、清关（CPT条款，DHL发货，仍需他自行清关）、交期4-7天。他最后选了标准BA115" },
  
  // Víctor Camino → 已在CRM
  { id: null, name: "Víctor Camino", content: "他回复了感谢" },
  
  // Hussain Alsayoud → hsinsight
  { id: null, name: "hsinsight", content: "他回复了感谢" },
  
  // Saddem Mourad → 不在CRM
  { id: null, name: "Saddem Mourad", content: "他回复了感谢我的理解" },
  
  // Thamara Banneheka → 不在CRM
  { id: null, name: "Thamara Banneheka", content: "他回复了感谢" },
  
  // C → Víctor Camino（匹配错了，先不管）
  // Guillaume Jonville → 已在CRM
  { id: null, name: "Guillaume Jonville", content: "他回复了感谢" },
  
  // Eng → EcoNOS Energy Solutions
  { id: null, name: "EcoNOS Energy Solutions Sdn. Bhd.", content: "他回复了感谢" },
  
  // Miguel alvarez → 已在CRM
  { id: null, name: "Miguel alvarez", content: "他回复了gracias" },
  
  // Sandra Ayu → 不在CRM
  { id: null, name: "Sandra Ayu", content: "她回复了好的谢谢" },
  
  // Pranit Patil → Nirvaa Automation Pvt Ltd
  { id: null, name: "Nirvaa Automation Pvt Ltd", content: "他回复说抱歉回复晚了" },
  
  // Md. Harun Rashid → 不在CRM
  { id: null, name: "Md. Harun Rashid", content: "他发了Hello" },
  
  // Diego → 已在CRM
  { id: null, name: "Diego", content: "他发了Hello" },
  
  // Full Frame → Iriann
  { id: null, name: "Iriann", content: "他发了Hello" },
];

async function loadAllCustomers() {
  const all = [];
  for (let page = 1; page <= 40; page++) {
    const url = `https://trade.joinf.com/rapi/d/customers?num=${page}&paging=true&size=50`;
    const res = await fetch(url, {
      headers: { Cookie: COOKIE, "X-Cid": "71376", "X-User": "183006" },
    });
    const data = await res.json();
    const values = data?.data?.values;
    if (!values || values.length === 0) break;
    all.push(...values);
  }
  return all;
}

function findCustomerId(allCustomers, name) {
  const n = name.toLowerCase();
  for (const row of allCustomers) {
    const contactName = (row.contactName || row.contact || row.linkman || "").toLowerCase();
    const companyName = (row.name || row.customerName || row.shortName || "").toLowerCase();
    const email = (row.email || "").toLowerCase();
    if (contactName.includes(n) || companyName.includes(n) || email.includes(n)) {
      return { id: row.id, name: row.name || row.customerName };
    }
  }
  return null;
}

async function main() {
  console.log("Loading all CRM customers...");
  const allCustomers = await loadAllCustomers();
  console.log(`Loaded ${allCustomers.length} customers\n`);

  let updated = 0, notFound = [];

  for (const u of UPDATES) {
    // Find customer ID
    let match = null;
    if (u.id) {
      match = { id: u.id, name: u.name };
    } else {
      match = findCustomerId(allCustomers, u.name);
    }

    if (!match) {
      notFound.push(u.name);
      console.log(`❌ ${u.name} → 未找到`);
      continue;
    }

    const now = new Date();
    const ts = `${now.getFullYear()}-${String(now.getMonth()+1).padStart(2,"0")}-${String(now.getDate()).padStart(2,"0")} ${String(now.getHours()).padStart(2,"0")}:${String(now.getMinutes()).padStart(2,"0")}:${String(now.getSeconds()).padStart(2,"0")}`;

    const r = await client.addFollowRecord({
      customerId: match.id,
      content: u.content,
      planningTime: ts,
      feedbackOperator: 183006,
    });

    if (r.json?.success) {
      updated++;
      console.log(`✅ ${u.name} → ${match.name} ✓`);
    } else {
      console.log(`⚠️ ${u.name} → ${match.name} (跟进失败)`);
    }
  }

  console.log(`\n===== 汇总 =====`);
  console.log(`已更新: ${updated}`);
  console.log(`未找到: ${notFound.length}`);
  if (notFound.length > 0) console.log(`名单: ${notFound.join(", ")}`);
}

main().catch(console.error);
