from __future__ import annotations

import array
import base64
import hashlib
import importlib.util
import json
import math
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BRIDGE_PATH = Path(r"C:\Users\Admin\AppData\Local\hermes\scripts\anki_notion_sync.py")
ROOT = Path(r"C:\Users\Admin\AppData\Local\hermes\memories\脚本缓存\anki-audio-repair")
MODEL = ROOT / "models" / "en_GB-cori-high.onnx"
MODEL_CONFIG = Path(str(MODEL) + ".json")
PIPER_DIR = ROOT / "piper_cli" / "runtime" / "piper"
BACKUP = Path(r"C:\Users\Admin\Documents\AnkiBackups\Anki_collection_2026-10-14_before_audio_repair.colpkg")
REPORT = ROOT / "batch_audio_repair_audit.json"
PREVIOUS_REPORT = ROOT / "batch_audio_repair_audit_attempt1.json"
TARGET_MODEL = "IELTS_Vocabulary_v1"

spec = importlib.util.spec_from_file_location("anki_audio_bridge", BRIDGE_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("Could not load the existing Anki–Notion bridge")
bridge = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = bridge
spec.loader.exec_module(bridge)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def save_report(report: dict[str, Any]) -> None:
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    temp = REPORT.with_suffix(".tmp")
    temp.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(REPORT)


def check(cond: bool, message: str) -> None:
    if not cond:
        raise RuntimeError(message)


def get_payload(page: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    raw = str(bridge.page_value(page, "PayloadJSON") or "")
    text = raw.strip()
    prefix = "json:" if text.startswith("json:") else ""
    if prefix:
        text = text[5:].lstrip()
    payload = json.loads(text)
    if not isinstance(payload, dict):
        raise RuntimeError("Notion PayloadJSON is not an object")
    return prefix, payload


def decode_media_result(result: Any) -> bytes | None:
    if result is False or result is None or result == "":
        return None
    if not isinstance(result, str):
        raise RuntimeError("AnkiConnect retrieveMediaFile returned an unexpected result type")
    try:
        return base64.b64decode(result, validate=True)
    except Exception as exc:
        raise RuntimeError("AnkiConnect returned invalid media base64") from exc


def retrieve_media(filename: str) -> bytes | None:
    response = bridge.anki("retrieveMediaFile", {"filename": filename})
    return decode_media_result(response.get("result"))


def validate_mp3(path: Path, text: str, ffmpeg: str, ffprobe: str) -> dict[str, Any]:
    if not path.is_file() or path.stat().st_size < 1000:
        raise RuntimeError("Generated MP3 is missing or unexpectedly small")
    probe = subprocess.run(
        [ffprobe, "-v", "error", "-show_entries", "format=duration,format_name,size:stream=codec_name,sample_rate,channels", "-of", "json", str(path)],
        capture_output=True, text=True, timeout=45,
    )
    if probe.returncode:
        raise RuntimeError("FFprobe could not read the generated MP3")
    parsed = json.loads(probe.stdout)
    streams = parsed.get("streams") or []
    if not streams:
        raise RuntimeError("FFprobe found no audio stream")
    stream = streams[0]
    duration = float((parsed.get("format") or {}).get("duration") or 0)
    words = len(re.findall(r"[A-Za-z0-9]+(?:['’][A-Za-z0-9]+)*", text))
    max_duration = min(90.0, max(6.0, words * 2.5 + 2.0))
    if stream.get("codec_name") != "mp3" or not 0.2 < duration < max_duration:
        raise RuntimeError("MP3 codec or duration did not meet validation bounds")
    decoded = subprocess.run([ffmpeg, "-v", "error", "-i", str(path), "-f", "null", "-"], capture_output=True, text=True, timeout=90)
    if decoded.returncode:
        raise RuntimeError("FFmpeg full decode failed")
    pcm = subprocess.run([ffmpeg, "-v", "error", "-i", str(path), "-f", "s16le", "-ac", "1", "-ar", "16000", "-"], capture_output=True, timeout=90)
    if pcm.returncode or not pcm.stdout or len(pcm.stdout) % 2:
        raise RuntimeError("Could not extract PCM for non-silence verification")
    samples = array.array("h")
    samples.frombytes(pcm.stdout)
    if sys.byteorder != "little":
        samples.byteswap()
    if not samples:
        raise RuntimeError("Decoded audio has no PCM samples")
    rms = math.sqrt(sum(int(x) * int(x) for x in samples) / len(samples))
    nonzero_ratio = sum(x != 0 for x in samples) / len(samples)
    peak = max(abs(int(x)) for x in samples)
    if rms < 150 or peak < 500 or nonzero_ratio < 0.01:
        raise RuntimeError("Audio is silent or below the non-silence threshold")
    return {
        "format": (parsed.get("format") or {}).get("format_name"),
        "codec": stream.get("codec_name"),
        "sample_rate": int(stream.get("sample_rate") or 0),
        "channels": int(stream.get("channels") or 0),
        "duration_seconds": round(duration, 6),
        "bytes": path.stat().st_size,
        "sha256": sha256(path.read_bytes()),
        "ffprobe_ok": True,
        "full_decode_ok": True,
        "non_silent_rms_s16": round(rms, 2),
        "peak_s16": peak,
        "nonzero_sample_ratio": round(nonzero_ratio, 5),
        "text_match_basis": "Exact English text, whitespace-normalized only, was supplied to local Piper synthesis",
    }


def prepare_runtime(scratch: Path) -> tuple[Path, Path, Path, Path]:
    check(MODEL.is_file() and MODEL_CONFIG.is_file(), "Piper model/config is missing")
    check((PIPER_DIR / "piper.exe").is_file() and (PIPER_DIR / "espeak-ng-data").is_dir(), "Piper CLI runtime is incomplete")
    runtime = scratch / "piper_runtime"
    if runtime.exists():
        shutil.rmtree(runtime)
    shutil.copytree(PIPER_DIR, runtime)
    model_copy = scratch / MODEL.name
    config_copy = Path(str(model_copy) + ".json")
    shutil.copy2(MODEL, model_copy)
    shutil.copy2(MODEL_CONFIG, config_copy)
    return runtime / "piper.exe", runtime / "espeak-ng-data", model_copy, config_copy


def synthesize_and_store(english: str, note_key: str, model_sha: str, scratch: Path, runtime: tuple[Path, Path, Path, Path], ffmpeg: str, ffprobe: str) -> tuple[str, dict[str, Any], Path]:
    piper, espeak_data, model_copy, config_copy = runtime
    speech_text = " ".join(english.split())
    if not speech_text or re.search(r"</?[A-Za-z][^>]*>", speech_text):
        raise RuntimeError("English field is empty or contains markup; refusing ambiguous speech text")
    safe_key = re.sub(r"[^A-Za-z0-9_-]+", "_", note_key).strip("_") or "note"
    english_sha = sha256(english.encode("utf-8"))
    stem = f"ielts_piper_en_gb_{safe_key}_{english_sha[:10]}_{model_sha[:8]}"
    staging = ROOT / "staging"
    staging.mkdir(parents=True, exist_ok=True)
    wav_temp = scratch / f"{stem}_{uuid.uuid4().hex[:8]}.wav"
    mp3_temp = scratch / f"{stem}_{uuid.uuid4().hex[:8]}.mp3"
    run = subprocess.run(
        [str(piper), "-m", str(model_copy), "-c", str(config_copy), "-f", str(wav_temp), "--espeak_data", str(espeak_data), "-q"],
        input=(speech_text + "\n").encode("utf-8"), capture_output=True, timeout=120,
    )
    if run.returncode or not wav_temp.is_file() or wav_temp.stat().st_size == 0:
        raise RuntimeError("Piper CLI synthesis failed")
    convert = subprocess.run(
        [ffmpeg, "-y", "-nostdin", "-v", "error", "-i", str(wav_temp), "-map", "0:a:0", "-vn", "-ac", "1", "-ar", "44100", "-c:a", "libmp3lame", "-b:a", "128k", str(mp3_temp)],
        capture_output=True, text=True, timeout=90,
    )
    if convert.returncode:
        raise RuntimeError("FFmpeg MP3 conversion failed")
    metrics = validate_mp3(mp3_temp, speech_text, ffmpeg, ffprobe)
    metrics.update({
        "filename": stem + ".mp3",
        "source_kind": "Local Piper TTS; not a human recording",
        "source_url": "https://huggingface.co/rhasspy/piper-voices/blob/main/en/en_GB/cori/high/MODEL_CARD",
        "voice_model": "en_GB-cori-high",
        "voice_model_sha256": model_sha,
        "piper_cli_release": "2023.11.14-2",
        "language_accent": "en_GB, UK English; single-speaker Cori voice per model card/config",
        "license_basis": "Piper voice model repository MIT; model card identifies LibriVox public-domain training source",
    })
    final_path = staging / (stem + ".mp3")
    shutil.copy2(mp3_temp, final_path)
    if sha256(final_path.read_bytes()) != metrics["sha256"]:
        raise RuntimeError("Staged MP3 SHA-256 differs from verified temporary output")
    wav_temp.unlink(missing_ok=True)
    mp3_temp.unlink(missing_ok=True)
    # Refuse to overwrite a pre-existing, different media file.
    existing = retrieve_media(metrics["filename"])
    if existing is not None and sha256(existing) != metrics["sha256"]:
        alt = f"{stem}_{metrics['sha256'][:10]}.mp3"
        metrics["filename"] = alt
        final_path2 = staging / alt
        shutil.copy2(final_path, final_path2)
        final_path = final_path2
        existing = retrieve_media(alt)
        if existing is not None and sha256(existing) != metrics["sha256"]:
            raise RuntimeError("Stable audio filename collides with different existing media")
    if existing is None:
        stored = bridge.anki("storeMediaFile", {"filename": metrics["filename"], "data": base64.b64encode(final_path.read_bytes()).decode("ascii")}).get("result")
        if stored != metrics["filename"]:
            raise RuntimeError("AnkiConnect storeMediaFile did not return the requested filename")
    readback = retrieve_media(metrics["filename"])
    if readback is None or sha256(readback) != metrics["sha256"] or len(readback) != metrics["bytes"]:
        raise RuntimeError("AnkiConnect retrieveMediaFile readback did not match the MP3")
    metrics["anki_media_store"] = "verified" if existing is None else "existing-identical-media-verified"
    metrics["anki_media_retrieve_sha256"] = sha256(readback)
    metrics["anki_media_retrieve_bytes"] = len(readback)
    return f"[sound:{metrics['filename']}]", metrics, final_path


def main() -> int:
    previous_by_key: dict[str, dict[str, Any]] = {}
    if PREVIOUS_REPORT.is_file():
        try:
            old = json.loads(PREVIOUS_REPORT.read_text(encoding="utf-8"))
            previous_by_key = {str(x.get("NoteKey")): x for x in old.get("items", []) if x.get("NoteKey")}
        except Exception:
            previous_by_key = {}
    ffmpeg, ffprobe = shutil.which("ffmpeg"), shutil.which("ffprobe")
    check(ffmpeg is not None and ffprobe is not None, "FFmpeg and FFprobe must be available on PATH")
    check(BACKUP.is_file() and BACKUP.stat().st_size > 0, "Verified full collection backup is missing")
    backup_sha = sha256(BACKUP.read_bytes())
    check(backup_sha == bridge.EXPECTED_BACKUP_SHA256, "Full collection backup hash differs from the approved snapshot")
    import zipfile
    with zipfile.ZipFile(BACKUP) as zf:
        check(zf.testzip() is None, "Full collection backup ZIP CRC check failed")
        check({"meta", "collection.anki21b", "media"}.issubset(set(zf.namelist())), "Full collection backup lacks required members")

    notion = bridge.NotionClient(bridge.load_notion_token())
    bridge.verify_runtime(notion)
    records = bridge.parse_card_rows(notion)
    rows_by_key: dict[str, list[dict[str, Any]]] = {}
    for row in records:
        rows_by_key.setdefault(row.get("note_key", ""), []).append(row)
    all_note_ids = bridge.anki("findNotes", {"query": ""}).get("result") or []
    all_notes = bridge.anki("notesInfo", {"notes": all_note_ids}).get("result") or []
    notes_by_key: dict[str, list[dict[str, Any]]] = {}
    for note in all_notes:
        fields = bridge.note_fields(note)
        if note.get("modelName") == TARGET_MODEL:
            notes_by_key.setdefault(fields.get("NoteKey", ""), []).append(note)

    targets = [r for r in records if r.get("status") == "SYNCED"]
    conflicts = [r for r in records if r.get("status") == "CONFLICT"]
    check(len(targets) == 99, f"Expected 99 SYNCED rows; found {len(targets)}")
    check(len(conflicts) == 1, f"Expected the protected CONFLICT row; found {len(conflicts)}")
    conflict_fields = bridge.field_map(conflicts[0])
    check(conflict_fields.get("English", "").strip().casefold() == "involve", "The sole CONFLICT row is not involve; refusing a broad assumption")
    check(len(records) == 100, f"Expected 100 Cards rows; found {len(records)}")
    check(sum(1 for n in all_notes if n.get("modelName") == TARGET_MODEL) == 99, "IELTS model note count differs from expected 99")

    state_db = sqlite3.connect(f"file:{bridge.STATE_PATH.as_posix()}?mode=ro", uri=True)
    state_db.row_factory = sqlite3.Row
    unfinished_rows = state_db.execute("SELECT run_id,started_at FROM runs WHERE finished_at IS NULL").fetchall()
    state_rows = {row["note_key"]: dict(row) for row in state_db.execute("SELECT note_key,page_id,revision,payload_hash,note_id,card_ids_json,deck FROM notes")}
    state_db.close()

    targets = bridge.sorted_records(targets)
    snapshots: dict[str, dict[str, Any]] = {}
    preflight: list[dict[str, Any]] = []
    for row in targets:
        check(not row.get("parse_error"), f"Invalid PayloadJSON for {row.get('note_key')}")
        check(len(rows_by_key.get(row["note_key"], [])) == 1, f"Duplicate Notion NoteKey {row['note_key']}")
        payload_fields = bridge.field_map(row)
        matches = notes_by_key.get(row["note_key"], [])
        check(len(matches) == 1, f"Anki NoteKey identity is not unique for {row['note_key']}")
        note = matches[0]
        note_id = int(note["noteId"])
        card_ids = [int(x) for x in (note.get("cards") or [])]
        notion_card_ids = json.loads(row.get("existing_card_ids") or "[]")
        check(note.get("modelName") == TARGET_MODEL, f"Unexpected model for {row['note_key']}")
        check(bridge.note_fields(note).get("English") == payload_fields["English"], f"English field differs for {row['note_key']}")
        check(bridge.note_fields(note).get("NoteKey") == row["note_key"], f"Anki NoteKey mismatch for {row['note_key']}")
        check(str(row.get("existing_note_id")) == str(note_id), f"Notion NoteID mismatch for {row['note_key']}")
        check(set(card_ids) == set(int(x) for x in notion_card_ids), f"Notion CardIDs mismatch for {row['note_key']}")
        if row["note_key"] in state_rows:
            st = state_rows[row["note_key"]]
            check(int(st["note_id"]) == note_id and st["page_id"] == row["page_id"], f"Local state identity mismatch for {row['note_key']}")
            check(json.loads(st["card_ids_json"]) == card_ids, f"Local state CardIDs mismatch for {row['note_key']}")
        snap = bridge.note_snapshot(note_id)
        snapshots[row["note_key"]] = snap
        preflight.append({
            "English": payload_fields["English"], "NoteKey": row["note_key"], "page_id": row["page_id"],
            "NoteID": note_id, "CardIDs": card_ids, "Revision_before": row["revision"],
            "Audio_before_anki": bridge.note_fields(note).get("Audio", ""),
            "Audio_before_notion": payload_fields.get("Audio", ""),
            "review_schedule_fingerprint_before": bridge.review_fingerprint(snap),
        })

    template = bridge.anki("modelTemplates", {"modelName": TARGET_MODEL}).get("result") or {}
    template_text = json.dumps(template, ensure_ascii=False)
    check("{{#Audio}}" in template_text and "{{^Audio}}" in template_text and "{{tts en_GB:English}}" in template_text, "Existing template does not have Audio-first, en_GB TTS fallback")
    model_sha = sha256(MODEL.read_bytes())
    scratch_root = Path(os.environ.get("TMPDIR") or (ROOT / "work")) / "anki_audio_repair_batch"
    scratch_root.mkdir(parents=True, exist_ok=True)
    runtime = prepare_runtime(scratch_root)

    report: dict[str, Any] = {
        "run_id": str(uuid.uuid4()),
        "started_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "backup": {"path": str(BACKUP), "sha256": backup_sha, "bytes": BACKUP.stat().st_size, "zip_crc_ok": True},
        "collection_gate": {"notion_cards": len(records), "synced_rows": len(targets), "conflict_rows_excluded": len(conflicts), "conflict_English": conflict_fields["English"], "anki_model_notes": 99, "autoSync_false_and_template_verified": True},
        "stale_run_records_before_lock": [{"run_id": r["run_id"], "started_at": r["started_at"]} for r in unfinished_rows],
        "voice": {"engine": "Piper CLI 2023.11.14-2", "model": "en_GB-cori-high", "model_sha256": model_sha, "language_accent": "en_GB / UK English; single speaker", "is_human_recording": False},
        "items": [],
        "preflight": preflight,
        "cloud_sync": {"status": "NOT_RUN", "collectionComplete": False, "mediaComplete": False},
    }
    save_report(report)

    conn = sqlite3.connect(bridge.STATE_PATH, timeout=60, isolation_level=None)
    conn.execute("PRAGMA busy_timeout=60000")
    committed = False
    counts = {"cloud_sync_status": "NOT_RUN", "cloud_sync_error_code": "", "cloud_sync_collection_complete": False, "cloud_sync_media_complete": False}
    try:
        conn.execute("BEGIN IMMEDIATE")
        bridge.init_state(conn)
        run_id = "audio-" + report["run_id"]
        conn.execute("INSERT INTO runs(run_id,started_at) VALUES(?,?)", (run_id, report["started_at_utc"]))
        report["stale_run_records_after_lock"] = [{"run_id": r[0], "started_at": r[1]} for r in conn.execute("SELECT run_id,started_at FROM runs WHERE run_id<>? AND finished_at IS NULL", (run_id,)).fetchall()]
        report["state_lock_acquired"] = True
        save_report(report)

        for row in targets:
            key = row["note_key"]
            fields = bridge.field_map(row)
            note_id = int(row["existing_note_id"])
            item: dict[str, Any] = {"English": fields["English"], "NoteKey": key, "NoteID": note_id, "CardIDs": json.loads(row["existing_card_ids"]), "Revision_before": row["revision"], "voice_source": "Local Piper en_GB-cori-high TTS", "text_exact": fields["English"]}
            report["items"].append(item)
            save_report(report)
            try:
                before = bridge.note_snapshot(note_id)
                check(bridge.review_fingerprint(before) == bridge.review_fingerprint(snapshots[key]), f"Schedule/review state changed after preflight for {key}")
                before_fields = bridge.note_fields(before["note"])
                check(before_fields.get("English") == fields["English"] and before_fields.get("NoteKey") == key, f"Anki identity changed after preflight for {key}")
                audio_ref = before_fields.get("Audio", "").strip()
                if audio_ref:
                    m = re.fullmatch(r"\[sound:([^\]]+)\]", audio_ref)
                    if not m:
                        raise RuntimeError("Existing Anki Audio value is not a single [sound:...] reference")
                    existing_bytes = retrieve_media(m.group(1))
                    if existing_bytes is None:
                        audio_ref = ""
                    else:
                        item["existing_audio_sha256"] = sha256(existing_bytes)
                        item["existing_audio_reused"] = True
                        prior = previous_by_key.get(key, {})
                        if prior.get("generated_mp3") is True and prior.get("filename") == m.group(1) and prior.get("sha256") == item["existing_audio_sha256"]:
                            item["generated_mp3"] = True
                            item["generated_in_prior_attempt"] = True
                            for metric in ("filename", "format", "codec", "sample_rate", "channels", "duration_seconds", "bytes", "sha256", "ffprobe_ok", "full_decode_ok", "non_silent_rms_s16", "peak_s16", "nonzero_sample_ratio", "text_match_basis", "source_kind", "source_url", "voice_model", "voice_model_sha256", "piper_cli_release", "language_accent", "license_basis"):
                                if metric in prior:
                                    item[metric] = prior[metric]
                if not audio_ref:
                    audio_ref, media_metrics, media_path = synthesize_and_store(fields["English"], key, model_sha, scratch_root, runtime, ffmpeg, ffprobe)
                    item.update(media_metrics)
                    item["local_staged_path"] = str(media_path)
                    item["generated_mp3"] = True
                else:
                    item["generated_mp3"] = item.get("generated_mp3", False)
                    item["audio_reference"] = audio_ref
                    item["anki_media_store"] = "existing-media-verified"
                    item["anki_media_retrieve_sha256"] = item.get("existing_audio_sha256")

                item["audio_reference"] = audio_ref
                if before_fields.get("Audio", "") != audio_ref:
                    try:
                        bridge.anki("updateNoteFields", {"note": {"id": note_id, "fields": {"Audio": audio_ref}}})
                    except Exception:
                        ambiguous = bridge.note_snapshot(note_id)
                        if bridge.note_fields(ambiguous["note"]).get("Audio", "") != audio_ref:
                            raise RuntimeError("AnkiConnect updateNoteFields failed and readback did not confirm the Audio value")
                after = bridge.note_snapshot(note_id)
                after_fields = bridge.note_fields(after["note"])
                check(after_fields.get("Audio", "") == audio_ref, f"Anki Audio field readback mismatch for {key}")
                check({k: v for k, v in after_fields.items() if k != "Audio"} == {k: v for k, v in before_fields.items() if k != "Audio"}, f"A non-Audio Anki field changed for {key}")
                check(after["card_ids"] == before["card_ids"], f"CardIDs changed for {key}")
                check(bridge.review_fingerprint(after) == bridge.review_fingerprint(before), f"Schedule/review fingerprint changed for {key}")
                item["anki_audio_field_readback"] = "verified"
                item["NoteID_preserved"] = True
                item["CardIDs_preserved"] = True
                item["schedule_and_review_preserved"] = True

                page = notion.get_page(row["page_id"])
                current_prefix, current_payload = get_payload(page)
                check(current_payload == row["payload"], f"Notion PayloadJSON changed concurrently for {key}")
                check(bridge.page_value(page, "Status") == "SYNCED", f"Notion Status changed concurrently for {key}")
                check(str(bridge.page_value(page, "NoteID")) == str(note_id), f"Notion NoteID changed concurrently for {key}")
                check(json.loads(str(bridge.page_value(page, "CardIDs") or "[]")) == after["card_ids"], f"Notion CardIDs changed concurrently for {key}")
                revision_before = int(bridge.page_value(page, "Revision"))
                check(revision_before == int(row["revision"]), f"Notion Revision changed concurrently for {key}")
                current_payload["Audio"] = audio_ref
                revision_after = revision_before + 1
                serialized = current_prefix + json.dumps(current_payload, ensure_ascii=False, separators=(",", ":"))
                properties = {"PayloadJSON": bridge.exact_rich_text_value(serialized), "Revision": {"number": revision_after}}
                try:
                    notion.patch_page(row["page_id"], properties)
                except Exception:
                    # One exact readback resolves an ambiguous PATCH; never resend it blindly.
                    pass
                check_page = notion.get_page(row["page_id"])
                _, payload_after = get_payload(check_page)
                check(payload_after.get("Audio") == audio_ref, f"Notion PayloadJSON Audio readback mismatch for {key}")
                check(int(bridge.page_value(check_page, "Revision")) == revision_after, f"Notion Revision readback mismatch for {key}")
                check(bridge.page_value(check_page, "Status") == "SYNCED", f"Notion Status changed during Audio patch for {key}")
                check(str(bridge.page_value(check_page, "NoteID")) == str(note_id), f"Notion NoteID changed during Audio patch for {key}")
                check(json.loads(str(bridge.page_value(check_page, "CardIDs") or "[]")) == after["card_ids"], f"Notion CardIDs changed during Audio patch for {key}")
                row["payload"] = current_payload
                row["revision"] = revision_after
                row["existing_note_id"] = str(note_id)
                row["existing_card_ids"] = json.dumps(after["card_ids"], separators=(",", ":"))
                digest = bridge.payload_hash(bridge.field_map(row))
                bridge.state_put(conn, row, revision_after, digest, note_id, after["card_ids"], row["deck"])
                item["Notion_Audio_readback"] = "verified"
                item["Revision_after"] = revision_after
                item["Status_after"] = "SYNCED"
                item["local_state_mapping"] = "verified/updated"
                item["result"] = "SUCCESS"
            except Exception as exc:
                item["result"] = "FAILED"
                item["failure_reason"] = f"{type(exc).__name__}: {str(exc)[:240]}"
                # Do not alter Status or retry writes blindly. Preserve exact partial state in the audit.
            save_report(report)

        success_count = sum(1 for x in report["items"] if x.get("result") == "SUCCESS")
        generated_count = sum(1 for x in report["items"] if x.get("generated_mp3") is True)
        notion_count = sum(1 for x in report["items"] if x.get("Notion_Audio_readback") == "verified")
        counts["records_seen"] = len(targets)
        counts["updated"] = success_count
        counts["errors"] = len(targets) - success_count
        cloud_ok = bridge.sync_ankiweb(counts)
        report["cloud_sync"] = {
            "status": counts.get("cloud_sync_status"),
            "collectionComplete": counts.get("cloud_sync_collection_complete"),
            "mediaComplete": counts.get("cloud_sync_media_complete"),
            "error_code": counts.get("cloud_sync_error_code"),
            "operation_required_user_choice": counts.get("cloud_sync_status") == "CONFLICT",
        }
        report["summary"] = {"generated_mp3": generated_count, "anki_audio_fields_verified": success_count, "notion_audio_fields_verified": notion_count, "failed": len(targets) - success_count, "conflict_excluded": len(conflicts)}
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
