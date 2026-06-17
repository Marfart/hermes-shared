/**
 * WhatsApp → 富通CRM 完整管道脚本
 * 
 * 用法：
 *   1. 先确保Chrome CDP 9223已启动（WhatsApp Web已登录）
 *   2. 确保富通已登录（cookie有效）
 *   3. 修改 TARGET_NAME / TARGET_COMPANY / TARGET_EMAIL 为目标客户信息
 *   4. 修改 FOLLOW_CONTENT 为跟进内容
 *   5. node whatsapp-to-crm-pipeline.mjs
 * 
 * 三字段匹配铁则：联系人姓名 / 公司名 / 邮箱，任意一个匹配就不能新建
 */

import { createJoinfClient, buildFollowRecordPayload } from "file:///C:/Users/Admin/AppData/Local/hermes/skills/sales/joinf-crm-api/references/joinf-api-client.mjs";

// ============================================================
// 配置区 — 每次使用前修改这里
// ============================================================

const TARGET_NAME = "Arnold Chimambo";        // 联系人姓名（从WhatsApp聊天标题获取）
const TARGET_COMPANY = "AC company";           // 公司名（从对话内容推断）
const TARGET_EMAIL = "";                       // 邮箱（如果对话中有）
const TARGET_COUNTRY = "Zimbabwe";             // 国家
const TARGET_PHONE = "";                       // 电话（如果对话中有）

// ⚠️ 语气铁则：用Kali第一人称！假装是Kali自己在记录今天干了什么
// ❌ 不要写"WhatsApp跟进 YYYY-MM-DD"、时间点、"状态：跟进中"
// ❌ 不要用"我方"、"客户"、"我们"
// ❌ 不要写"谢谢"、"再见"等客套话 — 往上翻找真正有内容的对话
// ✅ "我"=Kali（干活的人），"他/她"=客户
// ✅ 每条跟进都必须有"我"做了什么
// ✅ 只写跟项目/业务相关的内容
const FOLLOW_CONTENT = `他确认了外壳方案可以接受
他问我付款确认进度，我说还在等老板最终确认
我把老板的3个技术问题发给他了：变压器油被盗→温度飙升→报警流程
他给了详细回复，讲了热力学分析和硬件联动机制
我又追问了他：除了油温外还有没有其他触发机制（门磁、螺栓传感器等）`;

// ============================================================
// 认证信息（从浏览器获取）
// ============================================================

const COOKIE = ""; // 从浏览器document.cookie获取
const X_CID = "71376";
const X_USER = "183006";

// ============================================================
// 核心逻辑
// ============================================================

const HEADERS = {
  Cookie: COOKIE,
  "X-Cid": X_CID,
  "X-User": X_USER,
};

const client = createJoinfClient({ cookie: COOKIE, xCid: parseInt(X_CID), xUser: parseInt(X_USER) });

/**
 * 查询CRM中是否已有该客户（三字段匹配）
 */
async function findCustomer(name, company, email) {
  const nameLower = (name || "").toLowerCase().trim();
  const companyLower = (company || "").toLowerCase().trim();
  const emailLower = (email || "").toLowerCase().trim();

  for (let page = 1; page <= 40; page++) {
    const url = `https://trade.joinf.com/rapi/d/customers?num=${page}&paging=true&size=50`;
    const res = await fetch(url, { headers: HEADERS });
    const data = await res.json();
    const values = data?.data?.values;
    if (!values || values.length === 0) break;

    for (const row of values) {
      // 提取三字段
      const contactName = (row.contactName || row.contact || row.linkman || "").toLowerCase();
      const companyName = (row.name || row.customerName || row.shortName || "").toLowerCase();
      const rowEmail = (row.email || "").toLowerCase();

      // 任意一个匹配即返回
      if (
        (nameLower && contactName.includes(nameLower)) ||
        (companyLower && companyName.includes(companyLower)) ||
        (emailLower && rowEmail.includes(emailLower))
      ) {
        return {
          matched: true,
          customerId: row.id,
          customerName: row.name || row.customerName,
          matchedField: nameLower && contactName.includes(nameLower) ? "contactName" :
                        companyLower && companyName.includes(companyLower) ? "companyName" : "email",
        };
      }
    }
  }
  return { matched: false };
}

/**
 * 新建客户
 */
