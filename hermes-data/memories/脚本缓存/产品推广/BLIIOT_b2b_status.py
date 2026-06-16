#!/usr/bin/env python3
"""BLIIOT B2B Directory Status & Submission Manager"""

B2B_PLATFORMS = {
    # === 已覆盖（已确认有listing的）===
    "EC21": {"status": "exists", "url": "https://bliiot102800.en.ec21.com/", "priority": "high", "note": "已注册，有产品列表"},
    "B2BMAP": {"status": "exists", "url": "https://b2bmap.com/bliiot", "priority": "medium", "note": "已有公司页面"},
    "TradeWheel": {"status": "exists", "url": "https://www.tradewheel.com/co/bliiot-technology-917212/", "priority": "medium", "note": "已有listing"},
    "DIYTrade": {"status": "exists", "url": "https://www.diytrade.com/china/manufacturer/2990911/main/BLIIoT_Technology_Co_Ltd.html", "priority": "low", "note": "已有公司页面"},
    "WorldBid": {"status": "exists", "url": "https://www.worldbid.com/user/profile/59010", "priority": "medium", "note": "已注册"},
    "ExportHub": {"status": "exists", "url": "https://www.exporthub.com/product/bliiot-oemodm-bl200-4-20ma0-5v0-10v-analog-input-ethernet-io-module-modbus-tcp-module-24514783.html", "priority": "low", "note": "已有产品页面"},
    "Kompass": {"status": "exists", "url": "https://cn.kompass.com/p/shenzhen-beilai-technology-co-ltd/", "priority": "medium", "note": "已有页面"},
    "TradeKey": {"status": "exists", "url": "https://www.tradekey.com/", "priority": "medium", "note": "有产品listing"},
    "go4WorldBusiness": {"status": "exists", "url": "https://www.go4worldbusiness.com/", "priority": "medium", "note": "有产品listing"},
    "Hotfrog": {"status": "exists", "url": "https://www.hotfrog.com/", "priority": "low", "note": "有页面"},
    "ECeurope": {"status": "exists", "url": "https://www.eceurope.com/user/profile/29836", "priority": "low", "note": "已注册"},

    # === 待提交（最重要的空缺）===
    "DirectIndustry": {"status": "todo", "url": "https://www.directindustry.com/", "priority": "★★★★★", "note": "全球最大工业品B2B平台，必须上！"},
    "IndustryStock": {"status": "todo", "url": "https://www.industrystock.com/", "priority": "★★★★★", "note": "欧洲工业B2B，德国市场重要渠道"},
    "Europages": {"status": "todo", "url": "https://www.europages.com/", "priority": "★★★★★", "note": "欧洲最大企业目录"},
    "ThomasNet": {"status": "todo", "url": "https://www.thomasnet.com/", "priority": "★★★★☆", "note": "美国工业供应商目录"},
    "B2Brazil": {"status": "todo", "url": "https://b2brazil.com/", "priority": "★★★★☆", "note": "拉美市场重要平台"},
    "TheIndustrialMarketplace": {"status": "todo", "url": "https://www.theindustrialmarketplaceweb.com/", "priority": "★★★☆☆", "note": "美加工业目录"},
    "Applegate": {"status": "todo", "url": "https://www.applegate.com/", "priority": "★★★☆☆", "note": "英国企业目录"},

    # === 可选补充 ===
    "Indiamart": {"status": "todo", "url": "https://www.indiamart.com/", "priority": "★★★☆☆", "note": "印度最大B2B"},
    "PakBiz": {"status": "todo", "url": "https://www.pakbiz.com/", "priority": "★★☆☆☆", "note": "巴基斯坦/南亚市场"},
    "Sell123": {"status": "todo", "url": "https://www.sell123.org/", "priority": "★★☆☆☆", "note": "中东B2B平台"},
    "Kompas": {"status": "todo", "url": "https://kompas.id/", "priority": "★★☆☆☆", "note": "东南亚市场"},
}

def summary():
    exists = [k for k, v in B2B_PLATFORMS.items() if v["status"] == "exists"]
    todo = [k for k, v in B2B_PLATFORMS.items() if v["status"] == "todo"]
    print(f"✅ 已覆盖: {len(exists)} 个平台")
    for p in exists:
        print(f"   ✓ {p}")
    print(f"\n📋 待提交: {len(todo)} 个平台")
    for p in sorted(todo, key=lambda x: B2B_PLATFORMS[x]["priority"], reverse=True):
        info = B2B_PLATFORMS[p]
        print(f"   {info['priority']} {p} - {info['note']}")

if __name__ == "__main__":
    summary()