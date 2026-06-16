---
name: bliiot-b2b-directory-promotion
description: BLIIOT B2B产品推广 — 向全球B2B贸易目录提交公司信息，让买家主动找到BLIIOT。不碰社交平台（LinkedIn/Reddit/X/Telegram群组），专注工业B2B目录。
category: sales
---

## BLIIOT B2B Directory Promotion

### When to use
User says: "宣传产品", "推广公司", "找B2B平台", "去xxx上发广告", "提交公司信息". Also when user mentions product promotion without specifying platform context.

### CRITICAL RULE (user preference)
**Do NOT submit to social media platforms** (LinkedIn, Reddit, X/Twitter, Telegram groups/channels, Facebook, GitHub issues/discussions, etc.). Kali explicitly banned these channels for promotion:
- LinkedIn: "要被封的"
- Reddit: "容易被封号的平台"
- Telegram: "容易封号"  
- GitHub: "不要用github发帖，待会给我封了"
- Any platform needing phone-number registration with aggressive anti-bot

Only use B2B trade directories or content-writing platforms (Medium, 知乎, CSDN, 简书).

### Registration Credentials
| Field | Value | When to use |
|-------|-------|-------------|
| **Email** | `bl42@bliiot.com` | For all account registrations |
| **Phone** | `+86 17704014518` | For SMS verification codes (Kali relays code to me) |
| **WhatsApp** | `+86 17704014518` | Put in profile/product descriptions as contact |
| **Company** | Shenzhen Beilai Technology Co., Ltd. (深圳钡铼技术) | Company name on all platforms |
| **Website** | https://www.bliiot.com | Always include |

### Registration Flow (when Kali says "用这个号注册")
1. Navigate to platform's registration page via browser tool
2. Fill email = `bl42@bliiot.com`, phone = `+86 17704014518`
3. Click "send verification code" (发验证码)
4. **Tell Kali** "验证码发到你手机了，告诉小马" — wait for them to relay
5. Enter the code and complete registration
6. Fill company profile using B2B templates

### Fallback when automated registration is blocked
If the platform has Cloudflare, anti-bot, or otherwise blocks browser attempts:
1. Try launching a CDP-connected Chrome (user's real browser profile) — bypasses Cloudflare for most sites
2. If that also fails (some sites block remote IPs regardless), provide the manual registration template text and tell Kali what to copy-paste

### BLIIOT's Current B2B Coverage (16 platforms)
Most free B2B platforms are already covered. Don't waste time on ones already listed.

**Tier 1 - Flagship Stores (already done)**
- Alibaba.com: `bare.en.alibaba.com` — 925+ products, ISO cert
- Made-in-China.com: `szbeilai.en.made-in-china.com` — product listings
- GlobalSources: products listed

**Tier 2 - Established (already done)**
- EC21, TradeKey, TradeIndia, ExportersIndia, TradeWheel, go4WorldBusiness, Kompass

**Tier 3 - Small directories (already done)**
- B2BMAP, WorldBid, ExportHub, DIYTrade, Hotfrog, ECeurope

### Platforms NOT to pursue (paywalled)
- DirectIndustry — €3000+/year (world's largest industrial B2B, but paid)
- ThomasNet —北美工业目录，付费入驻
- IndustryStock — 欧洲B2B，付费
- Europages — 欧洲目录，免费listing有限
- B2Brazil — 拉美平台，以巴西出口商为主

### Strategy Priority
1. **Enrich existing platforms** — add more products, better descriptions, photos. Highest ROI since accounts exist.
2. **Manual submission** to any truly free remaining directories using the templates at `Desktop/Working/BLIIOT_B2B_Templates.md`

### Anti-Bot Reality
Most remaining platforms have Cloudflare or custom anti-bot. Automated registration is not feasible. Provide manual templates instead.

### Templates
Ready-to-use B2B submission templates saved at:
`C:\Users\Admin\Desktop\Working\BLIIOT_B2B_Templates.md`

Includes 5 templates:
- Company Profile (About Us field)
- ARMxy Edge Controllers product listing
- IoT Gateways (BL116/BE116/BA116) product listing
- R40 Cellular Router product listing
- Trade Lead / Selling Offer

All templates include:
- WhatsApp: +86 17704014518
- Email: bl42@bliiot.com
- Website: https://www.bliiot.com
- Phone for registration: 17704014518

### Reference File
See `references/b2b-platform-coverage.md` for the full coverage report with all URLs and status notes.

## Related Skill
For **outbound customer acquisition** (Google Maps → WhatsApp outreach), see: `bliiot-customer-acquisition`