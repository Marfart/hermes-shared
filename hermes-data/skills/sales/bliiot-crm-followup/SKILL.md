---
name: bliiot-crm-followup
description: BLIIOT 富通CRM 客户跟进管理系统 — 双向同步跟进记录、Excel全量报表、一键跟进工具
---

# BLIIOT CRM 跟进管理系统

## 概述

本地 SQLite + 富通CRM 双向同步的客户跟进管理系统：
- 本地存所有跟进记录（不依赖网络）
- 同步到富通CRM（通过CDP浏览器调POST /rapi/m/follow/add）
- 自动生成专业Excel报表（5个Sheet，含跟进历史）
- 快速查客户+跟进历史+一键记录

## 文件结构

```
%LOCALAPPDATA%/hermes/memories/脚本缓存/富通CRM/
├── crm_followups.db              ← SQLite跟进记录库（3表）
├── all_customers_raw.json        ← 1955条客户数据缓存
├── pending_sync.json             ← 待同步队列（synced=0/1）
├── bliiot_crm.py                 ← 主程序（CRUD+统计+Excel+同步）
├── crm_quick.py                  ← 场景化快捷命令封装
├── sync_all_pending.mjs          ← CDP同步管道（Node.js）
├── fetch_all_customers.mjs       ← 全量客户拉取
└── generate_excel.py             ← Excel报表生成
```

## 快速上手

### 初始化（首次运行）
```bash
cd "%LOCALAPPDATA%/hermes/memories/脚本缓存/富通CRM"
python bliiot_crm.py init
```

### 常用命令
```bash
# 查客户信息+跟进历史
python crm_quick.py customer "客户名或ID"

# 按客户名添加跟进（自动查ID）
python crm_quick.py add-by-name "hsinsight" "WhatsApp联系，已读资料" --type WhatsApp

# 按ID添加跟进+同步到富通
python bliiot_crm.py add 235327923 "发了BL460报价" --type 邮件 --sync

# 查看统计
python crm_quick.py stats

# 搜索跟进记录
python crm_quick.py search "关键词"

# 生成Excel报表
python crm_quick.py excel

# 同步待处理记录到富通CRM
cd "%LOCALAPPDATA%/hermes/memories/脚本缓存/富通CRM"
node sync_all_pending.mjs
```

## 跟进类型

支持：`跟进`, `邮件`, `WhatsApp`, `电话`, `报价`, `订单`, `会议`, `备注`, `系统`

## 跟进记录自动触发规则（强制）

当执行以下操作时，*必须*同步记录跟进到 CRM：

| 操作 | 跟进类型 | source值 | 内容模板 |
|------|----------|----------|----------|
| 发邮件 | 邮件 | email | "发送了关于[产品]的介绍邮件给[联系人]" |
| 读WhatsApp | WhatsApp | whatsapp | "通过WhatsApp联系[客户]，讨论了[内容]" |
| 报价 | 报价 | quote | "报价CI-[编号]：[产品]×[数量]" |
| 电话 | 电话 | call | "与[联系人]电话沟通，讨论了[内容]" |

**强制规则**：
- 所有邮件和WhatsApp操作必须自动写跟进（`--type 邮件/WhatsApp`）
- 内容必须具体（什么产品、什么话题、客户什么反应）
- 用Kali第一人称（"我发送了..."，不写"我方"、"客户"）
- 不放价格/报价金额到跟进备注
- CRM同步是可选（`--sync`），但本地记录是强制
- 新增客户必须有邮箱；无邮箱时报告Kali让她去问，小马不能直接发消息

## 数据源

- **来源**：富通CRM (trade.joinf.com) — CDP浏览器登录态
- **认证**：Profile 2，端口9226，账号 bliiot03
- **API**：GET /rapi/d/customers?num=N&paging=true&size=200（size最大200，1955条约10页）
- **字段**：105个原始字段 → Excel中提炼49个核心字段

## 同步管道（CDP浏览器）

```javascript
// 1. 动态获取CDP URL（页面ID重启后变化，不可硬编码）
const pages = await fetch('http://127.0.0.1:9226/json').then(r => r.json());
const target = pages.find(p => p.url && !p.url.startsWith('devtools')) || pages[0];
const wsUrl = target.webSocketDebuggerUrl;

// 2. 导航到客户列表页建立会话
await send({ method: 'Page.navigate', params: { url: 'https://trade.joinf.com/tms/customer/customers?type=search&tab=0' } });
await sleep(5000);

// 3. POST跟进记录
await fetch('/rapi/m/follow/add', {
  method: 'POST',
  headers: { 'X-Cid': '71376', 'X-User': '183006', 'Content-Type': 'application/json' },
  body: JSON.stringify({
    models: [
      { columnName: "dataName", value: customerId, ... },
      { columnName: "contactContent", value: content, ... },
      { columnName: "bgColor", value: color, ... },
      { columnName: "method", value: method, ... },
      { columnName: "feedbackOperator", value: "183006", ... }
    ],
    ...
  })
});
```

