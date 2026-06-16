import fs from "node:fs/promises";
import path from "node:path";

const INPUT_PATH =
  process.argv[2] ||
  "C:/Users/Admin/AppData/Local/hermes/memories/buyer-development/google_maps_seed_leads_2026-06-02.json";
const AUX_ENRICHED_PATH =
  process.argv[3] ||
  "C:/Users/Admin/AppData/Local/hermes/memories/buyer-development/iiot_search_enriched_2026-06-02.json";
const OUTPUT_DIR =
  process.argv[4] ||
  "C:/Users/Admin/AppData/Local/hermes/memories/buyer-development";
const OUTPUT_BASENAME =
  process.argv[5] ||
  "google_maps_enriched_2026-06-02";

function uniq(values) {
  return [...new Set((values || []).filter(Boolean))];
}

function normalizeName(value) {
  return String(value || "")
    .toLowerCase()
    .replace(/\(.*?\)/g, " ")
    .replace(/&/g, " and ")
    .replace(/\b(pty|ltd|limited|llc|inc|corp|company|co|sa|systems?)\b/g, " ")
    .replace(/[^a-z0-9]+/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function normalizeDomain(value) {
  return String(value || "")
    .trim()
    .toLowerCase()
    .replace(/^https?:\/\//, "")
    .replace(/^www\./, "")
    .replace(/\/.*$/, "");
}

function normalizePhone(phone) {
  const raw = String(phone || "").trim();
  if (!raw) return "";
  const digits = raw.replace(/[^\d]/g, "");
  if (!digits) return "";
  return raw.startsWith("+") ? `+${digits}` : `+${digits}`;
}

function buildWhatsappUrl(phone) {
  const digits = normalizePhone(phone).replace(/[^\d]/g, "");
  return digits ? `https://wa.me/${digits}` : "";
}

function extractEmails(text) {
  return uniq(String(text || "").match(/[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/gi) || []);
}

function extractLinkedInUrls(text) {
  return uniq(
    (String(text || "").match(/https?:\/\/(?:[\w-]+\.)?linkedin\.com\/company\/[^\s"'<>]+/gi) || []).map((url) =>
      url.replace(/[),.;]+$/, "")
    )
  );
}

function extractWhatsappUrls(text) {
  return uniq(
    (String(text || "").match(/https?:\/\/(?:api\.)?whatsapp\.com\/send\?[^\s"'<>]+|https?:\/\/wa\.me\/\d+/gi) || []).map((url) =>
      sanitizeWhatsappUrl(url.replace(/[),.;]+$/, ""))
    )
  );
}

function sanitizeWhatsappUrl(url) {
  const text = String(url || "");
  if (/wa\.me\//i.test(text)) {
    const match = text.match(/wa\.me\/(\+?\d+)/i);
    if (match) return `https://wa.me/${match[1].replace(/[^\d]/g, "")}`;
  }
  if (/whatsapp\.com\/send/i.test(text)) {
    const match = text.match(/phone=(\+?\d+)/i);
    if (match) return `https://api.whatsapp.com/send?phone=${match[1].replace(/[^\d]/g, "")}`;
  }
  return text;
}

function extractWhatsappNumbers(text) {
  const fromUrls = extractWhatsappUrls(text).map((url) => {
    const match = url.match(/(?:phone=|wa\.me\/)(\+?\d+)/i);
    return match ? normalizePhone(match[1]) : "";
  });
  const tagged = String(text || "").match(/whatsapp[:\s]*([+()0-9\s-]{7,20})/gi) || [];
  return uniq([
    ...fromUrls,
    ...tagged
      .map((chunk) => chunk.replace(/whatsapp[:\s]*/i, ""))
      .map((chunk) => normalizePhone(chunk)),
  ]);
}

function guessNeedsAndProducts(seed, description) {
  const text = `${seed.type || ""} ${seed.search_keyword || ""} ${description || ""}`.toLowerCase();
  const needs = [];
  const products = [];

  if (/plc|scada|control|automation|system integrator|machine/.test(text)) {
    needs.push("PLC/SCADA connectivity and protocol conversion");
    products.push("ARM edge controllers");
    products.push("industrial gateways and routers");
  }
  if (/iot|iiot|smartgrid|telecom|monitoring|remote/.test(text)) {
    needs.push("IIoT edge integration and remote monitoring");
    products.push("industrial gateways and routers");
  }
  if (/energy|power|grid|substation|utility/.test(text)) {
    needs.push("energy and utility equipment monitoring");
    products.push("remote I/O and data acquisition devices");
  }
  if (/building|hvac|home automation|bms|bacnet/.test(text)) {
    needs.push("building automation and HVAC integration");
    products.push("remote I/O and data acquisition devices");
  }
  if (/distribution|distributor/.test(text)) {
    needs.push("broad industrial product line sourcing");
    products.push("industrial gateways and routers");
    products.push("ARM edge controllers");
  }

  if (!needs.length) needs.push("industrial automation and field connectivity");
  if (!products.length) products.push("industrial gateways and routers");

  return {
    inferredNeeds: uniq(needs).slice(0, 3),
    recommendedProducts: uniq(products).slice(0, 3),
  };
}

function generateDescription(seed) {
  const type = seed.type || "industrial technology company";
  const country = seed.country || "its local market";
  const keyword = seed.search_keyword || "industrial automation";
  return `${seed.name} appears on Google Maps as a ${type} in ${country}. The lead was collected from a search related to ${keyword}, so the company is likely active in industrial automation, controls, integration, or adjacent engineering work.`;
}

function computeFitScore(seed, description, inferredNeeds) {
  const text = `${seed.type || ""} ${seed.search_keyword || ""} ${description || ""} ${inferredNeeds.join(" ")}`.toLowerCase();
  let score = 4.5;
  if (/system integrator|plc|scada|automation/.test(text)) score += 2;
  if (/iot|iiot|monitoring|remote|gateway/.test(text)) score += 1.5;
  if (/energy|power|building|hvac|utility/.test(text)) score += 1;
  if ((seed.rating || 0) >= 4.8) score += 0.8;
  return Math.min(9.8, Number(score.toFixed(1)));
}

async function fetchText(url) {
  if (!url) return "";
  try {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 8000);
    const res = await fetch(url, {
      headers: { "user-agent": "Mozilla/5.0" },
      redirect: "follow",
      signal: controller.signal,
    });
    clearTimeout(timer);
    if (!res.ok) return "";
    return await res.text();
  } catch {
    return "";
  }
}

async function crawlWebsite(url) {
  if (!url) {
    return {
      emails: [],
      linkedinUrls: [],
      whatsappUrls: [],
      whatsappNumbers: [],
      description: "",
    };
  }

  const targets = [url, `${url.replace(/\/$/, "")}/contact`, `${url.replace(/\/$/, "")}/contact-us`, `${url.replace(/\/$/, "")}/about`];
  const texts = [];
  for (const target of targets) {
    const text = await fetchText(target);
    if (text) texts.push(text);
  }
  const combined = texts.join("\n");
  const metaMatch = combined.match(/<meta[^>]+name=["']description["'][^>]+content=["']([^"']+)["']/i);

  return {
    emails: extractEmails(combined),
    linkedinUrls: extractLinkedInUrls(combined),
    whatsappUrls: extractWhatsappUrls(combined),
    whatsappNumbers: extractWhatsappNumbers(combined),
    description: metaMatch ? metaMatch[1].trim() : "",
  };
}

function findAuxLead(seed, auxLeads) {
  const seedName = normalizeName(seed.name);
  const exact = auxLeads.find((lead) => normalizeName(lead.name) === seedName);
  if (exact) return exact;
  return (
    auxLeads.find((lead) => {
      const auxName = normalizeName(lead.name);
      return auxName && seedName && (auxName.includes(seedName) || seedName.includes(auxName));
    }) || null
  );
}

function toCsv(rows) {
  if (!rows.length) return "";
  const headers = Object.keys(rows[0]);
  const escape = (value) => `"${String(value ?? "").replace(/"/g, '""')}"`;
  return [headers.join(","), ...rows.map((row) => headers.map((header) => escape(row[header])).join(","))].join("\n");
}

const seeds = JSON.parse(await fs.readFile(INPUT_PATH, "utf8"));
const auxLeads = JSON.parse(await fs.readFile(AUX_ENRICHED_PATH, "utf8"));

const enriched = [];
for (const seed of seeds) {
  const aux = findAuxLead(seed, auxLeads) || {};
  const website = aux.domain ? `https://${normalizeDomain(aux.domain)}` : seed.website || "";
  const crawled = await crawlWebsite(website);

  const baseDescription = aux.desc || crawled.description || generateDescription(seed);
  const computed = guessNeedsAndProducts(seed, baseDescription);
  const inferredNeeds = uniq([...(aux.inferredNeeds || []), ...computed.inferredNeeds]).slice(0, 3);
  const recommendedProducts = uniq([...(aux.recommendedProducts || []), ...computed.recommendedProducts]).slice(0, 3);
  const phone = normalizePhone(seed.phone || aux.phone || "");
  const whatsappNumbers = uniq([
    ...(aux.whatsappNumbers || []),
    ...crawled.whatsappNumbers,
    phone,
  ].map((value) => normalizePhone(value))).filter(Boolean);
  const whatsappUrls = uniq([...(aux.whatsappUrls || []), ...crawled.whatsappUrls, buildWhatsappUrl(phone)].map((value) => sanitizeWhatsappUrl(value))).filter(Boolean);
  const officialEmails = uniq([...(aux.officialEmails || []), ...crawled.emails]);
  const linkedinUrls = uniq([...(aux.linkedinUrls || []), ...crawled.linkedinUrls]);
  const fitScore = aux.fitScore || computeFitScore(seed, baseDescription, inferredNeeds);

  enriched.push({
    source: "google_maps",
    name: seed.name,
    country: seed.country,
    region: seed.country,
    rating: seed.rating || 0,
    leadType: seed.type || "",
    searchKeyword: seed.search_keyword || "",
    phone,
    domain: normalizeDomain(website || aux.domain || ""),
    officialEmails,
    linkedinUrls,
    whatsappNumbers,
    whatsappUrls,
    fitScore,
    inferredNeeds,
    recommendedProducts,
    desc: baseDescription,
    mapsNotes: `${seed.type || "Industrial lead"} from ${seed.country || "target market"} Google Maps search.`,
    website,
    hasWhatsApp: whatsappNumbers.length > 0,
  });
}

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
      rating: lead.rating,
      leadType: lead.leadType,
      phone: lead.phone,
      domain: lead.domain,
      officialEmails: (lead.officialEmails || []).join("; "),
      linkedinUrls: (lead.linkedinUrls || []).join("; "),
      whatsappNumbers: (lead.whatsappNumbers || []).join("; "),
      fitScore: lead.fitScore,
      inferredNeeds: (lead.inferredNeeds || []).join("; "),
      recommendedProducts: (lead.recommendedProducts || []).join("; "),
      desc: lead.desc,
    }))
  ),
  "utf8"
);

console.log(
  JSON.stringify(
    {
      count: enriched.length,
      jsonPath,
      csvPath,
      sample: enriched[0] || null,
    },
    null,
    2
  )
);
