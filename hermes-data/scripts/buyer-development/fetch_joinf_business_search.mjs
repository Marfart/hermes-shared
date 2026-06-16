import fs from "node:fs/promises";
import path from "node:path";
import { buildDebugUrl, connectOrLaunchChrome, parsePort } from "./chrome_cdp_launcher.mjs";

const OUTPUT_DIR =
  process.argv[2] ||
  "C:/Users/Admin/AppData/Local/hermes/memories/buyer-development";
const OUTPUT_BASENAME =
  process.argv[3] ||
  `joinf_business_search_results_${localDateStamp()}`;
const DEBUG_URL = process.argv[4] || "http://127.0.0.1:9226";
const DEBUG_PORT = parsePort(DEBUG_URL, 9226);

const KEYWORDS = [
  "Building Automation",
  "SCADA",
  "IIoT",
  "Remote Monitoring",
  "System Integrator",
];
const PAGES_PER_KEYWORD = 1;
const PAGE_SIZE = 20;

function localDateStamp() {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function normalizeDomain(value) {
  return String(value || "")
    .trim()
    .toLowerCase()
    .replace(/^https?:\/\//, "")
    .replace(/^www\./, "")
    .replace(/\/.*$/, "");
}

function cleanText(value) {
  return String(value || "")
    .replace(/<[^>]+>/g, " ")
    .replace(/\u00a0/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function uniq(values) {
  return [...new Set((values || []).filter(Boolean))];
}

function normalizeLead(row, keyword) {
  const snsList = Array.isArray(row?.snsList) ? row.snsList : [];
  const industryList = Array.isArray(row?.industryList)
    ? row.industryList.map((item) => cleanText(item?.industryName || item?.name || item))
    : [];

  return {
    source: "joinf_business_search",
    source_keyword: keyword,
    joinf_id: row.id || "",
    name: cleanText(row.companyName),
    country: cleanText(row.countryEn || row.country),
    country_code: cleanText(row.code),
    domain: normalizeDomain(row.website),
    website: row.website ? `https://${normalizeDomain(row.website)}` : "",
    emailCount: Number(row.emailCount || 0),
    contactTotal: Number(row.contactTotal || 0),
    star: Number(row.star || 0),
    grade: Number(row.grade || 0),
    hasWebsite: Boolean(row.hasWebsite),
    hasEmail: Boolean(row.hasEmail),
    followCount: Number(row.followCount || 0),
    desc: cleanText(row.fullOverview),
    mainBusiness: cleanText(row.mainBusiness),
    keywordHints: cleanText(row.keyword),
    industryList,
    reasons: uniq([
      cleanText(row.fullOverview),
      cleanText(row.mainBusiness),
      industryList.join(", "),
      cleanText(row.keyword),
    ]).filter(Boolean),
    socialProfiles: snsList
      .map((item) => ({
        type: Number(item?.type || 0),
        url: cleanText(item?.snsUrl || item?.url),
      }))
      .filter((item) => item.url),
    raw: row,
  };
}

function dedupeLeads(leads) {
  const map = new Map();
  for (const lead of leads) {
    const key = lead.domain || lead.name.toLowerCase();
    const existing = map.get(key);
    if (!existing) {
      map.set(key, lead);
      continue;
    }
    const existingScore =
      (existing.emailCount || 0) + (existing.contactTotal || 0) + (existing.star || 0);
    const nextScore =
      (lead.emailCount || 0) + (lead.contactTotal || 0) + (lead.star || 0);
    if (nextScore > existingScore) {
      map.set(key, lead);
      continue;
    }
    existing.source_keyword = uniq([existing.source_keyword, lead.source_keyword]).join(" | ");
    existing.reasons = uniq([...(existing.reasons || []), ...(lead.reasons || [])]);
    existing.socialProfiles = uniq([
      ...(existing.socialProfiles || []).map((item) => JSON.stringify(item)),
      ...(lead.socialProfiles || []).map((item) => JSON.stringify(item)),
    ]).map((item) => JSON.parse(item));
  }
  return [...map.values()];
}

async function main() {
  const { browser } = await connectOrLaunchChrome({
    debugPort: DEBUG_PORT,
    profileName: "joinf-maps-live",
    startUrls: [
      "https://data.joinf.com/searchResult?open=firstPage",
      "https://www.google.com/maps?hl=en",
    ],
  });
  const context = browser.contexts()[0];
  const page =
    context.pages().find((item) => /data\.joinf\.com/.test(item.url())) ||
    (await context.newPage());

  if (!/data\.joinf\.com/.test(page.url())) {
    await page.goto("https://data.joinf.com/searchResult?open=firstPage", {
      waitUntil: "domcontentloaded",
      timeout: 30000,
    });
  }

  const rawResponses = [];
  for (const keyword of KEYWORDS) {
    for (let pageNum = 1; pageNum <= PAGES_PER_KEYWORD; pageNum += 1) {
      const payload = {
        loginUserId: 786718,
        countries: [],
        etlMark: 0,
        socialMediaFlag: 0,
        labelIds: [],
        labelQueryType: 1,
        pageNum,
        pageSize: PAGE_SIZE,
        searchType: 1,
        keywords: keyword,
        multiKeywords: [keyword],
        sortField: "",
        sortType: "",
        fullMatch: 1,
        seeMore: 0,
        industries: [],
        industriesSession: [],
        excludeCountries: ["CHINA"],
      };

      const response = await page.evaluate(async (requestPayload) => {
        const res = await fetch("https://data.joinf.com/api/bs/searchBusiness", {
          method: "POST",
          credentials: "include",
          headers: {
            "content-type": "application/json;charset=UTF-8",
          },
          body: JSON.stringify(requestPayload),
        });
        return {
          status: res.status,
          json: await res.json(),
        };
      }, payload);

      rawResponses.push({
        keyword,
        pageNum,
        payload,
        status: response.status,
        response: response.json,
      });
    }
  }

  await browser.close().catch(() => {});

  const allLeads = rawResponses.flatMap((entry) =>
    (entry.response?.data?.businessListResponses || []).map((row) =>
      normalizeLead(row, entry.keyword)
    )
  );
  const deduped = dedupeLeads(allLeads);

  await fs.mkdir(OUTPUT_DIR, { recursive: true });
  const rawPath = path.join(OUTPUT_DIR, `${OUTPUT_BASENAME}_raw.json`);
  const normalizedPath = path.join(OUTPUT_DIR, `${OUTPUT_BASENAME}.json`);
  await fs.writeFile(rawPath, JSON.stringify(rawResponses, null, 2), "utf8");
  await fs.writeFile(normalizedPath, JSON.stringify(deduped, null, 2), "utf8");

  console.log(
    JSON.stringify(
      {
        debugUrl: buildDebugUrl(DEBUG_URL, 9226),
        rawPath,
        normalizedPath,
        keywordCount: KEYWORDS.length,
        rawLeadCount: allLeads.length,
        uniqueLeadCount: deduped.length,
        sample: deduped.slice(0, 5).map((lead) => ({
          name: lead.name,
          domain: lead.domain,
          country: lead.country,
          source_keyword: lead.source_keyword,
          emailCount: lead.emailCount,
          contactTotal: lead.contactTotal,
        })),
      },
      null,
      2
    )
  );
}

await main();
