# Hermes Browser / CDP UI 操作 — JoinF CRM 跟进记录

## ⚠️ API方式已确认不可用（2026-06-19）

`POST /rapi/m/follow/add` 返回 `success:true` 但跟进不落库。
**必须用CDP浏览器UI操作**。

## CDP UI操作流程

### 前提：Chrome CDP 9226端口已启动并已登录富通

```
Chrome启动参数:
  --remote-debugging-port=9226
  --user-data-dir=<已登录富通的profile目录>
```

验证登录状态：
```javascript
// CDP Runtime.evaluate
window.location.href
// 必须返回 trade.joinf.com 域名，不是 cloud.joinf.com/login
```

### Step 1: 导航到客户跟进页面

```
Page.navigate → https://trade.joinf.com/tms/customer/customers_follow?tab=0
```

或者从客户列表页点击左侧菜单"客户跟进"：
```javascript
let links = Array.from(document.querySelectorAll('a.menu-link'));
let followLink = links.find(a => a.textContent.trim() === '客户跟进');
if(followLink) followLink.click();
```

### Step 2: 点击"新建跟进"按钮

```javascript
let btns = Array.from(document.querySelectorAll('button'));
let btn = btns.find(b => b.textContent.trim() === '新建跟进');
if(btn) btn.click();
// BUTTON class="el-button searchbar-add-btn el-button--primary"
```

### Step 3: 填写客户名称（最关键步骤！）

弹窗出现后：

```javascript
let inputs = Array.from(document.querySelectorAll('input.el-input__inner'));
let custInput = inputs.find(i => i.placeholder && i.placeholder.includes('客户代码'));
```

**⚠️ 不能直接设置value！必须触发Vue远程搜索并选择：**

```javascript
// 1. focus
custInput.focus();
custInput.dispatchEvent(new Event('focus', {bubbles: true}));

// 2. 设置值并触发input事件
custInput.value = '客户名称或ID';
custInput.dispatchEvent(new Event('input', {bubbles: true}));

// 3. 等待2秒让下拉选项加载
await new Promise(r => setTimeout(r, 2000));

// 4. 从下拉列表中点击匹配的客户选项
let items = Array.from(document.querySelectorAll('.el-select-dropdown__item, .el-autocomplete-suggestion__list li'));
let match = items.find(i => i.textContent.includes('目标客户名'));
if(match) match.click();
```

**⚠️ 如果跳过步骤4直接保存，跟进不会绑定到客户！**

### Step 4: 填写跟进内容

```javascript
let textarea = document.querySelector('textarea.el-textarea__inner');
textarea.value = '[WhatsApp跟进 2026-06-19] 跟进内容...';
textarea.dispatchEvent(new Event('input', {bubbles: true}));
```

### Step 5: 点击保存

```javascript
let saveBtn = Array.from(document.querySelectorAll('button.el-button--primary'))
  .find(b => b.textContent.trim() === '保存');
if(saveBtn) saveBtn.click();
```

### Step 6: 验证

```javascript
let r = await fetch('/rapi/d/customers?num=0&paging=true&size=50&searchText=客户名', {headers:{'Accept':'application/json'}});
let j = await r.json();
let t = j.data?.values?.find(x => x.id === 客户ID);
console.log('displayLastFollowTime:', t?.displayLastFollowTime);
// 应该变成当前时间的Unix毫秒时间戳，如果还是旧值说明没写入
```

## 颜色映射

| 类型 | 颜色 |
|------|------|
| 邮件 | 2B579A |
| WhatsApp | 27AE60 |
| 报价 | E67E22 |
| 电话 | E74C3C |
| 跟进 | fe4145 |

## 已知问题

| 问题 | 原因 | 解决 |
|------|------|------|
| 保存成功但followRecordInfo为空 | 直接填客户名称value，没触发Vue远程搜索下拉选择 | 必须从下拉列表中点击匹配的客户选项 |
| displayLastFollowTime不更新 | 客户名称没正确绑定 | 同上 |
| 弹窗不出现 | 按钮选择器不对 | 用 `button.el-button--primary` 且文字="新建跟进" |
| customers_follow页面404 | 富通V4.41.0更新后URL变化 | 用 `/tms/customer/customers_follow?tab=0` |

## 过时方法（不要用！）

❌ browser_console + fetch POST — 返回success:true但不落库
❌ joinf-api-client addFollowRecord() — 底层同API，同样不落库
❌ 直接设置客户名称value不触发下拉 — 保存成功但不绑定客户
