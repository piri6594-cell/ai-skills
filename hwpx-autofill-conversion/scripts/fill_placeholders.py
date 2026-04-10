from __future__ import annotations

import argparse
import os
from pathlib import Path
import xml.etree.ElementTree as ET

from hwpx_package import (
    coerce_text_replacements,
    copy_to_output,
    load_json,
    normalize_input_to_hwpx,
    read_package,
    refresh_preview_text,
    replace_text_nodes,
    write_package,
)


def replace_images(files: dict[str, bytes], config: dict) -> int:
    replaced = 0
    for key, value in config.items():
        if not key.startswith("_img_"):
            continue
        image_path = Path(value)
        if not image_path.is_file():
            continue
        image_key = key[5:]
        matches = [name for name in files if name.startswith("BinData/") and image_key in name]
        if not matches:
            continue
        files[matches[0]] = image_path.read_bytes()
        replaced += 1
    return replaced


def main() -> int:
    parser = argparse.ArgumentParser(description="Fill simple text placeholders in HWPX files.")
    parser.add_argument("template_path")
    parser.add_argument("data_json")
    parser.add_argument("output_path")
    args = parser.parse_args()

    template_path = Path(args.template_path)
    data_json = Path(args.data_json)
    output_path = Path(args.output_path)

    config = load_json(data_json)
    replacements = coerce_text_replacements(config)

    hwpx_path, temp_converted = normalize_input_to_hwpx(template_path)
    copy_to_output(hwpx_path, output_path)
    files = read_package(output_path)

    changed_nodes = 0
    for name, data in list(files.items()):
        if not name.endswith(".xml"):
            continue
        try:
            root = ET.fromstring(data)
        except ET.ParseError:
            continue
        changed_nodes += replace_text_nodes(root, replacements)
        files[name] = ET.tostring(root, encoding="utf-8", xml_declaration=True)

    image_replacements = replace_images(files, config)
    refresh_preview_text(files)
    write_package(output_path, files)

    if temp_converted and temp_converted.exists():
        temp_converted.unlink()

    print(f"Filled HWPX: {output_path}")
    print(f"Changed text nodes: {changed_nodes}")
    print(f"Replaced images: {image_replacements}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
