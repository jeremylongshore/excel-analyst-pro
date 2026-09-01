#!/usr/bin/env python3
"""Profile every CSV row and reconcile it against an explicit data contract."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import sys
import tempfile
import time
from collections import defaultdict
from collections.abc import Iterable
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, TextIO

SCHEMA_VERSION = "excel-csv-profile/v1"
SPEC_SCHEMA_VERSION = "excel-csv-contract/v1"
ALLOWED_ENCODINGS = {"utf-8", "utf-8-sig"}
ALLOWED_TYPES = {"text", "integer", "decimal", "boolean"}
FORMULA_PREFIXES = {"=", "+", "-", "@", "\t", "\r", "\n", "＝", "＋", "－", "＠"}
MAX_INPUT_BYTES = 512 * 1024 * 1024
MAX_ROWS = 1_000_000
MAX_DISTINCT_VALUES = 500_000
MAX_EXCEPTIONS = 50_000
INTEGER_PATTERN = re.compile(r"[+-]?(?:0|[1-9][0-9]*)\Z")
DECIMAL_PATTERN = re.compile(
    r"[+-]?(?:(?:0|[1-9][0-9]*)(?:\.[0-9]+)?|\.[0-9]+)(?:[Ee][+-]?[0-9]+)?\Z"
)


class ProfileError(Exception):
    """A fail-closed contract or input error."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def _append_exception(
    exceptions: list[dict[str, Any]], record: dict[str, Any], source: str
) -> None:
    """Retain a bounded diagnostic or fail before allocating another record."""
    if len(exceptions) >= MAX_EXCEPTIONS:
        raise ProfileError(
            "EXCEPTION_LIMIT_EXCEEDED",
            f"{source} exceeds {MAX_EXCEPTIONS} retained exceptions",
        )
    exceptions.append(record)


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


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_sha256(value: Any) -> str:
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


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


def _require_string(value: Any, location: str) -> str:
    if not isinstance(value, str) or not value:
        raise ProfileError("INVALID_SPEC", f"{location} must be a non-empty string")
    return value


def _require_string_list(value: Any, location: str) -> list[str]:
    if (
        not isinstance(value, list)
        or not value
        or any(not isinstance(item, str) or not item for item in value)
        or len(value) != len(set(value))
    ):
        raise ProfileError(
            "INVALID_SPEC", f"{location} must be a non-empty list of unique strings"
        )
    return value


