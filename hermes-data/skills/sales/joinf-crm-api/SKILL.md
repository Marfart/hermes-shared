---
name: joinf-crm-api
description: 富通天下(金蝶)CRM API操作指南 — 通过CDP控制已登录Chrome浏览器操作富通CRM，包括新增客户、修改客户资料、添加跟进记录等。Playwright只作为触发器，正式写入优先用API。
---

# 富通天下(金蝶)CRM API 操作指南

## 总原则

1. **不要重新登录** — 复用当前已登录浏览器会话
2. **不要长期靠 Playwright 点页面** — Playwright 只用于拿认证信息和抓模板
3. **一旦模板抓到，后续一律改成直接 HTTP**
4. **删除客户直接忽略** — 当前账号没有删除权限

## 已验证的真实接口

| 功能 | Method | 路径 | 状态 |
|------|--------|------|------|
| 新增客户 | POST | `/rapi/d/customer` | ✅ 已验证 |
| 更新客户资料 | PATCH | `/rapi/d/customer` | ✅ 已验证 |
| 添加跟进记录 | POST | `/rapi/m/follow/add` | ✅ 已验证 |
| 删除客户 | POST | `/rapi/d/customers/delete` | ❌ 权限不足 |
| 保存邮件草稿 | — | — | ❓ 未探索 |
| 独立备注接口 | — | — | ❓ 未确认 |

## 认证信息

需要以下3项，从已登录浏览器获取：

| 字段 | 来源 | 当前值 |
|------|------|--------|
| `Cookie` | 浏览器 Cookie（关键是 `JOINF_SESSION`） | 从浏览器实时读取 |
| `X-Cid` | `localStorage.joinf-compnayId` | `71376` |
| `X-User` | `localStorage.joinf-XUser` | `183006` |

**获取方式（CDP）**:
```python
# 从浏览器读取认证信息
result = await page.evaluate("() => ({ cookie: document.cookie, xCid: localStorage.getItem('joinf-compnayId'), xUser: localStorage.getItem('joinf-XUser') })")
```

## 现成代码

API client 已封装好，直接用：

```
C:\Users\Admin\Documents\Codex\2026-06-17\codex-https-trade-joinf-com-api\outputs\joinf-api-client.mjs
```

支持的方法：
- `client.createCustomer({ templatePayload, fields, contactFields, ... })`
- `client.updateCustomer({ customerId, templatePayload, fields, ... })`
- `client.addFollowRecord({ customerId, content, ... })`
- `client.readCustomerDetail({ customerId })`

## 新增客户

### 接口
```
POST https://trade.joinf.com/rapi/d/customer
```

### 关键参数

**必须保留的字段值**:
- `displayType.value = 236496`（潜在工业客户）
- `markModel.companyId = 71376`
- `markModel.operatorId = 183006`

**需要替换的客户字段**:
- `name` — 客户名称
- `shortName` — 客户简称
- `description` — 描述
- `webSite` — 网站

**需要替换的联系人字段**:
- `contacts[0].models[].columnName === "name"` — 第一个联系人的名字

### 标准流程

1. 从浏览器获取认证信息（cookie, xCid, xUser）
2. 获取 create 模板 payload（从已成功创建的请求中抓取）
3. 基于模板替换 `name`, `shortName`, `description`, `webSite`
4. 替换 `contacts[0]` 中的联系人 `name`
5. 保留 `displayType = 236496`、`markModel.companyId = 71376`、`markModel.operatorId = 183006`
6. 发送 POST `/rapi/d/customer`
7. 返回的 `data` 就是新的 `customerId`
8. 回列表页或读取接口确认客户已存在

### 已验证的成功案例

| 客户名 | customerId | 联系人 | 网站 |
|--------|------------|--------|------|
| Hermes Atlas 79139 | 238858457 | Noah Reed | https://example-479139.test |
| Hermes Nova 40171 | 238858620 | Ethan Cole | https://example-740171.test |

## 更新客户资料

### 接口
```
PATCH https://trade.joinf.com/rapi/d/customer
```

### ⚠️ 关键限制

**不能自己拼最小 patch body！**

错误做法（会返回"系统繁忙"）：
```
1. 从 GET /rapi/d/customers/:id/1 读取客户详情
2. 自己平铺字段
3. 自己拼一个最小 patch body
4. 发 PATCH → 失败！
```

正确做法：
```
1. 从真实编辑页保存时抓到完整 payload 模板
2. 在模板上只替换目标字段
3. 发 PATCH → 成功！
```

### 标准流程

1. 从浏览器获取认证信息
2. 获取 update 模板 payload（从真实编辑页保存动作中抓取）
3. 基于模板只替换要修改的字段
4. 发送 PATCH `/rapi/d/customer`
5. 回读详情接口确认字段变化
6. 用新 marker 再打一次确认可重复

### 已验证的成功案例

- **目标客户**: Test Customer XMA (customerId: 238855638)
- **成功 marker**: `HERMES_API_TEST_20260617_090918`, `HERMES_API_TEST_20260617_090921`
- **验证字段**: `description` 字段已成功修改并回读确认

## 添加跟进记录

### 接口
```
POST https://trade.joinf.com/rapi/m/follow/add
```

### 参数
```javascript
{
  id: "",
  attachmentList: [],
  businessStep: 0,
  customerStep: 0,
  completeNoRemind: 0,
  models: [
    { columnName: "dataName", value: customerId },
    { columnName: "contactContent", value: "跟进内容" },
    { columnName: "planningTime", value: "2026-06-17 08:54:42" },
    { columnName: "feedbackOperator", value: "183006" },
    // ... 其他固定字段
  ]
}
```

### 已验证
- customerId: 238855638
- 成功 marker: `HERMES_API_TEST_20260617_085237`, `HERMES_API_TEST_20260617_085414`, `HERMES_API_TEST_20260617_085442`

## 删除客户

**结论：当前账号没有删除权限，不要继续研究。**

接口路径: `POST /rapi/d/customers/delete`
请求体: `{ "ids": [customerId], "flag": -1, "delReason": "1" }`
服务端返回: `{ "success": false, "errMsg": "没有[客户删除]的操作权限！" }`

## 待探索（按优先级）

1. ✅ 新增客户 — 已验证
2. ✅ 更新客户资料 — 已验证
3. ✅ 添加跟进记录 — 已验证
4. ❌ 删除客户 — 权限不足，跳过
5. ❓ 保存邮件草稿 — 未探索
6. ❓ 独立备注接口 — 未确认（如果指 description 字段，用 updateCustomer 即可）

## 关键资源

- **API client**: `outputs/joinf-api-client.mjs`
- **测试文件**: `outputs/joinf-api-client.test.mjs`
- **探索日志**: `work/api-exploration-log.md`
- **机器可读 findings**: `work/api-findings.jsonl`
- **前端 bundle**: `work/editAdd.js`, `work/app.bundle.js`
- **测试客户**: Test Customer XMA (ID: 238855638)
- **CDP端口**: 127.0.0.1:9223
- **登录账号**: bliiot03
