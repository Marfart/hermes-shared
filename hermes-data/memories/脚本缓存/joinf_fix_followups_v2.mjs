import { createJoinfClient } from "file:///C:/Users/Admin/AppData/Local/hermes/skills/sales/joinf-crm-api/references/joinf-api-client.mjs";

const COOKIE = "Qs_lvt_382761=1781631952; Hm_lvt_e76f42e145e722198c8bbc08c3b84314=1781631959; HMACCOUNT=7A7C7ADED95637BC; language=zh; Qs_pv_382761=3717785015376907300%2C898033854656484900; Hm_lpvt_e76f42e145e722198c8bbc08c3b84314=1781632366; releaseCenterLoginInfo=502662_786718; 5; sajssdk_2015_cross_new_user=1; sensorsdata2015jssdkcross=%7B%22distinct_id%22%3A%22786718%22%2C%22first_id%22%3A%2219ed1938aa2412-0a947dcaa26cbc-26061051-2073600-19ed1938aa3f6e%22%2C%22props%22%3A%7B%7D%2C%22%24device_id%22%3A%2219ed1938aa2412-0a947dcaa26cbc-26061051-2073600-19ed1938aa3f6e%22%7D; tgw_l7_route=a5f93c5498360a3e3582c320fcd2df2d; userLoginInfoSaas=%7B%22userName%22%3A%22bliiot03%22%7D; lname=bliiot03; releaseCenterToken=e0512e6c-2b3d-4545-bacb-7cd2d1bbfeaf; JOINF_SESSION=YWI5NjMzYzEtNDM4Ny00Zjc4LTkxNjEtN2VkNTNiZmM0Mzk0";

const client = createJoinfClient({
  cookie: COOKIE,
  xCid: 71376,
  xUser: 183006,
});

