import fs from "node:fs/promises";
import path from "node:path";

const CDP_BASE = "http://127.0.0.1:9226";
const OUTPUT_DIR = "C:/Users/Admin/AppData/Local/hermes/memories/joinf-crm-edm";
const TRADE_CUSTOMER_URL = "https://trade.joinf.com/tms/customer/customers?tab=0";
const PAGE_SIZE = 1000;
const DEFAULT_SINCE = "2025-01-01";
const TZ = "Asia/Shanghai";

const sinceArg = process.argv[2] || DEFAULT_SINCE;
const sinceMs = new Date(`${sinceArg}T00:00:00+08:00`).getTime();
if (!Number.isFinite(sinceMs)) {
  throw new Error(`Invalid since date: ${sinceArg}`);
}

const formatDate = (timestamp) => {
  if (!timestamp && timestamp !== 0) {
    return "";
  }
  const date = new Date(Number(timestamp));
  if (Number.isNaN(date.getTime())) {
    return "";
  }
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone: TZ,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  })
    .formatToParts(date)
    .reduce((acc, part) => {
      acc[part.type] = part.value;
      return acc;
    }, {});
  return `${parts.year}-${parts.month}-${parts.day} ${parts.hour}:${parts.minute}:${parts.second}`;
};

const cleanText = (value) =>
  String(value ?? "")
    .replace(/\u00a0/g, " ")
    .replace(/\s+/g, " ")
    .trim();

const normalizePhone = (value) => {
  const text = cleanText(value);
  if (!text) {
    return "";
  }
  const digits = text.replace(/[^\d]/g, "");
  if (!digits) {
    return "";
  }
  return text.startsWith("+") ? `+${digits}` : text;
};

const csvEscape = (value) => `"${String(value ?? "").replace(/"/g, '""')}"`;

const toCsv = (rows) => {
  if (!rows.length) {
    return "";
  }
  const keys = Array.from(
    rows.reduce((set, row) => {
      Object.keys(row).forEach((key) => set.add(key));
      return set;
    }, new Set())
  );
  return [keys.join(","), ...rows.map((row) => keys.map((key) => csvEscape(row[key])).join(","))].join("\n");
};

class CdpPage {
  constructor(webSocketUrl) {
    this.webSocketUrl = webSocketUrl;
    this.nextId = 0;
    this.pending = new Map();
    this.ws = null;
  }

  async connect() {
    const { WebSocket } = await import("ws");
    this.ws = new WebSocket(this.webSocketUrl);
    this.ws.on("message", (data) => {
      const message = JSON.parse(data.toString());
      if (message.id && this.pending.has(message.id)) {
        const { resolve, reject } = this.pending.get(message.id);
        this.pending.delete(message.id);
        if (message.error) {
          reject(new Error(JSON.stringify(message.error)));
        } else {
          resolve(message.result);
        }
      }
    });
    await new Promise((resolve, reject) => {
      this.ws.once("open", resolve);
      this.ws.once("error", reject);
    });
  }

  send(method, params = {}) {
    return new Promise((resolve, reject) => {
      const id = ++this.nextId;
      this.pending.set(id, { resolve, reject });
      this.ws.send(JSON.stringify({ id, method, params }));
    });
  }

  async evaluate(expression, awaitPromise = false) {
    const result = await this.send("Runtime.evaluate", {
      expression,
      awaitPromise,
      returnByValue: true,
    });
    return result.result?.value;
  }

  async close() {
    if (!this.ws) {
      return;
    }
    await new Promise((resolve) => {
      this.ws.once("close", resolve);
      this.ws.close();
    });
  }
}

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

const buildScopeUrl = (scope, pageNum) => {
  if (scope === "my_customers") {
    return `https://trade.joinf.com/rapi/d/customers?num=${pageNum}&paging=true&size=${PAGE_SIZE}&sortColumn=&sortType=&isAsterisk=0`;
  }
  return `https://trade.joinf.com/rapi/d/customers/public?num=${pageNum}&paging=true&size=${PAGE_SIZE}&sortColumn=lastTransferTime&sortType=desc&source=&mainProduct=`;
};