def _validate_spec(raw: Any, spec_path: Path) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise ProfileError("INVALID_SPEC", "Contract must be a JSON object")
    allowed = {
        "schema_version",
        "encoding",
        "delimiter",
        "has_header",
        "grain",
        "keys",
        "types",
        "required_columns",
        "units",
        "signs",
        "controls",
        "lookup",
    }
    unknown = sorted(set(raw) - allowed)
    if unknown:
        raise ProfileError("INVALID_SPEC", f"Unknown contract fields: {unknown}")
    if raw.get("schema_version") != SPEC_SCHEMA_VERSION:
        raise ProfileError(
            "INVALID_SPEC", f"schema_version must be {SPEC_SCHEMA_VERSION}"
        )
    encoding = _require_string(raw.get("encoding"), "encoding").lower()
    if encoding not in ALLOWED_ENCODINGS:
        raise ProfileError(
            "INVALID_SPEC", f"encoding must be one of {sorted(ALLOWED_ENCODINGS)}"
        )
    delimiter = _require_string(raw.get("delimiter"), "delimiter")
    if len(delimiter) != 1 or delimiter in {"\r", "\n", '"'}:
        raise ProfileError("INVALID_SPEC", "delimiter must be one safe character")
    if raw.get("has_header") is not True:
        raise ProfileError("INVALID_SPEC", "has_header must be true")
    grain = _require_string(raw.get("grain"), "grain")
    keys = _require_string_list(raw.get("keys"), "keys")

    types = raw.get("types")
    if not isinstance(types, dict) or not types:
        raise ProfileError("INVALID_SPEC", "types must be a non-empty object")
    normalized_types: dict[str, str] = {}
    for column, type_name in types.items():
        _require_string(column, "types column")
        type_name = _require_string(type_name, f"types.{column}")
        if type_name.startswith("date:"):
            if not type_name[5:]:
                raise ProfileError(
                    "INVALID_SPEC", f"types.{column} requires a date format"
                )
        elif type_name not in ALLOWED_TYPES:
            raise ProfileError(
                "INVALID_SPEC", f"Unsupported type for {column}: {type_name}"
            )
        normalized_types[column] = type_name
    missing_key_types = sorted(set(keys) - set(normalized_types))
    if missing_key_types:
        raise ProfileError(
            "INVALID_SPEC", f"Key columns missing types: {missing_key_types}"
        )

    required_columns = raw.get("required_columns", list(normalized_types))
    required_columns = _require_string_list(required_columns, "required_columns")
    if missing := sorted(set(required_columns) - set(normalized_types)):
        raise ProfileError("INVALID_SPEC", f"Required columns missing types: {missing}")

    units = raw.get("units")
    signs = raw.get("signs")
    if not isinstance(units, dict) or not units:
        raise ProfileError("INVALID_SPEC", "units must be a non-empty object")
    if not isinstance(signs, dict) or not signs:
        raise ProfileError("INVALID_SPEC", "signs must be a non-empty object")
    for label, mapping in (("units", units), ("signs", signs)):
        for column, value in mapping.items():
            if column not in normalized_types:
                raise ProfileError(
                    "INVALID_SPEC", f"{label} references unknown column: {column}"
                )
            _require_string(value, f"{label}.{column}")

    controls = raw.get("controls")
    if not isinstance(controls, list) or not controls:
        raise ProfileError("INVALID_SPEC", "controls must be a non-empty list")
    normalized_controls: list[dict[str, str]] = []
    control_names: set[str] = set()
    for index, control in enumerate(controls):
        if not isinstance(control, dict) or set(control) != {"name", "column"}:
            raise ProfileError(
                "INVALID_SPEC", f"controls[{index}] must contain name and column only"
            )
        name = _require_string(control["name"], f"controls[{index}].name")
        column = _require_string(control["column"], f"controls[{index}].column")
        if name in control_names:
            raise ProfileError("INVALID_SPEC", f"Duplicate control name: {name}")
        if normalized_types.get(column) not in {"integer", "decimal"}:
            raise ProfileError(
                "INVALID_SPEC", f"Control column must be numeric: {column}"
            )
        if column not in units or column not in signs:
            raise ProfileError(
                "INVALID_SPEC",
                f"Control column requires explicit units and signs: {column}",
            )
        control_names.add(name)
        normalized_controls.append({"name": name, "column": column})

    lookup = raw.get("lookup")
    normalized_lookup: dict[str, Any] | None = None
    if lookup is not None:
        if not isinstance(lookup, dict):
            raise ProfileError("INVALID_SPEC", "lookup must be an object")
        lookup_allowed = {
            "path",
            "encoding",
            "delimiter",
            "keys",
            "foreign_keys",
        }
        if unknown_lookup := sorted(set(lookup) - lookup_allowed):
            raise ProfileError(
                "INVALID_SPEC", f"Unknown lookup fields: {unknown_lookup}"
            )
        lookup_path_text = _require_string(lookup.get("path"), "lookup.path")
        lookup_encoding = _require_string(
            lookup.get("encoding"), "lookup.encoding"
        ).lower()
        if lookup_encoding not in ALLOWED_ENCODINGS:
            raise ProfileError("INVALID_SPEC", "Unsupported lookup encoding")
        lookup_delimiter = _require_string(lookup.get("delimiter"), "lookup.delimiter")
        if len(lookup_delimiter) != 1 or lookup_delimiter in {"\r", "\n", '"'}:
            raise ProfileError("INVALID_SPEC", "Invalid lookup delimiter")
        lookup_keys = _require_string_list(lookup.get("keys"), "lookup.keys")
        foreign_keys = _require_string_list(
            lookup.get("foreign_keys"), "lookup.foreign_keys"
        )
        if len(lookup_keys) != len(foreign_keys):
            raise ProfileError(
                "INVALID_SPEC", "lookup.keys and lookup.foreign_keys lengths differ"
            )
        if missing := sorted(set(foreign_keys) - set(normalized_types)):
            raise ProfileError(
                "INVALID_SPEC", f"Foreign keys missing source types: {missing}"
            )
        if Path(lookup_path_text).is_absolute():
            raise ProfileError(
                "INVALID_SPEC", "lookup.path must be relative to the contract directory"
            )
        contract_directory = spec_path.parent.resolve()
        lookup_path = (contract_directory / lookup_path_text).resolve()
        if not lookup_path.is_relative_to(contract_directory):
            raise ProfileError(
                "INVALID_SPEC", "lookup.path may not escape the contract directory"
            )
        normalized_lookup = {
            "path": lookup_path,
            "encoding": lookup_encoding,
            "delimiter": lookup_delimiter,
            "keys": lookup_keys,
            "foreign_keys": foreign_keys,
        }

    return {
        "schema_version": SPEC_SCHEMA_VERSION,
        "encoding": encoding,
        "delimiter": delimiter,
        "grain": grain,
        "keys": keys,
        "types": normalized_types,
        "required_columns": required_columns,
        "units": dict(sorted(units.items())),
        "signs": dict(sorted(signs.items())),
        "controls": normalized_controls,
        "lookup": normalized_lookup,
    }


