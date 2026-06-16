import fs from "node:fs/promises";
import path from "node:path";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const { chromium } = require("playwright-core");

const OUTPUT_DIR = process.argv[2] || "C:/Users/Admin/AppData/Local/hermes/memories/buyer-development";
const OUTPUT_BASENAME = process.argv[3] || `google_maps_latam_fresh_seeds_${localDateStamp()}`;
const DEBUG_URL = process.argv[4] || "http://127.0.0.1:9226";
const OLD_SEED_PATH = process.argv[5] || "C:/Users/Admin/AppData/Local/hermes/memories/buyer-development/google_maps_seed_leads_2026-06-02.json";

// Latin America focused queries - mix of English, Spanish, Portuguese
const QUERIES = [
  { query: "automação industrial São Paulo", country: "Brazil" },
  { query: "CLP SCADA Rio de Janeiro", country: "Brazil" },
  { query: "industrial automation Mexico City", country: "Mexico" },
  { query: "automatización industrial Buenos Aires", country: "Argentina" },
  { query: "system integrator Santiago Chile", country: "Chile" },
  { query: "automation control Bogotá", country: "Colombia" },
  { query: "IIoT integración industrial Lima", country: "Peru" },
  { query: "building automation Belo Horizonte", country: "Brazil" },
  { query: "SCADA Monterrey", country: "Mexico" },
  { query: "industrial control Campinas", country: "Brazil" },
];

