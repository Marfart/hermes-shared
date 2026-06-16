# Joinf CRM Write API Attempts (2026-06-17)

## Goal
Update customer name from "Вадим" to "Abhinav" for customer id=238854934 (email: Abhinav.global22@gmail.com).

## API Endpoints Tested — ALL FAILED

| Method | Endpoint | Status | Response |
|--------|----------|--------|----------|
| PUT | `/rapi/d/customers` | 200 | `{"success":false,"errMsg":"系统繁忙，请稍后再试！"}` |
| POST | `/rapi/d/customers` | 200 | `{"success":false,"errMsg":"系统繁忙，请稍后再试！"}` |
| PUT | `/rapi/d/customers/238854934` | 404 | Not Found |
| PUT | `/rapi/d/customer` | 404 | Not Found |
| POST | `/rapi/d/customers/save` | 404 | Not Found |
| POST | `/rapi/d/customer/update` | 404 | Not Found |
| POST | `/rapi/d/customers/edit` | 404 | Not Found |
| POST | `/rapi/d/customer/update` | 404 | Not Found |

## Body Formats Tested
1. **Full customer object** (all 75+ fields from GET response) — "系统繁忙"
2. **Minimal object** `{id, name, contactName, contactId}` — 404 on most, "系统繁忙" on PUT /rapi/d/customers

## Conclusion
The write/update API endpoint is **unknown**. The CRM frontend likely uses a different API path or a form-based submission that we haven't captured.

## Working Alternative: UI-Based Editing
1. Navigate to customer detail page (click customer row in list)
2. Click the edit icon (pencil) next to customer name in the detail panel
3. Modify the name field
4. Save

**Issue encountered:** Playwright MCP disconnected during this operation, preventing completion of the UI-based edit. The edit icon ref was `e3537` (next to customer name "Вадим").

## Pending Action
- Customer id=238854934 still needs name changed from "Вадим" to "Abhinav"
- Customer id=238855365 ("Вадим 2", email midav82@gmail.com) is the real Russian customer — name is correct

## Data Quality Finding
The CRM has at least one data entry error where customer name (Вадим) doesn't match the contact email (Abhinav.global22@gmail.com). This suggests the user accidentally entered a Russian name for an English-named contact, likely because they had just created another customer named Вадим and the name was auto-filled or copied.