def _load_spec(path: Path) -> tuple[dict[str, Any], str]:
    if not path.is_file():
        raise ProfileError("SPEC_NOT_FILE", f"Contract is not a file: {path}")
    payload = path.read_bytes()
    try:
        raw = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProfileError("INVALID_SPEC_JSON", str(exc)) from exc
    return _validate_spec(raw, path), hashlib.sha256(payload).hexdigest()


def _preview(value: str, limit: int = 120) -> str:
    escaped = value.encode("unicode_escape", errors="backslashreplace").decode("ascii")
    return escaped if len(escaped) <= limit else f"{escaped[:limit]}..."


def _is_formula_injection(value: str) -> bool:
    return bool(value) and value[0] in FORMULA_PREFIXES


def _parse_value(value: str, type_name: str) -> tuple[bool, Decimal | None]:
    if type_name == "text":
        return True, None
    if value == "":
        return True, None
    if type_name == "integer":
        if not INTEGER_PATTERN.fullmatch(value):
            return False, None
        return True, Decimal(value)
    if type_name == "decimal":
        if not DECIMAL_PATTERN.fullmatch(value):
            return False, None
        try:
            parsed = Decimal(value)
        except InvalidOperation:
            return False, None
        return parsed.is_finite(), parsed if parsed.is_finite() else None
    if type_name == "boolean":
        return value in {"true", "false"}, None
    if type_name.startswith("date:"):
        format_string = type_name[5:]
        try:
            parsed_date = time.strptime(value, format_string)
        except ValueError:
            return False, None
        return time.strftime(format_string, parsed_date) == value, None
    raise AssertionError(f"unhandled type: {type_name}")


def _read_csv_rows(
    path: Path, encoding: str, delimiter: str
) -> tuple[list[str], Iterable[tuple[int, list[str]]], TextIO]:
    if not path.is_file():
        raise ProfileError("INPUT_NOT_FILE", f"CSV is not a file: {path}")
    if path.stat().st_size > MAX_INPUT_BYTES:
        raise ProfileError(
            "INPUT_TOO_LARGE", f"CSV exceeds {MAX_INPUT_BYTES} bytes: {path}"
        )
    try:
        handle = path.open("r", encoding=encoding, newline="")
        reader = csv.reader(handle, delimiter=delimiter, strict=True)
        try:
            header = next(reader)
        except StopIteration as exc:
            handle.close()
            raise ProfileError("EMPTY_CSV", f"CSV is empty: {path}") from exc
    except (OSError, UnicodeError, csv.Error) as exc:
        raise ProfileError("CSV_READ_ERROR", str(exc)) from exc

    if not header or any(column == "" for column in header):
        handle.close()
        raise ProfileError("INVALID_HEADER", "CSV headers must be non-empty")
    if len(header) != len(set(header)):
        handle.close()
        raise ProfileError("DUPLICATE_HEADER", "CSV headers must be unique")

    def rows() -> Iterable[tuple[int, list[str]]]:
        try:
            yield from enumerate(reader, start=2)
        except (UnicodeError, csv.Error) as exc:
            raise ProfileError("CSV_READ_ERROR", str(exc)) from exc
        finally:
            handle.close()

    return header, rows(), handle


