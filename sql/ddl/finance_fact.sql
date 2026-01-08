-- sql/ddl/finance_fact.sql
--
-- Fact table for financial transactions
-- Grain: (transaction_date, department_id, account_code, funding_source_id)
--
-- Designed for BigQuery analytics workloads

CREATE TABLE IF NOT EXISTS finance.fact_financial_transactions (
  transaction_date DATE NOT NULL,
  fiscal_year STRING NOT NULL,
  department_id STRING NOT NULL,
  account_code STRING NOT NULL,
  funding_source_id STRING NOT NULL,
  amount NUMERIC NOT NULL,
  transaction_type STRING NOT NULL,  -- actual / accrual
  source_system STRING NOT NULL,
  created_at TIMESTAMP NOT NULL
)
PARTITION BY transaction_date
OPTIONS (
  description = "Immutable fact table containing normalized financial transactions for analytics"
);
