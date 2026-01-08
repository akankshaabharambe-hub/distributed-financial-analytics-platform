"""
data_pipeline/validate.py

Validation layer for staged financial records.

Responsibilities:
- Enforce schema contracts (required fields + types)
- Apply basic data quality checks (ranges, allowed values)
- Produce CI-friendly output and exit codes

Input:
- JSON file with shape: {"records": [ ... staged transactions ... ]}

Typical usage:
python -m data_pipeline.validate --input examples/staged.json
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


ALLOWED_TRANSACTION_TYPES = {"actual", "accrual"}


@dataclass(frozen=True)
class ValidationError:
    index: int
    field: str
    message: str
    record_preview: Dict[str, Any]


def _read_json(path: Path) -> Any:
    if not path.exists():
        raise FileNotFoundError(f"Input not found: {path}")
    raw = path.read_text(encoding="utf-8").strip()
    if raw == "":
        raise ValueError(f"Input is empty: {path}")
    return json.loads(raw)


def _is_iso_date(value: str) -> bool:
    try:
        # YYYY-MM-DD
        datetime.strptime(value, "%Y-%m-%d")
        return True
    except Exception:
        return False


def _get_records(payload: Any) -> List[Dict[str, Any]]:
    if isinstance(payload, dict) and "records" in payload:
        records = payload["records"]
    else:
        records = payload

    if not isinstance(records, list):
        raise ValueError("Expected JSON with key 'records' (list) or a list of records.")

    out: List[Dict[str, Any]] = []
    for i, r in enumerate(records):
        if not isinstance(r, dict):
            raise ValueError(f"Record at index {i} is not an object.")
        out.append(r)
    return out


def _require_str(rec: Dict[str, Any], key: str, idx: int, errors: List[ValidationError]) -> Optional[str]:
    if key not in rec:
        errors.append(ValidationError(idx, key, "missing required field", _preview(rec)))
        return None
    v = rec[key]
    if not isinstance(v, str) or v.strip() == "":
        errors.append(ValidationError(idx, key, "must be a non-empty string", _preview(rec)))
        return None
    return v.strip()


def _require_number(rec: Dict[str, Any], key: str, idx: int, errors: List[ValidationError]) -> Optional[float]:
    if key not in rec:
        errors.append(ValidationError(idx, key, "missing required field", _preview(rec)))
        return None
    v = rec[key]
    if not isinstance(v, (int, float)):
        errors.append(ValidationError(idx, key, "must be a number", _preview(rec)))
        return None
    return float(v)


def _preview(rec: Dict[str, Any]) -> Dict[str, Any]:
    # Keep previews small to avoid noisy logs
    keep = ["transaction_date", "department_id", "account_code", "funding_source_id", "amount", "transaction_type"]
    return {k: rec.get(k) for k in keep}


def validate_records(records: List[Dict[str, Any]]) -> Tuple[bool, List[ValidationError]]:
    errors: List[ValidationError] = []

    for idx, rec in enumerate(records):
        # Required fields
        tx_date = _require_str(rec, "transaction_date", idx, errors)
        dept = _require_str(rec, "department_id", idx, errors)
        acct = _require_str(rec, "account_code", idx, errors)
        fund = _require_str(rec, "funding_source_id", idx, errors)
        tx_type = _require_str(rec, "transaction_type", idx, errors)
        amount = _require_number(rec, "amount", idx, errors)
        _ = _require_str(rec, "created_at", idx, errors)
        _ = _require_str(rec, "source_system", idx, errors)

        # Field-level checks (only if present)
        if tx_date and not _is_iso_date(tx_date):
            errors.append(ValidationError(idx, "transaction_date", "must be ISO format YYYY-MM-DD", _preview(rec)))

        if tx_type and tx_type not in ALLOWED_TRANSACTION_TYPES:
            errors.append(
                ValidationError(
                    idx,
                    "transaction_type",
                    f"must be one of {sorted(ALLOWED_TRANSACTION_TYPES)}",
                    _preview(rec),
                )
            )

        if amount is not None:
            # Basic sanity checks; amounts can be negative depending on accounting (refunds),
            # so we only guard against absurd values.
            if abs(amount) > 1_000_000_000:
                errors.append(ValidationError(idx, "amount", "amount magnitude is unexpectedly large", _preview(rec)))

        # Identifier expectations: uppercase + underscores (from ingest normalization)
        for field_name, value in [("department_id", dept), ("account_code", acct), ("funding_source_id", fund)]:
            if value and (value != value.upper() or " " in value):
                errors.append(
                    ValidationError(
                        idx,
                        field_name,
                        "identifier should be normalized (uppercase with underscores)",
                        _preview(rec),
                    )
                )

    return (len(errors) == 0), errors


def _print_report(ok: bool, errors: List[ValidationError], *, max_show: int) -> None:
    if ok:
        print("[validate] OK: all records passed validation")
        return

    print(f"[validate] FAILED: {len(errors)} issue(s) found")
    for e in errors[:max_show]:
        print(f" - index={e.index} field={e.field} error={e.message} preview={e.record_preview}")

    if len(errors) > max_show:
        print(f"[validate] ... {len(errors) - max_show} more not shown")


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate staged financial records.")
    parser.add_argument("--input", required=True, help="Path to staged JSON (e.g., examples/staged.json)")
    parser.add_argument("--max_show", type=int, default=20, help="Max number of errors to print")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with non-zero code if validation fails (recommended for CI)",
    )
    args = parser.parse_args()

    payload = _read_json(Path(args.input))
    records = _get_records(payload)

    ok, errors = validate_records(records)
    _print_report(ok, errors, max_show=args.max_show)

    if args.strict and not ok:
        sys.exit(2)


if __name__ == "__main__":
    main()
