#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RFQ分析：Online Monitoring System
客户需求：GSM/GPRS + RS485/RS232 + Ethernet + WiFi + Modbus + Cloud + SMS + SCADA + IP65 + (-20~70°C)
预算：$120-$150 样品价
"""

print("=" * 80)
print("RFQ 分析：Online Monitoring System")
print("=" * 80)
print("""
客户需求规格：
  通信: GSM/GPRS, RS485, RS232, Ethernet, WiFi
  协议: Modbus RTU/TCP, HTTP, FTP
  数据: Web portal, cloud dashboard, SMS alerts
  集成: SCADA / IoT platforms
  防护: IP65 (outdoor), UV-stabilized material
  安装: Pole-mounted / Tripod with grounding
  温度: -20°C to +70°C
  湿度: 0-100% RH, non-condensing
  认证: CE, RoHS, FCC
  预算: $120-$150 样品价
""")

print("=" * 80)
print("关键约束分析")
print("=" * 80)
print("""
⛔ IP65 是硬约束 — BLIIOT 标准产品全部是 IP30（室内型）
   → 只有 IPM100 是 IP67（但它是IO模块，不是完整网关）
   → 其他产品需要配防水箱才能达到IP65

⛔ 完整功能（GSM+RS485+RS232+Ethernet+WiFi+Modbus+Cloud+SMS）
   → 只有 R40/R40A/R40B 和 S275/S274 有内置GSM+多接口
   → BL116/BL118/ARMxy 需要加4G模块才有GSM

⛔ $120-$150 样品价预算
   → 内置GSM的产品样品价普遍 >$120
   → 需要加4G模块的底座产品总价容易超预算
