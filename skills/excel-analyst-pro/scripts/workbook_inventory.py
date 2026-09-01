#!/usr/bin/env python3
"""Create a read-only, deterministic inventory of an OOXML Excel package."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import posixpath
import re
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

SCHEMA_VERSION = "excel-workbook-inventory/v1"
MAX_PARTS = 20_000
MAX_PART_BYTES = 128 * 1024 * 1024
MAX_TOTAL_BYTES = 1024 * 1024 * 1024
MAX_COMPRESSION_RATIO = 1_000

NS_MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
NS_REL_DOC = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS_REL_PACKAGE = "http://schemas.openxmlformats.org/package/2006/relationships"

WORKSHEET_CONTROL_TAGS = frozenset(
    {
        "conditionalFormatting",
        "controls",
        "dataConsolidate",
        "dataValidations",
        "drawing",
        "extLst",
        "hyperlinks",
        "legacyDrawing",
        "legacyDrawingHF",
        "mergeCells",
        "oleObjects",
        "protectedRanges",
        "scenarios",
        "sheetProtection",
        "tableParts",
    }
)
WORKBOOK_CONTROL_TAGS = frozenset(
    {
        "definedNames",
        "externalReferences",
        "extLst",
        "fileSharing",
        "functionGroups",
        "pivotCaches",
        "webPublishing",
        "workbookProtection",
    }
)


class InventoryError(Exception):
    """A fail-closed inventory error suitable for a JSON CLI response."""

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


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return _sha256_bytes(payload)


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


def _safe_part_name(name: str) -> bool:
    normalized = posixpath.normpath(name)
    return (
        bool(name)
        and not name.startswith(("/", "\\"))
        and normalized == name
        and normalized != ".."
        and not normalized.startswith("../")
        and "\\" not in name
    )


def _read_part(archive: zipfile.ZipFile, name: str) -> bytes:
    try:
        info = archive.getinfo(name)
    except KeyError as exc:
        raise InventoryError(
            "MISSING_REQUIRED_PART", f"Missing OOXML part: {name}"
        ) from exc
    if info.file_size > MAX_PART_BYTES:
        raise InventoryError("PART_TOO_LARGE", f"OOXML part exceeds size limit: {name}")
    payload = archive.read(info)
    if len(payload) != info.file_size:
        raise InventoryError("TRUNCATED_PART", f"OOXML part is truncated: {name}")
    return payload


def _parse_xml(payload: bytes, part_name: str) -> ET.Element:
    if re.search(rb"<!\s*(?:DOCTYPE|ENTITY)\b", payload, flags=re.IGNORECASE):
        raise InventoryError(
            "UNSAFE_XML_DECLARATION", f"DTD or entity declaration in {part_name}"
        )
    try:
        return ET.fromstring(payload)
    except ET.ParseError as exc:
        raise InventoryError(
            "INVALID_XML", f"Invalid XML in {part_name}: {exc}"
        ) from exc


def _relationship_part_for(source_part: str) -> str:
    directory = posixpath.dirname(source_part)
    filename = posixpath.basename(source_part)
    return posixpath.join(directory, "_rels", f"{filename}.rels")


def _source_part_for_relationship_part(relationship_part: str) -> str:
    if relationship_part == "_rels/.rels":
        return ""
    directory, filename = posixpath.split(relationship_part)
    if not directory.endswith("/_rels") or not filename.endswith(".rels"):
        raise InventoryError(
            "INVALID_RELATIONSHIP_PART",
            f"Cannot identify source for relationship part: {relationship_part}",
        )
    source_directory = directory[: -len("/_rels")]
    return posixpath.join(source_directory, filename[: -len(".rels")])


def _resolve_relationship_target(source_part: str, target: str) -> str:
    if target.startswith("/"):
        resolved = target.lstrip("/")
    else:
        resolved = posixpath.normpath(
            posixpath.join(posixpath.dirname(source_part), target)
        )
    if not _safe_part_name(resolved):
        raise InventoryError(
            "UNSAFE_RELATIONSHIP_TARGET",
            f"Relationship from {source_part} escapes the package: {target}",
        )
    return resolved


def _relationships(
    archive: zipfile.ZipFile, source_part: str
) -> tuple[dict[str, dict[str, str]], list[dict[str, str]]]:
    rels_name = _relationship_part_for(source_part)
    if rels_name not in archive.namelist():
        return {}, []
    root = _parse_xml(_read_part(archive, rels_name), rels_name)
    by_id: dict[str, dict[str, str]] = {}
    external: list[dict[str, str]] = []
    for element in root.findall(f"{{{NS_REL_PACKAGE}}}Relationship"):
        rel_id = element.attrib.get("Id", "")
        rel_type = element.attrib.get("Type", "")
        target = element.attrib.get("Target", "")
        target_mode = element.attrib.get("TargetMode", "Internal")
        if not rel_id or not rel_type or not target:
            raise InventoryError(
                "INVALID_RELATIONSHIP", f"Incomplete relationship in {rels_name}"
            )
        record = {
            "id": rel_id,
            "type": rel_type,
            "target": target,
            "target_mode": target_mode,
        }
        if target_mode.lower() == "external":
            external.append({"source_part": source_part, **record})
        else:
            record["resolved_target"] = _resolve_relationship_target(
                source_part, target
            )
        by_id[rel_id] = record
    return by_id, sorted(
        external, key=lambda row: (row["source_part"], row["id"], row["target"])
    )


def _feature_parts(
    parts: list[dict[str, Any]], external_relationships: list[dict[str, str]]
) -> dict[str, dict[str, Any]]:
    rules: dict[str, tuple[str, ...]] = {
        "macros": ("xl/vbaProject.bin", "xl/vbaProjectSignature.bin"),
        "pivots": ("xl/pivotTables/", "xl/pivotCache/"),
        "embedded": ("xl/embeddings/", "xl/oleObjects/"),
        "external_links": ("xl/externalLinks/",),
        "connections": ("xl/connections.xml",),
        "queries": ("xl/queryTables/", "xl/queries/"),
        "data_model": ("xl/model/", "xl/item.data"),
        "activex": ("xl/activeX/",),
        "custom_xml": ("customXml/",),
        "digital_signatures": ("_xmlsignatures/",),
        "web_extensions": ("xl/webextensions/", "webextensions/"),
        "drawings": ("xl/drawings/",),
        "charts": ("xl/charts/",),
        "media": ("xl/media/",),
        "slicers": ("xl/slicers/", "xl/slicerCaches/"),
        "controls": ("xl/ctrlProps/",),
        "comments": ("xl/comments", "xl/threadedComments/", "xl/persons/"),
        "printer_settings": ("xl/printerSettings/",),
    }
    features: dict[str, dict[str, Any]] = {}
    for category, prefixes in rules.items():
        selected = [
            {"name": row["name"], "sha256": row["sha256"], "size": row["size"]}
            for row in parts
            if any(
                row["name"] == prefix or row["name"].startswith(prefix)
                for prefix in prefixes
            )
        ]
        features[category] = {
            "present": bool(selected),
            "parts": sorted(selected, key=lambda row: row["name"]),
        }
    if external_relationships:
        features["external_links"]["present"] = True
        external_relationship_part_names = {
            _relationship_part_for(relationship["source_part"])
            for relationship in external_relationships
        }
        existing_names = {part["name"] for part in features["external_links"]["parts"]}
        for part in parts:
            if (
                part["name"] in external_relationship_part_names
                and part["name"] not in existing_names
            ):
                features["external_links"]["parts"].append(
                    {
                        "name": part["name"],
                        "sha256": part["sha256"],
                        "size": part["size"],
                    }
                )
        features["external_links"]["parts"].sort(key=lambda row: row["name"])
    features["external_links"]["relationships"] = external_relationships
    return features


def _structural_control_parts(
    root: ET.Element, part_name: str, protected_tags: frozenset[str]
) -> list[dict[str, Any]]:
    """Fingerprint non-cell OOXML controls embedded inside an XML part."""
    records: list[dict[str, Any]] = []
    occurrences: dict[str, int] = {}
    for element in root.iter():
        local_name = element.tag.rsplit("}", 1)[-1]
        if local_name not in protected_tags:
            continue
        ordinal = occurrences.get(local_name, 0)
        occurrences[local_name] = ordinal + 1
        payload = ET.tostring(element, encoding="utf-8")
        records.append(
            {
                "name": f"{part_name}#{local_name}[{ordinal}]",
                "sha256": _sha256_bytes(payload),
                "size": len(payload),
            }
        )
    return sorted(records, key=lambda row: row["name"])


def inspect_workbook(path: str | os.PathLike[str]) -> dict[str, Any]:
    workbook_path = Path(path).expanduser().resolve()
    if not workbook_path.is_file():
        raise InventoryError(
            "INPUT_NOT_FILE", f"Workbook is not a file: {workbook_path}"
        )
    if not zipfile.is_zipfile(workbook_path):
        raise InventoryError(
            "NOT_OOXML_ZIP", "Workbook is not a valid OOXML ZIP package"
        )

    input_sha256 = _sha256_file(workbook_path)
    try:
        archive = zipfile.ZipFile(workbook_path, "r")
    except (OSError, zipfile.BadZipFile) as exc:
        raise InventoryError(
            "INVALID_ZIP", f"Cannot open OOXML package: {exc}"
        ) from exc

    with archive:
        infos = archive.infolist()
        if len(infos) > MAX_PARTS:
            raise InventoryError(
                "TOO_MANY_PARTS", "OOXML package contains too many parts"
            )
        names = [info.filename for info in infos]
        if len(names) != len(set(names)):
            raise InventoryError(
                "DUPLICATE_PART", "OOXML package has duplicate part names"
            )

        total_size = 0
        parts: list[dict[str, Any]] = []
        for info in infos:
            if not _safe_part_name(info.filename):
                raise InventoryError(
                    "UNSAFE_PART_NAME", f"Unsafe OOXML part name: {info.filename}"
                )
            if info.flag_bits & 0x1:
                raise InventoryError(
                    "ENCRYPTED_ZIP_ENTRY", f"Encrypted OOXML part: {info.filename}"
                )
            total_size += info.file_size
            if info.file_size > MAX_PART_BYTES or total_size > MAX_TOTAL_BYTES:
                raise InventoryError(
                    "PACKAGE_TOO_LARGE", "OOXML package exceeds size limits"
                )
            if info.file_size > 1024 * 1024 and (
                info.compress_size == 0
                or info.file_size / info.compress_size > MAX_COMPRESSION_RATIO
            ):
                raise InventoryError(
                    "SUSPICIOUS_COMPRESSION_RATIO",
                    f"Suspicious compression ratio for {info.filename}",
                )
            payload = archive.read(info)
            parts.append(
                {
                    "name": info.filename,
                    "sha256": _sha256_bytes(payload),
                    "size": info.file_size,
                    "compressed_size": info.compress_size,
                }
            )
        parts.sort(key=lambda row: row["name"])

        for required in ("[Content_Types].xml", "xl/workbook.xml"):
            if required not in names:
                raise InventoryError(
                    "MISSING_REQUIRED_PART", f"Missing OOXML part: {required}"
                )

        workbook_root = _parse_xml(
            _read_part(archive, "xl/workbook.xml"), "xl/workbook.xml"
        )
        workbook_rels, workbook_external = _relationships(archive, "xl/workbook.xml")

        all_external = list(workbook_external)
        for name in names:
            if not name.endswith(".rels"):
                continue
            source_part = _source_part_for_relationship_part(name)
            if source_part == "xl/workbook.xml":
                continue
            root = _parse_xml(_read_part(archive, name), name)
            for element in root.findall(f"{{{NS_REL_PACKAGE}}}Relationship"):
                if element.attrib.get("TargetMode", "Internal").lower() != "external":
                    continue
                rel_id = element.attrib.get("Id", "")
                rel_type = element.attrib.get("Type", "")
                target = element.attrib.get("Target", "")
                if not rel_id or not rel_type or not target:
                    raise InventoryError(
                        "INVALID_RELATIONSHIP", f"Incomplete relationship in {name}"
                    )
                all_external.append(
                    {
                        "source_part": source_part,
                        "id": rel_id,
                        "type": rel_type,
                        "target": target,
                        "target_mode": element.attrib.get("TargetMode", "External"),
                    }
                )
        all_external = sorted(
            {json.dumps(row, sort_keys=True): row for row in all_external}.values(),
            key=lambda row: (row["source_part"], row["id"], row["target"]),
        )

        sheets: list[dict[str, Any]] = []
        formulas: list[dict[str, Any]] = []
        external_formula_cells: list[dict[str, str]] = []
        worksheet_controls: list[dict[str, Any]] = []
        sheets_parent = workbook_root.find(f"{{{NS_MAIN}}}sheets")
        if sheets_parent is None:
            raise InventoryError("MISSING_SHEETS", "Workbook has no sheets collection")
        for sheet in sheets_parent.findall(f"{{{NS_MAIN}}}sheet"):
            rel_id = sheet.attrib.get(f"{{{NS_REL_DOC}}}id", "")
            relationship = workbook_rels.get(rel_id)
            if relationship is None or "resolved_target" not in relationship:
                raise InventoryError(
                    "UNRESOLVED_SHEET_RELATIONSHIP",
                    f"Cannot resolve worksheet relationship {rel_id}",
                )
            sheet_path = relationship["resolved_target"]
            if sheet_path not in names:
                raise InventoryError(
                    "MISSING_WORKSHEET_PART", f"Missing worksheet part: {sheet_path}"
                )
            state = sheet.attrib.get("state", "visible")
            sheet_record = {
                "name": sheet.attrib.get("name", ""),
                "sheet_id": sheet.attrib.get("sheetId", ""),
                "state": state,
                "path": sheet_path,
            }
            sheets.append(sheet_record)
            sheet_root = _parse_xml(_read_part(archive, sheet_path), sheet_path)
            worksheet_controls.extend(
                _structural_control_parts(
                    sheet_root, sheet_path, WORKSHEET_CONTROL_TAGS
                )
            )
            for cell in sheet_root.iter(f"{{{NS_MAIN}}}c"):
                formula = cell.find(f"{{{NS_MAIN}}}f")
                if formula is None:
                    continue
                cached = cell.find(f"{{{NS_MAIN}}}v")
                formula_text = formula.text or ""
                formula_record = {
                    "sheet": sheet_record["name"],
                    "cell": cell.attrib.get("r", ""),
                    "formula": formula_text,
                    "attributes": dict(sorted(formula.attrib.items())),
                    "cached_value_present": cached is not None,
                    "cached_value_sha256": (
                        _sha256_bytes((cached.text or "").encode("utf-8"))
                        if cached is not None
                        else None
                    ),
                }
                formulas.append(formula_record)
                if "[" in formula_text and "]" in formula_text:
                    external_formula_cells.append(
                        {
                            "sheet": sheet_record["name"],
                            "cell": cell.attrib.get("r", ""),
                            "part": sheet_path,
                        }
                    )

        sheets.sort(key=lambda row: (row["sheet_id"], row["name"]))
        formulas.sort(key=lambda row: (row["sheet"], row["cell"], row["formula"]))
        external_formula_cells.sort(key=lambda row: (row["sheet"], row["cell"]))

        calc_pr = workbook_root.find(f"{{{NS_MAIN}}}calcPr")
        calculation = {
            "mode": (
                calc_pr.attrib.get("calcMode", "automatic")
                if calc_pr is not None
                else "automatic"
            ),
            "calc_id": calc_pr.attrib.get("calcId") if calc_pr is not None else None,
            "full_calc_on_load": (
                calc_pr.attrib.get("fullCalcOnLoad") if calc_pr is not None else None
            ),
            "force_full_calc": (
                calc_pr.attrib.get("forceFullCalc") if calc_pr is not None else None
            ),
            "calc_on_save": (
                calc_pr.attrib.get("calcOnSave") if calc_pr is not None else None
            ),
        }

        features = _feature_parts(parts, all_external)
        workbook_controls = _structural_control_parts(
            workbook_root, "xl/workbook.xml", WORKBOOK_CONTROL_TAGS
        )
        features["worksheet_controls"] = {
            "present": bool(worksheet_controls),
            "parts": sorted(worksheet_controls, key=lambda row: row["name"]),
        }
        features["workbook_controls"] = {
            "present": bool(workbook_controls),
            "parts": workbook_controls,
        }
        if external_formula_cells:
            features["external_links"]["present"] = True
            external_formula_part_names = {
                cell["part"] for cell in external_formula_cells
            }
            existing_names = {
                part["name"] for part in features["external_links"]["parts"]
            }
            for part in parts:
                if (
                    part["name"] in external_formula_part_names
                    and part["name"] not in existing_names
                ):
                    features["external_links"]["parts"].append(
                        {
                            "name": part["name"],
                            "sha256": part["sha256"],
                            "size": part["size"],
                        }
                    )
            features["external_links"]["parts"].sort(key=lambda row: row["name"])
        features["external_links"]["formula_cells"] = external_formula_cells
        risky_categories = sorted(
            category for category, value in features.items() if value["present"]
        )
        hidden_sheets = [
            {"name": row["name"], "state": row["state"]}
            for row in sheets
            if row["state"] != "visible"
        ]
        recalculation_required = bool(formulas)
        reasons: list[str] = []
        if formulas:
            reasons.append("formula_results_require_calculation-engine_evidence")
        if calculation["mode"].lower() in {"manual", "autoNoTable".lower(), "partial"}:
            reasons.append(f"workbook_calculation_mode_is_{calculation['mode']}")

        package_parts = [
            {"name": row["name"], "sha256": row["sha256"], "size": row["size"]}
            for row in parts
        ]
        inventory: dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "status": "INVENTORIED",
            "input": {
                "path": str(workbook_path),
                "sha256": input_sha256,
                "size": workbook_path.stat().st_size,
            },
            "package": {
                "part_count": len(parts),
                "uncompressed_size": total_size,
                "fingerprint_sha256": canonical_sha256(package_parts),
                "parts": parts,
            },
            "workbook": {
                "calculation": calculation,
                "sheets": sheets,
                "hidden_sheets": hidden_sheets,
                "formula_count": len(formulas),
                "formula_fingerprint_sha256": canonical_sha256(formulas),
                "formulas": formulas,
            },
            "features": features,
            "risk": {
                "categories": risky_categories,
                "requires_native_backend_for_write": bool(risky_categories),
                "recalculation_required": recalculation_required,
                "recalculation_reasons": reasons,
            },
        }
        inventory["inventory_sha256"] = canonical_sha256(
            {
                "input_sha256": input_sha256,
                "package_fingerprint_sha256": inventory["package"][
                    "fingerprint_sha256"
                ],
                "workbook": inventory["workbook"],
                "features": inventory["features"],
                "risk": inventory["risk"],
            }
        )
        if _sha256_file(workbook_path) != input_sha256:
            raise InventoryError(
                "INPUT_CHANGED_DURING_READ",
                "Workbook changed while its inventory was being generated",
            )
        return inventory


def _error_payload(exc: InventoryError) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "ERROR",
        "error": {"code": exc.code, "message": str(exc)},
    }


def main(argv: list[str] | None = None) -> int:
    parser = JsonArgumentParser(description=__doc__)
    parser.add_argument("workbook", help="Path to an .xlsx/.xlsm OOXML workbook")
    parser.add_argument("--output", type=Path, help="Atomic JSON output path")
    args = parser.parse_args(argv)
    try:
        result = inspect_workbook(args.workbook)
        _emit(result, args.output)
        return 0
    except InventoryError as exc:
        _emit(_error_payload(exc), args.output)
        return 2
    except (OSError, zipfile.BadZipFile) as exc:
        error = InventoryError("IO_ERROR", str(exc))
        _emit(_error_payload(error), args.output)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
