# Existing database audit and scoped write handshake

## When to Use

Use when mapping an existing Notion-backed workflow and verifying minimum integration write access, without running the downstream workflow or modifying production records.

## 1. Inventory before mutation

1. Fetch every page-child block (`GET /v1/blocks/{page_id}/children`, following `has_more` and `next_cursor`). Record block type and ID. For each child page relevant to the workflow, fetch its children too; inspect templates, mappings, diagnostics, and operating instructions. Do not treat an empty search as proof a page does not exist unless the integration can access the relevant scope.
2. For each `child_database`, use its block/database ID and inspect the database metadata to map its data sources. Read each data-source schema with `GET /v1/data_sources/{data_source_id}`. Record every property name and type, select/status options, relation target IDs, and any formulas/rollups. Do not guess property names from prose or invent fields.
3. Query existing rows with `POST /v1/data_sources/{data_source_id}/query`; paginate to completion when counts or duplicate detection require it. For large content databases, inspect only fields needed for schema validation and sync readiness. Inspect logs and setup/diagnostic pages for prior runs or test entries before creating another probe.
4. Check the local automation files/processes when the user asks whether a sync worker is already running. Distinguish a legacy script from the current integration; an empty remote log alone does not prove no local worker exists.
5. Identify operational rules from the existing config pages: stable identifiers, version/revision behavior, allowed status transitions, templates, idempotency, retry/error policy, and schedule. Report conflicts between those instructions and the user's current platform before any downstream work.

## 2. Decide whether a write probe is safe

Proceed only if the user explicitly authorized a test write and the existing schema has a suitable audit/log database. Prefer that database; never create a database or schema field for the test. If the available schema cannot mark and exclude a test row safely, stop and explain the limitation.

Before writing, query the log database for the test marker or unique run ID to avoid duplicate probes. Build the payload only from properties confirmed by the current schema:

- title: clearly prefix with `[HERMES_TEST]`;
- timestamp: use the existing time field and a real UTC timestamp;
- source/direction: identify the permission test, not a production sync;
- run ID: generate a unique value;
- notes/status: explicitly state that it is test-only and excluded from formal processing;
- optional counters: include only schema fields whose meanings are clear.

Do not populate unrelated production records, card rows, or review rows as a permission test.

## 3. Prove create and update by round-trip

1. Create exactly one page in the existing log database with `POST /v1/pages`, using the actual database ID as `parent.database_id` and correctly typed property values from the retrieved schema.
2. Save the returned page ID locally for this operation. Fetch `GET /v1/pages/{created_page_id}` and validate the marker/title, run ID, timestamp, and test-only note. If the create response or readback fails, do not create a second probe.
3. Update only that newly created page via `PATCH /v1/pages/{created_page_id}`. Change the existing notes or status property to an unmistakable result such as `WRITE_TEST_PASSED`; do not add a field.
4. Fetch the same page again and confirm the updated value and unchanged run ID. Retain the test row for audit. If any API call returns 403, `validation_error`, or another error, report the HTTP/API error type and message and stop; do not retry a mutation blindly.
5. A successful create/read/update/read round trip proves those specific operations on that specific shared database/page scope. It does not prove every Notion permission or authorize Anki access. Notion does not provide a general endpoint that substitutes for this functional test.

## 4. Assess workflow readiness and report

For each database, report both database ID and data-source ID, full schema (including option lists and relation targets), record count/status counts where relevant, and which requested capabilities are supported by existing properties. Distinguish an application-level key from an enforced unique constraint. Explicitly identify missing relations, uniqueness constraints, status/error fields, and local-runtime assumptions.

For an Anki bridge, do not call AnkiConnect during a Notion-only audit. Once separately authorized, first verify the local AnkiConnect endpoint from the Hermes execution environment using read-only actions; a configuration page that assumes macOS does not establish Windows loopback reachability. Never mark a Notion card synced until Anki write results have been read back and verified.