""")

print("=" * 80)
print("候选产品筛选（样品价 $120-$150）")
print("=" * 80)

# 从所有报价文件中提取的样品价数据
candidates = [
    # IIoT Gateways (BL120系列)
    ("BL120PL 4G L-CE", 110.93, "IIoT Gateway", "4G+RS485+RS232+Ethernet", "IP30"),
    ("BL120PL 4G L-E", 118.24, "IIoT Gateway", "4G+RS485+RS232+Ethernet", "IP30"),
    ("BL120PLG 4G L-CE", 117.09, "IIoT Gateway", "4G+RS485+RS232+Ethernet+WiFi", "IP30"),
    ("BL120PLG 4G L-E", 120.33, "IIoT Gateway", "4G+RS485+RS232+Ethernet+WiFi", "IP30"),
    ("BL120PLG 4G L-AU", 123.43, "IIoT Gateway", "4G+RS485+RS232+Ethernet+WiFi", "IP30"),
    ("BL120PLG 4G L-A", 130.12, "IIoT Gateway", "4G+RS485+RS232+Ethernet+WiFi", "IP30"),
    ("BL120PMPL 4G L-CE", 110.93, "IIoT Gateway", "4G+PLC+RS485+RS232+Ethernet", "IP30"),
    ("BL120PMPL 4G L-E", 118.24, "IIoT Gateway", "4G+PLC+RS485+RS232+Ethernet", "IP30"),
    ("BL120PMPLG 4G L-CE", 117.09, "IIoT Gateway", "4G+PLC+RS485+RS232+Ethernet+WiFi", "IP30"),
    ("BL120PMPLG 4G L-E", 120.33, "IIoT Gateway", "4G+PLC+RS485+RS232+Ethernet+WiFi", "IP30"),
    ("BL120PMPLG 4G L-AU", 123.43, "IIoT Gateway", "4G+PLC+RS485+RS232+Ethernet+WiFi", "IP30"),
    ("BL120PMPLG 4G L-A", 130.12, "IIoT Gateway", "4G+PLC+RS485+RS232+Ethernet+WiFi", "IP30"),
    ("BL120ACPL 4G L-CE", 110.93, "IIoT Gateway", "4G+RS485+RS232+Ethernet", "IP30"),
    ("BL120ACPL 4G L-E", 118.24, "IIoT Gateway", "4G+RS485+RS232+Ethernet", "IP30"),
    ("BL120ACPLG 4G L-CE", 117.09, "IIoT Gateway", "4G+RS485+RS232+Ethernet+WiFi", "IP30"),
    ("BL120ACPLG 4G L-E", 120.33, "IIoT Gateway", "4G+RS485+RS232+Ethernet+WiFi", "IP30"),
    ("BL120ACPLG 4G L-AU", 123.43, "IIoT Gateway", "4G+RS485+RS232+Ethernet+WiFi", "IP30"),
    ("BL120ACPLG 4G L-A", 130.12, "IIoT Gateway", "4G+RS485+RS232+Ethernet+WiFi", "IP30"),
    ("BL120DTPL 4G L-CE", 110.93, "IIoT Gateway", "4G+IEC104+RS485+RS232+Ethernet", "IP30"),
    ("BL120DTPL 4G L-E", 118.24, "IIoT Gateway", "4G+IEC104+RS485+RS232+Ethernet", "IP30"),
    ("BL120DTPLG 4G L-CE", 117.09, "IIoT Gateway", "4G+IEC104+RS485+RS232+Ethernet+WiFi", "IP30"),
    ("BL120DTPLG 4G L-E", 120.33, "IIoT Gateway", "4G+IEC104+RS485+RS232+Ethernet+WiFi", "IP30"),
    ("BL120DTPLG 4G L-AU", 123.43, "IIoT Gateway", "4G+IEC104+RS485+RS232+Ethernet+WiFi", "IP30"),
    ("BL120DTPLG 4G L-A", 130.12, "IIoT Gateway", "4G+IEC104+RS485+RS232+Ethernet+WiFi", "IP30"),
    ("BL120BNPL 4G L-CE", 110.93, "IIoT Gateway", "4G+BACnet+RS485+RS232+Ethernet", "IP30"),
    ("BL120BNPL 4G L-E", 118.24, "IIoT Gateway", "4G+BACnet+RS485+RS232+Ethernet", "IP30"),
    ("BL120BNPLG 4G L-CE", 117.09, "IIoT Gateway", "4G+BACnet+RS485+RS232+Ethernet+WiFi", "IP30"),
    ("BL120BNPLG 4G L-E", 120.33, "IIoT Gateway", "4G+BACnet+RS485+RS232+Ethernet+WiFi", "IP30"),
    ("BL120BNPLG 4G L-AU", 123.43, "IIoT Gateway", "4G+BACnet+RS485+RS232+Ethernet+WiFi", "IP30"),
    ("BL120BNPLG 4G L-A", 130.12, "IIoT Gateway", "4G+BACnet+RS485+RS232+Ethernet+WiFi", "IP30"),
    # BL116
    ("BL116-SOM334+4G模块", 64.0+23.0, "High-Perf Gateway", "2ETH+4RS485+4G", "IP30"),
    ("BL116A-SOM334+4G模块", 78.0+23.0, "High-Perf Gateway", "2ETH+8RS485+4G", "IP30"),
    # BL118
    ("BL118B-SOM335-X4-Y02-Y31", 149.0, "Node-RED Gateway", "2ETH+4RS485+4DI+4DO+4AI, 需加4G", "IP30"),
    # R40系列
    ("R40 CE version", 122.32, "4G Router", "4G+2DI+2DO+1RS485+1RS232+WiFi+Ethernet+MQTT+Cloud", "IP30"),
    ("R40 E version", 126.29, "4G Router", "4G+2DI+2DO+1RS485+1RS232+WiFi+Ethernet+MQTT+Cloud", "IP30"),
    ("R40A CE version", 132.10, "4G Router", "4G+Master+2DI+2DO+1RS485+1RS232+WiFi+Ethernet+MQTT+Cloud", "IP30"),
    ("R40A E version", 136.39, "4G Router", "4G+Master+2DI+2DO+1RS485+1RS232+WiFi+Ethernet+MQTT+Cloud", "IP30"),
    # RTU系列
    ("S270 4G CE", 118.61, "Cellular RTU", "2DI+2AI+2Relay+Modbus+MQTT+SMS", "IP30"),
    ("S270 4G E", 126.32, "Cellular RTU", "2DI+2AI+2Relay+Modbus+MQTT+SMS", "IP30"),
    ("S271 4G E", 135.68, "Cellular RTU", "4DI+4AI+4Relay+Modbus+MQTT+SMS", "IP30"),
    # K系列
    ("K5S 4G CE", 131.84, "GSM Communicator", "4G+SMS/GPRS/Ethernet+2DO", "IP30"),
    ("K5S 4G E", 139.23, "GSM Communicator", "4G+SMS/GPRS/Ethernet+2DO", "IP30"),
    ("K5 4G E", 102.76, "GSM Communicator", "4G+SMS/GPRS", "IP30"),
    ("K6 4G E", 120.38, "GSM Access Control", "4G+Relay", "IP30"),
    ("K9 4G E", 114.05, "GSM Alarm", "4G+touch keypad+95 zones", "IP30"),
    # IOy
    ("BL190+4G模块", 40.0+23.0, "Edge IO", "Modbus TCP+2ETH+1RS485+4G", "IP30"),
    ("BL192+4G模块", 51.0+23.0, "Edge IO", "MQTT+2ETH+1RS485+4G", "IP30"),
    # ARMxy BL310
    ("BL310-SOM312-X1+4G", 36.0+23.0, "ARMxy", "2ETH+4RS485+4G", "IP30"),
    # ARMxy BL460
    ("BL460-CM5002000-X10", 51.0, "ARMxy CM5", "2ETH+4RS485, 需加4G", "IP30"),
    ("BL461-CM5002016-X10", 71.0, "ARMxy CM5", "2ETH+4RS485, 需加4G", "IP30"),
]

# 筛选 $120-$150 范围内的
in_budget = [(name, price, cat, feat, ip) for name, price, cat, feat, ip in candidates if 120 <= price <= 150]

print(f"\n在 $120-$150 样品价范围内的产品 ({len(in_budget)} 个):")
print("-" * 80)
for name, price, cat, feat, ip in sorted(in_budget, key=lambda x: x[1]):
    print(f"  ${price:>7.2f} | {name:<35s} | {cat:<20s} | {ip}")
    print(f"         | {feat}")
    print()

print("=" * 80)
print("⭐ 最佳匹配推荐（按功能覆盖度排序）")
print("=" * 80)
print("""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🥇 最推荐：R40 (CE version) — $122.32 样品价
   ✅ 4G LTE 内置（覆盖GSM/GPRS需求）
   ✅ RS485 + RS232 各1路
   ✅ Ethernet (1WAN/LAN + 3LAN)
   ✅ WiFi 2.4G 内置 (AP/Client)
   ✅ Modbus RTU/TCP Slave
   ✅ MQTT + AWS + Aliyun + Huawei Cloud + KPIIOT Cloud
   ✅ 2DI + 2DO
   ✅ OpenWRT OS，支持逻辑编程
   ✅ 9-57VDC 宽电压
   ✅ VPN: IPSec, L2TP, OpenVPN
   ✅ 支持SCADA集成（通过Modbus/OPC UA/MQTT）
   ❌ IP30（需配防水箱才能户外使用，额外$20-50）
   → 温度：规格书工业级，应覆盖-20~70°C，需确认
   → GPS可选（+$3.34）
   → PoE可选（+$10.60）

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🥈 次推荐：BL120PLG 4G L-E — $120.33 样品价
   ✅ 4G LTE 内置
   ✅ RS485 + RS232
   ✅ Ethernet + WiFi 内置
   ✅ Modbus RTU/TCP（上行+下行）
   ✅ PLC协议下行（Siemens/Mitsubishi/Omron/Delta）
   ✅ 支持SCADA集成
   ❌ IP30（需配防水箱）
   ❌ 无内置SMS（需通过云端平台实现）
   → 优势：PLC协议支持更丰富，适合工业监控场景
   → 交流供电版本可选（BL120ACPLG）

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🥉 备选1：R40A CE version — $132.10 样品价
   ✅ 比R40多了Modbus Master功能（可采集下级设备）
   ✅ 其他同R40
   → 如果客户需要Modbus Master采集下级设备数据，选这个
   → 如果只需要Slave，R40更便宜

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🏅 备选2：S270 4G E version — $126.32 样品价
   ✅ 4G LTE 内置
   ✅ 2DI + 2AI + 2Relay
   ✅ Modbus RTU/TCP + MQTT
   ✅ SMS告警（I/O触发/恢复/电源故障）
   ✅ 内置内存保存200条历史数据
   ✅ 9-36VDC
   ❌ 无RS232
   ❌ 无WiFi
   ❌ 无Ethernet
   ❌ IP30
   → 适合简单数据采集场景，功能较精简

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ 关键问题汇总：

