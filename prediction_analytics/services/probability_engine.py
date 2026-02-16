"""Probability engine for implied probability calculations."""
import logging
from typing import Dict, List, Optional

import numpy as np
from sqlalchemy import text

from prediction_analytics.services.db import get_session_factory

logger = logging.getLogger(__name__)


class ProbabilityEngine:
    def __init__(self):
        self.session_factory = get_session_factory()

    def _calc_lmsr(self, yes_price: float, no_price: float) -> float:
        total = yes_price + no_price
        if total == 0:
            return 50.0
        return (yes_price / total) * 100

    def _calc_amm(self, yes_liq: float, no_liq: float) -> float:
        if yes_liq + no_liq == 0:
            return 50.0
        return (yes_liq / (yes_liq + no_liq)) * 100

    def _calc_orderbook(self, bids: List[float], asks: List[float]) -> Optional[float]:
        if not bids or not asks:
            return None
        return (np.mean(bids) + np.mean(asks)) / 2 * 100

    def _confidence(self, values: List[float]) -> float:
        if not values:
            return 0.0
        if len(values) == 1:
            return 0.8
        variance = np.var(values)
        return round(min(1.0, 1.0 / (1.0 + variance / 100)), 2)

    async def compute_and_store(self, contract_id: str) -> Optional[Dict]:
        with self.session_factory() as session:
            contract = session.execute(text(
                """
                SELECT yes_price, no_price, liquidity_usd
                FROM mansa_quant.event_contracts
                WHERE contract_id = :cid AND status = 'OPEN'
                """
            ), {"cid": contract_id}).fetchone()
            if not contract:
                logger.info("No open contract found for %s", contract_id)
                return None
            yes_price, no_price, liquidity = contract

            order_rows = session.execute(text(
                """
                SELECT price, side FROM mansa_quant.orderbook_data
                WHERE contract_id = :cid AND timestamp > NOW() - INTERVAL 1 HOUR
                ORDER BY timestamp DESC LIMIT 100
                """
            ), {"cid": contract_id}).fetchall()
            bids = [p for p, side in order_rows if side == "BID"]
            asks = [p for p, side in order_rows if side == "ASK"]

            calcs = {
                "lmsr": self._calc_lmsr(yes_price, no_price),
                "amm": self._calc_amm(yes_price, max(1e-6, 1 - yes_price)),
            }
            ob_prob = self._calc_orderbook(bids, asks)
            if ob_prob is not None:
                calcs["orderbook"] = ob_prob

            implied = float(np.mean(list(calcs.values())))
            confidence = self._confidence(list(calcs.values()))

            session.execute(text(
                """
                INSERT INTO mansa_quant.prediction_probabilities
                (contract_id, source, implied_probability, confidence_score, rationale)
                VALUES (:cid, 'engine', :prob, :conf, :rat)
                """
            ), {
                "cid": contract_id,
                "prob": round(implied, 2),
                "conf": confidence,
                "rat": f"Ensemble of {len(calcs)} methods"
            })
            session.commit()
            logger.info("Stored prediction for %s -> %.2f (conf %.2f)", contract_id, implied, confidence)
            return {"contract_id": contract_id, "implied_probability": implied, "confidence": confidence}
