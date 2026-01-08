# System Architecture — Distributed Financial Analytics & Budget Forecasting Platform

This document describes the high-level architecture of the platform and how data moves from
institutional sources into analytics-ready BigQuery tables, then to downstream consumers
(dashboards + conversational analytics).

This repo contains a **representative subset** of the system. Sensitive datasets, credentials,
and institution-specific configurations are intentionally excluded.

---

## Goals

- **Reliability first**: schema contracts, validation, and deterministic transforms
- **Warehouse-centric analytics**: BigQuery is the system of record for curated tables
- **Separation of concerns**: ingestion, validation, transformation, and serving are isolated
- **Extensible design**: add new sources/metrics without refactoring the whole pipeline
- **Consumer-friendly outputs**: stable SQL views + clean API/JSON interfaces for UI/chatbot

---

## High-Level Flow

```text
        +--------------------+
        |  Data Sources      |
        |  (CSV, PDF, APIs)  |
        +---------+----------+
                  |
                  v
        +--------------------+
        | Ingestion Layer    |
        | (standardize IO)   |
        +---------+----------+
                  |
                  v
        +--------------------+
        | Validation Layer   |
        | (schema contracts) |
        +---------+----------+
                  |
                  v
        +--------------------+
        | Transform Layer    |
        | (normalize + rollup|
        |  business logic)   |
        +---------+----------+
                  |
                  v
        +--------------------+
        | BigQuery Warehouse |
        |  - fact tables     |
        |  - dims            |
        |  - views           |
        +----+-----------+---+
             |           |
             v           v
   +----------------+  +----------------------+
   | Dashboards / UI|  | Dialogflow / Chatbot |
   | (reporting)    |  | (NLQ over metrics)   |
   +----------------+  +----------------------+
```

---

## Components

1) Ingestion (data_pipeline/ingest.py)

Purpose: ingest heterogeneous inputs and convert them into a consistent staging format.

Responsibilities:
	•	Input parsing (CSV/JSON examples; other formats documented but excluded)
	•	Minimal standardization (date parsing, currency normalization)
	•	Write a staged JSON artifact for validation

Output:
	•	examples/staged.json (representative staged payload)

⸻

2) Validation (data_pipeline/validate.py)

Purpose: enforce data contracts before transformation.

Responsibilities:
	•	Schema-driven validation (required fields, types, ranges)
	•	Error reporting that’s actionable for upstream fixes
	•	Reject malformed records early (fail fast)

Output:
	•	Validation report (stdout) + deterministic exit codes for CI integration

⸻

3) Transformation (data_pipeline/transform.py)

Purpose: transform staged records into analytics-ready rows matching warehouse schemas.

Responsibilities:
	•	Deterministic transformations (id normalization, mapping, derived fields)
	•	Consistent grain selection (e.g., daily department-level transactions)
	•	Produce outputs that directly map to BigQuery table schemas

Output:
	•	examples/analytics_rows.json

⸻

4) Warehouse Layer (BigQuery) (sql/)

Purpose: define stable storage + metrics layer.

Included in this repo:
	•	DDL for representative tables (fact + dims)
	•	Views for reporting use cases (budget vs actual, rollups)

Not included:
	•	Real project IDs, service accounts, scheduled queries, IAM configuration

⸻

5) Consumer Interfaces

Dashboards / UI
	•	UI is treated as a consumer of stable SQL views and/or API outputs
	•	This repo documents integration contracts (payload shapes, expected filters)

See: docs/ui-integration.md

Dialogflow
	•	Dialogflow is treated as a consumer of curated metrics with intent-based routing
	•	This repo documents the agent design and fulfillment interface (no credentials)

See: docs/dialogflow-integration.md

⸻

## Data Contracts

The platform is schema-first:
	•	ingestion standardizes raw inputs
	•	validation enforces contracts
	•	transformations emit warehouse-ready records

A representative logical model is documented here:
	•	docs/data-model.md

⸻

## Non-Goals / Constraints

This repo intentionally excludes:
	•	Real institutional datasets and identifiers
	•	BigQuery project configuration and service accounts
	•	Deployed Dialogflow agents and fulfillment services
	•	Internal UI deployment configuration

The included code and docs focus on:
	•	pipeline structure and contracts
	•	validation and transformation logic
	•	BigQuery schema + query patterns
	•	integration boundaries used in production-style systems

⸻

## How to Run (Locally)

This repo supports local execution using safe sample inputs:
python -m data_pipeline.ingest --input examples/sample_input.json --output examples/staged.json
python -m data_pipeline.validate --input examples/staged.json
python -m data_pipeline.transform --input examples/staged.json --output examples/analytics_rows.json

This demonstrates the pipeline behavior end-to-end without cloud credentials.
