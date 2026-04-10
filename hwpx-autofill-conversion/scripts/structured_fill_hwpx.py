from __future__ import annotations

import argparse
from pathlib import Path
import xml.etree.ElementTree as ET

from hwpx_package import (
    coerce_text_replacements,
    copy_to_output,
    iter_tables,
    load_json,
    normalize_input_to_hwpx,
    read_package,
    refresh_preview_text,
    replace_text_nodes,
    set_cell_text,
    table_to_rows,
    tag_name,
    cell_text,
    write_package,
)


def apply_label_fill(root: ET.Element, label_fill: dict) -> int:
    label = str(label_fill["label"]).strip()
    direction = str(label_fill.get("direction", "right")).strip().lower()
    value = str(label_fill["value"])
    occurrence_target = int(label_fill.get("occurrence", 1))

    occurrence = 0
    for table in iter_tables(root):
        rows = table_to_rows(table)
        for row_index, row in enumerate(rows):
            for col_index, cell in enumerate(row):
                if cell_text(cell) != label:
                    continue
                occurrence += 1
                if occurrence != occurrence_target:
                    continue
                if direction == "right" and col_index + 1 < len(row):
                    return 1 if set_cell_text(row[col_index + 1], value) else 0
                if direction == "down" and row_index + 1 < len(rows) and col_index < len(rows[row_index + 1]):
                    return 1 if set_cell_text(rows[row_index + 1][col_index], value) else 0
                return 0
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Fill HWPX content using placeholders and label-based table targeting.")
    parser.add_argument("template_path")
    parser.add_argument("config_json")
    parser.add_argument("output_path")
    args = parser.parse_args()

    template_path = Path(args.template_path)
    config_json = Path(args.config_json)
    output_path = Path(args.output_path)

    config = load_json(config_json)
    replacements = coerce_text_replacements(config)
    label_fills = config.get("label_fills", [])

    hwpx_path, temp_converted = normalize_input_to_hwpx(template_path)
    copy_to_output(hwpx_path, output_path)
    files = read_package(output_path)

    changed_nodes = 0
    label_changes = 0
    for name, data in list(files.items()):
        if not name.endswith(".xml"):
            continue
        try:
            root = ET.fromstring(data)
        except ET.ParseError:
            continue
        changed_nodes += replace_text_nodes(root, replacements)
        for label_fill in label_fills:
            label_changes += apply_label_fill(root, label_fill)
        files[name] = ET.tostring(root, encoding="utf-8", xml_declaration=True)

    refresh_preview_text(files)
    write_package(output_path, files)

    if temp_converted and temp_converted.exists():
        temp_converted.unlink()

    print(f"Structured fill complete: {output_path}")
    print(f"Changed text nodes: {changed_nodes}")
    print(f"Label-based fills: {label_changes}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
