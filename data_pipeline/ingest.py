"""
data_pipeline/ingest.py

Ingestion layer for the Distributed Financial Analytics Platform.

Goal:
- Accept heterogeneous inputs (this repo uses JSON examples)
- Standardize into a staging contract that downstream validation/transforms can rely on
- Write a deterministic staged artifact for reproducible pipelines

Notes:
- This repo is a representative subset; real connectors (APIs/PDF scraping/etc.) are excluded.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


# -----------------------------
# Helpers (pure functions)
# -----------------------------

_DATE_PATTERNS: Tuple[str, ...] = (
    r"^\d{4}-\d{2}-\d{2}$",  # YYYY-MM-DD
    r"^\d{2}/\d{2}/\d{4}$",  # MM/DD/YYYY
)


def _parse_date(value: str) -> date:
    value = value.strip()
    if re.match(_DATE_PATTERNS[0], value):
        return datetime.strptime(value, "%Y-%m-%d").date()
    if re.match(_DATE_PATTERNS[1], value):
        return datetime.strptime(value, "%m/%d/%Y").date()
    raise ValueError(f"Unsupported date format: {value!r} (expected YYYY-MM-DD or MM/DD/YYYY)")


def _to_upper_slug(value: str) -> str:
    # Normalize identifiers (department, funding source, etc.)
    # Example: "Computer Science " -> "COMPUTER_SCIENCE"
    cleaned = re.sub(r"[^A-Za-z0-9]+", "_", value.strip())
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    return cleaned.upper()


def _parse_amount(value: Any) -> float:
    """
    Parse amounts from numbers or currency-like strings.
    Examples: 1200, "1200", "$1,200.50", "1,200.50"
    """
    if isinstance(value, (int, float)):
        return float(value)

    if not isinstance(value, str):
        raise ValueError(f"Amount must be numeric or string, got {type(value).__name__}")

    s = value.strip()
    s = s.replace("$", "").replace(",", "")
    if s == "":
        raise ValueError("Amount is empty")
    return float(s)


def _utc_now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


# -----------------------------
# Staging contract
# -----------------------------

@dataclass(frozen=True)
class StagedTransaction:
    """
    Staging contract produced by ingestion.

    Downstream guarantees:
    - transaction_date is ISO YYYY-MM-DD
    - normalized IDs for department/account/funding_source
    - amount is numeric (float)
    - created_at is an ISO UTC timestamp
    """
    transaction_date: str
    department_id: str
    account_code: str
    funding_source_id: str
    amount: float
    transaction_type: str  # e.g., "actual" / "accrual"
    source_system: str     # e.g., "csv_upload", "erp_export"
    created_at: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "transaction_date": self.transaction_date,
            "department_id": self.department_id,
            "account_code": self.account_code,
            "funding_source_id": self.funding_source_id,
            "amount": self.amount,
            "transaction_type": self.transaction_type,
            "source_system": self.source_system,
            "created_at": self.created_at,
        }


# -----------------------------
# Ingestion logic
# -----------------------------

def _load_json_records(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Input not found: {path}")

    raw = path.read_text(encoding="utf-8").strip()
    if raw == "":
        raise ValueError(f"Input is empty: {path}")

    data = json.loads(raw)

    # Allow either a list of records or {"records":[...]}
    if isinstance(data, dict) and "records" in data:
        data = data["records"]

    if not isinstance(data, list):
        raise ValueError("Input JSON must be a list of records or an object with key 'records'")

    out: List[Dict[str, Any]] = []
    for i, item in enumerate(data):
        if not isinstance(item, dict):
            raise ValueError(f"Record at index {i} is not an object")
        out.append(item)
    return out


def _standardize_record(rec: Dict[str, Any]) -> StagedTransaction:
    """
    Map a raw record into the staging contract.

    Expected (representative) raw fields:
    - date: "YYYY-MM-DD" or "MM/DD/YYYY"
    - department: string
    - account: string
    - funding_source: string
    - amount: number or string like "$1,200.50"
    - transaction_type: optional, defaults to "actual"
    - source_system: optional, defaults to "unknown"
    """
    created_at = _utc_now_iso()

    # Defensive parsing with helpful errors
    if "date" not in rec:
        raise KeyError("Missing required field: date")
    if "department" not in rec:
        raise KeyError("Missing required field: department")
    if "account" not in rec:
        raise KeyError("Missing required field: account")
    if "funding_source" not in rec:
        raise KeyError("Missing required field: funding_source")
    if "amount" not in rec:
        raise KeyError("Missing required field: amount")

    tx_date = _parse_date(str(rec["date"]))
    department_id = _to_upper_slug(str(rec["department"]))
    account_code = _to_upper_slug(str(rec["account"]))
    funding_source_id = _to_upper_slug(str(rec["funding_source"]))
    amount = _parse_amount(rec["amount"])

    transaction_type = str(rec.get("transaction_type", "actual")).strip().lower()
    if transaction_type not in {"actual", "accrual"}:
        # Keep contract strict; unknown types should be handled upstream
        raise ValueError(f"Unsupported transaction_type: {transaction_type!r} (expected 'actual' or 'accrual')")

    source_system = str(rec.get("source_system", "unknown")).strip().lower() or "unknown"

    return StagedTransaction(
        transaction_date=tx_date.isoformat(),
        department_id=department_id,
        account_code=account_code,
        funding_source_id=funding_source_id,
        amount=amount,
        transaction_type=transaction_type,
        source_system=source_system,
        created_at=created_at,
    )


def ingest(input_path: Path) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Returns (staged_records, metadata).
    """
    raw_records = _load_json_records(input_path)

    staged: List[Dict[str, Any]] = []
    errors: List[Dict[str, Any]] = []

    for idx, rec in enumerate(raw_records):
        try:
            staged_tx = _standardize_record(rec)
            staged.append(staged_tx.to_dict())
        except Exception as e:
            errors.append(
                {
                    "index": idx,
                    "error": type(e).__name__,
                    "message": str(e),
                    "raw_record": rec,
                }
            )

    metadata = {
        "input_file": str(input_path),
        "record_count": len(raw_records),
        "staged_count": len(staged),
        "error_count": len(errors),
        "generated_at": _utc_now_iso(),
        "errors": errors[:25],  # avoid huge logs; keep a preview
    }
    return staged, metadata


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest raw financial records into a staging contract.")
    parser.add_argument("--input", required=True, help="Path to input JSON (list of records or {records:[...]})")
    parser.add_argument("--output", required=True, help="Path to write staged JSON output")
    parser.add_argument("--meta", default="", help="Optional path to write ingestion metadata (errors + counts)")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    meta_path = Path(args.meta) if args.meta else None

    staged, meta = ingest(input_path)

    _write_json(output_path, {"records": staged})
    if meta_path:
        _write_json(meta_path, meta)

    # CI-friendly summary
    print(f"[ingest] input={meta['record_count']} staged={meta['staged_count']} errors={meta['error_count']}")
    if meta["error_count"] > 0:
        print("[ingest] warning: some records failed ingestion (see --meta for details)")


if __name__ == "__main__":
    main()
