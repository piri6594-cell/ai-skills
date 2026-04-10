# HWPX Template Notes

## Package Anatomy

Typical HWPX packages in this skill use these paths:

- `mimetype`: package marker
- `META-INF/manifest.xml`: file manifest
- `Contents/content.hpf`: reading order and metadata
- `Contents/header.xml`: shared styles
- `Contents/section*.xml`: body text and tables
- `Preview/PrvText.txt`: quick text preview
- `Preview/PrvImage.png`: preview image
- `BinData/`: embedded images and other binary assets when present

Inspect these files before editing so you know whether the template is a simple text-only form or a form with images and additional controls.

## Bundled Samples

### `sample-report-template-1.hwpx`

Use this as the reference for a long-form formal report.

Observed traits:

- multi-page report structure
- cover/title area with department and contact information
- table of contents
- numbered chapter flow with Roman numeral style headings
- nested bullet rhythm with multiple indentation levels
- embedded `BinData/image1.png`

Choose this sample when the user asks for a detailed proposal, report, request-for-proposal style document, or anything that needs multiple sections and a formal chapter hierarchy.

### `sample-report-template-2-summary.hwpx`

Use this as the reference for a one-page summary report.

Observed traits:

- title line and department/date line near the top
- compact blocks for summary, plan, execution, budget, and cooperation notes
- short attachment section for supporting material

Choose this sample when the user asks for a summary memo, one-page briefing, executive note, or condensed project overview.

## Practical Editing Cues

- Replace placeholder organization names such as `OOO`, placeholder departments, or dummy dates with real values while keeping the same line structure.
- Preserve the heading text if it acts as a label and only replace the explanatory lines below it.
- If the preview text and section XML differ slightly, trust the section XML for exact editing locations and use the preview as a navigation aid.
- If a user provides new sample forms, compare them against these assets before deciding where to inject content.
