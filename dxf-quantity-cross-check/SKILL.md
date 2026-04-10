---
name: dxf-quantity-cross-check
description: "Use when comparing DXF drawing annotations in layout tabs with quantity takeoff spreadsheets, especially requests like \uB3C4\uBA74 \uC218\uB7C9 \uBE44\uAD50 or \uBC30\uCE58\uD0ED \uC9C0\uC2DC\uC120 \uBB38\uAD6C vs \uC218\uB7C9\uC0B0\uCD9C, and the result must be delivered as a separate Excel review workbook without modifying originals."
paths: "**/*.dxf"
---

# DXF Quantity Cross Check

## Overview

Compare quantity-bearing text in DXF layout tabs against quantity takeoff workbooks and write the review result to a new Excel file. Keep every original drawing and quantity workbook untouched.

## Core Rules

- Never modify original `.dxf`, `.xls`, or `.xlsx` files.
- Check Korean filenames, paths, and extracted text for encoding issues before comparing values.
- Use safe Excel tooling only. Prefer Excel COM or `openpyxl`. Never build `.xlsx` by zip/xml assembly.
- Treat success as: the review workbook opens in Excel without repair.

## Workflow

1. Confirm the drawing folder and quantity folder.
2. Scan the entire DXF folder first and classify files into:
   - `direct compare`: drawings that contain explicit quantity text or leader-note values
   - `reference only`: drawings that help identify the item but do not contain a directly comparable quantity
   - `exclude`: title sheets, templates, or files unrelated to quantity comparison
3. Extract candidate drawing text from DXF using text search first. Prioritize strings like `L=`, `A=`, `B=`, `H=`, pipe notes, manhole notes, riprap labels, paving labels, railing labels, cofferdam labels, temporary drainage labels, subbase labels, and deck-cover labels.
4. Record the DXF filename, line number, and extracted string as evidence.
5. Identify the matching workbook, sheet, and cell in the quantity folder. Always locate the exact source cell, not just the summary value.
6. Verify 2-3 sample matches before bulk comparison when the same comparison pattern repeats across many items.
7. Compare values with clear handling for rounding:
   - keep raw drawing values and raw workbook values separately
   - note when the workbook summary is rounded but the detailed basis matches
8. Mark each item as one of:
   - `match`
   - `mismatch`
   - `needs review`
9. Save the result as a separate workbook in the working folder.

## Comparison Guidance

- Prefer explicit quantity text from layout-tab leader notes over generic labels.
- When the drawing shows segmented lengths, compare against the detailed quantity sheet first, then the summary sheet.
- When the drawing shows one representative value but the workbook totals several segments, explain the aggregation logic in the review workbook.
- If the drawing shows a single segment and the workbook total is larger, do not assume it is correct. Mark `needs review` unless the additional segments are directly evidenced.
- If a drawing note cannot be mapped to any quantity item, keep it in the result workbook as `needs review` with the raw note preserved.

## Review Workbook

Create a separate Excel workbook with these sheets. If the user's existing workflow already uses Korean sheet names, keep those names instead of translating them.

- `summary`: high-level results and counts
- `detail`: one row per compared item with drawing evidence and workbook cell references
- `drawing-evidence`: raw extracted DXF text with file and line number
- `review-scope`: every reviewed DXF file classified as direct compare, reference only, or exclude

Include at minimum these columns in the detail sheet:

- category
- item
- drawing evidence
- drawing note
- quantity file
- quantity cell reference
- drawing value
- workbook value
- result
- comment

## Validation

- Re-open the generated workbook in Excel after saving.
- If Excel shows repair or recovery behavior, the task is not complete.
- In the final report, always give:
  - saved workbook path
  - created sheet names
  - a few sample facility or stream names reflected in the review

## Practical Notes

- If CAD-specific tooling is unavailable, DXF text search with line-number evidence is still valid for first-pass comparison.
- When multiple drawings repeat the same item, use the most explicit drawing as the primary comparison source and list the others in the scope sheet.
- Keep the workbook focused on traceability. Every conclusion should be traceable back to one DXF text snippet and one workbook cell.
