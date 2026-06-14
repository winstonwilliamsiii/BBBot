-- models/staging/stg_fundamentals.sql
-- Staging model for fundamental financial data from Airbyte/AlphaVantage/yfinance
{{ config(
    materialized='view',
    tags=['staging', 'fundamentals']
) }}

SELECT
    ticker,
    CAST(report_date AS DATE) AS report_date,
    CAST(net_income AS DECIMAL(18, 2)) AS net_income,
    CAST(ebit AS DECIMAL(18, 2)) AS ebit,
    CAST(ebitda AS DECIMAL(18, 2)) AS ebitda,
    CAST(total_assets AS DECIMAL(18, 2)) AS total_assets,
    CAST(total_equity AS DECIMAL(18, 2)) AS total_equity,
    CAST(total_liabilities AS DECIMAL(18, 2)) AS total_liabilities,
    CAST(cash_and_equivalents AS DECIMAL(18, 2)) AS cash_and_equivalents,
    CAST(shares_outstanding AS BIGINT) AS shares_outstanding,
    created_at AS ingested_at
FROM {{ source('raw', 'fundamentals_raw') }}
WHERE report_date IS NOT NULL
  AND ticker IS NOT NULL
  AND net_income IS NOT NULL
  AND total_assets IS NOT NULL
  AND total_equity IS NOT NULL
  AND shares_outstanding IS NOT NULL
  AND total_liabilities IS NOT NULL
  AND cash_and_equivalents IS NOT NULL
  AND ebit IS NOT NULL
  AND ebitda IS NOT NULL
