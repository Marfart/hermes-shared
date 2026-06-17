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
| 更新客户资料 | PATCH | `/rapi/d/customer` | ⚠️ | 2026-06-17 |
| 读取客户详情 | GET | `/rapi/d/customers/{id}/1` | ✅ | 2026-06-17 |
| 添加跟进记录 | POST | `/rapi/m/follow/add` | ✅ | 2026-06-17 |
| 客户列表 | GET | `/rapi/d/customers?paging=true&size=50` | ✅ | 2026-06-17 |

## 认证信息

从浏览器 CDP 端口 9223 获取（页面需已登录 trade.joinf.com）：

```javascript
// 1. GET http://127.0.0.1:9223/json → 找到 trade.joinf.com 页面的 webSocketDebuggerUrl
// 2. 通过 WebSocket 发送 CDP 命令：
//    Network.getCookies → 获取 Cookie
//    Runtime.evaluate → 获取 localStorage 中的 joinf-compnayId 和 joinf-XUser
```

保存到 `outputs/live_auth.json`：
```json
{
  "cookie": "...",
  "xCid": "71376",
  "xUser": "183006"
}
```

## 常量

| 常量 | 值 | 说明 |
|------|-----|------|
| companyId | 71376 | 公司ID |
| operatorId | 183006 | 操作员ID (bliiot03) |
| displayType | 236496 | 潜在工业客户（必填！） |
| xCid | 71376 | Header X-Cid |
| xUser | 183006 | Header X-User |
| baseUrl | https://trade.joinf.com | API 基础 URL |

## 一、新增客户

### 接口
```
POST https://trade.joinf.com/rapi/d/customer
Content-Type: application/json
```

### ✅ 已验证成功的模板

```javascript
import { createJoinfClient } from './joinf-api-client.mjs';

const client = createJoinfClient({ cookie, xCid: 71376, xUser: 183006 });

const result = await client.createCustomer({
  templatePayload: {
    models: [
      { columnName: 'name', value: '', displayValue: '', originalValue: '', displayOriginalValue: '' },
      { columnName: 'shortName', value: '', displayValue: '', originalValue: '', displayOriginalValue: '' },
      { columnName: 'description', value: '', displayValue: '', originalValue: '', displayOriginalValue: '' },
      { columnName: 'displayType', value: 236496, displayValue: '潜在工业客户', originalValue: 236496, displayOriginalValue: '潜在工业客户' },
    ],
    contacts: [{ models: [{ columnName: 'name', value: '', displayValue: '', originalValue: '', displayOriginalValue: '' }] }],
    banks: [],
    customerAttachmentDtoList: [],
    tagList: [],
    markModel: { customerId: 0, companyId: 71376, operatorId: 183006, isChanged: false },
  },
  fields: { name: '客户名称', shortName: '简称', description: '备注' },
  contactFields: { name: '联系人姓名' },
});
// result.json.data → 新 customerId
```

**必填字段**：
- `displayType: 236496` — 缺此字段返回"建档时客户类型不能为空"
- `markModel: { customerId: 0, companyId: 71376, operatorId: 183006, isChanged: false }`
- `contacts[0].models` 中 `name` 不能为空

## 二、更新客户资料

### 接口
```
PATCH https://trade.joinf.com/rapi/d/customer
Content-Type: application/json
```

### ⚠️ 关键铁则

1. **不能自己拼 patch body** — 必须先 `readCustomerDetail` 获取完整模板，再替换需要修改的字段
2. 模板必须包含完整的 `models[]`（所有字段）和 `contacts[]`
3. **contacts 中联系人 name 不能为空** — API 返回"建档时联系人姓名不能为空"
4. 如果客户联系人 name 为 null，需要设置默认值

### 更新流程

