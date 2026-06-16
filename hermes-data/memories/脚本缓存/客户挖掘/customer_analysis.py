#!/usr/bin/env python3
"""
BLIIOT 客户数据分析 + 产品匹配引擎
===============================
读取已有客户数据 → 产品匹配引擎 → 输出结构化分析报告 + 应用备忘录

用法:
  python customer_analysis.py enriched_data.json
  python customer_analysis.py enriched_data.json --output report.json
  python customer_analysis.py enriched_data.json --top 5
"""

import json
import os
import sys
import re
from datetime import datetime

# ====== 导入产品知识库（直接嵌入避免路径问题）======

PRODUCT_FAMILIES = {
    "Industrial Gateways (BL116/BL118/BE116/BA116)": {
        "type": "gateway",
        "description": "工业物联网网关，支持多种PLC协议（Modbus、PROFINET、EtherNet/IP等），4G/5G/WiFi通信",
        "use_cases": [
            "PLC数据采集与云平台对接",
            "Modbus RTU/TCP转MQTT/HTTP",
            "多协议转换（Modbus/PROFINET/EtherNet/IP）",
            "Building automation / HVAC 系统集成",
        ],
        "target_customers": ["PLC/SCADA系统集成商", "工厂自动化", "楼宇自动化", "能源监控"],
        "keywords": ["modbus", "protocol", "gateway", "plc", "scada", "mqtt", "protocol converter", "modbus tcp", "profinet", "ethernet/ip"],
    },
    "ARMxy Edge Controllers": {
        "type": "edge_controller",
        "description": "基于ARM处理器的边缘控制器/计算机，支持Linux系统，可运行Node-RED、Python等",
        "use_cases": [
            "边缘计算与数据处理",
            "PLC/SCADA数据采集与协议转换",
            "设备远程监控与控制",
        ],
        "target_customers": ["系统集成商", "工厂自动化", "SCADA系统"],
        "keywords": ["edge computing", "edge controller", "arm", "embedded", "linux", "programmable", "local processing"],
    },
    "Remote IO / RTU (IOy Series)": {
        "type": "remote_io",
        "description": "多功能可编程远程IO模块，支持多种IO组合（DI/DO/AI/AO），Modbus RTU/TCP通信",
        "use_cases": [
            "远程数据采集（数字量/模拟量）",
            "SCADA系统现场数据采集",
            "能源管理与监控",
        ],
        "target_customers": ["SCADA系统集成商", "水处理/能源监控", "工厂自动化"],
        "keywords": ["remote io", "rtu", "data acquisition", "io module", "digital input", "analog input", "sensor"],
    },
    "R40 Series Routers": {
        "type": "router",
        "description": "工业4G/5G路由器，支持VPN、多WAN备份、工业级可靠性",
        "use_cases": ["远程站点网络连接", "VPN安全通信", "4G/5G蜂窝网络备份"],
        "target_customers": ["远程监控项目", "分布式站点", "石油/天然气/水务"],
        "keywords": ["router", "4g", "5g", "vpn", "cellular", "remote connectivity", "network"],
    },
    "RTU50xx Series": {
        "type": "rtu",
        "description": "远程终端单元，专为SCADA系统设计，支持多种IO和通信协议",
        "use_cases": ["SCADA远程站点数据采集", "电力/水务/油气监控", "环境监测"],
        "target_customers": ["电力系统集成商", "水务/环保监控", "SCADA系统集成"],
        "keywords": ["rtu", "scada rtu", "telemetry", "remote terminal unit"],
    },
    "Signal Isolators": {
        "type": "isolator",
        "description": "信号隔离器，用于工业信号隔离、转换和分配",
        "use_cases": ["模拟信号隔离（4-20mA/0-10V）", "温度传感器信号隔离", "开关量信号隔离"],
        "target_customers": ["工控系统集成商", "配电/电力监控", "工厂自动化"],
        "keywords": ["signal isolator", "4-20ma", "signal conditioner", "analog isolator"],
    },
    "Software (BLIoTLink / BLRAT)": {
        "type": "software",
        "description": "IoT数据采集与远程访问软件，配合硬件实现远程监控和维护",
        "use_cases": ["PLC远程编程与维护", "设备数据采集到云平台", "远程桌面/VPN访问"],
        "target_customers": ["需要远程维护PLC的集成商", "设备制造商"],
        "keywords": ["remote maintenance", "plc remote access", "device management", "remote desktop", "iot platform"],
    },
}

