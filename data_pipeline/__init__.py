"""
data_pipeline

Core data pipeline package for the Distributed Financial Analytics Platform.

This package contains modular components responsible for:
- ingesting raw financial data
- validating schema and data quality
- transforming records into analytics-ready fact rows
- loading curated outputs into BigQuery (or compatible warehouses)

Each module is designed to be independently testable and composable
within batch-oriented production workflows.
"""

from data_pipeline.ingest import ingest_records
from data_pipeline.validate import validate_records
from data_pipeline.transform import transform_records

__all__ = [
    "ingest_records",
    "validate_records",
    "transform_records",
]
