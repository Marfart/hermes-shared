(function () {
  const cleanText = (value) =>
    String(value || "")
      .replace(/\u00a0/g, " ")
      .replace(/\s+/g, " ")
      .trim();

  const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

  const pickFieldKey = (className, fallbackIndex) => {
    const parts = String(className || "")
      .split(/\s+/)
      .filter(Boolean)
      .filter((part) => !/^w-\d+$/.test(part))
      .filter((part) => !/^cell(-is-left|-is-right)?$/.test(part))
      .filter((part) => !/^el-/.test(part))
      .filter((part) => !/^is-/.test(part))
      .filter((part) => !/^fc\d+$/.test(part))
      .filter((part) => !/^pointer$/.test(part))
      .filter((part) => !/^can-resize$/.test(part))
      .filter((part) => !/^column_/.test(part))
      .filter((part) => !/^ft-table__row-\d+$/.test(part))
      .filter((part) => !/^line_mode\d+$/.test(part))
      .filter((part) => !/^has-click$/.test(part));
    return parts[parts.length - 1] || `field_${fallbackIndex}`;
  };

  const downloadText = (filename, content, type) => {
    const blob = new Blob([content], { type });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  };

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
    const encode = (value) => {
      const text = String(value ?? "");
      return `"${text.replace(/"/g, '""')}"`;
    };
    return [keys.join(","), ...rows.map((row) => keys.map((key) => encode(row[key])).join(","))].join("\n");
  };

  const isPlainObject = (value) => Object.prototype.toString.call(value) === "[object Object]";

  const safeJsonParse = (text) => {
    try {
      return JSON.parse(text);
    } catch {
      return null;
    }
  };

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

  const pickFirst = (...values) => values.map((value) => cleanText(value)).find(Boolean) || "";

  const asArray = (value) => (Array.isArray(value) ? value : value ? [value] : []);

  const isJoinfCustomerApiUrl = (url) =>
    /trade\.joinf\.com|joinf\.com/i.test(String(url || "")) &&
    /(customer|customers|contact|contacts|transfer|follow|detail|list|query|search)/i.test(String(url || ""));

  const looksLikeCustomerRecord = (record) => {
    if (!isPlainObject(record)) {
      return false;
    }
    const keys = Object.keys(record);
    const joined = keys.join("|").toLowerCase();
    const score = [
      /code|customercode|custcode/.test(joined),
      /name|customername|companyname/.test(joined),
      /email|mail/.test(joined),
      /phone|mobile|tel|whatsapp/.test(joined),
      /creator|createuser|salesman|owner|remark|note/.test(joined),
    ].filter(Boolean).length;
    return score >= 2;
  };

  const normalizeCustomerRecord = (record, source = {}) => {
    const code = pickFirst(record.code, record.customerCode, record.custCode, record.customer_code);
    const companyName = pickFirst(record.customerName, record.name, record.companyName, record.custName);
    const contactName = pickFirst(
      record.contactsName,
      record.contactName,
      record.linkman,
      record.contact,
      record.contacts?.name
    );
    const email = pickFirst(
      record.contactsEmail,
      record.contactEmail,
      record.email,
      record.mail,
      record.contacts?.email
    );
    const phone = pickFirst(
      record.contactsPhone,
      record.contactPhone,
      record.phone,
      record.mobile,
      record.tel,
      record.contacts?.phone
    );
    const whatsapp = pickFirst(
      record.whatsapp,
      record.whatsApp,
      record.wa,
      normalizePhone(phone)
    );
    const website = pickFirst(record.website, record.webSite, record.homepage, record.domain);
    const country = pickFirst(record.country, record.countryName, record.nation, record.regionName);
    const creator = pickFirst(record.creator, record.createUserName, record.createName, record.founderName);
    const salesperson = pickFirst(record.salesmanName, record.saleName, record.ownerName, record.userName, record.businessName);
    const note = pickFirst(record.remark, record.memo, record.note, record.description, record.summary);
    const customerLevel = pickFirst(record.customerLevel, record.levelName, record.level, record.customerGrade);
    const lastTransferTime = pickFirst(record.lastTransferTime, record.transferTime, record.latestTransferTime);
    const lastFollowTime = pickFirst(record.lastFollowTime, record.followTime, record.latestFollowTime);
    const linkedin = pickFirst(record.linkedin, record.linkedinUrl, record.linkedinWebsite);
    const whatTheyDo = pickFirst(record.description, record.businessScope, record.introduction, record.profile, note);

    return {
      code,
      company_name: companyName,
      contact_name: contactName,
      country,
      linkedin_website: linkedin,
      email,
      phone: normalizePhone(phone),
      whatsapp: normalizePhone(whatsapp) || whatsapp,
      website,
      creator,
      salesperson,
      customer_level: customerLevel,
      last_transfer_time: lastTransferTime,
      last_follow_time: lastFollowTime,
      note,
      What_they_do: whatTheyDo,
      _source_url: source.url || "",
      _source_method: source.method || "",
      _raw: record,
    };
  };

  const flattenCustomerRecords = (payload, source = {}) => {
    const found = [];
    const stack = [payload];
    while (stack.length) {
      const current = stack.pop();
      if (Array.isArray(current)) {
        current.forEach((item) => stack.push(item));
        continue;
      }
      if (!isPlainObject(current)) {
        continue;
      }
      if (looksLikeCustomerRecord(current)) {
        found.push(normalizeCustomerRecord(current, source));
      }
      Object.values(current).forEach((value) => {
        if (Array.isArray(value) || isPlainObject(value)) {
          stack.push(value);
        }
      });
    }

    const deduped = new Map();
    found.forEach((record, index) => {
      const key = record.code || `${record.company_name}|${record.contact_name}|${record.email}` || `row_${index}`;
      if (!deduped.has(key)) {
        deduped.set(key, record);
      }
    });
    return [...deduped.values()];
  };

  const installApiCapture = (options = {}) => {
    if (window.__joinfApiCapture?.installed) {
      return window.__joinfApiCapture;
    }

    const maxEntries = options.maxEntries ?? 200;
    const state = {
      installed: true,
      installedAt: new Date().toISOString(),
      maxEntries,
      entries: [],
    };

    const pushEntry = (entry) => {
      state.entries.push({
        capturedAt: new Date().toISOString(),
        ...entry,
      });
      if (state.entries.length > state.maxEntries) {
        state.entries.splice(0, state.entries.length - state.maxEntries);
      }
    };

    const originalFetch = window.fetch?.bind(window);
    if (originalFetch) {
      window.fetch = async (...args) => {
        const response = await originalFetch(...args);
        try {
          const requestUrl = typeof args[0] === "string" ? args[0] : args[0]?.url || response.url;
          if (isJoinfCustomerApiUrl(requestUrl)) {
            const cloned = response.clone();
            const contentType = cloned.headers.get("content-type") || "";
            if (/json|text/i.test(contentType)) {
              const text = await cloned.text();
              const payload = safeJsonParse(text);
              if (payload) {
                pushEntry({
                  transport: "fetch",
                  method: args[1]?.method || args[0]?.method || "GET",
                  url: requestUrl,
                  payload,
                });
              }
            }
          }
        } catch (error) {
          console.warn("joinfTools fetch capture error", error);
        }
        return response;
      };
    }

    const originalOpen = XMLHttpRequest.prototype.open;
    const originalSend = XMLHttpRequest.prototype.send;

    XMLHttpRequest.prototype.open = function patchedOpen(method, url, ...rest) {
      this.__joinfMethod = method;
      this.__joinfUrl = url;
      return originalOpen.call(this, method, url, ...rest);
    };

    XMLHttpRequest.prototype.send = function patchedSend(...args) {
      this.addEventListener(
        "loadend",
        () => {
          try {
            const requestUrl = this.__joinfUrl || this.responseURL;
            if (!isJoinfCustomerApiUrl(requestUrl)) {
              return;
            }
            const contentType = this.getResponseHeader("content-type") || "";
            if (!/json|text/i.test(contentType)) {
              return;
            }
            const payload = safeJsonParse(this.responseText);
            if (!payload) {
              return;
            }
            pushEntry({
              transport: "xhr",
              method: this.__joinfMethod || "GET",
              url: requestUrl,
              payload,
            });
          } catch (error) {
            console.warn("joinfTools xhr capture error", error);
          }
        },
        { once: true }
      );
      return originalSend.apply(this, args);
    };

    window.__joinfApiCapture = state;
    console.log("joinfTools API capture installed", state);
    return state;
  };

  const exportApiCapture = (options = {}) => {
    const payload = window.__joinfApiCapture || { installed: false, entries: [] };
    if (options.download !== false) {
      const stamp = new Date().toISOString().replace(/[:.]/g, "-");
      downloadText(`joinf-api-capture-${stamp}.json`, JSON.stringify(payload, null, 2), "application/json");
    }
    console.log("Joinf API capture exported:", payload);
    return payload;
  };

  const exportCapturedCustomerRecords = (options = {}) => {
    const capture = window.__joinfApiCapture || { entries: [] };
    const allRecords = capture.entries.flatMap((entry) =>
      flattenCustomerRecords(entry.payload, { url: entry.url, method: entry.method })
    );
    const deduped = new Map();
    allRecords.forEach((record, index) => {
      const key = record.code || `${record.company_name}|${record.contact_name}|${record.email}` || `record_${index}`;
      if (!deduped.has(key)) {
        deduped.set(key, record);
      }
    });
    const rows = [...deduped.values()];
    const payload = {
      url: location.href,
      extractedAt: new Date().toISOString(),
      rowCount: rows.length,
      rows,
    };

    if (options.download !== false) {
      const stamp = new Date().toISOString().replace(/[:.]/g, "-");
      downloadText(`joinf-customer-records-${stamp}.json`, JSON.stringify(payload, null, 2), "application/json");
      downloadText(
        `joinf-customer-records-${stamp}.csv`,
        toCsv(
          rows.map((row) => {
            const { _raw, ...flat } = row;
            return flat;
          })
        ),
        "text/csv;charset=utf-8"
      );
    }

    window.__joinfLastCustomerRecords = payload;
    console.log("Joinf captured customer records:", payload);
    return payload;
  };

  const findCrmHeaderCells = () => {
    const candidates = [
      ...document.querySelectorAll(".el-table__header-wrapper .cell, .ft_table_header .cell"),
    ];
    return candidates
      .map((cell, index) => {
        const rect = cell.getBoundingClientRect();
        return {
          index,
          key: pickFieldKey(cell.className, index),
          label: cleanText(cell.innerText),
          width: rect.width,
          height: rect.height,
        };
      })
      .filter((item) => item.label && item.width > 0 && item.height > 0);
  };

  const findCrmScrollContainer = () => {
    const candidates = [
      ...document.querySelectorAll(
        ".el-scrollbar__wrap, .el-table__body-wrapper, .ft_table_body, .fl-table, .table_body"
      ),
    ];
    return candidates
      .filter((el) => el.scrollHeight > el.clientHeight + 40)
      .filter((el) => el.querySelector(".fl-table__row"))
      .sort((a, b) => {
        const aScore = a.clientHeight * a.clientWidth;
        const bScore = b.clientHeight * b.clientWidth;
        return bScore - aScore;
      })[0];
  };

  const extractVisibleCrmRows = (columns) => {
    const columnByIndex = new Map(columns.map((column, index) => [index, column]));
    return [...document.querySelectorAll(".ft_table_body .fl-table__row, .fl-table__row")]
      .map((row, rowIndex) => {
        const cells = [...row.querySelectorAll(":scope > .cell")];
        const flat = {};
        const byLabel = {};
        cells.forEach((cell, cellIndex) => {
          const key = pickFieldKey(cell.className, cellIndex);
          const label = columnByIndex.get(cellIndex)?.label || key;
          const value = cleanText(cell.innerText);
          flat[key] = value;
          byLabel[label] = value;
        });
        const code = flat.code || flat.customerCode || "";
        const fallbackKey = code || [flat.name, flat.contactName, flat.contactEmail].filter(Boolean).join("|");
        return {
          _rowIndex: rowIndex,
          _rowKey: fallbackKey || `row_${rowIndex}`,
          ...flat,
          _labels: byLabel,
        };
      })
      .filter((row) => Object.keys(row).length > 3);
  };

  const exportCrmTable = async (options = {}) => {
    const columns = findCrmHeaderCells();
    const container = findCrmScrollContainer();
    if (!columns.length || !container) {
      throw new Error("Could not find the CRM customer table.");
    }

    const step = Math.max(160, Math.floor(container.clientHeight * 0.75));
    const waitMs = options.waitMs ?? 120;
    const maxLoops = options.maxLoops ?? 200;
    const keepRows = new Map();
    const startTop = container.scrollTop;
    let lastSize = -1;
    let stablePasses = 0;

    for (let loop = 0; loop < maxLoops; loop += 1) {
      const visibleRows = extractVisibleCrmRows(columns);
      visibleRows.forEach((row) => {
        keepRows.set(row._rowKey, row);
      });

      if (keepRows.size === lastSize) {
        stablePasses += 1;
      } else {
        stablePasses = 0;
        lastSize = keepRows.size;
      }

      const maxTop = container.scrollHeight - container.clientHeight;
      if (container.scrollTop >= maxTop || stablePasses >= 3) {
        break;
      }

      container.scrollTop = Math.min(container.scrollTop + step, maxTop);
      await sleep(waitMs);
    }

    container.scrollTop = startTop;
    const rows = [...keepRows.values()];
    const payload = {
      url: location.href,
      extractedAt: new Date().toISOString(),
      rowCount: rows.length,
      columns,
      rows,
    };

    if (options.download !== false) {
      const stamp = new Date().toISOString().replace(/[:.]/g, "-");
      downloadText(`crm-export-${stamp}.json`, JSON.stringify(payload, null, 2), "application/json");
      downloadText(`crm-export-${stamp}.csv`, toCsv(rows), "text/csv;charset=utf-8");
    }

    window.__joinfLastCrmExport = payload;
    console.log("CRM export complete:", payload);
    return payload;
  };

  const flagJerryRelatedRows = (rows, options = {}) => {
    const keywords = (options.keywords || ["jerry", "bliiot06"]).map((item) => String(item).toLowerCase());
    const fields = options.fields || [
      "creator",
      "description",
      "activityType",
      "name",
      "contactName",
      "contactEmail",
      "shortName",
    ];
    const manualCodes = new Set((options.manualCodes || []).map((item) => cleanText(item)));

    const matchers = rows.map((row) => {
      const reasons = [];
      if (row.code && manualCodes.has(row.code)) {
        reasons.push("manual-code");
      }
      fields.forEach((field) => {
        const text = cleanText(row[field]).toLowerCase();
        if (!text) {
          return;
        }
        keywords.forEach((keyword) => {
          if (text.includes(keyword)) {
            reasons.push(`${field}:${keyword}`);
          }
        });
      });
      return {
        row,
        reasons: [...new Set(reasons)],
      };
    });

    const matched = matchers.filter((item) => item.reasons.length > 0);
    const unmatched = matchers.filter((item) => item.reasons.length === 0);
    const matchedRows = matched.map((item) => ({
      ...item.row,
      _reasons: item.reasons.join(";"),
    }));
    const codeList = matchedRows.map((row) => row.code).filter(Boolean);
    const payload = {
      total: rows.length,
      matched: matchedRows.length,
      unmatched: unmatched.length,
      codes: codeList,
      rows: matchedRows,
    };

    if (options.download !== false) {
      const stamp = new Date().toISOString().replace(/[:.]/g, "-");
      downloadText(`jerry-related-${stamp}.json`, JSON.stringify(payload, null, 2), "application/json");
      downloadText(`jerry-related-${stamp}.csv`, toCsv(matchedRows), "text/csv;charset=utf-8");
    }

    if (navigator.clipboard?.writeText) {
      navigator.clipboard.writeText(codeList.join("\n")).catch(() => {});
    }

    window.__joinfLastJerryMatch = payload;
    console.log("Jerry-related rows:", payload);
    return payload;
  };

  const findEdmDialogRoot = () => {
    const dialogs = [...document.querySelectorAll(".el-dialog, .el-dialog__wrapper, .v-modal + div")];
    return (
      dialogs.find((dialog) => cleanText(dialog.innerText).includes("选择客户")) ||
      [...document.querySelectorAll("*")].find((node) => {
        const text = cleanText(node.innerText);
        return text.includes("选择客户") && text.includes("符合搜索条件的收件人");
      }) ||
      document.body
    );
  };

  const findEdmScrollContainer = (root) => {
    const candidates = [...root.querySelectorAll(".el-scrollbar__wrap, .el-table__body-wrapper, .dialog-body")];
    return candidates
      .filter((el) => el.scrollHeight > el.clientHeight + 20)
      .filter((el) => el.querySelector("input[type='checkbox'], .el-checkbox"))
      .sort((a, b) => b.clientHeight * b.clientWidth - a.clientHeight * a.clientWidth)[0];
  };

  const extractVisibleEdmRows = (root) => {
    const rowNodes = [
      ...root.querySelectorAll("tr, .el-table__row, .fl-table__row"),
    ].filter((row) => row.querySelector(".el-checkbox, input[type='checkbox']"));

    return rowNodes
      .map((row, index) => {
        const text = cleanText(row.innerText);
        const codeMatch = text.match(/(?:C\d{5,}|\d{8,})/);
        if (!codeMatch) {
          return null;
        }
        const checkbox =
          row.querySelector(".el-checkbox__inner") ||
          row.querySelector(".el-checkbox") ||
          row.querySelector("input[type='checkbox']");
        const checked =
          !!row.querySelector(".el-checkbox.is-checked") ||
          !!row.querySelector("input[type='checkbox']:checked");
        return {
          key: codeMatch[0],
          code: codeMatch[0],
          text,
          checked,
          checkbox,
          index,
        };
      })
      .filter(Boolean);
  };

  const selectEdmRecipientsExcludingCodes = async (excludeCodes, options = {}) => {
    const root = findEdmDialogRoot();
    const container = findEdmScrollContainer(root);
    if (!container) {
      throw new Error("Could not find the EDM recipient table.");
    }

    const excludeSet = new Set((excludeCodes || []).map((item) => cleanText(item)));
    const step = Math.max(160, Math.floor(container.clientHeight * 0.8));
    const waitMs = options.waitMs ?? 100;
    const maxLoops = options.maxLoops ?? 120;
    const seen = new Set();
    const selected = [];
    const skipped = [];
    const startTop = container.scrollTop;

    for (let loop = 0; loop < maxLoops; loop += 1) {
      const rows = extractVisibleEdmRows(root);
      rows.forEach((row) => {
        if (seen.has(row.key)) {
          return;
        }
        seen.add(row.key);
        if (excludeSet.has(row.code)) {
          skipped.push(row.code);
          return;
        }
        if (!row.checked && row.checkbox) {
          row.checkbox.click();
        }
        selected.push(row.code);
      });

      const maxTop = container.scrollHeight - container.clientHeight;
      if (container.scrollTop >= maxTop) {
        break;
      }

      container.scrollTop = Math.min(container.scrollTop + step, maxTop);
      await sleep(waitMs);
    }

    container.scrollTop = startTop;
    const payload = {
      seen: seen.size,
      selected: selected.length,
      skipped: skipped.length,
      selectedCodes: selected,
      skippedCodes: skipped,
    };
    window.__joinfLastEdmSelection = payload;
    console.log("EDM selection complete:", payload);
    return payload;
  };

  window.joinfTools = {
    cleanText,
    downloadText,
    toCsv,
    installApiCapture,
    exportApiCapture,
    exportCapturedCustomerRecords,
    exportCrmTable,
    flagJerryRelatedRows,
    selectEdmRecipientsExcludingCodes,
  };

  console.log("joinfTools ready", Object.keys(window.joinfTools));
})();
