# ARMxy BL460 Series — Hardware Gotchas for Customer Q&A

## R34 Resistor — eMMC Partitioning for Custom OS Images

### What it is
- R34 is a **0-ohm resistor** (surface mount jumper) on the BL460 mainboard
- It controls whether Windows detects the eMMC as a single partition or multiple partitions when using `rpiboot` via USB Type-C

### Why a customer might ask about it
- Customer wants to **split the eMMC into 2+ partitions** (e.g. OS + data storage with overlayFS to make OS read-only)
- BL460 user manual mentions removing R34 for partition detection via `rpiboot` on Windows

### How to remove it
- **Soldering iron** — heat both pads, lift it off
- **Hot air gun** — heat until it floats, remove with tweezers
- Standard SMD rework — requires steady hands and magnification

### Alternative approach
The customer can also use `rpiboot` on a Linux system which handles partition detection differently — R34 removal is only needed when using Windows + `rpiboot`.

### When customers ask about this
- They typically want to harden the OS against power-loss corruption by making the OS partition read-only via overlayFS
- This came up in May 2026 with Abdul Rahman Zafar (Domotix Tech, Saudi Arabia) for BL461L units

## RS485 Auto Direction Control (DE/RE Pins)

### What customers ask
> "For the RS485 ports on the Y expansion boards, is Automatic Direction Control handled by the RS485 transceiver chip itself or is there a dedicated hardware logic circuit on the board that automatically toggles the DE/RE pins based on the TX line? We need to confirm that our software does not need to manually toggle RTS."

### Answer (from BLIIOT engineering)
The RS485 transceiver handles direction control automatically at the hardware level. The customer's software does NOT need to manually toggle RTS/DE/RE pins. This is standard for BLIIOT's RS485 implementation on ARMxy boards.

### Why this matters
- Customers integrating BL460 into their own Modbus/BACnet stacks need to know if they need RTS toggling logic
- BLIIOT's implementation is **transparent** — standard UART read/write works without special handling

## Capacitor Upgrade for RTC Retention

See main SKILL.md section on RTC Battery/Capacitor Options.

**TL;DR:** Stock capacitor → brief retention. Upgrade to larger capacitor → ~3 days, +$2/unit. Tested and confirmed working May 2026.