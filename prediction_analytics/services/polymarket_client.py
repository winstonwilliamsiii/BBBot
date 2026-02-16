"""Polymarket ingestion client for Gamma and CLOB feeds."""
import asyncio
import json
import logging
from typing import Dict, List

import aiohttp
from sqlalchemy import text

from prediction_analytics.services.db import get_session_factory

logger = logging.getLogger(__name__)


class PolymarketClient:
    base_url = "https://api.polymarket.com/events"
    clob_url = "https://clob.polymarket.com/orderbook"

    def __init__(self):
        self.session_factory = get_session_factory()

    async def fetch_events(self) -> List[Dict]:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, timeout=30) as resp:
                    if resp.status != 200:
                        logger.error("Polymarket events failed: %s", resp.status)
                        return []
                    data = await resp.json()
                    return data if isinstance(data, list) else []
        except Exception as exc:
            logger.error("Polymarket fetch error: %s", exc)
            return []

    async def fetch_orderbook(self, contract_id: str) -> Dict:
        url = f"{self.clob_url}/{contract_id}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=15) as resp:
                    if resp.status != 200:
                        logger.warning("Orderbook fetch failed %s: %s", contract_id, resp.status)
                        return {}
                    return await resp.json()
        except Exception as exc:
            logger.error("Orderbook fetch error %s: %s", contract_id, exc)
            return {}

    async def upsert_events(self, events: List[Dict]) -> int:
        inserted = 0
        with self.session_factory() as session:
            for ev in events:
                try:
                    query = text(
                        """
                        INSERT INTO mansa_quant.event_contracts
                        (contract_id, contract_name, description, source, source_connector,
                         category, resolution_date, status, yes_price, no_price, volume_24h,
                         liquidity_usd, last_synced)
                        VALUES (:cid, :cname, :descr, 'Polymarket', 'polymarket-gamma',
                                :cat, :rdate, :status, :yesp, :nop, :vol, :liq, NOW())
                        ON DUPLICATE KEY UPDATE
                            contract_name = VALUES(contract_name),
                            yes_price = VALUES(yes_price),
                            no_price = VALUES(no_price),
                            volume_24h = VALUES(volume_24h),
                            liquidity_usd = VALUES(liquidity_usd),
                            status = VALUES(status),
                            last_synced = NOW()
                        """
                    )
                    session.execute(query, {
                        "cid": ev.get("id", ""),
                        "cname": ev.get("title", ""),
                        "descr": ev.get("description", ""),
                        "cat": ev.get("category", "Unknown"),
                        "rdate": ev.get("resolvedAt"),
                        "status": self._map_status(ev.get("status")),
                        "yesp": float(ev.get("price", 0)),
                        "nop": 1.0 - float(ev.get("price", 0)),
                        "vol": float(ev.get("volume24h", 0)),
                        "liq": float(ev.get("liquidityUSD", 0)),
                    })
                    inserted += 1
                except Exception as exc:
                    logger.error("Upsert event failed %s: %s", ev.get("id"), exc)
            session.commit()
        return inserted

    async def ingest_orderbook(self, contract_id: str, ob: Dict) -> int:
        bids = ob.get("bids", [])
        asks = ob.get("asks", [])
        count = 0
        with self.session_factory() as session:
            for side, orders in (("BID", bids), ("ASK", asks)):
                for order in orders:
                    try:
                        query = text(
                            """
                            INSERT INTO mansa_quant.orderbook_data
                            (contract_id, source, feed_type, side, price, quantity, timestamp, raw_data)
                            VALUES (:cid, 'Polymarket', 'CLOB', :side, :price, :qty, NOW(), :raw)
                            """
                        )
                        session.execute(query, {
                            "cid": contract_id,
                            "side": side,
                            "price": float(order.get("price", 0)),
                            "qty": float(order.get("size", 0)),
                            "raw": json.dumps(order),
                        })
                        count += 1
                    except Exception as exc:
                        logger.error("Order insert failed %s: %s", contract_id, exc)
            session.commit()
        return count

    def _map_status(self, status: str) -> str:
        return {
            "active": "OPEN",
            "resolved": "RESOLVED",
            "cancelled": "CANCELLED",
        }.get(status, "OPEN")

    async def run(self) -> None:
        events = await self.fetch_events()
        if not events:
            logger.info("No events fetched from Polymarket")
            return
        inserted = await self.upsert_events(events)
        logger.info("Polymarket events upserted: %s", inserted)
        # Ingest orderbook for first few active contracts
        for ev in events[:10]:
            contract_id = ev.get("id")
            if not contract_id:
                continue
            ob = await self.fetch_orderbook(contract_id)
            if ob:
                count = await self.ingest_orderbook(contract_id, ob)
                logger.info("Orderbook records inserted for %s: %s", contract_id, count)


def main():
    asyncio.run(PolymarketClient().run())


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
