import { execFile } from "node:child_process";
import { promisify } from "node:util";
import fs from "node:fs/promises";
import path from "node:path";

const execFileAsync = promisify(execFile);

const OUTPUT_DIR =
  process.argv[2] ||
  "C:/Users/Admin/AppData/Local/hermes/memories/buyer-development";
const SEED_PATH =
  process.argv[3] ||
  path.join(OUTPUT_DIR, "google_maps_seed_leads_2026-06-02.json");
const AUX_ENRICHED_PATH =
  process.argv[4] ||
  path.join(OUTPUT_DIR, "iiot_search_enriched_2026-06-02.json");

const SCRIPT_DIR = "C:/Users/Admin/AppData/Local/hermes/scripts/buyer-development";
const ENRICHED_BASE = "google_maps_enriched_2026-06-02";
const QUEUE_BASE = "google_maps_whatsapp_priority_queue_2026-06-02";
const FOLLOWUP_BASE = "google_maps_customer_followup_document_2026-06-02";
const MESSAGES_BASE = "google_maps_whatsapp_messages_2026-06-02";
const SUMMARY_PATH = path.join(OUTPUT_DIR, "google_maps_pipeline_run_2026-06-02.json");

async function runNode(scriptPath, args) {
  const { stdout, stderr } = await execFileAsync("node", [scriptPath, ...args], {
    windowsHide: true,
  });
  return {
    stdout: stdout.trim(),
    stderr: stderr.trim(),
  };
}

const enrichScript = path.join(SCRIPT_DIR, "enrich_google_maps_leads.mjs");
const queueScript = path.join(SCRIPT_DIR, "build_whatsapp_queue.mjs");
const followupScript = path.join(SCRIPT_DIR, "build_followup_document.mjs");
const renderScript = path.join(SCRIPT_DIR, "render_whatsapp_messages.mjs");

const enrichResult = await runNode(enrichScript, [SEED_PATH, AUX_ENRICHED_PATH, OUTPUT_DIR, ENRICHED_BASE]);
const enrichedJsonPath = path.join(OUTPUT_DIR, `${ENRICHED_BASE}.json`);

const queueResult = await runNode(queueScript, [enrichedJsonPath, OUTPUT_DIR, QUEUE_BASE]);
const queueJsonPath = path.join(OUTPUT_DIR, `${QUEUE_BASE}.json`);

const followupResult = await runNode(followupScript, [enrichedJsonPath, queueJsonPath, OUTPUT_DIR, FOLLOWUP_BASE]);
const followupJsonPath = path.join(OUTPUT_DIR, `${FOLLOWUP_BASE}.json`);

const messagesResult = await runNode(renderScript, [queueJsonPath, OUTPUT_DIR, MESSAGES_BASE]);
const messagesJsonPath = path.join(OUTPUT_DIR, `${MESSAGES_BASE}.json`);

const enriched = JSON.parse(await fs.readFile(enrichedJsonPath, "utf8"));
const queue = JSON.parse(await fs.readFile(queueJsonPath, "utf8"));
const followup = JSON.parse(await fs.readFile(followupJsonPath, "utf8"));
const messages = JSON.parse(await fs.readFile(messagesJsonPath, "utf8"));

const summary = {
  generated_on: "2026-06-02",
  mode: "google_maps_to_whatsapp_pipeline",
  input_files: {
    seed_path: SEED_PATH,
    aux_enriched_path: AUX_ENRICHED_PATH,
  },
  outputs: {
    enriched_json: enrichedJsonPath,
    enriched_csv: path.join(OUTPUT_DIR, `${ENRICHED_BASE}.csv`),
    queue_json: queueJsonPath,
    queue_csv: path.join(OUTPUT_DIR, `${QUEUE_BASE}.csv`),
    followup_json: followupJsonPath,
    followup_csv: path.join(OUTPUT_DIR, `${FOLLOWUP_BASE}.csv`),
    messages_json: messagesJsonPath,
  },
  counts: {
    enriched: enriched.length,
    whatsapp_queue: queue.length,
    followup: followup.length,
    messages: messages.length,
  },
  top_whatsapp_lead: queue[0] || null,
  sample_message: messages[0] || null,
  logs: {
    enrich: enrichResult,
    queue: queueResult,
    followup: followupResult,
    render: messagesResult,
  },
};

await fs.writeFile(SUMMARY_PATH, JSON.stringify(summary, null, 2), "utf8");
console.log(JSON.stringify(summary, null, 2));
