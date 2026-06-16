import fs from "node:fs/promises";
import path from "node:path";

const ENRICHED_PATH =
  process.argv[2] ||
  "C:/Users/Admin/AppData/Local/hermes/memories/buyer-development/iiot_search_enriched_2026-06-02.json";
const QUEUE_PATH =
  process.argv[3] ||
  "C:/Users/Admin/AppData/Local/hermes/memories/buyer-development/whatsapp_priority_queue_2026-06-01.json";
const OUTPUT_DIR =
  process.argv[4] ||
  "C:/Users/Admin/AppData/Local/hermes/memories/buyer-development";
const OUTPUT_BASENAME =
  process.argv[5] ||
  "customer_followup_document_2026-06-02";

function normalizeDomain(domain) {
  return String(domain || "")
    .trim()
    .toLowerCase()
    .replace(/^https?:\/\//, "")
    .replace(/^www\./, "")
    .replace(/\/.*$/, "");
}

function uniq(values) {
  return [...new Set(values.filter(Boolean))];
}

function pickPrimaryEmail(emails, fallback = "") {
  return (
    (emails || []).find((email) => /^info@/i.test(email)) ||
    (emails || []).find((email) => /^sales@/i.test(email)) ||
    (emails || [])[0] ||
    fallback
  );
}

function pickPrimaryLinkedIn(urls, fallback = "") {
  const filtered = uniq(
    (urls || []).filter(
      (url) =>
        /linkedin\.com\/company\//i.test(url) &&
        !/signup|login|top-content|jobs\/|learning\/|redir\/|feed\/hashtag|similar-pages/i.test(url)
    )
  );
  return filtered[0] || fallback;
}

function classifyIndustry(text) {
  const lower = String(text || "").toLowerCase();
  if (/plc|scada|dcs|industrial control|control systems/.test(lower)) return "SCADA / PLC / Industrial Control";
  if (/system integrator|integration|integrator/.test(lower)) return "System Integration";
  if (/energy|utility|power|bems|monitoring/.test(lower)) return "Energy / Monitoring";
  if (/manufacturing|factory|automation/.test(lower)) return "Industrial Automation / Manufacturing";
  if (/iot|iiot|edge/.test(lower)) return "IIoT / Edge Connectivity";
  return "Industrial Technology";
}

function buildWhyNeedBliiot(lead) {
  const needs = lead.inferredNeeds || [];
  const products = lead.recommendedProducts || [];
  const reasons = [];

  if (needs.some((n) => /PLC|SCADA|protocol/i.test(n))) {
    reasons.push("They may need industrial gateways for PLC/SCADA connectivity and protocol conversion.");
  }
  if (needs.some((n) => /automation gateway|edge integration|IIoT/i.test(n))) {
    reasons.push("They may need edge connectivity products to collect field data and connect devices to cloud or software platforms.");
  }
  if (needs.some((n) => /energy|utility|monitoring/i.test(n))) {
    reasons.push("They may need remote monitoring hardware for distributed equipment, utilities, or telemetry projects.");
  }
  if (!reasons.length && products.length) {
    reasons.push(`They appear relevant to ${products.slice(0, 2).join(" and ")} for industrial communication and monitoring projects.`);
  }
  if (!reasons.length) {
    reasons.push("They appear to be a relevant prospect for BLIIOT industrial connectivity and monitoring products.");
  }

  return reasons.join(" ");
}

function toCsv(rows) {
  if (!rows.length) return "";
  const headers = Object.keys(rows[0]);
  const escape = (value) => `"${String(value ?? "").replace(/"/g, '""')}"`;
  return [headers.join(","), ...rows.map((row) => headers.map((header) => escape(row[header])).join(","))].join("\n");
}

const enriched = JSON.parse(await fs.readFile(ENRICHED_PATH, "utf8"));
const queue = JSON.parse(await fs.readFile(QUEUE_PATH, "utf8"));

const enrichedByDomain = new Map(
  enriched.map((lead) => [normalizeDomain(lead.domain || lead.normalizedDomain), lead])
);
const enrichedByName = new Map(enriched.map((lead) => [String(lead.name || "").toLowerCase(), lead]));

const followupRows = queue.map((lead) => {
  const keyDomain = normalizeDomain(lead.domain);
  const source =
    enrichedByDomain.get(keyDomain) ||
    enrichedByName.get(String(lead.name || "").toLowerCase()) ||
    {};

  const whatTheyDo = source.desc || lead.source_description || "";
  const industry = classifyIndustry(`${whatTheyDo} ${lead.inferred_need_1 || ""} ${lead.inferred_need_2 || ""}`);
  const whyNeed = buildWhyNeedBliiot(source);

  return {
    company_name: lead.name || "",
    contact_name: lead.contact_name || "",
    country: lead.country || "",
    linkedin_website: pickPrimaryLinkedIn(source.linkedinUrls, lead.primary_linkedin || ""),
    email: pickPrimaryEmail(source.officialEmails, lead.primary_email || ""),
    phone: source.phone || "",
    whatsapp: lead.whatsapp_number || (source.whatsappNumbers || [])[0] || "",
    website: lead.domain ? `https://${normalizeDomain(lead.domain)}` : "",
    industry,
    What_they_do: whatTheyDo,
    Why_they_need_BLIIOT: whyNeed,
  };
});

await fs.mkdir(OUTPUT_DIR, { recursive: true });
const jsonPath = path.join(OUTPUT_DIR, `${OUTPUT_BASENAME}.json`);
const csvPath = path.join(OUTPUT_DIR, `${OUTPUT_BASENAME}.csv`);
await fs.writeFile(jsonPath, JSON.stringify(followupRows, null, 2), "utf8");
await fs.writeFile(csvPath, toCsv(followupRows), "utf8");

console.log(
  JSON.stringify(
    {
      count: followupRows.length,
      jsonPath,
      csvPath,
      sample: followupRows[0] || null,
    },
    null,
    2
  )
);
