"""
data_pipeline/load_bigquery.py

Warehouse loading interface for analytics-ready financial data.

Design goals:
- Provide a clean boundary between transformation logic and warehouse I/O
- Support local execution without credentials via DRY-RUN mode
- Validate row shape and emit CI-friendly summaries

This repository intentionally excludes:
- Service account credentials
- Production BigQuery project configuration
- Deployed orchestration / scheduling setup
"""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple


REQUIRED_KEYS: Tuple[str, ...] = (
    "transaction_date",
    "fiscal_year",
    "department_id",
    "account_code",
    "funding_source_id",
    "amount",
    "transaction_type",
    "source_system",
    "created_at",
)


@dataclass(frozen=True)
class LoadConfig:
    project_id: str
    dataset: str
    table: str
    dry_run: bool = True

    @staticmethod
    def from_env(
        *,
        project_var: str = "BQ_PROJECT_ID",
        dataset_var: str = "BQ_DATASET",
        table_var: str = "BQ_TABLE",
        default_project: str = "demo_project",
        default_dataset: str = "finance",
        default_table: str = "fact_financial_transactions",
    ) -> "LoadConfig":
        """
        Allow config via environment variables to mirror production behavior
        while remaining runnable locally with safe defaults.
        """
        project_id = os.getenv(project_var, default_project).strip()
        dataset = os.getenv(dataset_var, default_dataset).strip()
        table = os.getenv(table_var, default_table).strip()

        if not project_id or not dataset or not table:
            raise ValueError(
                f"Invalid BigQuery config. Ensure {project_var}, {dataset_var}, {table_var} are set (or use defaults)."
            )

        return LoadConfig(project_id=project_id, dataset=dataset, table=table, dry_run=True)


class BigQueryLoader:
    """
    Thin abstraction over BigQuery loading logic.

    In production, this class would:
    - authenticate using a service account
    - enforce table schemas (BigQuery schema / DDL)
    - perform idempotent loads or MERGE operations
    """

    def __init__(self, config: LoadConfig) -> None:
        self.config = config

    def load_rows(self, rows: Sequence[Dict[str, Any]]) -> None:
        """
        Load analytics-ready rows into the warehouse.

        Args:
            rows: List of validated, transformed fact records
        """
        if not rows:
            raise ValueError("No rows provided for warehouse load")

        # Lightweight contract validation (fast + high signal)
        bad = self._validate_row_shape(rows)
        if bad:
            # Show only a few to avoid log spam
            sample = bad[:5]
            raise ValueError(
                "Row shape validation failed. Missing required keys in some rows. "
                f"First failures: {sample}"
            )

        if self.config.dry_run:
            self._log_dry_run(rows)
            return

        # Intentionally excluded from this public repo
        raise NotImplementedError(
            "Production BigQuery loading is not enabled in this repository. "
            "Use --dry-run (default) to validate payloads locally."
        )

    def _validate_row_shape(self, rows: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
        required: Set[str] = set(REQUIRED_KEYS)
        failures: List[Dict[str, Any]] = []

        for i, r in enumerate(rows):
            if not isinstance(r, dict):
                failures.append({"index": i, "error": "row is not an object"})
                continue
            missing = sorted(required - set(r.keys()))
            if missing:
                failures.append({"index": i, "missing_keys": missing})
        return failures

    def _log_dry_run(self, rows: Sequence[Dict[str, Any]]) -> None:
        target = f"{self.config.project_id}.{self.config.dataset}.{self.config.table}"
        print("[load_bigquery] DRY-RUN: no network calls will be made")
        print(f"[load_bigquery] target={target}")
        print(f"[load_bigquery] row_count={len(rows)}")

        # Basic schema inspection (what reviewers like seeing)
        keys = sorted(rows[0].keys())
        print(f"[load_bigquery] sample_keys={keys}")

        print("[load_bigquery] sample_row=")
        print(json.dumps(rows[0], indent=2, sort_keys=True))


def _read_rows(input_path: Path) -> List[Dict[str, Any]]:
    """
    Accept either:
    - {"rows": [...]}  (from transform.py)
    - a plain list [...]
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input not found: {input_path}")

    payload = json.loads(input_path.read_text(encoding="utf-8"))
    if isinstance(payload, dict) and "rows" in payload:
        rows = payload["rows"]
    else:
        rows = payload

    if not isinstance(rows, list):
        raise ValueError("Expected input JSON to be a list of rows or an object with key 'rows'")
    for i, r in enumerate(rows):
        if not isinstance(r, dict):
            raise ValueError(f"Row at index {i} is not an object")
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Load analytics-ready rows into BigQuery (dry-run by default).")
    parser.add_argument(
        "--input",
        required=True,
        help="Path to analytics rows JSON (e.g., examples/analytics_rows.json)",
    )
    parser.add_argument("--project_id", default=os.getenv("BQ_PROJECT_ID", "demo_project"))
    parser.add_argument("--dataset", default=os.getenv("BQ_DATASET", "finance"))
    parser.add_argument("--table", default=os.getenv("BQ_TABLE", "fact_financial_transactions"))
    parser.add_argument(
        "--dry_run",
        action="store_true",
        help="Validate and print load summary without making network calls (recommended).",
    )
    args = parser.parse_args()

    rows = _read_rows(Path(args.input))
    config = LoadConfig(
        project_id=str(args.project_id).strip(),
        dataset=str(args.dataset).strip(),
        table=str(args.table).strip(),
        dry_run=True if args.dry_run else True,  # always dry-run in this public repo
    )

    loader = BigQueryLoader(config)
    loader.load_rows(rows)


if __name__ == "__main__":
    main()
