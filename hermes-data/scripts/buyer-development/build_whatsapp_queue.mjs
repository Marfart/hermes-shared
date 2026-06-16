import fs from "node:fs/promises";
import path from "node:path";

const INPUT_PATH =
  process.argv[2] ||
  "C:/Users/Admin/AppData/Local/hermes/memories/buyer-development/iiot_search_enriched_2026-06-01.json";
const OUTPUT_DIR =
  process.argv[3] ||
  "C:/Users/Admin/AppData/Local/hermes/memories/buyer-development";
const OUTPUT_BASENAME =
  process.argv[4] ||
  "whatsapp_priority_queue_2026-06-01";

function uniq(values) {
  return [...new Set(values.filter(Boolean))];
}

function pickPrimaryEmail(emails) {
  return (emails || []).find((email) => /^info@/i.test(email)) || (emails || [])[0] || "";
}

function pickPrimaryLinkedIn(urls) {
  const clean = uniq(
    (urls || []).filter(
      (url) =>
        /linkedin\.com\/company\//i.test(url) &&
        !/signup|login|top-content|jobs\/|learning\/|redir\/|feed\/hashtag|similar-pages/i.test(url)
    )
  );
  return clean[0] || "";
}

function normalizePhone(phone) {
  return String(phone || "").replace(/[^\d+]/g, "");
}

function extractPhoneFromWhatsappUrl(url) {
  const text = String(url || "");
  const match = text.match(/(?:phone=|wa\.me\/)(\+?\d[\d\s-]{6,}\d)/i);
  return match ? normalizePhone(match[1]) : "";
}

function pickPrimaryWhatsappUrl(urls, fallbackNumber = "") {
  const clean = uniq(urls || [])
    .map((url) => String(url || "").trim())
    .find((url) => extractPhoneFromWhatsappUrl(url));
  if (clean) {
    const digits = extractPhoneFromWhatsappUrl(clean).replace(/[^\d]/g, "");
    return digits ? `https://wa.me/${digits}` : clean;
  }
  const fallbackDigits = normalizePhone(fallbackNumber).replace(/[^\d]/g, "");
  return fallbackDigits ? `https://wa.me/${fallbackDigits}` : "";
}

function toCsv(rows) {
  if (!rows.length) return "";
  const headers = Object.keys(rows[0]);
  const escape = (value) => `"${String(value ?? "").replace(/"/g, '""')}"`;
  return [headers.join(","), ...rows.map((row) => headers.map((h) => escape(row[h])).join(","))].join("\n");
}

const data = JSON.parse(await fs.readFile(INPUT_PATH, "utf8"));
const whatsappQueue = data
  .map((lead) => {
    const derivedNumber =
      normalizePhone(lead.whatsappNumbers?.[0] || "") ||
      extractPhoneFromWhatsappUrl((lead.whatsappUrls || [])[0] || "");
    const whatsappUrl = pickPrimaryWhatsappUrl(lead.whatsappUrls, derivedNumber);
    return {
      name: lead.name,
      country: lead.country,
      domain: lead.domain,
      whatsapp_number: derivedNumber,
      whatsapp_url: whatsappUrl,
      primary_email: pickPrimaryEmail(lead.officialEmails),
      primary_linkedin: pickPrimaryLinkedIn(lead.linkedinUrls),
      fit_score: lead.fitScore,
      inferred_need_1: lead.inferredNeeds?.[0] || "",
      inferred_need_2: lead.inferredNeeds?.[1] || "",
      recommended_product_1: lead.recommendedProducts?.[0] || "",
      recommended_product_2: lead.recommendedProducts?.[1] || "",
      source_description: lead.desc || "",
    };
  })
  .filter((lead) => Boolean(lead.whatsapp_number))
  .map((lead, index) => ({
    queue_id: index + 1,
    ...lead,
  }))
  .sort((a, b) => b.fit_score - a.fit_score);

await fs.mkdir(OUTPUT_DIR, { recursive: true });
const jsonPath = path.join(OUTPUT_DIR, `${OUTPUT_BASENAME}.json`);
const csvPath = path.join(OUTPUT_DIR, `${OUTPUT_BASENAME}.csv`);
await fs.writeFile(jsonPath, JSON.stringify(whatsappQueue, null, 2), "utf8");
await fs.writeFile(csvPath, toCsv(whatsappQueue), "utf8");

console.log(
  JSON.stringify(
    {
      count: whatsappQueue.length,
      jsonPath,
      csvPath,
      topLead: whatsappQueue[0] || null,
    },
    null,
    2
  )
);
