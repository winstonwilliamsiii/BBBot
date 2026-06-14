-- models/staging/stg_prices.sql
-- Staging model for daily price data from Airbyte/Tiingo
{{ config(
    materialized='view',
    tags=['staging', 'prices']
) }}

SELECT
    ticker,
    CAST(date AS DATE) AS price_date,
    CAST(open AS DECIMAL(18, 4)) AS open_price,
    CAST(high AS DECIMAL(18, 4)) AS high_price,
    CAST(low AS DECIMAL(18, 4)) AS low_price,
    CAST(close AS DECIMAL(18, 4)) AS close_price,
    CAST(volume AS BIGINT) AS volume,
    CAST(adj_close AS DECIMAL(18, 4)) AS adj_close_price,
    created_at AS ingested_at
FROM {{ source('raw', 'prices_daily') }}
WHERE date IS NOT NULL
  AND ticker IS NOT NULL
  AND close IS NOT NULL
