# Dialogflow Integration — Conversational Financial Analytics

This document describes how the analytics platform integrates with Dialogflow
to enable **natural-language access to financial metrics** such as budgets,
actuals, and variances.

The goal is to allow non-technical users to query institutional financial data
without writing SQL or navigating dashboards.

---

## Role of Dialogflow in the System

Dialogflow acts as a **thin conversational layer** on top of curated analytics
views in BigQuery.

Key principles:
- Dialogflow does **not** compute metrics
- Business logic lives in SQL and the warehouse
- The chatbot translates user intent into structured queries

---

## High-Level Flow

```text
User (NL Query)
      |
      v
Dialogflow Agent
  - Intent detection
  - Entity extraction
      |
      v
Fulfillment Layer
  - Parameterized query construction
  - Calls analytics views
      |
      v
BigQuery Views
  - budget vs actual
  - rollups
      |
      v
Formatted Response
  - Numbers
  - Time ranges
  - Variance summaries
```
---
## Example User Queries
	•	“What is the budget vs actual for Planning & Budget this year?”
	•	“How much did Research Computing spend last quarter?”
	•	“Which departments are over budget in FY2025?”

These queries map to predefined intents rather than free-form SQL.

⸻

## Intent Design (Representative)

Intent: budget_vs_actual.department

## Training phrases
	•	“Budget vs actual for {department}”
	•	“How much did {department} spend this year?”
	•	“Is {department} over budget?”

## Entities
	•	department → maps to department_id
	•	fiscal_year → optional, defaults to current FY

⸻

## Fulfillment Contract

Dialogflow fulfillment calls a backend service (or Cloud Function)
with a structured payload:
```text
{
  "intent": "budget_vs_actual.department",
  "parameters": {
    "department_id": "PLANNING_BUDGET",
    "fiscal_year": "FY2025"
  }
}
```
The fulfillment layer:
	•	Validates parameters
	•	Executes parameterized queries against BigQuery views
	•	Formats numeric results into conversational responses

⸻

Example Fulfillment Output
```text
{
  "department": "Planning & Budget",
  "fiscal_year": "FY2025",
  "total_budget": 1250000,
  "total_actual": 1314500,
  "variance_amount": 64500,
  "status": "Over budget"
}
```

## Why This Design Scales
	•	Business logic stays centralized in SQL
	•	New intents reuse existing analytics views
	•	Schema changes are isolated from the chatbot
	•	Supports dashboards and chat using the same metrics

⸻

## Scope & Constraints

Excluded from this repository:
	•	Deployed Dialogflow agents
	•	Fulfillment services and credentials
	•	Production project IDs and IAM configuration

Included here:
	•	Intent design patterns
	•	Parameter contracts
	•	Integration boundaries used in production-style systems

⸻

## Summary

Dialogflow is treated as an interface, not a compute layer.
This keeps conversational analytics consistent with dashboards,
prevents metric drift, and simplifies long-term maintenance.
