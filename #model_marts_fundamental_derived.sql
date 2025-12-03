#model_marts_fundamental_derived.sql
{{ config(materialized='table') }}

WITH fundamentals AS (
    SELECT * FROM {{ ref('stg_fundamentals') }}
),
prices AS (
    SELECT * FROM {{ ref('stg_prices') }}
)

SELECT
    f.ticker,
    f.report_date,
    p.price_per_share,
    (p.price_per_share / NULLIF(f.net_income / f.shares_outstanding,0)) AS pe_ratio,
    (p.price_per_share / NULLIF(f.total_equity / f.shares_outstanding,0)) AS pb_ratio,
    ((p.price_per_share * f.shares_outstanding + f.total_liabilities - f.cash_and_equivalents) / NULLIF(f.ebit,0)) AS ev_ebit,
    ((p.price_per_share * f.shares_outstanding + f.total_liabilities - f.cash_and_equivalents) / NULLIF(f.ebitda,0)) AS ev_ebitda,
    (f.net_income / NULLIF(f.total_assets,0)) AS roa,
    (f.net_income / NULLIF(f.total_equity,0)) AS roi,
    f.ebit AS noi
FROM fundamentals f
LEFT JOIN prices p
  ON f.ticker = p.ticker
 AND p.date <= f.report_date
QUALIFY ROW_NUMBER() OVER (PARTITION BY f.ticker, f.report_date ORDER BY p.date DESC) = 1