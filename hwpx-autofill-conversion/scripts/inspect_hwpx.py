#!/usr/bin/env python3
import argparse
import sys
import textwrap
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path


def safe_print(text: str = "") -> None:
    encoding = sys.stdout.encoding or "utf-8"
    sys.stdout.buffer.write((text + "\n").encode(encoding, errors="replace"))


def wrap(text: str, width: int = 88) -> str:
    text = " ".join(text.split())
    return "\n".join(textwrap.wrap(text, width=width)) if text else ""


def extract_preview(zf: zipfile.ZipFile) -> str:
    try:
        with zf.open("Preview/PrvText.txt") as handle:
            return handle.read().decode("utf-8", errors="replace").strip()
    except KeyError:
        return ""


def extract_section_snippet(zf: zipfile.ZipFile, entry_name: str, limit: int) -> str:
    with zf.open(entry_name) as handle:
        data = handle.read()
    root = ET.fromstring(data)
    parts = []
    for elem in root.iter():
        if elem.tag.endswith("}t") and elem.text:
            parts.append(elem.text)
    return " ".join(" ".join(parts).split())[:limit]


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect an HWPX file without editing it.")
    parser.add_argument("path", help="Path to the .hwpx file")
    parser.add_argument("--preview-lines", type=int, default=20, help="Number of preview lines to show")
    parser.add_argument("--snippet-chars", type=int, default=180, help="Maximum characters per section snippet")
    args = parser.parse_args()

    target = Path(args.path)
    if not target.exists():
        raise SystemExit(f"File not found: {target}")

    with zipfile.ZipFile(target) as zf:
        names = sorted(zf.namelist())
        safe_print(f"FILE: {target}")
        safe_print("")
        safe_print("ENTRIES:")
        for name in names:
            safe_print(f"- {name}")

        preview = extract_preview(zf)
        safe_print("")
        safe_print("PREVIEW:")
        if preview:
            preview_lines = preview.splitlines()[: args.preview_lines]
            for line in preview_lines:
                safe_print(line)
        else:
            safe_print("(Preview/PrvText.txt not found)")

        section_names = [name for name in names if name.startswith("Contents/section") and name.endswith(".xml")]
        safe_print("")
        safe_print("SECTIONS:")
        if not section_names:
            safe_print("(No section XML files found)")
            return 0

        for section_name in section_names:
            snippet = extract_section_snippet(zf, section_name, args.snippet_chars)
            safe_print(f"- {section_name}")
            if snippet:
                safe_print(wrap(snippet, width=84))
            else:
                safe_print("(No text nodes found)")
            safe_print("")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
