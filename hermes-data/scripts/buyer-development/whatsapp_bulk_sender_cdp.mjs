import fs from "node:fs/promises";
import path from "node:path";
import { connectOrLaunchChrome } from "./chrome_cdp_launcher.mjs";

const DEFAULT_QUEUE_PATH =
  "C:/Users/Admin/AppData/Local/hermes/memories/buyer-development/whatsapp_messages_2026-06-01.json";
const DEFAULT_RESULTS_DIR =
  "C:/Users/Admin/AppData/Local/hermes/memories/buyer-development";
const DEFAULT_SENT_REGISTRY_PATH = path.join(DEFAULT_RESULTS_DIR, "whatsapp_sent_registry.json");
const DEBUG_PORT = 9223;

function parseArgs(argv) {
  const options = {
    mode: "prepare",
    queuePath: DEFAULT_QUEUE_PATH,
    limit: 0,
    delayMs: 2500,
    startIndex: 0,
    visible: true,
    allowResend: false,
  };
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === "--mode") options.mode = argv[++i] || options.mode;
    else if (arg === "--queue") options.queuePath = argv[++i] || options.queuePath;
    else if (arg === "--limit") options.limit = Number(argv[++i] || 0);
    else if (arg === "--delay-ms") options.delayMs = Number(argv[++i] || options.delayMs);
    else if (arg === "--start-index") options.startIndex = Number(argv[++i] || 0);
    else if (arg === "--headless") options.visible = false;
    else if (arg === "--allow-resend") options.allowResend = true;
  }
  if (!["prepare", "send"].includes(options.mode)) {
    throw new Error(`Unsupported mode: ${options.mode}`);
  }
  return options;
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function normalizePhone(phone) {
  return String(phone || "").replace(/[^\d]/g, "");
}

function buildSendUrl(phone, message) {
  const normalizedPhone = normalizePhone(phone);
  if (!normalizedPhone) {
    throw new Error("Missing WhatsApp phone number");
  }
  return `https://web.whatsapp.com/send?phone=${normalizedPhone}&text=${encodeURIComponent(message || "")}`;
}

async function safeReadJson(filePath, fallback) {
  try {
    return JSON.parse(await fs.readFile(filePath, "utf8"));
  } catch {
    return fallback;
  }
}

async function loadSentRegistry() {
  const registry = await safeReadJson(DEFAULT_SENT_REGISTRY_PATH, {});
  const files = await fs.readdir(DEFAULT_RESULTS_DIR).catch(() => []);
  const sendFiles = files.filter(
    (name) => /^whatsapp_bulk_send_results_.*\.json$/i.test(name)
  );

  for (const fileName of sendFiles) {
    const fullPath = path.join(DEFAULT_RESULTS_DIR, fileName);
    const rows = await safeReadJson(fullPath, []);
    for (const row of rows) {
      const phone = normalizePhone(row.whatsapp_number);
      if (!phone || row.status !== "sent") continue;
      if (!registry[phone]) {
        registry[phone] = {
          phone,
          first_sent_at: null,
          last_sent_at: null,
          names: [],
          variants: [],
          files: [],
          send_count: 0,
        };
      }
      const match = fileName.match(
        /^whatsapp_bulk_send_results_(\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-\d{2})\.json$/i
      );
      const sentAt = match ? match[1] : null;
      const entry = registry[phone];
      entry.first_sent_at = entry.first_sent_at || sentAt;
      entry.last_sent_at = sentAt || entry.last_sent_at;
      if (row.name && !entry.names.includes(row.name)) entry.names.push(row.name);
      if (row.variant_id && !entry.variants.includes(row.variant_id)) entry.variants.push(row.variant_id);
      if (!entry.files.includes(fileName)) entry.files.push(fileName);
      entry.send_count += 1;
    }
  }

  await fs.writeFile(DEFAULT_SENT_REGISTRY_PATH, JSON.stringify(registry, null, 2), "utf8");
  return registry;
}

async function connectBrowser() {
  const { browser } = await connectOrLaunchChrome({
    debugPort: DEBUG_PORT,
    profileName: "whatsapp-bulk",
    startUrls: ["https://web.whatsapp.com/"],
  });
  return browser;
}

async function pickPage(browser) {
  const contexts = browser.contexts();
  const context = contexts[0];
  let page = context.pages().find((p) => p.url().includes("web.whatsapp.com"));
  if (!page) {
    page = await context.newPage();
    await page.goto("https://web.whatsapp.com/");
  }
  await page.bringToFront();
  return page;
}

async function ensureLoggedIn(page) {
  await page.waitForLoadState("domcontentloaded");
  const text = await page.locator("body").innerText({ timeout: 10000 }).catch(() => "");
  const needsLogin =
    /链接设备|link with phone number|use whatsapp on your computer|扫码|qr code|保持手机联网/i.test(text);
  if (needsLogin) {
    throw new Error("WhatsApp Web is not logged in for the Chrome profile yet");
  }
  return text;
}

