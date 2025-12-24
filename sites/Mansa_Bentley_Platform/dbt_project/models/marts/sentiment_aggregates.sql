-- models/marts/sentiment_aggregates.sql
-- Daily aggregated sentiment metrics by ticker
{{ config(
    materialized='table',
    tags=['marts', 'sentiment', 'aggregates']
) }}

WITH daily_sentiment AS (
    SELECT
        ticker,
        sentiment_date,
        AVG(sentiment_score) AS avg_sentiment_score,
        MIN(sentiment_score) AS min_sentiment_score,
        MAX(sentiment_score) AS max_sentiment_score,
        STDDEV(sentiment_score) AS stddev_sentiment_score,
        SUM(message_count) AS total_messages,
        SUM(bullish_count) AS total_bullish,
        SUM(bearish_count) AS total_bearish,
        COUNT(DISTINCT source) AS source_count,
        MAX(sentiment_timestamp) AS latest_timestamp
    FROM {{ ref('stg_sentiment') }}
    GROUP BY ticker, sentiment_date
)

SELECT
    ticker,
    sentiment_date,
    avg_sentiment_score,
    min_sentiment_score,
    max_sentiment_score,
    stddev_sentiment_score,
    total_messages,
    total_bullish,
    total_bearish,
    
    -- Sentiment momentum (vs previous day)
    LAG(avg_sentiment_score, 1) OVER (
        PARTITION BY ticker 
        ORDER BY sentiment_date
    ) AS prev_day_sentiment,
    
    avg_sentiment_score - LAG(avg_sentiment_score, 1) OVER (
        PARTITION BY ticker 
        ORDER BY sentiment_date
    ) AS sentiment_change,
    
    -- Sentiment ratios
    CASE 
        WHEN (total_bullish + total_bearish) > 0 
        THEN total_bullish / NULLIF(total_bullish + total_bearish, 0)
        ELSE NULL 
    END AS bullish_ratio,
    
    -- Rolling averages (7-day)
    AVG(avg_sentiment_score) OVER (
        PARTITION BY ticker 
        ORDER BY sentiment_date 
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) AS sentiment_7day_ma,
    
    AVG(total_messages) OVER (
        PARTITION BY ticker 
        ORDER BY sentiment_date 
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) AS messages_7day_ma,
    
    -- Metadata
    source_count,
    latest_timestamp,
    CURRENT_TIMESTAMP() AS calculated_at
    
FROM daily_sentiment
ORDER BY ticker, sentiment_date DESC
