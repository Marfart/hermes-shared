# Safe Notion-to-Anki bridge workflow

## When to Use

Use when initializing or synchronizing a Notion database/template with a local Anki collection. Follow the sequence below; this reference does not grant permission to import cards, sync, or alter Anki preferences.

## 1. Freeze scope and invariants

- Record which Anki model, card template, and deck names are authorized. Distinguish structural setup from note/card creation.
- Keep Notion source rows read-only unless the user separately authorizes a specific write. A PENDING queue is not permission to import it.
- Do not write directly to Anki's SQLite collection, restore a backup, trigger AnkiWeb sync, or substitute a single-deck `.apkg` for a full `.colpkg` backup.
- Preserve protected notes and review history; capture their IDs and a before-state fingerprint for later comparison.
- Ask before changing app preferences, plugin metadata/source, security settings, or software versions.

## 2. Verify the full collection backup first

1. Check the user-designated `.colpkg` exists, is non-empty, and is the expected file. Compute and retain its SHA-256 for the final report.
2. Open the archive read-only with Python `zipfile`; require `testzip()` to return `None`, then confirm the expected collection and media members are present. Do not rewrite the archive.
3. Decompress `collection.anki21b` and verify the SQLite file signature. If a compatible SQLite reader is available, run `PRAGMA quick_check` on this current collection member. If the runtime cannot read it, report the exact limitation; a legacy `collection.anki2` check does not replace verification of the current member.
4. Check media-manifest consistency and whether note fields reference media. Do not claim a restore/recovery test unless one was explicitly authorized and actually performed.
5. If the file is absent, archive CRC fails, required members are missing, or the backup cannot meet the user's stated verification gate, stop before every Anki write.

Useful read-only archive probe:

```python
from pathlib import Path
from zipfile import ZipFile

p = Path("<user-designated-folder>/<collection>.colpkg")
assert p.is_file() and p.stat().st_size > 0
with ZipFile(p) as z:
    assert z.testzip() is None
    names = set(z.namelist())
    assert {"meta", "collection.anki21b", "media"}.issubset(names)
# Stream the file for SHA-256; do not print or alter unrelated profile data.
```

## 3. Reconstruct and fingerprint the Notion source

1. Use the page-scoped integration only. Read the complete ordered template block tree, following every `has_more`/`next_cursor`; concatenate each rich-text block's `plain_text` fragments in order.
2. Preserve code-block content verbatim. Combine split CSS or other fragments only in the source's documented order. Record lengths and hashes of the exact fields, Front, Back, and CSS payloads; never approximate a missing template.
3. Query Cards with the data-source endpoint. For HTTP pagination, send `page_size` and `start_cursor` in the POST JSON body, not as URL query parameters. Continue through all pages.
4. Before any structural write, fingerprint each row by stable page ID, NoteKey, and status. Confirm the expected row count/status distribution. Re-read and compare after initialization; do not import or update queue rows unless separately authorized.

## 4. Check the desktop/API state without causing sync

1. Probe the Anki process and `127.0.0.1:8765` read-only. Use loopback only; never bind AnkiConnect to `0.0.0.0`, expose a firewall port, or disable API authentication.
2. If the API responds, check its version and inspect model/deck names and the protected note before writing. Confirm the installed AnkiConnect metadata/source and running Anki version; a successful version response alone does not prove every write action is supported.
3. If the API refuses connections, do not repeatedly retry the same request. Passively inspect whether Anki is running. Before launching a stopped application, verify whether opening the profile can trigger sync or other prohibited side effects.
4. On Windows, `prefs21.db` stores profile data as pickles. If a read-only sync-setting check is needed, use a restricted unpickler that rejects all global/class loading, and emit only sync-related key names and non-secret booleans. Redact string/byte values, especially sync user/key fields; never print the pickle, credentials, or complete profile object.
5. If `autoSync` is enabled, or its value cannot be safely determined, do not launch Anki when the user forbids sync. Do not silently change the preference. Request explicit permission for a narrowly scoped preference change or ask the user to provide an already-open, no-sync session.
6. If AnkiConnect/API compatibility is unclear, or the model/deck action returns an error, stop and report; do not edit plugin files, loosen version constraints, update software, write SQLite directly, or switch to another profile.

## 5. Create only authorized structure and verify it

1. If the model already exists, read its ordered field names, template names/Front/Back, and CSS. Reuse it only if it exactly matches the source; otherwise stop without overwriting.
2. If absent and compatibility checks pass, create only the authorized model and template through the supported local AnkiConnect action. Read back and compare every field and template byte-for-byte before creating decks.
3. Create only the authorized missing decks; leave existing decks and their settings untouched. Read back deck names and IDs. Do not create notes/cards as a side effect.
4. Re-read protected note metadata and compare ID, model, card IDs, tags, and hashes of field values with the pre-write snapshot. Compare the Notion row fingerprint and status counts. Report created versus reused objects separately.
5. Stop after this phase. Do not start imports, Reviews synchronization, scheduled jobs, or AnkiWeb sync unless separately authorized.

## 6. Report with precise evidence

State the backup path, byte size, SHA-256, ZIP CRC result, required members, and exactly which database checks did or did not complete. Then report API/plugin compatibility evidence, model/template verification, deck IDs, protected-note comparison, Notion before/after fingerprint, and whether any cards were imported. Label blocked or unverified items explicitly; do not infer success from a command exit code alone.