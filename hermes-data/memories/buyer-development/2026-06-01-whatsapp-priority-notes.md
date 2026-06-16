# Buyer Development Notes

Date: `2026-06-01`

## Current flow

1. In `全球买家`, search by an industry keyword such as `IIOT`.
2. Extract both result pages into structured JSON.
3. Parse each lead card for:
   - company name
   - country
   - domain
   - description
   - email count in Joinf
   - social icon breakdown
4. Prioritize leads with official-site WhatsApp evidence:
   - `wa.me`
   - `api.whatsapp.com`
   - `whatsapp.com/send`
5. Then rank by product fit using BLIIOT-relevant signals such as:
   - `SCADA`
   - `PLC`
   - `DCS`
   - `remote monitoring`
   - `IIoT`
   - `energy management`
   - `asset monitoring`
   - `smart factory`

## Reusable files

- Source results:
  `C:\Users\Admin\AppData\Local\hermes\memories\buyer-development\iiot_search_results_2026-06-01.json`
- Enriched output:
  `C:\Users\Admin\AppData\Local\hermes\memories\buyer-development\iiot_search_enriched_2026-06-01.json`
- CSV:
  `C:\Users\Admin\AppData\Local\hermes\memories\buyer-development\iiot_search_enriched_2026-06-01.csv`
- Crawler script:
  `C:\Users\Admin\AppData\Local\hermes\scripts\buyer-development\crawl_buyer_leads.mjs`

## Current IIOT run

- Total deduped leads analyzed: `35`
- Leads with official-site WhatsApp evidence: `3`

Top WhatsApp-priority leads:

1. `Iris Automation Pvt. Ltd.`
2. `serendibtechnologies`
3. `1.618 S.R.L.`

## Future automation direction

- For WhatsApp-first outreach, filter leads where `whatsappUrls` or `whatsappNumbers` is non-empty.
- Use the filtered output as the source list for later WhatsApp message automation.
