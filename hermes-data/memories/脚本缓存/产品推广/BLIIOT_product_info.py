#!/usr/bin/env python3
"""BLIIOT 产品信息库 — 供所有推广脚本调用的产品数据和宣传模板"""

PRODUCT_LINES = {
    "ARMxy": {
        "name": "ARMxy Industrial Edge Controllers",
        "short": "ARM Edge Controllers",
        "description": (
            "ARM-based industrial edge computers with modular I/O (RS485, RS232, CAN Bus, DI/DO). "
            "Runs Linux, Node-RED, Python. Ideal for edge computing, protocol conversion, and IIoT gateways."
        ),
        "models": ["BL301", "BL302", "BL304", "BL310", "BL330", "BL335", "BL340", "BL350", "BL360", "BL370", "BL410", "BL440", "BL450", "BL460"],
        "keywords": ["edge computing", "industrial controller", "arm computer", "iiot gateway", "modbus", "node-red"],
        "use_cases": ["SCADA", "IIoT", "Edge Computing", "Protocol Conversion", "Data Acquisition"],
    },
    "IOy": {
        "name": "IOy Series Programmable Remote IO",
        "short": "Remote I/O Modules",
        "description": (
            "Modular remote I/O modules supporting multiple fieldbus protocols. "
            "Flexible digital/analog I/O combinations for industrial automation and data acquisition."
        ),
        "keywords": ["remote io", "data acquisition", "modbus tcp", "rtu", "fieldbus"],
        "use_cases": ["Industrial Automation", "Building Automation", "Remote Monitoring"],
    },
    "BL116_BE116_BA116": {
        "name": "BL116 / BE116 / BA116 Industrial IoT Gateways",
        "short": "Industrial IoT Gateways",
        "description": (
            "Compact industrial IoT gateways with 4G LTE, dual Ethernet, RS485, "
            "pre-loaded with Node-RED and Modbus. Perfect for remote equipment monitoring and smart manufacturing."
        ),
        "keywords": ["iot gateway", "4g router", "industrial gateway", "modbus gateway", "node-red"],
        "use_cases": ["IIoT", "Smart Manufacturing", "Equipment Monitoring", "Building Automation"],
    },
    "R40": {
        "name": "R40 Series Industrial Cellular Routers",
        "short": "Industrial Cellular Routers",
        "description": (
            "Industrial 4G LTE cellular routers with dual SIM, dual Ethernet, WiFi, GPS, "
            "and wide voltage input. Designed for reliable connectivity in harsh environments."
        ),
        "keywords": ["cellular router", "4g lte router", "industrial router", "vpn router"],
        "use_cases": ["Remote Connectivity", "Oil & Gas", "Transportation", "Smart Grid"],
    },
    "RTU50xx": {
        "name": "RTU5020 Series Remote Terminal Units",
        "short": "RTU / Remote Terminal Units",
        "description": (
            "Remote terminal units with 4G LTE connectivity, digital/analog I/O, "
            "and built-in Modbus support for SCADA and telemetry applications."
        ),
        "keywords": ["rtu", "remote terminal unit", "scada", "telemetry", "modbus rtu"],
        "use_cases": ["SCADA", "Water/Wastewater", "Oil & Gas", "Environmental Monitoring"],
    },
    "EdgePLC": {
        "name": "EdgePLC Series",
        "short": "Edge PLC Controllers",
        "description": (
            "PLC + edge computing hybrid controllers combining traditional PLC reliability "
            "with IIoT connectivity for smart manufacturing."
        ),
        "keywords": ["plc", "edge plc", "programmable controller", "iiot"],
        "use_cases": ["Industrial Automation", "Smart Manufacturing", "Machine Control"],
    },
}

COMPANY_INFO = {
    "name": "BLIIOT (Shenzhen BLIIOT Technology Co., Ltd.)",
    "short": "BLIIOT",
    "website": "https://www.bliiot.com",
    "whatsapp": "+86 17704014518",
    "email": "bl42@bliiot.com",
    "phone_reg": "17704014518",
    "tagline": "Industrial IoT Connectivity Solutions Provider",
    "description": (
        "BLIIOT is a leading manufacturer of industrial IoT hardware based in Shenzhen, China. "
        "We specialize in ARMxy edge controllers, IoT gateways, remote I/O modules, industrial cellular routers, "
        "and RTU solutions. Our products power SCADA systems, smart manufacturing, building automation, "
        "and remote monitoring applications worldwide."
    ),
    "strengths": [
        "10+ years of industrial automation experience",
        "Full R&D and manufacturing in-house",
        "Custom/OEM solutions available",
        "Global shipping with fast delivery",
        "Technical support with quick response",
        "Cost-effective compared to European/US brands",
    ],
}

HASHTAGS = [
    "#IndustrialIoT", "#IIoT", "#SCADA", "#EdgeComputing", "#IndustrialAutomation",
    "#IoTGateway", "#RemoteMonitoring", "#PLC", "#Modbus", "#SmartManufacturing",
    "#Industry40", "#IoT", "#M2M", "#Telemetry", "#RTU",
]

def get_product_pitch(target_segment="generic"):
    """返回不同目标受众的产品介绍"""
    pitches = {
        "scada_plc": (
            "BLIIOT provides industrial edge controllers and remote I/O modules "
            "that integrate seamlessly with SCADA systems. Our ARMxy series supports "
            "Modbus TCP/RTU, OPC UA, and MQTT for easy PLC connectivity."
        ),
        "system_integrator": (
            "BLIIOT offers a complete range of industrial IoT hardware including "
            "ARM edge controllers, IoT gateways, remote I/O modules, and industrial routers. "
            "All products support Node-RED, Python, and multiple industrial protocols."
        ),
        "energy_monitoring": (
            "BLIIOT's R40 cellular routers and RTU series provide reliable connectivity "
            "for energy monitoring and smart grid applications. Dual SIM + dual Ethernet "
            "ensure maximum uptime for critical infrastructure."
        ),
        "generic_iiot": (
            "BLIIOT manufactures industrial IoT hardware: edge computers, IoT gateways, "
            "remote I/O modules, and 4G routers. We serve over 50 countries across "
            "manufacturing, energy, building automation, and smart agriculture."
        ),
    }
    return pitches.get(target_segment, pitches["generic_iiot"])

def get_company_intro():
    """公司自我介绍"""
    return (
        "Hi, I represent BLIIOT Technology, a professional industrial IoT hardware "
        "manufacturer based in Shenzhen, China with 10+ years in the automation industry."
    )

def get_cta():
    """行动号召"""
    return (
        "If you're interested in our products for your projects, feel free to reach out on WhatsApp: "
        "+86 17704014518. I'd be happy to share our catalog and discuss your requirements!"
    )

if __name__ == "__main__":
    print("BLIIOT Product Info Library loaded successfully!")
    print(f"Product lines: {list(PRODUCT_LINES.keys())}")