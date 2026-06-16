import fs from "node:fs/promises";
import path from "node:path";

const usage = () => {
  console.error("Usage: node flag_jerry_related.mjs <crm-export.json> [output.json]");
  process.exit(1);
};

const [, , inputArg, outputArg] = process.argv;
if (!inputArg) {
  usage();
}

const inputPath = path.resolve(inputArg);
const outputPath = outputArg ? path.resolve(outputArg) : null;

const raw = await fs.readFile(inputPath, "utf8");
const payload = JSON.parse(raw);
const rows = Array.isArray(payload) ? payload : payload.rows;
if (!Array.isArray(rows)) {
  throw new Error("Unsupported JSON shape: expected an array or an object with rows.");
}

const keywords = ["jerry", "bliiot06"];
const fields = [
  "creator",
  "description",
  "activityType",
  "name",
  "customer_name",
  "customerName",
  "contactName",
  "contact",
  "contactRaw",
  "contactEmail",
  "email",
  "shortName",
  "short_name",
];

const results = [];
for (const row of rows) {
  const reasons = [];
  for (const field of fields) {
    const value = String(row[field] || "").toLowerCase();
    if (!value) {
      continue;
    }
    for (const keyword of keywords) {
      if (value.includes(keyword)) {
        reasons.push(`${field}:${keyword}`);
      }
    }
  }
  if (reasons.length) {
    results.push({
      ...row,
      _reasons: [...new Set(reasons)],
    });
  }
}

const uniqueCodes = [...new Set(results.map((row) => String(row.code || "").trim()).filter(Boolean))];
const summary = {
  input_row_count: rows.length,
  matched_row_count: results.length,
  matched_unique_code_count: uniqueCodes.length,
  matched_codes: uniqueCodes,
  rows: results,
};

if (outputPath) {
  await fs.writeFile(outputPath, JSON.stringify(summary, null, 2), "utf8");
}

console.log(JSON.stringify(summary, null, 2));