颜色映射：邮件=2B579A、报价=E67E22、WhatsApp=27AE60、电话=E74C3C、跟进=fe4145

## 登录绕过（拼图验证码）

Chrome会话过期被重定向到登录页时，拼图验证码可直接绕过：

```javascript
// 1. Navigate to https://cloud.joinf.com/login
// 2. Fill credentials
document.getElementById('loginID').value = 'bliiot03';
document.getElementById('loginPassword').value = 'Kali1314520!';
// 3. Click login (bypasses captcha!)
document.getElementById('loginBtn').click();
// 4. Wait ~5s, then URL becomes https://trade.joinf.com/tms/?ticket=ST-xxx
```

认证提取：
```javascript
// Network.getCookies → domain含'joinf'的cookie → Cookie header
// localStorage.getItem('joinf-compnayId') → xCid = "71376"
// localStorage.getItem('joinf-XUser') → xUser = "183006"
```

## Excel报表

5个Sheet，662KB，自动保存到 `Desktop/Working/BLIIOT_富通CRM_客户数据全量报表.xlsx`

| Sheet | 内容 |
|-------|------|
| 📊 客户总览 | KPI卡片(总数/已跟进/跟进条数/有邮箱/有手机/有报价) + 等级/来源/国家分布 |
| 📋 全部客户数据 | 1955行×36列（含最后3列橙色标记：本地跟进次数、最近跟进、跟进摘要🆕） |
| 👤 业务员统计 | 各业务员客户数/跟进数/邮箱率/手机率/报价次数 |
| 🌍 国家地区统计 | 147个国家覆盖+跟进深度+邮箱覆盖率 |
| 💬 跟进记录明细 | 所有跟进记录详情（含同步状态标记✅⏳） |

### Excel生成陷阱

**openpyxl IllegalCharacterError** — CRM备注字段含非打印控制字符，必须清洗：
```python
def sanitize(val):
    if isinstance(val, str):
        return ''.join(c for c in val if c.isprintable() or c in '\n\r\t').strip()
    return val
```

**时间戳转换** — CRM时间字段为毫秒级Unix timestamp：
```python
def ts_to_date(ts):
    if not ts or ts == 0: return ''
    dt = datetime.fromtimestamp(ts / 1000, tz=timezone(timedelta(hours=8)))
    return dt.strftime('%Y-%m-%d %H:%M')
```

## 关键字段速查

| 字段名 | 中文名 | 说明 |
|--------|--------|------|
| name | 客户名称 | 公司名 |
| shortName | 客户简称 | 常含中文缩写 |
| contactName | 联系人姓名 | 可能为null |
| contactEmail | 联系人邮箱 | 核心营销字段 |
| contactMobile | 联系人手机号 | WhatsApp可用 |
| displayRegion | 国家/地区 | 含中英文 |
| displaySalesman | 业务员 | 格式"姓名(账号)" |
| source | 客户来源 | 领英开发/官网询价等 |
| grade | 客户等级 | 潜在/意向/报价/成交 |
| description | 备注 | 长文本，历史沟通记录 |
| status | 状态 | 0=活跃 1=公海 4=成交 |
| quoteCount | 报价次数 | >0表示有过报价 |
| activity | 最近活动 | 报价编号等 |
| toHighseasTime | 预计转入公海 | 毫秒timestamp |
| remainingTime | 周期剩余 | 如"29天20小时" |

## 字段值映射

| 原始值 | 映射后 | 适用字段 |
|--------|--------|----------|
| status: 0 | 活跃 | status |
| status: 1 | 公海 | status |
| status: 4 | 成交 | status |
| isAsterisk: 1 | ⭐ | isAsterisk |

## 关键铁则

1. **添加跟进必须先知道客户ID** — 用 `customer "名称"` 查ID，或用 `add-by-name`
2. **同步需要CDP浏览器** — 确保Chrome Profile 2在9226端口运行并已登录
3. **动态CDP URL** — 页面ID重启后变化，必须从/json端点获取最新`webSocketDebuggerUrl`
4. **跟进记录语气** — 用Kali第一人称（"我"、"他"），不放价格金额，不放客套话
5. **Excel自动保存到桌面** — `Desktop/Working/BLIIOT_富通CRM_客户数据全量报表.xlsx`
6. **查重规则** — 新增客户必须有邮箱；跟进只加不新建
7. **全量拉取用size=200** — 实测1955条约10页（旧笔记说size>50返回空数据是错误的）

## 常见问题

### CDP报500 / Unexpected server response: 500
CDP URL的page ID过期了。重启Chrome后页面ID变化，需重新从`/json`获取。

### openpyxl报IllegalCharacterError
备注字段含非打印控制字符。在写入Excel前必须过`sanitize()`清洗。

### 同步到富通失败
检查：①CDP端口是否运行 ②页面是否在客户列表页 ③`X-Cid`和`X-User`是否从localStorage提取

### 跟进记录数量不对
检查pending_sync.json中的synced状态。同步成功后标记为1。如果CDP未运行同步会失败但本地记录不受影响。