# Customer Requirement Matching Reference

## Case 1: LTE Data Logger with MQTT + RS485 + 0-10V/0-20mA + Counter

**Customer request:** "We are looking for a LTE data logger with mqtt connectivity, RS485 and 0-10v / 0-20mA & counter inputs"

### Product Comparison

| Requirement | S475 | S275 | MxxxT | MxxxE |
|------------|:----:|:----:|:-----:|:-----:|
| LTE/4G | ✅ | ✅ | ❌ Ethernet only | ✅ (from product images) |
| MQTT | ✅ | ✅ | ✅ | ✅ |
| RS485 | ✅ 2 ports | ⚠️ 1 port | ✅ 1 port | ✅ 1 port |
| AI 0-20mA/4-20mA | ✅ 24-bit | ⚠️ 12-bit | ✅ 16-bit | ✅ |
| AI 0-10V | ❌ 0-5V only | ❌ 0-5V only | ✅ | ✅ |
| Counter inputs | ✅ 4 (DIN0 1MHz, DIN1-3 1KHz) | ⚠️ 1 | ✅ Up to 12 (DIN1 700KHz) | ✅ |
| SD Card | ✅ 32GB | ✅ 8GB | ❌ | ❌ |
| Backup battery | ✅ | ✅ | ❌ | ❌ |
| Price tier | Mid | Low | Low | Unknown |

### Recommendation

**S475** is the best match for 4/5 requirements. The only gap: AI supports 0-5V / 0-20mA / 4-20mA but NOT 0-10V. If customer needs 0-10V, use a 0-10V→4-20mA signal converter ($5-15/channel).

**MxxxT** has 0-10V AI but no LTE — only Ethernet. Not suitable as standalone.

**MxxxE** (from product images: M120E/M160E/M420E) appears to be the 4G version of MxxxT, but no datasheet available — needs confirmation from BLIIOT engineering.

---

## ⚠️ Core Workflow: How to Match Customer Requirements to Products

When a customer sends a multi-I/O requirement, **never jump to one product first.** Follow this workflow:

1. List ALL product lines that could handle the requirement (BL118B, IOy, MxxxT/MxxxE, S475, ARMxy)
2. Check each one systematically — read the skill or datasheet, map each requirement
3. Identify the gaps honestly — be explicit about what doesn't fit
4. Present multiple options — the "best" depends on tradeoffs the customer may not have stated
5. Only then recommend — flag any assumptions needing customer confirmation

**Pitfall**: Starting with "BL118B is the best" before checking MxxxT/M350T or S475 misses alternatives. The user calls this out. Enumerate first.

## Case 2: All-in-One PLC/Module (Dominican Republic)

**Customer request:** "I'm looking for an 'all-in-one' module or PLC with: 2-4 DI, 1-2 AI (4-20mA or 0-10V), 1-4 TC inputs, and encoder input (any pulse signal)"

### ⚠️ Key Constraint: BL118B Only Has 2 Y-Board Slots

BL118B has exactly **2 Y-board slots**. You cannot fit 4 different I/O types (DI + AI + TC + pulse) on 2 boards. At least 2 functions must be handled via external Modbus RTU modules on the RS485 bus.

### Recommended Configuration (2 Y-Boards + External Modbus Modules)

**BL118B-SOM334-X4-Y58-Y95 + 4G EC25-AUXGA (Latin America)**

| Component | Function | Price (<100pcs) |
|-----------|----------|:---------------:|
| BL118B Host | Dual-core CA7@1.2GHz, Node-RED+BLIoTLink | $58 |
| SOM334 | 512MB RAM, 8GB eMMC | $30 |
| X4 | 2×RS485 + 2×CAN | $8 |
| **Y58** | **4TC (B/E/J/K/N/R/S/T)** — hardest to externalize | $17 |
| **Y95** | **4 pulse counting** (1×700KHz + 3×1KHz) — hardest to externalize | $23 |
| 4G EC25-AUXGA | Latin America 4G LTE bands | $25 |
| External Modbus 4DI module | via RS485 | ~$15 |
| External Modbus 2AI module | via RS485 | ~$20 |
| **Total** | | **~$196** |

### Requirement Match

| Requirement | How It's Handled | Status |
|------------|-----------------|:------:|
| 2-4 DI | External Modbus RTU 4DI module on RS485 | ✅ |
| 1-2 AI 4-20mA or 0-10V | External Modbus RTU 2AI module on RS485 | ✅ |
| 1-4 TC | Y58 (4TC, B/E/J/K/N/R/S/T) — direct slot | ✅ |
| Encoder/pulse input | Y95 (4 pulse counting) — direct slot | ⚠️ See note |
| 4G LTE | EC25-AUXGA | ✅ |
| MQTT | BL118B built-in (Node-RED) | ✅ |
| RS485 | X4 (2×RS485) for external modules | ✅ |

### ⚠️ Encoder Input Caveat

Y95 provides **pulse counting** (1 high-speed channel up to 700KHz + 3 low-speed channels up to 1KHz), NOT **quadrature encoder (A/B phase)**. If the customer needs:
- **Simple pulse counting** (e.g., flow meter, revolution counter) → Y95 works ✅
- **Quadrature encoder with direction detection** (e.g., motor position/speed control) → Y95 does NOT support A/B phase decoding ❌

**Alternative for true encoder:** Use an external quadrature encoder module via RS485 (e.g., Modbus RTU encoder reader) connected to the X4 RS485 port.

### Alternative: IOy Series (No 4G, Lower Cost)

If 4G is not needed, use **BL190 + Y58 + Y95 + external Modbus DI/AI modules** instead:
- BL190 (Modbus TCP Edge IO, 2×RJ45, 1×RS485, **3 Y-board slots** — more room than BL118B)
- Same Y-board combination
- No 4G, no Node-RED, lower cost (~$100 base)

### Alternative: M160T + M350T Dual-Module Combo

If the customer can accept two devices working together via Ethernet:

| Device | I/O | Price |
|--------|-----|:-----:|
| **M160T** | 8DI (with pulse counting) + 8AI (0-10V/4-20mA) + 8DO | $128 |
| **M350T** | 8TC (B/E/J/K/N/R/S/T) | ~$80 |
| **Total** | Covers all 4 requirements | **~$208** |

✅ Covers all 4 input types
⚠️ Two separate devices, not truly "all-in-one"
⚠️ No 4G (Ethernet only) — MxxxE series has 2×RJ45 but still no cellular

### Honest Assessment

**No single BLIIOT product covers DI + AI + TC + pulse in one box.** The closest approaches are:
1. **BL118B + 2 Y-boards + external Modbus modules** (~$196) — best "single-box" solution
2. **M160T + M350T** (~$208) — covers all I/O but needs two devices
3. **BL190 + 2 Y-boards + external modules** (~$130) — cheapest, no 4G, 3 Y-board slots available
