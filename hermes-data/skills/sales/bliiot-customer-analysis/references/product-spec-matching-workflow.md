# BLIIOT Product Spec-Matching Workflow

## When to use
Customer describes their requirements (protocols, I/O, power, mounting, software) and asks which BLIIOT product fits best.

## Workflow

### Step 1: Read the full requirement
Don't jump to a product recommendation after reading the first line. Read the ENTIRE requirement first — the customer may mention DI/AI/DO, ERP integration, IT/OT isolation, etc. that changes the recommendation.

### Step 2: Check specs against ALL product lines
Search across ALL product families:
- BL10x/BL120 series (plastic shell, ARM MCU 300MHz, Modbus/MQTT gateways)
- BE10x/BA10x series (plastic shell, IEC104/BACnet gateways)
- BL116/BE116/BA116 (metal shell, dual-core Cortex-A7 1.2GHz, high-performance)
- BL118 (Node-RED pre-installed, Allwinner T113-i, programmable)
- ARMxy BL460/BL461 (Raspberry Pi CM4/CM5, embedded controller)
- IOy series (remote I/O modules, RS485)
- RTU50xx/S27x series (industrial RTU/controllers)
- R40 series (industrial routers)

### Step 3: Pick ONE primary recommendation
**Do NOT switch between products mid-explanation.** If you realize a different product is better, acknowledge the change explicitly: "I initially said X but after checking the specs, Y is more suitable because..."

### Step 4: Structure the response clearly

```
## 推薦方案：[產品型號]

### ✅ 能滿足的
| 需求 | 狀態 | 說明 |
|------|------|------|
| Modbus RTU/TCP | ✅ | 內建支持 |
| ... | ✅ | ... |

### ❌ 不能滿足的
| 需求 | 狀態 | 替代方案 |
|------|------|---------|
| 本地DI/AI/DO | ❌ | ✅ 搭配IOy系列... |
| IT/OT隔離 | ❌ | 需客戶自行部署... |

### 🎯 為什麼推薦這款
- 對比其他產品的優勢
- 針對客戶行業/場景的匹配理由
- 如果客戶是軟體公司，強調可編程性/靈活性
```

### Step 5: Explain WHY, not just WHAT
For each recommendation, explain:
- Why this product over others in the same family
- What gap it fills in the customer's architecture
- What the customer needs to provide themselves (honest about limitations)

## Key product knowledge

### BL118 (Node-RED Edge Gateway)
- **CPU**: Allwinner T113-i (dual Cortex-A7 1.2GHz + HiFi4 DSP + RISC-V)
- **Protocols**: Modbus RTU/TCP, OPC UA, MQTT, BACnet, CAN, HTTP, WebSocket
- **I/O**: Via X/Y expansion boards (RS485/232, DI, AI, etc.)
- **Key advantage**: Pre-installed Node-RED — visual programming, customer can customize
- **Best for**: Software companies, MES integration, custom data pipelines
- **Cannot**: Local DI/AI/DO without IOy module, IT/OT isolation, platform-level features

### BL116/BE116/BA116 (High-Performance Gateways)
- **CPU**: Dual-core Cortex-A7 1.2GHz
- **Protocols**: Same as BL118 but FIXED firmware (BLIoTLink)
- **Key advantage**: 10,000 data points, 1,000 points in 1.5s, -40°C~85°C
- **Best for**: Fixed protocol conversion, high-volume SCADA
- **Cannot**: Custom programming, Node-RED, local I/O

### BL10x/BL120 series (Plastic Shell Gateways)
- **CPU**: ARM MCU 300MHz
- **Protocols**: Modbus/MQTT (BL10x), plus PLC/BACnet/IEC104 (BL120 variants)
- **Key advantage**: Low cost, compact (30mm wide)
- **Best for**: Simple Modbus-to-MQTT, cost-sensitive deployments
- **Cannot**: High data volume, custom programming, OPC UA (most models)

### ARMxy BL460/BL461 (Embedded Controllers)
- **CPU**: Raspberry Pi CM4/CM5 (BCM2711/BCM2712)
- **Key advantage**: Full Linux OS, GPIO, HDMI, USB, SD card
- **Best for**: Edge computing, custom application development
- **Cannot**: Industrial temperature range (CM5 only 0~85°C), no pre-installed industrial protocols

## Common pitfalls
- ❌ Saying BL118 then switching to BL460 without explanation → user gets confused
- ❌ Claiming a product can do something not in its spec sheet → always verify from the actual datasheet
- ❌ Forgetting to mention what the customer needs to provide themselves (IT/OT isolation, platform, ERP integration)
- ❌ Recommending a product without explaining WHY over alternatives
