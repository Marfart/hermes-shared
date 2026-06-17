import test from "node:test";
import assert from "node:assert/strict";

import {
  buildCustomerCreatePayloadFromTemplate,
  buildCustomerPatchPayloadFromTemplate,
  buildFollowRecordPayload,
  createJoinfClient,
} from "./joinf-api-client.mjs";

test("buildFollowRecordPayload creates the discovered follow payload shape", () => {
  const payload = buildFollowRecordPayload({
    customerId: 238855638,
    content: "HERMES_API_TEST_PAYLOAD",
    planningTime: "2026-06-17 08:54:42",
    feedbackOperator: 183006,
  });

  assert.equal(payload.models.find((item) => item.columnName === "dataName").value, 238855638);
  assert.equal(payload.models.find((item) => item.columnName === "contactContent").value, "HERMES_API_TEST_PAYLOAD");
  assert.equal(payload.models.find((item) => item.columnName === "planningTime").value, "2026-06-17 08:54:42");
  assert.equal(payload.models.find((item) => item.columnName === "feedbackOperator").value, "183006");
});

test("buildCustomerPatchPayloadFromTemplate updates the targeted customer field", () => {
  const templatePayload = {
    models: [
      {
        columnName: "name",
        value: "Test Customer XMA",
        displayValue: "Test Customer XMA",
        originalValue: "Test Customer XMA",
        displayOriginalValue: "Test Customer XMA",
      },
      {
        columnName: "description",
        value: "OLD_VALUE",
        displayValue: "OLD_VALUE",
        originalValue: "OLD_VALUE",
        displayOriginalValue: "OLD_VALUE",
      },
    ],
    contacts: [{ models: [], id: 208899969 }],
    banks: [],
    customerAttachmentDtoList: [],
    id: 238855638,
    tagList: [],
    markModel: { isChanged: false, customerId: 238855638 },
  };

  const payload = buildCustomerPatchPayloadFromTemplate({
    templatePayload,
    customerId: 238855638,
    fields: { description: "HERMES_API_TEST_UPDATE" },
    previousValues: { description: "OLD_VALUE" },
  });

  assert.equal(payload.id, 238855638);
  assert.equal(payload.models.find((item) => item.columnName === "description").value, "HERMES_API_TEST_UPDATE");
  assert.equal(payload.models.find((item) => item.columnName === "description").originalValue, "OLD_VALUE");
  assert.equal(payload.models.find((item) => item.columnName === "name").value, "Test Customer XMA");
  assert.equal(payload.markModel.customerId, 238855638);
});

test("buildCustomerCreatePayloadFromTemplate updates customer and first-contact fields", () => {
  const templatePayload = {
    models: [
      {
        columnName: "name",
        value: "",
        displayValue: "",
        originalValue: "",
        displayOriginalValue: "",
      },
      {
        columnName: "shortName",
        value: "",
        displayValue: "",
        originalValue: "",
        displayOriginalValue: "",
      },
      {
        columnName: "description",
        value: "",
        displayValue: "",
        originalValue: "",
        displayOriginalValue: "",
      },
    ],
    contacts: [
      {
        models: [
          {
            columnName: "name",
            value: "",
            displayValue: "",
            originalValue: "",
            displayOriginalValue: "",
          },
        ],
      },
    ],
    banks: [],
    customerAttachmentDtoList: [],
    tagList: [],
    markModel: { customerId: 123, isChanged: false },
  };

  const payload = buildCustomerCreatePayloadFromTemplate({
    templatePayload,
    fields: {
      name: "Hermes Atlas 79139",
      shortName: "H9139",
      description: "HERMES_CREATE_TEST_1781659479139",
    },
    contactFields: {
      name: "Noah Reed",
    },
  });

  assert.equal(payload.id, undefined);
  assert.equal(payload.models.find((item) => item.columnName === "name").value, "Hermes Atlas 79139");
  assert.equal(payload.models.find((item) => item.columnName === "shortName").value, "H9139");
  assert.equal(
    payload.models.find((item) => item.columnName === "description").value,
    "HERMES_CREATE_TEST_1781659479139"
  );
  assert.equal(payload.contacts[0].models.find((item) => item.columnName === "name").value, "Noah Reed");
  assert.equal(payload.markModel.customerId, 0);
});

