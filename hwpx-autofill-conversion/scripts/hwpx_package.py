from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path


PLACEHOLDER_PATTERN = re.compile(r"\[[^\[\]\r\n]+\]")


def tag_name(elem: ET.Element) -> str:
    return elem.tag.rsplit("}", 1)[-1]


def namespace_of(elem: ET.Element) -> str:
    if elem.tag.startswith("{") and "}" in elem.tag:
        return elem.tag.split("}", 1)[0] + "}"
    return ""


def convert_hwp_to_hwpx(input_path: Path) -> Path:
    output_path = input_path.with_name(input_path.stem + "_converted.hwpx")
    script = (
        "$hwp = New-Object -ComObject HWPFrame.HwpObject;"
        "$hwp.RegisterModule('FilePathCheckDLL', 'FilePathCheckerModule');"
        f"$hwp.Open('{str(input_path)}', 'HWP', 'forceopen:true');"
        f"$hwp.SaveAs('{str(output_path)}', 'HWPX', '');"
        "$hwp.Quit();"
    )
    result = subprocess.run(
        ["powershell", "-ExecutionPolicy", "Bypass", "-Command", script],
        capture_output=True,
        text=True,
    )
    if not output_path.exists():
        raise RuntimeError(result.stderr or "Failed to convert HWP to HWPX.")
    return output_path


def normalize_input_to_hwpx(input_path: Path) -> tuple[Path, Path | None]:
    if input_path.suffix.lower() == ".hwp":
        converted = convert_hwp_to_hwpx(input_path)
        return converted, converted
    return input_path, None


def read_package(path: Path) -> dict[str, bytes]:
    with zipfile.ZipFile(path, "r") as zf:
        return {name: zf.read(name) for name in zf.namelist()}


def write_package(path: Path, files: dict[str, bytes]) -> None:
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, data in files.items():
            zf.writestr(name, data)


def parse_xml_bytes(data: bytes) -> ET.Element:
    return ET.fromstring(data)


def iter_section_names(files: dict[str, bytes]) -> list[str]:
    return sorted(
        name
        for name in files
        if name.startswith("Contents/section") and name.endswith(".xml")
    )


def get_text_nodes(root: ET.Element) -> list[ET.Element]:
    return [elem for elem in root.iter() if tag_name(elem) == "t"]


def node_text_join(root: ET.Element) -> str:
    return "".join((elem.text or "") for elem in get_text_nodes(root)).strip()


def cell_text(cell: ET.Element) -> str:
    return "".join((elem.text or "") for elem in get_text_nodes(cell)).strip()


def set_cell_text(cell: ET.Element, value: str) -> bool:
    text_nodes = get_text_nodes(cell)
    if not text_nodes:
        ns = namespace_of(cell)
        paragraph = next((elem for elem in cell.iter() if tag_name(elem) == "p"), None)
        if paragraph is None:
            paragraph = ET.SubElement(cell, f"{ns}p")
        run = next((elem for elem in paragraph.iter() if tag_name(elem) == "run"), None)
        if run is None:
            run = ET.SubElement(paragraph, f"{ns}run")
        text_node = ET.SubElement(run, f"{ns}t")
        text_node.text = value
        return True
    text_nodes[0].text = value
    for node in text_nodes[1:]:
        node.text = ""
    return True


def iter_tables(root: ET.Element) -> list[ET.Element]:
    return [elem for elem in root.iter() if tag_name(elem) == "tbl"]


def table_to_rows(table: ET.Element) -> list[list[ET.Element]]:
    rows: list[list[ET.Element]] = []
    for row in table:
        if tag_name(row) != "tr":
            continue
        rows.append([cell for cell in row if tag_name(cell) == "tc"])
    return rows


def extract_placeholders_from_files(files: dict[str, bytes]) -> list[str]:
    found: set[str] = set()
    for name in iter_section_names(files) + [n for n in files if n.endswith("header.xml")]:
        try:
            root = parse_xml_bytes(files[name])
        except ET.ParseError:
            continue
        text = node_text_join(root)
        found.update(PLACEHOLDER_PATTERN.findall(text))
    return sorted(found)


def extract_label_candidates(files: dict[str, bytes]) -> list[dict[str, object]]:
    candidates: list[dict[str, object]] = []
    for section_name in iter_section_names(files):
        root = parse_xml_bytes(files[section_name])
        for table_index, table in enumerate(iter_tables(root)):
            rows = table_to_rows(table)
            for row_index, row in enumerate(rows):
                for col_index, cell in enumerate(row):
                    label = cell_text(cell)
                    if not label:
                        continue
                    if col_index + 1 < len(row):
                        candidates.append(
                            {
                                "section": section_name,
                                "table_index": table_index,
                                "row_index": row_index,
                                "col_index": col_index,
                                "label": label,
                                "direction": "right",
                                "current_value": cell_text(row[col_index + 1]),
                            }
                        )
                    if row_index + 1 < len(rows) and col_index < len(rows[row_index + 1]):
                        candidates.append(
                            {
                                "section": section_name,
                                "table_index": table_index,
                                "row_index": row_index,
                                "col_index": col_index,
                                "label": label,
                                "direction": "down",
                                "current_value": cell_text(rows[row_index + 1][col_index]),
                            }
                        )
    return candidates


