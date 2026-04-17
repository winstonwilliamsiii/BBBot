# Altair Bot — Strategy & Technical Reference

## Overview

| Field | Value |
|-------|-------|
| **Bot ID** | 4 |
| **Fund** | Mansa AI |
| **Strategy** | News Trading (AI Momentum) |
| **Primary Broker** | Alpaca |
| **Asset Class** | Equities — AI/Tech momentum names |
| **Timeframe** | 30m |
| **Universe** | AI_News_Momentum screener (`altair_ai_news_signals.csv`) |
| **Status** | Implementation in progress (scaffold in `bentley-bot/bots/altair.py`) |

---

## Strategy: News-Driven AI Momentum Trading

Altair is an event-driven momentum bot targeting AI and high-growth technology stocks. It monitors news feeds and headline sentiment to identify momentum triggers, entering trades when news sentiment exceeds a minimum threshold and holding for up to 24 hours.

### Signal Generation Logic

1. **News Aggregation** — Headlines collected from configured news sources (RSS, API, or manual injection).
2. **Sentiment Scoring** — Each headline scored for relevance to the target ticker and polarity (positive/negative).
3. **News Score Threshold** — Composite news score must exceed **0.70** (70%) to generate a signal.
4. **Momentum Confirmation** — Price action on the 30m bar confirms directional bias before entry.
5. **Signal Decay** — Maximum holding period is 24 hours; positions are closed at EOD if signal has not resolved.

### Score Calculation

```
news_score = weighted_average(headline_sentiment_scores)
signal = BUY  if news_score >= 0.70 and price_momentum > 0
signal = SELL if news_score <= -0.70 and price_momentum < 0
signal = HOLD otherwise
```

---

## Trade Parameters

```yaml
strategy:
  timeframe: 30m
  position_size: 1800
  label: Altair_AI_News_Momentum

risk:
  min_news_score: 0.70
  max_holding_hours: 24
  max_daily_loss_pct: 1.5
  max_open_positions: 4

execution:
  primary_client: alpaca_client
  mode: paper
  order_type: market
```

---

## Position Sizing & Risk Controls

| Parameter | Value |
|-----------|-------|
| **Position size** | $1,800 per trade |
| **Max open positions** | 4 |
| **Max holding time** | 24 hours |
| **Min news score** | 0.70 |
| **Max daily loss** | 1.5% of account |

---

## Algorithms Used

| Algorithm | Role |
|-----------|------|
| **NLP Sentiment Scoring** | Headline polarity → news score |
| **Momentum Filter** | Price bar confirmation on 30m timeframe |
| **Time-decay Exit** | Forced close at 24-hour holding limit |

---

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `ALTAIR_ENABLE_TRADING` | `false` | Set `true` to enable order submission |
| `ALTAIR_TRADING_MODE` | `paper` | `paper` or `live` |
| `ALTAIR_MIN_NEWS_SCORE` | `0.70` | Override minimum news score threshold |
| `ALTAIR_MAX_HOLDING_HOURS` | `24` | Max position duration |
| `ALPACA_API_KEY` | — | Alpaca API key |
| `ALPACA_SECRET_KEY` | — | Alpaca API secret |
| `MLFLOW_TRACKING_URI` | `http://localhost:5000` | MLflow server |

---

## Main Files

| File | Purpose |
|------|---------|
| `bentley-bot/bots/altair.py` | Bot implementation (scaffold) |
| `bentley-bot/config/bots/altair.yml` | Bot profile and risk config |

---

## Implementation Notes

Altair is implemented as a scaffold bot. The core framework (bot registry, health check routing, execution interface) is in place. The remaining implementation surface involves:

1. **News API integration** — Wire up preferred headline sources
2. **Scoring model** — Build or integrate a headline-to-score NLP pipeline (TextBlob / FinBERT / GPT)
3. **Momentum confirmation layer** — Integrate 30m OHLCV bars for price confirmation
4. **MLflow logging** — Log scores and trade outcomes per signal

---

## Notification

Discord notification triggers on:
- `FVFI` signal (Fundamental Value Fair Interest)
- `ROVL` signal (Risk-Objective Validation Level)
