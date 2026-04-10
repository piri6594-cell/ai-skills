---
name: xlsx
description: Use when tasks involve creating, editing, auditing, or analyzing Excel workbooks and delimited spreadsheets (`.xlsx`, `.xlsm`, `.xls`, `.csv`, `.tsv`), especially when formulas, formatting fidelity, cached recalculation, or finance-style spreadsheet conventions matter.
paths: "**/*.xlsx, **/*.xlsm, **/*.xls, **/*.csv, **/*.tsv"
---

# XLSX

Port of Anthropic's `xlsx` skill adapted for Codex in this Windows-heavy workspace.

## Overview

- On Windows, prefer `win32com` when Excel fidelity, recalculation, or legacy `.xls` handling matters.
- Use `openpyxl` for `.xlsx` and `.xlsm` formulas, formatting, comments, merges, widths, and workbook structure edits.
- Use `pandas` for analysis, cleanup, joins, pivots, and CSV/TSV workflows.
- Keep derived values as Excel formulas when the workbook should stay dynamic.
- Avoid `xlrd` for Korean legacy spreadsheet workflows; prefer Excel COM when possible.

## When to Use

- Create a new Excel workbook.
- Update an existing workbook without breaking formulas or formatting.
- Convert `.csv` or `.tsv` inputs into a polished `.xlsx` deliverable.
- Audit workbooks for broken references, stale cached values, or formula errors.
- Build or revise finance-style spreadsheets where number formats and color conventions matter.

## Core Workflow

1. Classify the task first: create, edit, analyze, or audit.
2. If the file already exists, inspect workbook structure, sheet names, formulas, styles, and hidden content before editing.
3. Pick the tool deliberately:
   - `win32com` for Excel-accurate behavior, `.xls`, or final recalculation
   - `openpyxl` for workbook edits and formatting preservation
   - `pandas` for data analysis and delimited files
4. Use Excel formulas instead of Python-computed hardcoded results wherever feasible.
5. Recalculate after saving, then reopen and verify the output.
6. Existing template conventions always override default styling rules.

## Tool Selection

### win32com

Prefer `win32com` when:

- the workbook must behave exactly like Excel
- cached formula values must be refreshed reliably
- the file is `.xls` or depends on Excel-only behavior
- macros, named ranges, external links, or complex formatting must survive intact

```python
import win32com.client as win32

excel = win32.Dispatch("Excel.Application")
excel.Visible = False
excel.DisplayAlerts = False
wb = excel.Workbooks.Open(path)
excel.CalculateFullRebuild()
wb.Save()
wb.Close(False)
excel.Quit()
```

### openpyxl

Prefer `openpyxl` when:

- editing `.xlsx` or `.xlsm` structure directly
- writing formulas, styles, fills, alignment, merges, widths, or comments
- reading and modifying workbooks without launching Excel

Notes:

- Do not save a workbook opened with `data_only=True`; formulas can be lost.
- For macro-enabled files, prefer COM first. If needed, evaluate `keep_vba=True`.

### pandas

Prefer `pandas` when:

- filtering, grouping, pivoting, joining, or summarizing table data
- normalizing CSV or TSV files before exporting to Excel
- bulk data cleanup matters more than cell-level formatting

## Formula Rules

- Sums, averages, growth rates, ratios, and deltas should remain Excel formulas when possible.
- Put assumptions in dedicated cells and reference them from formulas.
- Prefer referenced cells over magic numbers.
- Validate 2-3 representative formulas before filling large ranges.
- Remember Excel is 1-indexed; DataFrame offsets often differ from worksheet row numbers.
- Guard against `#REF!`, `#DIV/0!`, `#VALUE!`, `#N/A`, and `#NAME?`.

Wrong:

```python
total = df["sales"].sum()
ws["B10"] = total
```

Correct:

```python
ws["B10"] = "=SUM(B2:B9)"
```

## Recalculation and Verification

Preferred recalculation order:

1. Use `win32com` and run `CalculateFullRebuild()`.
2. If COM is unavailable, use `soffice --headless` or any repo-local recalculation workflow available in the current project.
3. Reopen the workbook and inspect formulas and cached values.

Verification checklist:

- required sheets exist
- formula cells are still formulas
- cached values exist where recalculation was expected
- no Excel error tokens remain
- layout still matches the user's expectations

## Formatting Requirements

### Existing Templates

- Match the existing font, fills, borders, number formats, alignment, merge rules, and spacing.
- Do not impose a new style on a workbook with an established template.

### New Workbooks

- Unless the user specifies otherwise, use a readable professional font such as `Malgun Gothic` in this workspace.
- Make headers visually distinct from body cells.
- Apply explicit date, currency, and percentage formats.
- Set row heights and column widths so text does not spill unnecessarily.

### Finance Defaults

Apply only when the user has no stronger formatting rules and the workbook is a finance-style model.

- blue text: user inputs
- black text: formulas
- green text: internal workbook links
- red text: external links
- yellow fill: key assumptions or update-required cells
- zero values as `-`
- negative values in parentheses
- percentages as `0.0%`
- multiples as `0.0x`
- units included in headers

## Source Notes

- Add cell comments or adjacent notes for hardcoded inputs when provenance matters.
- Source notes should prefer document name, date, exact reference point, and URL.
- Add short notes for complex formulas or key assumptions when future editing is likely.

## Practical Guardrails

- Decide early whether edits should happen on a copy rather than the original file.
- Do not end a formula-sensitive task by replacing logic with Python-calculated constants.
- When converting CSV to XLSX, keep the verification and formatting steps if the output is meant for delivery.
- If layout matters, render to PDF or image for a final visual check.

## Minimal Examples

Read with `pandas`:

```python
import pandas as pd

df = pd.read_excel("input.xlsx")
```

Edit with `openpyxl`:

```python
from openpyxl import load_workbook

wb = load_workbook("input.xlsx")
ws = wb["Sheet1"]
ws["D2"] = "=B2*C2"
wb.save("output.xlsx")
```

## Priority

System instructions, user instructions, and existing template conventions override this skill.