def extract_section_summaries(files: dict[str, bytes], max_chars: int = 160) -> list[dict[str, str]]:
    summaries: list[dict[str, str]] = []
    for name in iter_section_names(files):
        root = parse_xml_bytes(files[name])
        text = " ".join(node_text_join(root).split())
        summaries.append({"section": name, "summary": text[:max_chars]})
    return summaries


def preview_text(files: dict[str, bytes]) -> str:
    data = files.get("Preview/PrvText.txt")
    if not data:
        return ""
    return data.decode("utf-8", errors="replace")


def refresh_preview_text(files: dict[str, bytes]) -> None:
    section_texts: list[str] = []
    for name in iter_section_names(files):
        root = parse_xml_bytes(files[name])
        text = " ".join(node_text_join(root).split())
        if text:
            section_texts.append(text)
    if section_texts:
        files["Preview/PrvText.txt"] = ("\n".join(section_texts) + "\n").encode("utf-8")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def kordoc_available() -> bool:
    result = subprocess.run(
        [
            "powershell",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            "Get-Command kordoc -ErrorAction SilentlyContinue | Out-Null; if ($?) { exit 0 } else { exit 1 }",
        ],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def run_kordoc_json(input_path: Path) -> dict | None:
    ps_command = (
        "$utf8 = New-Object System.Text.UTF8Encoding($false);"
        "[Console]::OutputEncoding = $utf8;"
        "$OutputEncoding = $utf8;"
        f"kordoc '{str(input_path)}' --format json --silent"
    )
    result = subprocess.run(
        [
            "powershell",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            ps_command,
        ],
        capture_output=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        return None
    text = result.stdout.strip()
    if not text:
        return None
    return json.loads(text)


def extract_label_candidates_from_kordoc(payload: dict) -> list[dict[str, object]]:
    candidates: list[dict[str, object]] = []
    for block_index, block in enumerate(payload.get("blocks", [])):
        if block.get("type") != "table":
            continue
        table = block.get("table") or {}
        rows = table.get("cells") or []
        for row_index, row in enumerate(rows):
            if not isinstance(row, list):
                continue
            for col_index, cell in enumerate(row):
                if not isinstance(cell, dict):
                    continue
                label = str(cell.get("text", "")).strip()
                if not label:
                    continue
                if col_index + 1 < len(row) and isinstance(row[col_index + 1], dict):
                    candidates.append(
                        {
                            "section": f"kordoc:block:{block_index}",
                            "table_index": block_index,
                            "row_index": row_index,
                            "col_index": col_index,
                            "label": label,
                            "direction": "right",
                            "current_value": str(row[col_index + 1].get("text", "")),
                            "source": "kordoc",
                            "page_number": block.get("pageNumber"),
                        }
                    )
                if row_index + 1 < len(rows) and col_index < len(rows[row_index + 1]) and isinstance(rows[row_index + 1][col_index], dict):
                    candidates.append(
                        {
                            "section": f"kordoc:block:{block_index}",
                            "table_index": block_index,
                            "row_index": row_index,
                            "col_index": col_index,
                            "label": label,
                            "direction": "down",
                            "current_value": str(rows[row_index + 1][col_index].get("text", "")),
                            "source": "kordoc",
                            "page_number": block.get("pageNumber"),
                        }
                    )
    return candidates


def merge_label_candidates(*groups: list[dict[str, object]]) -> list[dict[str, object]]:
    merged: list[dict[str, object]] = []
    seen: set[tuple] = set()
    for group in groups:
        for item in group:
            key = (
                item.get("section"),
                item.get("table_index"),
                item.get("row_index"),
                item.get("col_index"),
                item.get("label"),
                item.get("direction"),
                item.get("current_value"),
            )
            if key in seen:
                continue
            seen.add(key)
            merged.append(item)
    return merged


def coerce_text_replacements(config: dict) -> dict[str, str]:
    if "text_replacements" in config:
        mapping = config["text_replacements"] or {}
        return {str(k): str(v) for k, v in mapping.items()}
    replacements: dict[str, str] = {}
    for key, value in config.items():
        if key.startswith("_"):
            continue
        key_text = str(key)
        if key_text.startswith("[") and key_text.endswith("]"):
            replacements[key_text] = str(value)
        else:
            replacements[f"[{key_text}]"] = str(value)
    return replacements


def replace_text_nodes(root: ET.Element, replacements: dict[str, str]) -> int:
    changed = 0
    for node in get_text_nodes(root):
        original = node.text or ""
        updated = original
        for old, new in replacements.items():
            updated = updated.replace(old, new)
        if updated != original:
            node.text = updated
            changed += 1
    return changed


def copy_to_output(source: Path, output: Path) -> None:
    shutil.copy(source, output)


def temp_hwpx_copy(path: Path) -> Path:
    temp_dir = Path(tempfile.mkdtemp(prefix="hwpx_pkg_"))
    temp_path = temp_dir / path.name
    shutil.copy(path, temp_path)
    return temp_path
