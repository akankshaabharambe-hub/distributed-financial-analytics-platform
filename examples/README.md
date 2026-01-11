# Examples — Safe End-to-End Pipeline Artifacts

This folder contains **sanitized, representative** inputs and outputs used to
demonstrate the pipeline locally without cloud credentials or sensitive data.

These files mirror how production pipelines move data through stages:

```text
sample_input.json  -> ingest.py     -> staged.json
staged.json        -> validate.py   -> (validated in-place / schema checks)
staged.json        -> transform.py  -> analytics_rows.json
analytics_rows.json -> BigQuery load (conceptual)
```

Note: Values and identifiers are anonymized and do not represent real institutional data.
Files
⸻
sample_input.json

Purpose: Representative raw input from upstream systems (ERP exports, planning tools, etc.).
Characteristics:
	•	Heterogeneous fields and formats
	•	Requires normalization and type coercion
	•	May include missing or inconsistent values in real deployments

Used by: data_pipeline/ingest.py

⸻

staged.json

Purpose: Normalized, schema-aligned records ready for deterministic transformation.
Characteristics:
	•	Types enforced (dates, amounts, enums)
	•	Required fields guaranteed
	•	Source system + ingestion timestamp preserved
	•	Still at record-level grain (not aggregated)

Used by: data_pipeline/validate.py and data_pipeline/transform.py

⸻

analytics_rows.json

Purpose: Analytics-ready outputs aligned to warehouse tables/views.
Characteristics:
	•	Curated schema for BI and conversational analytics
	•	Budget vs actual calculations
	•	Variance amount and variance percentage
	•	Ready to load into BigQuery (conceptual)

Produced by: data_pipeline/transform.py

⸻
How to Run Locally

From the repository root:
```text
python -m data_pipeline.ingest --input examples/sample_input.json --output examples/staged.json
python -m data_pipeline.validate --input examples/staged.json
python -m data_pipeline.transform --input examples/staged.json --output examples/analytics_rows.json
```

This demonstrates the pipeline behavior end-to-end without requiring BigQuery
credentials or access to real institutional datasets.
