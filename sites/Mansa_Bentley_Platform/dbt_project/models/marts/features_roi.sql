-- models/marts/features_roi.sql
-- Feature engineering table for MLFlow ROI prediction models
-- Combines fundamental ratios with technical indicators and sentiment
{{ config(
    materialized='table',
    tags=['marts', 'features', 'mlflow', 'roi']
) }}

WITH fundamentals AS (
    SELECT * FROM {{ ref('fundamentals_derived') }}
),

sentiment AS (
    SELECT * FROM {{ ref('sentiment_aggregates') }}
),

prices AS (
    SELECT * FROM {{ ref('stg_prices') }}
),

price_features AS (
    SELECT
        ticker,
        price_date,
        close_price,
        
        -- 30-day price momentum
        LAG(close_price, 30) OVER (
            PARTITION BY ticker ORDER BY price_date
        ) AS price_30d_ago,
        
        (close_price - LAG(close_price, 30) OVER (
            PARTITION BY ticker ORDER BY price_date
        )) / NULLIF(LAG(close_price, 30) OVER (
            PARTITION BY ticker ORDER BY price_date
        ), 0) AS price_momentum_30d,
        
        -- Volume features
        AVG(volume) OVER (
            PARTITION BY ticker 
            ORDER BY price_date 
            ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
        ) AS avg_volume_30d,
        
        -- Volatility
        STDDEV(close_price) OVER (
            PARTITION BY ticker 
            ORDER BY price_date 
            ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
        ) AS price_volatility_30d
        
    FROM prices
)

SELECT
    f.ticker,
    f.report_date,
    f.price_date,
    
    -- Target variable (ROI)
    f.roi AS target_roi,
    
    -- Fundamental Features
    f.pe_ratio,
    f.pb_ratio,
    f.ev_ebit,
    f.ev_ebitda,
    f.roa,
    f.eps,
    f.debt_to_equity,
    f.cash_ratio,
    
    -- Normalized fundamentals
    LOG(NULLIF(ABS(f.net_income), 0)) AS log_net_income,
    LOG(NULLIF(f.total_assets, 0)) AS log_total_assets,
    LOG(NULLIF(f.total_equity, 0)) AS log_total_equity,
    
    -- Price Features
    pf.price_momentum_30d,
    pf.avg_volume_30d,
    pf.price_volatility_30d,
    
    -- Sentiment Features
    s.avg_sentiment_score,
    s.sentiment_change,
    s.bullish_ratio,
    s.sentiment_7day_ma,
    s.total_messages,
    
    -- Interaction Features
    f.pe_ratio * s.avg_sentiment_score AS pe_sentiment_interaction,
    f.roa * s.bullish_ratio AS roa_sentiment_interaction,
    
    -- Categorical Encoding (for ML models)
    CASE 
        WHEN f.ticker IN ({{ var('quantum_tickers') | join(', ') | replace('[', "'") | replace(']', "'") | replace(',', "','") }}) 
        THEN 'quantum' 
        ELSE 'traditional' 
    END AS ticker_category,
    
    -- Data Quality Flags
    CASE 
        WHEN f.pe_ratio IS NULL OR f.pb_ratio IS NULL OR f.roi IS NULL 
        THEN 1 ELSE 0 
    END AS has_missing_fundamentals,
    
    CASE 
        WHEN s.avg_sentiment_score IS NULL 
        THEN 1 ELSE 0 
    END AS has_missing_sentiment,
    
    -- Metadata
    f.calculated_at AS fundamental_calculated_at,
    s.calculated_at AS sentiment_calculated_at,
    CURRENT_TIMESTAMP() AS features_calculated_at

FROM fundamentals f
LEFT JOIN price_features pf
    ON f.ticker = pf.ticker
    AND f.price_date = pf.price_date
LEFT JOIN sentiment s
    ON f.ticker = s.ticker
    AND f.report_date = s.sentiment_date

WHERE f.roi IS NOT NULL  -- Must have target variable
  AND f.pe_ratio IS NOT NULL
  AND f.pb_ratio IS NOT NULL
  
ORDER BY f.ticker, f.report_date DESC
