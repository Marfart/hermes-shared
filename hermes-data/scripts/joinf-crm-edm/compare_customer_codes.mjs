import fs from "node:fs/promises";
import path from "node:path";

const usage = () => {
  console.error("Usage: node compare_customer_codes.mjs <base.json> <exclude.json> [output.json]");
  process.exit(1);
};

const readJson = async (filePath) => {
  const raw = await fs.readFile(filePath, "utf8");
  return JSON.parse(raw);
};

const normalizeRows = (payload) => {
  if (Array.isArray(payload)) {
    return payload;
  }
  if (Array.isArray(payload.rows)) {
    return payload.rows;
  }
  throw new Error("Unsupported JSON shape: expected an array or an object with rows.");
};

const getCodes = (rows) =>
  new Set(
    rows
      .map((row) => row.code || row.customerCode || row.Code || "")
      .map((value) => String(value).trim())
      .filter(Boolean)
  );

const [, , baseArg, excludeArg, outputArg] = process.argv;
if (!baseArg || !excludeArg) {
  usage();
}

const basePath = path.resolve(baseArg);
const excludePath = path.resolve(excludeArg);
const outputPath = outputArg ? path.resolve(outputArg) : null;

const baseRows = normalizeRows(await readJson(basePath));
const excludeRows = normalizeRows(await readJson(excludePath));
const excludeCodes = getCodes(excludeRows);
const remainingRows = baseRows.filter((row) => {
  const code = String(row.code || row.customerCode || row.Code || "").trim();
  return code && !excludeCodes.has(code);
});

const summary = {
  baseCount: baseRows.length,
  excludeCount: excludeRows.length,
  excludeCodeCount: excludeCodes.size,
  remainingCount: remainingRows.length,
  remainingRows,
};

if (outputPath) {
  await fs.writeFile(outputPath, JSON.stringify(summary, null, 2), "utf8");
}

console.log(JSON.stringify(summary, null, 2));
