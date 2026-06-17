---
name: joinf-crm-api
description: 富通天下(金蝶)CRM API操作指南 — 直接HTTP调用富通CRM API，包括新增客户、修改客户资料、添加跟进记录。所有接口已实测验证通过（2026-06-17）。
---

# 富通天下(金蝶)CRM API 操作指南

## 总原则

1. **不要重新登录** — 复用当前已登录浏览器会话
2. **直接HTTP调用** — 不用Playwright点页面，Playwright只用于首次拿认证信息
3. **删除客户直接忽略** — 当前账号没有删除权限
4. **所有写入操作前先读取当前值** — 用于填充 `previousValues`

## 已验证的真实接口（2026-06-17实测）

| 功能 | Method | 路径 | 状态 | 实测日期 |
|------|--------|------|------|----------|
| 新增客户 | POST | `/rapi/d/customer` | ✅ | 2026-06-17 |
| 更新客户资料 | PATCH | `/rapi/d/customer` | ✅ | 2026-06-17 |
| 添加跟进记录 | POST | `/rapi/m/follow/add` | ✅ | 2026-06-17 |
| 读取客户详情 | GET | `/rapi/d/customers/:id/1` | ✅ | 2026-06-17 |
| 删除客户 | POST | `/rapi/d/customers/delete` | ❌ 权限不足 | — |

## 认证信息

需要以下3项，从已登录浏览器CDP获取：

| 字段 | 来源 | 当前值 |
|------|------|--------|
| `Cookie` | 浏览器 Cookie（关键是 `JOINF_SESSION`） | 从浏览器实时读取 |
| `X-Cid` | `localStorage.joinf-compnayId` | `71376` |
| `X-User` | `localStorage.joinf-XUser` | `183006` |

**CDP获取方式（Node.js）**:
```javascript
// 1. curl http://127.0.0.1:9223/json 获取页面ID
// 2. 连接 websocket
const ws = new WebSocket(page.webSocketDebuggerUrl);
// 3. 获取cookies
ws.send(JSON.stringify({id:1, method:'Network.getCookies', params:{urls:['https://trade.joinf.com']}}));
// 4. 获取localStorage
ws.send(JSON.stringify({id:2, method:'Runtime.evaluate', params:{expression:'JSON.stringify({xCid:localStorage.getItem("joinf-compnayId"),xUser:localStorage.getItem("joinf-XUser")})'}}));
```

## API Client

已封装好的client，直接用：

**位置**: `C:\Users\Admin\Documents\Codex\2026-06-17\codex-https-trade-joinf-com-api\outputs\joinf-api-client.mjs`

```javascript
import { createJoinfClient } from './joinf-api-client.mjs';

const client = createJoinfClient({
  cookie: "从浏览器获取的完整cookie字符串",
  xCid: 71376,
  xUser: 183006,
});
```

支持的方法：
- `client.createCustomer({ templatePayload, fields, contactFields })`
- `client.updateCustomer({ customerId, templatePayload, fields, previousValues })`
- `client.addFollowRecord({ customerId, content, planningTime })`
- `client.readCustomerDetail({ customerId })`

---

## 一、新增客户

### 接口
```
POST https://trade.joinf.com/rapi/d/customer
```

### ✅ 已验证成功的模板

```javascript
const createTemplate = {
  models: [
    { columnName: "name", value: "", displayValue: "", originalValue: "", displayOriginalValue: "" },
    { columnName: "shortName", value: "", displayValue: "", originalValue: "", displayOriginalValue: "" },
    { columnName: "description", value: "", displayValue: "", originalValue: "", displayOriginalValue: "" },
    { columnName: "displayType", value: 236496, displayValue: "潜在工业客户", originalValue: 236496, displayOriginalValue: "潜在工业客户" },
  ],
  contacts: [{
    models: [
      { columnName: "name", value: "", displayValue: "", originalValue: "", displayOriginalValue: "" },
    ],
  }],
  banks: [],
  customerAttachmentDtoList: [],
  tagList: [],
  markModel: { customerId: 0, companyId: 71376, operatorId: 183006, isChanged: false },
};
```

### 调用方式

```javascript
const result = await client.createCustomer({
  templatePayload: createTemplate,
  fields: {
    name: "客户名称",        // 必填
    shortName: "简称",       // 可选
    description: "描述",     // 可选
  },
  contactFields: {
    name: "联系人姓名",      // 可选
  },
});

// result.json.data = 新客户的 customerId
// result.json.success = true 表示成功
```

### ⚠️ 必须包含的字段

- `displayType.value = 236496`（潜在工业客户）— **缺少会报错"建档时客户类型不能为空"**
- `markModel.companyId = 71376`
- `markModel.operatorId = 183006`

### 实测结果

| 客户名 | customerId | 联系人 |
|--------|------------|--------|
| Hermes Atlas 79139 | 238858457 | Noah Reed |
| Hermes Nova 40171 | 238858620 | Ethan Cole |
| Hermes Live (2026-06-17) | 238889444 | Test Contact |

---

## 二、更新客户资料

### 接口
```
PATCH https://trade.joinf.com/rapi/d/customer
```

### ⚠️ 关键限制

**不能自己拼最小 patch body！** 必须基于完整模板替换字段。

错误做法 → 返回"系统繁忙"：
```
1. 从 GET /rapi/d/customers/:id/1 读取客户详情
2. 自己平铺字段拼一个最小 body
3. 发 PATCH → 失败！
```

正确做法：
```
1. 先用 readCustomerDetail 读取当前值（用于 previousValues）
2. 构建包含所有必要字段的完整模板
3. 在模板上替换目标字段
4. 发 PATCH
```