test("createJoinfClient.addFollowRecord posts to the confirmed endpoint", async () => {
  const calls = [];
  const fakeFetch = async (url, init) => {
    calls.push({ url: String(url), init });
    return {
      ok: true,
      status: 200,
      headers: new Headers({ "content-type": "application/json" }),
      text: async () => JSON.stringify({ code: 0, success: true, data: [70850656] }),
    };
  };

  const client = createJoinfClient({
    cookie: "JOINF_SESSION=test",
    xCid: 71376,
    xUser: 183006,
    fetchImpl: fakeFetch,
  });

  const result = await client.addFollowRecord({
    customerId: 238855638,
    content: "HERMES_API_TEST_CLIENT",
    planningTime: "2026-06-17 08:54:42",
  });

  assert.equal(calls.length, 1);
  assert.equal(calls[0].url, "https://trade.joinf.com/rapi/m/follow/add");
  assert.equal(calls[0].init.method, "POST");
  assert.equal(result.status, 200);
  assert.equal(result.json.success, true);

  const posted = JSON.parse(calls[0].init.body);
  assert.equal(posted.models.find((item) => item.columnName === "contactContent").value, "HERMES_API_TEST_CLIENT");
});

test("createJoinfClient.updateCustomer uses PATCH on the confirmed endpoint", async () => {
  const calls = [];
  const fakeFetch = async (url, init) => {
    calls.push({ url: String(url), init });
    return {
      ok: true,
      status: 200,
      headers: new Headers({ "content-type": "application/json" }),
      text: async () => JSON.stringify({ code: 0, success: true, data: 238855638 }),
    };
  };

  const client = createJoinfClient({
    cookie: "JOINF_SESSION=test",
    xCid: 71376,
    xUser: 183006,
    fetchImpl: fakeFetch,
  });

  const result = await client.updateCustomer({
    customerId: 238855638,
    templatePayload: {
      models: [
        {
          columnName: "description",
          value: "OLD",
          displayValue: "OLD",
          originalValue: "OLD",
          displayOriginalValue: "OLD",
        },
      ],
      contacts: [],
      banks: [],
      customerAttachmentDtoList: [],
      id: 238855638,
      tagList: [],
      markModel: { isChanged: false, customerId: 238855638 },
    },
    fields: { description: "HERMES_API_TEST_PATCH" },
    previousValues: { description: "OLD" },
  });

  assert.equal(calls.length, 1);
  assert.equal(calls[0].url, "https://trade.joinf.com/rapi/d/customer");
  assert.equal(calls[0].init.method, "PATCH");
  assert.equal(result.status, 200);
  assert.equal(result.json.success, true);

  const posted = JSON.parse(calls[0].init.body);
  assert.equal(posted.id, 238855638);
  assert.equal(posted.models.find((item) => item.columnName === "description").value, "HERMES_API_TEST_PATCH");
});

test("createJoinfClient.createCustomer uses POST on the confirmed endpoint", async () => {
  const calls = [];
  const fakeFetch = async (url, init) => {
    calls.push({ url: String(url), init });
    return {
      ok: true,
      status: 200,
      headers: new Headers({ "content-type": "application/json" }),
      text: async () => JSON.stringify({ code: 0, success: true, data: 238858620 }),
    };
  };

  const client = createJoinfClient({
    cookie: "JOINF_SESSION=test",
    xCid: 71376,
    xUser: 183006,
    fetchImpl: fakeFetch,
  });

  const result = await client.createCustomer({
    templatePayload: {
      models: [
        {
          columnName: "name",
          value: "",
          displayValue: "",
          originalValue: "",
          displayOriginalValue: "",
        },
        {
          columnName: "description",
          value: "",
          displayValue: "",
          originalValue: "",
          displayOriginalValue: "",
        },
      ],
      contacts: [
        {
          models: [
            {
              columnName: "name",
              value: "",
              displayValue: "",
              originalValue: "",
              displayOriginalValue: "",
            },
          ],
        },
      ],
      banks: [],
      customerAttachmentDtoList: [],
      tagList: [],
      markModel: { customerId: 123, isChanged: false },
    },
    fields: { name: "Hermes Nova 40171", description: "HERMES_CREATE_TEST_1781659740171" },
    contactFields: { name: "Ethan Cole" },
  });

  assert.equal(calls.length, 1);
  assert.equal(calls[0].url, "https://trade.joinf.com/rapi/d/customer");
  assert.equal(calls[0].init.method, "POST");
  assert.equal(result.status, 200);
  assert.equal(result.json.success, true);

  const posted = JSON.parse(calls[0].init.body);
  assert.equal(posted.models.find((item) => item.columnName === "name").value, "Hermes Nova 40171");
  assert.equal(posted.contacts[0].models.find((item) => item.columnName === "name").value, "Ethan Cole");
});
