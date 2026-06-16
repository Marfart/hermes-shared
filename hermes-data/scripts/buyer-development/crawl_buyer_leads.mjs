import fs from "node:fs/promises";
import path from "node:path";

const INPUT_PATH =
  process.argv[2] ||
  "C:/Users/Admin/AppData/Local/hermes/memories/buyer-development/iiot_search_results_2026-06-01.json";
const OUTPUT_DIR =
  process.argv[3] ||
  "C:/Users/Admin/AppData/Local/hermes/memories/buyer-development";

const USER_AGENT =
  "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0 Safari/537.36";
const FETCH_TIMEOUT_MS = 8000;
const CONCURRENCY = 6;

const FIT_KEYWORDS = [
  { pattern: /\bscada\b/gi, score: 6, need: "SCADA data acquisition and protocol connectivity" },
  { pattern: /\bplc\b/gi, score: 6, need: "PLC connectivity and industrial protocol conversion" },
  { pattern: /\bdcs\b/gi, score: 6, need: "DCS remote monitoring and integration" },
  { pattern: /remote monitoring/gi, score: 5, need: "remote monitoring gateway deployment" },
  { pattern: /industrial automation/gi, score: 5, need: "automation gateway and edge integration" },
  { pattern: /smart factory/gi, score: 5, need: "smart factory data collection" },
  { pattern: /asset health|predictive maintenance/gi, score: 5, need: "asset monitoring and predictive maintenance data capture" },
  { pattern: /energy management|utility management|bems/gi, score: 5, need: "energy monitoring and building/utility management" },
  { pattern: /iiot|iot integration|industry 4\.0/gi, score: 4, need: "IIoT platform connectivity and field data access" },
  { pattern: /control panel/gi, score: 4, need: "industrial control panel networking and gateway add-ons" },
  { pattern: /edge|edge-ai|edge ai/gi, score: 4, need: "industrial edge computing hardware" },
  { pattern: /robotics|agv/gi, score: 3, need: "robotics or AGV edge control and telemetry" },
  { pattern: /cloud/gi, score: 2, need: "cloud-connected industrial data transmission" },
];

const CONTACT_PATH_HINTS = [
  "/contact",
  "/contact-us",
  "/about",
  "/company",
  "/imprint",
  "/kontakt",
];

