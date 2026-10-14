from __future__ import annotations

import array
import hashlib
import importlib.util
import json
import math
import os
import shutil
import subprocess
import sys
from pathlib import Path

BASE = Path(r"C:\Users\Admin\AppData\Local\hermes\memories\脚本缓存\anki-audio-repair")
STAGE = BASE / "staging"
MODEL = BASE / "models" / "en_GB-cori-high.onnx"
MODEL_CONFIG = Path(str(MODEL) + ".json")
PIPER_DIR = BASE / "piper_cli" / "runtime" / "piper"
PIPER_EXE = PIPER_DIR / "piper.exe"
PIPER_DATA = PIPER_DIR / "espeak-ng-data"
ANKI_SYNC = Path(r"C:\Users\Admin\AppData\Local\hermes\scripts\anki_notion_sync.py")


def run() -> dict:
    STAGE.mkdir(parents=True, exist_ok=True)
    assert MODEL.is_file() and MODEL_CONFIG.is_file()

    spec = importlib.util.spec_from_file_location("anki_notion_sync_audit", ANKI_SYNC)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    terms = ["opportunity", "modern society", "benefits and drawbacks"]
    note_ids = module.anki("findNotes", {"query": "note:IELTS_Vocabulary_v1"}).get("result") or []
    notes = {}
    for note in module.anki("notesInfo", {"notes": note_ids}).get("result") or []:
        fields = {name: value.get("value", "") for name, value in note.get("fields", {}).items()}
        key = " ".join(fields.get("English", "").split()).casefold()
        if key in terms:
            notes[key] = (int(note["noteId"]), fields)
    if len(notes) != 3:
        raise RuntimeError(f"Expected 3 exact existing notes; found {len(notes)}")
    card_text = {term: notes[term][1]["English"] for term in terms}
    if any(card_text[t] != t for t in terms):
        raise RuntimeError("Anki English text differs from the requested test phrases")

    ffmpeg, ffprobe = shutil.which("ffmpeg"), shutil.which("ffprobe")
    if not ffmpeg or not ffprobe:
        raise RuntimeError("ffmpeg/ffprobe unavailable")

    cfg = json.loads(MODEL_CONFIG.read_text(encoding="utf-8"))
    model_sha = hashlib.sha256(MODEL.read_bytes()).hexdigest()
    scratch_root = Path(os.environ.get("TMPDIR") or (BASE / "work")) / "anki_audio_repair_ascii"
    scratch_root.mkdir(parents=True, exist_ok=True)
    runtime_ascii = scratch_root / "piper_runtime"
    if runtime_ascii.exists():
        shutil.rmtree(runtime_ascii)
    shutil.copytree(PIPER_DIR, runtime_ascii)
    model_ascii = scratch_root / MODEL.name
    config_ascii = Path(str(model_ascii) + ".json")
    shutil.copy2(MODEL, model_ascii)
    shutil.copy2(MODEL_CONFIG, config_ascii)
    piper_ascii = runtime_ascii / "piper.exe"
    espeak_ascii = runtime_ascii / "espeak-ng-data"
    wav_paths = {}
    wav_ascii_paths = {}
    for term in terms[1:]:
        wav_path = STAGE / (term.replace(" ", "_") + ".wav")
        wav_ascii = scratch_root / (term.replace(" ", "_") + ".wav")
        result = subprocess.run(
            [str(piper_ascii), "-m", str(model_ascii), "-c", str(config_ascii), "-f", str(wav_ascii), "--espeak_data", str(espeak_ascii), "-q"],
            input=(card_text[term] + "\n").encode("utf-8"), capture_output=True, timeout=120,
        )
        if result.returncode or not wav_ascii.is_file() or wav_ascii.stat().st_size == 0:
            raise RuntimeError(f"Piper synthesis failed for {term}: {(result.stderr or b'').decode('cp1252', 'replace')[:300]}")
        shutil.copy2(wav_ascii, wav_path)
        wav_paths[term] = wav_path
        wav_ascii_paths[term] = wav_ascii

    source_ogg = BASE / "sources" / "En-GB-opportunity.ogg"
    if not source_ogg.is_file():
        raise RuntimeError("The exact Commons original file is missing")
    source_ogg_ascii = scratch_root / "En-GB-opportunity.ogg"
    shutil.copy2(source_ogg, source_ogg_ascii)

    items = []
    for term in terms:
        if term == "opportunity":
            input_path = source_ogg
            convert_input = source_ogg_ascii
            source_kind = "Wikimedia Commons human recording"
            source_title = "File:En-GB-opportunity.ogg"
            source_url = "https://commons.wikimedia.org/wiki/File:En-GB-opportunity.ogg"
            license_name = "CC BY-SA 4.0"
            attribution = "ArtyUK"
            source_description = "Commons description identifies a British English pronunciation of opportunity"
            generator = "FFmpeg transcode from source Ogg Vorbis; no TTS"
        else:
            input_path = wav_paths[term]
            convert_input = wav_ascii_paths[term]
            source_kind = "Local Piper TTS (not a human recording)"
            source_title = "en_GB-cori-high"
            source_url = "https://huggingface.co/rhasspy/piper-voices/blob/main/en/en_GB/cori/high/MODEL_CARD"
            license_name = "Model repository MIT; model card identifies LibriVox public-domain dataset; personal study"
            attribution = "Cori voice model card: UK English female, single speaker"
            source_description = "Generated locally from the exact English field in the Anki note"
            generator = "Piper CLI 2023.11.14-2, en_GB-cori-high, local CPU inference"

        source_sha = hashlib.sha256(input_path.read_bytes()).hexdigest()
        suffix = hashlib.sha256((term + "\0" + source_kind + "\0" + source_sha + "\0" + generator).encode()).hexdigest()[:16]
        filename = f"ielts_en_gb_{term.replace(' ', '_')}_{suffix}.mp3"
        output_path = STAGE / filename
        output_ascii = scratch_root / filename
        convert = subprocess.run(
            [ffmpeg, "-y", "-nostdin", "-v", "error", "-i", str(convert_input), "-map", "0:a:0", "-vn", "-ac", "1", "-ar", "44100", "-c:a", "libmp3lame", "-b:a", "128k", str(output_ascii)],
            capture_output=True, text=True, timeout=60,
        )
        if convert.returncode:
            raise RuntimeError(f"Transcode failed for {term}: {convert.stderr[:300]}")

        probe = subprocess.run(
            [ffprobe, "-v", "error", "-show_entries", "format=duration,format_name,size:stream=codec_name,sample_rate,channels", "-of", "json", str(output_ascii)],
            capture_output=True, text=True, timeout=30,
        )
        if probe.returncode:
            raise RuntimeError(f"FFprobe failed for {term}: {probe.stderr[:300]}")
        parsed = json.loads(probe.stdout)
        duration = float(parsed["format"]["duration"])
        stream = parsed["streams"][0]
        decode = subprocess.run([ffmpeg, "-v", "error", "-i", str(output_ascii), "-f", "null", "-"], capture_output=True, text=True, timeout=60)
        if decode.returncode:
            raise RuntimeError(f"Full decode failed for {term}: {decode.stderr[:300]}")
        pcm = subprocess.run([ffmpeg, "-v", "error", "-i", str(output_ascii), "-f", "s16le", "-ac", "1", "-ar", "16000", "-"], capture_output=True, timeout=60)
        if pcm.returncode or len(pcm.stdout) < 4:
            raise RuntimeError(f"PCM decode failed for {term}")
        samples = array.array("h")
        samples.frombytes(pcm.stdout)
        if sys.byteorder == "big":
            samples.byteswap()
        rms = math.sqrt(sum(int(x) * int(x) for x in samples) / len(samples))
        peak = max(abs(int(x)) for x in samples)
        nonzero = sum(abs(int(x)) > 300 for x in samples)
        if rms < 250 or peak < 1000 or nonzero / len(samples) < 0.05:
            raise RuntimeError(f"Silent/near-silent audio for {term}: RMS={rms:.1f}")
        max_duration = 2.6 if len(term.split()) == 1 else 8.0
        if not 0.15 < duration < max_duration:
            raise RuntimeError(f"Implausible duration for {term}: {duration:.3f}s")
        shutil.copy2(output_ascii, output_path)
        if hashlib.sha256(output_path.read_bytes()).hexdigest() != hashlib.sha256(output_ascii.read_bytes()).hexdigest():
            raise RuntimeError(f"Final staged MP3 copy mismatch for {term}")

        snapshot = module.note_snapshot(notes[term][0])
        items.append({
            "English": card_text[term], "NoteID": notes[term][0], "CardIDs": snapshot["card_ids"],
            "filename": filename, "source_kind": source_kind, "source_title": source_title,
            "source_url": source_url, "source_license": license_name, "attribution_or_voice": attribution,
            "source_description": source_description, "generator": generator,
            "model_sha256": model_sha if term != "opportunity" else None,
            "source_file_sha256": source_sha, "mp3_sha256": hashlib.sha256(output_path.read_bytes()).hexdigest(),
            "mp3_bytes": output_path.stat().st_size, "format": parsed["format"]["format_name"],
            "codec": stream["codec_name"], "sample_rate": int(stream["sample_rate"]),
            "channels": int(stream["channels"]), "duration_seconds": round(duration, 6),
            "ffprobe_ok": True, "full_decode_ok": True, "non_silent_rms_s16": round(rms, 2),
            "peak_s16": peak, "nonzero_sample_ratio": round(nonzero / len(samples), 4),
            "text_match_basis": "Commons file description names the exact target" if term == "opportunity" else "Exact card English string passed as Piper synthesis input",
            "independent_listening_or_asr": False, "anki_media_stored": False, "anki_web_sync": False,
        })

    report = {
        "piper_version": "rhasspy/piper release 2023.11.14-2", "voice_model": "en_GB-cori-high",
        "voice_config": {
            "language": cfg.get("language"), "sample_rate": cfg.get("audio", {}).get("sample_rate"),
            "num_speakers": cfg.get("num_speakers"), "dataset": cfg.get("dataset"),
        },
        "model_sha256": model_sha, "test_count": len(items), "items": items,
    }
    report_path = BASE / "pilot_audio_audit.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"report_path": str(report_path), "voice_config": report["voice_config"], "test_count": len(items), "items": [
        {k: item[k] for k in ("English", "filename", "source_kind", "source_license", "format", "codec", "duration_seconds", "ffprobe_ok", "full_decode_ok", "non_silent_rms_s16", "mp3_sha256", "mp3_bytes")}
        for item in items
    ]}


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False))
