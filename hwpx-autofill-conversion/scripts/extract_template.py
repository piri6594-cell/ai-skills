from __future__ import annotations

import argparse
from pathlib import Path

from hwpx_package import (
    extract_label_candidates,
    extract_label_candidates_from_kordoc,
    extract_placeholders_from_files,
    extract_section_summaries,
    kordoc_available,
    load_json,
    merge_label_candidates,
    normalize_input_to_hwpx,
    preview_text,
    read_package,
    run_kordoc_json,
    save_json,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract placeholders and fill candidates from an HWPX template.")
    parser.add_argument("input_path", help="Path to .hwpx or .hwp")
    parser.add_argument("output_json", help="Path to write extraction report JSON")
    parser.add_argument("--kordoc-json", dest="kordoc_json", help="Optional precomputed kordoc JSON path")
    parser.add_argument("--prefer-kordoc", action="store_true", help="Try kordoc first when available")
    args = parser.parse_args()

    input_path = Path(args.input_path)
    output_json = Path(args.output_json)

    hwpx_path, temp_converted = normalize_input_to_hwpx(input_path)
    files = read_package(hwpx_path)
    xml_candidates = extract_label_candidates(files)

    kordoc_payload = None
    if args.kordoc_json:
        kordoc_payload = load_json(Path(args.kordoc_json))
    elif args.prefer_kordoc and kordoc_available():
        kordoc_payload = run_kordoc_json(input_path)

    kordoc_candidates = extract_label_candidates_from_kordoc(kordoc_payload) if kordoc_payload else []
    analysis_engine = "xml"
    if kordoc_payload:
        analysis_engine = "kordoc+xml"

    report = {
        "source_path": str(input_path),
        "resolved_hwpx_path": str(hwpx_path),
        "analysis_engine": analysis_engine,
        "placeholders": extract_placeholders_from_files(files),
        "label_candidates": merge_label_candidates(xml_candidates, kordoc_candidates),
        "sections": extract_section_summaries(files),
        "preview_text": preview_text(files),
    }
    if kordoc_payload:
        report["kordoc"] = {
            "metadata": kordoc_payload.get("metadata", {}),
            "markdown": kordoc_payload.get("markdown", ""),
            "block_count": len(kordoc_payload.get("blocks", [])),
        }
    save_json(output_json, report)

    if temp_converted and temp_converted.exists():
        temp_converted.unlink()

    print(f"Wrote extraction report: {output_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
