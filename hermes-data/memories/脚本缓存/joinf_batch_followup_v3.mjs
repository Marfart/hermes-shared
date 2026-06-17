import { createJoinfClient } from "file:///C:/Users/Admin/AppData/Local/hermes/skills/sales/joinf-crm-api/references/joinf-api-client.mjs";

const COOKIE = "Qs_lvt_382761=1781631952; Hm_lvt_e76f42e145e722198c8bbc08c3b84314=1781631959; HMACCOUNT=7A7C7ADED95637BC; language=zh; Qs_pv_382761=3717785015376907300%2C898033854656484900; Hm_lpvt_e76f42e145e722198c8bbc08c3b84314=1781632366; releaseCenterLoginInfo=502662_786718; 5; sajssdk_2015_cross_new_user=1; sensorsdata2015jssdkcross=%7B%22distinct_id%22%3A%22786718%22%2C%22first_id%22%3A%2219ed1938aa2412-0a947dcaa26cbc-26061051-2073600-19ed1938aa3f6e%22%2C%22props%22%3A%7B%7D%2C%22%24device_id%22%3A%2219ed1938aa2412-0a947dcaa26cbc-26061051-2073600-19ed1938aa3f6e%22%7D; tgw_l7_route=a5f93c5498360a3e3582c320fcd2df2d; userLoginInfoSaas=%7B%22userName%22%3A%22bliiot03%22%7D; lname=bliiot03; releaseCenterToken=e0512e6c-2b3d-4545-bacb-7cd2d1bbfeaf; JOINF_SESSION=YWI5NjMzYzEtNDM4Ny00Zjc4LTkxNjEtN2VkNTNiZmM0Mzk0";

const client = createJoinfClient({
  cookie: COOKIE,
  xCid: 71376,
  xUser: 183006,
});