const fetchJson = async (url) => {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Request failed: ${url} (${response.status})`);
  }
  return response.json();
};

const pickJoinfPageTarget = (targets) =>
  targets.find((target) => /trade\.joinf\.com\/tms\/customer\/customers/i.test(target.url)) ||
  targets.find((target) => /joinf\.com/i.test(target.url) && !/cloud\.joinf\.com\/login/i.test(target.url)) ||
  targets.find((target) => target.type === "page");

const enrichRows = (rows) =>
  rows.map((row) => ({
    ...row,
    display_create_time: formatDate(row.display_create_timestamp),
    display_last_transfer_time: formatDate(row.last_transfer_timestamp),
    display_last_follow_time: formatDate(row.last_follow_timestamp),
    display_next_remind_time: formatDate(row.next_remind_timestamp),
  }));

const dedupeRows = (rows) => {
  const keep = new Map();
  for (const row of rows) {
    const key =
      [row.scope, row.code, row.contact_id, row.contact_mobile, row.contact_email, row.customer_id]
        .map((part) => cleanText(part))
        .join("|") || JSON.stringify(row);
    if (!keep.has(key)) {
      keep.set(key, row);
    }
  }
  return [...keep.values()];
};

const pageFetchExpression = (url, scope, pageNum, sinceValue) => `
  (async () => {
    const normalizePhone = (value) => {
      const text = String(value ?? "").replace(/\\u00a0/g, " ").replace(/\\s+/g, " ").trim();
      if (!text) return "";
      const digits = text.replace(/[^\\d]/g, "");
      if (!digits) return "";
      return text.startsWith("+") ? "+" + digits : text;
    };
    const response = await fetch(${JSON.stringify(url)}, { credentials: "include" });
    const json = await response.json();
    const values = Array.isArray(json?.data?.values) ? json.data.values : [];
    const rows = values
      .filter((item) => Number(item.displayCreateTime || 0) >= ${sinceValue})
      .filter((item) => normalizePhone(item.contactMobile))
      .map((item) => ({
        scope: ${JSON.stringify(scope)},
        page_num: ${pageNum},
        customer_id: item.id ?? "",
        contact_id: item.contactId ?? "",
        code: item.code ?? "",
        customer_name: item.name ?? "",
        customer_short_name: item.shortName ?? "",
        contact_name: item.contactName ?? "",
        contact_nickname: item.contactNickName ?? "",
        contact_mobile: normalizePhone(item.contactMobile),
        contact_email: item.contactEmail ?? "",
        telephone: normalizePhone(item.telephone),
        website: item.webSite ?? "",
        linkedin_account: item.linkedinAccount ?? "",
        country_region: item.displayRegion ?? "",
        customer_type: item.displayType ?? "",
        customer_grade: item.grade ?? "",
        creator: item.creator ?? "",
        salesman: item.displaySalesman ?? "",
        source: item.source ?? "",
        business_type: item.businessType ?? "",
        industry_type: item.industryType ?? "",
        main_product: item.mainProduct ?? "",
        description: item.description ?? "",
        activity_type: item.activityType ?? "",
        time_zone: item.timeZone ?? "",
        public_group: item.publicGroup ?? "",
        old_department: item.oldDepartment ?? "",
        display_create_timestamp: Number(item.displayCreateTime || 0) || null,
        last_transfer_timestamp: Number(item.lastTransferTime || 0) || null,
        last_follow_timestamp: Number(item.displayLastFollowTime || 0) || null,
        next_remind_timestamp: Number(item.nextRemindTime || 0) || null
      }));
    return {
      success: !!json?.success,
      code: json?.code ?? null,
      totalPage: Number(json?.totalPage || 0),
      totalRecords: Number(json?.totalRecords || 0),
      rows
    };
  })()
`;

const run = async () => {
  await fs.mkdir(OUTPUT_DIR, { recursive: true });

  const targets = await fetchJson(`${CDP_BASE}/json/list`);
  const target = pickJoinfPageTarget(targets);
  if (!target?.webSocketDebuggerUrl) {
    throw new Error("Could not find a controllable Joinf page on 9226. Please log into Joinf in the dedicated browser first.");
  }

  const cdp = new CdpPage(target.webSocketDebuggerUrl);
  await cdp.connect();

  try {
    await cdp.send("Page.enable");
    await cdp.send("Page.navigate", { url: TRADE_CUSTOMER_URL });
    await sleep(8000);

    const current = await cdp.evaluate("location.href + ' | ' + document.title");
    if (!/trade\.joinf\.com\/tms\/customer\/customers/i.test(current)) {
      throw new Error(`Unexpected page after navigation: ${current}`);
    }

    const allRows = [];
    const scopes = ["my_customers", "public_pool"];
    const summary = [];

    for (const scope of scopes) {
      const metaUrl = buildScopeUrl(scope, 1);
      const meta = await cdp.evaluate(pageFetchExpression(metaUrl, scope, 1, sinceMs), true);
      if (!meta?.success) {
        throw new Error(`Failed to fetch scope ${scope}: ${JSON.stringify(meta)}`);
      }

      const scopeSummary = {
        scope,
        total_records: meta.totalRecords,
        total_pages: meta.totalPage,
        matched_rows_first_page: meta.rows.length,
        matched_rows_total: meta.rows.length,
      };
      summary.push(scopeSummary);
      allRows.push(...meta.rows);

      for (let pageNum = 2; pageNum <= meta.totalPage; pageNum += 1) {
        const url = buildScopeUrl(scope, pageNum);
        const pageData = await cdp.evaluate(pageFetchExpression(url, scope, pageNum, sinceMs), true);
        if (!pageData?.success) {
          throw new Error(`Failed on ${scope} page ${pageNum}: ${JSON.stringify(pageData)}`);
        }
        allRows.push(...pageData.rows);
        scopeSummary.matched_rows_total += pageData.rows.length;
      }
    }

    const uniqueRows = enrichRows(dedupeRows(allRows)).sort((a, b) => {
      const aTime = Number(a.display_create_timestamp || 0);
      const bTime = Number(b.display_create_timestamp || 0);
      return bTime - aTime;
    });

    const stamp = new Date().toISOString().slice(0, 10);
    const baseName = `joinf_customer_public_mobile_since_${sinceArg}_${stamp}`;
    const jsonPath = path.join(OUTPUT_DIR, `${baseName}.json`);
    const csvPath = path.join(OUTPUT_DIR, `${baseName}.csv`);
    const summaryPath = path.join(OUTPUT_DIR, `${baseName}_summary.json`);

    const payload = {
      exported_at: new Date().toISOString(),
      since: sinceArg,
      since_timezone: TZ,
      cdp_base: CDP_BASE,
      page_size: PAGE_SIZE,
      total_rows: uniqueRows.length,
      rows: uniqueRows,
    };

    await fs.writeFile(jsonPath, JSON.stringify(payload, null, 2), "utf8");
    await fs.writeFile(csvPath, toCsv(uniqueRows), "utf8");
    await fs.writeFile(
      summaryPath,
      JSON.stringify(
        {
          exported_at: payload.exported_at,
          since: sinceArg,
          scopes: summary,
          total_rows: uniqueRows.length,
          sample: uniqueRows.slice(0, 10),
        },
        null,
        2
      ),
      "utf8"
    );

    console.log(
      JSON.stringify(
        {
          jsonPath,
          csvPath,
          summaryPath,
          totalRows: uniqueRows.length,
          scopes: summary,
        },
        null,
        2
      )
    );
  } finally {
    await cdp.close().catch(() => {});
  }
};

run().catch((error) => {
  console.error(error.stack || String(error));
  process.exitCode = 1;
});
