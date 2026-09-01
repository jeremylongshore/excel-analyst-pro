from __future__ import annotations

import csv
import io
import json
import shutil
import sys
import tempfile
import unittest
import zipfile
from contextlib import redirect_stderr
from pathlib import Path
from unittest.mock import patch

SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = SKILL_DIR / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import profile_reconcile
import verify_artifact
import workbook_inventory

CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
  <Override PartName="/xl/worksheets/sheet2.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
</Types>
"""

ROOT_RELS = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>
"""


def create_workbook(
    path: Path,
    *,
    formula: bool = True,
    manual: bool = True,
    hidden: bool = True,
    risky_features: bool = True,
    merged_cells: bool = False,
    external_target: str = "https://example.invalid/source.xlsx",
) -> None:
    hidden_state = ' state="veryHidden"' if hidden else ""
    calc_mode = "manual" if manual else "auto"
    workbook = f"""<?xml version="1.0" encoding="UTF-8"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets>
    <sheet name="Model" sheetId="1" r:id="rId1"/>
    <sheet name="HiddenInputs" sheetId="2" r:id="rId2"{hidden_state}/>
  </sheets>
  <calcPr calcMode="{calc_mode}" calcId="191029" fullCalcOnLoad="0" forceFullCalc="0"/>
</workbook>
"""
    external_rel = (
        '\n  <Relationship Id="rId3" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/externalLink" '
        f'Target="{external_target}" TargetMode="External"/>'
        if risky_features
        else ""
    )
    workbook_rels = f"""<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet2.xml"/>{external_rel}
</Relationships>
"""
    formula_cell = (
        '<c r="C2"><f>SUM(A2:B2)</f><v>999</v></c>'
        if formula
        else '<c r="C2" t="n"><v>3</v></c>'
    )
    merge_xml = (
        '<mergeCells count="1"><mergeCell ref="A2:B2"/></mergeCells>'
        if merged_cells
        else ""
    )
    sheet1 = f"""<?xml version="1.0" encoding="UTF-8"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <sheetData><row r="2"><c r="A2"><v>1</v></c><c r="B2"><v>2</v></c>{formula_cell}</row></sheetData>
  {merge_xml}
</worksheet>
"""
    sheet2 = """<?xml version="1.0" encoding="UTF-8"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <sheetData><row r="1"><c r="A1" t="inlineStr"><is><t>secret</t></is></c></row></sheetData>
</worksheet>
"""
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", CONTENT_TYPES)
        archive.writestr("_rels/.rels", ROOT_RELS)
        archive.writestr("xl/workbook.xml", workbook)
        archive.writestr("xl/_rels/workbook.xml.rels", workbook_rels)
        archive.writestr("xl/worksheets/sheet1.xml", sheet1)
        archive.writestr("xl/worksheets/sheet2.xml", sheet2)
        if risky_features:
            archive.writestr("xl/vbaProject.bin", b"test-vba")
            archive.writestr(
                "xl/pivotTables/pivotTable1.xml", b"<pivotTableDefinition/>"
            )
            archive.writestr(
                "xl/pivotCache/pivotCacheDefinition1.xml", b"<pivotCacheDefinition/>"
            )
            archive.writestr("xl/embeddings/oleObject1.bin", b"embedded")
            archive.writestr("xl/externalLinks/externalLink1.xml", b"<externalLink/>")
            archive.writestr("xl/connections.xml", b"<connections/>")
            archive.writestr("xl/queryTables/queryTable1.xml", b"<queryTable/>")
            archive.writestr("xl/activeX/activeX1.bin", b"activex")
            archive.writestr("customXml/item1.xml", b"<custom/>")


