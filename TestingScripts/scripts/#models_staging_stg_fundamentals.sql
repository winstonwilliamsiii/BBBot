#models/staging/stg_fundamentals.sql
{{ config(materialized='view') }}

SELECT
    ticker,
    CAST(report_date AS DATE) AS report_date,
    net_income,
    ebit,
    ebitda,
    total_assets,
    total_equity,
    total_liabilities,
    cash_and_equivalents,
    shares_outstanding
FROM {{ source('raw', 'fundamentals_raw') }}
WHERE report_date IS NOT NULL
  AND net_income IS NOT NULL
  AND total_assets IS NOT NULL
  AND total_equity IS NOT NULL
  AND shares_outstanding IS NOT NULL
  AND total_liabilities IS NOT NULL
  AND cash_and_equivalents IS NOT NULL
  AND ebit IS NOT NULL
  AND ebitda IS NOT NULL    