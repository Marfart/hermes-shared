# Document Verification Checklist

When generating a client-facing commercial/technical document from multiple source files, systematically cross-reference every data point before delivery. WhatsApp chats, original docx files, signed PDFs, and pricing spreadsheets often contain conflicting or superseded information.

## Source Inventory

Start by finding ALL source files in the project folder:

```bash
find /path/to/client/folder -type f | sort
```

Typical sources:
- `_chat.txt` — WhatsApp chat transcript (often has last-minute corrections)
- `Requirements Confirmation.docx` — original spec document
- `仍需改良的确认文件.docx` — revised / addendum doc
- `采购单价.xlsx` — pricing spreadsheet
- `津巴布韦客户定制项目时间预估.docx` — timeline document
- Signed PDFs — customer-signed confirmation showing what was actually agreed
- `**_PI_**.pdf` — proforma invoices with actual prices

## Verification Points

### 1. Pricing Matrix

Cross-check EVERY cell in the pricing table against three sources:
- The **pricing spreadsheet** (采购单价.xlsx) — ground truth for unit costs
- The **WhatsApp chat** — last confirmed prices (e.g. "USD 10,000 development cost" on May 21, not "USD 6,000" from April 22)
- The **signed confirmation document** — prices the customer actually agreed to

Check specifically:
- □ Base node price per qty tier (2000/5000/10000)
- □ Accessories subtotal (battery + IoT lock + controller + solar panel + stand)
- □ Final total (EXW)
- □ NRE/development fee — was it updated (e.g. $6,000→$10,000)?
- □ Promotional pricing (e.g. 50W bundled price)
- □ Payment terms (30/70 or 50/50 — confirmed in chat, not just in spreadsheet)

### 2. Accessories List

Cross-check each accessories item:
- □ **Battery**: Voltage (12V or 11.1V?), capacity (5Ah or 8Ah?), type (Li-ion). Chat often updates these after battery supplier quotes.
- □ **Antenna**: Was originally 7dBi, but customer may have agreed to 8dBi. Check latest chat message.
- □ **IoT lock**: Confirmed? Price ($1.50/unit)? Integration method (relay board via ThingsBoard)?
- □ **Solar charge controller**: Spec (100W MPPT)? Price ($6.50 at 2000pcs, $6.00 at 10000pcs)?
- **Solar panel**: Spec (30W/40W/50W)? Price source: customer's official quote or BLIIOT estimate? These may differ significantly (e.g. $9.20 vs $19.50 for 50W). Check the LATEST chat message — customer may have sourced a cheaper supplier after initial estimates.
- **Solar panel pricing cross-reference**: When the customer provides an official quotation from their own supplier (e.g. Gamko 50W for $9.20/unit), this supersedes BLIIOT's estimated price (e.g. $19.50/unit). Always check the formal quotation PDFs attached in chat (e.g. `260520  GAMKO 50W  QUOTATION.pdf`). Apply the customer-quoted price to the accessories subtotal and recalculate the final total.
- □ **Solar panel stand**: Included? Price (35 RMB/pc)? Pole-mount or roof-mount?

### 3. Technical Specifications

- □ **Antenna dBi**: Consistent across ALL sections of the document (not 7dBi in one place and 8dBi in another)
- □ **Battery voltage**: Use the value from the latest chat/customer quote, not the initial assumption
- □ **Solar input range**: 9–36V DC (S275 range) — verify this is correct
- □ **Charging**: 100W MPPT charger mentioned
- □ **Local logic**: IF-THEN without cloud dependency confirmed
- □ **Prototype qty**: 20 units total, first 2 engineering prototypes

### 4. Company Names & Transaction Entities

- □ **Client company**: Chat may specify a different entity handles the transaction (e.g. SmartGrid Africa handles payments, ZODSAT is the implementation company)
- □ **Client contact**: Name, title, email confirmed
- □ **Supplier**: Company name correct (BLIIOT / Beilai Technology)

### 5. Timeline

- □ **Schematic/PCB**: 4 weeks from spec freeze
- □ **Prototype production**: 15 working days
- □ **Delivery**: Express air freight (TBC if not yet confirmed)
- □ **Mass production**: 30 working days after prototype approval
- □ **Monthly capacity**: 400–700 units/month (check against chat: customer said "400-600/month, max ~700")
- □ **Total volume**: 50,000 units over 6 years

