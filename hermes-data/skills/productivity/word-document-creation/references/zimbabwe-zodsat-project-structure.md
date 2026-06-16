# Zimbabwe ZODSAT Project — Document Structure Reference

This reference records the document structure generated for the Zimbabwe ZODSAT Transformer Anti-Theft project. Use as a template for similar client-facing product specification documents.

## Document Purpose

A specification document showing the customer what final product features are available, design timeline, integrated accessories pricing, and signature confirmation.

## Section Structure

1. **Overall Technical Route for Confirmation** — Device type, communication, base hardware, integrated scope, local alarm, prototype qty
2. **Key Hardware and I/O Requirements for Confirmation** — LoRaWAN, DI, AI, PT100, DO, local logic, antenna, config software, branding
3. **Sensor and Output Function List for Confirmation** — 10 function categories with descriptions
4. **Power Supply, Battery, Solar Power, and Enclosure Requirements** — 8 items covering battery, solar, enclosure, cabling
5. **Platform System Requirements and Hardware Project Boundary (ThingsBoard)** — Platform communication, alarms, map dashboard, boundary
6. **Integrated Accessories Breakdown & Commercial Scheme** — NRE fee ($10K), pricing matrix (2K/5K/10K qty × 30W/40W/50W panel), accessories notes
7. **Project Development, Design, and Delivery Schedule** — Schematic 4wk, prototype 15d, mass production 30d, monthly capacity 400-700
8. **Customer Confirmation and Signature** — Customer company, name, title, signature, date, stamp

## Key Data Points

- **Device**: BLIIOT S275 with LoRaWAN EU868 (replacing 4G module)
- **Customer**: ZODSAT, Zimbabwe
- **Application**: Transformer anti-theft and intrusion prevention
- **Prototypes**: 20 units (2 engineering prototypes first)
- **Battery**: 12V 5Ah Li-ion, 72h backup
- **Solar**: MPPT 100W charger included
- **Production**: 400-700 units/month, up to 50,000 total

## Font/Color Palette Used

### Light Blue Theme (client-facing confirmation docs)
| Element | Color | Hex |
|---------|-------|-----|
| Title text | Dark | #0F172A |
| Subtitle text | Blue accent | #1D4ED8 |
| Table header bg | Light blue | #EFF6FF |
| Odd row bg | Off-white | #F8FAFC |
| Even row bg | White | #FFFFFF |
| Body text | Slate | #1E293B |
| Muted text | Gray | #64748B |
| Footer text | Light gray | #94A3B8 |
| Table borders | Gray | #CBD5E1, #E2E8F0 |

### Dark Navy Theme (formal/proposal-grade docs, v2.0)
| Element | Color | Hex |
|---------|-------|-----|
| Title text | Dark | #0F172A |
| Subtitle text | Blue accent | #1D4ED8 |
| Table header bg | Dark navy | #1E3A5F |
| Header text | White | #FFFFFF |
| Odd row bg | Off-white | #F8FAFC |
| Even row bg | White | #FFFFFF |
| First col (label) | Dark | #1E293B |
| Other cols (data) | Medium | #475569 |
| Table borders | Gray | #CBD5E1 / #E2E8F0 |

## Logo Watermark

- File: 钡铼英文LOGO.png (481×302px)
- v1 (simple): placed in header as inline element, 2.8×1.76 inches
- v2 (proper DML): anchored `<wp:anchor>` with `behindDoc="1"`, centered on page, 3.5×2.2 inches
- Verify in `word/header1.xml` — NOT document.xml
