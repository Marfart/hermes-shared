# This is a reference placeholder. The actual build script lives at
# ~/Desktop/Working/Hermes/build_v7_final.py and is actively maintained there.
# Copy the latest version here when archiving a stable release.
# Key patterns from v7.4 (latest):
# - All content sections (hero_stories, secondary, culture, economy_stories, science_stories, fund_stories) defined as Python dicts with id/img/tag/tc/title/src/text fields
# - Card HTML generated via f-string loops (sec-card, cult-card formats)
# - Detail pages generated via separate loops with margin-top:16px paragraph spacing
# - New sections MUST use same card+detail pattern as existing sections (Bug #6)
# - Section ordering: s1=核心 s2=科研 s3=经济 s4=政治 s5=太空 s6=文化 s7=生命科学 s8=基金 s9=风险(RISK LAST!)
# - Image download priority: Playwright evaluate og:image → curl --noproxy → Python urllib → picsum semantic seed → gradient card
# - Image cache: news_b64_v7_real_optimized.json, JPEG q85, 1200px width minimum
# - ⛔ NEVER compress images below 1200px width or q85 quality for upload size — Cloudflare Tunnel has no size limit
# - ⛔ Kali explicitly rejected q35 400px compression: "图这么糊" + "对应的图也没了"
# - Total HTML: Cloudflare Tunnel has NO size limit (9MB+ tested OK). Only compress if Tunnel is unavailable.
# - Reddit URLs (cf.preview.redd.it) return 403 Forbidden — never use as image source
# - picsum IDs must use semantic seeds (e.g. seed/spacex-rocket-launch), never random numbers (e.g. id/83)
# - ⛔ MD5 dedup ALL images after building — risk_section == uk_healey was a real failure (same Unsplash URL)
# - ⛔ Wuthering Waves × Cyberpunk Edgerunners section MUST use official collab/key art image, not generic gaming image
# - Navigation bar: 🔥核心 🔬科研 📈经济 🛡️政治 🚀太空 🎨文化 🧬生命 📈基金 ⚠️风险 (risk MUST be last!)