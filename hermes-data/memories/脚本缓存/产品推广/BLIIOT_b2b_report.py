#!/usr/bin/env python3
"""BLIIOT B2B Directory Comprehensive Coverage Report"""

B2B_PLATFORMS = {
    # ==================== 已覆盖 ====================
    "Alibaba.com": {"status": "✅", "url": "https://bare.en.alibaba.com/", "priority": "★★★★★", "note": "旗舰店，产品925+，ISO认证"},
    "Made-in-China.com": {"status": "✅", "url": "https://szbeilai.en.made-in-china.com/", "priority": "★★★★★", "note": "旗舰店，有产品列表"},
    "GlobalSources": {"status": "✅", "url": "https://www.globalsources.com/", "priority": "★★★★★", "note": "有产品页面"},
    "EC21": {"status": "✅", "url": "https://bliiot102800.en.ec21.com/", "priority": "★★★★☆", "note": "公司页面+产品列表"},
    "TradeKey": {"status": "✅", "url": "https://www.tradekey.com/", "priority": "★★★★☆", "note": "有产品listing"},
    "TradeIndia": {"status": "✅", "url": "https://www.tradeindia.com/", "priority": "★★★★☆", "note": "有产品页面"},
    "ExportersIndia": {"status": "✅", "url": "https://www.exportersindia.com/", "priority": "★★★☆☆", "note": "有公司页面"},
    "TradeWheel": {"status": "✅", "url": "https://www.tradewheel.com/co/bliiot-technology-917212/", "priority": "★★★☆☆", "note": "有公司页面"},
    "go4WorldBusiness": {"status": "✅", "url": "https://www.go4worldbusiness.com/", "priority": "★★★☆☆", "note": "有产品listing"},
    "Kompass": {"status": "✅", "url": "https://cn.kompass.com/p/shenzhen-beilai-technology-co-ltd/", "priority": "★★★☆☆", "note": "有公司页面"},
    "B2BMAP": {"status": "✅", "url": "https://b2bmap.com/bliiot", "priority": "★★☆☆☆", "note": "有公司页面"},
    "WorldBid": {"status": "✅", "url": "https://www.worldbid.com/user/profile/59010", "priority": "★★☆☆☆", "note": "已注册"},
    "ExportHub": {"status": "✅", "url": "https://www.exporthub.com/", "priority": "★★☆☆☆", "note": "有产品页面"},
    "DIYTrade": {"status": "✅", "url": "https://www.diytrade.com/", "priority": "★★☆☆☆", "note": "有公司页面"},
    "Hotfrog": {"status": "✅", "url": "https://www.hotfrog.com/", "priority": "★★☆☆☆", "note": "有公司页面"},
    "ECeurope": {"status": "✅", "url": "https://www.eceurope.com/user/profile/29836", "priority": "★★☆☆☆", "note": "已注册"},

    # ==================== 付费/受限 ====================
    "DirectIndustry": {"status": "💎付费", "url": "https://www.directindustry.com/", "priority": "★★★★★", "note": "全球最大工业B2B，需付费入驻（年费约€3000+）"},
    "ThomasNet": {"status": "💎付费", "url": "https://www.thomasnet.com/", "priority": "★★★★☆", "note": "北美最大工业供应商目录，付费入驻"},
    "IndustryStock": {"status": "💎付费", "url": "https://www.industrystock.com/", "priority": "★★★★☆", "note": "欧洲B2B，需付费入驻"},
    "Europages": {"status": "💎付费", "url": "https://www.europages.com/", "priority": "★★★★☆", "note": "欧洲企业目录，免费listing有限"},
    "B2Brazil": {"status": "💎付费", "url": "https://b2brazil.com/", "priority": "★★★☆☆", "note": "拉美平台，主要面向巴西出口商"},
    "Applegate": {"status": "💎受限", "url": "https://www.applegate.com/", "priority": "★★☆☆☆", "note": "英国目录，需审核"},
}

def print_report():
    print("=" * 70)
    print("  BLIIOT B2B Directory Coverage Report")
    print("=" * 70)
    
    exists = {k: v for k, v in B2B_PLATFORMS.items() if v["status"] == "✅"}
    paid = {k: v for k, v in B2B_PLATFORMS.items() if v["status"].startswith("💎")}
    
    print(f"\n✅ 已覆盖: {len(exists)} 个平台")
    print("-" * 60)
    for p in sorted(exists, key=lambda x: exists[x]["priority"], reverse=True):
        info = exists[p]
        print(f"  {info['priority']} {p}")
        print(f"     URL: {info['url']}")
        print(f"     {info['note']}")
        print()
    
    print(f"\n💎 付费/受限（建议人工评估）: {len(paid)} 个平台")
    print("-" * 60)
    for p in sorted(paid, key=lambda x: paid[x]["priority"], reverse=True):
        info = paid[p]
        print(f"  {info['priority']} {p} - {info['note']}")
    
    print()
    print("=" * 70)
    print("  结论：BLIIOT 免费B2B平台覆盖已很全面")
    print("  剩余高价值平台多为付费入驻（DirectIndustry等）")
    print("  建议策略：增强现有平台的完整度（更多产品、SEO优化）")
    print("=" * 70)

if __name__ == "__main__":
    print_report()