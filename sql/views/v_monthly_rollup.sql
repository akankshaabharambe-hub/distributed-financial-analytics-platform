-- sql/views/v_monthly_rollup.sql
--
-- Monthly rollup view for departmental financial analysis
-- Used by dashboards and forecasting pipelines

CREATE OR REPLACE VIEW finance.v_monthly_rollup AS
SELECT
  DATE_TRUNC(transaction_date, MONTH) AS month,
  fiscal_year,
  department_id,
  account_code,
  SUM(amount) AS total_amount,
  COUNT(*) AS transaction_count
FROM finance.fact_financial_transactions
WHERE transaction_type = 'actual'
GROUP BY
  month,
  fiscal_year,
  department_id,
  account_code
ORDER BY
  month,
  department_id,
  account_code;
