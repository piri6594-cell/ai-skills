from __future__ import annotations

import argparse
from pathlib import Path
import xml.etree.ElementTree as ET

from hwpx_package import iter_section_names, load_json, node_text_join, parse_xml_bytes, preview_text, read_package


REQUIRED_ENTRIES = [
    "mimetype",
    "META-INF/manifest.xml",
    "Contents/content.hpf",
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate HWPX package structure and expected text.")
    parser.add_argument("hwpx_path")
    parser.add_argument("--expect-json", dest="expect_json")
    args = parser.parse_args()

    hwpx_path = Path(args.hwpx_path)
    files = read_package(hwpx_path)

    errors: list[str] = []
    for name in REQUIRED_ENTRIES:
        if name not in files:
            errors.append(f"Missing required entry: {name}")

    section_names = iter_section_names(files)
    if not section_names:
        errors.append("No section XML files found.")

    collected_text: list[str] = []
    for name, data in files.items():
        if not name.endswith(".xml"):
            continue
        try:
            root = parse_xml_bytes(data)
        except ET.ParseError as exc:
            errors.append(f"XML parse failed for {name}: {exc}")
            continue
        if name in section_names:
            collected_text.append(node_text_join(root))

    collected_text.append(preview_text(files))
    full_text = "\n".join(text for text in collected_text if text)

    if args.expect_json:
        expect_data = load_json(Path(args.expect_json))
        for expected in expect_data.get("expected_text", []):
            if str(expected) not in full_text:
                errors.append(f"Expected text not found: {expected}")

    if errors:
        print("FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("PASS")
    print(f"Validated file: {hwpx_path}")
    print(f"Sections: {len(section_names)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