def _lookup_keys(
    spec: dict[str, Any],
) -> tuple[set[tuple[str, ...]], list[dict[str, Any]], dict[str, Any] | None]:
    lookup = spec["lookup"]
    if lookup is None:
        return set(), [], None
    path: Path = lookup["path"]
    if not path.is_file():
        raise ProfileError("INPUT_NOT_FILE", f"Lookup CSV is not a file: {path}")
    initial_sha256 = _sha256_file(path)
    header, rows, handle = _read_csv_rows(path, lookup["encoding"], lookup["delimiter"])
    missing = sorted(set(lookup["keys"]) - set(header))
    if missing:
        handle.close()
        raise ProfileError(
            "LOOKUP_SCHEMA_MISMATCH", f"Missing lookup columns: {missing}"
        )
    indexes = [header.index(column) for column in lookup["keys"]]
    keys: set[tuple[str, ...]] = set()
    first_rows: dict[tuple[str, ...], int] = {}
    exceptions: list[dict[str, Any]] = []
    row_count = 0
    for row_number, row in rows:
        row_count += 1
        if row_count > MAX_ROWS:
            raise ProfileError("ROW_LIMIT_EXCEEDED", f"Lookup exceeds {MAX_ROWS} rows")
        if len(row) != len(header):
            _append_exception(
                exceptions,
                {
                    "code": "LOOKUP_ROW_WIDTH_MISMATCH",
                    "row": row_number,
                    "expected": len(header),
                    "actual": len(row),
                },
                "Lookup",
            )
            continue
        key = tuple(row[index] for index in indexes)
        if any(value == "" for value in key):
            _append_exception(
                exceptions,
                {"code": "MISSING_LOOKUP_KEY", "row": row_number, "key": list(key)},
                "Lookup",
            )
            continue
        if key in keys:
            _append_exception(
                exceptions,
                {
                    "code": "DUPLICATE_LOOKUP_KEY",
                    "row": row_number,
                    "first_row": first_rows[key],
                    "key": list(key),
                },
                "Lookup",
            )
        else:
            keys.add(key)
            first_rows[key] = row_number
            if len(keys) > MAX_ROWS:
                raise ProfileError(
                    "KEY_LIMIT_EXCEEDED", f"Lookup exceeds {MAX_ROWS} unique keys"
                )
    if _sha256_file(path) != initial_sha256:
        raise ProfileError(
            "LOOKUP_CHANGED_DURING_READ", "Lookup CSV changed while it was profiled"
        )
    return (
        keys,
        exceptions,
        {
            "path": str(path),
            "sha256": initial_sha256,
            "row_count": row_count,
            "unique_key_count": len(keys),
            "keys": lookup["keys"],
        },
    )


