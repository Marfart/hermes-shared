---
name: whatsapp-to-joinf-crm
version: 1.2.0
description: WhatsApp读消息 → 富通CRM查询/新增/跟进完整管道。从WhatsApp Web读取客户消息，提取联系人信息，在富通CRM中查询匹配，然后新增客户或添加跟进记录。
tags: [whatsapp, joinf, crm, follow-up, customer]
requires_skills: [human-like-behavior, sales/joinf-crm-api]
---

# WhatsApp → 富通CRM 管道 🐴✨

## 总原则

1. **先查后增** — 每次新增跟进前，必须查询CRM中是否已有该客户
2. **三字段匹配铁则** — 查询以下三个字段，**任意一个匹配就不能新建**：
   - 🔍 **联系人姓名**（contactName / linkman / contact）
   - 🔍 **公司名**（name / customerName / shortName）
   - 🔍 **邮箱**（email）
3. 匹配 → 在原有客户档案下**添加跟进记录**
4. 三字段都不匹配 → 才考虑**新建客户**
5. **新增客户必须有邮箱** — 邮箱从WhatsApp对话中提取。如果对话中没有邮箱，**报告给Kali让她去问客户要邮箱**，拿到邮箱后才能创建客户记录。**小马不能直接在WhatsApp上给客户发消息。**
6. **WhatsApp操作必须加载 human-like-behavior 技能** — 所有浏览器操作要有随机延迟，像人一样
7. **读WhatsApp消息时必须像人一样** — 打开对话后先滚到顶部，从第一条开始逐条往下读，不能只看最后一条预览
8. **一次只能看一个人的聊天** — 像人一样，看完一个客户的全部对话，处理完（查CRM+加跟进），再看下一个。不能一次性批量翻多个人的聊天
9. **富通API操作加载 sales/joinf-crm-api 技能** — 使用API客户端

## 完整流程

### Step 0: 准备工作

```bash
# 1. 确保Chrome CDP端口9223已启动（WhatsApp Web）
# 2. 确保Chrome CDP端口9226或已有登录态（富通天下）
# 3. 获取富通认证信息（cookie + xCid + xUser）
```

### Step 1: 读WhatsApp消息

加载 `human-like-behavior` 技能，通过 **Hermes原生瀏覽器工具**（`browser_navigate`、`browser_click` 等）連接 **CDP 9223端口**（你本機已登錄好WhatsApp Web的Chrome）：

1. 用 `browser_navigate` 打開 `https://web.whatsapp.com`（CDP會連接到已有登錄態的Chrome）
2. 等待頁面加載，用 `browser_snapshot` 查看聊天列表
3. 找到目標客戶的聊天（按時間排序，看最新消息）
4. 用 `browser_click` 點擊進入聊天
5. 用 `browser_scroll(direction='up')` 滾動到頂部，逐條讀取完整對話
6. 提取關鍵信息：
   - **联系人姓名**（聊天标题）
   - **公司名**（从对话内容推断）
   - **邮箱**（如果对话中有）
   - **电话**（如果对话中有）
   - **今日跟进内容**（所有新消息的时间线）

**⚠️ 重要：絕對不要用 Playwright MCP 工具（`mcp_playwright_browser_*`）！**
- Playwright啟動的是全新瀏覽器實例，容易被WhatsApp檢測為自動化
- 必須用 Hermes原生瀏覽器工具（`browser_navigate`、`browser_click`、`browser_snapshot`、`browser_scroll`、`browser_type`）
- 這些工具通過CDP連接到你本機已登錄的Chrome，行為更自然

**⚠️ 仿人操作：所有操作之間加隨機延遲**
- 點擊聊天之間：`random.uniform(2, 8)` 秒
- 滾動時慢慢滾，不要biu一下到底
- 每操作10個動作休息15-45秒
- 不要連續快速點擊

### Step 2: 查询CRM

加载 `sales/joinf-crm-api` 技能，使用API客户端查询：

