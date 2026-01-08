# Data Model — Distributed Financial Analytics Platform

This document describes the logical data model used by the analytics platform.
The model is designed for **institutional financial reporting, forecasting, and variance analysis**
with BigQuery as the system of record.

The schemas shown here are **representative** and intentionally anonymized.

---

## Design Principles

- **Fact / dimension modeling** for analytical workloads
- **Explicit grains** to prevent aggregation ambiguity
- **Time-aware schemas** for budget vs actual comparisons
- **Warehouse-first metrics** (SQL over BI logic)
- **Immutable facts**, derived views for flexibility

---

## Core Tables

### 1) `fact_financial_transactions`

**Grain:**  
One record per *(date × department × account × funding_source)*

| Column Name        | Type      | Description |
|--------------------|-----------|-------------|
| transaction_date   | DATE      | Date of transaction |
| department_id      | STRING    | Owning department |
| account_code       | STRING    | Financial account |
| funding_source_id  | STRING    | Funding category |
| amount             | NUMERIC   | Transaction amount |
| transaction_type   | STRING    | actual / accrual |
| created_at         | TIMESTAMP | Ingestion timestamp |

**Notes**
- Source of truth for actual spend
- Append-only, no updates in place
- Partitioned by `transaction_date`

---

### 2) `fact_budget_allocations`

**Grain:**  
One record per *(fiscal_year × department × account)*

| Column Name       | Type    | Description |
|-------------------|---------|-------------|
| fiscal_year       | STRING  | Fiscal year (e.g. FY2025) |
| department_id     | STRING  | Department |
| account_code      | STRING  | Financial account |
| allocated_amount  | NUMERIC | Approved budget |

---

## Dimension Tables

### `dim_department`
| Column | Type | Description |
|------|------|-------------|
| department_id | STRING | Primary key |
| department_name | STRING | Display name |
| cost_center | STRING | Cost center mapping |

---

### `dim_account`
| Column | Type | Description |
|-------|------|-------------|
| account_code | STRING | Primary key |
| account_name | STRING | Human-readable name |
| account_category | STRING | OPEX / CAPEX |

---

### `dim_funding_source`
| Column | Type | Description |
|------|------|-------------|
| funding_source_id | STRING | Primary key |
| source_type | STRING | Grant / Internal / External |

---

## Analytical Views

### `vw_budget_vs_actual`

Joins budgets and actuals to support variance analysis.

**Metrics:**
- total_actual
- total_budget
- variance_amount
- variance_percentage

Used by:
- dashboards
- conversational queries
- exports to downstream systems

---

### `vw_department_rollups`

Aggregates spend by:
- department
- fiscal period
- account category

Optimized for UI filters and summary views.

---

## Forecasting Readiness

The model supports forecasting by:
- isolating historical actuals
- keeping budgets explicit and immutable
- enabling time-windowed aggregations

Forecasting logic is intentionally **out of scope** for this repo and handled downstream.

---

## Why This Model Works in Practice

- Prevents metric drift by enforcing grains
- Keeps business logic centralized in SQL
- Scales naturally with BigQuery partitioning
- Supports dashboards and conversational analytics equally well

---

## Scope & Constraints

Excluded from this repo:
- Real institution identifiers
- Production BigQuery datasets
- Cost controls, quotas, and scheduling configs

Included here:
- Logical schemas
- Analytics-ready patterns
- Design decisions used in production systems
