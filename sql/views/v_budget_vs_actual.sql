-- sql/views/v_budget_vs_actual.sql
--
-- Budget vs actual comparison view
-- Used by dashboards and conversational analytics

CREATE OR REPLACE VIEW finance.v_budget_vs_actual AS
SELECT
  f.fiscal_year,
  f.department_id,
  d.department_name,
  f.account_code,
  SUM(CASE WHEN f.transaction_type = 'actual' THEN f.amount ELSE 0 END) AS total_actual,
  b.allocated_amount AS total_budget,
  SUM(CASE WHEN f.transaction_type = 'actual' THEN f.amount ELSE 0 END) - b.allocated_amount
    AS variance_amount,
  SAFE_DIVIDE(
    SUM(CASE WHEN f.transaction_type = 'actual' THEN f.amount ELSE 0 END) - b.allocated_amount,
    b.allocated_amount
  ) AS variance_percentage
FROM finance.fact_financial_transactions f
LEFT JOIN finance.fact_budget_allocations b
  ON f.fiscal_year = b.fiscal_year
 AND f.department_id = b.department_id
 AND f.account_code = b.account_code
LEFT JOIN finance.dim_department d
  ON f.department_id = d.department_id
GROUP BY
  f.fiscal_year,
  f.department_id,
  d.department_name,
  f.account_code,
  b.allocated_amount;
