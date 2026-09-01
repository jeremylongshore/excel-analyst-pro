#!/usr/bin/env python3
"""Verify an Excel artifact, its baseline features, and bound calculation evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

from workbook_inventory import InventoryError, canonical_sha256, inspect_workbook

SCHEMA_VERSION = "excel-artifact-verification/v1"
RECEIPT_SCHEMA_VERSION = "excel-artifact-receipt/v1"
CALCULATION_EVIDENCE_SCHEMA_VERSION = "excel-calculation-evidence/v1"
SUPPORTED_CALCULATION_ENGINES = {"libreoffice_calc", "microsoft_excel"}
PRESERVATION_CATEGORIES = (
    "macros",
    "pivots",
    "embedded",
    "external_links",
    "connections",
    "queries",
    "data_model",
    "activex",
    "custom_xml",
    "digital_signatures",
    "web_extensions",
    "drawings",
    "charts",
    "media",
    "slicers",
    "controls",
    "comments",
    "printer_settings",
    "worksheet_controls",
    "workbook_controls",
)


class VerificationError(Exception):
    """A malformed verification input that cannot be evaluated safely."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


class JsonArgumentParser(argparse.ArgumentParser):
    """Emit machine-readable argument errors."""

    def error(self, message: str) -> None:
        json.dump(
            {
                "schema_version": SCHEMA_VERSION,
                "status": "ERROR",
                "error": {"code": "INVALID_ARGUMENTS", "message": message},
            },
            sys.stderr,
            sort_keys=True,
            separators=(",", ":"),
        )
        sys.stderr.write("\n")
        self.exit(2)


def _atomic_json_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(
                payload,
                handle,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, path)
    except BaseException:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise


