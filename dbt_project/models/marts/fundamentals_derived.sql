-- models/marts/fundamentals_derived.sql
-- Calculate derived fundamental ratios (PE, PB, EV/EBIT, ROA, ROI, etc.)
{{ config(
    materialized='table',
    tags=['marts', 'fundamentals', 'ratios']
) }}

WITH fundamentals AS (
    SELECT * FROM {{ ref('stg_fundamentals') }}
),

prices AS (
    SELECT * FROM {{ ref('stg_prices') }}
),

latest_prices AS (
    SELECT
        f.ticker,
        f.report_date,
        p.close_price AS price_per_share,
        p.price_date,
        ROW_NUMBER() OVER (
            PARTITION BY f.ticker, f.report_date 
            ORDER BY p.price_date DESC
        ) AS price_rank
    FROM fundamentals f
    LEFT JOIN prices p
        ON f.ticker = p.ticker
        AND p.price_date <= f.report_date
        AND p.price_date >= DATE_SUB(f.report_date, INTERVAL 30 DAY)
)

SELECT
    f.ticker,
    f.report_date,
    lp.price_per_share,
    lp.price_date,
    
    -- Valuation Ratios
    CASE 
        WHEN f.net_income / NULLIF(f.shares_outstanding, 0) != 0 
        THEN lp.price_per_share / NULLIF(f.net_income / f.shares_outstanding, 0)
        ELSE NULL 
    END AS pe_ratio,
    
    CASE 
        WHEN f.total_equity / NULLIF(f.shares_outstanding, 0) != 0 
        THEN lp.price_per_share / NULLIF(f.total_equity / f.shares_outstanding, 0)
        ELSE NULL 
    END AS pb_ratio,
    
    -- Enterprise Value Ratios
    CASE 
        WHEN f.ebit != 0 
        THEN (
            lp.price_per_share * f.shares_outstanding 
            + f.total_liabilities 
            - f.cash_and_equivalents
        ) / NULLIF(f.ebit, 0)
        ELSE NULL 
    END AS ev_ebit,
    
    CASE 
        WHEN f.ebitda != 0 
        THEN (
            lp.price_per_share * f.shares_outstanding 
            + f.total_liabilities 
            - f.cash_and_equivalents
        ) / NULLIF(f.ebitda, 0)
        ELSE NULL 
    END AS ev_ebitda,
    
    -- Profitability Ratios
    f.net_income / NULLIF(f.total_assets, 0) AS roa,
    f.net_income / NULLIF(f.total_equity, 0) AS roi,
    f.net_income / NULLIF(f.shares_outstanding, 0) AS eps,
    
    -- Additional Metrics
    f.ebit AS noi,
    f.total_liabilities / NULLIF(f.total_equity, 0) AS debt_to_equity,
    f.cash_and_equivalents / NULLIF(f.total_assets, 0) AS cash_ratio,
    
    -- Raw Fundamentals
    f.net_income,
    f.ebit,
    f.ebitda,
    f.total_assets,
    f.total_equity,
    f.total_liabilities,
    f.cash_and_equivalents,
    f.shares_outstanding,
    
    -- Metadata
    f.ingested_at,
    CURRENT_TIMESTAMP() AS calculated_at
    
FROM fundamentals f
LEFT JOIN latest_prices lp
    ON f.ticker = lp.ticker
    AND f.report_date = lp.report_date
    AND lp.price_rank = 1
WHERE lp.price_per_share IS NOT NULL