def write_csv(path: Path, header: list[str], rows: list[list[str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(rows)


def write_contract(
    path: Path,
    *,
    lookup_name: str | None = None,
) -> None:
    contract: dict[str, object] = {
        "schema_version": profile_reconcile.SPEC_SCHEMA_VERSION,
        "encoding": "utf-8",
        "delimiter": ",",
        "has_header": True,
        "grain": "one row per transaction",
        "keys": ["id"],
        "types": {
            "id": "integer",
            "customer_id": "text",
            "amount": "decimal",
            "note": "text",
        },
        "required_columns": ["id", "customer_id", "amount", "note"],
        "units": {"amount": "USD"},
        "signs": {"amount": "positive_is_revenue"},
        "controls": [{"name": "amount_total", "column": "amount"}],
    }
    if lookup_name is not None:
        contract["lookup"] = {
            "path": lookup_name,
            "encoding": "utf-8",
            "delimiter": ",",
            "keys": ["customer_id"],
            "foreign_keys": ["customer_id"],
        }
    path.write_text(json.dumps(contract), encoding="utf-8")


def build_receipt(
    artifact_inventory: dict[str, object],
    baseline_inventory: dict[str, object] | None,
    *,
    prove_recalculation: bool = True,
) -> dict[str, object]:
    artifact_input = artifact_inventory["input"]
    artifact_package = artifact_inventory["package"]
    artifact_workbook = artifact_inventory["workbook"]
    receipt: dict[str, object] = {
        "schema_version": verify_artifact.RECEIPT_SCHEMA_VERSION,
        "artifact": {
            "sha256": artifact_input["sha256"],
            "inventory_sha256": artifact_inventory["inventory_sha256"],
            "package_fingerprint_sha256": artifact_package["fingerprint_sha256"],
        },
        "baseline": None,
        "recalculation": {
            "required": False,
            "reason": "artifact_contains_no_formulas",
        },
    }
    if baseline_inventory is not None:
        baseline_input = baseline_inventory["input"]
        baseline_package = baseline_inventory["package"]
        receipt["baseline"] = {
            "sha256": baseline_input["sha256"],
            "inventory_sha256": baseline_inventory["inventory_sha256"],
            "package_fingerprint_sha256": baseline_package["fingerprint_sha256"],
            "protected_features": verify_artifact._feature_snapshot(baseline_inventory),
        }
    if artifact_workbook["formula_count"] and prove_recalculation:
        evidence = verify_artifact.seal_calculation_evidence(
            {
                "schema_version": verify_artifact.CALCULATION_EVIDENCE_SCHEMA_VERSION,
                "artifact_sha256": artifact_input["sha256"],
                "inventory_sha256": artifact_inventory["inventory_sha256"],
                "engine": "microsoft_excel",
                "engine_version": "16.0-test",
                "completed": True,
                "full_calculation": True,
                "formula_count": artifact_workbook["formula_count"],
                "error_cells": [],
            }
        )
        receipt["recalculation"] = {"required": True, "evidence": evidence}
    return verify_artifact.seal_receipt(receipt)


class AssuranceScriptsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_directory.name)

    def tearDown(self) -> None:
        self.temp_directory.cleanup()

    def test_inventory_detects_manual_stale_and_risky_features(self) -> None:
        workbook = self.root / "manual.xlsm"
        create_workbook(workbook)

        inventory = workbook_inventory.inspect_workbook(workbook)

        self.assertEqual(inventory["workbook"]["calculation"]["mode"], "manual")
        self.assertEqual(inventory["workbook"]["formula_count"], 1)
        self.assertEqual(
            inventory["workbook"]["hidden_sheets"],
            [{"name": "HiddenInputs", "state": "veryHidden"}],
        )
        self.assertTrue(inventory["risk"]["recalculation_required"])
        for category in (
            "macros",
            "pivots",
            "embedded",
            "external_links",
            "connections",
            "queries",
            "activex",
            "custom_xml",
        ):
            self.assertTrue(inventory["features"][category]["present"], category)

    def test_profile_scans_defects_after_row_1000(self) -> None:
        source = self.root / "source.csv"
        contract = self.root / "contract.json"
        rows = [[str(index), f"C{index}", "1.25", "safe"] for index in range(1, 1003)]
        rows[1000][2] = "not-a-decimal"
        rows[1001][3] = '=HYPERLINK("https://example.invalid")'
        write_csv(source, ["id", "customer_id", "amount", "note"], rows)
        write_contract(contract)

        report = profile_reconcile.profile_csv(source, contract)

        self.assertEqual(report["source"]["row_count"], 1002)
        late_exceptions = [
            row
            for row in report["exceptions"]
            if row["code"] in {"TYPE_MISMATCH", "FORMULA_INJECTION_RISK"}
        ]
        self.assertEqual([row["row"] for row in late_exceptions], [1002, 1003])
        self.assertFalse(report["controls"][0]["complete"])
        self.assertEqual(report["status"], "BLOCKED")

    def test_formula_injection_prefixes_are_never_silently_accepted(self) -> None:
        source = self.root / "injection.csv"
        contract = self.root / "contract.json"
        dangerous = [
            "=1+1",
            "+1",
            "-1",
            "@SUM(A1:A2)",
            "\t=1",
            "\r=1",
            "\n=1",
            "＝1",
            "＋1",
            "－1",
            "＠A1",
        ]
        rows = [
            [str(index), f"C{index}", "1", value]
            for index, value in enumerate(dangerous, start=1)
        ]
        rows[0][2] = "-1.25"
        write_csv(source, ["id", "customer_id", "amount", "note"], rows)
        write_contract(contract)

        report = profile_reconcile.profile_csv(source, contract)

        injection_findings = [
            row
            for row in report["exceptions"]
            if row["code"] == "FORMULA_INJECTION_RISK"
        ]
        self.assertEqual(len(injection_findings), len(dangerous))
        self.assertEqual(
            report["profile"]["note"]["formula_injection_count"], len(dangerous)
        )
        self.assertEqual(report["profile"]["amount"]["formula_injection_count"], 0)

    def test_duplicate_lookup_keys_and_unmatched_foreign_keys_block(self) -> None:
        source = self.root / "source.csv"
        lookup = self.root / "customers.csv"
        contract = self.root / "contract.json"
        write_csv(
            source,
            ["id", "customer_id", "amount", "note"],
            [["1", "C1", "10", "safe"], ["2", "C9", "20", "safe"]],
        )
        write_csv(
            lookup,
            ["customer_id", "name"],
            [["C1", "One"], ["C1", "Duplicate"]],
        )
        write_contract(contract, lookup_name=lookup.name)

        report = profile_reconcile.profile_csv(source, contract)
        codes = {row["code"] for row in report["exceptions"]}

        self.assertIn("DUPLICATE_LOOKUP_KEY", codes)
        self.assertIn("UNMATCHED_FOREIGN_KEY", codes)
        self.assertEqual(report["status"], "BLOCKED")

    def test_empty_control_value_is_not_silently_zero(self) -> None:
        source = self.root / "source.csv"
        contract = self.root / "contract.json"
        write_csv(
            source,
            ["id", "customer_id", "amount", "note"],
            [["1", "C1", "", "safe"]],
        )
        write_contract(contract)

        report = profile_reconcile.profile_csv(source, contract)

        self.assertIn(
            "MISSING_REQUIRED_VALUE",
            {row["code"] for row in report["exceptions"]},
        )
        self.assertEqual(report["controls"][0]["partial_total"], "0")
        self.assertFalse(report["controls"][0]["complete"])

    def test_profile_row_budget_fails_closed(self) -> None:
        source = self.root / "source.csv"
        contract = self.root / "contract.json"
        write_csv(
            source,
            ["id", "customer_id", "amount", "note"],
            [["1", "C1", "10", "safe"], ["2", "C2", "20", "safe"]],
        )
        write_contract(contract)

        with patch.object(profile_reconcile, "MAX_ROWS", 1), self.assertRaisesRegex(
            profile_reconcile.ProfileError, "Source exceeds 1 rows"
        ):
            profile_reconcile.profile_csv(source, contract)

    def test_lookup_path_cannot_escape_contract_directory(self) -> None:
        contract = self.root / "contract.json"
        write_contract(contract, lookup_name="../outside.csv")

        with self.assertRaisesRegex(profile_reconcile.ProfileError, "may not escape"):
            profile_reconcile._load_spec(contract)

    def test_source_exception_budget_applies_before_continue(self) -> None:
        source = self.root / "source.csv"
        contract = self.root / "contract.json"
        write_csv(
            source,
            ["id", "customer_id", "amount", "note"],
            [["1"], ["2"], ["3"]],
        )
        write_contract(contract)

        with patch.object(
            profile_reconcile, "MAX_EXCEPTIONS", 1
        ), self.assertRaisesRegex(
            profile_reconcile.ProfileError, "Source exceeds 1 retained exceptions"
        ):
            profile_reconcile.profile_csv(source, contract)

    def test_lookup_exception_budget_applies_before_continue(self) -> None:
        source = self.root / "source.csv"
        lookup = self.root / "lookup.csv"
        contract = self.root / "contract.json"
        write_csv(
            source,
            ["id", "customer_id", "amount", "note"],
            [["1", "C1", "10", "safe"]],
        )
        write_csv(lookup, ["customer_id"], [[], [], []])
        write_contract(contract, lookup_name=lookup.name)

        with patch.object(
            profile_reconcile, "MAX_EXCEPTIONS", 1
        ), self.assertRaisesRegex(
            profile_reconcile.ProfileError, "Lookup exceeds 1 retained exceptions"
        ):
            profile_reconcile.profile_csv(source, contract)

    def test_verify_accepts_bound_artifact_and_preserved_features(self) -> None:
        baseline = self.root / "baseline.xlsm"
        artifact = self.root / "artifact.xlsm"
        receipt_path = self.root / "receipt.json"
        create_workbook(baseline)
        shutil.copyfile(baseline, artifact)
        baseline_inventory = workbook_inventory.inspect_workbook(baseline)
        artifact_inventory = workbook_inventory.inspect_workbook(artifact)
        receipt = build_receipt(artifact_inventory, baseline_inventory)
        receipt_path.write_text(json.dumps(receipt), encoding="utf-8")

        report = verify_artifact.verify_artifact(artifact, receipt_path, baseline)

        self.assertEqual(report["status"], "EVIDENCE_CONSISTENT")
        self.assertEqual(report["failure_count"], 0)

    def test_verify_blocks_worksheet_control_loss(self) -> None:
        baseline = self.root / "baseline.xlsx"
        artifact = self.root / "artifact.xlsx"
        receipt_path = self.root / "receipt.json"
        create_workbook(baseline, risky_features=False, merged_cells=True)
        create_workbook(artifact, risky_features=False, merged_cells=False)
        baseline_inventory = workbook_inventory.inspect_workbook(baseline)
        artifact_inventory = workbook_inventory.inspect_workbook(artifact)
        receipt = build_receipt(artifact_inventory, baseline_inventory)
        receipt_path.write_text(json.dumps(receipt), encoding="utf-8")

        report = verify_artifact.verify_artifact(artifact, receipt_path, baseline)

        self.assertEqual(report["status"], "BLOCKED")
        self.assertIn(
            "PROTECTED_FEATURE_CHANGED",
            {row["code"] for row in report["failures"]},
        )

    def test_verify_blocks_feature_loss_even_with_resealed_artifact_receipt(
        self,
    ) -> None:
        baseline = self.root / "baseline.xlsm"
        artifact = self.root / "artifact.xlsx"
        receipt_path = self.root / "receipt.json"
        create_workbook(baseline)
        create_workbook(artifact, risky_features=False)
        baseline_inventory = workbook_inventory.inspect_workbook(baseline)
        artifact_inventory = workbook_inventory.inspect_workbook(artifact)
        receipt = build_receipt(artifact_inventory, baseline_inventory)
        receipt_path.write_text(json.dumps(receipt), encoding="utf-8")

        report = verify_artifact.verify_artifact(artifact, receipt_path, baseline)
        codes = {row["code"] for row in report["failures"]}

        self.assertEqual(report["status"], "BLOCKED")
        self.assertIn("PROTECTED_FEATURE_CHANGED", codes)

    def test_verify_blocks_external_relationship_change(self) -> None:
        baseline = self.root / "baseline.xlsm"
        artifact = self.root / "artifact.xlsm"
        receipt_path = self.root / "receipt.json"
        create_workbook(baseline)
        create_workbook(
            artifact, external_target="https://attacker.invalid/replacement.xlsx"
        )
        baseline_inventory = workbook_inventory.inspect_workbook(baseline)
        artifact_inventory = workbook_inventory.inspect_workbook(artifact)
        receipt = build_receipt(artifact_inventory, baseline_inventory)
        receipt_path.write_text(json.dumps(receipt), encoding="utf-8")

        report = verify_artifact.verify_artifact(artifact, receipt_path, baseline)

        self.assertEqual(report["status"], "BLOCKED")
        self.assertIn(
            "PROTECTED_FEATURE_CHANGED",
            {row["code"] for row in report["failures"]},
        )

    def test_verify_blocks_unproven_recalculation(self) -> None:
        artifact = self.root / "artifact.xlsx"
        receipt_path = self.root / "receipt.json"
        create_workbook(artifact, risky_features=False)
        inventory = workbook_inventory.inspect_workbook(artifact)
        receipt = build_receipt(inventory, None, prove_recalculation=False)
        receipt_path.write_text(json.dumps(receipt), encoding="utf-8")

        report = verify_artifact.verify_artifact(artifact, receipt_path)

        self.assertEqual(report["status"], "BLOCKED")
        self.assertIn(
            "RECALCULATION_EVIDENCE_REQUIRED",
            {row["code"] for row in report["failures"]},
        )

    def test_verify_blocks_tampered_receipt(self) -> None:
        artifact = self.root / "artifact.xlsx"
        receipt_path = self.root / "receipt.json"
        create_workbook(artifact, risky_features=False)
        inventory = workbook_inventory.inspect_workbook(artifact)
        receipt = build_receipt(inventory, None)
        receipt["artifact"]["sha256"] = "0" * 64
        receipt_path.write_text(json.dumps(receipt), encoding="utf-8")

        report = verify_artifact.verify_artifact(artifact, receipt_path)
        codes = {row["code"] for row in report["failures"]}

        self.assertEqual(report["status"], "BLOCKED")
        self.assertIn("RECEIPT_HASH_MISMATCH", codes)
        self.assertIn("ARTIFACT_SHA256_MISMATCH", codes)

    def test_cli_outputs_are_json_and_atomic(self) -> None:
        workbook = self.root / "workbook.xlsx"
        inventory_output = self.root / "inventory.json"
        create_workbook(workbook, risky_features=False)

        exit_code = workbook_inventory.main(
            [str(workbook), "--output", str(inventory_output)]
        )

        self.assertEqual(exit_code, 0)
        self.assertEqual(
            json.loads(inventory_output.read_text())["status"], "INVENTORIED"
        )

        source = self.root / "source.csv"
        contract = self.root / "contract.json"
        profile_output = self.root / "profile.json"
        write_csv(
            source,
            ["id", "customer_id", "amount", "note"],
            [["1", "C1", "10", "safe"]],
        )
        write_contract(contract)
        exit_code = profile_reconcile.main(
            [str(source), "--spec", str(contract), "--output", str(profile_output)]
        )
        self.assertEqual(exit_code, 0)
        self.assertEqual(json.loads(profile_output.read_text())["status"], "RECONCILED")

        inventory = workbook_inventory.inspect_workbook(workbook)
        receipt_path = self.root / "receipt.json"
        verify_output = self.root / "verified.json"
        receipt_path.write_text(
            json.dumps(build_receipt(inventory, None)), encoding="utf-8"
        )
        exit_code = verify_artifact.main(
            [
                str(workbook),
                "--receipt",
                str(receipt_path),
                "--output",
                str(verify_output),
            ]
        )
        self.assertEqual(exit_code, 0)
        self.assertEqual(
            json.loads(verify_output.read_text())["status"], "EVIDENCE_CONSISTENT"
        )

        self.assertEqual(list(self.root.glob(".inventory.json.*.tmp")), [])
        self.assertEqual(list(self.root.glob(".profile.json.*.tmp")), [])
        self.assertEqual(list(self.root.glob(".verified.json.*.tmp")), [])

    def test_cli_argument_errors_are_json(self) -> None:
        for entrypoint in (
            workbook_inventory.main,
            profile_reconcile.main,
            verify_artifact.main,
        ):
            with self.subTest(entrypoint=entrypoint.__module__):
                stderr = io.StringIO()
                with redirect_stderr(stderr), self.assertRaises(SystemExit) as raised:
                    entrypoint([])
                self.assertEqual(raised.exception.code, 2)
                payload = json.loads(stderr.getvalue())
                self.assertEqual(payload["error"]["code"], "INVALID_ARGUMENTS")


if __name__ == "__main__":
    unittest.main()