### 6. Document Metadata

- □ **Version number**: Incremented correctly (V1.0 → V2.0 → V3.0)
- □ **Date**: Current/appropriate date
- □ **Document status**: "Customer confirmation draft" or "Final"

### 7. Special Customer Requests

- □ **IoT lock integration**: Description of how it works with ThingsBoard for access logging
- □ **Branding**: Customer logo on final product enclosure
- □ **Payment terms**: Explicitly stated in the commercial section (e.g. "50% deposit, 50% before shipment")

### 8. Footnote & Disclaimer Formatting

- □ **Accessories footnote**: Small red italic text (6pt, #B91C1C), NOT gray
- □ **Platform boundary note**: Small red italic (6.5pt, #B91C1C)
- □ **Timeline disclaimer**: Small red italic (6.5pt, #B91C1C)
- □ **Quotation terms**: Small red italic (6.5pt, #B91C1C)
- □ **Consistency**: All footnotes match between English and Chinese versions

**Never use gray (#64748B) for notes** — users consistently prefer red to visually distinguish notes from body text.

## Common Discrepancies Found in Practice

| Source A | Source B | Which to Use |
|---|---|---|
| Pricing spreadsheet ($19.50 for 50W panel) | Customer's official quote ($9.20 for 50W panel) | Use latest confirmed price from chat, or note both |
| Battery "12V" in original doc | Battery "11.1V" in chat | 11.1V nominal / 12V compatible — clarify in document |
| Antenna "7dBi" in Section 2 | Antenna "8dBi" in accessories list | Customer agreed to 8dBi — use 8dBi everywhere |
| Development fee $6,000 (April 22) | Development fee $10,000 (May 21) | $10,000 — later and supersedes |
| Payment 30/70 (April 22) | Payment 50/50 (May 21) | 50/50 — later and supersedes |
| "Client: ZODSAT" | "SmartGrid Africa handles transaction" | List both with their roles |

## Iterative Refinement Cycle

In practice, generating a complex commercial document rarely succeeds in one pass. Plan for an iterative cycle:

**v1** → Initial generation from source files
**v2** → Fix watermark issues (behindDoc depth, opacity)
**v3** → Fix table transparency (remove w:shd so watermark shows through)
**v4** → Fix pricing, specs, company names based on cross-reference audit
**v5** → Polish formatting (margins, fonts, colors to match reference doc)
**v5.1+** → User feedback corrections (note size, note color, alignment tweaks)

Each version should address ONE category of feedback. Version-bump when content changes (pricing, specs), patch incrementally for style-only fixes. Save each version to the client's working folder with a clear filename (e.g. `更新后新文件_v5.0.docx`).

## When to Regenerate

Regenerate the document (increment version number) if ANY of the following are wrong:
- Pricing numbers (base node, accessories, total)
- Payment terms
- Technical specs that affect cost or feasibility
- Company/entity names
- Antenna spec (affects BOM)
- Battery spec (affects enclosure design)

Minor wording improvements can be patched in-place without version bump.

## Source Extraction Commands

```bash
# Extract text from .docx
unzip -p /path/to/document.docx word/document.xml 2>/dev/null | \
  grep -oP '<w:t[^>]*>\K[^<]+' | tr -d '\n'

# Read .xlsx (requires openpyxl)
python -c "
import openpyxl
wb = openpyxl.load_workbook('/path/to/file.xlsx', data_only=True)
for name in wb.sheetnames:
    ws = wb[name]
    for row in ws.iter_rows(values_only=True):
        vals = [str(v) if v is not None else '' for v in row]
        if any(v.strip() for v in vals):
            print(' | '.join(vals))
"

# Read .pdf text
pdftotext "/path/to/file.pdf" - 2>/dev/null
```

## Last Resort: File Delivery

When direct file transfer fails (WeChat rejects docx, etc.), use a temporary file host:

```bash
curl -s -F "file=@/path/to/file.docx" https://tmpfiles.org/api/v1/upload
# Returns {"status":"success","data":{"url":"https://tmpfiles.org/XXXXX/filename.docx"}}
# Direct download: https://tmpfiles.org/dl/XXXXX/filename.docx
```

Provide both the page URL and the direct download link so the user can choose.
