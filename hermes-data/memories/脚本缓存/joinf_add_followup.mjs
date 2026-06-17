import { createJoinfClient } from "file:///C:/Users/Admin/AppData/Local/hermes/skills/sales/joinf-crm-api/references/joinf-api-client.mjs";
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import path from "path";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// Load auth
const auth = JSON.parse(readFileSync("C:\\Users\\Admin\\Documents\\Codex\\2026-06-17\\codex-https-trade-joinf-com-api\\outputs\\live_auth.json", "utf8"));

const client = createJoinfClient({
  cookie: auth.cookie,
  xCid: parseInt(auth.xCid),
  xUser: parseInt(auth.xUser),
});

async function searchCustomer(name) {
  console.log(`Searching for: ${name}...`);
  // Search all pages
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
      const rowName = (row.name || row.customerName || "").toLowerCase();
      const rowEmail = (row.email || "").toLowerCase();
      const rowPhone = (row.phone || row.mobile || "").toLowerCase();
      const searchLower = name.toLowerCase();

      if (rowName.includes(searchLower) || rowEmail.includes(searchLower) || rowPhone.includes(searchLower)) {
        console.log(`\n✅ FOUND on page ${page}:`);
        console.log(`  ID: ${row.id}`);
        console.log(`  Name: ${row.name || row.customerName}`);
        console.log(`  Email: ${row.email || "N/A"}`);
        console.log(`  Phone: ${row.phone || row.mobile || "N/A"}`);
        console.log(`  Country: ${row.country || "N/A"}`);
        return row;
      }
    }
  }
  console.log("❌ Not found in CRM");
  return null;
}

async function addFollowUp(customerId, content) {
  console.log(`\nAdding follow-up record for customer ID ${customerId}...`);
  const now = new Date();
  const ts = `${now.getFullYear()}-${String(now.getMonth()+1).padStart(2,'0')}-${String(now.getDate()).padStart(2,'0')} ${String(now.getHours()).padStart(2,'0')}:${String(now.getMinutes()).padStart(2,'0')}:${String(now.getSeconds()).padStart(2,'0')}`;

  const result = await client.addFollowRecord({
    customerId,
    content,
    planningTime: ts,
  });

  if (result.json?.data) {
    console.log(`✅ Follow-up added! ID: ${result.json.data}`);
  } else {
    console.log(`❌ Failed: ${JSON.stringify(result.json || result.error)}`);
  }
  return result;
}

// Main
async function main() {
  // Try searching by name first
  let customer = await searchCustomer("Arnold Chimambo");
  
  // If not found, try email or other identifiers
  if (!customer) {
    console.log("\nTrying alternative search...");
    customer = await searchCustomer("Chimambo");
  }

  if (customer) {
    const followContent = `【WhatsApp跟进 2026-06-17】
1. 客户确认外壳方案可接受（17:35）
2. 客户询问付款确认进度（13:46），我方回复正在等待老板最终确认（14:13）
3. 我方回复了老板的3个技术问题（20:18）：
   - 变压器油被盗→温度飙升→报警的完整流程说明
4. 客户给了详细回复（21:25）：
   - 热力学分析：变压器油既是绝缘体也是导热体，油位下降后内部组件失去冷却介质，局部温度在负载下急剧上升
   - 硬件联动机制说明
5. 我方回复感谢（22:01）
6. 我方进一步追问（22:45）：
   - 除了油温报警外，是否有其他触发机制（门磁、螺栓传感器等）
   - 等待客户回复中

状态：跟进中，客户对S275+PT100方案感兴趣，正在确认更多技术细节`;

    await addFollowUp(customer.id, followContent);
  } else {
    console.log("\nCustomer not found in CRM. Need to create new record.");
  }
}

main().catch(console.error);
