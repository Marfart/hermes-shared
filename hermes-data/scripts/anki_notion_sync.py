#!/usr/bin/env python3
"""Safe, on-demand Notion ↔ Anki bridge for the authorized IELTS control page.

No scheduler, AnkiWeb sync, collection DB writes, deletions, or note recreation.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import io
import json
import logging
import os
import pathlib
import pickle
import re
import sqlite3
import sys
import time
import urllib.error
import urllib.request
import uuid
import zipfile
from typing import Any

MODEL = "IELTS_Vocabulary_v1"
TEMPLATE_NAME = "01 · English → Meaning"
CONTROL_PAGE = "3f8db368-b7f0-815a-9446-c4c892fc4626"
TEMPLATE_PAGE = "3f8db368-b7f0-81dd-80d0-edcedd7f7624"
CARDS_DS = "997c6c3c-a19e-4a4f-a545-8167e39db8bf"
REVIEWS_DS = "9673aa81-af52-4aed-b8d8-71a59fe26048"
LOG_DS = "e51cc2cf-affb-425e-a066-8034e031ddec"
EXPECTED_FIELDS = ["English", "IPA", "POS", "MeaningZH", "ExampleEN", "ExampleZH", "WordFamily", "WordFamilyExamples", "Chunks", "Source", "OfficialExcerpt", "OfficialLink", "Audio", "NoteKey", "Notes"]
EXPECTED_HASHES = {
    "front": "541a45a204bc6ebf3cb9969d33cdbade4b2f239306c5556175ba1e0a80280495",
    "back": "677cf05d9ea6bca09271fa6d6291406c9716b9b20d2f3c6d86d602a7f25917e2",
    "css": "14c4294ab4d81e9d7c3a86c53bafb0d3d2c2b421d016d121ba5cdb39a7dda4ae",
}
EXPECTED_BACKUP_SHA256 = "97839b5604d0a9affaca1a15396eeb30a9ca0f8942780125f21343648058cf8e"
TARGET_DECKS = {"IELTS::2026-10-13::Priority", "IELTS::2026-10-13::Review"}
API_URL = "http://127.0.0.1:8765"
NOTION_BASE = "https://api.notion.com/v1"
NOTION_VERSION = "2025-09-03"

HOME = pathlib.Path(os.environ.get("LOCALAPPDATA", pathlib.Path.home())) / "hermes"
CACHE = HOME / "memories" / "脚本缓存" / "anki-notion-sync"
STATE_PATH = CACHE / "sync_state.sqlite3"
LOG_PATH = CACHE / "sync.log"
PREFS_PATH = pathlib.Path(os.environ.get("APPDATA", "")) / "Anki2" / "prefs21.db"
BACKUP_PATH = pathlib.Path.home() / "Documents" / "AnkiBackups" / "Anki_collection_2026-10-14_10-43-22.colpkg"

class SyncFailure(RuntimeError):
    pass

class RestrictedUnpickler(pickle.Unpickler):
    def find_class(self, module: str, name: str) -> Any:
        raise pickle.UnpicklingError("blocked global")

def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")

def safe_log(event: str, **fields: Any) -> None:
    # Never log request bodies, field payloads, environment values, or exceptions' raw messages.
    record = {"time": utc_now(), "event": event, **fields}
    logging.info(json.dumps(record, ensure_ascii=False, separators=(",", ":")))

def read_prefs() -> dict[str, Any]:
    if not PREFS_PATH.is_file():
        raise SyncFailure("Anki preferences are unavailable; refusing to run without the no-sync gate.")
    con = sqlite3.connect(f"file:{PREFS_PATH.as_posix()}?mode=ro", uri=True, timeout=5)
    try:
        blob = con.execute("SELECT data FROM profiles WHERE name=?", ("账户 1",)).fetchone()
        if not blob:
            raise SyncFailure("The authorized Anki profile 账户 1 was not found.")
        return RestrictedUnpickler(io.BytesIO(blob[0])).load()
    finally:
        con.close()

def anki(action: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    body: dict[str, Any] = {"action": action, "version": 6}
    if params is not None:
        body["params"] = params
    request = urllib.request.Request(API_URL, json.dumps(body, ensure_ascii=False).encode("utf-8"), {"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            data = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        raise SyncFailure(f"AnkiConnect unavailable during {action} ({type(exc).__name__}).") from None
    if not isinstance(data, dict) or data.get("error") is not None:
        raise SyncFailure(f"AnkiConnect rejected {action} (API error).")
    return data

def load_notion_token() -> str:
    token = os.environ.get("NOTION_API_KEY", "").strip()
    env_path = HOME / ".env"
    if token:
        return token
    if env_path.is_file():
        for line in env_path.read_text(encoding="utf-8-sig").splitlines():
            line = line.strip()
            if line.startswith("NOTION_API_KEY="):
                value = line.split("=", 1)[1].strip()
                if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                    value = value[1:-1]
                return value
    raise SyncFailure("Notion API credential is not available locally; no secret was printed.")

class NotionClient:
    def __init__(self, token: str) -> None:
        self.headers = {"Authorization": "Bearer " + token, "Notion-Version": NOTION_VERSION, "Content-Type": "application/json"}
        self.last_call = 0.0

    def request(self, path: str, method: str = "GET", body: dict[str, Any] | None = None, read_only: bool = False) -> dict[str, Any]:
        delay = 0.36 - (time.monotonic() - self.last_call)
        if delay > 0:
            time.sleep(delay)
        data = None if body is None else json.dumps(body, ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(NOTION_BASE + path, data=data, headers=self.headers, method=method)
        tries = 3 if read_only else 1
        for attempt in range(tries):
            try:
                with urllib.request.urlopen(request, timeout=25) as response:
                    result = json.loads(response.read().decode("utf-8"))
                self.last_call = time.monotonic()
                return result
            except urllib.error.HTTPError as exc:
                self.last_call = time.monotonic()
                if read_only and exc.code in (429, 500, 502, 503, 504) and attempt + 1 < tries:
                    time.sleep(min(2 ** attempt, 4))
                    continue
                raise SyncFailure(f"Notion {method} {path.split('?')[0]} returned HTTP {exc.code}.") from None
            except Exception as exc:
                self.last_call = time.monotonic()
                if read_only and attempt + 1 < tries:
                    time.sleep(min(2 ** attempt, 4))
                    continue
                raise SyncFailure(f"Notion {method} {path.split('?')[0]} failed ({type(exc).__name__}).") from None
        raise SyncFailure("Notion read request exhausted safe retries.")

    def query_all(self, source_id: str) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        cursor: str | None = None
        while True:
            body: dict[str, Any] = {"page_size": 100}
            if cursor:
                body["start_cursor"] = cursor
            data = self.request(f"/data_sources/{source_id}/query", "POST", body, read_only=True)
            rows.extend(data.get("results", []))
            cursor = data.get("next_cursor")
            if not data.get("has_more"):
                return rows

    def schema(self, source_id: str) -> dict[str, Any]:
        return self.request(f"/data_sources/{source_id}", read_only=True)

    def get_page(self, page_id: str) -> dict[str, Any]:
        return self.request(f"/pages/{page_id}", read_only=True)

    def patch_page(self, page_id: str, properties: dict[str, Any]) -> dict[str, Any]:
        return self.request(f"/pages/{page_id}", "PATCH", {"properties": properties})

    def create_page(self, database_id: str, properties: dict[str, Any]) -> dict[str, Any]:
        return self.request("/pages", "POST", {"parent": {"database_id": database_id}, "properties": properties})

def prop_value(prop: dict[str, Any]) -> Any:
    kind = prop.get("type")
    value = prop.get(kind)
    if kind in ("title", "rich_text"):
        return "".join(x.get("plain_text", "") for x in (value or []))
    if kind in ("select", "status"):
        return (value or {}).get("name", "")
    if kind == "number":
        return value
    if kind == "url":
        return value
    if kind == "date":
        return (value or {}).get("start")
    if kind == "checkbox":
        return value
    return None

def page_value(page: dict[str, Any], name: str) -> Any:
    return prop_value((page.get("properties") or {}).get(name, {}))

def rich_text(value: str) -> list[dict[str, Any]]:
    if not value:
        return []
    return [{"type": "text", "text": {"content": value[i:i + 1900]}} for i in range(0, len(value), 1900)][:100]

def exact_rich_text_value(value: str) -> dict[str, Any]:
    return {"rich_text": rich_text(value)}

def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()

def extract_template(notion: NotionClient) -> dict[str, Any]:
    page = notion.get_page(TEMPLATE_PAGE)
    if (page.get("parent") or {}).get("page_id") != CONTROL_PAGE:
        raise SyncFailure("Vocabulary template is not a child of the authorized control page.")
    blocks: list[dict[str, Any]] = []
    cursor = None
    while True:
        path = f"/blocks/{TEMPLATE_PAGE}/children?page_size=100" + ("&start_cursor=" + cursor if cursor else "")
        result = notion.request(path, read_only=True)
        blocks.extend(result.get("results", []))
        cursor = result.get("next_cursor")
        if not result.get("has_more"):
            break
    sequence = []
    for block in blocks:
        kind = block.get("type")
        content = (block.get(kind) or {}).get("rich_text", [])
        sequence.append((kind, "".join(x.get("plain_text", "") for x in content)))

    def following(label: str, expected_type: str) -> str:
        for index, (kind, text) in enumerate(sequence):
            if text == label:
                for next_type, next_text in sequence[index + 1:]:
                    if next_text or next_type in ("code", "paragraph"):
                        if next_type != expected_type:
                            raise SyncFailure(f"Template block type mismatch at {label}.")
                        return next_text
        raise SyncFailure(f"Template block missing: {label}.")

    fields = json.loads(following("inOrderFields（JSON）", "code"))
    name = following("cardTemplates[0].Name", "paragraph")
    front = following("cardTemplates[0].Front", "code")
    back = following("cardTemplates[0].Back", "code")
    css = following("CSS_PART_1", "code") + following("CSS_PART_2", "code")
    hashes = {"front": sha256_text(front), "back": sha256_text(back), "css": sha256_text(css)}
    if fields != EXPECTED_FIELDS or name != TEMPLATE_NAME or hashes != EXPECTED_HASHES:
        raise SyncFailure("Notion template differs from the approved baseline; refusing to alter Anki notes.")
    return {"fields": fields, "name": name, "front": front, "back": back, "css": css}

def verify_runtime(notion: NotionClient) -> tuple[dict[str, Any], dict[str, Any]]:
    prefs = read_prefs()
    if prefs.get("autoSync") is not False:
        raise SyncFailure("Anki autoSync is not false; no Anki write or sync was attempted.")
    if prefs.get("customSyncUrl"):
        raise SyncFailure("A custom Anki sync URL is configured; refusing to proceed.")
    if anki("getActiveProfile").get("result") != "账户 1" or anki("version").get("result") != 6:
        raise SyncFailure("Anki profile/API does not match the authorized local target.")
    models = anki("modelNames").get("result") or []
    if MODEL not in models:
        raise SyncFailure("The approved Anki note type is missing.")
    template = extract_template(notion)
    fields = anki("modelFieldNames", {"modelName": MODEL}).get("result")
    templates = anki("modelTemplates", {"modelName": MODEL}).get("result")
    styling = anki("modelStyling", {"modelName": MODEL}).get("result")
    if fields != template["fields"] or templates != {template["name"]: {"Front": template["front"], "Back": template["back"]}} or (styling or {}).get("css") != template["css"]:
        raise SyncFailure("Anki model/template/CSS readback differs from the Notion source.")
    deck_map = anki("deckNamesAndIds").get("result") or {}
    if any(name not in deck_map for name in TARGET_DECKS):
        raise SyncFailure("One or more authorized IELTS target decks are missing.")
    schemas = {"cards": notion.schema(CARDS_DS), "reviews": notion.schema(REVIEWS_DS), "log": notion.schema(LOG_DS)}
    required_cards = {"Name": "title", "Status": "select", "NoteKey": "rich_text", "Revision": "number", "PayloadJSON": "rich_text", "NoteID": "rich_text", "CardIDs": "rich_text", "SyncedAt": "rich_text", "Error": "rich_text", "Deck": "rich_text", "Model": "rich_text", "Tags": "rich_text"}
    for name, kind in required_cards.items():
        if (schemas["cards"].get("properties") or {}).get(name, {}).get("type") != kind:
            raise SyncFailure(f"Cards schema mismatch at property {name}.")
    required_reviews = {"Name": "title", "CardID": "rich_text", "NoteID": "rich_text", "NoteKey": "rich_text", "Reps": "number", "Lapses": "number", "AgainCount": "number", "EaseFactor": "number", "IntervalDays": "number", "Due": "rich_text", "Deck": "rich_text", "CardState": "rich_text", "FetchedAtUTC": "rich_text", "LastReviewUTC": "rich_text", "RawJSON": "rich_text"}
    for name, kind in required_reviews.items():
        if (schemas["reviews"].get("properties") or {}).get(name, {}).get("type") != kind:
            raise SyncFailure(f"Reviews schema mismatch at property {name}.")
    required_log = {"Name": "title", "TimeUTC": "rich_text", "Direction": "rich_text", "RunID": "rich_text", "Created": "number", "Updated": "number", "Skipped": "number", "Failed": "number", "RecordsSeen": "number", "Notes": "rich_text"}
    for name, kind in required_log.items():
        if (schemas["log"].get("properties") or {}).get(name, {}).get("type") != kind:
            raise SyncFailure(f"Sync Log schema mismatch at property {name}.")
    return template, schemas

def parse_card_rows(notion: NotionClient) -> list[dict[str, Any]]:
    records = []
    for page in notion.query_all(CARDS_DS):
        props = page.get("properties", {})
        raw = prop_value(props.get("PayloadJSON", {})) or ""
        text = str(raw).strip()
        if text.startswith("json:"):
            text = text[5:].lstrip()
        try:
            payload = json.loads(text)
            if not isinstance(payload, dict):
                raise ValueError("payload must be a JSON object")
            parse_error = None
        except Exception:
            payload = {}
            parse_error = "PayloadJSON is not valid JSON after the json: prefix."
        records.append({
            "page_id": page.get("id"),
            "last_edited_time": page.get("last_edited_time"),
            "status": prop_value(props.get("Status", {})),
            "note_key": str(prop_value(props.get("NoteKey", {})) or "").strip(),
            "revision": prop_value(props.get("Revision", {})),
            "payload": payload,
            "parse_error": parse_error,
            "priority": prop_value(props.get("Priority", {})),
            "deck": str(prop_value(props.get("Deck", {})) or "").strip(),
            "existing_note_id": str(prop_value(props.get("NoteID", {})) or "").strip(),
            "existing_card_ids": str(prop_value(props.get("CardIDs", {})) or "").strip(),
            "tags": str(prop_value(props.get("Tags", {})) or "").strip(),
        })
    return records

def sorted_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    def key(record: dict[str, Any]) -> tuple[str, int, str]:
        match = re.search(r"(\d+)$", record.get("note_key", ""))
        return (record.get("note_key", ""), int(match.group(1)) if match else 0, record.get("page_id", ""))
    return sorted(records, key=key)

def field_map(record: dict[str, Any]) -> dict[str, str]:
    payload = record["payload"]
    if set(payload) != set(EXPECTED_FIELDS):
        raise SyncFailure("PayloadJSON fields do not exactly match the approved 15-field model.")
    if payload.get("NoteKey") != record.get("note_key"):
        raise SyncFailure("Payload NoteKey does not match the Cards row NoteKey.")
    result = {}
    for field in EXPECTED_FIELDS:
        value = payload.get(field, "")
        if value is None:
            value = ""
        if not isinstance(value, (str, int, float, bool)):
            raise SyncFailure(f"Payload field {field} is not a scalar string value.")
        result[field] = str(value)
    if not result["English"].strip():
        raise SyncFailure("English headword is empty.")
    return result

def payload_hash(fields: dict[str, str]) -> str:
    return sha256_text(json.dumps(fields, ensure_ascii=False, sort_keys=True, separators=(",", ":")))

def init_state(conn: sqlite3.Connection) -> None:
    conn.execute("CREATE TABLE IF NOT EXISTS notes (note_key TEXT PRIMARY KEY, page_id TEXT NOT NULL, revision INTEGER NOT NULL, payload_hash TEXT NOT NULL, note_id INTEGER NOT NULL, card_ids_json TEXT NOT NULL, deck TEXT NOT NULL, updated_at TEXT NOT NULL)")
    conn.execute("CREATE TABLE IF NOT EXISTS runs (run_id TEXT PRIMARY KEY, started_at TEXT NOT NULL, finished_at TEXT, summary_json TEXT)")
    conn.execute("CREATE TABLE IF NOT EXISTS review_state (card_id TEXT PRIMARY KEY, page_id TEXT NOT NULL, raw_hash TEXT NOT NULL, updated_at TEXT NOT NULL)")

def state_get(conn: sqlite3.Connection, note_key: str) -> dict[str, Any] | None:
    row = conn.execute("SELECT note_key,page_id,revision,payload_hash,note_id,card_ids_json,deck,updated_at FROM notes WHERE note_key=?", (note_key,)).fetchone()
    if not row:
        return None
    return dict(zip(("note_key", "page_id", "revision", "payload_hash", "note_id", "card_ids_json", "deck", "updated_at"), row))

def state_put(conn: sqlite3.Connection, record: dict[str, Any], revision: int, digest: str, note_id: int, card_ids: list[int], deck: str) -> None:
    conn.execute("INSERT INTO notes(note_key,page_id,revision,payload_hash,note_id,card_ids_json,deck,updated_at) VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(note_key) DO UPDATE SET page_id=excluded.page_id,revision=excluded.revision,payload_hash=excluded.payload_hash,note_id=excluded.note_id,card_ids_json=excluded.card_ids_json,deck=excluded.deck,updated_at=excluded.updated_at", (record["note_key"], record["page_id"], revision, digest, note_id, json.dumps(card_ids), deck, utc_now()))

def normal_text(value: Any) -> str:
    value = str(value or "").replace("<br>", " ").replace("<br/>", " ")
    value = re.sub(r"<[^>]+>", " ", value)
    return " ".join(value.split()).casefold()

def find_exact_notes(field: str, value: str, any_field: bool = False) -> list[dict[str, Any]]:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    query = f'"{escaped}"' if any_field else f'{field}:{escaped}'
    ids = anki("findNotes", {"query": query}).get("result") or []
    if not ids:
        return []
    return anki("notesInfo", {"notes": ids}).get("result") or []

def cards_for_note(note_id: int) -> tuple[list[int], list[dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    card_ids = anki("findCards", {"query": f"nid:{note_id}"}).get("result") or []
    info = anki("cardsInfo", {"cards": card_ids}).get("result") or [] if card_ids else []
    reviews = anki("getReviewsOfCards", {"cards": card_ids}).get("result") or {} if card_ids else {}
    return card_ids, info, reviews

def note_snapshot(note_id: int) -> dict[str, Any]:
    notes = anki("notesInfo", {"notes": [note_id]}).get("result") or []
    if len(notes) != 1:
        raise SyncFailure("Anki note readback returned an unexpected count.")
    note = notes[0]
    card_ids, cards, reviews = cards_for_note(note_id)
    schedule = [{k: card.get(k) for k in ("cardId", "note", "deckName", "factor", "interval", "type", "queue", "due", "reps", "lapses", "left", "flags", "ord", "mod")} for card in cards]
    return {"note": note, "card_ids": card_ids, "cards": cards, "schedule": schedule, "reviews": reviews}

def note_fields(note: dict[str, Any]) -> dict[str, str]:
    return {name: str(value.get("value", "")) for name, value in (note.get("fields") or {}).items()}

def verify_note(note_id: int, fields: dict[str, str]) -> dict[str, Any]:
    snap = note_snapshot(note_id)
    note = snap["note"]
    if note.get("modelName") != MODEL or note_fields(note) != fields:
        raise SyncFailure("Anki note readback did not exactly match its NoteKey and field payload.")
    if not snap["card_ids"] or len(snap["card_ids"]) != len(snap["cards"]):
        raise SyncFailure("Anki did not return the expected card records for the note.")
    for card in snap["cards"]:
        if not str(card.get("question", "")).strip() or not str(card.get("answer", "")).strip():
            raise SyncFailure("Anki card front/back rendered blank.")
        if fields["English"].casefold() not in str(card.get("question", "")).casefold():
            raise SyncFailure("Anki card front does not render the English headword.")
        if fields["MeaningZH"] and fields["MeaningZH"] not in str(card.get("answer", "")):
            raise SyncFailure("Anki card back does not render the Chinese meaning.")
    return snap

def review_fingerprint(snapshot: dict[str, Any]) -> str:
    safe = {"card_ids": snapshot["card_ids"], "schedule": snapshot["schedule"], "reviews": snapshot["reviews"]}
    return sha256_text(json.dumps(safe, ensure_ascii=False, sort_keys=True, separators=(",", ":")))

def safe_error_text(error: Exception) -> str:
    if isinstance(error, SyncFailure):
        # SyncFailure texts are fixed, sanitized descriptions; no raw request or token data.
        return str(error)[:1800]
    return f"Unexpected {type(error).__name__}; details omitted to protect local data."

def update_card_page(notion: NotionClient, record: dict[str, Any], status: str, note_id: int | None = None, card_ids: list[int] | None = None, model: str | None = None, error: str = "") -> bool:
    properties: dict[str, Any] = {"Status": {"select": {"name": status}}, "Error": exact_rich_text_value(error)}
    if note_id is not None:
        properties["NoteID"] = exact_rich_text_value(str(note_id))
    if card_ids is not None:
        properties["CardIDs"] = exact_rich_text_value(json.dumps(card_ids, separators=(",", ":")))
    if model is not None:
        properties["Model"] = exact_rich_text_value(model)
    if status == "SYNCED":
        properties["SyncedAt"] = exact_rich_text_value(utc_now())
    try:
        notion.patch_page(record["page_id"], properties)
    except SyncFailure:
        # A write response can be ambiguous; read the exact page once, never blindly repeat.
        page = notion.get_page(record["page_id"])
        if page_value(page, "Status") == status and (note_id is None or str(page_value(page, "NoteID")) == str(note_id)) and page_value(page, "Error") == error:
            return True
        return False
    page = notion.get_page(record["page_id"])
    ok = page_value(page, "Status") == status and page_value(page, "Error") == error
    if note_id is not None:
        ok = ok and str(page_value(page, "NoteID")) == str(note_id)
    if card_ids is not None:
        ok = ok and page_value(page, "CardIDs") == json.dumps(card_ids, separators=(",", ":"))
    if model is not None:
        ok = ok and page_value(page, "Model") == model
    return ok

def note_tags(raw: str) -> list[str]:
    return [tag for tag in re.split(r"\s+", raw.strip()) if tag]

def duplicate_note_key(record: dict[str, Any]) -> list[dict[str, Any]]:
    return find_exact_notes("NoteKey", record["note_key"])

def exact_english_duplicates(fields: dict[str, str]) -> list[dict[str, Any]]:
    candidates = find_exact_notes("", fields["English"], any_field=True)
    target = normal_text(fields["English"])
    return [note for note in candidates if any(normal_text(v.get("value", "")) == target for v in (note.get("fields") or {}).values())]

def process_record(notion: NotionClient, conn: sqlite3.Connection, record: dict[str, Any], counts: dict[str, int]) -> str:
    counts["records_seen"] += 1
    key = record["note_key"]
    if record["parse_error"]:
        ok = update_card_page(notion, record, "ERROR", error=record["parse_error"])
        counts["errors"] += 1
        safe_log("card_error", note_key=key, reason="invalid_payload", notion_write_ok=ok)
        return "ERROR"
    try:
        fields = field_map(record)
    except Exception as exc:
        message = safe_error_text(exc)
        ok = update_card_page(notion, record, "ERROR", error=message)
        counts["errors"] += 1
        safe_log("card_error", note_key=key, reason="invalid_fields", notion_write_ok=ok)
        return "ERROR"
    revision = record.get("revision")
    if not isinstance(revision, int) or revision < 1:
        message = "Revision must be a positive integer."
        ok = update_card_page(notion, record, "ERROR", error=message)
        counts["errors"] += 1
        safe_log("card_error", note_key=key, reason="invalid_revision", notion_write_ok=ok)
        return "ERROR"
    if record["deck"] not in TARGET_DECKS:
        message = "Deck is not one of the two authorized IELTS target decks."
        ok = update_card_page(notion, record, "ERROR", error=message)
        counts["errors"] += 1
        safe_log("card_error", note_key=key, reason="unauthorized_deck", notion_write_ok=ok)
        return "ERROR"
    digest = payload_hash(fields)
    state = state_get(conn, key)
    matches = duplicate_note_key(record)
    if len(matches) > 1:
        message = "Multiple Anki notes have this NoteKey; none were modified."
        ok = update_card_page(notion, record, "CONFLICT", error=message)
        counts["conflicts"] += 1
        safe_log("card_conflict", note_key=key, reason="duplicate_note_key", notion_write_ok=ok)
        return "CONFLICT"
    if len(matches) == 1:
        found = matches[0]
        note_id = int(found["noteId"])
        found_fields = note_fields(found)
        if found.get("modelName") != MODEL or found_fields.get("NoteKey") != key or found_fields.get("English") != fields["English"]:
            message = "NoteKey matched but model/headword identity did not; no existing note was modified."
            ok = update_card_page(notion, record, "CONFLICT", error=message)
            counts["conflicts"] += 1
            safe_log("card_conflict", note_key=key, reason="identity_mismatch", notion_write_ok=ok)
            return "CONFLICT"
        if record["existing_note_id"] and record["existing_note_id"] != str(note_id):
            message = "Notion NoteID does not match the Anki note found by NoteKey; no note was modified."
            ok = update_card_page(notion, record, "CONFLICT", error=message)
            counts["conflicts"] += 1
            safe_log("card_conflict", note_key=key, reason="notion_note_id_mismatch", notion_write_ok=ok)
            return "CONFLICT"
        before = note_snapshot(note_id)
        if state and int(state["note_id"]) != note_id:
            message = "Local NoteKey state points to a different NoteID; no note was modified."
            ok = update_card_page(notion, record, "CONFLICT", error=message)
            counts["conflicts"] += 1
            safe_log("card_conflict", note_key=key, reason="local_note_id_mismatch", notion_write_ok=ok)
            return "CONFLICT"
        if state and revision > int(state["revision"]):
            if record["deck"] != state["deck"]:
                message = "Deck change detected for an existing note; automatic deck moves are disabled."
                ok = update_card_page(notion, record, "CONFLICT", error=message)
                counts["conflicts"] += 1
                safe_log("card_conflict", note_key=key, reason="deck_change", notion_write_ok=ok)
                return "CONFLICT"
            before_fingerprint = review_fingerprint(before)
            try:
                anki("updateNoteFields", {"note": note_id, "fields": fields})
            except SyncFailure as exc:
                after = note_snapshot(note_id)
                if note_fields(after["note"]) != fields:
                    message = "Anki update failed; existing note was not recreated. " + safe_error_text(exc)
                    ok = update_card_page(notion, record, "ERROR", error=message)
                    counts["errors"] += 1
                    safe_log("card_error", note_key=key, reason="update_api_error", notion_write_ok=ok)
                    return "ERROR"
            after = verify_note(note_id, fields)
            if after["card_ids"] != before["card_ids"] or review_fingerprint(after) != before_fingerprint:
                message = "Update readback detected a CardID/schedule/review-history change; automatic repair was not attempted."
                ok = update_card_page(notion, record, "CONFLICT", error=message)
                counts["conflicts"] += 1
                safe_log("card_conflict", note_key=key, reason="history_invariant_changed", notion_write_ok=ok)
                return "CONFLICT"
            state_put(conn, record, revision, digest, note_id, after["card_ids"], record["deck"])
            ok = update_card_page(notion, record, "SYNCED", note_id, after["card_ids"], MODEL)
            if not ok:
                counts["errors"] += 1
                safe_log("card_error", note_key=key, reason="notion_readback_failed_after_update", notion_write_ok=False)
                return "ERROR"
            counts["updated"] += 1
            safe_log("card_updated", note_key=key, note_id=note_id, card_count=len(after["card_ids"]))
            return "UPDATED"
        if note_fields(before["note"]) != fields:
            message = "Existing NoteKey note differs from payload but has no trusted local revision baseline; no overwrite occurred."
            ok = update_card_page(notion, record, "CONFLICT", error=message)
            counts["conflicts"] += 1
            safe_log("card_conflict", note_key=key, reason="no_revision_baseline", notion_write_ok=ok)
            return "CONFLICT"
        after = verify_note(note_id, fields)
        state_put(conn, record, revision, digest, note_id, after["card_ids"], record["deck"])
        ok = update_card_page(notion, record, "SYNCED", note_id, after["card_ids"], MODEL)
        if not ok:
            counts["errors"] += 1
            safe_log("card_error", note_key=key, reason="notion_readback_failed_after_adoption", notion_write_ok=False)
            return "ERROR"
        counts["skipped"] += 1
        safe_log("card_skipped", note_key=key, reason="already_exactly_synced", note_id=note_id)
        return "SKIPPED"

    # No NoteKey match. Never overwrite a text-only legacy note such as involve.
    exact_duplicates = exact_english_duplicates(fields)
    if exact_duplicates:
        ids = sorted(int(n.get("noteId")) for n in exact_duplicates if n.get("noteId") is not None)
        message = "Exact English field already exists in Anki note(s) " + ", ".join(map(str, ids)) + "; identity is unconfirmed, so this row was not imported."
        ok = update_card_page(notion, record, "CONFLICT", error=message)
        counts["conflicts"] += 1
        safe_log("card_conflict", note_key=key, reason="legacy_english_duplicate", legacy_note_ids=ids, notion_write_ok=ok)
        return "CONFLICT"
    note = {"deckName": record["deck"], "modelName": MODEL, "fields": fields, "tags": note_tags(record["tags"]), "options": {"allowDuplicate": False, "duplicateScope": "collection", "duplicateScopeOptions": {"checkAllModels": True, "checkChildren": False}}}
    validation = anki("canAddNoteWithErrorDetail", {"note": note}).get("result")
    if isinstance(validation, dict) and not validation.get("canAdd", False):
        reason = str(validation.get("reason") or "AnkiConnect validation rejected a possible duplicate.")
        status = "CONFLICT" if "duplicate" in reason.casefold() else "ERROR"
        ok = update_card_page(notion, record, status, error=reason[:1800])
        counts["conflicts" if status == "CONFLICT" else "errors"] += 1
        safe_log("card_validation_rejected", note_key=key, reason_type=status, notion_write_ok=ok)
        return status
    try:
        created_id = anki("addNote", {"note": note}).get("result")
    except SyncFailure as exc:
        # Resolve an ambiguous response via identity readback; never repeat addNote blindly.
        reread = duplicate_note_key(record)
        if len(reread) == 1 and reread[0].get("modelName") == MODEL and note_fields(reread[0]) == fields:
            created_id = int(reread[0]["noteId"])
        else:
            message = "Anki addNote failed or returned ambiguously; no retry was sent. " + safe_error_text(exc)
            ok = update_card_page(notion, record, "ERROR", error=message)
            counts["errors"] += 1
            safe_log("card_error", note_key=key, reason="add_api_error", notion_write_ok=ok)
            return "ERROR"
    if not isinstance(created_id, int) or created_id <= 0:
        message = "Anki addNote returned no valid NoteID."
        ok = update_card_page(notion, record, "ERROR", error=message)
        counts["errors"] += 1
        safe_log("card_error", note_key=key, reason="invalid_note_id", notion_write_ok=ok)
        return "ERROR"
    after = verify_note(created_id, fields)
    if after["note"].get("modelName") != MODEL:
        raise SyncFailure("New note model readback mismatch; note was retained, not deleted.")
    state_put(conn, record, revision, digest, created_id, after["card_ids"], record["deck"])
    ok = update_card_page(notion, record, "SYNCED", created_id, after["card_ids"], MODEL)
    if not ok:
        counts["errors"] += 1
        safe_log("card_error", note_key=key, reason="notion_readback_failed_after_create", note_id=created_id, notion_write_ok=False)
        return "ERROR"
    counts["created"] += 1
    safe_log("card_created", note_key=key, note_id=created_id, card_count=len(after["card_ids"]))
    return "CREATED"

def review_state_name(card: dict[str, Any]) -> str:
    labels = {-3: "suspended", -2: "buried", -1: "scheduler_buried", 0: "new", 1: "learning", 2: "review", 3: "day_learning", 4: "preview"}
    return labels.get(card.get("queue"), f"queue_{card.get('queue')}")

def review_events_for(review_map: dict[str, Any], card_id: int) -> list[dict[str, Any]]:
    return review_map.get(str(card_id), review_map.get(card_id, [])) or []

def review_raw(card: dict[str, Any], note_key: str, events: list[dict[str, Any]], fetched: str) -> str:
    return json.dumps({"card_id": card.get("cardId"), "note_id": card.get("note"), "note_key": note_key, "deck": card.get("deckName"), "queue": card.get("queue"), "type": card.get("type"), "due_raw": card.get("due"), "interval_days": card.get("interval"), "reps": card.get("reps"), "lapses": card.get("lapses"), "factor": card.get("factor"), "review_events": events, "fetched_at_utc": fetched}, ensure_ascii=False, separators=(",", ":"))

def review_properties(card: dict[str, Any], note_key: str, events: list[dict[str, Any]], fetched: str) -> dict[str, Any]:
    card_id = int(card["cardId"])
    note_id = int(card["note"])
    factor = card.get("factor")
    ease_factor = float(factor) / 1000.0 if isinstance(factor, (int, float)) and factor > 10 else factor
    last_review = ""
    if events:
        try:
            last_id = max(int(event.get("id", 0)) for event in events)
            if last_id > 0:
                last_review = dt.datetime.fromtimestamp(last_id / 1000, dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
        except Exception:
            last_review = ""
    raw = review_raw(card, note_key, events, fetched)
    if len(raw) > 190000:
        compact_events = events[-250:]
        raw = json.dumps({"card_id": card_id, "note_id": note_id, "note_key": note_key, "deck": card.get("deckName"), "reps": card.get("reps"), "lapses": card.get("lapses"), "interval_days": card.get("interval"), "due_raw": card.get("due"), "review_event_count": len(events), "review_events_last_250": compact_events, "truncated_for_notion_property_limit": True, "fetched_at_utc": fetched}, ensure_ascii=False, separators=(",", ":"))
    name = f"Card {card_id} · {note_key}"
    return {
        "Name": {"title": [{"type": "text", "text": {"content": name[:1900]}}]},
        "CardID": exact_rich_text_value(str(card_id)),
        "NoteID": exact_rich_text_value(str(note_id)),
        "NoteKey": exact_rich_text_value(note_key),
        "Reps": {"number": int(card.get("reps") or 0)},
        "Lapses": {"number": int(card.get("lapses") or 0)},
        "AgainCount": {"number": sum(1 for event in events if event.get("ease") == 1)},
        "EaseFactor": {"number": ease_factor if isinstance(ease_factor, (int, float)) else None},
        "IntervalDays": {"number": int(card.get("interval") or 0)},
        "Due": exact_rich_text_value(str(card.get("due", ""))),
        "Deck": exact_rich_text_value(str(card.get("deckName", ""))),
        "CardState": exact_rich_text_value(review_state_name(card)),
        "FetchedAtUTC": exact_rich_text_value(fetched),
        "LastReviewUTC": exact_rich_text_value(last_review),
        "RawJSON": exact_rich_text_value(raw),
    }

def existing_reviews(notion: NotionClient) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for page in notion.query_all(REVIEWS_DS):
        card_id = str(page_value(page, "CardID") or "").strip()
        if card_id:
            grouped.setdefault(card_id, []).append(page)
    return grouped

def review_page_matches(page: dict[str, Any], expected: dict[str, Any]) -> bool:
    for name in ("CardID", "NoteID", "NoteKey", "Reps", "Lapses", "AgainCount", "EaseFactor", "IntervalDays", "Due", "Deck", "CardState", "LastReviewUTC"):
        expected_value = expected[name]
        expected_type = next(iter(expected_value))
        expected_value = expected_value[expected_type]
        if isinstance(expected_value, list):
            expected_text = "".join(x.get("text", {}).get("content", "") for x in expected_value)
        elif isinstance(expected_value, dict):
            expected_text = expected_value.get("name")
        else:
            expected_text = expected_value
        actual = page_value(page, name)
        if actual != expected_text:
            return False
    return True

def upsert_review(notion: NotionClient, db_id: str, grouped: dict[str, list[dict[str, Any]]], card: dict[str, Any], note_key: str, events: list[dict[str, Any]], counts: dict[str, int]) -> None:
    card_id = str(card.get("cardId"))
    properties = review_properties(card, note_key, events, utc_now())
    matches = grouped.get(card_id, [])
    if len(matches) > 1:
        counts["review_conflicts"] += 1
        safe_log("review_conflict", card_id=card_id, reason="duplicate_review_rows")
        return
    if len(matches) == 1:
        page_id = matches[0]["id"]
        try:
            notion.patch_page(page_id, properties)
        except SyncFailure:
            page = notion.get_page(page_id)
            if not review_page_matches(page, properties):
                counts["review_errors"] += 1
                safe_log("review_error", card_id=card_id, reason="update_notion_failed")
                return
        else:
            page = notion.get_page(page_id)
            if not review_page_matches(page, properties):
                counts["review_errors"] += 1
                safe_log("review_error", card_id=card_id, reason="update_readback_mismatch")
                return
        # RawJSON is verified by the Anki source read above; check its identity fields too.
        if str(page_value(page, "RawJSON") or "").find('"card_id":' + card_id) < 0:
            counts["review_errors"] += 1
            safe_log("review_error", card_id=card_id, reason="raw_json_readback_mismatch")
            return
        counts["review_updated"] += 1
        safe_log("review_updated", card_id=card_id)
        return
    try:
        created = notion.create_page(db_id, properties)
        page_id = created.get("id")
        if not page_id:
            raise SyncFailure("Notion review create returned no page ID.")
        page = notion.get_page(page_id)
    except SyncFailure:
        # The write may have committed despite a lost response; search the existing DB once.
        after = existing_reviews(notion).get(card_id, [])
        if len(after) == 1 and review_page_matches(after[0], properties):
            grouped[card_id] = after
            counts["review_created"] += 1
            safe_log("review_created", card_id=card_id, recovered_by_readback=True)
            return
        counts["review_errors"] += 1
        safe_log("review_error", card_id=card_id, reason="create_notion_failed_no_retry")
        return
    if not review_page_matches(page, properties) or str(page_value(page, "RawJSON") or "").find('"card_id":' + card_id) < 0:
        counts["review_errors"] += 1
        safe_log("review_error", card_id=card_id, reason="create_readback_mismatch")
        return
    grouped[card_id] = [page]
    counts["review_created"] += 1
    safe_log("review_created", card_id=card_id)

def sync_reviews(notion: NotionClient, conn: sqlite3.Connection, counts: dict[str, int]) -> None:
    note_ids = anki("findNotes", {"query": f"note:{MODEL}"}).get("result") or []
    notes = anki("notesInfo", {"notes": note_ids}).get("result") or [] if note_ids else []
    if not notes:
        return
    card_map: dict[str, str] = {}
    all_card_ids: list[int] = []
    for note in notes:
        key = note_fields(note).get("NoteKey", "")
        if not key:
            continue
        card_ids = anki("findCards", {"query": f"nid:{int(note['noteId'])}"}).get("result") or []
        for card_id in card_ids:
            card_map[str(card_id)] = key
            all_card_ids.append(int(card_id))
    if not all_card_ids:
        return
    card_infos = anki("cardsInfo", {"cards": all_card_ids}).get("result") or []
    review_map = anki("getReviewsOfCards", {"cards": all_card_ids}).get("result") or {}
    schemas = notion.schema(REVIEWS_DS)
    database_id = (schemas.get("parent") or {}).get("database_id")
    if not database_id:
        raise SyncFailure("The existing Reviews database ID could not be determined.")
    grouped = existing_reviews(notion)
    fetched = utc_now()
    for card in card_infos:
        card_id = int(card["cardId"])
        note_key = card_map.get(str(card_id), "")
        if not note_key:
            continue
        events = review_events_for(review_map, card_id)
        before_hash = sha256_text(review_raw(card, note_key, events, ""))
        try:
            upsert_review(notion, database_id, grouped, card, note_key, events, counts)
            conn.execute("INSERT INTO review_state(card_id,page_id,raw_hash,updated_at) VALUES(?,?,?,?) ON CONFLICT(card_id) DO UPDATE SET page_id=excluded.page_id,raw_hash=excluded.raw_hash,updated_at=excluded.updated_at", (str(card_id), (grouped.get(str(card_id)) or [{}])[0].get("id", ""), before_hash, fetched))
            counts["reviews_seen"] += 1
        except Exception as exc:
            counts["review_errors"] += 1
            safe_log("review_error", card_id=str(card_id), reason=type(exc).__name__)
            continue

def sync_log(notion: NotionClient, run_id: str, started: str, counts: dict[str, int]) -> bool:
    schema = notion.schema(LOG_DS)
    database_id = (schema.get("parent") or {}).get("database_id")
    if not database_id:
        return False
    notes = (f"Cards: created={counts['created']}, updated={counts['updated']}, skipped={counts['skipped']}, conflicts={counts['conflicts']}, errors={counts['errors']}. "
             f"Reviews: created={counts['review_created']}, updated={counts['review_updated']}, conflicts={counts['review_conflicts']}, errors={counts['review_errors']}; seen={counts['reviews_seen']}.")
    props = {
        "Name": {"title": [{"type": "text", "text": {"content": f"Anki sync {started}"}}]},
        "TimeUTC": exact_rich_text_value(started),
        "Direction": exact_rich_text_value("Bidirectional"),
        "RunID": exact_rich_text_value(run_id),
        "Created": {"number": counts["created"]},
        "Updated": {"number": counts["updated"]},
        "Skipped": {"number": counts["skipped"]},
        "Failed": {"number": counts["errors"] + counts["conflicts"] + counts["review_errors"] + counts["review_conflicts"]},
        "RecordsSeen": {"number": counts["records_seen"]},
        "Notes": exact_rich_text_value(notes),
    }
    try:
        created = notion.create_page(database_id, props)
        if not created.get("id"):
            raise SyncFailure("Sync Log create returned no page ID.")
        check = notion.get_page(created["id"])
        return page_value(check, "RunID") == run_id and page_value(check, "Direction") == "Bidirectional"
    except SyncFailure:
        # Check this unique RunID once; do not repeat the create blindly.
        for page in notion.query_all(LOG_DS):
            if page_value(page, "RunID") == run_id:
                return page_value(page, "Direction") == "Bidirectional"
        return False

def main() -> int:
    parser = argparse.ArgumentParser(description="On-demand bidirectional Notion ↔ Anki IELTS sync")
    parser.add_argument("--first-safe-test", action="store_true", help="Sync one conflict-free PENDING row only")
    parser.add_argument("--cards-only", action="store_true", help="Do not run the Reviews return sync")
    parser.add_argument("--reviews-only", action="store_true", help="Only upsert Anki review/card state to Notion")
    args = parser.parse_args()
    CACHE.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(filename=LOG_PATH, level=logging.INFO, format="%(message)s", encoding="utf-8")
    run_id = str(uuid.uuid4())
    started = utc_now()
    counts = {k: 0 for k in ("records_seen", "created", "updated", "skipped", "errors", "conflicts", "review_created", "review_updated", "review_errors", "review_conflicts", "reviews_seen")}
    token = load_notion_token()
    notion = NotionClient(token)
    # Verify only the existing scoped objects; never create a database.
    _, _schemas = verify_runtime(notion)
    cards = sorted_records(parse_card_rows(notion))
    key_counts: dict[str, int] = {}
    for record in cards:
        key_counts[record["note_key"]] = key_counts.get(record["note_key"], 0) + 1
    conn = sqlite3.connect(STATE_PATH, timeout=60, isolation_level=None)
    try:
        conn.execute("PRAGMA busy_timeout=60000")
        conn.execute("BEGIN IMMEDIATE")  # Serializes competing invocations for the entire run.
        init_state(conn)
        conn.execute("INSERT OR REPLACE INTO runs(run_id,started_at) VALUES(?,?)", (run_id, started))
        if not args.reviews_only:
            pending = [r for r in cards if r["status"] == "PENDING"]
            # Allow already-SYNCED rows to update only when a recorded revision has increased.
            for record in cards:
                state = state_get(conn, record["note_key"]) if record.get("note_key") else None
                if record["status"] == "SYNCED" and state and isinstance(record.get("revision"), int) and record["revision"] > int(state["revision"]):
                    pending.append(record)
            if args.first_safe_test:
                eligible = []
                for record in sorted_records(pending):
                    if record.get("parse_error") or key_counts.get(record.get("note_key"), 0) != 1:
                        continue
                    try:
                        fields = field_map(record)
                    except Exception:
                        continue
                    if record.get("deck") not in TARGET_DECKS:
                        continue
                    if duplicate_note_key(record):
                        continue
                    if exact_english_duplicates(fields):
                        continue
                    eligible.append(record)
                    break
                if not eligible:
                    raise SyncFailure("No conflict-free PENDING row is available for the safe pilot test.")
                selected = eligible
            else:
                selected = sorted_records(pending)
            # Enforce the existing full-backup gate before the first add/update.
            bootstrap_done = conn.execute("SELECT 1 FROM notes LIMIT 1").fetchone() is not None
            if selected and not bootstrap_done:
                if not BACKUP_PATH.is_file():
                    raise SyncFailure("Verified full .colpkg backup is missing; no card writes were attempted.")
                digest = hashlib.sha256(BACKUP_PATH.read_bytes()).hexdigest()
                if digest != EXPECTED_BACKUP_SHA256:
                    raise SyncFailure("Full .colpkg backup fingerprint changed; no card writes were attempted.")
                with zipfile.ZipFile(BACKUP_PATH) as archive:
                    if archive.testzip() is not None or not {"meta", "collection.anki21b", "media"}.issubset(set(archive.namelist())):
                        raise SyncFailure("Full .colpkg backup integrity check failed; no card writes were attempted.")
            for record in selected:
                if key_counts.get(record.get("note_key", ""), 0) != 1:
                    message = "Duplicate NoteKey exists in the Cards database; no note was created or updated."
                    try:
                        ok = update_card_page(notion, record, "CONFLICT", error=message)
                    except Exception:
                        ok = False
                    counts["records_seen"] += 1; counts["conflicts"] += 1
                    safe_log("card_conflict", note_key=record.get("note_key", ""), reason="duplicate_notion_note_key", notion_write_ok=ok)
                    continue
                try:
                    process_record(notion, conn, record, counts)
                except Exception as exc:
                    message = safe_error_text(exc)
                    try:
                        ok = update_card_page(notion, record, "ERROR", error=message)
                    except Exception:
                        ok = False
                    counts["errors"] += 1
                    safe_log("card_error", note_key=record.get("note_key", ""), reason=type(exc).__name__, notion_write_ok=ok)
        if not args.cards_only:
            sync_reviews(notion, conn, counts)
        try:
            log_ok = sync_log(notion, run_id, started, counts)
        except Exception as exc:
            log_ok = False
            safe_log("sync_log_error", run_id=run_id, reason=type(exc).__name__)
        finished = utc_now()
        summary = {"run_id": run_id, "started_at_utc": started, "finished_at_utc": finished, "counts": counts, "sync_log_verified": log_ok, "mode": "reviews-only" if args.reviews_only else ("first-safe-test" if args.first_safe_test else "bidirectional")}
        conn.execute("UPDATE runs SET finished_at=?,summary_json=? WHERE run_id=?", (finished, json.dumps(summary, ensure_ascii=False), run_id))
        conn.commit()
        safe_log("run_complete", run_id=run_id, created=counts["created"], updated=counts["updated"], skipped=counts["skipped"], errors=counts["errors"], conflicts=counts["conflicts"], review_created=counts["review_created"], review_updated=counts["review_updated"], sync_log_verified=log_ok)
        print(json.dumps(summary, ensure_ascii=False))
        return 0 if log_ok and counts["errors"] == 0 and counts["review_errors"] == 0 else 2
    finally:
        try:
            if conn.in_transaction:
                conn.rollback()
        finally:
            conn.close()

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SyncFailure as exc:
        print(json.dumps({"status": "blocked", "reason": str(exc)}, ensure_ascii=False), file=sys.stderr)
        raise SystemExit(2)
    except Exception as exc:
        # Do not expose raw exception text, which might include request or local data.
        print(json.dumps({"status": "error", "reason": type(exc).__name__}, ensure_ascii=False), file=sys.stderr)
        raise SystemExit(3)