async function waitForComposer(page) {
  const sendButton = page.locator('button[aria-label="发送"], button[aria-label="Send"]');
  const composer = page.locator('footer [contenteditable="true"], div[contenteditable="true"][role="textbox"]').last();
  try {
    await composer.waitFor({ state: "visible", timeout: 8000 });
    return { composerReady: true, sendReady: await sendButton.count().catch(() => 0) > 0 };
  } catch {
    await sendButton.first().waitFor({ state: "visible", timeout: 12000 });
    return { composerReady: false, sendReady: true };
  }
}

async function clickSend(page) {
  const sendCandidates = [
    page.getByRole("button", { name: "发送", exact: true }),
    page.getByRole("button", { name: "Send", exact: true }),
    page.locator('span[data-icon="send"]').locator(".."),
    page.locator('button[aria-label="发送"]'),
    page.locator('button[aria-label="Send"]'),
  ];
  for (const locator of sendCandidates) {
    try {
      const count = await locator.count();
      if (count > 0) {
        await locator.first().click({ timeout: 5000 });
        return true;
      }
    } catch {
      continue;
    }
  }
  await page.keyboard.press("Enter");
  return true;
}

async function openPreparedChat(page, lead) {
  const url = buildSendUrl(lead.whatsapp_number, lead.message);
  await page.goto(url, { waitUntil: "domcontentloaded", timeout: 30000 });
  await waitForComposer(page);
  return url;
}

async function run() {
  const options = parseArgs(process.argv.slice(2));
  const raw = JSON.parse(await fs.readFile(options.queuePath, "utf8"));
  const queue = raw.slice(options.startIndex, options.limit ? options.startIndex + options.limit : undefined);
  const sentRegistry = await loadSentRegistry();
  const browser = await connectBrowser();
  try {
    const page = await pickPage(browser);
    await ensureLoggedIn(page);

    const results = [];
    for (const lead of queue) {
      const normalizedPhone = normalizePhone(lead.whatsapp_number);
      const item = {
        queue_id: lead.queue_id,
        name: lead.name,
        whatsapp_number: lead.whatsapp_number,
        style_id: lead.style_id || "",
        variant_id: lead.variant_id || "",
        mode: options.mode,
        status: "pending",
      };
      if (!options.allowResend && normalizedPhone && sentRegistry[normalizedPhone]) {
        item.status = "skipped_already_sent";
        item.previous_send = sentRegistry[normalizedPhone];
        results.push(item);
        continue;
      }
      try {
        item.opened_url = await openPreparedChat(page, lead);
        await sleep(1500);
        if (options.mode === "send") {
          await clickSend(page);
          item.status = "sent";
          if (normalizedPhone) {
            sentRegistry[normalizedPhone] = {
              phone: normalizedPhone,
              first_sent_at: sentRegistry[normalizedPhone]?.first_sent_at || new Date().toISOString(),
              last_sent_at: new Date().toISOString(),
              names: [...new Set([...(sentRegistry[normalizedPhone]?.names || []), lead.name].filter(Boolean))],
              variants: [...new Set([...(sentRegistry[normalizedPhone]?.variants || []), lead.variant_id].filter(Boolean))],
              files: [...new Set([...(sentRegistry[normalizedPhone]?.files || [])])],
              send_count: Number(sentRegistry[normalizedPhone]?.send_count || 0) + 1,
            };
          }
        } else {
          item.status = "prepared";
        }
        await sleep(options.delayMs);
      } catch (error) {
        item.status = "error";
        item.error = error instanceof Error ? error.message : String(error);
      }
      results.push(item);
    }

    await fs.mkdir(DEFAULT_RESULTS_DIR, { recursive: true });
    const outPath = path.join(
      DEFAULT_RESULTS_DIR,
      `whatsapp_bulk_${options.mode}_results_${new Date().toISOString().slice(0, 19).replace(/[:T]/g, "-")}.json`
    );
    await fs.writeFile(outPath, JSON.stringify(results, null, 2), "utf8");
    for (const phone of Object.keys(sentRegistry)) {
      if (!sentRegistry[phone].files.includes(path.basename(outPath)) && results.some((row) => normalizePhone(row.whatsapp_number) === phone && row.status === "sent")) {
        sentRegistry[phone].files.push(path.basename(outPath));
      }
    }
    await fs.writeFile(DEFAULT_SENT_REGISTRY_PATH, JSON.stringify(sentRegistry, null, 2), "utf8");

    console.log(
      JSON.stringify(
        {
          mode: options.mode,
          processed: results.length,
          dedupe_enabled: !options.allowResend,
          sent_registry_path: DEFAULT_SENT_REGISTRY_PATH,
          outPath,
          results,
        },
        null,
        2
      )
    );
  } finally {
    try {
      await browser.close();
    } catch {
      // Ignore cleanup errors from a remote browser session.
    }
  }
}

run().catch((error) => {
  console.error(
    JSON.stringify(
      {
        error: error instanceof Error ? error.message : String(error),
      },
      null,
      2
    )
  );
  process.exit(1);
});
