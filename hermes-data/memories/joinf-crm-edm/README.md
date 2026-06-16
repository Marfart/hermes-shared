# Joinf Browser Scripts

`joinf_browser_tools.js` exposes `window.joinfTools` in the browser console.

Main functions:

- `await joinfTools.exportCrmTable()`
  Exports the current CRM customer list, including virtual-scroll rows.
- `joinfTools.installApiCapture()`
  Hooks page `fetch` and `XMLHttpRequest` so Joinf customer/list/detail JSON can be captured directly from browser network activity.
- `joinfTools.exportApiCapture()`
  Downloads the captured API payloads as JSON.
- `joinfTools.exportCapturedCustomerRecords()`
  Normalizes captured API payloads into customer rows and downloads JSON/CSV.
- `joinfTools.flagJerryRelatedRows(window.__joinfLastCrmExport.rows, { keywords: ["Jerry", "bliiot06"] })`
  Flags Jerry-related rows from the exported CRM rows.
- `await joinfTools.selectEdmRecipientsExcludingCodes(["C00000001", "C00000002"])`
  In the EDM customer picker, selects all rows except the provided codes.

`compare_customer_codes.mjs` compares two local JSON exports by `code` and writes the remaining set.

`build_joinf_customer_document.mjs` converts either:

- a browser API-capture export from `exportCapturedCustomerRecords()`, or
- a CRM table export from `exportCrmTable()`

into a standardized follow-up document with columns such as:

- `code`
- `company_name`
- `contact_name`
- `country`
- `linkedin_website`
- `email`
- `phone`
- `whatsapp`
- `website`
- `creator`
- `salesperson`
- `customer_level`
- `last_transfer_time`
- `last_follow_time`
- `note`
- `What_they_do`