1. IP65防护 — 这是最大障碍
   BLIIOT所有标准产品都是IP30（室内型）。
   解决方案：
   a) 配防水箱（额外$20-50）
   b) 如果客户能接受IP67，可以考虑IPM100（但它是IO模块不是网关）
   c) 向公司咨询是否有IP65外壳版本

2. 温度范围
   规格书写工业级-40~85°C，应该覆盖-20~70°C
   但需要向公司确认具体型号的工作温度范围

3. SCADA集成
   所有产品都支持Modbus RTU/TCP或OPC UA
   可以通过这些协议对接主流SCADA系统
   R40系列还支持MQTT直连云平台

4. SMS功能
   R40/K系列有内置SMS告警
   BL120系列需要通过云端平台（如阿里云/华为云）发通知
   S270/S271/S272有内置SMS告警

5. 认证
   BLIIOT产品一般有CE、RoHS认证
   FCC需要确认（部分型号可能没有）

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 建议报价方案：

方案A（最经济）：R40 CE version — $122.32
  + 防水箱 — ~$30
  合计：~$152.32（略超预算但功能最全）

方案B（功能优先）：R40A CE version — $132.10
  + 防水箱 — ~$30
  合计：~$162.10（支持Modbus Master）

方案C（工业协议）：BL120PLG 4G L-E — $120.33
  + 防水箱 — ~$30
  合计：~$150.33（支持PLC协议）

方案D（简单监控）：S270 4G E — $126.32
  + 防水箱 — ~$30
  合计：~$156.32（适合简单数据采集）

""")