// 上一轮已处理：LA, Subhodeep, Abhinav, Вадим, Areej Procurement, Bikramjit Singh, Dudley May, SYED ALI, Enrique Madrigal
// 这一轮处理剩下的
const CUSTOMERS = [
  { name: "Smart SAC", company: "Smart SAC", followup: "他催我尽快处理清关进口许可证的事，说没有许可证货物可能会被海关弃置，建议我找当地报关行解决" },
  { name: "Ali Jaber", company: "Ali Jaber", followup: "他说目前没有明确的解决时间表，技术团队还在处理问题，他无法给出确切的时间框架" },
  { name: "BL340", company: "BL340", followup: "他问BLRAT激活后外网访问不了，是不是还需要其他配置" },
  { name: "Zantar Abdurab Segeir", company: "Zantar Abdurab Segeir", followup: "他回复了不客气" },
  { name: "Alvick", company: "Alvick", followup: "他回复了感谢我的耐心" },
  { name: "Eli Cohen Kadosh", company: "Eli Cohen Kadosh", followup: "他说很高兴我收到了货物，感谢我的付出，以后有问题随时联系他" },
  { name: "Víctor Camino", company: "Víctor Camino", followup: "他回复了感谢" },
  { name: "Hussain Alsayoud", company: "Hussain Alsayoud", followup: "他回复了感谢" },
  { name: "Saddem Mourad", company: "Saddem Mourad", followup: "他回复了感谢我的理解" },
  { name: "Mahde Hassan", company: "Mahde Hassan", followup: "我跟他确认了我们的网关产品目前不支持IEC 104协议的时间戳功能" },
  { name: "BOUSARIA Brahim", company: "BOUSARIA Brahim", followup: "他让我看看这个" },
  { name: "Thamara Banneheka", company: "Thamara Banneheka", followup: "他回复了感谢" },
  { name: "C", company: "C", followup: "他回复了感谢" },
  { name: "Guillaume Jonville", company: "Guillaume Jonville", followup: "他回复了感谢" },
  { name: "Eng", company: "Eng", followup: "他回复了感谢" },
  { name: "anubius696", company: "anubius696", followup: "他回复说最好后天再问，明天发货" },
  { name: "Miguel alvarez", company: "Miguel alvarez", followup: "他回复了感谢（西班牙语）" },
  { name: "Peer IDE Security Engg", company: "Peer IDE Security Engg", followup: "他问我有没有更新" },
  { name: "Patricio González", company: "Patricio González", followup: "他问我有没有更新" },
  { name: "Rafaqat Ali", company: "Rafaqat Ali", followup: "他问我有没有新消息" },
  { name: "Francisco Ramos", company: "Francisco Ramos", followup: "他问我有没有新消息" },
  { name: "Andrés Montoya", company: "Andrés Montoya", followup: "他问我有没有新消息" },
  { name: "Nyein Chan Lu", company: "Nyein Chan Lu", followup: "他问我有没有新消息" },
  { name: "Ion", company: "Ion", followup: "他问我有没有更新" },
  { name: "Haythem Sassi", company: "Haythem Sassi", followup: "他问我有没有更新" },
  { name: "Sandra Ayu", company: "Sandra Ayu", followup: "他回复了好的谢谢" },
  { name: "Wecon", company: "Wecon", followup: "他回复说看到了" },
  { name: "Тт", company: "Тт", followup: "他说他的同事会负责我的订单" },
  { name: "Dunja", company: "Dunja", followup: "他问我还要不要他发报价，还是这个型号不符合我的要求" },
  { name: "Harbin Sulbarán", company: "Harbin Sulbarán", followup: "他问我是否还对我们的产品感兴趣" },
  { name: "Sa16", company: "Sa16", followup: "他说是的，而且价格还涨了" },
  { name: "huy hoang", company: "huy hoang", followup: "他问我是否还对我们的产品感兴趣" },
  { name: "Bader", company: "Bader", followup: "他问我是否还对我们的产品感兴趣" },
  { name: "Pranit Patil", company: "Pranit Patil", followup: "他回复说抱歉回复晚了" },
  { name: "Mojtaba Jahani", company: "Mojtaba Jahani", followup: "他问我的客户是否还对我们的产品感兴趣" },
  { name: "Saulo Madruga", company: "Saulo Madruga | ENGIPROT", followup: "他问我是否还对我们的产品感兴趣" },
  { name: "NGUYEN DINH THANH", company: "NGUYEN DINH THANH", followup: "他问我有没有什么问题或消息" },
  { name: "Md. Harun Rashid", company: "Md. Harun Rashid", followup: "他发了Hello" },
  { name: "Diego", company: "Diego", followup: "他发了Hello" },
  { name: "Full Frame", company: "Full Frame", followup: "他发了Hello" },
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

  let found = 0, added = 0, notFound = [];

  for (const c of CUSTOMERS) {
    const result = matchCustomer(allCustomers, c.name, c.company);
    
    if (result.matched) {
      found++;
      const now = new Date();
      const ts = `${now.getFullYear()}-${String(now.getMonth()+1).padStart(2,"0")}-${String(now.getDate()).padStart(2,"0")} ${String(now.getHours()).padStart(2,"0")}:${String(now.getMinutes()).padStart(2,"0")}:${String(now.getSeconds()).padStart(2,"0")}`;
      
      const r = await client.addFollowRecord({
        customerId: result.customerId,
        content: c.followup,
        planningTime: ts,
        feedbackOperator: 183006,
      });
      
      if (r.json?.success) {
        added++;
        console.log(`✅ ${c.name} → ${result.customerName} ✓`);
      } else {
        console.log(`⚠️ ${c.name} → ${result.customerName} (跟进失败)`);
      }
    } else {
      notFound.push(c.name);
      console.log(`❌ ${c.name} → CRM中未找到`);
    }
  }

  console.log(`\n===== 汇总 =====`);
  console.log(`找到客户: ${found}`);
  console.log(`已添加跟进: ${added}`);
  console.log(`未找到: ${notFound.length}`);
  if (notFound.length > 0) console.log(`名单: ${notFound.join(", ")}`);
}

main().catch(console.error);
