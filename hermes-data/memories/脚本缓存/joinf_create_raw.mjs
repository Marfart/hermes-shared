import { readFileSync } from "fs";

const auth = JSON.parse(readFileSync("C:\\Users\\Admin\\Documents\\Codex\\2026-06-17\\codex-https-trade-joinf-com-api\\outputs\\live_auth.json", "utf8"));

async function main() {
  // Create customer
  const body = {
    models: [
      { columnName: "name", value: "Arnold Chimambo", displayValue: "Arnold Chimambo", originalValue: "", displayOriginalValue: "" },
      { columnName: "shortName", value: "A. Chimambo", displayValue: "A. Chimambo", originalValue: "", displayOriginalValue: "" },
      { columnName: "description", value: "ZODSAT Zimbabwe - 变压器防盗项目。S275+PT100方案，LoRaWAN EU868。正在确认报警触发机制。", displayValue: "ZODSAT Zimbabwe - 变压器防盗项目。S275+PT100方案，LoRaWAN EU868。正在确认报警触发机制。", originalValue: "", displayOriginalValue: "" },
      { columnName: "displayType", value: 236496, displayValue: "潜在工业客户", originalValue: 236496, displayOriginalValue: "潜在工业客户" },
      { columnName: "country", value: "Zimbabwe", displayValue: "Zimbabwe", originalValue: "", displayOriginalValue: "" },
    ],
    contacts: [{ models: [{ columnName: "name", value: "Arnold Chimambo", displayValue: "Arnold Chimambo", originalValue: "", displayOriginalValue: "" }] }],
    banks: [],
    customerAttachmentDtoList: [],
    tagList: [],
    markModel: { customerId: 0, companyId: 71376, operatorId: 183006, isChanged: false },
  };

  const res = await fetch("https://trade.joinf.com/rapi/d/customer", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Cookie: auth.cookie,
      "X-Cid": auth.xCid,
      "X-User": auth.xUser,
    },
    body: JSON.stringify(body),
  });

  const text = await res.text();
  console.log("Status:", res.status);
  console.log("Response:", text.substring(0, 1000));

  // If successful, try to add follow-up
  try {
    const json = JSON.parse(text);
    if (json.data) {
      const customerId = json.data;
      console.log("\nCustomer ID:", customerId);

      // Add follow-up
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
状态：跟进中，客户对S275+PT100方案感兴趣`,
        planningTime: ts,
      };

      const followRes = await fetch("https://trade.joinf.com/rapi/m/follow/add", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Cookie: auth.cookie,
          "X-Cid": auth.xCid,
          "X-User": auth.xUser,
        },
        body: JSON.stringify(followBody),
      });

      const followText = await followRes.text();
      console.log("\nFollow-up Status:", followRes.status);
      console.log("Follow-up Response:", followText.substring(0, 500));
    }
  } catch (e) {
    console.log("Parse error:", e.message);
  }
}

main().catch(console.error);
