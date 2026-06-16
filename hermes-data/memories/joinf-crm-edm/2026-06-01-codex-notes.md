# Joinf CRM / EDM Notes

Date: 2026-06-01

## Goal

Build a reusable workflow for:

- scraping customer rows from Joinf CRM
- identifying Jerry-related customers by `客户代码`
- excluding those codes inside the EDM recipient picker
- auto-selecting the remaining recipients

## Confirmed Page Flows

### EDM

Path:

`数据营销 -> 新建任务 -> 外贸管理 -> 客户类型 = 成交工业客户 -> 查询`

Known result:

- result count shown in dialog: `607`
- table can be shown in one page
- EDM export already captured locally as:
  - `edm_all_deal_industrial_607.json`
  - `edm_all_deal_industrial_607.csv`

Observed user-approved sending flow:

`数据营销 -> 新建任务 -> 外贸管理 -> 客户类型 = 成交工业客户 -> 查询 -> 全选 -> 全部发送`

Latest clarification from user:

- do not filter Jerry in this run
- send to the whole selected deal-industrial-customer set directly
- when the user demonstrates steps live, observe and record instead of interrupting with extra scraping
- final action is direct send
- this flow is the EDM marketing bulk-email workflow

Observed body step:

`正文`

Observed subject:

`Follow-up on Product Usage & Future Cooperation | BLIIOT`

Observed final step:

`发送`

Observed body template copied into EDM body:

```text
Dear [$contacts_name],

Hope you're doing well.

This is Kali from BLIIOT. I'm following up on the products you purchased from us to check if they fit your business requirements perfectly.

Please kindly let us know if you have encountered any technical or usage issues during operation. We are always ready to offer professional support to help you solve problems promptly.

Meanwhile, we would like to know if you have any ongoing old project demands, new project plans, or further purchasing intentions for our products.

Additionally, we have recently launched a variety of upgraded products with optimized performance and cost-effectiveness. I can send you the full product catalog and exclusive pricing for existing customers at your convenience.

Please feel free to contact me via WhatsApp +86 18111156001 if you would like to know more details.

Looking forward to your reply！

Best regards,
Kali

BLIIOT
```

Macro observed for recipient name:

- `[$contacts_name]`

### CRM

Current CRM page:

`https://trade.joinf.com/tms/customer/customers?type=search&tab=0`

The CRM customer list exposes these useful fields directly in the list table:

- `备注`
- `客户等级`
- `最近活动`
- `联系人邮箱`
- `业务员`
- `创建人`
- `客户代码`
- `最近移交时间`

The CRM `高级` filter panel is present and field positions were mapped. Confirmed filter rows include:

- `客户代码`
- `客户名称`
- `客户类型`
- `客户等级`
- `联系人邮箱`
- `创建人`
- `业务员`
- `备注`
- `最近移交时间`
- `最近跟进`
- `最近跟进时间`

Useful note:

- `创建人` is a dedicated select-like control in the advanced filter panel, not a plain free-text input.
- In the current browser automation surface, opening that control is possible, but the searchable popup input was not exposed as a visible editable element yet.

## Scripts

Scripts are stored in:

- `C:\Users\Admin\AppData\Local\hermes\scripts\joinf-crm-edm`

Files:

- `joinf_browser_tools.js`
- `compare_customer_codes.mjs`

## What Works

- local code-to-code comparison by customer code
- EDM recipient table export already exists
- browser helper script prepared for:
  - API capture from Joinf page requests
  - normalized customer-record export from captured payloads
  - CRM export
  - Jerry matching
  - EDM checkbox selection excluding codes

## Clarification: what was and was not "virtual mouse"

The previous workflow was not mainly a system-level virtual mouse approach.

What it actually used:

- in-page JavaScript to read DOM tables
- local Node scripts to compare and normalize customer codes
- some browser-surface clicks only where the UI had to be opened or confirmed

So the main scraping work was already closer to:

- `JS in page`
- `DOM extraction`
- `local scripts`

and not a pure "move mouse around and click everything" approach.

## Better technical route going forward

Preferred order for future Joinf scraping:

1. install page API capture with `joinfTools.installApiCapture()`
2. trigger the relevant CRM search / filter / detail opening flow once
3. export normalized customer rows with `joinfTools.exportCapturedCustomerRecords()`
4. only if some fields are still missing, fall back to `exportCrmTable()`
5. convert the export to a standard follow-up document with:
   - `C:\Users\Admin\AppData\Local\hermes\scripts\joinf-crm-edm\build_joinf_customer_document.mjs`

This is better than relying on virtual clicks because:

- raw API payloads often contain richer fields than the visible table
- less fragile than virtual-scroll scraping
- less sensitive to UI layout changes
- easier for Hermes to repeat consistently

## Important Limitation

Inside Codex in-app browser, `tab.playwright.evaluate(...)` behaves like a read-only page scope in practice:

- direct DOM mutation like `scrollTop = ...` failed
- direct in-page `click()` also failed in evaluate scope

So for automation:

- use page reads inside `evaluate`
- use Playwright actions for visible clicks
- prefer reusable local scripts plus code comparison
- if full virtual-scroll harvesting is needed, expect to mix Playwright scrolling with repeated DOM reads
- some Element Plus select popups may not surface as visible editable nodes through the current automation surface, even after the wrapper is clicked

## Next Best Continuation

1. Re-open EDM recipient picker on the `607`-customer query.
2. Derive Jerry exclusion codes from the CRM result set in the same business scope.
3. Feed those codes into `selectEdmRecipientsExcludingCodes(...)`.
4. Verify selected count before any send action.

## Reminder

Per user request, future scripts, learned techniques, and memory files for this workflow should be stored under:

`C:\Users\Admin\AppData\Local\hermes\`
