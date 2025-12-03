-- models/staging/stg_sentiment.sql
-- Staging model for sentiment data from StockTwits/social media
{{ config(
    materialized='view',
    tags=['staging', 'sentiment']
) }}

SELECT
    ticker,
    CAST(timestamp AS DATETIME) AS sentiment_timestamp,
    CAST(DATE(timestamp) AS DATE) AS sentiment_date,
    source,
    sentiment_score,
    sentiment_label,
    message_count,
    bullish_count,
    bearish_count,
    created_at AS ingested_at
FROM {{ source('raw', 'sentiment_raw') }}
WHERE ticker IS NOT NULL
  AND timestamp IS NOT NULL
  AND sentiment_score IS NOT NULL
