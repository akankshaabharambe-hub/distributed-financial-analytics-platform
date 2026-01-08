-- sql/ddl/dim_department.sql
--
-- Department dimension table

CREATE TABLE IF NOT EXISTS finance.dim_department (
  department_id STRING NOT NULL,
  department_name STRING NOT NULL,
  cost_center STRING,
  is_active BOOL DEFAULT TRUE
)
OPTIONS (
  description = "Department dimension for financial reporting"
);
