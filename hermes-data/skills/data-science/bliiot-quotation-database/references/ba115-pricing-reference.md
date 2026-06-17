# BA115 Series Pricing Reference (202605 IIoT Gateways File)

Source: `202605 BLIIOT IIoT Gateways & BL116 & BL118 Price List_Updated.xls`, sheet "IIoT Gateways", rows 322-343.

## Column Mapping

| Col | Tier |
|:---:|------|
| 2 | Model name |
| 3 | Sample |
| 4 | 50pcs |
| 5 | 100pcs |
| 6 | 500pcs |

## ⚠️ Tier Selection for BA115

The IIoT Gateways file has 4 tiers: **Sample / 50pcs / 100pcs / 500pcs**.

**For quantities 1-49, ALWAYS use the Sample tier.** The 50pcs tier only applies at 50+ units.

Common mistake (caught 2026-06-17): Quoting BA115 at $65 for 12 units. The Sample price is $67 — $65 is BELOW the correct price. The 50pcs price is $63, so $65 sits between 50pcs and Sample, but for 12 units the correct tier is Sample ($67).

## Full BA115 Model List with Prices (ALL tiers)

| Model | Sample | 50pcs | 100pcs | 500pcs |
|-------|--------|-------|--------|---------|
| BA115 | $67 | $63 | $61 | $59 |
| BA115L 4G L-CE | $100 | $94 | $91 | $88 |
| BA115L 4G L-E | $108 | $102 | $98 | $95 |
| BA115L 4G L-AU | $112 | $105 | $102 | $98 |
| BA115L 4G L-A | $120 | $113 | $109 | $105 |
| BA115L 4G CAT-1 | $81 | $76 | $73 | $71 |
| BA115LG 4G L-CE | $107 | $100 | $97 | $94 |
| BA115LG 4G L-E | $111 | $104 | $101 | $97 |
| BA115LG 4G L-AU | $114 | $107 | $104 | $101 |
| BA115LG 4G L-A | $122 | $115 | $111 | $107 |
| BA115W | $76 | $71 | $69 | $67 |
| BA115P | $98 | $92 | $89 | $86 |
| BA115PL 4G L-CE | $131 | $123 | $119 | $115 |
| BA115PL 4G L-E | $139 | $131 | $127 | $122 |
| BA115PL 4G L-AU | $143 | $134 | $130 | $126 |
| BA115PL 4G L-A | $151 | $142 | $137 | $133 |
| BA115PL 4G CAT-1 | $112 | $105 | $102 | $98 |
| BA115PLG 4G L-CE | $138 | $130 | $125 | $121 |
| BA115PLG 4G L-E | $142 | $133 | $129 | $125 |
| BA115PLG 4G L-AU | $145 | $137 | $132 | $128 |
| BA115PLG 4G L-A | $153 | $144 | $139 | $135 |
| BA115PW | $107 | $100 | $97 | $94 |

## Naming Convention

- **BA115** = base model (BACnet/IP gateway)
- **L** = 4G module added (L-E=Europe, L-CE=Central Europe, L-AU=Australia, L-A=Americas, CAT-1=LTE Cat-1)
- **LG** = 4G + GPS module
- **P** = PoE power supply
- **W** = WiFi module
- Combined: **PL** = PoE + 4G, **PLG** = PoE + 4G + GPS, **PW** = PoE + WiFi

## Price Source Priority

⚠️ Always use the **202605 IIoT Gateways file** for BA115 series pricing. The BL10x file (20240628) has older/outdated prices for BA110/BA115 models.

## Other Models Verified (2026-06-17)

| Model | File | Sample Price | Notes |
|-------|------|-------------|-------|
| BL120 | IIoT Gateways | $49 | All 4 tiers identical |
| BL120PM | IIoT Gateways | $49 | All 4 tiers identical |
| BL121PO | IIoT Gateways | $57 | OPC UA + PLC protocols |
| BL103 | IIoT Gateways | $57 | OPC UA gateway |
| M160E | RTU & Router | N/A (use <50Pcs=$157) | Samples=N/A, no sample tier |
| BL118B | BL118 sheet | $63 (Online Store) | Host only, no SOM |
| SOM335 | BL118 sheet | ¥420 RMB | ⚠️ File shows $62/$66 but actual price is ¥420 RMB |
| X4 | BL118 sheet | $9 (Online Store) | |
| Y02 | BL118 sheet | $10 (<100pcs) | Online Store = "Refer to <100pcs" |
| Y31 | BL118 sheet | $18 (<100pcs) | Online Store = "Refer to <100pcs" |