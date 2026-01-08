"""
data_pipeline/transform.py

Transformation layer for staged financial records.

Responsibilities:
- Convert staged records into analytics-ready rows
- Enforce a clear grain aligned with warehouse schemas
- Derive fields needed for reporting and forecasting
- Produce deterministic outputs suitable for BigQuery loading

Input:
- JSON file with shape: {"records": [ ... validated staged records ... ]}

Output:
- JSON file with shape: {"rows": [ ... analytics-ready fact rows ... ]}
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List


# -----------------------------
# Transform helpers
# -----------------------------

def _read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Input not found: {path}")
    raw = path.read_text(encoding="utf-8").strip()
    if raw == "":
        raise ValueError(f"Input is empty: {path}")
    return json.loads(raw)


def _derive_fiscal_year(tx_date: str) -> str:
    """
    Example fiscal year rule:
    - Fiscal year starts July 1
    - FY2025 covers 2024-07-01 through 2025-06-30
    """
    dt = datetime.strptime(tx_date, "%Y-%m-%d").date()
    return f"FY{dt.year + 1}" if dt.month >= 7 else f"FY{dt.year}"


def _normalize_fact_row(rec: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert a staged record into a warehouse fact row.

    Grain:
    - (transaction_date, department_id, account_code, funding_source_id)
    """
    fiscal_year = _derive_fiscal_year(rec["transaction_date"])

    return {
        "transaction_date": rec["transaction_date"],
        "fiscal_year": fiscal_year,
        "department_id": rec["department_id"],
        "account_code": rec["account_code"],
        "funding_source_id": rec["funding_source_id"],
        "amount": rec["amount"],
        "transaction_type": rec["transaction_type"],
        "source_system": rec["source_system"],
        "created_at": rec["created_at"],
    }


def transform_records(records: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for rec in records:
        rows.append(_normalize_fact_row(rec))
    return rows


# -----------------------------
# CLI
# -----------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Transform staged records into analytics-ready rows.")
    parser.add_argument("--input", required=True, help="Path to staged JSON (e.g., examples/staged.json)")
    parser.add_argument("--output", required=True, help="Path to write transformed rows JSON")
    args = parser.parse_args()

    payload = _read_json(Path(args.input))

    if "records" not in payload or not isinstance(payload["records"], list):
        raise ValueError("Expected input JSON with key 'records' containing a list")

    rows = transform_records(payload["records"])

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps({"rows": rows}, indent=2), encoding="utf-8")

    print(f"[transform] rows_written={len(rows)} output={out_path}")


if __name__ == "__main__":
    main()
