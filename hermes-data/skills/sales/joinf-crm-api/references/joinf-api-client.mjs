const DEFAULT_BASE_URL = "https://trade.joinf.com";

function required(name, value) {
  if (value === undefined || value === null || value === "") {
    throw new Error(`Missing required value: ${name}`);
  }
  return value;
}

function cloneJson(value) {
  return JSON.parse(JSON.stringify(value));
}

function formatDateTime(date = new Date()) {
  const pad = (n) => String(n).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(
    date.getHours()
  )}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`;
}

function setModelValue(model, nextValue, previousValue) {
  model.value = nextValue;
  model.displayValue = nextValue;
  model.originalValue = previousValue;
  model.displayOriginalValue = previousValue;
}

function updateModels(models, fields, previousValues = {}, { scope }) {
  for (const [columnName, nextValue] of Object.entries(fields)) {
    const model = models.find((item) => item.columnName === columnName);
    if (!model) {
      throw new Error(`Unknown ${scope} field in template payload: ${columnName}`);
    }

    const previousValue = Object.prototype.hasOwnProperty.call(previousValues, columnName)
      ? previousValues[columnName]
      : model.originalValue ?? "";

    setModelValue(model, nextValue, previousValue);
  }
}

export function buildFollowRecordPayload({
  customerId,
  content,
  planningTime = formatDateTime(),
  feedbackOperator,
  bgColor = "fe4145",
  completeNoRemind = 0,
}) {
  required("customerId", customerId);
  required("content", content);
  required("feedbackOperator", feedbackOperator);

  return {
    id: "",
    attachmentList: [],
    businessStep: 0,
    customerStep: 0,
    completeNoRemind,
    cycleEndDay: "",
    cycleStartDay: "",
    cycleId: "",
    dataType: 0,
    currentDoneFlag: 0,
    models: [
      {
        columnDisplayName: "Customer Name",
        columnName: "dataName",
        dict: false,
        displayOriginalValue: customerId,
        displayValue: "",
        originalValue: "",
        value: customerId,
      },
      {
        columnDisplayName: "Contact Name",
        columnName: "dataContactName",
        dict: false,
        displayOriginalValue: "",
        displayValue: "",
        originalValue: "",
        value: null,
      },
      {
        columnDisplayName: "Content",
        columnName: "contactContent",
        dict: false,
        displayOriginalValue: "",
        displayValue: "",
        originalValue: "",
        value: content,
      },
      {
        columnDisplayName: "Attachment",
        columnName: "annex",
        dict: false,
        displayOriginalValue: "",
        displayValue: "",
        originalValue: "",
        value: null,
      },
      {
        columnDisplayName: "Color",
        columnName: "bgColor",
        dict: false,
        displayOriginalValue: "",
        displayValue: "",
        originalValue: "",
        value: bgColor,
      },
      {
        columnDisplayName: "Follow Method",
        columnName: "method",
        dict: true,
        displayOriginalValue: "",
        displayValue: "",
        originalValue: "",
        value: "",
      },
      {
        columnDisplayName: "Planning Time",
        columnName: "planningTime",
        dict: false,
        displayOriginalValue: "",
        displayValue: "",
        originalValue: "",
        value: planningTime,
      },
      {
        columnDisplayName: "Step",
        columnName: "step",
        dict: true,
        displayOriginalValue: "",
        displayValue: "",
        originalValue: "",
        value: null,
      },
      {
        columnDisplayName: "Next Remind Time",
        columnName: "nextRemindTime",
        dict: false,
        displayOriginalValue: "",
        displayValue: "",
        originalValue: "",
        value: null,
      },
      {
        columnDisplayName: "Repeat Cycle",
        columnName: "repeatCycle",
        dict: false,
        displayOriginalValue: "",
        displayValue: "",
        originalValue: "",
        value: null,
      },
      {
        columnDisplayName: "Relevant",
        columnName: "relevant",
        dict: false,
        displayOriginalValue: "",
        displayValue: "",
        originalValue: "",
        value: null,
      },
      {
        columnDisplayName: "Operator",
        columnName: "operatorName",
        dict: false,
        displayOriginalValue: "",
        displayValue: "",
        originalValue: "",
        value: null,
      },
      {
        columnDisplayName: "Feedback Operator",
        columnName: "feedbackOperator",
        dict: false,
        displayOriginalValue: "",
        displayValue: "",
        originalValue: "",
        value: String(feedbackOperator),
      },
    ],
    relevantList: [{ relevantId: "", relevant: "" }],
    flowStep: "",
    forceRefresh: true,
    followType: "",
    followObject: "",
  };
}

export function buildCustomerPatchPayloadFromTemplate({
  templatePayload,
  customerId,
  fields,
  previousValues = {},
  attachmentList,
  tagList,
  markModel,
}) {
  required("templatePayload", templatePayload);
  required("customerId", customerId);
  required("fields", fields);

  if (!Array.isArray(templatePayload.models)) {
    throw new Error("templatePayload.models must be an array");
  }

  const payload = cloneJson(templatePayload);
  payload.id = customerId;

  if (attachmentList !== undefined) {
    payload.customerAttachmentDtoList = attachmentList;
  }

  if (tagList !== undefined) {
    payload.tagList = tagList;
  }

  if (markModel !== undefined) {
    payload.markModel = markModel;
  }

  updateModels(payload.models, fields, previousValues, { scope: "customer" });

  return payload;
}

export function buildCustomerCreatePayloadFromTemplate({
  templatePayload,
  fields,
  customerPreviousValues = {},
  contactFields = {},
  contactPreviousValues = {},
  attachmentList,
  tagList,
  markModel,
}) {
  required("templatePayload", templatePayload);
  required("fields", fields);

  if (!Array.isArray(templatePayload.models)) {
    throw new Error("templatePayload.models must be an array");
  }

  const payload = cloneJson(templatePayload);
  delete payload.id;

  if (attachmentList !== undefined) {
    payload.customerAttachmentDtoList = attachmentList;
  }

  if (tagList !== undefined) {
    payload.tagList = tagList;
  }

  if (markModel !== undefined) {
    payload.markModel = markModel;
  } else if (payload.markModel && typeof payload.markModel === "object") {
    payload.markModel.customerId = 0;
  }

  updateModels(payload.models, fields, customerPreviousValues, { scope: "customer" });

  if (Object.keys(contactFields).length > 0) {
    const firstContact = payload.contacts?.[0];
    if (!firstContact || !Array.isArray(firstContact.models)) {
      throw new Error("templatePayload.contacts[0].models must exist when contactFields are provided");
    }

    updateModels(firstContact.models, contactFields, contactPreviousValues, { scope: "contact" });
  }

  return payload;
}

export function extractCustomerFieldValue(detailResponseJson, columnName) {
  const categories = detailResponseJson?.data;
  if (!Array.isArray(categories)) {
    return undefined;
  }

  for (const category of categories) {
    const columnData = category?.columnData?.[columnName];
    if (columnData && Object.prototype.hasOwnProperty.call(columnData, "value")) {
      return columnData.value;
    }
  }

  return undefined;
}

export function createJoinfClient({
  baseUrl = DEFAULT_BASE_URL,
  cookie,
  xCid,
  xUser,
  userAgent = "Mozilla/5.0",
  origin = DEFAULT_BASE_URL,
  referer = `${DEFAULT_BASE_URL}/tms/customer/customers?type=search&tab=0`,
  fetchImpl = fetch,
}) {
  required("cookie", cookie);
  required("xCid", xCid);
  required("xUser", xUser);

  async function request(path, { method = "GET", body, extraHeaders = {} } = {}) {
    const headers = {
      Accept: "application/json, text/plain, */*",
      Cookie: cookie,
      Origin: origin,
      Referer: referer,
      "User-Agent": userAgent,
      "X-Cid": String(xCid),
      "X-User": String(xUser),
      ...extraHeaders,
    };

    if (body !== undefined && !headers["Content-Type"]) {
      headers["Content-Type"] = "application/json";
    }

    const response = await fetchImpl(new URL(path, baseUrl), {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
    });

    const text = await response.text();
    let json = null;
    try {
      json = JSON.parse(text);
    } catch {
      json = null;
    }

    return {
      ok: response.ok,
      status: response.status,
      headers: Object.fromEntries(response.headers.entries()),
      text,
      json,
    };
  }

  return {
    async addFollowRecord({ customerId, content, planningTime, feedbackOperator = xUser, bgColor }) {
      const payload = buildFollowRecordPayload({
        customerId,
        content,
        planningTime,
        feedbackOperator,
        bgColor,
      });
      return request("/rapi/m/follow/add", { method: "POST", body: payload });
    },

    async readCustomerDetail({ customerId, pageType = 1 }) {
      required("customerId", customerId);
      return request(`/rapi/d/customers/${customerId}/${pageType}`);
    },

    async updateCustomer({
      customerId,
      templatePayload,
      fields,
      previousValues,
      attachmentList,
      tagList,
      markModel,
    }) {
      const payload = buildCustomerPatchPayloadFromTemplate({
        templatePayload,
        customerId,
        fields,
        previousValues,
        attachmentList,
        tagList,
        markModel,
      });
      return request("/rapi/d/customer", { method: "PATCH", body: payload });
    },

    async createCustomer({
      templatePayload,
      fields,
      customerPreviousValues,
      contactFields,
      contactPreviousValues,
      attachmentList,
      tagList,
      markModel,
    }) {
      const payload = buildCustomerCreatePayloadFromTemplate({
        templatePayload,
        fields,
        customerPreviousValues,
        contactFields,
        contactPreviousValues,
        attachmentList,
        tagList,
        markModel,
      });
      return request("/rapi/d/customer", { method: "POST", body: payload });
    },

    async addRemark() {
      throw new Error(
        "Standalone addRemark API is not confirmed yet. Use updateCustomer({ fields: { description: ... } }) for the customer remark field."
      );
    },

    async saveMailDraft() {
      throw new Error("saveMailDraft is not implemented yet: API not confirmed in this exploration run.");
    },
  };
}

export { formatDateTime };
