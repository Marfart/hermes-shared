# Google Maps to WhatsApp Workflow

Date: `2026-06-02`

This is the second executable BLIIOT customer development workflow.

## Goal

Use Google Maps leads as the source, then bridge them into the same WhatsApp automation pipeline that is already working for the buyer-search workflow.

Important:

- Google Maps development is not limited to Europe.
- Market selection should be decided dynamically based on BLIIOT product fit, language practicality, and contact quality.
- Europe, Africa, the Middle East, and other regions can all be used when they are a better match.
- The Europe run is only one fresh example, not the permanent default geography.

## Step Order

1. choose target markets and keyword strategy
2. build or update the Google Maps seed lead list from the current target market
3. enrich the seed list by merging prior lead intelligence and website crawl results
4. generate the customer follow-up document
5. build the WhatsApp priority queue
6. render personalized WhatsApp messages by industry style
7. audit duplicates before sending
8. run the WhatsApp sender

## Core Input Files

Target market strategy:

- `C:\Users\Admin\AppData\Local\hermes\memories\buyer-development\google_maps_target_markets_2026-06-02.json`

Seed lead list:

- `C:\Users\Admin\AppData\Local\hermes\memories\buyer-development\google_maps_seed_leads_2026-06-02.json`

Auxiliary enriched intelligence reused from the buyer-search workflow:

- `C:\Users\Admin\AppData\Local\hermes\memories\buyer-development\iiot_search_enriched_2026-06-02.json`

## Core Scripts

Google Maps enrichment:

- `C:\Users\Admin\AppData\Local\hermes\scripts\buyer-development\enrich_google_maps_leads.mjs`

Reusable queue builder:

- `C:\Users\Admin\AppData\Local\hermes\scripts\buyer-development\build_whatsapp_queue.mjs`

Reusable follow-up document builder:

- `C:\Users\Admin\AppData\Local\hermes\scripts\buyer-development\build_followup_document.mjs`

Reusable message renderer:

- `C:\Users\Admin\AppData\Local\hermes\scripts\buyer-development\render_whatsapp_messages.mjs`

Reusable WhatsApp sender:

- `C:\Users\Admin\AppData\Local\hermes\scripts\buyer-development\whatsapp_bulk_sender_cdp.mjs`

One-shot orchestrator for this Google Maps workflow:

- `C:\Users\Admin\AppData\Local\hermes\scripts\buyer-development\run_google_maps_to_whatsapp_pipeline.mjs`

## Main Outputs

Enriched Google Maps leads:

- `C:\Users\Admin\AppData\Local\hermes\memories\buyer-development\google_maps_enriched_2026-06-02.json`
- `C:\Users\Admin\AppData\Local\hermes\memories\buyer-development\google_maps_enriched_2026-06-02.csv`

Customer follow-up document:

- `C:\Users\Admin\AppData\Local\hermes\memories\buyer-development\google_maps_customer_followup_document_2026-06-02.json`
- `C:\Users\Admin\AppData\Local\hermes\memories\buyer-development\google_maps_customer_followup_document_2026-06-02.csv`

WhatsApp queue:

- `C:\Users\Admin\AppData\Local\hermes\memories\buyer-development\google_maps_whatsapp_priority_queue_2026-06-02.json`
- `C:\Users\Admin\AppData\Local\hermes\memories\buyer-development\google_maps_whatsapp_priority_queue_2026-06-02.csv`

Rendered WhatsApp messages:

- `C:\Users\Admin\AppData\Local\hermes\memories\buyer-development\google_maps_whatsapp_messages_2026-06-02.json`

Pipeline run summary:

- `C:\Users\Admin\AppData\Local\hermes\memories\buyer-development\google_maps_pipeline_run_2026-06-02.json`

## Notes

- This workflow reuses previously enriched intelligence where company names match, so older crawling work is not wasted.
- If Google Maps has a public phone number, that number is normalized and treated as the first WhatsApp candidate.
- The follow-up document keeps:
  - company name
  - contact name
  - country
  - LinkedIn website
  - email
  - phone
  - WhatsApp
  - website
  - industry
  - `What they do`
  - `Why they need BLIIOT`
- The rendered messages still follow the BLIIOT WhatsApp rules:
  - polite day-opening first
  - clear BLIIOT company positioning
  - industry-specific message style
  - website link
  - duplicate audit before send
- Message style should stay concise:
  - short paragraphs
  - clear line breaks
  - no long wall-of-text
