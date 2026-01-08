# UI Integration — Financial Analytics & Budget Forecasting

This document describes how the analytics platform integrates with a
web-based reporting UI to deliver financial insights to analysts,
administrators, and decision-makers.

The UI is treated as a **consumer of curated data**, not a place for
business logic or metric computation.

---

## Design Principles

- **Warehouse-driven metrics**: all calculations live in SQL
- **Thin UI layer**: UI focuses on visualization and interaction
- **Consistency across consumers**: dashboards and chatbot use the same views
- **Filter-first experience**: users slice data without redefining logic

---

## High-Level Flow

```text
User (UI)
  |
  v
Dashboard Filters
  - Department
  - Fiscal Year
  - Account Category
  |
  v
Analytics API / Query Layer
  |
  v
BigQuery Views
  - v_budget_vs_actual
  - v_department_rollups
  |
  v
Rendered Charts & Tables
```
---
## Core Dashboard Views

1) Budget vs Actual Overview

Purpose
	•	Compare approved budgets against actual spend
	•	Identify over- and under-spending at a glance

Primary Metrics
	•	Total Budget
	•	Total Actual
	•	Variance Amount
	•	Variance Percentage

Typical Visualizations
	•	Bar charts (budget vs actual)
	•	Variance heatmaps by department
	•	KPI cards for fiscal summaries

---

2) Department Spend Drilldown

Purpose
	•	Analyze spending patterns within a department

Dimensions
	•	Account category (OPEX / CAPEX)
	•	Funding source
	•	Time (month, quarter)

Visualizations
	•	Time-series line charts
	•	Stacked bars by account category
	•	Tabular detail views for exports

---

3) Trend & Forecast Readiness Views

Purpose
	•	Provide historical context for forecasting models
	•	Support planning and scenario analysis

Data Characteristics
	•	Immutable historical actuals
	•	Explicit budget baselines
	•	Time-windowed aggregations

Forecasting logic is intentionally out of scope for the UI and handled
by downstream systems.

---

## Filter & Parameter Contract

The UI passes parameters to the analytics layer in a structured form:
```text
{
  "department_id": "PLANNING_BUDGET",
  "fiscal_year": "FY2025",
  "account_category": "OPEX"
}
```
These parameters are applied directly to predefined views rather than
dynamically generated SQL.

---

## Why This Design Works
	•	Prevents metric drift between dashboards and chatbots
	•	Keeps the UI simple and maintainable
	•	Allows backend and analytics layers to evolve independently
	•	Supports role-based access control at the data layer

---

## Scope & Constraints

Excluded from this repository:
	•	UI source code and styling
	•	Authentication and authorization logic
	•	Deployment and hosting configuration

Included here:
	•	Integration patterns
	•	Filter contracts
	•	Dashboard design assumptions used in production-style systems

---

## Summary

The UI layer is designed as a consumer of trusted analytics outputs.
By keeping business logic centralized in SQL and the warehouse, the platform
ensures consistency, scalability, and long-term maintainability across all
user-facing surfaces.
