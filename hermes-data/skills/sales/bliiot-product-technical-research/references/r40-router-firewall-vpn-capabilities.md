# R40 Industrial Cellular Router — Firewall & VPN Capabilities

> Source: `BLIIOT R40 Industrial Cellular Router Data Sheet V2.0.docx` at `2025新版R40系列/规格书/`

## Processor
- MIPS CPU, Clock Speed: 580 MHz

## Key Differentiator
R40 is the **only BLIIOT product with built-in firewall functionality**. All other BLIIOT products (gateways, RTUs, IO modules) do NOT have firewall/DMZ/IT-OT isolation features.

## Firewall Features
- **DMZ** — Demilitarized Zone support
- **DoS Protection** — Denial of Service attack prevention
- **IP Packet Filtering** — Source/destination IP rules
- **Domain Name Filtering** — Block/allow by domain
- **MAC Address Filtering** — Block/allow by hardware address
- **Port Mapping** — Forward external ports to internal devices
- **Access Control** — Role-based network access rules

## VPN Tunnel Support
- **IPsec** — Standard IPsec VPN tunnel
- **OpenVPN** — OpenVPN client/server
- **L2TP** — Layer 2 Tunneling Protocol

## I/O Capabilities (Not All Versions!)
Some R40 models include:
- **1×RS485 + 1×RS232**
- **DI (Digital Input)**
- **DO (Digital Output)**
- **AI (Analog Input)**
- Modbus master/slave function
- MQTT function
- Logic control function

This makes certain R40 models a **3-in-1 device** (router + firewall + protocol gateway + limited I/O).

## Cellular
- 4G LTE (dual SIM with automatic failover)
- M.2 form factor module (customizable per region)

## Physical
- 4×RJ45 (1 WAN + 3 LAN, all 10/100Mbps)
- Optional PoE PSE (IEEE 802.3af/at, up to 30W)
- WiFi STA/AP mode (2.4G, up to 20m outdoors)
- DIN35 rail or wall mounting
- 9~36V DC input
- Independent hardware watchdog
- Operating temp: -40°C to 85°C

## Use Case: MES/IoT Access Solution
When customer needs:
- Firewall/DMZ for IT/OT isolation → R40
- VPN for remote maintenance → R40
- Field data acquisition → R40 + gateway (e.g. BL116 for protocol conversion)

R40 is placed at the **network edge** between the field devices and the corporate IT network.

## Limitations
- No OPC UA or higher-level protocol support (pure network layer)
- Cellular-only WAN (no fiber/DSL WAN option)
- 100Mbps Ethernet only (no Gigabit)