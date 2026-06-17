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

async function main() {
  // Step 1: Create customer
  console.log("Creating customer: Arnold Chimambo...");
  
  const createResult = await client.createCustomer({
    templatePayload: {
      models: [
        { columnName: "name", value: "Arnold Chimambo", displayValue: "Arnold Chimambo", originalValue: "", displayOriginalValue: "" },
        { columnName: "shortName", value: "A. Chimambo", displayValue: "A. Chimambo", originalValue: "", displayOriginalValue: "" },
        { columnName: "description", value: "ZODSAT Zimbabwe - 变压器防盗项目。S275+PT100方案，LoRaWAN EU868。正在确认报警触发机制（油温/门磁/螺栓传感器等）。", displayValue: "ZODSAT Zimbabwe - 变压器防盗项目。S275+PT100方案，LoRaWAN EU868。正在确认报警触发机制（油温/门磁/螺栓传感器等）。", originalValue: "", displayOriginalValue: "" },
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
    },
    fields: { name: "Arnold Chimambo", shortName: "A. Chimambo", description: "ZODSAT Zimbabwe - 变压器防盗项目", country: "Zimbabwe" },
    contactFields: { name: "Arnold Chimambo" },
  });

  const customerId = createResult.json?.data;
  if (!customerId) {
    console.log(`❌ Create failed: ${JSON.stringify(createResult.json || createResult.error)}`);
    return;
  }
  console.log(`✅ Customer created! ID: ${customerId}`);

  // Step 2: Add follow-up record
  const now = new Date();
  const ts = `${now.getFullYear()}-${String(now.getMonth()+1).padStart(2,'0')}-${String(now.getDate()).padStart(2,'0')} ${String(now.getHours()).padStart(2,'0')}:${String(now.getMinutes()).padStart(2,'0')}:${String(now.getSeconds()).padStart(2,'0')}`;

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

  const followResult = await client.addFollowRecord({
    customerId,
    content: followContent,
    planningTime: ts,
  });

  if (followResult.json?.data) {
    console.log(`✅ Follow-up added! ID: ${followResult.json.data}`);
  } else {
    console.log(`❌ Follow-up failed: ${JSON.stringify(followResult.json || followResult.error)}`);
  }
}

main().catch(console.error);