def _emit(payload: dict[str, Any], output: Path | None) -> None:
    if output is None:
        json.dump(
            payload,
            sys.stdout,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        sys.stdout.write("\n")
    else:
        _atomic_json_write(output, payload)


def _load_json(path: Path, label: str) -> dict[str, Any]:
    if not path.is_file():
        raise VerificationError(
            f"{label.upper()}_NOT_FILE", f"{label} is not a file: {path}"
        )
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise VerificationError(f"INVALID_{label.upper()}_JSON", str(exc)) from exc
    if not isinstance(value, dict):
        raise VerificationError(
            f"INVALID_{label.upper()}_JSON", f"{label} must be a JSON object"
        )
    return value


def _feature_snapshot(inventory: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    return {
        category: inventory["features"][category]["parts"]
        for category in PRESERVATION_CATEGORIES
    }


def _validate_sha(value: Any, location: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise VerificationError(
            "INVALID_RECEIPT", f"{location} must be lowercase SHA-256"
        )
    return value


def _validate_receipt_shape(receipt: dict[str, Any]) -> None:
    allowed = {
        "schema_version",
        "artifact",
        "baseline",
        "recalculation",
        "receipt_sha256",
    }
    if set(receipt) != allowed:
        raise VerificationError(
            "INVALID_RECEIPT", f"Receipt fields must be exactly {sorted(allowed)}"
        )
    if receipt.get("schema_version") != RECEIPT_SCHEMA_VERSION:
        raise VerificationError(
            "INVALID_RECEIPT",
            f"Receipt schema_version must be {RECEIPT_SCHEMA_VERSION}",
        )
    artifact = receipt.get("artifact")
    if not isinstance(artifact, dict) or set(artifact) != {
        "sha256",
        "inventory_sha256",
        "package_fingerprint_sha256",
    }:
        raise VerificationError("INVALID_RECEIPT", "Invalid artifact receipt fields")
    for name, value in artifact.items():
        _validate_sha(value, f"artifact.{name}")

    baseline = receipt.get("baseline")
    if baseline is not None:
        if not isinstance(baseline, dict) or set(baseline) != {
            "sha256",
            "inventory_sha256",
            "package_fingerprint_sha256",
            "protected_features",
        }:
            raise VerificationError(
                "INVALID_RECEIPT", "Invalid baseline receipt fields"
            )
        for name in ("sha256", "inventory_sha256", "package_fingerprint_sha256"):
            _validate_sha(baseline[name], f"baseline.{name}")
        protected = baseline["protected_features"]
        if not isinstance(protected, dict) or set(protected) != set(
            PRESERVATION_CATEGORIES
        ):
            raise VerificationError(
                "INVALID_RECEIPT", "Baseline protected_features are incomplete"
            )
        for category, parts in protected.items():
            if not isinstance(parts, list):
                raise VerificationError(
                    "INVALID_RECEIPT", f"protected_features.{category} must be a list"
                )
            for part in parts:
                if not isinstance(part, dict) or set(part) != {
                    "name",
                    "sha256",
                    "size",
                }:
                    raise VerificationError(
                        "INVALID_RECEIPT", f"Invalid protected part in {category}"
                    )
                if not isinstance(part["name"], str) or not part["name"]:
                    raise VerificationError(
                        "INVALID_RECEIPT", "Protected part needs a name"
                    )
                _validate_sha(part["sha256"], f"protected_features.{category}.sha256")
                if not isinstance(part["size"], int) or part["size"] < 0:
                    raise VerificationError(
                        "INVALID_RECEIPT", "Protected part has invalid size"
                    )

    recalculation = receipt.get("recalculation")
    if not isinstance(recalculation, dict) or "required" not in recalculation:
        raise VerificationError("INVALID_RECEIPT", "Invalid recalculation receipt")
    if recalculation["required"] is True:
        if set(recalculation) != {"required", "evidence"}:
            raise VerificationError(
                "INVALID_RECEIPT", "Required recalculation needs evidence"
            )
        evidence = recalculation["evidence"]
        evidence_fields = {
            "schema_version",
            "artifact_sha256",
            "inventory_sha256",
            "engine",
            "engine_version",
            "completed",
            "full_calculation",
            "formula_count",
            "error_cells",
            "evidence_sha256",
        }
        if not isinstance(evidence, dict) or set(evidence) != evidence_fields:
            raise VerificationError(
                "INVALID_RECEIPT", "Invalid calculation evidence fields"
            )
        if evidence["schema_version"] != CALCULATION_EVIDENCE_SCHEMA_VERSION:
            raise VerificationError(
                "INVALID_RECEIPT", "Invalid calculation evidence schema"
            )
        _validate_sha(evidence["artifact_sha256"], "recalculation.artifact_sha256")
        _validate_sha(evidence["inventory_sha256"], "recalculation.inventory_sha256")
        _validate_sha(evidence["evidence_sha256"], "recalculation.evidence_sha256")
        if evidence["engine"] not in SUPPORTED_CALCULATION_ENGINES:
            raise VerificationError("INVALID_RECEIPT", "Unsupported calculation engine")
        if (
            not isinstance(evidence["engine_version"], str)
            or not evidence["engine_version"]
        ):
            raise VerificationError(
                "INVALID_RECEIPT", "Missing calculation engine version"
            )
        if (
            not isinstance(evidence["formula_count"], int)
            or evidence["formula_count"] < 0
        ):
            raise VerificationError("INVALID_RECEIPT", "Invalid formula_count")
        if not isinstance(evidence["error_cells"], list) or any(
            not isinstance(cell, str) or not cell for cell in evidence["error_cells"]
        ):
            raise VerificationError(
                "INVALID_RECEIPT", "Invalid calculation error_cells"
            )
    elif recalculation["required"] is False:
        if set(recalculation) != {"required", "reason"} or not isinstance(
            recalculation["reason"], str
        ):
            raise VerificationError("INVALID_RECEIPT", "Invalid recalculation waiver")
    else:
        raise VerificationError(
            "INVALID_RECEIPT", "recalculation.required must be boolean"
        )
    _validate_sha(receipt.get("receipt_sha256"), "receipt_sha256")


def seal_calculation_evidence(evidence: dict[str, Any]) -> dict[str, Any]:
    sealed = dict(evidence)
    sealed.pop("evidence_sha256", None)
    sealed["evidence_sha256"] = canonical_sha256(sealed)
    return sealed


def seal_receipt(receipt: dict[str, Any]) -> dict[str, Any]:
    sealed = dict(receipt)
    sealed.pop("receipt_sha256", None)
    sealed["receipt_sha256"] = canonical_sha256(sealed)
    return sealed


def verify_artifact(
    artifact_path: str | os.PathLike[str],
    receipt_path: str | os.PathLike[str],
    baseline_path: str | os.PathLike[str] | None = None,
) -> dict[str, Any]:
    artifact = Path(artifact_path).expanduser().resolve()
    receipt_file = Path(receipt_path).expanduser().resolve()
    receipt = _load_json(receipt_file, "receipt")
    _validate_receipt_shape(receipt)
    artifact_inventory = inspect_workbook(artifact)
    failures: list[dict[str, str]] = []
    checks: list[dict[str, str]] = []

    expected_receipt_sha = canonical_sha256(
        {key: value for key, value in receipt.items() if key != "receipt_sha256"}
    )
    if receipt["receipt_sha256"] != expected_receipt_sha:
        failures.append(
            {
                "code": "RECEIPT_HASH_MISMATCH",
                "message": "Receipt self-hash does not match",
            }
        )
    else:
        checks.append({"code": "RECEIPT_HASH_BOUND", "status": "PASS"})

    artifact_expectation = receipt["artifact"]
    artifact_values = {
        "sha256": artifact_inventory["input"]["sha256"],
        "inventory_sha256": artifact_inventory["inventory_sha256"],
        "package_fingerprint_sha256": artifact_inventory["package"][
            "fingerprint_sha256"
        ],
    }
    for field, actual in artifact_values.items():
        if artifact_expectation[field] != actual:
            failures.append(
                {
                    "code": f"ARTIFACT_{field.upper()}_MISMATCH",
                    "message": f"Artifact {field} does not match its receipt",
                }
            )
        else:
            checks.append({"code": f"ARTIFACT_{field.upper()}_BOUND", "status": "PASS"})

    baseline_expectation = receipt["baseline"]
    if baseline_expectation is None and baseline_path is not None:
        failures.append(
            {
                "code": "UNEXPECTED_BASELINE",
                "message": "Baseline supplied but receipt has none",
            }
        )
    elif baseline_expectation is not None and baseline_path is None:
        failures.append(
            {
                "code": "MISSING_BASELINE",
                "message": "Receipt requires an explicit baseline",
            }
        )
    elif baseline_expectation is not None and baseline_path is not None:
        baseline_inventory = inspect_workbook(baseline_path)
        baseline_values = {
            "sha256": baseline_inventory["input"]["sha256"],
            "inventory_sha256": baseline_inventory["inventory_sha256"],
            "package_fingerprint_sha256": baseline_inventory["package"][
                "fingerprint_sha256"
            ],
        }
        for field, actual in baseline_values.items():
            if baseline_expectation[field] != actual:
                failures.append(
                    {
                        "code": f"BASELINE_{field.upper()}_MISMATCH",
                        "message": f"Baseline {field} does not match its receipt",
                    }
                )
        actual_baseline_features = _feature_snapshot(baseline_inventory)
        if baseline_expectation["protected_features"] != actual_baseline_features:
            failures.append(
                {
                    "code": "BASELINE_FEATURE_RECEIPT_MISMATCH",
                    "message": "Baseline feature inventory does not match its receipt",
                }
            )
        artifact_features = _feature_snapshot(artifact_inventory)
        for category in PRESERVATION_CATEGORIES:
            if artifact_features[category] != actual_baseline_features[category]:
                failures.append(
                    {
                        "code": "PROTECTED_FEATURE_CHANGED",
                        "message": f"Protected feature parts changed: {category}",
                    }
                )
        if not any(
            failure["code"].startswith("BASELINE_")
            or failure["code"] == "PROTECTED_FEATURE_CHANGED"
            for failure in failures
        ):
            checks.append({"code": "BASELINE_FEATURES_PRESERVED", "status": "PASS"})

    formula_count = artifact_inventory["workbook"]["formula_count"]
    recalculation = receipt["recalculation"]
    if formula_count and recalculation["required"] is not True:
        failures.append(
            {
                "code": "RECALCULATION_EVIDENCE_REQUIRED",
                "message": "Artifact contains formulas but receipt waives recalculation",
            }
        )
    elif recalculation["required"] is True:
        evidence = recalculation["evidence"]
        expected_evidence_hash = canonical_sha256(
            {key: value for key, value in evidence.items() if key != "evidence_sha256"}
        )
        evidence_checks = {
            "hash": evidence["evidence_sha256"] == expected_evidence_hash,
            "artifact": evidence["artifact_sha256"] == artifact_values["sha256"],
            "inventory": evidence["inventory_sha256"]
            == artifact_values["inventory_sha256"],
            "completed": evidence["completed"] is True,
            "full": evidence["full_calculation"] is True,
            "formula_count": evidence["formula_count"] == formula_count,
            "errors": evidence["error_cells"] == [],
        }
        for label, passed in evidence_checks.items():
            if not passed:
                failures.append(
                    {
                        "code": f"RECALCULATION_{label.upper()}_MISMATCH",
                        "message": f"Recalculation evidence failed check: {label}",
                    }
                )
        if all(evidence_checks.values()):
            checks.append({"code": "RECALCULATION_EVIDENCE_BOUND", "status": "PASS"})
    elif formula_count == 0 and recalculation != {
        "required": False,
        "reason": "artifact_contains_no_formulas",
    }:
        failures.append(
            {
                "code": "INVALID_RECALCULATION_WAIVER",
                "message": "Formula-free waiver reason is not exact",
            }
        )

    failures.sort(key=lambda row: (row["code"], row["message"]))
    checks.sort(key=lambda row: row["code"])
    result: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        # This verifier proves internal consistency of supplied hashes and
        # structural inventories.  Its recalculation JSON is self-attested,
        # not a signature from Excel or LibreOffice, so it must never emit the
        # stronger word VERIFIED.
        "status": "BLOCKED" if failures else "EVIDENCE_CONSISTENT",
        "artifact": artifact_values,
        "receipt": {
            "path": str(receipt_file),
            "sha256": hashlib.sha256(receipt_file.read_bytes()).hexdigest(),
        },
        "checks": checks,
        "failure_count": len(failures),
        "failures": failures,
    }
    result["report_sha256"] = canonical_sha256(result)
    return result


def _error_payload(code: str, message: str) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "ERROR",
        "error": {"code": code, "message": message},
    }


def main(argv: list[str] | None = None) -> int:
    parser = JsonArgumentParser(description=__doc__)
    parser.add_argument("artifact", help="Artifact workbook to verify")
    parser.add_argument("--receipt", required=True, help="Bound JSON receipt")
    parser.add_argument("--baseline", help="Explicit baseline workbook")
    parser.add_argument("--output", type=Path, help="Atomic JSON output path")
    args = parser.parse_args(argv)
    try:
        report = verify_artifact(args.artifact, args.receipt, args.baseline)
        _emit(report, args.output)
        return 0 if report["status"] == "EVIDENCE_CONSISTENT" else 1
    except (VerificationError, InventoryError) as exc:
        code = exc.code
        _emit(_error_payload(code, str(exc)), args.output)
        return 2
    except OSError as exc:
        _emit(_error_payload("IO_ERROR", str(exc)), args.output)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