def profile_csv(
    input_path: str | os.PathLike[str], spec_path: str | os.PathLike[str]
) -> dict[str, Any]:
    csv_path = Path(input_path).expanduser().resolve()
    contract_path = Path(spec_path).expanduser().resolve()
    spec, spec_sha256 = _load_spec(contract_path)
    if not csv_path.is_file():
        raise ProfileError("INPUT_NOT_FILE", f"CSV is not a file: {csv_path}")
    source_sha256 = _sha256_file(csv_path)
    lookup_keys, lookup_exceptions, lookup_receipt = _lookup_keys(spec)
    header, rows, handle = _read_csv_rows(csv_path, spec["encoding"], spec["delimiter"])

    missing_columns = sorted(set(spec["required_columns"]) - set(header))
    if missing_columns:
        handle.close()
        raise ProfileError(
            "SOURCE_SCHEMA_MISMATCH", f"Missing source columns: {missing_columns}"
        )
    unknown_columns = sorted(set(header) - set(spec["types"]))
    if unknown_columns:
        handle.close()
        raise ProfileError(
            "SOURCE_SCHEMA_MISMATCH",
            f"Source columns without explicit types: {unknown_columns}",
        )

    exceptions: list[dict[str, Any]] = list(lookup_exceptions)
    profiles: dict[str, dict[str, Any]] = {
        column: {
            "empty_count": 0,
            "nonempty_count": 0,
            "distinct_values": set(),
            "type_error_count": 0,
            "formula_injection_count": 0,
        }
        for column in header
    }
    key_indexes = [header.index(column) for column in spec["keys"]]
    source_keys: dict[tuple[str, ...], int] = {}
    foreign_indexes = (
        [header.index(column) for column in spec["lookup"]["foreign_keys"]]
        if spec["lookup"] is not None
        else []
    )
    control_by_column: dict[str, list[str]] = defaultdict(list)
    for control in spec["controls"]:
        control_by_column[control["column"]].append(control["name"])
    control_totals: dict[str, Decimal] = {
        control["name"]: Decimal(0) for control in spec["controls"]
    }
    control_valid_counts: dict[str, int] = defaultdict(int)
    control_invalid_counts: dict[str, int] = defaultdict(int)
    row_count = 0
    valid_width_count = 0
    distinct_value_count = 0

    for row_number, row in rows:
        row_count += 1
        if row_count > MAX_ROWS:
            raise ProfileError("ROW_LIMIT_EXCEEDED", f"Source exceeds {MAX_ROWS} rows")
        if len(row) != len(header):
            _append_exception(
                exceptions,
                {
                    "code": "ROW_WIDTH_MISMATCH",
                    "row": row_number,
                    "expected": len(header),
                    "actual": len(row),
                },
                "Source",
            )
            continue
        valid_width_count += 1
        key = tuple(row[index] for index in key_indexes)
        if any(value == "" for value in key):
            _append_exception(
                exceptions,
                {"code": "MISSING_KEY", "row": row_number, "key": list(key)},
                "Source",
            )
        elif key in source_keys:
            _append_exception(
                exceptions,
                {
                    "code": "DUPLICATE_SOURCE_KEY",
                    "row": row_number,
                    "first_row": source_keys[key],
                    "key": list(key),
                },
                "Source",
            )
        else:
            source_keys[key] = row_number
            if len(source_keys) > MAX_ROWS:
                raise ProfileError(
                    "KEY_LIMIT_EXCEEDED", f"Source exceeds {MAX_ROWS} unique keys"
                )

        if foreign_indexes:
            foreign_key = tuple(row[index] for index in foreign_indexes)
            if any(value == "" for value in foreign_key):
                _append_exception(
                    exceptions,
                    {
                        "code": "MISSING_FOREIGN_KEY",
                        "row": row_number,
                        "key": list(foreign_key),
                    },
                    "Source",
                )
            elif foreign_key not in lookup_keys:
                _append_exception(
                    exceptions,
                    {
                        "code": "UNMATCHED_FOREIGN_KEY",
                        "row": row_number,
                        "key": list(foreign_key),
                    },
                    "Source",
                )

        for index, column in enumerate(header):
            value = row[index]
            profile = profiles[column]
            if value == "":
                profile["empty_count"] += 1
                if column in spec["required_columns"]:
                    _append_exception(
                        exceptions,
                        {
                            "code": "MISSING_REQUIRED_VALUE",
                            "row": row_number,
                            "column": column,
                        },
                        "Source",
                    )
            else:
                profile["nonempty_count"] += 1
                if value not in profile["distinct_values"]:
                    distinct_value_count += 1
                    if distinct_value_count > MAX_DISTINCT_VALUES:
                        raise ProfileError(
                            "DISTINCT_LIMIT_EXCEEDED",
                            "Source exceeds the retained distinct-value budget of "
                            f"{MAX_DISTINCT_VALUES}",
                        )
                    profile["distinct_values"].add(value)
            valid, numeric_value = _parse_value(value, spec["types"][column])
            is_declared_numeric = (
                spec["types"][column] in {"integer", "decimal"}
                and valid
                and numeric_value is not None
            )
            if _is_formula_injection(value) and not is_declared_numeric:
                profile["formula_injection_count"] += 1
                _append_exception(
                    exceptions,
                    {
                        "code": "FORMULA_INJECTION_RISK",
                        "row": row_number,
                        "column": column,
                        "value_preview": _preview(value),
                    },
                    "Source",
                )
            if not valid:
                profile["type_error_count"] += 1
                _append_exception(
                    exceptions,
                    {
                        "code": "TYPE_MISMATCH",
                        "row": row_number,
                        "column": column,
                        "expected_type": spec["types"][column],
                        "value_preview": _preview(value),
                    },
                    "Source",
                )
            for control_name in control_by_column.get(column, []):
                if valid and numeric_value is not None:
                    control_totals[control_name] += numeric_value
                    control_valid_counts[control_name] += 1
                else:
                    control_invalid_counts[control_name] += 1

    serialized_profiles: dict[str, dict[str, int]] = {}
    for column, profile in profiles.items():
        serialized_profiles[column] = {
            "empty_count": profile["empty_count"],
            "nonempty_count": profile["nonempty_count"],
            "distinct_count": len(profile["distinct_values"]),
            "type_error_count": profile["type_error_count"],
            "formula_injection_count": profile["formula_injection_count"],
        }

    controls: list[dict[str, Any]] = []
    for control in spec["controls"]:
        name = control["name"]
        controls.append(
            {
                "name": name,
                "column": control["column"],
                "unit": spec["units"][control["column"]],
                "sign_convention": spec["signs"][control["column"]],
                "partial_total": format(control_totals[name], "f"),
                "valid_value_count": control_valid_counts[name],
                "invalid_value_count": control_invalid_counts[name],
                "complete": control_invalid_counts[name] == 0,
            }
        )

    exceptions.sort(
        key=lambda row: (
            int(row.get("row", 0)),
            str(row["code"]),
            str(row.get("column", "")),
            json.dumps(row.get("key", []), ensure_ascii=False),
        )
    )
    normalized_spec = {key: value for key, value in spec.items() if key != "lookup"}
    if spec["lookup"] is not None:
        normalized_spec["lookup"] = {
            key: (str(value) if isinstance(value, Path) else value)
            for key, value in spec["lookup"].items()
        }
    else:
        normalized_spec["lookup"] = None

    if _sha256_file(csv_path) != source_sha256:
        raise ProfileError(
            "SOURCE_CHANGED_DURING_READ", "Source CSV changed while it was profiled"
        )

    report: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": "BLOCKED" if exceptions else "RECONCILED",
        "source": {
            "path": str(csv_path),
            "sha256": source_sha256,
            "row_count": row_count,
            "valid_width_row_count": valid_width_count,
            "columns": header,
        },
        "contract": {
            "path": str(contract_path),
            "sha256": spec_sha256,
            "normalized": normalized_spec,
        },
        "lookup": lookup_receipt,
        "profile": serialized_profiles,
        "source_unique_key_count": len(source_keys),
        "controls": controls,
        "exception_count": len(exceptions),
        "exceptions": exceptions,
    }
    report["report_sha256"] = _canonical_sha256(report)
    return report


def _error_payload(exc: ProfileError) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "ERROR",
        "error": {"code": exc.code, "message": str(exc)},
    }


def main(argv: list[str] | None = None) -> int:
    parser = JsonArgumentParser(description=__doc__)
    parser.add_argument("csv_file", help="Source CSV path")
    parser.add_argument("--spec", required=True, help="Explicit JSON data contract")
    parser.add_argument("--output", type=Path, help="Atomic JSON output path")
    args = parser.parse_args(argv)
    try:
        report = profile_csv(args.csv_file, args.spec)
        _emit(report, args.output)
        return 0 if report["status"] == "RECONCILED" else 1
    except ProfileError as exc:
        _emit(_error_payload(exc), args.output)
        return 2
    except OSError as exc:
        error = ProfileError("IO_ERROR", str(exc))
        _emit(_error_payload(error), args.output)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
