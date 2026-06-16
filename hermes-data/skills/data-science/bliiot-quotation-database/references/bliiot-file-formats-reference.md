# BLIIOT File Format Reference

Quick reference for all quotation file formats and their price tier columns.

## IIoT Gateways (`IIoT Gateways` sheet)

| Col | Tier | Notes |
|:---:|------|-------|
| 2 | Model name | Variant name (e.g. BL121W, BA110P) |
| 3 | Sample | 1 unit |
| 4 | 50pcs | ~50 units |
| 5 | 100pcs | ~100 units |
| 6 | 500pcs | ~500 units |

⚠️ Contains BA series (BACnet) products — these are in the Building HVAC section.
**BA series prices from the 202605 file ARE correct.** Do not substitute BL10x prices (outdated).

## BL10x 塑胶外壳报价单

Same column layout as IIoT Gateways (Col 2=Model, 3=Sample, 4=50pcs, 5=100pcs, 6=500pcs).
**Correct price source for: BA110, BA110P, BA110W, BA110PW, BA108, BA108P, BA108W, BA108PW**

## RTU & Router (`Price List` sheet)

| Col | Tier | Notes |
|:---:|------|-------|
| 0 | Model | |
| 4 | Samples | 1 unit |
| 5 | <50Pcs | 2~49 units |
| 6 | >50Pcs | 50~99 units |
| 7 | >100Pcs | 100~499 units |
| 8 | >500Pcs | 500+ units |

## BLIIoT Master Price List (`Price List` sheet)

Same column layout as RTU & Router (Col 4=Samples, 5=<50Pcs, 6=>50Pcs, 7=>100Pcs, 8=>500Pcs).

## BL116 / BL118 (sheets in IIoT Gateways file)

| Col | Tier | Notes |
|:---:|------|-------|
| 0/1 | Model | Either column may contain the model name |
| 3 | Sample | |
| 4 | <50Pcs | |
| 5 | >50Pcs | |
| 6 | >100Pcs | |
| 7 | >500Pcs | |

## ARMxy (`Sheet1`, 11 variant files)

| Col | Tier | Notes |
|:---:|------|-------|
| 0 | Model | |
| 7 | <100pcs | 10~99 units |
| 8 | >=100pcs | 100+ units |
| 9 | Online Store & Quotation | Sample/1 unit price |

## ARMxy Y-Board Section (two-column layout)

See `references/armxy-y-board-two-column-layout.md`.

## DB Junction Box (xlsx)

| Col | Tier |
|:---:|------|
| 1 | Model |
| 2 | Sample |
| 3 | 100PCS |
| 4 | 500PCS |