function localDateStamp() {
  const now = new Date();
  const y = now.getFullYear();
  const m = String(now.getMonth() + 1).padStart(2, "0");
  const d = String(now.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}

function normalizeName(value) {
  return String(value || "")
    .toLowerCase()
    .replace(/\(.*?\)/g, " ")
    .replace(/&/g, " and ")
    .replace(/\b(pty|ltd|limited|llc|inc|corp|company|co|gmbh|srl|bv|sa|spa|ltda|eireli|mei)\b/g, " ")
    .replace(/[^a-z0-9]+/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function normalizePhone(phone) {
  const raw = String(phone || "").trim();
  const digits = raw.replace(/[^\d]/g, "");
  return digits ? `+${digits}` : "";
}

function uniq(values) {
  return [...new Set((values || []).filter(Boolean))];
}

function parseRating(text) {
  const match = String(text || "").match(/\b([0-5]\.\d)\b/);
  return match ? Number(match[1]) : 0;
}

async function wait(page, ms) {
  await page.waitForTimeout(ms);
}

async function collectSearchResults(page, query) {
  await page.goto(`https://www.google.com/maps/search/${encodeURIComponent(query)}?hl=en`, {
    waitUntil: "domcontentloaded",
    timeout: 60000,
  });
  await wait(page, 8000);

  return await page.evaluate(() => {
    const links = [...document.querySelectorAll('a[href*="/maps/place/"]')];
    const seen = new Set();
    const rows = [];
    for (const link of links) {
      const name = (link.getAttribute("aria-label") || "").trim();
      const href = link.href || "";
      if (!name || !href || seen.has(name)) continue;
      seen.add(name);
      rows.push({ name, placeUrl: href });
      if (rows.length >= 12) break;
    }
    return rows;
  });
}

async function extractPlaceDetails(page, candidate, fallbackCountry, query) {
  // Retry up to 2 times for flaky Google Maps place pages
  for (let attempt = 0; attempt < 3; attempt += 1) {
    try {
      const url = candidate.placeUrl.replace(/([?&])hl=[^&]+/i, "$1hl=en");
      await page.goto(url, { waitUntil: "domcontentloaded", timeout: 60000 });
      await wait(page, 7000);
      break;
    } catch {
      if (attempt >= 2) throw new Error(`Failed to load place page after 3 attempts: ${candidate.name}`);
      await wait(page, 3000);
    }
  }

  const data = await page.evaluate(() => {
    const title = document.querySelector("h1")?.textContent?.trim() ||
      document.title.replace(/\s*-\s*Google Maps\s*$/i, "").trim();
    const websiteLink =
      document.querySelector('a[data-item-id="authority"]')?.href ||
      document.querySelector('a[aria-label*="Website"]')?.href ||
      document.querySelector('a[aria-label*="Open website"]')?.href || "";
    const phoneAria =
      document.querySelector('button[data-item-id^="phone:tel:"]')?.getAttribute("aria-label") ||
      document.querySelector('a[href^="tel:"]')?.getAttribute("aria-label") ||
      document.querySelector('a[href^="tel:"]')?.getAttribute("href") || "";
    const telHref = document.querySelector('a[href^="tel:"]')?.getAttribute("href") || "";
    const addressAria =
      document.querySelector('button[data-item-id="address"]')?.getAttribute("aria-label") ||
      document.querySelector('button[data-item-id*="address"]')?.getAttribute("aria-label") || "";
    const body = document.body.innerText || "";
    return { title, websiteLink, phoneAria, telHref, addressAria, body };
  });

  const bodyLines = data.body.split("\n").map(l => l.trim()).filter(Boolean);
  const titleIndex = Math.max(0, bodyLines.indexOf(data.title));
  const snippet = bodyLines.slice(titleIndex, titleIndex + 12);
  const rating = parseRating(snippet.join(" "));
  const type = snippet[2] || snippet[3] || "";
  const phoneMatch =
    data.phoneAria.match(/\+[\d\s()\-]+/) ||
    data.telHref.match(/tel:(\+?[\d]+)/i) ||
    data.body.match(/\+55[\d\s()\-]{8,}\d/) || // Brazilian numbers
    data.body.match(/\+52[\d\s()\-]{8,}\d/) || // Mexican numbers
    data.body.match(/\+56[\d\s()\-]{8,}\d/) || // Chilean numbers
    data.body.match(/\+57[\d\s()\-]{8,}\d/) || // Colombian numbers
    data.body.match(/\+51[\d\s()\-]{8,}\d/) || // Peruvian numbers
    data.body.match(/\+54[\d\s()\-]{8,}\d/) || // Argentinian numbers
    data.body.match(/\+58[\d\s()\-]{8,}\d/) || // Venezuelan
    data.body.match(/\+[\d][\d\s()\-]{6,}\d/);
  const phone = normalizePhone(phoneMatch ? phoneMatch[0].replace(/^tel:/i, "") : "");
  const address = data.addressAria.replace(/^Address:\s*/i, "").trim() ||
    bodyLines.find(l => /\d/.test(l) && /,/.test(l)) || "";
  const countryFromAddress = address.split(",").pop()?.trim() || "";

  return {
    name: data.title || candidate.name,
    country: countryFromAddress || fallbackCountry,
    phone,
    rating,
    type,
    website: data.websiteLink || "",
    place_url: candidate.placeUrl,
    search_keyword: query,
    address,
  };
}

const oldSeeds = JSON.parse(await fs.readFile(OLD_SEED_PATH, "utf8"));
const oldNames = new Set(oldSeeds.map(s => normalizeName(s.name)));

const browser = await chromium.connectOverCDP(DEBUG_URL);
const context = browser.contexts()[0];
const page = await context.newPage();

const freshSeeds = [];
const seenNames = new Set();

for (const item of QUERIES) {
  if (freshSeeds.length >= 40) break;
  const results = await collectSearchResults(page, item.query);
  for (const candidate of results) {
    if (freshSeeds.length >= 40) break;
    const normalized = normalizeName(candidate.name);
    if (!normalized || oldNames.has(normalized) || seenNames.has(normalized)) continue;
    const detail = await extractPlaceDetails(page, candidate, item.country, item.query);
    if (!detail.phone || detail.rating < 4.0) continue;
    seenNames.add(normalized);
    freshSeeds.push(detail);
  }
}

await browser.close().catch(() => {});

await fs.mkdir(OUTPUT_DIR, { recursive: true });
const jsonPath = path.join(OUTPUT_DIR, `${OUTPUT_BASENAME}.json`);
const csvPath = path.join(OUTPUT_DIR, `${OUTPUT_BASENAME}.csv`);

function toCsv(rows) {
  if (!rows.length) return "";
  const headers = Object.keys(rows[0]);
  const escape = (value) => `"${String(value ?? "").replace(/"/g, '""')}"`;
  return [headers.join(","), ...rows.map(r => headers.map(h => escape(r[h])).join(","))].join("\n");
}

await fs.writeFile(jsonPath, JSON.stringify(freshSeeds, null, 2), "utf8");
await fs.writeFile(csvPath, toCsv(freshSeeds), "utf8");

console.log(JSON.stringify({
  jsonPath, csvPath, count: freshSeeds.length, sample: freshSeeds.slice(0, 8),
}, null, 2));