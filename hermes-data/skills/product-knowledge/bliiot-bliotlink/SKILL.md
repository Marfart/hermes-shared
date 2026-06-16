---
name: bliiot-bliotlink
description: BLIoTLink 工业协议转换软件 — 各类PLC协议→Modbus/MQTT/OPC UA/BACnet/云平台, 256点免费, 安装于ARMxy/Linux网关
---

# BLIoTLink 工业协议转换软件

## 概述
BLIoTLink 是BLIIoT自研的工业协议转换软件, 预装于所有ARMxy和ARM高性能网关。

## 协议转换能力
**下游(数据源)**:
- 各品牌PLC协议(西门子/三菱/欧姆龙/施耐德/台达/汇川等)
- Modbus RTU Master, Modbus TCP Master
- DL/T645 电表协议

**上游(目标)**:
- Modbus TCP
- MQTT (ThingsBoard/华为云/阿里云/AWS IoT)
- OPC UA
- BACnet/IP
- 各IoT云平台直连

## 特性
- 支持4×串口 + 2×以太网口输入
- 免费: 1设备 + 256数据点
- 更多设备/点数需联系销售获取License
- 预装于所有Linux/Ubuntu网关
- 安装: `chmod 777 BLIoTLink.bin && ./BLIoTLink.bin`

## 文档路径
`产品规格书/英文资料/BLIoTLink/`

## 相关软件
- **BLRAT** — 远程访问维护工具
- **QuickConfig** — 快速配置工具
- **Node-RED** — 可视化编程环境(预装于BL118)