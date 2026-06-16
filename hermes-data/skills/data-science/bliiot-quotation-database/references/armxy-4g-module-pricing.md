# ARMxy 4G/5G Module Pricing

Source: `202512 ARMxy Series Embedded Computer Price List.xlsx`, Sheet BL350, Rows 79-92
(These modules appear in ALL ARMxy sheets — BL310 through BL460 — at the same prices.)

## 4G/5G Module Section (ARMxy Optional Modules)

The 4G/WiFi/5G module section appears at the bottom of each ARMxy sheet sheet, AFTER the X-board and Y-board sections. The header row is:

```
R81: 料号 | (空) | 名称 | (空) | (空) | 带GPS功能 | 适用国家与地区 | <100pcs | >=100pcs | Online Store
```

### Complete 4G Module Pricing Table

| Part No. | Name | GPS | Region | <100pcs | >=100pcs |
|:---------|:-----|:---:|:-------|:------:|:--------:|
| 024031 | EC25AFFA-512-SGAS PCIE | ✅ | 北美 (North America) | $33 | $32 |
| 024009 | EC25-AFA MINIPCIE PCIE | ✅ | 北美 (North America) | $30 | $29 |
| 024010 | EC25-AUXGA-PCIE | ✅ | 澳洲、台湾、拉丁美洲 (Australia, Taiwan, LatAm) | $25 | $24 |
| **024027** | **EC25-EUXGR PCIE** | **✅** | **欧州、非州、中东、亚州、香港、澳门、东南亚** | **$23** | **$22** |
| 024050 | EC200U-EUAB | ❌ | 欧版 CAT1 | $12 | $11 |
| 024051 | EC200A-EUHA | ❌ | 欧版 CAT4 | $15 | $14 |
| 024008 | EC20-CE | ✅ | 国内4G CAT4 (China) | $21 | $20 |
| 024034 | EC20CEHDLG-MINIPCIE-CB | ❌ | 国内全网通、印度 (China+India) | $19 | $18 |
| 024026 | EC200NCNLA-N05-MN0CA PCIE | ❌ | 国内4G CAT1 (China) | $9 | $8 |
| 024048 | 5G模块全网通 | ❌ | 国内 (China) | $58 | $57 |
| 024049 | 5G模块（Redcap网络） | ❌ | 国内 (China) | $42 | $40 |

### WiFi Module Pricing

| Part No. | Name | Band | <100pcs | >=100pcs |
|:---------|:-----|:----|:------:|:--------:|
| 024047 | 双频WiFi模块2.4G+5.8G | 2.4G+5.8G | $9 | $8 |
| 24030 | 单频WIFI模块2.4G | 2.4G | $8 | $7 |

### Key Notes

- **WiFi and 4G/5G are mutually exclusive** — only one can be selected per unit. This is stated in the file itself.
- All prices include the antenna ("报价含天线").
- "亚洲" (Asia) region → use **EC25-EUXGR** (024027) which covers Europe, Africa, Middle East, Asia, Hong Kong, Macau, Southeast Asia.
- "国内" (China domestic) → use **EC20-CE** (024008, with GPS) or **EC20CEHDLG** (024034) or budget **EC200NCNLA** (024026, CAT1).
- No Samples column for modules → use <100pcs price as sample tier.

## ARMxy Naming Convention

From the file:

> **L suffix** = 4G module added, e.g. BL350L-SOM350-X10
> **W suffix** = WiFi module added, e.g. BL350W-SOM350-X10

When pricing: base host + SOM + X board + (optional: Y board) + (optional: 4G module or WiFi module)

## Price Calculation Example

```python
# BL352BL-SOM353-X25 with Asia 4G, qty=1
# Rule: Online Store = Sample price for ARMxy products
bl352   = 63     # BL352 Online Store
som353  = 57     # SOM353 Online Store
x25     = 18     # X25 <100pcs (Online Store = "Refer to <100pcs")
mod_4g  = 23     # EC25-EUXGR <100pcs (024027, Asia version)
total   = bl352 + som353 + x25 + mod_4g  # = $161
```

## Regional 4G Version Mapping

From `202605 BLIIOT RTU&Router Price List.xls`, sheet "4G Band & Countries":

| Version | Bands | Countries/Regions |
|:--------|:------|:-----------------|
| **4G (E version)** | GSM/EDGE: 900,1800; WCDMA: B1,B5,B8; FDD: B1,B3,B5,B7,B8,B20; TDD: B38,B40,B41 | Europe, Middle East, Africa, Thailand |
| **4G (CE version)** | GSM/EDGE: 900,1800; WCDMA: B1,B8; TD-SCDMA: B34,B39; FDD: B1,B3,B8; TDD: B38,B39,B40,B41 | India, Vietnam, Cambodia, China |
| **4G (AU version)** | GSM/EDGE: 850,900,1800; WCDMA: B1,B2,B5,B8; FDD: B1,B2,B3,B4,B5,B7,B8,B28; TDD: B40 | South America, Australia, Taiwan |
| **4G (A version)** | WCDMA: B2,B4,B5; FDD: B2,B4,B12 | USA AT&T, USA T-Mobile |
| **4G (V version)** | FDD: B4,B13 | USA Verizon |
| **4G (J version)** | WCDMA: B1,B3,B8,B18,B19,B26; FDD: B2,B4,B12; TDD: B41 | Japan |
