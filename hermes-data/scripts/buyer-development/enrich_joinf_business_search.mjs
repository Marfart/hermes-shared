import fs from "node:fs/promises";
import path from "node:path";

const INPUT_PATH =
  process.argv[2] ||
  `C:/Users/Admin/AppData/Local/hermes/memories/buyer-development/joinf_business_search_results_${localDateStamp()}.json`;
const OUTPUT_DIR =
  process.argv[3] ||
  "C:/Users/Admin/AppData/Local/hermes/memories/buyer-development";
const OUTPUT_BASENAME =
  process.argv[4] ||
  `joinf_business_search_enriched_${localDateStamp()}`;

const USER_AGENT =
  "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0 Safari/537.36";
const FETCH_TIMEOUT_MS = 8000;
const CONCURRENCY = 6;
const CONTACT_PATH_HINTS = ["/contact", "/contact-us", "/about", "/company", "/imprint", "/kontakt"];

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

function uniq(values) {
  return [...new Set((values || []).filter(Boolean))];
}

function stripTags(html) {
  return String(html || "")
    .replace(/<script[\s\S]*?<\/script>/gi, " ")
    .replace(/<style[\s\S]*?<\/style>/gi, " ")
    .replace(/<[^>]+>/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function absoluteUrl(base, href) {
  try {
    return new URL(href, base).toString();
  } catch {
    return null;
  }
}

function cleanText(value) {
  return String(value || "")
    .replace(/<[^>]+>/g, " ")
    .replace(/\u00a0/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

async function fetchText(url) {
  const response = await fetch(url, {
    signal: AbortSignal.timeout(FETCH_TIMEOUT_MS),
    headers: { "user-agent": USER_AGENT },
    redirect: "follow",
  });
  if (!response.ok) {
    throw new Error(`${response.status} ${response.statusText}`);
  }
  return {
    url: response.url,
    text: await response.text(),
  };
}

async function fetchSitePages(domain) {
  if (!domain) {
    return { pages: [], fetchedUrls: [] };
  }
  const attempts = [`https://${domain}`, `http://${domain}`];
  let homepage = null;
  for (const url of attempts) {
    try {
      homepage = await fetchText(url);
      break;
    } catch {
      continue;
    }
  }
  if (!homepage) {
    return { pages: [], fetchedUrls: [] };
  }

  const fetchedUrls = [homepage.url];
  const pages = [{ url: homepage.url, html: homepage.text }];
  const linkMatches = [...homepage.text.matchAll(/href\s*=\s*["']([^"'#]+)["']/gi)];
  const candidates = uniq(
    linkMatches
      .map((match) => absoluteUrl(homepage.url, match[1]))
      .filter((url) => url && CONTACT_PATH_HINTS.some((hint) => url.toLowerCase().includes(hint)))
  ).slice(0, 2);

  for (const url of candidates) {
    try {
      const page = await fetchText(url);
      pages.push({ url: page.url, html: page.text });
      fetchedUrls.push(page.url);
    } catch {
      continue;
    }
  }

  return { pages, fetchedUrls };
}

function extractEmails(text) {
  const matches = String(text || "").match(/[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/gi) || [];
  return uniq(matches.map((item) => item.toLowerCase())).filter(
    (email) => !email.endsWith(".png") && !email.includes("example.com")
  );
}

function extractLinkedIn(text, baseUrl) {
  const direct = [...String(text || "").matchAll(/https?:\/\/(?:[\w-]+\.)?linkedin\.com\/[^\s"'<>]+/gi)].map((m) => m[0]);
  const hrefs = [...String(text || "").matchAll(/href\s*=\s*["']([^"']*linkedin\.com\/[^"']+)["']/gi)].map((m) =>
    absoluteUrl(baseUrl, m[1])
  );
  return uniq([...direct, ...hrefs]).map((url) => url?.replace(/[),.;]+$/, "")).filter(Boolean);
}

function extractWhatsapp(text, baseUrl) {
  const direct = [
    ...String(text || "").matchAll(
      /https?:\/\/(?:wa\.me|api\.whatsapp\.com|chat\.whatsapp\.com|web\.whatsapp\.com|whatsapp\.com\/send)[^\s"'<>]*/gi
    ),
  ].map((m) => m[0]);
  const hrefs = [...String(text || "").matchAll(/href\s*=\s*["']([^"']*(?:wa\.me|whatsapp\.com|api\.whatsapp\.com)[^"']*)["']/gi)].map(
    (m) => absoluteUrl(baseUrl, m[1])
  );
  const urls = uniq([...direct, ...hrefs]).map((url) => url?.replace(/[),.;]+$/, "")).filter(Boolean);
  const numbers = uniq(
    urls
      .map((url) => {
        const phoneMatch = url.match(/(?:phone=|send\/|wa\.me\/)(\+?\d[\d-]{6,}\d)/i);
        return phoneMatch ? `+${phoneMatch[1].replace(/[^\d]/g, "")}` : "";
      })
      .filter(Boolean)
  );
  return { urls, numbers };
}

function socialUrlsByType(lead, type) {
  return (lead.socialProfiles || [])
    .filter((item) => Number(item.type) === type)
    .map((item) => item.url)
    .filter(Boolean);
}

function inferNeeds(text) {
  const lower = String(text || "").toLowerCase();
  const needs = [];
  if (/plc|scada|dcs|protocol|modbus|opc/.test(lower)) {
    needs.push("PLC/SCADA connectivity and industrial protocol conversion");
  }
  if (/system integrator|integration|integrator/.test(lower)) {
    needs.push("system integration and industrial device networking");
  }
  if (/building automation|hvac|bms|bacnet/.test(lower)) {
    needs.push("building automation and HVAC connectivity");
  }
  if (/energy|power|utility|substation|renewable/.test(lower)) {
    needs.push("energy monitoring and utility equipment communication");
  }
  if (/iiot|iot|remote monitoring|telemetry|edge/.test(lower)) {
    needs.push("IIoT edge integration and remote monitoring");
  }
  if (!needs.length) {
    needs.push("industrial automation and field connectivity");
  }
  return uniq(needs).slice(0, 3);
}

function recommendProducts(text) {
  const lower = String(text || "").toLowerCase();
  const products = [];
  if (/building automation|hvac|bms|bacnet/.test(lower)) {
    products.push("BA building automation gateways");
  }
  if (/plc|scada|protocol|modbus|opc|integration/.test(lower)) {
    products.push("industrial gateways and routers");
  }
  if (/edge|controller|control/.test(lower)) {
    products.push("ARM edge controllers");
  }
  if (/energy|power|remote monitoring|telemetry|utility|monitoring/.test(lower)) {
    products.push("remote I/O and data acquisition devices");
  }
  if (!products.length) {
    products.push("industrial gateways and routers");
  }
  return uniq(products).slice(0, 3);
}

function computeFitScore(lead, inferredNeeds, assets) {
  let score = 4;
  score += Math.min(2.5, (lead.emailCount || 0) / 20);
  score += Math.min(1.5, (lead.contactTotal || 0) / 40);
  score += Math.min(1, Number(lead.star || 0) / 5);
  score += inferredNeeds.length * 0.9;
  if (assets.whatsappNumbers.length || assets.whatsappUrls.length) score += 2.8;
  if (assets.officialEmails.length) score += 1.2;
  if (assets.linkedinUrls.length) score += 0.6;
  if (/building automation|scada|system integrator|remote monitoring/i.test(lead.source_keyword || "")) score += 0.7;
  return Number(Math.min(9.9, score).toFixed(1));
}

function pickBestDescription(lead, pages) {
  const metaMatches = pages
    .map((page) => page.html.match(/<meta[^>]+name=["']description["'][^>]+content=["']([^"']+)["']/i)?.[1] || "")
    .filter(Boolean);
  return cleanText(metaMatches[0] || lead.desc || lead.mainBusiness || lead.reasons?.join(" ") || "");
}

function toCsv(rows) {
  if (!rows.length) return "";
  const headers = Object.keys(rows[0]);
  const escape = (value) => {
    const text = Array.isArray(value) ? value.join(" | ") : String(value ?? "");
    return `"${text.replace(/"/g, '""')}"`;
  };
  return [headers.join(","), ...rows.map((row) => headers.map((header) => escape(row[header])).join(","))].join("\n");
}

async function mapWithConcurrency(items, worker, limit) {
  const results = new Array(items.length);
  let index = 0;
  async function run() {
    while (true) {
      const current = index;
      index += 1;
      if (current >= items.length) return;
      results[current] = await worker(items[current], current);
    }
  }
  await Promise.all(Array.from({ length: Math.min(limit, items.length) }, () => run()));
  return results;
}

const rawLeads = JSON.parse(await fs.readFile(INPUT_PATH, "utf8"));

async function enrichLead(lead) {
  const domain = normalizeDomain(lead.domain || lead.website);
  const site = await fetchSitePages(domain).catch(() => ({ pages: [], fetchedUrls: [] }));
  const htmlPool = site.pages.map((page) => page.html).join("\n");
  const textPool = site.pages.map((page) => stripTags(page.html)).join("\n");

  const crawledEmails = extractEmails(htmlPool);
  const linkedins = uniq([
    ...socialUrlsByType(lead, 3),
    ...site.pages.flatMap((page) => extractLinkedIn(page.html, page.url)),
  ]);
  const whatsapp = site.pages.reduce(
    (acc, page) => {
      const found = extractWhatsapp(page.html, page.url);
      return {
        urls: uniq([...acc.urls, ...found.urls]),
        numbers: uniq([...acc.numbers, ...found.numbers]),
      };
    },
    { urls: [], numbers: [] }
  );

  const description = pickBestDescription(lead, site.pages);
  const inferredNeeds = inferNeeds(
    [
      lead.source_keyword,
      lead.desc,
      lead.mainBusiness,
      lead.keywordHints,
      (lead.industryList || []).join(" "),
      textPool,
    ]
      .filter(Boolean)
      .join("\n")
  );
  const recommendedProducts = recommendProducts(
    [lead.source_keyword, description, inferredNeeds.join(" "), textPool].join("\n")
  );
  const assets = {
    officialEmails: uniq(crawledEmails),
    linkedinUrls: linkedins,
    whatsappUrls: whatsapp.urls,
    whatsappNumbers: whatsapp.numbers,
  };

  return {
    source: "joinf_business_search",
    name: lead.name,
    country: lead.country,
    domain,
    sourceKeyword: lead.source_keyword,
    emailCount: lead.emailCount,
    contactTotal: lead.contactTotal,
    star: lead.star,
    desc: description,
    joinfDescription: lead.desc,
    mainBusiness: lead.mainBusiness,
    keywordHints: lead.keywordHints,
    industryList: lead.industryList || [],
    officialEmails: assets.officialEmails,
    linkedinUrls: assets.linkedinUrls,
    whatsappUrls: assets.whatsappUrls,
    whatsappNumbers: assets.whatsappNumbers,
    fetchedUrls: site.fetchedUrls,
    inferredNeeds,
    recommendedProducts,
    fitScore: computeFitScore(lead, inferredNeeds, assets),
  };
}

const enriched = await mapWithConcurrency(rawLeads, enrichLead, CONCURRENCY);
enriched.sort((a, b) => {
  const aWhatsapp = (a.whatsappUrls?.length || 0) + (a.whatsappNumbers?.length || 0);
  const bWhatsapp = (b.whatsappUrls?.length || 0) + (b.whatsappNumbers?.length || 0);
  if (bWhatsapp !== aWhatsapp) return bWhatsapp - aWhatsapp;
  return (b.fitScore || 0) - (a.fitScore || 0);
});

await fs.mkdir(OUTPUT_DIR, { recursive: true });
const jsonPath = path.join(OUTPUT_DIR, `${OUTPUT_BASENAME}.json`);
const csvPath = path.join(OUTPUT_DIR, `${OUTPUT_BASENAME}.csv`);
await fs.writeFile(jsonPath, JSON.stringify(enriched, null, 2), "utf8");
await fs.writeFile(
  csvPath,
  toCsv(
    enriched.map((lead) => ({
      name: lead.name,
      country: lead.country,
      domain: lead.domain,
      source_keyword: lead.sourceKeyword,
      official_emails: lead.officialEmails,
      linkedin_urls: lead.linkedinUrls,
      whatsapp_urls: lead.whatsappUrls,
      whatsapp_numbers: lead.whatsappNumbers,
      fit_score: lead.fitScore,
      inferred_needs: lead.inferredNeeds,
      recommended_products: lead.recommendedProducts,
    }))
  ),
  "utf8"
);

console.log(
  JSON.stringify(
    {
      count: enriched.length,
      whatsappLeadCount: enriched.filter((lead) => (lead.whatsappUrls?.length || 0) + (lead.whatsappNumbers?.length || 0) > 0).length,
      jsonPath,
      csvPath,
      topLeads: enriched.slice(0, 10).map((lead) => ({
        name: lead.name,
        domain: lead.domain,
        whatsappNumbers: lead.whatsappNumbers,
        officialEmails: lead.officialEmails,
        fitScore: lead.fitScore,
        sourceKeyword: lead.sourceKeyword,
      })),
    },
    null,
    2
  )
);
