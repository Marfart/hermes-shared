# IIoT 高性能网关 (BL116/BL118/BE116/BA116)

## BL116 / BE116 / BA116
- **处理器**: 双核Cortex-A7 @1.2GHz
- **RAM**: 512MB / 1GB
- **存储**: 8GB eMMC
- **以太网**: 2xRJ45 10/100Mbps
- **串口**: 4xRS485/RS232 (隔离)
- **4G**: 可选 (L-E/L-CE/L-A/L-AU/L-AF/CAT-1)
- **GPS**: 可选
- **供电**: DC 12~24V
- **温宽**: -40°C~85°C
- **协议**: Modbus RTU/TCP, MQTT, OPC UA, IEC104(BE116), BACnet/IP(BA116)
- **特点**: 双网口+可选WiFi/4G/5G

## BL118 (Node-RED 网关)
- **处理器**: 双核Cortex-A7 @1.2GHz
- **RAM/存储**: 1GB + 16GB
- **以太网**: 1xGigabit
- **串口**: 4xRS485
- **扩展**: X板(ETH/RS485) + Y板(DI/DO/AI/AO/RTD/TC), 最多2个Y板
- **Node-RED**: 预装
- **4G**: 仅4G (无5G)
- **远程工具**: BLRAT (无OpenVPN)
- **协议**: Modbus, MQTT, OPC UA, Node-RED逻辑

## 命名规则
```
BL118B-SOM334-X4-Y02-Y31
│      │       │   │   └── Y2板型号
│      │       │   └────── Y1板型号
│      │       └────────── X板型号
│      └────────────────── SOM型号
└───────────────────────── 主机型号 (A=1个Y板, B=2个Y板)
```

## X板型号
X0=$5, X2=$6, X4=$8, X6=$10, X7=$10, X8=$12, X10=$12

## SOM型号
SOM332, SOM334, SOM335, SOM353, SOM354, SOM355

## 文档路径
产品规格书/英文资料/ARM高性能网关/BL116/
产品规格书/英文资料/ARM高性能网关/BL118/
