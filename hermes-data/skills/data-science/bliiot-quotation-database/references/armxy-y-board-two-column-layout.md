# ARMxy Y-Board Two-Column Layout

In `202511 ARMxy Series BL3xx Embedded Computer Price List.xls`, the Y-board section uses a **two-column layout** where each spreadsheet row contains two Y-board models.

## Header Row Structure

```
Col 0        | Col 1         | Col 2     | Col 3     | Col 4      || Col 5    | Col 6         | Col 7     | Col 8     | Col 9
-------------|---------------|-----------|-----------|------------||----------|---------------|-----------|-----------|------------
Model        | Description   | <100pcs   | >=100pcs  | Online     || Model    | Description   | <100pcs   | >=100pcs  | Online
```

## Data Rows (from BL335 file)

### Left column boards (Col 0-4)

| Model | Description | <100pcs | ≥100pcs |
|-------|------------|:-------:|:-------:|
| Y01 | 4DI+4DO, NPN | $10 | $9 |
| Y02 | 4DI+4DO, PNP | $10 | $9 |
| Y11 | 8DI, NPN | $10 | $9 |
| Y12 | 8DI, PNP | $10 | $9 |
| Y13 | 8DI, Dry Contact | $10 | $9 |
| Y21 | 8DO, PNP | $10 | $9 |
| Y22 | 8DO, NPN | $12 | $11 |
| Y24 | 4DO, Relay | $12 | $11 |
| Y31 | 4AI, 0/4~20mA | $18 | $17 |
| Y33 | 4AI, 0~5/10V | $18 | $17 |
| Y34 | 4AI, 0~5/10V diff | $17 | $15 |
| Y36 | 4AI, ±5/±10V diff | $17 | $15 |
| Y37 | 4 IEPE Measurement | $970 | $925 | **CONFIRMED DELETED** — user does not produce this |

### Right column boards (Col 5-9)

| Model | Description | <100pcs | ≥100pcs |
|-------|------------|:-------:|:-------:|
| Y41 | 4AO, 0/4~20mA | $17 | $15 |
| Y43 | 4AO, 0~5/10V | $17 | $15 |
| Y46 | 4AO, ±5V/±10V | $17 | $15 |
| Y51 | 2RTD, 3-Wire PT100 | $15 | $14 |
| Y52 | 2RTD, 3-Wire PT1000 | $15 | $14 |
| Y53 | 2RTD, 4-Wire PT100 | $15 | $14 |
| Y54 | 2RTD, 4-Wire PT1000 | $15 | $14 |
| Y56 | Resistance measurement | / | / (no price) |
| Y57 | Voltage measurement | / | / (no price) |
| Y58 | 4TC (thermocouple) | $17 | $15 |
| Y63 | 4 RS485/RS232 | $14 | $13 |
| Y95 | 4 PWM + 4 Pulse Counter (1 Hz~1 MHz) | $23 | $21 |
| Y96 | 4 PWM + 4 Pulse Counter (1 Hz~1 MHz) | $23 | $21 |

## Import Code Pattern

```python
// For Y boards: two-column layout
// NOTE: always round() prices — xlrd reads 92.3889 as float, actual value is 92
for r in range(y_section_start, y_section_end):
    // Left Y board (col 0-4)
    l_model = str(ws.cell_value(r, 0)).strip()
    if l_model and l_model.upper().startswith("Y") and l_model[1:].isdigit():
        imp(l_model, src, "<100pcs", ws.cell_value(r, 2))   // Col 2
        imp(l_model, src, ">=100pcs", ws.cell_value(r, 3))  // Col 3
        
        // Right Y board (col 5-9)
        r_model = str(ws.cell_value(r, 5)).strip()
        if r_model and r_model.upper().startswith("Y") and r_model[1:].isdigit():
            imp(r_model, src, "<100pcs", ws.cell_value(r, 7))   // Col 7
            imp(r_model, src, ">=100pcs", ws.cell_value(r, 8))  // Col 8
    
    // For X boards and host/SOM models: standard layout
    else:
        imp(model, src, "Online Store & Quotation", ws.cell_value(r, 9))  // Col 9 = Sample
        imp(model, src, "<100pcs", ws.cell_value(r, 7))                   // Col 7
        imp(model, src, ">=100pcs", ws.cell_value(r, 8))                  // Col 8
```

## Rule: Y Board Sample Price

Y boards do NOT have a Sample column in the file. When querying:
**Sample price = <100pcs price** (for 1~9 units)
