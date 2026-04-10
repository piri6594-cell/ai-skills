import json
import shutil
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"


def u(text: str) -> str:
    return text.encode("ascii").decode("unicode_escape")


PH_NAME = u(r"\uc131\uba85")
PH_NAME_BRACKET = f"[{PH_NAME}]"
VALUE_NAME = u(r"\uae40\ud14c\uc2a4\ud2b8")
VALUE_OLD = u(r"\ud64d\uae38\ub3d9")
LABEL_SCHEDULE = u(r"\uc0ac\uc5c5 \ucd94\uc9c4\uc77c\uc815")
KEY_SCHEDULE = u(r"\ucd94\uc9c4\uc77c\uc815")
VALUE_SCHEDULE = u(r"2026\ub144 \uc77c\uc815")
LABEL_ATTACH = u(r"\ubd99\uc784")
VALUE_ATTACH = u(r"\ucca8\ubd80\uc790\ub8cc")


def build_minimal_hwpx(path: Path) -> None:
    section = f"""<?xml version="1.0" encoding="UTF-8"?>
<hp:section xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph">
  <hp:p>
    <hp:run><hp:t>{PH_NAME_BRACKET}</hp:t></hp:run>
  </hp:p>
  <hp:tbl>
    <hp:tr>
      <hp:tc><hp:p><hp:run><hp:t>{PH_NAME}</hp:t></hp:run></hp:p></hp:tc>
      <hp:tc><hp:p><hp:run><hp:t>{VALUE_OLD}</hp:t></hp:run></hp:p></hp:tc>
    </hp:tr>
  </hp:tbl>
</hp:section>
"""
    header = """<?xml version="1.0" encoding="UTF-8"?>
<hh:header xmlns:hh="http://www.hancom.co.kr/hwpml/2011/head"/>
"""
    content_hpf = """<?xml version="1.0" encoding="UTF-8"?>
<opf:package xmlns:opf="http://www.idpf.org/2007/opf" version="3.0">
  <opf:spine>
    <opf:itemref idref="section0"/>
  </opf:spine>
</opf:package>
"""
    manifest = """<?xml version="1.0" encoding="UTF-8"?>
<manifest xmlns="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0">
  <file-entry full-path="/" media-type="application/hwp+zip"/>
</manifest>
"""
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("mimetype", "application/hwp+zip")
        zf.writestr("META-INF/manifest.xml", manifest)
        zf.writestr("Contents/content.hpf", content_hpf)
        zf.writestr("Contents/header.xml", header)
        zf.writestr("Contents/section0.xml", section)
        zf.writestr("Preview/PrvText.txt", f"{PH_NAME_BRACKET}\n{PH_NAME} {VALUE_OLD}\n")


class HwpxWorkflowTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = Path(tempfile.mkdtemp(prefix="hwpx_test_"))
        self.template = self.tempdir / "template.hwpx"
        build_minimal_hwpx(self.template)

    def tearDown(self) -> None:
        shutil.rmtree(self.tempdir, ignore_errors=True)

    def run_script(self, script_name: str, *args: str) -> subprocess.CompletedProcess[str]:
        script = SCRIPTS / script_name
        return subprocess.run(
            ["python", str(script), *map(str, args)],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )

    def test_extract_template_outputs_placeholder_and_label_candidates(self) -> None:
        out_json = self.tempdir / "extract.json"
        result = self.run_script("extract_template.py", self.template, out_json)
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        data = json.loads(out_json.read_text(encoding="utf-8"))
        self.assertIn(PH_NAME_BRACKET, data["placeholders"])
        self.assertTrue(any(item["label"] == PH_NAME for item in data["label_candidates"]))

    def test_structured_fill_replaces_cell_to_the_right_of_label(self) -> None:
        config = self.tempdir / "fill.json"
        out_hwpx = self.tempdir / "filled.hwpx"
        config.write_text(
            json.dumps({"label_fills": [{"label": PH_NAME, "direction": "right", "value": VALUE_NAME}]}, ensure_ascii=False),
            encoding="utf-8",
        )
        result = self.run_script("structured_fill_hwpx.py", self.template, config, out_hwpx)
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        with zipfile.ZipFile(out_hwpx) as zf:
            section = zf.read("Contents/section0.xml").decode("utf-8")
        self.assertIn(VALUE_NAME, section)

    def test_structured_fill_can_populate_empty_target_cell(self) -> None:
        template = self.tempdir / "empty_cell.hwpx"
        section = f"""<?xml version="1.0" encoding="UTF-8"?>
<hp:section xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph">
  <hp:tbl>
    <hp:tr>
      <hp:tc><hp:p><hp:run><hp:t>{LABEL_ATTACH}</hp:t></hp:run></hp:p></hp:tc>
      <hp:tc><hp:p><hp:run /></hp:p></hp:tc>
    </hp:tr>
  </hp:tbl>
</hp:section>
"""
        with zipfile.ZipFile(template, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("mimetype", "application/hwp+zip")
            zf.writestr("META-INF/manifest.xml", """<?xml version="1.0" encoding="UTF-8"?><manifest xmlns="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0"><file-entry full-path="/" media-type="application/hwp+zip"/></manifest>""")
            zf.writestr("Contents/content.hpf", """<?xml version="1.0" encoding="UTF-8"?><opf:package xmlns:opf="http://www.idpf.org/2007/opf" version="3.0"><opf:spine><opf:itemref idref="section0"/></opf:spine></opf:package>""")
            zf.writestr("Contents/header.xml", """<?xml version="1.0" encoding="UTF-8"?><hh:header xmlns:hh="http://www.hancom.co.kr/hwpml/2011/head"/>""")
            zf.writestr("Contents/section0.xml", section)
            zf.writestr("Preview/PrvText.txt", f"{LABEL_ATTACH}\n")

        config = self.tempdir / "fill_empty.json"
        out_hwpx = self.tempdir / "filled_empty.hwpx"
        config.write_text(
            json.dumps({"label_fills": [{"label": LABEL_ATTACH, "direction": "right", "value": VALUE_ATTACH}]}, ensure_ascii=False),
            encoding="utf-8",
        )
        result = self.run_script("structured_fill_hwpx.py", template, config, out_hwpx)
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        with zipfile.ZipFile(out_hwpx) as zf:
            section_xml = zf.read("Contents/section0.xml").decode("utf-8")
        self.assertIn(VALUE_ATTACH, section_xml)

    def test_validate_hwpx_checks_expected_text(self) -> None:
        out_hwpx = self.tempdir / "filled.hwpx"
        shutil.copy(self.template, out_hwpx)
        expect_json = self.tempdir / "expect.json"
        expect_json.write_text(
            json.dumps({"expected_text": [PH_NAME_BRACKET, VALUE_OLD]}, ensure_ascii=False),
            encoding="utf-8",
        )
        result = self.run_script("validate_hwpx.py", out_hwpx, "--expect-json", expect_json)
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertIn("PASS", result.stdout)

    def test_extract_template_merges_kordoc_table_candidates(self) -> None:
        out_json = self.tempdir / "extract.json"
        kordoc_json = self.tempdir / "kordoc.json"
        kordoc_json.write_text(
            json.dumps(
                {
                    "success": True,
                    "blocks": [
                        {
                            "type": "table",
                            "pageNumber": 1,
                            "table": {
                                "rows": 1,
                                "cols": 2,
                                "cells": [[
                                    {"text": "Name", "colSpan": 1, "rowSpan": 1},
                                    {"text": "Alice", "colSpan": 1, "rowSpan": 1},
                                ]],
                            },
                        }
                    ],
                    "markdown": "Name Alice",
                }
            ),
            encoding="utf-8",
        )
        result = self.run_script("extract_template.py", self.template, out_json, "--kordoc-json", kordoc_json)
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        data = json.loads(out_json.read_text(encoding="utf-8"))
        self.assertEqual(data["analysis_engine"], "kordoc+xml")
        self.assertTrue(any(item["label"] == "Name" for item in data["label_candidates"]))

    def test_build_fill_config_maps_values_from_extract_report(self) -> None:
        extract_json = self.tempdir / "extract.json"
        values_json = self.tempdir / "values.json"
        output_json = self.tempdir / "fill.json"
        extract_json.write_text(
            json.dumps(
                {
                    "placeholders": [PH_NAME_BRACKET],
                    "label_candidates": [{"label": PH_NAME, "direction": "right", "current_value": VALUE_OLD}],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        values_json.write_text(json.dumps({PH_NAME: VALUE_NAME}, ensure_ascii=False), encoding="utf-8")
        result = self.run_script("build_fill_config.py", extract_json, values_json, output_json)
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        config = json.loads(output_json.read_text(encoding="utf-8"))
        self.assertEqual(config["text_replacements"][PH_NAME_BRACKET], VALUE_NAME)
        self.assertEqual(config["label_fills"][0]["label"], PH_NAME)
        self.assertEqual(config["label_fills"][0]["value"], VALUE_NAME)

    def test_build_fill_config_supports_contains_matching(self) -> None:
        extract_json = self.tempdir / "extract.json"
        values_json = self.tempdir / "values.json"
        output_json = self.tempdir / "fill.json"
        extract_json.write_text(
            json.dumps(
                {"placeholders": [], "label_candidates": [{"label": LABEL_SCHEDULE, "direction": "right", "current_value": ""}]},
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        values_json.write_text(json.dumps({KEY_SCHEDULE: VALUE_SCHEDULE}, ensure_ascii=False), encoding="utf-8")
        result = self.run_script("build_fill_config.py", extract_json, values_json, output_json)
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        config = json.loads(output_json.read_text(encoding="utf-8"))
        self.assertEqual(config["label_fills"][0]["label"], LABEL_SCHEDULE)
        self.assertEqual(config["label_fills"][0]["value"], VALUE_SCHEDULE)

    def test_suggest_fill_mapping_generates_ranked_candidates(self) -> None:
        extract_json = self.tempdir / "extract.json"
        values_json = self.tempdir / "values.json"
        output_json = self.tempdir / "mapping.json"
        fill_json = self.tempdir / "suggested_fill.json"
        extract_json.write_text(
            json.dumps(
                {
                    "placeholders": [],
                    "label_candidates": [
                        {"label": LABEL_ATTACH, "direction": "right", "current_value": ""},
                        {"label": LABEL_SCHEDULE, "direction": "right", "current_value": ""},
                        {"label": u(r"\uac1c\uc694"), "direction": "right", "current_value": ""},
                    ],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        values_json.write_text(
            json.dumps({KEY_SCHEDULE: VALUE_SCHEDULE, LABEL_ATTACH: VALUE_ATTACH}, ensure_ascii=False),
            encoding="utf-8",
        )
        result = self.run_script(
            "suggest_fill_mapping.py",
            extract_json,
            values_json,
            output_json,
            "--fill-config-output",
            fill_json,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        mapping = json.loads(output_json.read_text(encoding="utf-8"))
        self.assertTrue(any(item["key"] == LABEL_ATTACH and item["status"] == "matched" for item in mapping["suggestions"]))
        schedule = next(item for item in mapping["suggestions"] if item["key"] == KEY_SCHEDULE)
        self.assertEqual(schedule["status"], "review")
        self.assertEqual(schedule["candidates"][0]["label"], LABEL_SCHEDULE)
        fill_config = json.loads(fill_json.read_text(encoding="utf-8"))
        self.assertEqual(fill_config["label_fills"][0]["label"], LABEL_ATTACH)
        self.assertEqual(fill_config["label_fills"][0]["value"], VALUE_ATTACH)


if __name__ == "__main__":
    unittest.main()
