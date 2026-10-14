from __future__ import annotations

import base64
import hashlib
import importlib.util
import json
import re
import sqlite3
import sys
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BRIDGE_PATH = Path(r"C:\Users\Admin\AppData\Local\hermes\scripts\anki_notion_sync.py")
ROOT = Path(r"C:\Users\Admin\AppData\Local\hermes\memories\脚本缓存\anki-audio-repair")
ASSET_AUDIT = ROOT / "batch_audio_repair_audit_attempt1.json"
REPORT = ROOT / "audio_repair_reconciliation_audit.json"
BACKUP = Path(r"C:\Users\Admin\Documents\AnkiBackups\Anki_collection_2026-10-14_before_audio_repair.colpkg")
TARGET_MODEL = "IELTS_Vocabulary_v1"

spec = importlib.util.spec_from_file_location("anki_audio_reconcile_bridge", BRIDGE_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("Cannot load existing Anki–Notion bridge")
bridge = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = bridge
spec.loader.exec_module(bridge)


class SafetyStop(RuntimeError):
    pass


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def save_report(report: dict[str, Any]) -> None:
    temp = REPORT.with_suffix(".tmp")
    temp.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(REPORT)


def payload_from_page(page: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    raw = str(bridge.page_value(page, "PayloadJSON") or "").strip()
    prefix = "json:" if raw.startswith("json:") else ""
    if prefix:
        raw = raw[5:].lstrip()
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise SafetyStop("Notion PayloadJSON is not an object")
    return prefix, value


def media_bytes(filename: str) -> bytes | None:
    result = bridge.anki("retrieveMediaFile", {"filename": filename}).get("result")
    if result is False or result is None or result == "":
        return None
    if not isinstance(result, str):
        raise SafetyStop("retrieveMediaFile returned an unexpected type")
    try:
        return base64.b64decode(result, validate=True)
    except Exception as exc:
        raise SafetyStop("retrieveMediaFile returned invalid base64") from exc


def main() -> int:
    check = lambda ok, msg: (_ for _ in ()).throw(SafetyStop(msg)) if not ok else None
    if not ASSET_AUDIT.is_file():
        raise SafetyStop("The completed 99-file media audit is missing")
    previous = json.loads(ASSET_AUDIT.read_text(encoding="utf-8"))
    assets = {str(x.get("NoteKey")): x for x in previous.get("items", []) if x.get("NoteKey")}
    if len(assets) != 99 or len({x.get("filename") for x in assets.values()}) != 99:
        raise SafetyStop("The prior media audit does not contain 99 unique assets")
    for key, item in assets.items():
        check(item.get("generated_mp3") is True, f"No verified generated MP3 for {key}")
        check(item.get("anki_media_store") == "verified", f"storeMediaFile was not verified for {key}")
        check(item.get("anki_media_retrieve_sha256") == item.get("sha256"), f"Prior media readback hash mismatch for {key}")
        check(item.get("ffprobe_ok") and item.get("full_decode_ok") and float(item.get("non_silent_rms_s16") or 0) >= 150, f"File-level audio checks missing for {key}")

    if not BACKUP.is_file() or sha(BACKUP.read_bytes()) != bridge.EXPECTED_BACKUP_SHA256:
        raise SafetyStop("The verified pre-repair Anki backup does not match its recorded hash")
    with zipfile.ZipFile(BACKUP) as zf:
        if zf.testzip() is not None or not {"meta", "collection.anki21b", "media"}.issubset(set(zf.namelist())):
            raise SafetyStop("The pre-repair backup failed archive validation")

    notion = bridge.NotionClient(bridge.load_notion_token())
    bridge.verify_runtime(notion)
    records = bridge.parse_card_rows(notion)
    targets = bridge.sorted_records([x for x in records if x.get("status") == "SYNCED"])
    conflicts = [x for x in records if x.get("status") == "CONFLICT"]
    if len(records) != 100 or len(targets) != 99 or len(conflicts) != 1:
        raise SafetyStop(f"Expected 100 rows (99 SYNCED + 1 CONFLICT); found {len(records)}, {len(targets)}, {len(conflicts)}")
    conflict_fields = bridge.field_map(conflicts[0])
    if conflict_fields.get("English", "").strip().casefold() != "involve":
        raise SafetyStop("The sole CONFLICT row is not involve; refusing to proceed")

    all_ids = bridge.anki("findNotes", {"query": ""}).get("result") or []
    all_notes = bridge.anki("notesInfo", {"notes": all_ids}).get("result") or []
    notes_by_key: dict[str, list[dict[str, Any]]] = {}
    for note in all_notes:
        if note.get("modelName") == TARGET_MODEL:
            note_fields = bridge.note_fields(note)
            notes_by_key.setdefault(note_fields.get("NoteKey", ""), []).append(note)
    if sum(1 for n in all_notes if n.get("modelName") == TARGET_MODEL) != 99:
        raise SafetyStop("IELTS model note count changed from 99")

    baseline: dict[str, dict[str, Any]] = {}
    for row in targets:
        key = row["note_key"]
        check(key in assets, f"No audited MP3 asset maps to NoteKey {key}")
        check(len(notes_by_key.get(key, [])) == 1, f"Anki NoteKey is not unique for {key}")
        note = notes_by_key[key][0]
        f = bridge.field_map(row)
        nf = bridge.note_fields(note)
        nid = int(note["noteId"])
        card_ids = [int(c) for c in (note.get("cards") or [])]
        notion_card_ids = [int(c) for c in json.loads(row.get("existing_card_ids") or "[]")]
        check(note.get("modelName") == TARGET_MODEL and nf.get("English") == f["English"] and nf.get("NoteKey") == key, f"Anki identity or English mismatch for {key}")
        check(str(row.get("existing_note_id")) == str(nid) and set(card_ids) == set(notion_card_ids), f"Notion NoteID/CardIDs mismatch for {key}")
        asset = assets[key]
        check(asset.get("English") == f["English"] and int(asset.get("NoteID")) == nid, f"Audited audio text/NoteID mismatch for {key}")
        snap = bridge.note_snapshot(nid)
        baseline[key] = {"note_id": nid, "card_ids": card_ids, "snapshot": snap, "fields": nf, "asset": asset}

    report: dict[str, Any] = {
        "run_id": str(uuid.uuid4()),
        "started_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "asset_audit_source": str(ASSET_AUDIT),
        "asset_audit_sha256": sha(ASSET_AUDIT.read_bytes()),
        "backup_sha256_verified": bridge.EXPECTED_BACKUP_SHA256,
        "scope": {"rows": 100, "synced_targets": 99, "conflict_excluded": conflict_fields["English"]},
        "items": [],
        "cloud_sync": {"status": "NOT_RUN", "collectionComplete": False, "mediaComplete": False},
    }
    save_report(report)

    conn = sqlite3.connect(bridge.STATE_PATH, timeout=120, isolation_level=None)
    conn.execute("PRAGMA busy_timeout=120000")
    committed = False
    try:
        conn.execute("BEGIN IMMEDIATE")
        bridge.init_state(conn)
        run_id = "audio-reconcile-" + report["run_id"]
        conn.execute("INSERT INTO runs(run_id,started_at) VALUES(?,?)", (run_id, report["started_at_utc"]))
        report["state_lock_acquired"] = True
        report["stale_run_records_preserved"] = [{"run_id": r[0], "started_at": r[1]} for r in conn.execute("SELECT run_id,started_at FROM runs WHERE run_id<>? AND finished_at IS NULL", (run_id,)).fetchall()]
        save_report(report)

        for row in targets:
            key = row["note_key"]
            asset = assets[key]
            nid = baseline[key]["note_id"]
            expected_ref = f"[sound:{asset['filename']}]"
            item: dict[str, Any] = {
                "NoteKey": key, "English": row["payload"].get("English", ""), "NoteID": nid,
                "CardIDs": baseline[key]["card_ids"], "filename": asset["filename"],
                "generated_mp3": True, "source_kind": asset.get("source_kind"), "voice_model": asset.get("voice_model"),
                "duration_seconds": asset.get("duration_seconds"), "bytes": asset.get("bytes"), "sha256": asset.get("sha256"),
                "ffprobe_ok": asset.get("ffprobe_ok"), "full_decode_ok": asset.get("full_decode_ok"),
                "non_silent_rms_s16": asset.get("non_silent_rms_s16"),
            }
            report["items"].append(item)
            save_report(report)
            try:
                raw_media = media_bytes(asset["filename"])
                if raw_media is None or sha(raw_media) != asset["sha256"] or len(raw_media) != int(asset["bytes"]):
                    raise SafetyStop(f"Anki media readback hash/size mismatch for {key}")
                before = bridge.note_snapshot(nid)
                before_fields = bridge.note_fields(before["note"])
                if before_fields.get("NoteKey") != key or before_fields.get("English") != row["payload"].get("English"):
                    raise SafetyStop(f"Anki identity/English changed before update for {key}")
                if before["card_ids"] != baseline[key]["card_ids"] or bridge.review_fingerprint(before) != bridge.review_fingerprint(baseline[key]["snapshot"]):
                    raise SafetyStop(f"CardIDs or review schedule changed before update for {key}")
                current_audio = before_fields.get("Audio", "").strip()
                if current_audio and current_audio != expected_ref:
                    raise SafetyStop(f"Anki Audio already has a different value for {key}; refusing overwrite")
                if not current_audio:
                    try:
                        bridge.anki("updateNoteFields", {"note": {"id": nid, "fields": {"Audio": expected_ref}}})
                    except Exception:
                        ambiguous = bridge.note_snapshot(nid)
                        if bridge.note_fields(ambiguous["note"]).get("Audio", "") != expected_ref:
                            raise RuntimeError("updateNoteFields failed and readback did not confirm the Audio value")
                after = bridge.note_snapshot(nid)
                after_fields = bridge.note_fields(after["note"])
                if after_fields.get("Audio", "") != expected_ref:
                    raise RuntimeError("Anki Audio readback mismatch")
                if {k: v for k, v in after_fields.items() if k != "Audio"} != {k: v for k, v in before_fields.items() if k != "Audio"}:
                    raise SafetyStop(f"A non-Audio Anki field changed for {key}")
                if after["card_ids"] != before["card_ids"] or bridge.review_fingerprint(after) != bridge.review_fingerprint(before):
                    raise SafetyStop(f"CardIDs or schedule/review data changed for {key}")
                item["anki_media_retrieve_sha256"] = sha(raw_media)
                item["anki_audio_field_readback"] = "verified"
                item["NoteID_preserved"] = True
                item["CardIDs_preserved"] = True
                item["schedule_and_review_preserved"] = True

                notion_audio = str(row["payload"].get("Audio") or "").strip()
                if notion_audio and notion_audio != expected_ref:
                    raise SafetyStop(f"Notion Audio already has a different value for {key}; refusing overwrite")
                revision_after = int(row["revision"])
                if not notion_audio:
                    page = notion.get_page(row["page_id"])
                    prefix, payload_now = payload_from_page(page)
                    if payload_now != row["payload"] or bridge.page_value(page, "Status") != "SYNCED" or str(bridge.page_value(page, "NoteID")) != str(nid):
                        raise SafetyStop(f"Notion record changed concurrently for {key}")
                    cards_now = [int(c) for c in json.loads(str(bridge.page_value(page, "CardIDs") or "[]"))]
                    if cards_now != after["card_ids"]:
                        raise SafetyStop(f"Notion CardIDs changed concurrently for {key}")
                    revision_now = int(bridge.page_value(page, "Revision"))
                    if revision_now != int(row["revision"]):
                        raise SafetyStop(f"Notion Revision changed concurrently for {key}")
                    payload_now["Audio"] = expected_ref
                    revision_after = revision_now + 1
                    serialized = prefix + json.dumps(payload_now, ensure_ascii=False, separators=(",", ":"))
                    try:
                        notion.patch_page(row["page_id"], {"PayloadJSON": bridge.exact_rich_text_value(serialized), "Revision": {"number": revision_after}})
                    except Exception:
                        pass  # Resolve an ambiguous PATCH by exact readback; never blindly resend.
                    page_after = notion.get_page(row["page_id"])
                    _, payload_after = payload_from_page(page_after)
                    if payload_after.get("Audio") != expected_ref or int(bridge.page_value(page_after, "Revision")) != revision_after or bridge.page_value(page_after, "Status") != "SYNCED":
                        raise RuntimeError("Notion Audio/Revision/Status readback mismatch")
                    if str(bridge.page_value(page_after, "NoteID")) != str(nid) or [int(c) for c in json.loads(str(bridge.page_value(page_after, "CardIDs") or "[]"))] != after["card_ids"]:
                        raise SafetyStop(f"Notion NoteID/CardIDs changed during patch for {key}")
                    row["payload"] = payload_now
                    row["revision"] = revision_after
                else:
                    item["notion_audio_already_present"] = True
                digest = bridge.payload_hash(bridge.field_map(row))
                bridge.state_put(conn, row, revision_after, digest, nid, after["card_ids"], row["deck"])
                item["Notion_Audio_readback"] = "verified"
                item["Revision_after"] = revision_after
                item["Status_after"] = "SYNCED"
                item["local_state_mapping"] = "verified/updated"
                item["result"] = "SUCCESS"
            except SafetyStop as exc:
                item["result"] = "SAFETY_STOP"
                item["failure_reason"] = str(exc)[:300]
                save_report(report)
                raise
            except Exception as exc:
                item["result"] = "FAILED"
                item["failure_reason"] = f"{type(exc).__name__}: {str(exc)[:240]}"
            save_report(report)

        success = sum(x.get("result") == "SUCCESS" for x in report["items"])
        counts = {"records_seen": len(targets), "updated": success, "errors": len(targets) - success, "cloud_sync_status": "NOT_RUN", "cloud_sync_error_code": "", "cloud_sync_collection_complete": False, "cloud_sync_media_complete": False}
        cloud_ok = bridge.sync_ankiweb(counts)
        report["cloud_sync"] = {
            "status": counts.get("cloud_sync_status"),
            "collectionComplete": counts.get("cloud_sync_collection_complete"),
            "mediaComplete": counts.get("cloud_sync_media_complete"),
            "error_code": counts.get("cloud_sync_error_code"),
            "operation_required_user_choice": counts.get("cloud_sync_status") == "CONFLICT",
        }
        report["summary"] = {
            "generated_mp3": sum(x.get("generated_mp3") is True for x in report["items"]),
            "anki_audio_fields_verified": success,
            "notion_audio_fields_verified": sum(x.get("Notion_Audio_readback") == "verified" for x in report["items"]),
            "failed": len(targets) - success,
            "conflict_excluded": len(conflicts),
        }
        report["finished_at_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
        conn.execute("UPDATE runs SET finished_at=?,summary_json=? WHERE run_id=?", (report["finished_at_utc"], json.dumps(report["summary"], ensure_ascii=False), run_id))
        conn.commit()
        committed = True
        save_report(report)
        print(json.dumps({"status": "complete", "report_path": str(REPORT), "summary": report["summary"], "cloud_sync": report["cloud_sync"]}, ensure_ascii=False))
        return 0 if cloud_ok and report["summary"]["failed"] == 0 else 2
    finally:
        if not committed and conn.in_transaction:
            conn.rollback()
        conn.close()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"status": "blocked_or_error", "reason": f"{type(exc).__name__}: {str(exc)[:500]}", "report_path": str(REPORT)}, ensure_ascii=False), file=sys.stderr)
        raise SystemExit(3)
