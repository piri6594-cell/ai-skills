from __future__ import annotations

import argparse
from pathlib import Path

from hwpx_package import load_json, save_json


def normalize(text: str) -> str:
    return "".join(str(text).strip().split())


def candidate_score(key: str, label: str) -> tuple[int, str]:
    key_raw = str(key).strip()
    label_raw = str(label).strip()
    key_norm = normalize(key_raw)
    label_norm = normalize(label_raw)

    if not key_norm or not label_norm:
        return (0, "empty")
    if key_raw == label_raw:
        return (100, "exact")
    if key_norm == label_norm:
        return (95, "normalized-exact")
    if key_raw in label_raw or key_norm in label_norm:
        return (80, "contains")
    if label_raw in key_raw or label_norm in key_norm:
        return (70, "reverse-contains")
    return (0, "none")


def build_suggestions(extract_data: dict, values: dict[str, str]) -> dict:
    suggestions = []
    label_candidates = extract_data.get("label_candidates", [])

    for key, value in values.items():
        ranked = []
        for candidate in label_candidates:
            score, reason = candidate_score(key, candidate.get("label", ""))
            if score <= 0:
                continue
            ranked.append(
                {
                    "label": candidate.get("label", ""),
                    "direction": candidate.get("direction", "right"),
                    "score": score,
                    "reason": reason,
                    "current_value": candidate.get("current_value", ""),
                    "section": candidate.get("section"),
                }
            )
        ranked.sort(key=lambda item: (-item["score"], item["label"]))

        if ranked and ranked[0]["score"] >= 95:
            status = "matched"
        elif ranked:
            status = "review"
        else:
            status = "unmatched"

        suggestions.append(
            {
                "key": key,
                "value": value,
                "status": status,
                "candidates": ranked[:5],
            }
        )

    suggested_fill_config = {
        "text_replacements": {},
        "label_fills": [],
    }
    seen = set()
    for item in suggestions:
        if item["status"] != "matched" or not item["candidates"]:
            continue
        candidate = item["candidates"][0]
        dedupe_key = (item["key"], candidate["label"], candidate["direction"])
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        suggested_fill_config["label_fills"].append(
            {
                "label": candidate["label"],
                "direction": candidate["direction"],
                "value": item["value"],
            }
        )

    return {
        "suggestions": suggestions,
        "suggested_fill_config": suggested_fill_config,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Suggest label mappings from an extract report and value JSON.")
    parser.add_argument("extract_json")
    parser.add_argument("values_json")
    parser.add_argument("output_json")
    parser.add_argument(
        "--fill-config-output",
        dest="fill_config_output",
        help="Optional path to write the suggested_fill_config as a standalone fill JSON.",
    )
    args = parser.parse_args()

    extract_data = load_json(Path(args.extract_json))
    values = load_json(Path(args.values_json))
    output = build_suggestions(extract_data, values)
    save_json(Path(args.output_json), output)
    print(f"Wrote mapping suggestions: {args.output_json}")
    if args.fill_config_output:
        save_json(Path(args.fill_config_output), output["suggested_fill_config"])
        print(f"Wrote suggested fill config: {args.fill_config_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
