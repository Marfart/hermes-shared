# Google Maps Europe Fresh Pipeline

Date: 2026-06-02

This run uses freshly scraped Google Maps prospects from Europe only. It does not reuse the previous Africa seed list as the source.

Important:

- Europe is only the region used in this specific fresh run.
- The Google Maps workflow itself is not limited to Europe.
- Future runs should choose the best market dynamically instead of assuming Europe by default.

## Fresh source strategy

- Search directly on Google Maps through the controllable Chrome session.
- Restrict to Europe-focused automation terms.
- Exclude any company names already present in:
  - `C:\Users\Admin\AppData\Local\hermes\memories\buyer-development\google_maps_seed_leads_2026-06-02.json`

## Queries used

- `industrial automation Berlin`
- `building automation Amsterdam`
- `PLC SCADA Warsaw`
- `system integrator Munich`
- `industrial control Milan`

## Fresh-source script

- `C:\Users\Admin\AppData\Local\hermes\scripts\buyer-development\scrape_google_maps_fresh_seeds.mjs`

## Downstream scripts used

- `C:\Users\Admin\AppData\Local\hermes\scripts\buyer-development\enrich_google_maps_leads.mjs`
- `C:\Users\Admin\AppData\Local\hermes\scripts\buyer-development\build_whatsapp_queue.mjs`
- `C:\Users\Admin\AppData\Local\hermes\scripts\buyer-development\build_followup_document.mjs`
- `C:\Users\Admin\AppData\Local\hermes\scripts\buyer-development\render_whatsapp_messages.mjs`
- `C:\Users\Admin\AppData\Local\hermes\scripts\buyer-development\whatsapp_bulk_sender_cdp.mjs`

## Output files

Fresh seeds:

- `C:\Users\Admin\AppData\Local\hermes\memories\buyer-development\google_maps_europe_fresh_seeds_2026-06-02.json`
- `C:\Users\Admin\AppData\Local\hermes\memories\buyer-development\google_maps_europe_fresh_seeds_2026-06-02.csv`

Enriched data:

- `C:\Users\Admin\AppData\Local\hermes\memories\buyer-development\google_maps_europe_fresh_enriched_2026-06-02.json`
- `C:\Users\Admin\AppData\Local\hermes\memories\buyer-development\google_maps_europe_fresh_enriched_2026-06-02.csv`

Queue:

- `C:\Users\Admin\AppData\Local\hermes\memories\buyer-development\google_maps_europe_fresh_whatsapp_queue_2026-06-02.json`
- `C:\Users\Admin\AppData\Local\hermes\memories\buyer-development\google_maps_europe_fresh_whatsapp_queue_2026-06-02.csv`

Follow-up document:

- `C:\Users\Admin\AppData\Local\hermes\memories\buyer-development\google_maps_europe_fresh_followup_2026-06-02.json`
- `C:\Users\Admin\AppData\Local\hermes\memories\buyer-development\google_maps_europe_fresh_followup_2026-06-02.csv`

Rendered messages:

- `C:\Users\Admin\AppData\Local\hermes\memories\buyer-development\google_maps_europe_fresh_messages_2026-06-02.json`

Send results:

- `C:\Users\Admin\AppData\Local\hermes\memories\buyer-development\whatsapp_bulk_send_results_2026-06-02-05-57-47.json`

Shared dedupe registry:

- `C:\Users\Admin\AppData\Local\hermes\memories\buyer-development\whatsapp_sent_registry.json`

## Verified counts

- Fresh Europe Google Maps seeds scraped: `18`
- Enriched leads: `18`
- WhatsApp queue rows: `18`
- Follow-up rows: `18`
- Messages rendered: `18`
- WhatsApp sent successfully: `5`
- WhatsApp send errors / non-sendable cases: `13`

## Sent successfully in this Europe run

1. `Core Automation` - `+31627593130`
2. `Benelux Electric` - `+31687600185`
3. `AiSash` - `+491625991856`
4. `i4 Automation & Engineering GmbH` - `+491639253985`
5. `Automatyka PLC - PLCSpace` - `+48889631956`

## Notes

- Many Google Maps public phone numbers are ordinary office numbers and may not be active WhatsApp numbers.
- When WhatsApp Web does not show a send button, the run records an error and does not count that lead as sent.
- The fresh-source Europe pipeline is separate from the older Africa Google Maps seed list.
- Future message rendering should stay concise, well-spaced, and easy to read on WhatsApp.
