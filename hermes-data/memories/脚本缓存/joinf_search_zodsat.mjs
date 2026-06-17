import { readFileSync } from "fs";

const auth = JSON.parse(readFileSync("C:\\Users\\Admin\\Documents\\Codex\\2026-06-17\\codex-https-trade-joinf-com-api\\outputs\\live_auth.json", "utf8"));

async function searchCustomers(keyword) {
  for (let page = 1; page <= 40; page++) {
    const url = `https://trade.joinf.com/rapi/d/customers?num=${page}&paging=true&size=50`;
    const res = await fetch(url, {
      headers: {
        Cookie: auth.cookie,
        "X-Cid": auth.xCid,
        "X-User": auth.xUser,
      },
    });
    const data = await res.json();
    const values = data?.data?.values;
    if (!values || values.length === 0) break;

    for (const row of values) {
      const searchFields = [
        row.name, row.customerName, row.shortName,
        row.email, row.phone, row.mobile,
        row.country, row.description, row.remark,
        row.contactName, row.contact, row.contactPerson,
        row.linkman,
      ].filter(Boolean).map(s => String(s).toLowerCase()).join(" ");

      if (searchFields.includes(keyword.toLowerCase())) {
        console.log(`\n✅ Page ${page} | ID: ${row.id}`);
        console.log(`   Name: ${row.name || row.customerName || "N/A"}`);
        console.log(`   Contact: ${row.contactName || row.contact || row.linkman || "N/A"}`);
        console.log(`   Email: ${row.email || "N/A"}`);
        console.log(`   Phone: ${row.phone || row.mobile || "N/A"}`);
        console.log(`   Country: ${row.country || "N/A"}`);
        console.log(`   Desc: ${(row.description || "").substring(0, 100)}`);
        return row;
      }
    }
  }
  return null;
}

async function main() {
  // Try multiple keywords
  const keywords = ["ZODSAT", "Zimbabwe", "Chimambo", "Arnold", "transformer", "transformer anti-theft"];
  
  for (const kw of keywords) {
    console.log(`\n=== Searching: "${kw}" ===`);
    const result = await searchCustomers(kw);
    if (result) {
      console.log("\n🎯 FOUND! Now let's get full detail...");
      
      // Get full detail
      const detailRes = await fetch(`https://trade.joinf.com/rapi/d/customers/${result.id}/1`, {
        headers: {
          Cookie: auth.cookie,
          "X-Cid": auth.xCid,
          "X-User": auth.xUser,
        },
      });
      const detail = await detailRes.json();
      
      // Print all categories and their fields
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
      return;
    }
  }
  console.log("\n❌ Not found in CRM with any keyword");
}

main().catch(console.error);
