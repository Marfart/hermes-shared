from __future__ import annotations

import json
import re
import zipfile
from collections import defaultdict
from pathlib import Path
from typing import Iterable
from xml.etree import ElementTree as ET


ROOT = Path(r"C:\Users\Admin\Desktop\Working\产品规格书\英文资料")
OUT_DIR = Path(r"C:\Users\Admin\AppData\Local\hermes\memories\product-knowledge")
NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
DATASHEET_RE = re.compile(r"(?i)(data\s*sheet|datasheet)")
MODEL_RE = re.compile(r"\b(?:BL|BA|BE|R|RTU|IO|IPM|M|S|X|Y)[A-Z0-9\-]{1,15}\b")
MODEL_STOPWORDS = {
    "BLIIOT",
    "BLIIOT",
    "SHEET",
    "DATA",
    "SIM",
    "STA",
    "SCADA",
    "RJ45",
    "RS232",
    "RS485",
    "M2M",
    "SOM",
}
SECTION_RE = re.compile(
    r"(?i)\b("
    r"overview|introduction|features|feature|benefits|applications|application|"
    r"specifications|technical specification|technical data|interfaces|interface|"
    r"protocols|protocol|network|communication|wireless|cellular|ethernet|serial|"
    r"modbus|mqtt|opc ua|bacnet|iec 104|iec61850|input|output|power|supply|"
    r"temperature|humidity|dimensions|mounting|protection|ip\d{2}|certification|"
    r"performance|cpu|memory|storage"
    r")\b"
)


def iter_datasheets(root: Path) -> list[Path]:
    files = [
        path
        for path in root.rglob("*.docx")
        if DATASHEET_RE.search(path.name)
    ]
    return sorted(files)


def extract_docx_paragraphs(path: Path) -> list[str]:
    with zipfile.ZipFile(path) as zf:
        with zf.open("word/document.xml") as fh:
            xml_data = fh.read()

    root = ET.fromstring(xml_data)
    paragraphs: list[str] = []
    for para in root.findall(".//w:p", NS):
        runs = [
            "".join(node.itertext()).strip()
            for node in para.findall(".//w:t", NS)
            if "".join(node.itertext()).strip()
        ]
        text = re.sub(r"\s+", " ", " ".join(runs)).strip()
        if text:
            paragraphs.append(text)
    return paragraphs


def normalize_paragraphs(paragraphs: Iterable[str]) -> list[str]:
    cleaned: list[str] = []
    previous = None
    for para in paragraphs:
        text = re.sub(r"\s+", " ", para).strip()
        if not text:
            continue
        if text == previous:
            continue
        cleaned.append(text)
        previous = text
    return cleaned


def infer_title(path: Path, paragraphs: list[str]) -> str:
    for para in paragraphs[:12]:
        if len(para) >= 8:
            return para
    stem = re.sub(DATASHEET_RE, "", path.stem).replace("_", " ")
    return re.sub(r"\s+", " ", stem).strip()


def detect_models(path: Path, paragraphs: list[str]) -> list[str]:
    hits = set(MODEL_RE.findall(path.name))
    for para in paragraphs[:40]:
        for match in MODEL_RE.findall(para):
            hits.add(match)
    return sorted(hit for hit in hits if hit.upper() not in MODEL_STOPWORDS)


def extract_highlights(paragraphs: list[str], limit: int = 16) -> list[str]:
    highlights: list[str] = []
    seen = set()
    for index, para in enumerate(paragraphs):
        if not SECTION_RE.search(para):
            continue
        block = [para]
        for next_para in paragraphs[index + 1 : index + 4]:
            if SECTION_RE.search(next_para):
                break
            block.append(next_para)
        text = " ".join(block)
        text = re.sub(r"\s+", " ", text).strip()
        if text and text not in seen:
            highlights.append(text)
            seen.add(text)
        if len(highlights) >= limit:
            break
    return highlights


def build_entry(path: Path) -> dict:
    paragraphs = normalize_paragraphs(extract_docx_paragraphs(path))
    title = infer_title(path, paragraphs)
    models = detect_models(path, paragraphs)
    highlights = extract_highlights(paragraphs)
    preview = paragraphs[:24]
    return {
        "file_name": path.name,
        "full_path": str(path),
        "relative_path": str(path.relative_to(ROOT)),
        "category_chain": list(path.relative_to(ROOT).parts[:-1]),
        "title": title,
        "models": models,
        "paragraph_count": len(paragraphs),
        "preview_paragraphs": preview,
        "highlights": highlights,
        "full_text": "\n".join(paragraphs),
    }


def write_markdown(entries: list[dict], output_path: Path) -> None:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for entry in entries:
        key = " / ".join(entry["category_chain"][:2]) if entry["category_chain"] else "Uncategorized"
        grouped[key].append(entry)

    lines: list[str] = []
    lines.append("# English Datasheet Knowledge")
    lines.append("")
    lines.append(f"Source root: `{ROOT}`")
    lines.append("")
    lines.append(f"Datasheet DOCX count: `{len(entries)}`")
    lines.append("")
    lines.append("This memory was generated from DOCX datasheet files only.")
    lines.append("")
    lines.append("## Family Index")
    lines.append("")
    for group_name in sorted(grouped):
        lines.append(f"- `{group_name}`: `{len(grouped[group_name])}` datasheets")
    lines.append("")

    for group_name in sorted(grouped):
        items = sorted(grouped[group_name], key=lambda item: item["relative_path"])
        lines.append(f"## {group_name}")
        lines.append("")
        for item in items:
            lines.append(f"### {item['title']}")
            lines.append("")
            lines.append(f"- File: `{item['relative_path']}`")
            if item["models"]:
                lines.append(f"- Models: `{', '.join(item['models'])}`")
            lines.append(f"- Paragraphs: `{item['paragraph_count']}`")
            if item["highlights"]:
                lines.append("- Highlights:")
                for highlight in item["highlights"][:6]:
                    lines.append(f"  - {highlight}")
            elif item["preview_paragraphs"]:
                lines.append("- Preview:")
                for preview in item["preview_paragraphs"][:4]:
                    lines.append(f"  - {preview}")
            lines.append("")

    output_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    files = iter_datasheets(ROOT)
    entries = [build_entry(path) for path in files]

    catalog = {
        "source_root": str(ROOT),
        "datasheet_count": len(entries),
        "entries": entries,
    }

    json_path = OUT_DIR / "english_datasheet_catalog.json"
    md_path = OUT_DIR / "english_datasheet_knowledge.md"
    json_path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(entries, md_path)

    print(json.dumps({
        "datasheet_count": len(entries),
        "json_path": str(json_path),
        "markdown_path": str(md_path),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
