# Joinf CRM API Reference

## Authentication
- Login URL: `https://cloud.joinf.com`
- Main app URL: `https://trade.joinf.com/tms/`
- Account: bliiot03 (stored in .env)
- Captcha: Tencent slider puzzle — clicking "安全登录" usually auto-passes
- Session uses cookie auth (ticket-based SSO)

## API Endpoints

### Customer List (with pagination)
```
GET https://trade.joinf.com/rapi/d/customers?num={page}&paging=true&size={pageSize}&sortColumn=&sortType=&isAsterisk=0
```

**Parameters:**
- `num`: Page number (1-based)
- `paging`: Always `true`
- `size`: Page size (max 50 — larger values return empty data)
- `sortColumn`: Sort field (empty = default)
- `sortType`: Sort direction (empty = default)
- `isAsterisk`: Star filter (0 = all)

**Response structure:**
```json
{
  "data": {
    "headLists": [...],   // 75 column definitions
    "values": [...],      // Array of customer objects (NOT arrays!)
    "lockingNum": 0,
    "decimalNumber": 3,
    "displayed": 0
  },
  "totalRecords": 1948,
  "totalPage": 98,   // When size=20; recalculate for other sizes
  "success": true
}
```

**Important:** Each value in `values[]` is a **JSON object** (not an array). Column order does NOT match `headLists` — use field names directly.

### Customer Category/Filter Endpoints
```
GET /rapi/d/customer/category/step?sharedCategory=false
GET /rapi/d/customer/filter/setting?type=0      // My customers filters
GET /rapi/d/customer/filter/setting?type=-1      // System filters
GET /rapi/d/customer/filter/setting?type=-2      // Custom filters
GET /rapi/d/customers/contact/email/select/setting
GET /rapi/d/customers/delCustomerCache
GET /rapi/d/customer/query/boxs?type=0
GET /rapi/d/customers/importantField
GET /rapi/d/customers/0/0                      // Customer detail
```

### Public Sea (公海)
```
GET https://trade.joinf.com/tms/customer/customers?tab=1
```
Note: API tab parameter may not differentiate — both tab=0 and tab=1 return 1948 records. The UI handles filtering client-side.

## Complete Customer Field Map (75 fields)

