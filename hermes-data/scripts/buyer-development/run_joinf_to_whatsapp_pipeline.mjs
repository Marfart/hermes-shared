import { execFile } from "node:child_process";
import fs from "node:fs/promises";
import path from "node:path";
import { promisify } from "node:util";

const run = promisify(execFile);

const SCRIPTS_DIR = "C:/Users/Admin/AppData/Local/hermes/scripts/buyer-development";
const OUTPUT_DIR = "C:/Users/Admin/AppData/Local/hermes/memories/buyer-development";
const DATE_STAMP = localDateStamp();

function localDateStamp() {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

async function runNode(scriptPath, args = []) {
  const { stdout, stderr } = await run(process.execPath, [scriptPath, ...args], {
    env: {
      ...process.env,
      NODE_PATH: "C:/Users/Admin/AppData/Local/hermes/scripts/node_modules",
    },
    maxBuffer: 10 * 1024 * 1024,
  });
  return { stdout, stderr };
}

const rawBase = `joinf_business_search_results_${DATE_STAMP}`;
const enrichedBase = `joinf_business_search_enriched_${DATE_STAMP}`;
const queueBase = `joinf_whatsapp_priority_queue_${DATE_STAMP}`;
const followupBase = `joinf_customer_followup_document_${DATE_STAMP}`;
const messagesBase = `joinf_whatsapp_messages_${DATE_STAMP}`;

const fetchScript = path.join(SCRIPTS_DIR, "fetch_joinf_business_search.mjs");
const enrichScript = path.join(SCRIPTS_DIR, "enrich_joinf_business_search.mjs");
const queueScript = path.join(SCRIPTS_DIR, "build_whatsapp_queue.mjs");
const followupScript = path.join(SCRIPTS_DIR, "build_followup_document.mjs");
const renderScript = path.join(SCRIPTS_DIR, "render_whatsapp_messages.mjs");

const fetchResult = await runNode(fetchScript, [OUTPUT_DIR, rawBase, "http://127.0.0.1:9226"]);
const rawJsonPath = path.join(OUTPUT_DIR, `${rawBase}.json`);
const rawCapturePath = path.join(OUTPUT_DIR, `${rawBase}_raw.json`);

const enrichResult = await runNode(enrichScript, [rawJsonPath, OUTPUT_DIR, enrichedBase]);
const enrichedJsonPath = path.join(OUTPUT_DIR, `${enrichedBase}.json`);
const enrichedCsvPath = path.join(OUTPUT_DIR, `${enrichedBase}.csv`);

const queueResult = await runNode(queueScript, [enrichedJsonPath, OUTPUT_DIR, queueBase]);
const queueJsonPath = path.join(OUTPUT_DIR, `${queueBase}.json`);
const queueCsvPath = path.join(OUTPUT_DIR, `${queueBase}.csv`);

const followupResult = await runNode(followupScript, [enrichedJsonPath, queueJsonPath, OUTPUT_DIR, followupBase]);
const followupJsonPath = path.join(OUTPUT_DIR, `${followupBase}.json`);
const followupCsvPath = path.join(OUTPUT_DIR, `${followupBase}.csv`);

const renderResult = await runNode(renderScript, [queueJsonPath, OUTPUT_DIR, messagesBase]);
const messagesJsonPath = path.join(OUTPUT_DIR, `${messagesBase}.json`);

const queue = JSON.parse(await fs.readFile(queueJsonPath, "utf8"));
const followup = JSON.parse(await fs.readFile(followupJsonPath, "utf8"));
const messages = JSON.parse(await fs.readFile(messagesJsonPath, "utf8"));

const summary = {
  ranAt: new Date().toISOString(),
  rawCapturePath,
  rawJsonPath,
  enrichedJsonPath,
  enrichedCsvPath,
  queueJsonPath,
  queueCsvPath,
  followupJsonPath,
  followupCsvPath,
  messagesJsonPath,
  counts: {
    queue: queue.length,
    followup: followup.length,
    messages: messages.length,
  },
  samples: {
    queue: queue.slice(0, 5),
    followup: followup.slice(0, 3),
    messages: messages.slice(0, 2),
  },
  logs: {
    fetch: fetchResult.stdout.trim(),
    enrich: enrichResult.stdout.trim(),
    queue: queueResult.stdout.trim(),
    followup: followupResult.stdout.trim(),
    render: renderResult.stdout.trim(),
  },
};

const summaryPath = path.join(OUTPUT_DIR, `joinf_pipeline_run_${DATE_STAMP}.json`);
await fs.writeFile(summaryPath, JSON.stringify(summary, null, 2), "utf8");

console.log(JSON.stringify({ summaryPath, ...summary.counts }, null, 2));
