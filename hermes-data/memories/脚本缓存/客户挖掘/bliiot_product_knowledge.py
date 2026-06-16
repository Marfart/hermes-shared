"""
BLIIOT 产品知识与匹配引擎 v1.0
===============================
从datasheet/报价文件提取的产品矩阵 + 客户需求匹配逻辑
"""

# ====== 产品家族总览 ======

PRODUCT_FAMILIES = {
    "ARMxy Edge Controllers": {
        "aliases": ["ARM嵌入式控制器", "ARMxy", "ARM edge", "BL310", "BL320", "BL330"],
        "type": "edge_controller",
        "description": "基于ARM处理器的边缘控制器/计算机，支持Linux系统，可运行Node-RED、Python等",
        "use_cases": [
            "边缘计算与数据处理",
            "PLC/SCADA数据采集与协议转换",
            "工业物联网网关功能",
            "设备远程监控与控制",
        ],
        "target_customers": [
            "系统集成商 needing edge computing",
            "工厂自动化需要本地数据处理",
            "SCADA系统需要远程终端单元",
        ],
        "keywords": ["edge computing", "edge controller", "ARM", "embedded", "Linux gateway", "programmable controller"],
    },

    "Industrial Gateways (BL116/BL118/BE116/BA116)": {
        "aliases": ["IIoT Gateways", "BL116", "BL118", "BE116", "BA116", "工业网关"],
        "type": "gateway",
        "description": "工业物联网网关，支持多种PLC协议（Modbus、PROFINET、EtherNet/IP等），4G/5G/WiFi通信",
        "use_cases": [
            "PLC数据采集与云平台对接",
            "Modbus RTU/TCP转MQTT/HTTP",
            "工业设备远程运维",
            "多协议转换（Modbus/PROFINET/EtherNet/IP）",
            "Building automation / HVAC 系统集成",
        ],
        "target_customers": [
            "PLC/SCADA系统集成商",
            "工厂自动化部门",
            "楼宇自动化项目",
            "能源监控项目",
        ],
        "keywords": ["protocol gateway", "Modbus gateway", "PLC gateway", "IIoT gateway", "industrial gateway", "protocol converter", "Modbus TCP", "PROFINET", "EtherNet/IP"],
    },

    "Remote IO / RTU (IOy Series)": {
        "aliases": ["IOy", "远程IO", "RTU", "IOy系列"],
        "type": "remote_io",
        "description": "多功能可编程远程IO模块，支持多种IO组合（DI/DO/AI/AO），Modbus RTU/TCP通信",
        "use_cases": [
            "远程数据采集（数字量/模拟量）",
            "工业现场IO扩展",
            "SCADA系统现场数据采集",
            "远程设备控制",
            "能源管理与监控",
        ],
        "target_customers": [
            "SCADA系统集成商",
            "水处理/能源/电力监控项目",
            "工厂自动化需要远程IO",
        ],
        "keywords": ["remote IO", "RTU", "data acquisition", "Modbus IO", "digital input", "analog input", "IO module", "remote terminal unit"],
    },

    "R40 Series Routers": {
        "aliases": ["R40", "路由器", "R40系列"],
        "type": "router",
        "description": "工业4G/5G路由器，支持VPN、多WAN备份、工业级可靠性",
        "use_cases": [
            "远程站点网络连接",
            "VPN安全通信",
            "4G/5G蜂窝网络备份",
            "分布式站点网络互联",
        ],
        "target_customers": [
            "远程监控项目需要蜂窝连接",
            "分布式站点网络互联",
            "石油/天然气/水务远程站点",
        ],
        "keywords": ["industrial router", "4G router", "5G router", "VPN router", "cellular router", "remote connectivity"],
    },

    "RTU50xx Series": {
        "aliases": ["RTU50xx", "RTU5000"],
        "type": "rtu",
        "description": "远程终端单元，专为SCADA系统设计，支持多种IO和通信协议",
        "use_cases": [
            "SCADA系统远程站点数据采集",
            "电力/水务/油气监控",
            "环境监测",
        ],
        "target_customers": [
            "电力系统集成商",
            "水务/环保监控项目",
            "SCADA系统集成",
        ],
        "keywords": ["RTU", "SCADA RTU", "remote terminal unit", "telemetry", "SCADA data acquisition"],
    },

    "Signal Isolators": {
        "aliases": ["隔离器", "BL15x", "BL151", "BL152", "BL153", "BL154", "BL155"],
        "type": "isolator",
        "description": "信号隔离器，用于工业信号隔离、转换和分配，确保系统安全和信号完整性",
        "use_cases": [
            "模拟信号隔离（4-20mA/0-10V）",
            "温度传感器信号隔离",
            "开关量信号隔离",
            "信号转换与分配",
        ],
        "target_customers": [
            "工业控制系统集成商",
            "配电/电力监控项目",
            "工厂自动化需要信号隔离",
        ],
        "keywords": ["signal isolator", "signal conditioner", "4-20mA isolator", "analog isolator", "temperature transmitter"],
    },

    "Industrial Switches": {
        "aliases": ["交换机", "BL16x", "BL168"],
        "type": "switch",
        "description": "工业以太网交换机，支持PoE、冗余环网、工业级宽温设计",
        "use_cases": [
            "工业现场网络部署",
            "PoE供电设备连接",
            "冗余环网网络架构",
        ],
        "target_customers": [
            "工厂自动化网络部署",
            "视频监控系统集成",
            "工业网络基础设施",
        ],
        "keywords": ["industrial switch", "PoE switch", "managed switch", "Ethernet switch", "ring network"],
    },

    "Software (BLIoTLink / BLRAT)": {
        "aliases": ["BLIoTLink", "BLRAT"],
        "type": "software",
        "description": "IoT数据采集与远程访问软件，配合硬件实现设备远程监控和维护",
        "use_cases": [
            "PLC远程编程与维护",
            "设备数据采集到云平台",
            "远程桌面/VPN访问",
        ],
        "target_customers": [
            "需要远程维护PLC的集成商",
            "设备制造商需要远程服务",
        ],
        "keywords": ["remote maintenance", "PLC remote access", "IoT platform", "device management", "remote desktop"],
    },
}


