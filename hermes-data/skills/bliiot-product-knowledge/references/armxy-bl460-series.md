# ARMxy BL310~BL460 边缘控制器

## 概述
ARMxy系列基于Raspberry Pi Compute Module 4/5，是BLIIOT的边缘计算产品线。

## 型号命名规则
BL461L-CM5002016-X10 分解：
- BL461L: 主机型号 (461=1ETH variant), L=4G模块
- CM5: Compute Module 5 (BCM2712, Cortex-A76, 2.4GHz, RPi5-based)
- 00: 无WiFi
- 2: 2GB LPDDR4X
- 016: 16GB eMMC
- X10: I/O扩展板 (2 ETH + 4 RS485)

## SD Card Slot Rule
SD slot ONLY on Lite SOM (0GB eMMC). CM5002000=SD boot, others=eMMC boot.

## 4G模块选型
- 北美: EC25AFFA-512-SGAS (GPS) $33 + 30RMB
- 欧洲/非洲/中东/亚洲: EC25-EUXGR PCIE (GPS) $23 + 30RMB
- 中国/印度 CAT4: EC20CEHDLG (无GPS) $19 + 30RMB
- 中国4G CAT4: EC20-CE (GPS) $21 + 30RMB
- 4G与WiFi互斥

## 价格体系
- Online Store & Quotation = Sample price (1-9台)
- <100pcs / >=100pcs = 批量价
- SOM335特殊价: 文件写$62但实际420 RMB
- 4G模块加价30 RMB (按最新汇率换算USD)

## 文档路径
产品规格书/英文资料/ARM嵌入式控制器/BL460/ 等
