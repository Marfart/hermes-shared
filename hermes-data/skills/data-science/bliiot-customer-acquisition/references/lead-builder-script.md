# Master Lead Builder Script

**Location:** `C:\Users\Admin\AppData\Local\hermes\memories\脚本缓存\客户挖掘\master_leads_builder.py`

This is a self-contained Python script using `hermes_tools` (web_search, web_extract). It implements the full Google Maps → lead extraction → Excel output pipeline.

## How to use

1. First use `browser_navigate` to search Google Maps for a given market/keyword
2. Manually extract company data from the browser snapshot
3. Add the data to `LeadMaster.add_batch()` calls in the script
4. Run via `execute_code` — the script handles website crawling, email extraction, product scoring, and Excel generation

## Key class: `LeadMaster`

```python
finder = LeadMaster()
finder.add_batch([
    {'name':'Company Name','phone':'+27 XX XXX XXXX','rating':5.0,'type':'System Integrator'},
], 'South Africa')
finder.process_all()
```

## Output

- Excel: `C:\Users\Admin\Desktop\Working\BLIIoT_Customer_Leads_Master.xlsx`
- 3 sheets: Leads (green = WhatsApp available), Summary, How to Use (with outreach template)

## Note on execution limits

The script uses web_search (up to 3 queries per lead) and web_extract (up to 3 URLs per lead). For 30 leads this uses ~50 tool calls. The `execute_code` tool has a 50-call limit, so batch size per execution should be ≤30 leads.
