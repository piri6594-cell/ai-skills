from __future__ import annotations

import argparse
from pathlib import Path

from hwpx_package import load_json, save_json


def normalize_value_lookup(values: dict) -> dict[str, str]:
    return {str(key).strip(): str(value) for key, value in values.items()}


def key_from_placeholder(placeholder: str) -> str:
    text = str(placeholder).strip()
    if text.startswith("[") and text.endswith("]"):
        return text[1:-1].strip()
    return text


def resolve_value_for_label(label: str, values: dict[str, str]) -> str | None:
    if label in values:
        return values[label]
    for key, value in values.items():
        if key and key in label:
            return value
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Build fill config JSON from extract report and user values.")
    parser.add_argument("extract_json")
    parser.add_argument("values_json")
    parser.add_argument("output_json")
    args = parser.parse_args()

    extract_data = load_json(Path(args.extract_json))
    values = normalize_value_lookup(load_json(Path(args.values_json)))

    text_replacements: dict[str, str] = {}
    for placeholder in extract_data.get("placeholders", []):
        key = key_from_placeholder(placeholder)
        if key in values:
            text_replacements[str(placeholder)] = values[key]

    label_fills = []
    seen = set()
    for candidate in extract_data.get("label_candidates", []):
        label = str(candidate.get("label", "")).strip()
        resolved_value = resolve_value_for_label(label, values)
        if not label or resolved_value is None:
            continue
        fill = {
            "label": label,
            "direction": str(candidate.get("direction", "right")),
            "value": resolved_value,
        }
        if "occurrence" in candidate:
            fill["occurrence"] = candidate["occurrence"]
        key = (fill["label"], fill["direction"], fill["value"], fill.get("occurrence", 1))
        if key in seen:
            continue
        seen.add(key)
        label_fills.append(fill)

    output = {
        "text_replacements": text_replacements,
        "label_fills": label_fills,
    }
    save_json(Path(args.output_json), output)
    print(f"Wrote fill config: {args.output_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