### ✅ 已验证成功的模板

```javascript
const patchTemplate = {
  models: [
    { columnName: "name", value: "当前名称", displayValue: "当前名称", originalValue: "当前名称", displayOriginalValue: "当前名称" },
    { columnName: "description", value: "新描述", displayValue: "新描述", originalValue: "旧描述", displayOriginalValue: "旧描述" },
    { columnName: "displayType", value: 236496, displayValue: "潜在工业客户", originalValue: 236496, displayOriginalValue: "潜在工业客户" },
  ],
  contacts: [{ models: [], id: 208899969 }],  // id从readCustomerDetail获取
  banks: [],
  customerAttachmentDtoList: [],
  id: customerId,
  tagList: [],
  markModel: { isChanged: false, customerId: customerId },
};
```

### 调用方式

```javascript
// Step 1: 读取当前值
const detail = await client.readCustomerDetail({ customerId: 238855638 });
// 从 detail.json.data 中提取当前字段值作为 previousValues

// Step 2: 更新
const result = await client.updateCustomer({
  customerId: 238855638,
  templatePayload: patchTemplate,
  fields: { description: "新的描述内容" },
  previousValues: { description: "旧的描述内容" },
});
```

### 注意事项

- `contacts[0].id` 需要从 `readCustomerDetail` 返回数据中获取
- 更新后 `originalValue` 会变成 `previousValues` 中的值
- 实测中 PATCH 报错"建档时联系人姓名不能为空"说明 contacts 模板也需要完整

---

## 三、添加跟进记录

### 接口
```
POST https://trade.joinf.com/rapi/m/follow/add
```

### 调用方式

```javascript
const now = new Date();
const ts = `${now.getFullYear()}-${String(now.getMonth()+1).padStart(2,'0')}-${String(now.getDate()).padStart(2,'0')} ${String(now.getHours()).padStart(2,'0')}:${String(now.getMinutes()).padStart(2,'0')}:${String(now.getSeconds()).padStart(2,'0')}`;

const result = await client.addFollowRecord({
  customerId: 238855638,
  content: "跟进内容",
  planningTime: ts,
  // feedbackOperator 默认使用 xUser (183006)
});

// result.json.data = [followId]
```

### 实测结果

- customerId: 238855638
- 成功创建 Follow ID: 70867552

---

## 四、读取客户详情

### 接口
```
GET https://trade.joinf.com/rapi/d/customers/:customerId/1
```

### 调用方式

```javascript
const result = await client.readCustomerDetail({ customerId: 238855638 });
// result.json.data = 客户详情数组
// 每个元素有 categoryName 和 columnData
// columnData 中每个字段有 value, displayValue, originalValue 等
```

---

## 五、删除客户

**结论：当前账号没有删除权限，不要继续研究。**

接口路径: `POST /rapi/d/customers/delete`
服务端返回: `{ "success": false, "errMsg": "没有[客户删除]的操作权限！" }`

---

## 完整操作示例

### 新增客户（一步到位）

```javascript
import { createJoinfClient } from './joinf-api-client.mjs';
import { readFileSync } from 'fs';

// 读取认证信息（从浏览器CDP获取后保存的文件）
const auth = JSON.parse(readFileSync('./live_auth.json'));

const client = createJoinfClient({
  cookie: auth.cookie,
  xCid: parseInt(auth.xCid),
  xUser: parseInt(auth.xUser),
});

// 新增
const result = await client.createCustomer({
  templatePayload: {
    models: [
      { columnName: "name", value: "", displayValue: "", originalValue: "", displayOriginalValue: "" },
      { columnName: "shortName", value: "", displayValue: "", originalValue: "", displayOriginalValue: "" },
      { columnName: "description", value: "", displayValue: "", originalValue: "", displayOriginalValue: "" },
      { columnName: "displayType", value: 236496, displayValue: "潜在工业客户", originalValue: 236496, displayOriginalValue: "潜在工业客户" },
    ],
    contacts: [{ models: [{ columnName: "name", value: "", displayValue: "", originalValue: "", displayOriginalValue: "" }] }],
    banks: [],
    customerAttachmentDtoList: [],
    tagList: [],
    markModel: { customerId: 0, companyId: 71376, operatorId: 183006, isChanged: false },
  },
  fields: { name: "新客户名称", shortName: "简称", description: "描述" },
  contactFields: { name: "联系人" },
});

console.log('新客户ID:', result.json?.data);
```

### 更新+跟进（组合操作）

```javascript
// 1. 读取当前值
const detail = await client.readCustomerDetail({ customerId: 12345 });

// 2. 更新描述
await client.updateCustomer({
  customerId: 12345,
  templatePayload: { /* 完整模板 */ },
  fields: { description: "新描述" },
  previousValues: { description: "旧描述" },
});

// 3. 添加跟进
await client.addFollowRecord({
  customerId: 12345,
  content: "已更新客户描述",
  planningTime: new Date().toISOString().slice(0, 19).replace('T', ' '),
});
```

---

## 关键资源

| 资源 | 路径 |
|------|------|
| API client | `outputs/joinf-api-client.mjs` |
| 测试文件 | `outputs/joinf-api-client.test.mjs` |
| 交接包 | `outputs/Hermes-最终完整交接包.md` |
| 操作手册 | `outputs/Hermes-新增与更新操作手册.md` |
| 探索日志 | `work/api-exploration-log.md` |
| 测试客户 | Test Customer XMA (ID: 238855638) |
| CDP端口 | 127.0.0.1:9223 |
| 登录账号 | bliiot03 |