# 行业分类关键词
INDUSTRY_PATTERNS = {
    "SCADA / PLC / Industrial Control": ["plc", "scada", "dcs", "industrial control", "control system", "process control", "automation control"],
    "System Integration": ["system integrator", "integration", "integrator", "turnkey", "solution provider"],
    "Energy / Solar / Utility": ["energy", "utility", "power", "solar", "renewable", "wind", "grid", "substation", "electricity"],
    "Water / Wastewater": ["water", "wastewater", "treatment plant", "pump station", "water supply", "irrigation"],
    "Industrial Automation / Manufacturing": ["manufacturing", "factory", "automation", "production line", "plant", "industry 4.0"],
    "IIoT / Edge / Telecom": ["iot", "iiot", "edge computing", "smart", "telecom", "communication", "5g", "lte", "network"],
    "Oil & Gas / Mining": ["oil", "gas", "pipeline", "mining", "petroleum", "refinery", "wellhead"],
    "Building Automation": ["building", "hvac", "bems", "facility management", "smart building"],
    "Transportation": ["traffic", "transportation", "railway", "tunnel", "logistics", "fleet"],
}


def classify_industry(text):
    """从文本推断行业"""
    if not text:
        return "General Industrial"
    lower = text.lower()
    for industry, patterns in INDUSTRY_PATTERNS.items():
        if any(p in lower for p in patterns):
            return industry
    return "General Industrial"


def match_products(text, industry=""):
    """匹配客户文本到BLIIOT产品"""
    if not text:
        return []
    text_lower = text.lower()
    results = []

    for name, family in PRODUCT_FAMILIES.items():
        score = 0
        reasons = []

        for kw in family["keywords"]:
            if kw in text_lower:
                score += 2

        for uc in family["use_cases"]:
            uc_words = set(uc.lower().split())
            text_words = set(text_lower.split())
            if len(uc_words & text_words) >= 2:
                score += 1

        if industry:
            il = industry.lower()
            for tc in family["target_customers"]:
                if any(w in il for w in tc.lower().split() if len(w) > 4):
                    score += 1
                    break

        if score > 0:
            results.append({
                "product": name,
                "type": family["type"],
                "score": min(score, 10),
                "description": family["description"][:80],
            })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results


def build_why_need(products, text):
    """基于匹配结果生成为什么需要BLIIOT的描述"""
    if not products:
        return ""
    
    top_types = [p["type"] for p in products[:3]]
    
    if "gateway" in top_types and "remote_io" in top_types:
        return "They likely need industrial gateways for protocol conversion and cloud connectivity, together with remote I/O modules for field data acquisition in their automation and monitoring systems."
    elif "gateway" in top_types:
        return "They may need industrial gateways for reliable PLC/SCADA connectivity, protocol conversion, and secure data transmission to cloud or control center."
    elif "edge_controller" in top_types and "remote_io" in top_types:
        return "They may benefit from ARM edge controllers for local data processing and control, combined with remote I/O modules for flexible field signal acquisition."
    elif "edge_controller" in top_types:
        return "They may need ARM-based edge controllers for on-site data processing, protocol conversion, and intelligent device control in automation applications."
    elif "remote_io" in top_types:
        return "They likely need remote I/O and data acquisition modules for monitoring and controlling distributed field devices and sensors."
    elif "router" in top_types:
        return "They may need industrial routers for reliable remote connectivity, VPN security, and cellular network backup at distributed sites."
    elif "rtu" in top_types:
        return "They may need remote terminal units for SCADA telemetry and data acquisition at remote or unmanned stations."
    else:
        return "They appear to be a relevant prospect for BLIIOT's industrial communication, automation, and monitoring products."


def analyze_customers(data, top_n=20):
    """分析一批客户数据并生成匹配报告"""
    results = []
    stats = {"total": len(data), "matched": 0, "by_product": {}, "by_industry": {}, "by_country": {}}

    for item in data:
        # 提取关键字段（兼容不同格式）
        name = item.get("name", item.get("company", item.get("company_name", "Unknown")))
        country = item.get("country", "")
        desc = item.get("desc", item.get("description", item.get("What_they_do", "")))
        domain = item.get("domain", item.get("website", ""))
        industry = item.get("industry", "")
        
        if isinstance(desc, str) and len(desc) > 5:
            # 推断行业
            if not industry:
                industry = classify_industry(desc)
            
            # 匹配产品
            products = match_products(desc, industry)
            
            if products:
                stats["matched"] += 1
                top_product = products[0]["product"]
                stats["by_product"][top_product] = stats["by_product"].get(top_product, 0) + 1
            
            stats["by_industry"][industry] = stats["by_industry"].get(industry, 0) + 1
            if country:
                stats["by_country"][country] = stats["by_country"].get(country, 0) + 1
            
            results.append({
                "name": name,
                "country": country,
                "domain": domain,
                "industry": industry,
                "description": desc[:200],
                "recommended_products": products[:3],
                "why_bliiot": build_why_need(products, desc),
                "fit_score": products[0]["score"] if products else 0,
            })

    # 按匹配度排序
    results.sort(key=lambda x: x["fit_score"], reverse=True)
    
    return results[:top_n], stats