function normalizeDomain(domain) {
  return (domain || "")
    .trim()
    .toLowerCase()
    .replace(/^https?:\/\//, "")
    .replace(/^www\./, "")
    .replace(/\/.*$/, "");
}

function uniq(values) {
  return [...new Set(values.filter(Boolean))];
}

function stripTags(html) {
  return html
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
  const attempts = [`https://${domain}`, `http://${domain}`];
  let homepage;
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
  const contactCandidates = uniq(
    linkMatches
      .map((m) => absoluteUrl(homepage.url, m[1]))
      .filter((url) => url && CONTACT_PATH_HINTS.some((hint) => url.toLowerCase().includes(hint)))
  ).slice(0, 2);

  for (const url of contactCandidates) {
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
  const matches = text.match(/[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/gi) || [];
  return uniq(matches.map((x) => x.toLowerCase())).filter(
    (email) => !email.endsWith(".png") && !email.includes("example.com")
  );
}

function extractLinkedIn(text, baseUrl) {
  const matches = [...text.matchAll(/https?:\/\/(?:[\w-]+\.)?linkedin\.com\/[^\s"'<>]+/gi)].map((m) => m[0]);
  const hrefMatches = [...text.matchAll(/href\s*=\s*["']([^"']*linkedin\.com\/[^"']+)["']/gi)].map((m) =>
    absoluteUrl(baseUrl, m[1])
  );
  return uniq([...matches, ...hrefMatches]);
}

function extractWhatsApp(text, baseUrl) {
  const direct = [
    ...text.matchAll(
      /https?:\/\/(?:wa\.me|api\.whatsapp\.com|chat\.whatsapp\.com|web\.whatsapp\.com|whatsapp\.com\/send)[^\s"'<>]*/gi
    ),
  ].map((m) => m[0]);
  const hrefMatches = [...text.matchAll(/href\s*=\s*["']([^"']*(?:wa\.me|whatsapp\.com|api\.whatsapp\.com)[^"']*)["']/gi)].map(
    (m) => absoluteUrl(baseUrl, m[1])
  );
  const normalized = uniq([...direct, ...hrefMatches]);
  const numbers = uniq(
    normalized
      .map((url) => {
        const phoneMatch = url.match(/(?:phone=|send\/|wa\.me\/)(\+?\d[\d-]{6,}\d)/i);
        return phoneMatch ? phoneMatch[1].replace(/[^\d+]/g, "") : "";
      })
      .filter(Boolean)
  );
  return { urls: normalized, numbers };
}

function inferNeeds(text) {
  const needs = [];
  let score = 0;
  for (const rule of FIT_KEYWORDS) {
    const matches = text.match(rule.pattern);
    if (matches?.length) {
      score += rule.score * matches.length;
      needs.push(rule.need);
    }
  }
  return {
    fitScore: score,
    needs: uniq(needs),
  };
}

function recommendProducts(text) {
  const lower = text.toLowerCase();
  const products = [];
  if (
    /(remote monitoring|scada|plc|dcs|iiot|cloud|modbus|mqtt|energy|utility|bems)/i.test(lower)
  ) {
    products.push("BLIIOT gateways/routers (R40, BA/BE/BL gateway series)");
  }
  if (/(edge|ai|machine vision|robotics|agv)/i.test(lower)) {
    products.push("ARMxy edge computers/controllers");
  }
  if (/(asset health|predictive maintenance|utilities|monitor|data acquisition)/i.test(lower)) {
    products.push("Remote IO / RTU / data acquisition modules");
  }
  return uniq(products);
}

function dedupeLeads(leads) {
  const map = new Map();
  for (const lead of leads) {
    const key = normalizeDomain(lead.domain) || lead.name.toLowerCase();
    const existing = map.get(key);
    if (!existing || (lead.emailCount || 0) > (existing.emailCount || 0)) {
      map.set(key, lead);
    }
  }
  return [...map.values()];
}

function toCsv(rows) {
  if (!rows.length) return "";
  const headers = Object.keys(rows[0]);
  const escape = (value) => {
    const text = Array.isArray(value) ? value.join(" | ") : String(value ?? "");
    return `"${text.replace(/"/g, '""')}"`;
  };
  return [headers.join(","), ...rows.map((row) => headers.map((h) => escape(row[h])).join(","))].join("\n");
}

const rawLeads = JSON.parse(await fs.readFile(INPUT_PATH, "utf8"));
const leads = dedupeLeads(rawLeads);
async function enrichLead(lead) {
  const domain = normalizeDomain(lead.domain);
  const combinedText = `${lead.name}\n${lead.desc}\n${lead.reasons.join(" ")}`;
  const site = domain ? await fetchSitePages(domain).catch(() => ({ pages: [], fetchedUrls: [] })) : { pages: [], fetchedUrls: [] };
  const siteText = site.pages.map((page) => stripTags(page.html)).join("\n");
  const emailPool = uniq([
    ...extractEmails(`${combinedText}\n${site.pages.map((p) => p.html).join("\n")}`),
  ]);
  const linkedinPool = uniq(
    site.pages.flatMap((page) => extractLinkedIn(page.html, page.url))
  );
  const whatsapp = site.pages.reduce(
    (acc, page) => {
      const found = extractWhatsApp(page.html, page.url);
      return {
        urls: uniq([...acc.urls, ...found.urls]),
        numbers: uniq([...acc.numbers, ...found.numbers]),
      };
    },
    { urls: [], numbers: [] }
  );
  const inferred = inferNeeds(`${combinedText}\n${siteText}`);
  const socialScore = lead.social.reduce((sum, item) => {
    if (item.type === "whatsapp") return sum + 10 * item.count;
    if (item.type === "linkedin") return sum + 2 * item.count;
    return sum + item.count;
  }, 0);
  const whatsappPriority = whatsapp.urls.length || whatsapp.numbers.length ? 40 : 0;

  return {
    ...lead,
    normalizedDomain: domain,
    officialEmails: emailPool,
    linkedinUrls: linkedinPool,
    whatsappUrls: whatsapp.urls,
    whatsappNumbers: whatsapp.numbers,
    fetchedUrls: site.fetchedUrls,
    fitScore: inferred.fitScore + socialScore + whatsappPriority + (lead.emailCount || 0),
    inferredNeeds: inferred.needs,
    recommendedProducts: recommendProducts(`${combinedText}\n${siteText}`),
  };
}

async function mapWithConcurrency(items, worker, limit) {
  const results = new Array(items.length);
  let index = 0;
  async function run() {
    while (true) {
      const current = index++;
      if (current >= items.length) return;
      results[current] = await worker(items[current], current);
    }
  }
  await Promise.all(Array.from({ length: Math.min(limit, items.length) }, () => run()));
  return results;
}

const enriched = await mapWithConcurrency(leads, enrichLead, CONCURRENCY);

enriched.sort((a, b) => {
  const aWhatsApp = a.whatsappUrls.length + a.whatsappNumbers.length;
  const bWhatsApp = b.whatsappUrls.length + b.whatsappNumbers.length;
  if (bWhatsApp !== aWhatsApp) return bWhatsApp - aWhatsApp;
  return b.fitScore - a.fitScore;
});

await fs.mkdir(OUTPUT_DIR, { recursive: true });
await fs.writeFile(
  path.join(OUTPUT_DIR, "iiot_search_enriched_2026-06-01.json"),
  JSON.stringify(enriched, null, 2),
  "utf8"
);
await fs.writeFile(
  path.join(OUTPUT_DIR, "iiot_search_enriched_2026-06-01.csv"),
  toCsv(
    enriched.map((lead) => ({
      name: lead.name,
      country: lead.country,
      domain: lead.domain,
      email_count_in_joinf: lead.emailCount,
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

const summary = {
  totalLeads: enriched.length,
  whatsappLeadCount: enriched.filter((lead) => lead.whatsappUrls.length || lead.whatsappNumbers.length).length,
  topWhatsAppLeads: enriched
    .filter((lead) => lead.whatsappUrls.length || lead.whatsappNumbers.length)
    .slice(0, 10)
    .map((lead) => ({
      name: lead.name,
      domain: lead.domain,
      whatsappUrls: lead.whatsappUrls,
      whatsappNumbers: lead.whatsappNumbers,
      officialEmails: lead.officialEmails,
      linkedinUrls: lead.linkedinUrls,
      fitScore: lead.fitScore,
    })),
};

console.log(JSON.stringify(summary, null, 2));