async function createCustomer(name, company, country, contactName, email) {
  const body = {
    models: [
      { columnName: "name", value: company, displayValue: company, originalValue: "", displayOriginalValue: "" },
      { columnName: "shortName", value: name, displayValue: name, originalValue: "", displayOriginalValue: "" },
      { columnName: "description", value: `${country}客户，联系人: ${contactName}`, displayValue: `${country}客户，联系人: ${contactName}`, originalValue: "", displayOriginalValue: "" },
      { columnName: "displayType", value: 236496, displayValue: "潜在工业客户", originalValue: 236496, displayOriginalValue: "潜在工业客户" },
      { columnName: "country", value: country, displayValue: country, originalValue: "", displayOriginalValue: "" },
      { columnName: "email", value: email, displayValue: email, originalValue: "", displayOriginalValue: "" },
    ],
    contacts: [{ models: [{ columnName: "name", value: contactName, displayValue: contactName, originalValue: "", displayOriginalValue: "" }] }],
    banks: [],
    customerAttachmentDtoList: [],
    tagList: [],
    markModel: { customerId: 0, companyId: 71376, operatorId: 183006, isChanged: false },
  };

  const res = await fetch("https://trade.joinf.com/rapi/d/customer", {
    method: "POST",
    headers: { "Content-Type": "application/json", ...HEADERS },
    body: JSON.stringify(body),
  });

  const json = await res.json();
  if (json.success && json.data) {
    console.log(`✅ 客户创建成功! ID: ${json.data}`);
    return json.data;
  }
  throw new Error(`创建客户失败: ${json.errMsg || JSON.stringify(json)}`);
}

/**
 * 添加跟进记录
 */
async function addFollowUp(customerId, content) {
  const now = new Date();
  const ts = `${now.getFullYear()}-${String(now.getMonth()+1).padStart(2,"0")}-${String(now.getDate()).padStart(2,"0")} ${String(now.getHours()).padStart(2,"0")}:${String(now.getMinutes()).padStart(2,"0")}:${String(now.getSeconds()).padStart(2,"0")}`;

  const result = await client.addFollowRecord({
    customerId,
    content,
    planningTime: ts,
    feedbackOperator: 183006,
  });

  if (result.json?.success) {
    console.log(`✅ 跟进记录添加成功! Follow ID: ${JSON.stringify(result.json.data)}`);
  } else {
    throw new Error(`添加跟进失败: ${JSON.stringify(result.json || result.error)}`);
  }
}

// ============================================================
// 主流程
// ============================================================

async function main() {
  console.log("=".repeat(50));
  console.log("WhatsApp → 富通CRM 管道");
  console.log("=".repeat(50));
  console.log(`\n目标客户:`);
  console.log(`  联系人: ${TARGET_NAME}`);
  console.log(`  公司:   ${TARGET_COMPANY}`);
  console.log(`  邮箱:   ${TARGET_EMAIL || "(无)"}`);
  console.log(`  国家:   ${TARGET_COUNTRY}`);

  // Step 1: 查询CRM
  console.log("\n🔍 Step 1: 查询CRM...");
  const result = await findCustomer(TARGET_NAME, TARGET_COMPANY, TARGET_EMAIL);

  if (result.matched) {
    console.log(`✅ 找到匹配客户!`);
    console.log(`  客户ID: ${result.customerId}`);
    console.log(`  客户名: ${result.customerName}`);
    console.log(`  匹配字段: ${result.matchedField}`);

    // Step 2a: 添加跟进
    console.log("\n📝 Step 2: 添加跟进记录...");
    await addFollowUp(result.customerId, FOLLOW_CONTENT);
    console.log("\n🎉 完成! 已在现有客户下添加跟进记录。");
  } else {
    console.log("❌ CRM中未找到匹配客户（三字段均不匹配）");

    // 检查是否有邮箱
    if (!TARGET_EMAIL) {
      console.log("\n⚠️ 没有邮箱! 新增客户必须有邮箱。");
      console.log("请先在WhatsApp上问客户要邮箱，拿到邮箱后再执行此脚本。");
      console.log("步骤: 修改 TARGET_EMAIL 变量后重新运行。");
      return;
    }

    // Step 2b: 新建客户
    console.log("\n🆕 Step 2: 新建客户...");
    const newId = await createCustomer(TARGET_NAME, TARGET_COMPANY, TARGET_COUNTRY, TARGET_NAME, TARGET_EMAIL);

    // Step 3: 添加跟进
    console.log("\n📝 Step 3: 添加跟进记录...");
    await addFollowUp(newId, FOLLOW_CONTENT);
    console.log("\n🎉 完成! 已新建客户并添加跟进记录。");
  }
}

main().catch(err => {
  console.error("\n❌ 管道执行失败:", err.message);
  process.exit(1);
});