def generate_report(results, stats):
    """生成可读报告"""
    lines = []
    lines.append(f"{'='*65}")
    lines.append(f"📊 BLIIOT 客户数据分析报告")
    lines.append(f"   生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"{'='*65}")
    
    lines.append(f"\n📈 概览:")
    lines.append(f"   总客户数: {stats['total']}")
    lines.append(f"   匹配成功: {stats['matched']} ({stats['matched']/max(stats['total'],1)*100:.0f}%)")
    
    lines.append(f"\n🏭 按行业分布:")
    for ind, cnt in sorted(stats['by_industry'].items(), key=lambda x: x[1], reverse=True):
        bar = "█" * cnt
        lines.append(f"   {ind:40s} {cnt:3d}  {bar}")
    
    lines.append(f"\n🌍 按国家分布:")
    for cty, cnt in sorted(stats['by_country'].items(), key=lambda x: x[1], reverse=True)[:10]:
        lines.append(f"   {cty:30s} {cnt:3d}")
    
    lines.append(f"\n📦 推荐产品分布:")
    for prod, cnt in sorted(stats['by_product'].items(), key=lambda x: x[1], reverse=True):
        bar = "█" * cnt
        lines.append(f"   {prod:45s} {cnt:3d}  {bar}")
    
    lines.append(f"\n{'='*65}")
    lines.append(f"🎯 TOP {len(results)} 高匹配客户")
    lines.append(f"{'='*65}")
    
    for i, r in enumerate(results):
        lines.append(f"\n[{i+1}] {r['name']} ({r['country']}) ⭐ 匹配度: {r['fit_score']}/10")
        lines.append(f"   行业: {r['industry']}")
        if r['domain']:
            lines.append(f"   网站: {r['domain']}")
        lines.append(f"   描述: {r['description'][:120]}")
        if r['recommended_products']:
            prods = " → ".join([p['product'].split("(")[0].strip() for p in r['recommended_products'][:2]])
            lines.append(f"   🎯 推荐: {prods}")
        if r['why_bliiot']:
            lines.append(f"   💡 {r['why_bliiot'][:120]}")
    
    return "\n".join(lines)


def generate_application_memos(results):
    """为每个客户生成应用备忘录"""
    memos = []
    for r in results:
        if not r['recommended_products']:
            continue
        
        top = r['recommended_products'][0]
        app_text = f"""
📋 客户: {r['name']} ({r['country']})
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
行业: {r['industry']}
描述: {r['description'][:150]}

🎯 推荐产品: {top['product']}
   匹配度: {top['score']}/10
   产品说明: {top['description']}

💡 应用场景:
{r['why_bliiot']}

📎 跟进建议:
• 优先WhatsApp联系（WhatsApp在非洲普及率高）
• 简介BLIIOT产品线 + {top['product'].split('(')[0].strip()} 具体方案
• 询问当前使用的自动化设备和面临的问题
"""
        memos.append({"company": r['name'], "memo": app_text.strip()})
    
    return memos


def main():
    import argparse
    parser = argparse.ArgumentParser(description="BLIIOT客户数据分析引擎")
    parser.add_argument("input", help="客户JSON数据文件路径")
    parser.add_argument("--output", "-o", help="输出报告路径")
    parser.add_argument("--top", "-t", type=int, default=20, help="显示前N个客户")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input):
        print(f"❌ 文件不存在: {args.input}")
        sys.exit(1)
    
    with open(args.input) as f:
        data = json.load(f)
    
    print(f"📥 加载了 {len(data)} 条客户数据\n")
    
    results, stats = analyze_customers(data, args.top)
    
    report = generate_report(results, stats)
    print(report)
    
    if results:
        memos = generate_application_memos(results)
        print(f"\n\n{'='*65}")
        print(f"📋 产品应用备忘录 ({len(memos)}份)")
        print(f"{'='*65}")
        for m in memos[:3]:
            print(f"\n{m['memo']}")
    
    if args.output:
        output = {
            "generated_at": datetime.now().isoformat(),
            "source": args.input,
            "stats": stats,
            "top_customers": results,
            "application_memos": memos,
        }
        with open(args.output, "w") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        print(f"\n💾 完整报告已保存到: {args.output}")


if __name__ == "__main__":
    main()