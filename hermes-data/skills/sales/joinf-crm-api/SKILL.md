---
name: joinf-crm-api
description: 富通天下(金蝶)CRM API操作指南 — 通过CDP控制已登录Chrome浏览器操作富通CRM，包括新增客户、修改客户资料、添加备注/跟进记录等。Playwright只作为触发器，正式写入优先用API。
---

# 富通天下(金蝶)CRM API 操作指南

## 核心发现

### 已验证：新增客户（通过UI表单）

**认证方式**: 依赖Chrome已登录的session cookie，无需额外token

**关键发现**: 直接POST/PUT API返回"系统繁忙"，必须通过UI表单的Vue组件保存

**已验证字段值**:
- `displayType`: "潜在工业客户" | "Key Accounts" | "Protected Prospects" | "成交工业客户" | "成交家用客户"
- `displayRegion`格式: `中文 英文`（如 `印度  INDIA`）
- `customerTypeId`: "236496"（潜在工业客户）

## CDP连接注意事项

### 超时问题解决

CDP websocket连接可能超时，原因：
1. 之前的连接没有正确关闭（Chrome只允许一个websocket连接per page）
2. 页面正在加载/导航中
3. recv timeout设置过短

**正确连接顺序**:
```
1. curl http://127.0.0.1:9223/json → 获取页面ID
2. curl http://127.0.0.1:9223/json/activate/{page_id} → 激活页面
3. time.sleep(3~5) → 等待页面就绪
4. websocket.create_connection(ws_url, timeout=60)
5. ws.settimeout(15)
6. 发送命令后等待response，如超时则重新连接
```

### 已知问题

- `Page.navigate` 后页面可能处于加载状态，需要等待
- 多个快速命令可能丢失response
- 每次操作后建议关闭连接，下次重新连接

## 操作方法

### 1. 打开客户详情/新建页面

```
URL格式:
- 新建: https://trade.joinf.com/tms/customer/customers?type=new&tab=0
- 编辑: https://trade.joinf.com/tms/customer/customers?type=edit&id={customerId}&tab=0
```

### 2. 填写表单字段

**文本字段**（name, shortName等）:
```python
# 使用native setter + input事件触发Vue reactivity
nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set
nativeSetter.call(input_el, 'value')
input_el.dispatchEvent(new Event('input', {bubbles: true}))
input_el.dispatchEvent(new Event('change', {bubbles: true}))
```

**下拉选择字段**（displayType, displayRegion等）:
```python
# 方法1: 点击下拉 → 等待选项出现 → 点击目标选项
input_el.click()
time.sleep(1)
items = document.querySelectorAll('.el-select-dropdown__item')
# 找到目标并点击

# 方法2: 使用Vue组件的handleOptionSelect（更可靠）
selectComp = input_el.closest('.el-select').__vue__
opts = selectComp.options || []
target = opts.find(o => o.label === '目标值')
selectComp.handleOptionSelect(target)
```

### 3. 保存

**方法A**: 点击保存按钮
```python
buttons = document.querySelectorAll('button')
saveBtn = [b for b in buttons if b.textContent.trim() == '保存'][0]
saveBtn.click()
```

**方法B**: 调用Vue组件save方法
```python
comp = document.querySelector('.customer_edit_add_vue').__vue__
comp.save()
```

## 常用字段ID

| 字段 | ID | 类型 |
|------|-----|------|
| 客户编码 | code | text (自动) |
| 客户名称 | name | text (必填) |
| 客户简称 | shortName | text |
| 客户类型 | displayType | select (必填) |
| 国家/地区 | displayRegion | select (必填) |
| 时区 | timeZone | select |
| 主要产品 | mainProduct | text |
| 公司网站 | webSite | text |
| 客户描述 | introduce | text |
| 员工数 | employeesCount | text |
| 成立时间 | establishTime | text |
| 行业类型 | industryType | text |
| 年营业额 | yearTurnover | text |
| 公司简介 | introduce | textarea |

## 待探索接口（按优先级）

1. ✅ 新增客户 — 通过UI表单已实现
2. ❌ 添加备注(introduce字段) — 待通过编辑表单测试
3. ❌ 添加跟进记录 — 待探索follow/record相关API
4. ❌ 修改客户资料 — 待通过编辑表单测试
5. ❌ 保存邮件草稿 — 待探索mail/draft相关API

## 接口探索方法论

当普通Network抓包不到API时，按以下顺序尝试：

### 阶段1: HAR搜索
1. 启用Network监听
2. 用Playwright触发一次最小保存操作
3. 等待8-15秒后停止监听
4. 搜索payload/response中包含唯一测试字符串(HERMES_API_TEST_时间戳)的请求

### 阶段2: 前端JS分析
1. 导出所有加载的JS bundle
2. 搜索关键词: save, update, add, create, customer, contact, follow, remark, api, gateway, graphql, rpc, service
3. 提取API路径和方法名

### 阶段3: Storage/Token解析
1. 检查 localStorage, sessionStorage, cookies
2. 提取: token, csrf/xsrf, authorization, tenantId, companyId, userId, employeeId
3. 检查window全局变量

### 阶段4: GraphQL/Gateway/RPC
1. 检查payload中的 operationName, method, action, service, variables
2. 分析是否走统一网关

### 阶段5: WebSocket
1. 监听WebSocket frame
2. 在保存前后的message中搜索测试字符串

### 阶段6: 页面内部request函数
1. 查找页面封装的axios/fetch/apiService
2. 在浏览器上下文中直接调用页面自己的请求函数

### 阶段7: 备选方案
- Excel导入/批量导入
- 企业邮箱SMTP/IMAP/Exchange API

## 关键资源

- **测试客户**: Test Customer XMA (ID: 238855638)
- **CDP端口**: 127.0.0.1:9223
- **登录账号**: bliiot03
- **前端框架**: Vue.js + Element UI
- **表单组件类**: customer_edit_add_vue, contact_edit_add_vue
