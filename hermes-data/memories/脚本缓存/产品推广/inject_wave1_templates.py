#!/usr/bin/env python3
"""Inject personalized email templates into BLIIOT mailer for Wave 1 leads"""

import json
import os
from pathlib import Path

SCRIPT_DIR = Path("C:/Users/Admin/AppData/Local/hermes/memories/脚本缓存/产品推广")
TEMPLATES_FILE = SCRIPT_DIR / ".templates.json"

# ===== Wave 1: 5 personalized templates =====

templates = {
    "advansys_best_fit": {
        "target_email": "information@advansys.co.za",
        "target_company": "Advansys",
        "subject": "Edge Computing & IIoT Gateways for Advansys SCADA Projects",
        "body_text": """Dear Advansys Team,

I came across Advansys while researching leading SCADA and industrial automation integrators in South Africa. Your expertise in PLC systems, MES, and batch solutions is impressive — especially your work across Food & Beverage, Mining, and Utilities.

I'm writing because I believe BLIIOT's product line could complement Advansys's existing offerings, particularly as your clients look to bridge their legacy SCADA systems with modern IIoT platforms.

We specialize in three areas directly relevant to your integration projects:

1. Industrial IoT Gateways (BL116/BL118)
   - Multi-protocol conversion: Modbus RTU/TCP ↔ PROFINET ↔ EtherNet/IP ↔ MQTT
   - Direct cloud connectivity (AWS/Azure/private) without middleware
   - PLC-agnostic data acquisition for mixed-brand environments

2. ARMxy Edge Controllers
   - Linux-based edge computing platform (Python, Node-RED)
   - Local data processing before cloud upload — reduces bandwidth costs
   - Can replace traditional PLCs in IIoT-centric architectures

3. R40 Series Industrial Routers
   - 4G/5G cellular connectivity for remote sites
   - VPN-secured communication back to central SCADA
   - Dual-WAN failover for mission-critical links

I'd love to send over our full product catalog and arrange a short call to discuss how we could support upcoming Advansys projects — especially any where clients are asking for remote monitoring, cloud connectivity, or edge processing capabilities.

Would that be of interest?

Best regards,
BLIIOT (Shenzhen Bliiot Technology Co., Ltd)
www.bliiot.com | bl42@bliiot.com""",
        "product_focus": ["Industrial Gateways", "ARMxy Edge Controllers", "R40 Routers"],
        "priority": "HIGH"
    },

    "integ_system_integrators": {
        "target_email": "info@integ.co.za",
        "target_company": "INTEG System Integrators",
        "subject": "Expanding INTEG's IIoT Capability with BLIIOT Edge Solutions",
        "body_text": """Dear INTEG Team,

Congratulations on your 2025 Best Partner Award — your team's work in control systems engineering across Food & Beverage, Pharma, and Water sectors clearly sets a high standard.

I'm reaching out because INTEG's core services (PLC systems, SCADA, HMI, MES, batching) align closely with the IIoT infrastructure gap many system integrators are helping clients address today. BLIIOT manufactures industrial connectivity hardware that slots directly into that gap.

Three products that may be particularly relevant:

1. ARMxy Edge Controllers
   - ARM-based edge computing with Linux + Node-RED
   - Ideal for pre-processing data before it reaches your SCADA layer
   - Programmable via Python for custom logic — extends what traditional PLCs can do

2. Industrial IoT Gateways (BL116/BA116 series)
   - Protocol conversion: Modbus ↔ PROFINET ↔ EtherNet/IP ↔ MQTT
   - Direct cloud push — no middleware server needed
   - Compact DIN-rail form factor for control panel integration

3. Remote IO (IOy Series)
   - Modular DI/DO/AI/AO configurations
   - Modbus RTU/TCP communication back to PLC or SCADA
   - Cost-effective field I/O expansion for distributed sites

We're already supporting system integrators in Europe, the Middle East, and across Africa with these solutions. I'd like to share our technical datasheets and see if there's a current INTEG project where our devices could add value.

Happy to send documentation or arrange a brief technical call.

Best regards,
BLIIOT (Shenzhen Bliiot Technology Co., Ltd)
www.bliiot.com | bl42@bliiot.com""",
        "product_focus": ["ARMxy Edge Controllers", "Industrial Gateways", "Remote IO"],
        "priority": "HIGH"
    },

    "sam_systems": {
        "target_email": "info@sam.co.za",
        "target_company": "SAM (Systems Automation & Management)",
        "subject": "IIoT Connectivity Solutions for SAM's 40-Year Automation Legacy",
        "body_text": """Dear SAM Team,

40 years of serving the South African automation industry is a remarkable milestone — from PLC and SCADA integration to industrial IT and BMS, SAM's breadth of expertise is impressive.

As your clients increasingly ask for remote monitoring, cloud connectivity, and edge computing capabilities alongside their existing SCADA investments, BLIIOT's product range could provide the hardware layer to make those transitions smooth and cost-effective.

Key products for SAM's integration projects:

1. R40 Series Industrial Routers
   - 4G/5G cellular with hardware VPN
   - Dual-WAN failover for critical remote sites
   - Industrial temperature rating for harsh environments

2. Industrial IoT Gateways (BL116/BE116)
   - Multi-protocol engine: Modbus, PROFINET, EtherNet/IP all in one device
   - Pre-integrated with major cloud platforms (AWS IoT, Azure IoT, Alibaba Cloud)
   - BLIoTLink software for remote PLC access and data mapping

3. ARMxy Edge Controllers
   - Linux edge computer with Node-RED, Python, OPC-UA support
   - Local data logging with SD card backup
   - Acts as IoT bridge between legacy fieldbus and modern IT systems

SAM's experience with Fieldbus systems and data acquisition makes you an ideal partner for deploying these solutions across your client base.

I'd be happy to share our full product portfolio and discuss how BLIIOT can support SAM's ongoing projects.

Best regards,
BLIIOT (Shenzhen Bliiot Technology Co., Ltd)
www.bliiot.com | bl42@bliiot.com""",
        "product_focus": ["R40 Routers", "Industrial Gateways", "ARMxy Edge Controllers"],
        "priority": "HIGH"
    },

    "amsi_wonderware": {
        "target_email": "info@amsi.co.za",
        "target_company": "AM Systems Integration",
        "subject": "Adding IIoT Hardware Layer to AMSI's Wonderware SCADA Solutions",
        "body_text": """Dear Michael and the AMSI Team,

I've been following AMSI's work as a Wonderware-registered system integrator — your turnkey approach from project design through programming and installation is exactly the kind of full-service capability we look to partner with.

BLIIOT manufactures industrial IoT hardware that works alongside Wonderware SCADA platforms to extend data acquisition capabilities at the field level.

Products that integrate naturally with your SCADA projects:

1. Remote IO Modules (IOy Series)
   - Flexible DI/DO/AI/AO configurations
   - Modbus RTU/TCP direct to Wonderware via OPC or Modbus driver
   - DIN-rail mount, industrial temperature range
   - Cost-effective field I/O expansion without replacing existing PLCs

2. Industrial IoT Gateways (BL116 series)
   - Protocol conversion: bring legacy Modbus RTU devices onto your TCP network
   - Built-in data logging and Edge computing
   - Cloud push for remote monitoring dashboards

3. ARMxy Edge Controllers
   - Local data preprocessing before SCADA ingestion
   - Custom Python scripts for data transformation
   - Acts as IoT bridge — ideal for Industry 4.0 upgrades

Many of our integrator partners use BLIIOT devices to add an IIoT layer without disrupting their existing SCADA architecture. I'd love to send over technical documentation and samples.

Would you be open to a brief conversation?

Best regards,
BLIIOT (Shenzhen Bliiot Technology Co., Ltd)
www.bliiot.com | bl42@bliiot.com""",
        "product_focus": ["Remote IO", "Industrial Gateways", "ARMxy Edge Controllers"],
        "priority": "HIGH"
    },

    "gil_nigeria": {
        "target_email": "info@gilautomation.com",
        "target_company": "Gil Automations Ltd",
        "subject": "Strengthening Gil Automation's IIoT Portfolio in Nigeria & West Africa",
        "body_text": """Dear Gil Automation Team,

As a Siemens Value-Added Reseller and Valmet partner with 195 staff across West Africa, Gil Automation's position in the Nigerian industrial market is unique. Your coverage of Oil & Gas, Power, and general industry makes you an ideal partner for industrial IoT expansion in the region.

BLIIOT designs and manufactures industrial IoT hardware that would complement Gil's existing Siemens and instrumentation portfolio:

1. Industrial IoT Gateways (BL116/BL118)
   - Multi-protocol: Siemens S7, Modbus, PROFINET, EtherNet/IP
   - Direct cloud connectivity — no middleware
   - Built to industrial standards for harsh field environments

2. ARMxy Edge Controllers
   - Linux-based edge computing, programmable via Python/Node-RED
   - Local data processing and protocol conversion
   - Remote device management via web dashboard

3. R40 Series Routers
   - 4G/5G with hardware VPN for remote oil & gas sites
   - Dual SIM failover for critical uptime
   - Wide input voltage for solar/battery powered installations

For the West African market specifically, our devices support:
- Remote pipeline monitoring (R40 + solar power)
- Generator/fleet telemetry via BL116 gateway
- SCADA RTU replacement with ARMxy edge controllers

We're looking for strong integration partners in Nigeria and would be delighted to explore how BLIIOT products fit Gil's sales and project pipeline.

Would you be interested in receiving our product catalog and discussing a partnership?

Best regards,
BLIIOT (Shenzhen Bliiot Technology Co., Ltd)
www.bliiot.com | bl42@bliiot.com""",
        "product_focus": ["Industrial Gateways", "ARMxy Edge Controllers", "R40 Routers"],
        "priority": "HIGH"
    }
}

# Save to mailer's template directory
os.makedirs(SCRIPT_DIR, exist_ok=True)
with open(TEMPLATES_FILE, 'w', encoding='utf-8') as f:
    json.dump(templates, f, indent=2, ensure_ascii=False)

print(f"✅ Saved {len(templates)} personalized templates to {TEMPLATES_FILE}")
print()
for key, t in templates.items():
    print(f"  📧 [{t['priority']}] {t['target_company']} → {t['target_email']}")
    print(f"     Subject: {t['subject']}")
    print(f"     Products: {', '.join(t['product_focus'])}")
    print()
print("=" * 60)
print("To send, first set SMTP authorization code:")
print("  python bliit_mailer.py --set-password")
print("Then send with:")
print("  python bliit_mailer.py --send")