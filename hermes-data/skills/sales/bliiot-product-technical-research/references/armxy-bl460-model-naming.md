# ARMxy BL460 Series — Model Naming Reference

*Source: ARMxy BL460 Datasheet V1.0.docx*
*Path: `产品规格书/英文资料/ARM嵌入式控制器/BL460/`*

## Part Number Structure

```
BL461L - CM5 00 2 016 - X10
  │        │   │ │  │      │
  │        │   │ │  │      └── I/O Expansion Board code
  │        │   │ │  └──────── eMMC capacity (3 digits)
  │        │   │ └─────────── LPDDR4X capacity (1 digit)
  │        │   └───────────── Wireless config (2 digits)
  │        └───────────────── Compute Module type
  └────────────────────────── Base model variant
```

## CM5 Variants

| Model Code | CPU | Wireless Config | eMMC | LPDDR4X | Temp Range |
|------------|-----|----------------|------|---------|------------|
| CM5002000 | BCM2712 2.4GHz | x (none) | 0GB (Lite) | 2GB | 0~85°C |
| CM5002016 | BCM2712 2.4GHz | x (none) | 16GB | 2GB | 0~85°C |
| CM5002032 | BCM2712 2.4GHz | x (none) | 32GB | 2GB | 0~85°C |
| CM5004000 | BCM2712 2.4GHz | x (none) | 0GB (Lite) | 4GB | 0~85°C |
| CM5004016 | BCM2712 2.4GHz | x (none) | 16GB | 4GB | 0~85°C |
| CM5004032 | BCM2712 2.4GHz | x (none) | 32GB | 4GB | 0~85°C |
| CM5008000 | BCM2712 2.4GHz | x (none) | 0GB (Lite) | 8GB | 0~85°C |
| CM5008016 | BCM2712 2.4GHz | x (none) | 16GB | 8GB | 0~85°C |
| CM5008032 | BCM2712 2.4GHz | x (none) | 32GB | 8GB | 0~85°C |
| CM5016000 | BCM2712 2.4GHz | x (none) | 0GB (Lite) | 16GB | 0~85°C |
| CM5016016 | BCM2712 2.4GHz | x (none) | 16GB | 16GB | 0~85°C |
| CM5016032 | BCM2712 2.4GHz | x (none) | 32GB | 16GB | 0~85°C |
| CM5016064 | BCM2712 2.4GHz | x (none) | 64GB | 16GB | 0~85°C |

### CM5 with Wireless (PCB/ext antenna suffix)

Same as above but with `10` or `11` etc. after `CM5`:
- CM5102000 = BCM2712 2.4GHz, PCB/ext antenna, 0GB eMMC (Lite), 2GB LPDDR4X
- CM5102016 = BCM2712 2.4GHz, PCB/ext antenna, 16GB eMMC, 2GB LPDDR4X
- ...etc (all combinations repeat with wireless)

## I/O Expansion Board Codes

| Code | ETH Ports | RS232/RS485 | CAN | DI | DO | GPIO | Notes |
|------|-----------|-------------|-----|----|----|------|-------|
| X10 | 2 | 4 × RS485 | x | x | x | x | Standard IO variant |
| X20 | 3 | 2 × RS232+RS485 | x | x | x | x | Multi-COM variant |
| X30 | 2 | 2 × RS485 + 2 × RS232 | ✓ | x | x | x | CAN bus variant |
| X40 | 2 | 2 × RS485 | x | 4 | 4 | x | DI/DO variant |
| X50 | 2 | 2 × RS485 | ✓ | 4 | 4 | 8 | Full I/O variant |

## Base Model Variants

| Base Code | ETH on base board | Use case |
|-----------|-------------------|----------|
| BL460 | 2× RJ45 (GbE) | Standard dual-ETH controller |
| BL461 | 1× RJ45 (GbE) | Single-ETH, lower cost |

## SD Card Slot Summary

| eMMC | SD Slot | Boot |
|------|---------|------|
| 0GB (Lite) | ✅ Yes (1x microSD) | SD card |
| 16GB | ❌ No | eMMC |
| 32GB | ❌ No | eMMC |
| 64GB | ❌ No | eMMC |

Full datasheet at: `产品规格书/英文资料/ARM嵌入式控制器/BL460/ARMxy BL460 Datasheet V1.0.docx`