import { readFileSync } from "fs";

const COOKIE = "Qs_lvt_382761=1781631952; Hm_lvt_e76f42e145e722198c8bbc08c3b84314=1781631959; HMACCOUNT=7A7C7ADED95637BC; language=zh; Qs_pv_382761=3717785015376907300%2C898033854656484900; Hm_lpvt_e76f42e145e722198c8bbc08c3b84314=1781632366; releaseCenterLoginInfo=502662_786718; 5; sajssdk_2015_cross_new_user=1; sensorsdata2015jssdkcross=%7B%22distinct_id%22%3A%22786718%22%2C%22first_id%22%3A%2219ed1938aa2412-0a947dcaa26cbc-26061051-2073600-19ed1938aa3f6e%22%2C%22props%22%3A%7B%7D%2C%22%24device_id%22%3A%2219ed1938aa2412-0a947dcaa26cbc-26061051-2073600-19ed1938aa3f6e%22%7D; tgw_l7_route=a5f93c5498360a3e3582c320fcd2df2d; userLoginInfoSaas=%7B%22userName%22%3A%22bliiot03%22%7D; lname=bliiot03; releaseCenterToken=e0512e6c-2b3d-4545-bacb-7cd2d1bbfeaf; JOINF_SESSION=YWI5NjMzYzEtNDM4Ny00Zjc4LTkxNjEtN2VkNTNiZmM0Mzk0";

const HEADERS = {
  Cookie: COOKIE,
  "X-Cid": "71376",
  "X-User": "183006",
};

async function searchAllCustomers() {
  const results = [];
  
  for (let page = 1; page <= 40; page++) {
    const url = `https://trade.joinf.com/rapi/d/customers?num=${page}&paging=true&size=50`;
    const res = await fetch(url, { headers: HEADERS });
    const data = await res.json();
    const values = data?.data?.values;
    if (!values || values.length === 0) break;

    for (const row of values) {
      // Check ALL fields for Arnold/Chimambo/ZODSAT
      const allFields = Object.values(row).filter(Boolean).map(v => String(v).toLowerCase()).join(" ");
      if (allFields.includes("arnold") || allFields.includes("chimambo") || allFields.includes("zodsat")) {
        results.push({
          id: row.id,
          name: row.name || row.customerName,
          contactName: row.contactName || row.contact || row.linkman || "N/A",
          email: row.email || "N/A",
          phone: row.phone || row.mobile || "N/A",
          country: row.country || "N/A",
          description: (row.description || "").substring(0, 150),
          allFields: Object.entries(row).filter(([k,v]) => v).map(([k,v]) => `${k}=${v}`).join(" | "),
        });
      }
    }
  }
  return results;
}

async function main() {
  console.log("Searching all CRM customers for Arnold/Chimambo/ZODSAT...\n");
  const results = await searchAllCustomers();
  
  if (results.length === 0) {
    console.log("❌ No customer found with Arnold/Chimambo/ZODSAT in any field.");
    console.log("\nLet me also check the newly created customer (ID: 238930372)...");
    
    // Check the customer I just created
    const res = await fetch(`https://trade.joinf.com/rapi/d/customers/238930372/1`, { headers: HEADERS });
    const detail = await res.json();
    console.log("\nNewly created customer detail:");
    const cats = detail.data || [];
    for (const cat of cats) {
      console.log(`\n--- ${cat.categoryName} ---`);
      if (cat.columnData) {
        for (const [col, val] of Object.entries(cat.columnData)) {
          if (val && val.value !== null && val.value !== "" && val.value !== undefined) {
            console.log(`   ${col}: ${val.value}`);
          }
        }
      }
    }
  } else {
    console.log(`✅ Found ${results.length} matching customer(s):\n`);
    for (const r of results) {
      console.log(`ID: ${r.id}`);
      console.log(`Name: ${r.name}`);
      console.log(`Contact: ${r.contactName}`);
      console.log(`Email: ${r.email}`);
      console.log(`Phone: ${r.phone}`);
      console.log(`Country: ${r.country}`);
      console.log(`Desc: ${r.description}`);
      console.log("---");
    }
  }
}

main().catch(console.error);
