from __future__ import annotations

import array
import base64
import hashlib
import importlib.util
import json
import math
import re
import sqlite3
import subprocess
import sys
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BRIDGE_PATH = Path(r"C:\Users\Admin\AppData\Local\hermes\scripts\anki_notion_sync.py")
ROOT = Path(r"C:\Users\Admin\AppData\Local\hermes\memories\脚本缓存\anki-audio-repair")
ASSET_AUDIT = ROOT / "batch_audio_repair_audit_attempt1.json"
CURRENT_AUDIT = ROOT / "batch_audio_repair_audit.json"
REPORT = ROOT / "audio_repair_reconciliation_audit_v2.json"
BACKUP = Path(r"C:\Users\Admin\Documents\AnkiBackups\Anki_collection_2026-10-14_before_audio_repair.colpkg")
TARGET_MODEL = "IELTS_Vocabulary_v1"

spec = importlib.util.spec_from_file_location("anki_audio_reconcile_bridge_v2", BRIDGE_PATH)
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
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


def require(cond: bool, message: str) -> None:
    if not cond:
        raise SafetyStop(message)


def payload_from_page(page: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    raw = str(bridge.page_value(page, "PayloadJSON") or "").strip()
    prefix = "json:" if raw.startswith("json:") else ""
    if prefix:
        raw = raw[5:].lstrip()
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise SafetyStop("Notion PayloadJSON is not an object")
    return prefix, payload


def media_bytes(filename: str) -> bytes | None:
    value = bridge.anki("retrieveMediaFile", {"filename": filename}).get("result")
    if value is False or value is None or value == "":
        return None
    if not isinstance(value, str):
        raise SafetyStop("retrieveMediaFile returned an unexpected type")
    try:
        return base64.b64decode(value, validate=True)
    except Exception as exc:
        raise SafetyStop("retrieveMediaFile returned invalid base64") from exc


def validate_unknown_variant(filename: str, data: bytes) -> dict[str, Any]:
    ffmpeg = shutil_which("ffmpeg")
    ffprobe = shutil_which("ffprobe")
    if not ffmpeg or not ffprobe:
        raise SafetyStop("FFmpeg/FFprobe unavailable to verify an interrupted audio variant")
    temp = ROOT / "work" / "resume_verify" / filename
    temp.parent.mkdir(parents=True, exist_ok=True)
    temp.write_bytes(data)
    probe = subprocess.run([ffprobe, "-v", "error", "-show_entries", "format=duration:stream=codec_name", "-of", "json", str(temp)], capture_output=True, text=True, timeout=45)
    if probe.returncode:
        raise SafetyStop("FFprobe rejected an interrupted audio variant")
    meta = json.loads(probe.stdout)
    streams = meta.get("streams") or []
    duration = float((meta.get("format") or {}).get("duration") or 0)
    if not streams or streams[0].get("codec_name") != "mp3" or not 0.2 < duration < 90:
        raise SafetyStop("Interrupted audio variant has invalid MP3 codec/duration")
    dec = subprocess.run([ffmpeg, "-v", "error", "-i", str(temp), "-f", "null", "-"], capture_output=True, timeout=90)
    pcm = subprocess.run([ffmpeg, "-v", "error", "-i", str(temp), "-f", "s16le", "-ac", "1", "-ar", "16000", "-"], capture_output=True, timeout=90)
    if dec.returncode or pcm.returncode or not pcm.stdout or len(pcm.stdout) % 2:
        raise SafetyStop("Interrupted audio variant failed complete decode")
    samples = array.array("h")
    samples.frombytes(pcm.stdout)
    if sys.byteorder != "little":
        samples.byteswap()
    rms = math.sqrt(sum(int(v) * int(v) for v in samples) / max(1, len(samples)))
    peak = max((abs(int(v)) for v in samples), default=0)
    if rms < 150 or peak < 500:
        raise SafetyStop("Interrupted audio variant is silent")
    return {"ffprobe_ok": True, "full_decode_ok": True, "duration_seconds": round(duration, 5), "non_silent_rms_s16": round(rms, 2), "sha256": sha(data), "bytes": len(data)}


def shutil_which(name: str) -> str | None:
    import shutil
    return shutil.which(name)


def validate_reference(ref: str, key: str, english: str, initial: dict[str, Any], current: dict[str, Any] | None, model_sha: str) -> tuple[str, bytes, dict[str, Any]]:
    match = re.fullmatch(r"\[sound:([^\]]+)\]", ref)
    if not match:
        raise SafetyStop(f"Audio value is not a single sound reference for {key}")
    filename = match.group(1)
    safe_key = re.sub(r"[^A-Za-z0-9_-]+", "_", key).strip("_") or "note"
    english_sha = hashlib.sha256(english.encode("utf-8")).hexdigest()[:10]
    prefix = f"ielts_piper_en_gb_{safe_key}_{english_sha}_{model_sha[:8]}"
    if filename != prefix + ".mp3" and not re.fullmatch(re.escape(prefix) + r"_[0-9a-f]{10}\.mp3", filename):
        raise SafetyStop(f"Audio filename is not the verified Piper asset for {key}")
    data = media_bytes(filename)
    if data is None:
        raise SafetyStop(f"Anki media file is missing for {key}")
    digest = sha(data)
    known: dict[str, dict[str, Any]] = {}
    for asset in (initial, current):
        if asset and asset.get("filename"):
            known[str(asset["filename"])] = asset
    if filename in known:
        asset = known[filename]
        if digest != asset.get("sha256") or len(data) != int(asset.get("bytes") or -1):
            raise SafetyStop(f"Media bytes differ from the recorded audit for {key}")
        metrics = {k: asset.get(k) for k in ("format", "codec", "sample_rate", "channels", "duration_seconds", "ffprobe_ok", "full_decode_ok", "non_silent_rms_s16", "peak_s16", "nonzero_sample_ratio", "voice_model", "voice_model_sha256", "source_kind", "language_accent")}
        metrics["sha256"] = digest
        metrics["bytes"] = len(data)
    else:
        suffix = filename[len(prefix) + 1:len(prefix) + 11]
        if not digest.startswith(suffix):
            raise SafetyStop(f"Audio hash suffix does not match the media bytes for {key}")
        metrics = validate_unknown_variant(filename, data)
        metrics.update({"voice_model": "en_GB-cori-high", "voice_model_sha256": model_sha, "source_kind": "Local Piper TTS; not a human recording", "language_accent": "en_GB / UK English"})
    return filename, data, metrics


def main() -> int:
    if not ASSET_AUDIT.is_file() or not CURRENT_AUDIT.is_file():
        raise SafetyStop("Required generated-audio audit files are missing")
    previous = json.loads(ASSET_AUDIT.read_text(encoding="utf-8"))
    current_report = json.loads(CURRENT_AUDIT.read_text(encoding="utf-8"))
    initial_assets = {str(x.get("NoteKey")): x for x in previous.get("items", []) if x.get("NoteKey")}
    current_assets = {str(x.get("NoteKey")): x for x in current_report.get("items", []) if x.get("NoteKey") and x.get("sha256") and x.get("anki_media_retrieve_sha256") == x.get("sha256")}
    if len(initial_assets) != 99 or len({x.get("filename") for x in initial_assets.values()}) != 99:
        raise SafetyStop("The initial audit does not contain 99 unique Piper MP3s")
    for key, asset in initial_assets.items():
        require(asset.get("generated_mp3") is True and asset.get("anki_media_store") == "verified", f"Initial media write not verified for {key}")
        require(asset.get("anki_media_retrieve_sha256") == asset.get("sha256"), f"Initial media readback hash mismatch for {key}")
        require(asset.get("ffprobe_ok") and asset.get("full_decode_ok") and float(asset.get("non_silent_rms_s16") or 0) >= 150, f"File-level validation missing for {key}")
    model_sha = str(previous.get("voice", {}).get("model_sha256") or "")
    if len(model_sha) != 64:
        raise SafetyStop("Piper model hash is missing from the verified audit")
    if not BACKUP.is_file() or sha(BACKUP.read_bytes()) != bridge.EXPECTED_BACKUP_SHA256:
        raise SafetyStop("The full pre-repair Anki backup hash does not match")
    with zipfile.ZipFile(BACKUP) as zf:
        if zf.testzip() is not None or not {"meta", "collection.anki21b", "media"}.issubset(set(zf.namelist())):
            raise SafetyStop("The pre-repair backup archive failed validation")

    notion = bridge.NotionClient(bridge.load_notion_token())
    bridge.verify_runtime(notion)
    records = bridge.parse_card_rows(notion)
    targets = bridge.sorted_records([r for r in records if r.get("status") == "SYNCED"])
    conflicts = [r for r in records if r.get("status") == "CONFLICT"]
    if len(records) != 100 or len(targets) != 99 or len(conflicts) != 1:
        raise SafetyStop("Notion scope changed; expected 99 SYNCED and 1 CONFLICT")
    conflict_fields = bridge.field_map(conflicts[0])
    if conflict_fields.get("English", "").strip().casefold() != "involve":
        raise SafetyStop("The protected CONFLICT record is not involve")

    all_ids = bridge.anki("findNotes", {"query": ""}).get("result") or []
    all_notes = bridge.anki("notesInfo", {"notes": all_ids}).get("result") or []
    notes_by_key: dict[str, list[dict[str, Any]]] = {}
    for note in all_notes:
        if note.get("modelName") == TARGET_MODEL:
            nf = bridge.note_fields(note)
            notes_by_key.setdefault(nf.get("NoteKey", ""), []).append(note)
    if sum(1 for n in all_notes if n.get("modelName") == TARGET_MODEL) != 99:
        raise SafetyStop("IELTS model note count changed")

    baseline: dict[str, dict[str, Any]] = {}
    for row in targets:
        key = row["note_key"]
        if key not in initial_assets or len(notes_by_key.get(key, [])) != 1:
            raise SafetyStop(f"NoteKey identity missing or duplicate for {key}")
        note = notes_by_key[key][0]
        nf = bridge.note_fields(note)
        fields = bridge.field_map(row)
        nid = int(note["noteId"])
        cards = [int(c) for c in (note.get("cards") or [])]
        notion_cards = [int(c) for c in json.loads(row.get("existing_card_ids") or "[]")]
        if note.get("modelName") != TARGET_MODEL or nf.get("NoteKey") != key or nf.get("English") != fields["English"]:
            raise SafetyStop(f"NoteKey/English/model mismatch for {key}")
        if str(row.get("existing_note_id")) != str(nid) or set(cards) != set(notion_cards):
            raise SafetyStop(f"Notion NoteID/CardIDs mismatch for {key}")
        original = initial_assets[key]
        if original.get("English") != fields["English"] or int(original.get("NoteID")) != nid:
            raise SafetyStop(f"Audio audit does not map to current text/NoteID for {key}")
        snap = bridge.note_snapshot(nid)
        baseline[key] = {"note_id": nid, "card_ids": cards, "snapshot": snap, "fields": nf, "original_asset": original, "current_asset": current_assets.get(key)}

    conflict_note = notes_by_key.get(conflict_fields.get("NoteKey", ""), [])
    conflict_snapshot = bridge.note_snapshot(int(conflict_note[0]["noteId"])) if len(conflict_note) == 1 else None
    report: dict[str, Any] = {
        "run_id": str(uuid.uuid4()), "started_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "asset_audit_sources": [str(ASSET_AUDIT), str(CURRENT_AUDIT)], "piper_model_sha256": model_sha,
        "backup_sha256_verified": bridge.EXPECTED_BACKUP_SHA256,
        "scope": {"notion_rows": 100, "synced_targets": 99, "conflict_excluded": conflict_fields["English"]},
        "items": [], "cloud_sync": {"status": "NOT_RUN", "collectionComplete": False, "mediaComplete": False},
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
            saved = baseline[key]
            nid = saved["note_id"]
            original = saved["original_asset"]
            current_asset = saved["current_asset"]
            row_fields = bridge.field_map(row)
            item = {"NoteKey": key, "English": row_fields["English"], "NoteID": nid, "CardIDs": saved["card_ids"], "generated_mp3": True, "source_kind": "Local Piper TTS; not a human recording", "voice_model": "en_GB-cori-high"}
            report["items"].append(item)
            save_report(report)
            try:
                before = bridge.note_snapshot(nid)
                before_fields = bridge.note_fields(before["note"])
                if before_fields.get("NoteKey") != key or before_fields.get("English") != row_fields["English"]:
                    raise SafetyStop(f"Anki identity/text changed during repair for {key}")
                if before["card_ids"] != saved["card_ids"] or bridge.review_fingerprint(before) != bridge.review_fingerprint(saved["snapshot"]):
                    raise SafetyStop(f"CardIDs/review state changed during repair for {key}")

                anki_ref = before_fields.get("Audio", "").strip()
                notion_ref = str(row["payload"].get("Audio") or "").strip()
                valid_refs: dict[str, tuple[str, bytes, dict[str, Any]]] = {}
                for candidate in (anki_ref, notion_ref):
                    if candidate and candidate not in valid_refs:
                        valid_refs[candidate] = validate_reference(candidate, key, row_fields["English"], original, current_asset, model_sha)
                preferred_asset = current_asset or original
                preferred_ref = f"[sound:{preferred_asset['filename']}]"
                if anki_ref:
                    chosen_ref = anki_ref
                elif notion_ref:
                    chosen_ref = notion_ref
                else:
                    chosen_ref = preferred_ref
                    valid_refs[chosen_ref] = validate_reference(chosen_ref, key, row_fields["English"], original, current_asset, model_sha)
                if chosen_ref not in valid_refs:
                    valid_refs[chosen_ref] = validate_reference(chosen_ref, key, row_fields["English"], original, current_asset, model_sha)
                filename, raw_media, metrics = valid_refs[chosen_ref]
                item.update({"filename": filename, "duration_seconds": metrics.get("duration_seconds"), "bytes": metrics.get("bytes"), "sha256": metrics["sha256"], "ffprobe_ok": metrics.get("ffprobe_ok"), "full_decode_ok": metrics.get("full_decode_ok"), "non_silent_rms_s16": metrics.get("non_silent_rms_s16"), "anki_media_retrieve_sha256": metrics["sha256"], "anki_media_presence": "verified"})

                if anki_ref != chosen_ref:
                    try:
                        bridge.anki("updateNoteFields", {"note": {"id": nid, "fields": {"Audio": chosen_ref}}})
                    except Exception:
                        ambiguous = bridge.note_snapshot(nid)
                        if bridge.note_fields(ambiguous["note"]).get("Audio", "") != chosen_ref:
                            raise RuntimeError("updateNoteFields failed and readback did not confirm Audio")
                after = bridge.note_snapshot(nid)
                after_fields = bridge.note_fields(after["note"])
                if after_fields.get("Audio", "") != chosen_ref:
                    raise RuntimeError("Anki Audio field readback mismatch")
                if {k: v for k, v in after_fields.items() if k != "Audio"} != {k: v for k, v in before_fields.items() if k != "Audio"}:
                    raise SafetyStop(f"Non-Audio Anki field changed for {key}")
                if after["card_ids"] != before["card_ids"] or bridge.review_fingerprint(after) != bridge.review_fingerprint(before):
                    raise SafetyStop(f"CardIDs or learning history changed for {key}")
                item["anki_audio_field_readback"] = "verified"
                item["NoteID_preserved"] = True
                item["CardIDs_preserved"] = True
                item["schedule_and_review_preserved"] = True

                if notion_ref and notion_ref != chosen_ref:
                    # Both references were validated as this NoteKey's own Piper output; converge Notion to Anki.
                    pass
                if notion_ref != chosen_ref:
                    page = notion.get_page(row["page_id"])
                    prefix, payload_now = payload_from_page(page)
                    if payload_now != row["payload"] or bridge.page_value(page, "Status") != "SYNCED" or str(bridge.page_value(page, "NoteID")) != str(nid):
                        raise SafetyStop(f"Notion record changed concurrently for {key}")
                    cards_now = [int(c) for c in json.loads(str(bridge.page_value(page, "CardIDs") or "[]"))]
                    if cards_now != after["card_ids"] or int(bridge.page_value(page, "Revision")) != int(row["revision"]):
                        raise SafetyStop(f"Notion CardIDs/Revision changed concurrently for {key}")
                    payload_now["Audio"] = chosen_ref
                    new_revision = int(row["revision"]) + 1
                    serialized = prefix + json.dumps(payload_now, ensure_ascii=False, separators=(",", ":"))
                    try:
                        notion.patch_page(row["page_id"], {"PayloadJSON": bridge.exact_rich_text_value(serialized), "Revision": {"number": new_revision}})
                    except Exception:
                        pass
                    page_after = notion.get_page(row["page_id"])
                    _, after_payload = payload_from_page(page_after)
                    if after_payload.get("Audio") != chosen_ref or int(bridge.page_value(page_after, "Revision")) != new_revision or bridge.page_value(page_after, "Status") != "SYNCED":
                        raise RuntimeError("Notion Audio/Revision/Status readback mismatch")
                    if str(bridge.page_value(page_after, "NoteID")) != str(nid) or [int(c) for c in json.loads(str(bridge.page_value(page_after, "CardIDs") or "[]"))] != after["card_ids"]:
                        raise SafetyStop(f"Notion NoteID/CardIDs changed for {key}")
                    row["payload"] = payload_now
                    row["revision"] = new_revision
                else:
                    item["notion_audio_already_present"] = True
                digest = bridge.payload_hash(bridge.field_map(row))
                bridge.state_put(conn, row, int(row["revision"]), digest, nid, after["card_ids"], row["deck"])
                item["Notion_Audio_readback"] = "verified"
                item["Revision_after"] = row["revision"]
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

        # Final cross-check: all synced NoteKeys have the same real media reference in Anki and Notion.
        final_rows = bridge.parse_card_rows(notion)
        final_by_key = {r["note_key"]: r for r in final_rows if r.get("status") == "SYNCED"}
        for row in targets:
            key = row["note_key"]
            if key not in final_by_key:
                raise SafetyStop(f"Final Notion row missing for {key}")
            final_row = final_by_key[key]
            ref = str(final_row["payload"].get("Audio") or "").strip()
            note_infos = bridge.anki("notesInfo", {"notes": [baseline[key]["note_id"]]}).get("result") or []
            if len(note_infos) != 1 or bridge.note_fields(note_infos[0]).get("Audio", "") != ref or not ref:
                raise SafetyStop(f"Final Anki–Notion Audio mismatch for {key}")
            if int(final_row["revision"]) < int(row["revision"]):
                raise SafetyStop(f"Notion Revision regressed for {key}")
        final_conflict = next((r for r in final_rows if r.get("status") == "CONFLICT" and bridge.field_map(r).get("English", "").strip().casefold() == "involve"), None)
        if not final_conflict:
            raise SafetyStop("The protected involve CONFLICT record changed status")
        if conflict_snapshot is not None:
            current_conflict_note = bridge.note_snapshot(int(conflict_note[0]["noteId"]))
            if bridge.review_fingerprint(current_conflict_note) != bridge.review_fingerprint(conflict_snapshot) or bridge.note_fields(current_conflict_note["note"]).get("Audio", "") != bridge.note_fields(conflict_snapshot["note"]).get("Audio", ""):
                raise SafetyStop("The protected involve note was modified")

        success = sum(x.get("result") == "SUCCESS" for x in report["items"])
        counts = {"records_seen": 99, "updated": success, "errors": 99-success, "cloud_sync_status": "NOT_RUN", "cloud_sync_error_code": "", "cloud_sync_collection_complete": False, "cloud_sync_media_complete": False}
        cloud_ok = bridge.sync_ankiweb(counts)
        report["cloud_sync"] = {"status": counts.get("cloud_sync_status"), "collectionComplete": counts.get("cloud_sync_collection_complete"), "mediaComplete": counts.get("cloud_sync_media_complete"), "error_code": counts.get("cloud_sync_error_code"), "operation_required_user_choice": counts.get("cloud_sync_status") == "CONFLICT"}
        report["summary"] = {"generated_mp3": sum(x.get("generated_mp3") is True for x in report["items"]), "anki_audio_fields_verified": success, "notion_audio_fields_verified": sum(x.get("Notion_Audio_readback") == "verified" for x in report["items"]), "failed": 99-success, "conflict_excluded": 1}
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
