# Africa Lead Mining — Session Example (2026-06-04)

**Method:** Search Engine Lead Mining (Tier 4), no Google Maps, no LinkedIn scraping
**Duration:** ~15 minutes, 15 leads across 3 countries
**Output:** `BLIIoT_Customer_Leads_v3.xlsx`

## Best-performing query patterns

### South Africa (9 leads)
```
"system integrator" "South Africa" "industrial" "email" OR "contact" company
"industrial automation" "South Africa" system integrator PLC SCADA IIoT IoT email
South Africa PLC SCADA system integrator companies list contact email
```

### Contact sources found
| Source | Type | Example |
|--------|------|---------|
| Company homepage | Direct email/phone | `information@advansys.co.za` on homepage |
| Company /contact page | Contact form or email | `Info@weconplc.co.za` on /contact-us/ |
| EngNet directory | Rich data (phone, email, address, map) | `engnet.co.za/c/f.aspx/SYS020` |
| African Advice / AfricaBizInfo | Business directory with phone | `africabizinfo.com/ZA/systems-automation...` |
| LinkedIn company page | Sector/description only (no email) | Use to confirm specialty |
| Crunchbase | Email + phone | `information@advansys.co.za` confirmed |
| CSIA Exchange | Contact person data | `david.greaves@advansys.co.za` |

## Scoring rubric used

★★★★★ = Company directly matches PLC/SCADA/IIoT all three → **HIGH - Best fit**
- Example: Advansys (PLC, SCADA, MES, IIoT, Batch)
- Example: INTEG (PLC, SCADA, HMI, MES, Batching)
- Example: SAM (PLC, SCADA, Fieldbus, Industrial IT, MES, BMS)
- Example: Gil Automation Nigeria (PLC, SCADA, Siemens VAR)

★★★★☆ = Matches 2 out of 3; strong fit but not 100% → **HIGH or MEDIUM**
- Example: AM Systems Integration (Wonderware/SCADA/HMI)
- Example: Calibrant (PLC/SCADA + OT Security + Integration)

★★★☆☆ = Only partially related; may need different BLIIOT product pitch
- Example: Nkokhi Group (defence SCADA niche)
- Example: Fronthill Controls (building automation, not industrial)

## Tech notes
- `mcp_fetch_fetch` works well for South African websites (slower but connects)
- `web_extract` (ddgs backend) **does not work for URL extraction** — use `mcp_fetch_fetch` instead
- `browser_navigate` timed out on African sites (connection refused) — don't rely on browser stack for this pipeline
- South African companies often have both `.co.za` domain and `engnet.co.za` directory listing — check both