// 正确的人称：我=Kali，他=客户
// 我不能在WhatsApp上回复，所以"我回复了"不对
// 只有Kali亲自回复过的才算"我回复了"
const FIXES = [
  // 这些是客户单方面说感谢/Hello，Kali没回复或不需要回复
  { id: "Alvick", company: "Energy Cloud SAC", content: "他回复了感谢我的耐心" },
  { id: "Víctor Camino", company: "Víctor Camino", content: "他回复了感谢" },
  { id: "Hussain Alsayoud", company: "hsinsight", content: "他回复了感谢" },
  { id: "C", company: "Víctor Camino", content: "他回复了感谢" },
  { id: "Guillaume Jonville", company: "Guillaume Jonville", content: "他回复了感谢" },
  { id: "Eng", company: "EcoNOS Energy Solutions Sdn. Bhd.", content: "他回复了感谢" },
  { id: "Miguel alvarez", company: "Miguel alvarez", content: "他回复了感谢（西班牙语）" },
  { id: "Diego", company: "Diego", content: "他发了Hello" },
  { id: "Full Frame", company: "Iriann", content: "他发了Hello" },
  { id: "Pranit Patil", company: "Nirvaa Automation Pvt Ltd", content: "他回复说抱歉回复晚了" },
  { id: "Sa16", company: "Sa16", content: "他说是的而且价格还涨了" },
  
  // 这些是客户问问题，Kali还没回复
  { id: "Peer IDE Security Engg", company: "Peer IDE Security Engg", content: "他问我有没有更新，我还没回复他" },
  { id: "Patricio González", company: "Patricio González", content: "他问我有没有更新，我还没回复他" },
  { id: "Rafaqat Ali", company: "Rafaqat Ali", content: "他问我有没有新消息，我还没回复他" },
  { id: "Francisco Ramos", company: "Sosi", content: "他问我有没有新消息，我还没回复他" },
  { id: "Andrés Montoya", company: "Estamos en Bogotá Colombia", content: "他问我有没有新消息，我还没回复他" },
  { id: "Nyein Chan Lu", company: "novanestmyanmar", content: "他问我有没有新消息，我还没回复他" },
  { id: "Ion", company: "Fieldtech Automation Co.,ltd.", content: "他问我有没有更新，我还没回复他" },
  { id: "Dunja", company: "Dunja", content: "他问我还要不要他发报价，还是型号不符合要求，我还没回复他" },
  { id: "Harbin Sulbarán", company: "Harbin Sulbarán", content: "他问我是否还对我们的产品感兴趣，我还没回复他" },
  { id: "huy hoang", company: "Huy Hoang", content: "他问我是否还对我们的产品感兴趣，我还没回复他" },
  { id: "Bader", company: "Bader", content: "他问我是否还对我们的产品感兴趣，我还没回复他" },
  { id: "NGUYEN DINH THANH", company: "NGUYEN DINH THANH", content: "他问我有没有什么问题或消息，我还没回复他" },
  { id: "Mojtaba Jahani", company: "Mojtaba Jahani", content: "他问我的客户是否还对我们的产品感兴趣，我还没回复他" },
  { id: "Saulo Madruga", company: "Saulo Madruga | ENGIPROT", content: "他问我是否还对我们的产品感兴趣，我还没回复他" },
  { id: "Md. Harun Rashid", company: "Md. Harun Rashid", content: "他发了Hello，我还没回复他" },
  { id: "Haythem Sassi", company: "Haythem Sassi", content: "他问我有没有更新，我还没回复他" },
  { id: "Sandra Ayu", company: "Sandra Ayu", content: "他回复了好的谢谢" },
  { id: "Wecon", company: "Wecon", content: "他回复说看到了" },
  { id: "Тт", company: "Тт", content: "他说他的同事会负责我的订单" },
  { id: "anubius696", company: "anubius696", content: "他回复说最好后天再问，明天发货" },
  { id: "BOUSARIA Brahim", company: "BOUSARIA Brahim", content: "他让我看看这个，我还没回复他" },
  { id: "Thamara Banneheka", company: "Thamara Banneheka", content: "他回复了感谢" },
  { id: "Saddem Mourad", company: "Saddem Mourad", content: "他回复了感谢我的理解" },
  { id: "Zantar Abdurab Segeir", company: "Zantar Abdurab Segeir", content: "他回复了不客气" },
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

function matchCustomer(allCustomers, name, company) {
  const n = name.toLowerCase();
  const c = company.toLowerCase();
  for (const row of allCustomers) {
    const contactName = (row.contactName || row.contact || row.linkman || "").toLowerCase();
    const companyName = (row.name || row.customerName || row.shortName || "").toLowerCase();
    const email = (row.email || "").toLowerCase();
    if (contactName.includes(n) || companyName.includes(n) || email.includes(n) ||
        contactName.includes(c) || companyName.includes(c) || email.includes(c)) {
      return { matched: true, customerId: row.id, customerName: row.name || row.customerName };
    }
  }
  return { matched: false };
}

async function main() {
  console.log("Loading all CRM customers...");
  const allCustomers = await loadAllCustomers();
  console.log(`Loaded ${allCustomers.length} customers\n`);

  let fixed = 0, notFound = [];

  for (const f of FIXES) {
    const result = matchCustomer(allCustomers, f.id, f.company);
    
    if (result.matched) {
      const now = new Date();
      const ts = `${now.getFullYear()}-${String(now.getMonth()+1).padStart(2,"0")}-${String(now.getDate()).padStart(2,"0")} ${String(now.getHours()).padStart(2,"0")}:${String(now.getMinutes()).padStart(2,"0")}:${String(now.getSeconds()).padStart(2,"0")}`;
      
      const r = await client.addFollowRecord({
        customerId: result.customerId,
        content: f.content,
        planningTime: ts,
        feedbackOperator: 183006,
      });
      
      if (r.json?.success) {
        fixed++;
        console.log(`✅ ${f.id} → ${result.customerName}`);
      } else {
        console.log(`⚠️ ${f.id} → ${result.customerName} (失败)`);
      }
    } else {
      notFound.push(f.id);
      console.log(`❌ ${f.id} → 未找到`);
    }
  }

  console.log(`\n===== 修复完成 =====`);
  console.log(`已修复: ${fixed}`);
  if (notFound.length > 0) console.log(`未找到: ${notFound.join(", ")}`);
}

main().catch(console.error);
