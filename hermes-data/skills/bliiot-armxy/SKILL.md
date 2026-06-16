---
name: bliiot-armxy
description: ARMxy 系列 ARM 嵌入式控制器产品知识 — BL301/BL302/BL303/BL304/BL310/BL330/BL335/BL340/BL350/BL360/BL370/BL410/BL440/BL450/BL460 完整规格、处理器、接口、OS、认证及应用场景
---

# ARMxy ARM嵌入式控制器系列 (BLIIoT)

## 产品矩阵总览

| 型号 | 处理器 | 核心 | 频率 | RAM | 存储 | 网口 | NPU | 特色 |
|------|--------|------|------|-----|------|------|-----|------|
| BL301 | NXP i.MX6ULL | Cortex-A7×1 | 800MHz | 256MB DDR3L | 8GB eMMC | 1×100M | — | 入门级，1网口 |
| BL302 | NXP i.MX6ULL | Cortex-A7×1 | 800MHz | 256MB DDR3L | 8GB eMMC | 2×100M | — | 入门级，2网口 |
| BL303 | Allwinner T113-i | 双CA7+RISC-V+DSP | 1.2GHz | 512MB DDR3L | 8GB eMMC | 1×100M | — | Docker |
| BL304 | Allwinner T113-i | 双CA7+RISC-V+DSP | 1.2GHz | 512MB DDR3L | 8GB eMMC | 2×100M | — | Ignition支持 |
| BL310 | NXP i.MX6ULL | Cortex-A7×1 | 800MHz | 256-512MB | 4-8GB | 2×100M | — | 经典畅销款 |
| BL330 | Allwinner T113-i | 双CA7+RISC-V+DSP | 1.2GHz | 512MB DDR3L | 8GB | 1-3可选 | — | 国产异构，光伏 |
| BL335 | Allwinner T113-i | 双CA7 | 1.2GHz | 512MB | 8GB | 2×100M | — | 4000+组合 |
| BL340 | Allwinner T507-H | 四核CA53 | 1.4GHz | 1-2GB DDR4 | 8-16GB | 1-3可选 | — | 四核性价 |
| BL350 | TI Sitara AM62x | 1-4×CA53+M4F | 1.4GHz | 512MB-2GB | 8-32GB | 1-3可选 | — | 16nm,3D GPU |
| BL360 | NXP i.MX8M Mini | 四核CA53+M4 | 1.6GHz | 1-2GB DDR4 | 8-16GB | 1-3可选 | — | 视频编解码 |
| BL370 | Rockchip RK3562/J | 四核CA53+M0 | 1.8GHz | 1-4GB LPDDR4X | 8-32GB | 1-3×100M | 1TOPS | 入门NPU |
| BL410 | Rockchip RK3568J | 四核CA55 | 1.8GHz | 1-4GB LPDDR4X | 8-32GB | 3×100M | 1TOPS | 经典NPU |
| BL440 | Rockchip RK3576J | 4×CA72+4×CA53 | 2.1GHz | 2-8GB LPDDR4X | 16-64GB | 2×千兆+1×百兆 | 6TOPS | 双千兆 |
| BL450 | Rockchip RK3588J | 4×CA76+4×CA55 | 2.4GHz | 4-16GB LPDDR4X | 32-128GB | 2×千兆+1×百兆 | 6TOPS | 旗舰8K |
| BL460 | BCM2712 (Pi5) | 四核CA76 | 2.4GHz | 最大16GB | 最大64GB | 1-3含千兆 | — | Pi生态 |

## 详细规格

### 各型号关键特性

**BL301/BL302** — 入门级
- NXP i.MX6ULL, ARM Cortex-A7 @800MHz
- 预装BLIoTLink+BLRAT+QuickConfig+Node-Red
- 支持Python, QT, SQLite

**BL303/BL304** — 进阶版
- Allwinner T113-i 异构多核(CA7+RISC-V+DSP)
- 额外支持Docker, Ignition, Eclipse

**BL310** — 经典畅销
- 选配SOM板：256/512MB DDR3L, 4/8GB eMMC
- X板30种+ Y板18种IO组合
- Mini PCIe → WiFi/4G

**BL330** — 国产异构(光伏储能专用)
- Allwinner T113-i 三核异构，国产自主

**BL340** — 四核性能
- Allwinner T507-H 四核CA53 @1.4GHz

**BL350** — TI工业级
- TI AM62x 16nm, 可选1-4核CA53+M4F协核
- 3D GPU加速，Yocto/Debian
- 应用：EMS/BMS, EV充电桩, AGV, 医疗

**BL360** — 视频处理
- NXP i.MX8M Mini 14nm
- 1080P60 H.264编解码

**BL370** — 入门NPU (1TOPS)
- 4K@30fps H.265

**BL410** — 经典NPU (1TOPS) 3网口

**BL440** — 高性能NPU (6TOPS)
- 首款双千兆+USB 3.2
- 8K@30fps H.265解码

**BL450** — 旗舰NPU (6TOPS)
- 8K@60fps H.265解码
- 最大16GB/128GB

**BL460** — Pi CM5生态
- 40-pin GPIO+WiringPi
- 仅-20~85°C
- 无NPU但生态庞大

## 通用特性
- 所有型号预装: BLIoTLink+BLRAT+QuickConfig
- X系列IO板: RS485/RS232/CAN/DI/DO/GPIO
- Y系列IO板: DI/DO/Relay/AI/AO/RTD/TC/脉冲
- 无线: Mini PCIe→WiFi/4G/5G
- 温度: -40~85°C (除BL460)
- 安装: DIN35导轨
- 认证: EMC/EMI, 高低温, 振动/跌落/IP
- 协议: Modbus RTU/TCP, MQTT, OPC UA, BACnet, PLC协议

## 命名规则
`主机-SOM型号-X板-Y1板-Y2板`
后缀W=WiFi, L=4G
例: BL310-SOM312-X4 = 2网口+512MB+8GB+2RS485+2CAN

## 源码路径
`产品规格书/英文资料/ARM嵌入式控制器/` 每个型号独立目录