import fs from "node:fs/promises";
import path from "node:path";

const INPUT_PATH = process.argv[2] || "";
const OUTPUT_DIR =
  process.argv[3] ||
  "C:/Users/Admin/AppData/Local/hermes/memories/joinf-crm-edm";
const OUTPUT_BASENAME =
  process.argv[4] ||
  "joinf_customer_document";

if (!INPUT_PATH) {
  console.error("Usage: node build_joinf_customer_document.mjs <input-json> [output-dir] [basename]");
  process.exit(1);
}

function cleanText(value) {
  return String(value || "")
    .replace(/\u00a0/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function normalizePhone(value) {
  const text = cleanText(value);
  if (!text) return "";
  const digits = text.replace(/[^\d]/g, "");
  if (!digits) return "";
  return text.startsWith("+") ? `+${digits}` : text;
}

function pickFirst(...values) {
  return values.map((value) => cleanText(value)).find(Boolean) || "";
}

function toCsv(rows) {
  if (!rows.length) return "";
  const headers = Object.keys(rows[0]);
  const escape = (value) => `"${String(value ?? "").replace(/"/g, '""')}"`;
  return [headers.join(","), ...rows.map((row) => headers.map((header) => escape(row[header])).join(","))].join("\n");
}

function normalizeFromApiRow(row) {
  return {
    code: pickFirst(row.code),
    company_name: pickFirst(row.company_name, row.name),
    contact_name: pickFirst(row.contact_name),
    country: pickFirst(row.country),
    linkedin_website: pickFirst(row.linkedin_website),
    email: pickFirst(row.email),
    phone: normalizePhone(row.phone),
    whatsapp: normalizePhone(row.whatsapp),
    website: pickFirst(row.website),
    creator: pickFirst(row.creator),
    salesperson: pickFirst(row.salesperson),
    customer_level: pickFirst(row.customer_level),
    last_transfer_time: pickFirst(row.last_transfer_time),
    last_follow_time: pickFirst(row.last_follow_time),
    note: pickFirst(row.note),
    What_they_do: pickFirst(row.What_they_do),
  };
}

function normalizeFromCrmExportRow(row) {
  const labels = row._labels || {};
  const get = (...keys) => keys.map((key) => cleanText(labels[key] || row[key])).find(Boolean) || "";
  return {
    code: get("客户代码", "瀹㈡埛浠ｇ爜", "code"),
    company_name: get("客户名称", "瀹㈡埛鍚嶇О", "name"),
    contact_name: get("联系人名称", "联系人", "鑱旂郴浜", "contactName"),
    country: get("国家", "鍥藉", "country"),
    linkedin_website: get("LinkedIn", "linkedin_website", "linkedin"),
    email: get("联系人邮箱", "鑱旂郴浜洪偖绠", "contactEmail"),
    phone: normalizePhone(get("联系电话", "手机", "phone", "contactPhone")),
    whatsapp: normalizePhone(get("WhatsApp", "whatsapp")),
    website: get("官网", "website"),
    creator: get("创建人", "鍒涘缓浜", "creator"),
    salesperson: get("业务员", "涓氬姟鍛", "salesperson"),
    customer_level: get("客户等级", "瀹㈡埛绛夌骇", "customerLevel"),
    last_transfer_time: get("最近移交时间", "鏈€杩戠Щ浜ゆ椂闂", "lastTransferTime"),
    last_follow_time: get("最近跟进时间", "鏈€杩戣窡杩涙椂闂", "lastFollowTime"),
    note: get("备注", "澶囨敞", "remark"),
    What_they_do: get("公司简介", "description"),
  };
}

const raw = JSON.parse(await fs.readFile(INPUT_PATH, "utf8"));
let rows = [];

if (Array.isArray(raw.rows) && raw.rows.length && "company_name" in raw.rows[0]) {
  rows = raw.rows.map(normalizeFromApiRow);
} else if (Array.isArray(raw.rows)) {
  rows = raw.rows.map(normalizeFromCrmExportRow);
} else if (Array.isArray(raw)) {
  rows = raw.map((row) =>
    "company_name" in row || "code" in row
      ? normalizeFromApiRow(row)
      : normalizeFromCrmExportRow(row)
  );
} else {
  throw new Error("Unsupported input format for Joinf customer document.");
}

rows = rows.filter((row) => row.company_name || row.code || row.email || row.phone);

await fs.mkdir(OUTPUT_DIR, { recursive: true });
const jsonPath = path.join(OUTPUT_DIR, `${OUTPUT_BASENAME}.json`);
const csvPath = path.join(OUTPUT_DIR, `${OUTPUT_BASENAME}.csv`);
await fs.writeFile(
  jsonPath,
  JSON.stringify(
    {
      source: INPUT_PATH,
      generatedAt: new Date().toISOString(),
      rowCount: rows.length,
      rows,
    },
    null,
    2
  ),
  "utf8"
);
await fs.writeFile(csvPath, toCsv(rows), "utf8");

console.log(
  JSON.stringify(
    {
      count: rows.length,
      jsonPath,
      csvPath,
      sample: rows[0] || null,
    },
    null,
    2
  )
);
