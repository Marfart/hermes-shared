# Joinf Live Customer Development Pipeline

Date: 2026-06-02

This pipeline develops new prospects directly from the logged-in Joinf/Futong "Global Buyers" session, then enriches them with website-crawled contact assets, generates a follow-up document, builds industry-specific WhatsApp messages, checks resend history, and sends through the existing WhatsApp automation stack.

## Live source

- Chrome remote debugging session: `http://127.0.0.1:9226`
- Source site: `https://data.joinf.com/searchResult?open=firstPage`
- Live Joinf API used:
  - `POST https://data.joinf.com/api/bs/searchBusiness`

## Search keyword set used on 2026-06-02

- `Building Automation`
- `SCADA`
- `IIoT`
- `Remote Monitoring`
- `System Integrator`

## Automation order

1. Fetch live Joinf search results from the logged-in browser session.
2. Normalize and deduplicate companies by domain/name.
3. Crawl official websites and selected contact/about pages.
4. Extract:
   - emails
   - LinkedIn company URLs
   - WhatsApp URLs
   - WhatsApp numbers
5. Infer:
   - `What they do`
   - `Why they need BLIIOT`
   - industry
   - recommended BLIIOT product directions
6. Build follow-up document for analysis.
7. Build WhatsApp priority queue.
8. Render industry-specific WhatsApp messages.
9. Check `whatsapp_sent_registry.json` before sending.
10. Send through `whatsapp_bulk_sender_cdp.mjs`.

## Scripts

- Chrome / reconnect helper:
  - `C:\Users\Admin\AppData\Local\hermes\scripts\buyer-development\chrome_cdp_launcher.mjs`
- One-click opener for Joinf + Google Maps browser:
  - `C:\Users\Admin\AppData\Local\hermes\scripts\buyer-development\open_joinf_maps_browser.mjs`
- One-click opener for WhatsApp browser:
  - `C:\Users\Admin\AppData\Local\hermes\scripts\buyer-development\open_whatsapp_browser.mjs`
- Live Joinf fetch:
  - `C:\Users\Admin\AppData\Local\hermes\scripts\buyer-development\fetch_joinf_business_search.mjs`
- Joinf enrichment:
  - `C:\Users\Admin\AppData\Local\hermes\scripts\buyer-development\enrich_joinf_business_search.mjs`
- Full Joinf pipeline runner:
  - `C:\Users\Admin\AppData\Local\hermes\scripts\buyer-development\run_joinf_to_whatsapp_pipeline.mjs`
- Queue builder:
  - `C:\Users\Admin\AppData\Local\hermes\scripts\buyer-development\build_whatsapp_queue.mjs`
- Follow-up document builder:
  - `C:\Users\Admin\AppData\Local\hermes\scripts\buyer-development\build_followup_document.mjs`
- Message renderer:
  - `C:\Users\Admin\AppData\Local\hermes\scripts\buyer-development\render_whatsapp_messages.mjs`
- WhatsApp sender:
  - `C:\Users\Admin\AppData\Local\hermes\scripts\buyer-development\whatsapp_bulk_sender_cdp.mjs`

## Output files from 2026-06-02 run

- Raw Joinf API capture:
  - `C:\Users\Admin\AppData\Local\hermes\memories\buyer-development\joinf_business_search_results_2026-06-02_raw.json`
- Normalized Joinf lead list:
  - `C:\Users\Admin\AppData\Local\hermes\memories\buyer-development\joinf_business_search_results_2026-06-02.json`
- Enriched lead data:
  - `C:\Users\Admin\AppData\Local\hermes\memories\buyer-development\joinf_business_search_enriched_2026-06-02.json`
  - `C:\Users\Admin\AppData\Local\hermes\memories\buyer-development\joinf_business_search_enriched_2026-06-02.csv`
- WhatsApp queue:
  - `C:\Users\Admin\AppData\Local\hermes\memories\buyer-development\joinf_whatsapp_priority_queue_2026-06-02.json`
  - `C:\Users\Admin\AppData\Local\hermes\memories\buyer-development\joinf_whatsapp_priority_queue_2026-06-02.csv`
- Follow-up document:
  - `C:\Users\Admin\AppData\Local\hermes\memories\buyer-development\joinf_customer_followup_document_2026-06-02.json`
  - `C:\Users\Admin\AppData\Local\hermes\memories\buyer-development\joinf_customer_followup_document_2026-06-02.csv`
- Rendered WhatsApp messages:
  - `C:\Users\Admin\AppData\Local\hermes\memories\buyer-development\joinf_whatsapp_messages_2026-06-02.json`
- Pipeline run summary:
  - `C:\Users\Admin\AppData\Local\hermes\memories\buyer-development\joinf_pipeline_run_2026-06-02.json`
- WhatsApp send results:
  - `C:\Users\Admin\AppData\Local\hermes\memories\buyer-development\whatsapp_bulk_send_results_2026-06-02-04-09-33.json`
- Send registry:
  - `C:\Users\Admin\AppData\Local\hermes\memories\buyer-development\whatsapp_sent_registry.json`

## Verified run result

- Joinf raw leads fetched: `100`
- Deduplicated new Joinf companies: `63`
- Enriched companies: `63`
- Valid WhatsApp-ready leads after cleanup: `4`
- Follow-up document rows: `4`
- Messages rendered: `4`
- WhatsApp messages actually sent: `4`

## Sent companies in this run

1. `Excel Automation Solutions` - `+918870007000`
2. `Neel Smartec Co` - `+919538047356`
3. `Ecava Sdn. Bhd.` - `+60380804838`
4. `Tlm Telemetria E Sensoriamento` - `+5541991129953`

## Important implementation detail

- Prefer direct API capture and scripted fetch from Joinf over virtual mouse clicking.
- Only fall back to DOM/table extraction when Joinf API payloads are unavailable.
- Always sanitize WhatsApp URLs and extract a clean phone number before queue generation.
- Always check `whatsapp_sent_registry.json` before sending.
- If CDP `9226` is not running, start:
  - `C:\Users\Admin\AppData\Local\hermes\scripts\buyer-development\open_joinf_maps_browser.mjs`
- If CDP `9223` is not running, start:
  - `C:\Users\Admin\AppData\Local\hermes\scripts\buyer-development\open_whatsapp_browser.mjs`
- Dedicated persistent profiles:
  - Joinf + Google Maps: `C:\Users\Admin\AppData\Local\hermes\chrome-profiles\joinf-maps-live`
  - WhatsApp: `C:\Users\Admin\AppData\Local\hermes\chrome-profiles\whatsapp-bulk`
