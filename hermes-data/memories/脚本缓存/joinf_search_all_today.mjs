import { readFileSync } from "fs";

const COOKIE = "Qs_lvt_382761=1781631952; Hm_lvt_e76f42e145e722198c8bbc08c3b84314=1781631959; HMACCOUNT=7A7C7ADED95637BC; language=zh; Qs_pv_382761=3717785015376907300%2C898033854656484900; Hm_lpvt_e76f42e145e722198c8bbc08c3b84314=1781632366; releaseCenterLoginInfo=502662_786718; 5; sajssdk_2015_cross_new_user=1; sensorsdata2015jssdkcross=%7B%22distinct_id%22%3A%22786718%22%2C%22first_id%22%3A%2219ed1938aa2412-0a947dcaa26cbc-26061051-2073600-19ed1938aa3f6e%22%2C%22props%22%3A%7B%7D%2C%22%24device_id%22%3A%2219ed1938aa2412-0a947dcaa26cbc-26061051-2073600-19ed1938aa3f6e%22%7D; tgw_l7_route=a5f93c5498360a3e3582c320fcd2df2d; userLoginInfoSaas=%7B%22userName%22%3A%22bliiot03%22%7D; lname=bliiot03; releaseCenterToken=e0512e6c-2b3d-4545-bacb-7cd2d1bbfeaf; JOINF_SESSION=YWI5NjMzYzEtNDM4Ny00Zjc4LTkxNjEtN2VkNTNiZmM0Mzk0";

const HEADERS = {
  Cookie: COOKIE,
  "X-Cid": "71376",
  "X-User": "183006",
};

// Today's customers from WhatsApp
const TARGETS = [
  { name: "LA", company: "LA", desc: "22:30 确认了电池不包含在标准发货中" },
  { name: "Abdul Rahman Zafar", company: "Raas", desc: "22:27 👍了我们的详细说明，说明天回办公室转给技术部" },
  { name: "Subhodeep", company: "Subhodeep", desc: "21:06 说定制项目申请流程需要时间，有进展会尽快通知" },
  { name: "Miguel", company: "BL 120 BN", desc: "21:02 发了2张照片（未读）" },
  { name: "C", company: "C", desc: "20:28 🙏了\"I will thanks!\"" },
  { name: "Вадим", company: "Вадим", desc: "19:41 🙏了\"Okay, thank you. I'm waiting for your response.\"" },
  { name: "Abhinav", company: "Abhinav", desc: "19:20 说两款入门级产品卖得很好" },
  { name: "Thamara Banneheka", company: "Thamara Banneheka", desc: "19:11 🙏了\"Thanks\"" },
  { name: "Zantar Abdurab Segeir", company: "Zantar Abdurab Segeir", desc: "14:04 You're welcome!" },
  { name: "Alvick", company: "Alvick", desc: "12:00 Thank you for your patience" },
  { name: "Areej Procurement", company: "Areej Procurement", desc: "昨天 问DHL tracking number" },
  { name: "Smart SAC", company: "Smart SAC", desc: "昨天 催进口许可证清关" },
  { name: "anubius696", company: "anubius696", desc: "昨天 🙏了俄语消息" },
  { name: "Miguel alvarez", company: "Miguel alvarez", desc: "昨天 gracias" },
  { name: "Eli Cohen Kadosh", company: "Eli Cohen Kadosh", desc: "星期一 很高兴我们收到货了" },
  { name: "Ali Jaber", company: "Ali Jaber", desc: "星期五 说技术团队在解决问题但没有时间表" },
  { name: "BOUSARIA Brahim", company: "BOUSARIA Brahim", desc: "星期四 Please view this" },
  { name: "Mahde Hassan", company: "Mahde Hassan", desc: "6月8日 确认网关不支持IEC 104时间戳" },
  { name: "Hussain Alsayoud", company: "Hussain Alsayoud", desc: "6月8日 Thank you!" },
  { name: "Rafaqat Ali", company: "Rafaqat Ali", desc: "6月4日 问有没有新消息" },
  { name: "Francisco Ramos", company: "Francisco Ramos", desc: "6月4日 问有没有新消息" },
  { name: "Andrés Montoya", company: "Andrés Montoya", desc: "6月4日 问有没有新消息" },
  { name: "Nyein Chan Lu", company: "Nyein Chan Lu", desc: "6月4日 问有没有新消息" },
];

async function searchCRM() {
  const allCustomers = [];
  
  for (let page = 1; page <= 40; page++) {
    const url = `https://trade.joinf.com/rapi/d/customers?num=${page}&paging=true&size=50`;
    const res = await fetch(url, { headers: HEADERS });
    const data = await res.json();
    const values = data?.data?.values;
    if (!values || values.length === 0) break;
    allCustomers.push(...values);
  }
  
  console.log(`Total CRM customers loaded: ${allCustomers.length}\n`);
  
  for (const target of TARGETS) {
    const targetName = target.name.toLowerCase();
    const targetCompany = target.company.toLowerCase();
    
    let matched = null;
    let matchedField = "";
    
    for (const row of allCustomers) {
      const contactName = (row.contactName || row.contact || row.linkman || "").toLowerCase();
      const companyName = (row.name || row.customerName || row.shortName || "").toLowerCase();
      const email = (row.email || "").toLowerCase();
      
      if (contactName.includes(targetName) || companyName.includes(targetName) || companyName.includes(targetCompany)) {
        matched = row;
        if (contactName.includes(targetName)) matchedField = "联系人";
        else if (companyName.includes(targetName)) matchedField = "公司名";
        else matchedField = "公司名(模糊)";
        break;
      }
    }
    
    if (matched) {
      console.log(`✅ ${target.name.padEnd(25)} → 已存在 | ID: ${matched.id} | ${matched.name} | 匹配: ${matchedField}`);
    } else {
      console.log(`❌ ${target.name.padEnd(25)} → 未找到`);
    }
  }
  
  return allCustomers;
}

searchCRM().catch(console.error);