# ====== 客户需求匹配引擎 ======

import re

def match_products(customer_text: str, customer_industry: str = "") -> list:
    """
    根据客户描述文本，匹配最适合的BLIIOT产品
    
    返回: [(产品名, 匹配度, 匹配理由)]
    """
    text_lower = customer_text.lower()
    matches = []
    
    for family_name, family in PRODUCT_FAMILIES.items():
        score = 0
        reasons = []
        
        # 1. 关键词匹配
        for kw in family["keywords"]:
            if kw.lower() in text_lower:
                score += 2
                reasons.append(f"关键词 '{kw}' 匹配")
        
        # 2. use case 匹配
        for uc in family["use_cases"]:
            uc_words = set(uc.lower().split())
            text_words = set(text_lower.split())
            overlap = uc_words & text_words
            if len(overlap) >= 2:
                score += 1
                reasons.append(f"用例重合: {uc[:30]}")
        
        # 3. 行业匹配
        if customer_industry:
            industry_lower = customer_industry.lower()
            for tc in family["target_customers"]:
                tc_lower = tc.lower()
                if any(word in industry_lower for word in tc_lower.split() if len(word) > 4):
                    score += 1
                    reasons.append(f"目标客户行业匹配: {tc[:30]}")
                    break
        
        # 4. 特定场景的产品推荐
        if family["type"] == "gateway" and any(w in text_lower for w in ["scada", "plc", "modbus", "protocol", "mqtt"]):
            score += 3
            reasons.append("PLC/SCADA/协议转换场景 → 推荐工业网关")
        elif family["type"] == "remote_io" and any(w in text_lower for w in ["io", "digital", "analog", "sensor", "采集", "acquisition"]):
            score += 2
            reasons.append("数据采集场景 → 推荐远程IO/RTU")
        elif family["type"] == "edge_controller" and any(w in text_lower for w in ["edge", "local", "processing", "compute", "programmable"]):
            score += 2
            reasons.append("边缘计算场景 → 推荐ARMxy边缘控制器")
        elif family["type"] == "router" and any(w in text_lower for w in ["remote site", "connectivity", "vpn", "4g", "5g", "cellular", "network"]):
            score += 2
            reasons.append("远程连接场景 → 推荐工业路由器")
        
        if score > 0:
            matches.append({
                "product": family_name,
                "type": family["type"],
                "score": min(score, 10),
                "reasons": reasons[:3],
                "description": family["description"],
            })
    
    # 按分数排序
    matches.sort(key=lambda x: x["score"], reverse=True)
    return matches


def generate_application_memo(customer_name: str, customer_desc: str, industry: str = "", matches: list = None) -> str:
    """
    生成客户应用备忘录——客户需求 × BLIIOT产品匹配
    """
    if matches is None:
        matches = match_products(customer_desc, industry)
    
    if not matches:
        return f"⚠️ 未找到 {customer_name} 的匹配产品。可能需要补充产品信息。"
    
    lines = []
    lines.append(f"{'='*60}")
    lines.append(f"📋 {customer_name} 产品匹配报告")
    lines.append(f"{'='*60}")
    lines.append(f"行业: {industry or '待确认'}")
    lines.append(f"客户描述: {customer_desc[:200]}")
    lines.append("")
    lines.append(f"🎯 推荐产品（按匹配度排序）:")
    lines.append(f"{'-'*60}")
    
    for i, m in enumerate(matches):
        stars = "⭐" * min(int(m["score"] / 2) + 1, 5)
        lines.append(f"\n[{i+1}] {m['product']} {stars} (匹配度: {m['score']}/10)")
        lines.append(f"   类型: {m['type']}")
        lines.append(f"   产品描述: {m['description'][:100]}")
        lines.append(f"   匹配理由: {'; '.join(m['reasons'][:2])}")
    
    # 组合推荐
    top_types = [m["type"] for m in matches[:3]]
    if "gateway" in top_types and "remote_io" in top_types:
        lines.append(f"\n💡 推荐组合: 工业网关 + 远程IO模块 = PLC数据采集+协议转换完整方案")
    elif "edge_controller" in top_types and "remote_io" in top_types:
        lines.append(f"\n💡 推荐组合: ARMxy边缘控制器 + IO模块 = 边缘计算+数据采集一体方案")
    elif "gateway" in top_types and "router" in top_types:
        lines.append(f"\n💡 推荐组合: 工业网关 + 4G路由器 = 远程站点数据采集+通信方案")
    
    return "\n".join(lines)


if __name__ == "__main__":
    # 测试
    test_cases = [
        ("测试PLC集成商", "We are a system integrator specializing in PLC and SCADA systems for water treatment plants. We need Modbus-to-cloud gateways and remote IO for pump monitoring stations.", "System Integration"),
        ("测试能源公司", "Energy monitoring company looking for remote data acquisition solutions for solar farms across South Africa. Need to collect inverter data and send to cloud.", "Energy / Monitoring"),
        ("测试工厂自动化", "Manufacturing plant needs edge computing device to run local analytics on production line data, with Modbus TCP connectivity to existing PLCs.", "Manufacturing"),
    ]
    
    for name, desc, industry in test_cases:
        print(generate_application_memo(name, desc, industry))
        print()