```javascript
// 查询所有客户（遍历所有页）
for (let page = 1; page <= 40; page++) {
  const url = `https://trade.joinf.com/rapi/d/customers?num=${page}&paging=true&size=50`;
  const res = await fetch(url, { headers: { Cookie, "X-Cid": xCid, "X-User": xUser } });
  const data = await res.json();
  const values = data?.data?.values;
  if (!values || values.length === 0) break;

  for (const row of values) {
    // 检查三个字段：联系人姓名、公司名、邮箱
    const contactName = (row.contactName || row.contact || row.linkman || "").toLowerCase();
    const companyName = (row.name || row.customerName || row.shortName || "").toLowerCase();
    const email = (row.email || "").toLowerCase();
    
    const searchTerms = [contactName, companyName, email].join(" ");
    
    if (searchTerms.includes(targetName.toLowerCase()) ||
        searchTerms.includes(targetCompany.toLowerCase()) ||
        (targetEmail && searchTerms.includes(targetEmail.toLowerCase()))) {
      // ✅ 匹配！记录客户ID
      return { matched: true, customerId: row.id, customerName: row.name };
    }
  }
}
```

### Step 3: 决策分支

```
                    ┌─────────────────────┐
                    │  查询CRM三字段匹配    │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │  任意一个匹配？       │
                    └──────┬───────┬──────┘
                           │       │
                        ┌──▼──┐ ┌─▼──────────┐
                        │ 是  │ │    否       │
                        └──┬──┘ └──┬─────────┘
                           │       │
              ┌────────────▼──┐  ┌─▼──────────────────┐
              │ 在原客户下     │  │ WhatsApp对话中有    │
              │ 添加跟进记录   │  │ 邮箱吗？            │
              └───────────────┘  └──┬──────────┬─────┘
                                    │          │
                                 ┌──▼──┐   ┌───▼──────────┐
                                 │ 有  │   │    没有       │
                                 └──┬──┘   └───┬──────────┘
                                    │          │
                              ┌─────▼──────┐ ┌─▼──────────────┐
                              │ 新建客户    │ │ 报告Kali       │
                              │ + 添加跟进  │ │ 让Kali去问邮箱  │
                              └────────────┘ └────────────────┘
```

### Step 4a: 添加跟进记录（已有客户）

```javascript
import { createJoinfClient } from "file:///C:/Users/Admin/AppData/Local/hermes/skills/sales/joinf-crm-api/references/joinf-api-client.mjs";

const client = createJoinfClient({ cookie, xCid: 71376, xUser: 183006 });

const now = new Date();
const ts = `${now.getFullYear()}-${String(now.getMonth()+1).padStart(2,"0")}-${String(now.getDate()).padStart(2,"0")} ${String(now.getHours()).padStart(2,"0")}:${String(now.getMinutes()).padStart(2,"0")}:${String(now.getSeconds()).padStart(2,"0")}`;

const result = await client.addFollowRecord({
  customerId: matchedCustomerId,
  content: `他回复说理解电池不包含在标准发货中，我跟他确认了这件事`,
  planningTime: ts,
  feedbackOperator: 183006,
});
```

### Step 4b: 新建客户 + 添加跟进记录（新客户）

**⚠️ 前提条件：必须从WhatsApp对话中提取到客户的邮箱！**
如果对话中没有邮箱，报告给Kali让她去问客户要邮箱。

```javascript
// 1. 创建客户（邮箱必填）
const createResult = await client.createCustomer({
  templatePayload: {
    models: [
      { columnName: "name", value: companyName, displayValue: companyName, originalValue: "", displayOriginalValue: "" },
      { columnName: "shortName", value: shortName, displayValue: shortName, originalValue: "", displayOriginalValue: "" },
      { columnName: "description", value: description, displayValue: description, originalValue: "", displayOriginalValue: "" },
      { columnName: "displayType", value: 236496, displayValue: "潜在工业客户", originalValue: 236496, displayOriginalValue: "潜在工业客户" },
      { columnName: "country", value: country, displayValue: country, originalValue: "", displayOriginalValue: "" },
      { columnName: "email", value: customerEmail, displayValue: customerEmail, originalValue: "", displayOriginalValue: "" }, // ⚠️ 邮箱必填！
    ],
    contacts: [{ models: [{ columnName: "name", value: contactName, displayValue: contactName, originalValue: "", displayOriginalValue: "" }] }],
    banks: [],
    customerAttachmentDtoList: [],
    tagList: [],
    markModel: { customerId: 0, companyId: 71376, operatorId: 183006, isChanged: false },
  },
  fields: { name: companyName, shortName: shortName, description: description, country: country, email: customerEmail },
  contactFields: { name: contactName },
});