```javascript
// Step 1: 读取客户详情获取完整模板
const detail = await client.readCustomerDetail({ customerId: 238855638 });
const categories = detail.json.data || [];

// Step 2: 提取所有 models
const customerModels = [];
for (const cat of categories) {
  if (cat.categoryName === '主要信息' && cat.columnData) {
    for (const [columnName, colData] of Object.entries(cat.columnData)) {
      if (colData && typeof colData === 'object' && 'value' in colData) {
        customerModels.push({
          columnName, value: colData.value,
          displayValue: colData.displayValue || colData.value,
          originalValue: colData.originalValue ?? colData.value,
          displayOriginalValue: colData.displayOriginalValue ?? colData.displayValue ?? colData.value,
        });
      }
    }
  }
}

// Step 3: 提取 contacts（注意处理 name 为 null 的情况）
const contactModels = [];
let contactId = null;
for (const cat of categories) {
  if (cat.categoryName === '联系人' && cat.columnData) {
    for (const [columnName, colData] of Object.entries(cat.columnData)) {
      if (colData && typeof colData === 'object' && 'value' in colData) {
        contactModels.push({
          columnName, value: colData.value,
          displayValue: colData.displayValue || colData.value,
          originalValue: colData.originalValue ?? colData.value,
          displayOriginalValue: colData.displayOriginalValue ?? colData.displayValue ?? colData.value,
        });
      }
    }
    if (cat.columnData?.id?.value) contactId = cat.columnData.id.value;
  }
}

// Step 4: 构建 PATCH payload（联系人 name 为 null 时设默认值）
const updatedContactModels = contactModels.map(m => ({
  ...m,
  value: m.columnName === 'name' && (m.value === null || m.value === '') ? 'Default Contact' : m.value,
  displayValue: m.columnName === 'name' && (m.displayValue === null || m.displayValue === '') ? 'Default Contact' : m.displayValue,
}));

const patchResult = await client.updateCustomer({
  customerId: 238855638,
  templatePayload: {
    models: customerModels.map(m => ({ ...m, value: m.columnName === 'description' ? '新值' : m.value })),
    contacts: [{ models: updatedContactModels, id: contactId || 0 }],
    banks: [], customerAttachmentDtoList: [], tagList: [],
    id: 238855638, markModel: { isChanged: false, customerId: 238855638 },
  },
  fields: { description: '新值' },
  previousValues: { description: '旧值' },
});
```

## 三、读取客户详情

```javascript
const result = await client.readCustomerDetail({ customerId: 238855638 });
// result.json.data[] → 分类数组
// 主要信息: name, shortName, description, displayType, code...
// 联系人: name, email, phone, mobile, whatsApp...
```

## 四、添加跟进记录

```javascript
const now = new Date();
const ts = `${now.getFullYear()}-${String(now.getMonth()+1).padStart(2,'0')}-${String(now.getDate()).padStart(2,'0')} ${String(now.getHours()).padStart(2,'0')}:${String(now.getMinutes()).padStart(2,'0')}:${String(now.getSeconds()).padStart(2,'0')}`;

const result = await client.addFollowRecord({
  customerId: 238855638,
  content: '跟进内容',
  planningTime: ts,
});
// result.json.data → follow ID
```

## 五、客户列表查询

```
GET /rapi/d/customers?num={page}&paging=true&size=50
```
- 每页最多 50 条（size > 50 返回空数据）
- 数据在 `result.json.data.values[]`

## 已知问题与解决方案

### PATCH 更新失败：建档时联系人姓名不能为空

**现象**: PATCH 返回 `{"errMsg": "建档时联系人姓名不能为空!"}`

**原因**: 客户联系人 `name` 字段为 `null`，API 要求非空。

**临时方案**: 在 `contacts[0].models` 中给 `name` 设置非空默认值（见上方更新流程 Step 4）。

**根本方案**: 从浏览器编辑页 Vue SPA 抓取完整保存 payload 作为模板。

### displayType 必填

新增/更新客户必须包含 `displayType: 236496`，否则返回"建档时客户类型不能为空"。

## 文件结构

```
skills/sales/joinf-crm-api/
├── SKILL.md                          ← 本文件
└── references/
    ├── joinf-api-client.mjs          ← API 客户端（420行，完整封装）
    └── joinf-api-client.test.mjs     ← 测试用例
```

## 待完善

- [x] PATCH 更新：已定位问题（联系人name为null），临时方案已验证
- [ ] 保存邮件草稿 API
- [ ] 独立备注接口
- [ ] CDP 认证提取自动化脚本
