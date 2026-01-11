"""
load_bigquery.py

Warehouse loading interface for analytics-ready financial data.

This module demonstrates how transformed fact rows would be
loaded into BigQuery using a schema-first, idempotent approach.

Actual credentials and production project configuration are
intentionally excluded.
"""

from typing import List, Dict


class BigQueryLoader:
    """
    Thin abstraction over BigQuery loading logic.

    In production, this class would:
    - authenticate using a service account
    - enforce table schemas
    - perform idempotent loads or MERGE operations
    """

    def __init__(
        self,
        project_id: str,
        dataset: str,
        table: str,
        dry_run: bool = True,
    ) -> None:
        self.project_id = project_id
        self.dataset = dataset
        self.table = table
        self.dry_run = dry_run

    def load_rows(self, rows: List[Dict]) -> None:
        """
        Load analytics-ready rows into the warehouse.

        Args:
            rows: List of validated, transformed fact records
        """
        if not rows:
            raise ValueError("No rows provided for warehouse load")

        if self.dry_run:
            self._log_dry_run(rows)
            return

        # Placeholder for real BigQuery load logic
        # e.g. load_table_from_json or MERGE-based ingestion
        raise NotImplementedError(
            "Production BigQuery loading is not enabled in this repository"
        )

    def _log_dry_run(self, rows: List[Dict]) -> None:
        print("BigQuery load (dry-run)")
        print(f"Target: {self.project_id}.{self.dataset}.{self.table}")
        print(f"Row count: {len(rows)}")

        # Print a single representative record for inspection
        print("Sample row:")
        print(rows[0])