const newCustomerId = createResult.json.data;

// 2. 添加跟进记录（同上Step 4a）
```

## 跟进记录内容格式

**⚠️ 语气铁则：用Kali第一人称！假装是Kali自己在记录今天干了什么**
- ❌ 不要写"WhatsApp跟进 YYYY-MM-DD"
- ❌ 不要写具体时间点（如"17:35"）
- ❌ 不要写"状态：跟进中"
- ❌ 不要用"我方"、"客户"、"我们"
- ✅ **"我" = Kali**（干活的人），**"他/她" = 客户**
- ✅ **每条跟进都必须有"我"做了什么**，不能只有"他"做了什么
- ✅ **跟进内容不能写"谢谢"、"再见"等客套话** — 如果对话最后只是客套话，要往上翻找真正有内容的对话
- ✅ 只写跟项目/业务相关的内容，比如：
  - "他回复说理解电池不包含在标准发货中，我跟他确认了这件事"
  - "他问我付款进度，我说还在等老板确认"
  - "我把老板的3个技术问题发给他了"
  - "他给了详细回复，讲了热力学分析和硬件联动机制"
  - "我又追问了他除了油温外还有没有其他触发机制"
- ❌ **不能把价格/报价金额放进跟进内容** — 跟进记录只写业务沟通内容，不写具体价格数字
- ❌ "他回复了感谢" ❌ → 往上翻找真正的内容

## 关键铁则

### 仿人操作铁则（必读）

**每次读WhatsApp消息前，必须加载 human-like-behavior 技能！**

所有浏览器操作必须像人一样：
- 点击聊天之间加 **2-8秒随机延迟**
- 滚动时 **慢慢滚**，不要biu一下到底
- 每操作10个动作 **休息15-45秒**
- 不要连续快速点击，不要biubiubiu
- 读消息时像人一样从上往下看，不是瞬间抓取

### 查询三字段匹配规则

| 字段 | CRM字段名 | 匹配方式 |
|------|-----------|----------|
| 联系人姓名 | contactName / contact / linkman | 包含匹配（不区分大小写） |
| 公司名 | name / customerName / shortName | 包含匹配（不区分大小写） |
| 邮箱 | email | 精确匹配（不区分大小写） |

**注意**：查询时必须遍历CRM所有页（每页50条，最多40页=2000条），不能只查第一页。

### 认证过期处理

富通API认证约30分钟过期。如果API返回401 Unauthorized：
1. 切换到富通浏览器标签页
2. 检查是否已登录（看URL是否在 trade.joinf.com/tms/ 下）
3. 如果已登录，从浏览器获取新cookie
4. 如果未登录，重新登录（用户名bliiot03，密码Kali1314520!）
5. 拼图验证码：直接点击"安全登录"按钮可绕过（Vue前端逻辑）

### 跟进记录API注意事项

- 必须使用 `buildFollowRecordPayload` 生成的完整models数组格式
- 必须传 `feedbackOperator: 183006`
- 内容不要太长（建议≤500字），太长可能报"系统繁忙"
- 时间格式：`YYYY-MM-DD HH:mm:ss`

### 新建客户API注意事项

- `displayType: 236496` 必填（潜在工业客户）
- `contacts[0].models` 中 `name` 不能为空
- `markModel` 必须包含 `{ customerId: 0, companyId: 71376, operatorId: 183006, isChanged: false }`

## 常见错误处理

| 错误 | 原因 | 解决 |
|------|------|------|
| 401 Unauthorized | 认证过期 | 重新获取cookie |
| 建档时客户类型不能为空 | 缺displayType | 加 displayType: 236496 |
| 建档时联系人姓名不能为空 | contacts name为空 | 确保有联系人姓名 |
| 系统繁忙，请稍后再试 | 跟进内容太长或参数不对 | 缩短内容或用buildFollowRecordPayload |
| 客户已存在（重复创建） | 没查全三字段 | 遍历所有页，检查所有字段 |

## 文件结构

```
skills/sales/whatsapp-to-joinf-crm/
├── SKILL.md                    ← 本文件
└── references/
    └── whatsapp-to-crm-pipeline.mjs  ← 完整管道脚本（可选）
```

## 依赖技能

- `human-like-behavior` — WhatsApp浏览器操作必须像人
- `sales/joinf-crm-api` — 富通CRM API客户端
