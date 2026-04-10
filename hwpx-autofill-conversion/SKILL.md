---
name: hwpx-autofill-conversion
description: Use when receiving `.hwpx` or `.hwp` report forms that must be analyzed, filled, and validated while preserving document structure and delivering a clean output file for Hancom Office.
paths: "**/*.hwpx, **/*.hwp"
---

# HWPX Autofill Conversion

## Overview
Use this skill for HWPX form work where layout preservation matters more than freeform rewriting.

The workflow is:
1. inspect the template first
2. choose the safest fill engine
3. validate the output before handoff

## When To Use
- Existing HWPX form must be filled without breaking structure
- Placeholder replacement alone may be risky
- Table labels and nearby cells matter
- The user wants a filled copy, not a redesigned document

Do not overwrite the original file. Always write a copied output.

## Engine Selection
- `extract_template.py`
  - Run first to inspect placeholders, preview text, section summaries, and table label candidates
  - If `kordoc` is installed, prefer `extract_template.py input.hwpx extract.json --prefer-kordoc`
  - This combines XML placeholder inspection with `kordoc` table/block analysis
- `fill_placeholders.py`
  - Use for simple placeholder-driven templates such as `[성명]`, `[보고서명]`
- `structured_fill_hwpx.py`
  - Use when values must be filled relative to labels in tables or when direct text-node replacement is safer than raw XML byte replacement
- `validate_hwpx.py`
  - Run after filling to verify ZIP structure, XML parseability, and expected text presence

## Recommended Workflow
1. Copy the source to a new output path
2. Run `extract_template.py` and inspect:
   - placeholders
   - section summaries
   - table label candidates
3. Choose engine:
   - simple placeholders only: `fill_placeholders.py`
   - table-driven or structure-sensitive: `structured_fill_hwpx.py`
4. Run `validate_hwpx.py`
5. If the document is Korean-heavy or visually sensitive, reopen it in Hancom Office and visually check line overflow, font issues, and broken tables

## Commands
```bash
python scripts/extract_template.py input.hwpx extract.json
python scripts/extract_template.py input.hwpx extract.json --prefer-kordoc
python scripts/suggest_fill_mapping.py extract.json values.json mapping.json --fill-config-output fill.json
python scripts/fill_placeholders.py template.hwpx data.json output.hwpx
python scripts/structured_fill_hwpx.py template.hwpx fill.json output.hwpx
python scripts/validate_hwpx.py output.hwpx --expect-json expect.json
```

## Config Shapes
Simple fill:
```json
{
  "text_replacements": {
    "[성명]": "홍길동",
    "[보고서명]": "하천 정비 검토보고서"
  }
}
```

Structured fill:
```json
{
  "text_replacements": {
    "[성명]": "홍길동"
  },
  "label_fills": [
    {
      "label": "성명",
      "direction": "right",
      "value": "홍길동"
    }
  ]
}
```

Validation:
```json
{
  "expected_text": [
    "홍길동",
    "하천 정비 검토보고서"
  ]
}
```

## Safety Rules
- Preserve existing structure and style-bearing nodes whenever possible
- Replace text in place instead of rebuilding the whole XML tree
- Avoid adding new sections, manifests, or BinData references unless required
- Keep temp work outside the workspace root
- For Korean content, follow the Korean-safe session rules before bulk generation

## Residual Limitation
Font auto-fit and line overflow are still rendering problems. Treat them as a validation and final adjustment step, not as the primary fill engine.