| API Field Name | 中文列名 | Type | Description |
|---|---|---|---|
| tags | 标签 | 10 | Customer tags |
| displayRegion | 国家/地区 | 6 | Country/region with flag |
| name | 客户名称 | 10 | Company name |
| contactName | 联系人姓名 | 10 | Contact person |
| source | 客户来源 | 6 | 来源 (阿里询盘/官网询价/谷歌开发/领英开发/客户主动询价/MIC询盘/展会/客户来访/公司后台/商业数据/其他B2B) |
| description | 备注 | 10 | Notes/remarks (follow-up history) |
| grade | 客户等级 | 6 | Customer grade |
| recentlyFollowTime | 最近联系时间 | 3 | Last contact timestamp |
| displayCreateTime | 创建日期 | 3 | Creation timestamp (Unix ms) |
| toHighseasTime | 预计转入公海日期 | — | Auto-assignment date |
| lastTransferTime | 最近移交时间 | — | Last transfer date |
| telephone | 固定电话 | 10 | Landline phone |
| timeZone | 时区 | — | Timezone |
| displayType | 客户类型 | 6 | Type (潜在工业客户/成交工业客户/成交家用客户/Key Accounts/Protected Prospects等) |
| isAsterisk | 星标 | — | Star flag |
| mainProduct | 主营产品 | 10 | Main products |
| businessType | 业务类型 | — | Business type (代采/编程服务/系统集成等) |
| webSite | 企业网站 | 10 | Company website URL |
| address | 联系地址 | 10 | Full address |
| port | 港口 | — | Nearest port |
| activityType | 最近活动 | — | Latest activity type |
| faceBookCmpMain | Facebook公司主页 | 10 | Facebook page |
| twitterCmpMain | Twitter公司主页 | 10 | Twitter page |
| instagramCmpMain | Instagram公司主页 | 10 | Instagram page |
| linkedinAccount | LinkedIn账号 | 10 | LinkedIn URL |
| contactNickName | 联系人称呼 | 10 | Contact title/salutation |
| contactEmail | 联系人邮箱 | 10 | Email address |
| contactMobile | 联系人手机号 | 10 | Mobile phone |
| fax | 传真 | 10 | Fax number |
| bankAccount | 银行账号 | — | Bank account |
| displayBank | 开户银行 | — | Bank name |
| displaySalesman | 业务员 | 10 | Sales person |
| displayLastFollowTime | 下一跟进周期 | — | Next follow-up date |
| remainingTime | 周期剩余时长 | — | Time remaining |
| creator | 创建人 | 10 | Creator |
| code | 客户代码 | 10 | Customer code (C000XXXXX) |
| quoteCount | 报价次数 | — | Quote count |
| shortName | 客户简称 | 10 | Short name |
| quoteFirstDate | 首次报价日期 | — | First quote date |
| quoteLastDate | 最近报价日期 | — | Last quote date |
| inquireCount | 询价次数 | — | Inquiry count |
| inquireFirstDate | 首次询价日期 | — | First inquiry date |
| inquireLastDate | 最近询价日期 | — | Last inquiry date |
| orderCount | 成交订单数量 | — | Order count |
| orderAmountUsd | 成交订单金额USD | — | Order amount USD |
| orderAmountCny | 成交订单金额CNY | — | Order amount CNY |
| orderFirstAmountUsd | 首次订单金额USD | — | First order USD |
| orderFirstAmountCny | 首次订单金额CNY | — | First order CNY |
| orderAvgPriceUsd | 成交订单均价USD | — | Average price USD |
| orderAvgPriceCny | 成交订单均价CNY | — | Average price CNY |
| orderFirstDate | 首次订单成交日期 | — | First order date |
| orderLastDate | 最近订单成交日期 | — | Last order date |
| industryType | 行业类型 | 10 | Industry (系统集成商/自动化解决方案/工厂自动化系统等) |
| establishTime | 建立时间 | — | Establishment date |
| employeesCount | 员工人数 | — | Employee count |
| yearTurnover | 年营业额 | 10 | Annual turnover |
| introduce | 企业介绍 | 10 | Company intro |
| cooperationPeriod | 合作年限 | — | Cooperation years |
| flowStep | 跟进阶段 | 6 | Follow-up stage (初步了解/样品订单/成交等) |

## Internal Fields (not displayed but available)
| Field | Description |
|---|---|
| id | Internal customer ID (e.g., 238855365) |
| contactId | Contact person ID |
| corporationId | Company ID (e.g., 76993) |
| operatorId | Operator/user ID (e.g., 183006) |
| customerClassification | Classification number |
| shareType | Share type |
| status | Status flag |
| lock | Lock flag |
| open | Open flag |
| newPermission | Permission level |
| customerType | Internal type code |
| customerTagPersonalList | Personal tags array |
| customerAiTagList | AI tags array |
| replyEmailStatus | Email reply status |
| receiveApprovalStatus | Approval status |

## Data Verification Checklist (Kali铁律)

When extracting customer data from CRM, ALWAYS verify:

1. **Data ownership** — Check `displaySalesman` distribution. Expect: Kali Marfa(bliiot03) = 1943, Sam(bliiot01) = 5
2. **Today's additions** — Filter `displayCreateTime` for today (UTC+8). Compare count with CRM UI.
3. **Customer type distribution** — Check `displayType` breakdown:
   - 成交家用客户: ~1113
   - 成交工业客户: ~400
   - 潜在工业客户: ~377
   - 成交老人产品客户: ~43
4. **Source distribution** — Top sources: 阿里询盘(353), 客户主动询价(253), 谷歌开发(191), 官网询价(154)
5. **Empty vs null fields** — Many fields are empty strings ("") not null, especially: phone, website, address, industry

## Session: 2026-06-17

Successfully extracted all 1948 customer records via CDP browser + API.
- Login: cloud.joinf.com → auto-redirected to trade.joinf.com with SSO ticket
- Captcha: Clicked "安全登录" → auto-passed (no manual slider needed)
- API: `/rapi/d/customers?num=X&paging=true&size=50`
- Total: 1948 records across 40 pages (size=50)
- Data verified: salesman distribution, type distribution, source distribution all match CRM UI