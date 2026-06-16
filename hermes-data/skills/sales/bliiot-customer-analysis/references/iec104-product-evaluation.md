# IEC 104 产品评估指南

## 客户常见术语解读

| 客户说的词 | 真实含义 |
|-----------|---------|
| **NT** / **NT STATUS** | IEC 104 协议中的 **No Time** — 数据点没有时间戳。**不是** "National Transmission" |
| **With time tag** | IEC 104 的 **CP56Time2a** 时标格式（7字节时间戳：秒、分、时、日、月、年、星期） |
| **Vini program** | 一款 IEC 104 协议测试软件，可以查看每个数据点的时间质量状态 |
| **AI points** | 模拟量输入（Analog Input），如电流 A 相、电压 AB 相、MW、Pf、KWh |
| **NT SCADA / NT调度** | IEC 104 调度主站系统，要求数据带时标上报 |

## IEC 104 ASDU 类型速查

| ASDU 类型 | 含义 | 是否带时标 |
|-----------|------|-----------|
| M_SP_NA_1 | 单点信息（状态量） | ❌ 无 |
| M_SP_TB_1 | 单点信息（带时标） | ✅ CP56Time2a |
| M_ME_NA_1 | 归一化测量值（模拟量） | ❌ 无 |
| M_ME_NB_1 | 标度化测量值 | ❌ 无 |
| M_ME_NC_1 | 短浮点测量值 | ❌ 无 |
| M_ME_TD_1 | 短浮点测量值（带时标） | ✅ CP56Time2a |
| M_ME_TE_1 | 归一化测量值（带时标） | ✅ CP56Time2a |
| M_ME_TF_1 | 短浮点测量值（带时标·精简） | ✅ CP56Time2a |
| C_CS_NA_1 | 时钟同步命令 | N/A |

> 客户需要的是 **M_ME_TF_1**（或 M_ME_TD_1）——模拟量带时标上报。

## BLIIOT 产品 IEC 104 支持状态

### BE102P / BE115(BE115P)
- 处理器：ARM MCU 300MHz
- IEC 104：仅上行（BE102P）/ 双向（BE115）
- **实测不支持模拟量带时标**（客户在 Vini 测试中确认 AI 点只显示 NT STATUS）
- 固件层面：BLIoTLink 的 IEC 104 协议栈只实现了无时标 ASDU 类型
- 结论：**不适合需要 CP56Time2a 时标的场景**

### BE116 (Smart Grid Edge Gateway)
- 处理器：双核 Cortex A7 1.2GHz + 512MB RAM + 8GB eMMC
- IEC 104：双向（下行+上行）
- 定位：智能电网专用
- 规格书未明确写时标支持，需向 BLIIOT 工程确认 BLIoTLink 固件版本是否支持

### BE190 (IEC104 Edge I/O Module)
- 定位：**专为 IEC 104 设计**的远程 I/O 模块
- 应用：智能变电站监控、配电自动化、电网调度数据网关
- 描述："map Modbus protocol instrument data to standard IEC 104 information objects"
- 是理论上最有可能支持全协议栈（含时标）的产品
- 规格书同样未明确写时标支持，需向工程确认

## 评估流程

当客户问"某产品是否支持 IEC 104 时间戳"：

1. **读客户聊天记录** — 看客户实际测试结果（实测 > 规格书）
2. **查规格书** — 看协议列在哪（下行/上行/双向），但规格书一般不会写 ASDU 类型级别
3. **区分产品层级**：
   - ARM MCU 平台（BE102P/BE115/BE115P 等塑胶壳系列）→ 轻量级协议转换，时标支持有限
   - 高性能平台（BE116/BE190 等）→ 专为智能电网/变电站设计，可能性更高
4. **找工程确认** — 最终答案取决于 BLIoTLink 固件实现的 ASDU 类型，只能问王工或研发

## Reference Material From Datasheets

BE116 full uplink protocol: `IEC104, OPC UA, MQTT, Modbus RTU, Modbus TCP, Huawei Cloud IoT, AWS IoT Core, Alibaba Cloud IoT, Thingsboard, BEILAI Cloud, Ignition SCADA`
BE116 full downlink protocol: `Siemens, Mitsubishi, Omron, Delta PLCs, Modbus RTU, Modbus TCP, DL/T645, IEC104, BACnet/IP, BACnet MS/TP`
