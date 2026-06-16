import fs from "node:fs/promises";
import path from "node:path";

const usage = () => {
  console.error("Usage: node normalize_customer_codes.mjs <input.json> [output.json]");
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

const groups = new Map();
for (const row of rows) {
  const code = String(row.code || row.customerCode || "").trim();
  if (!code) {
    continue;
  }
  if (!groups.has(code)) {
    groups.set(code, {
      code,
      customer_name: row.customer_name || row.customerName || "",
      salesman: row.salesman || row.displaySalesman || "",
      short_name: row.short_name || row.shortName || "",
      contacts: [],
      emails: [],
      row_count: 0,
    });
  }
  const group = groups.get(code);
  group.row_count += 1;
  const contact = row.contact || row.contactRaw || row.contactName || "";
  const email = row.email || row.contactEmail || "";
  if (contact && !group.contacts.includes(contact)) {
    group.contacts.push(contact);
  }
  if (email && !group.emails.includes(email)) {
    group.emails.push(email);
  }
  if (!group.customer_name && (row.customer_name || row.customerName)) {
    group.customer_name = row.customer_name || row.customerName || "";
  }
  if (!group.salesman && (row.salesman || row.displaySalesman)) {
    group.salesman = row.salesman || row.displaySalesman || "";
  }
  if (!group.short_name && (row.short_name || row.shortName)) {
    group.short_name = row.short_name || row.shortName || "";
  }
}

const normalized = [...groups.values()].sort((a, b) => a.code.localeCompare(b.code));
const summary = {
  input_row_count: rows.length,
  unique_customer_code_count: normalized.length,
  rows: normalized,
};

if (outputPath) {
  await fs.writeFile(outputPath, JSON.stringify(summary, null, 2), "utf8");
}

console.log(JSON.stringify(summary, null, 2));
