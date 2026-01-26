"""Kalshi ingestion client for REST and WebSocket feeds."""
import asyncio
import json
import logging
from typing import Dict, List

import aiohttp
import websockets
from sqlalchemy import text

from prediction_analytics.services.db import get_session_factory

logger = logging.getLogger(__name__)


class KalshiClient:
    base_url = "https://api.kalshi.com/v1"
    ws_url = "wss://feeds.kalshi.com/v1/streamer"

    def __init__(self, api_key: str = ""):
        self.api_key = api_key
        self.session_factory = get_session_factory()

    async def fetch_markets(self) -> List[Dict]:
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/markets", headers=headers, timeout=30) as resp:
                    if resp.status != 200:
                        logger.error("Kalshi markets failed: %s", resp.status)
                        return []
                    data = await resp.json()
                    return data.get("markets", [])
        except Exception as exc:
            logger.error("Kalshi fetch error: %s", exc)
            return []

    async def upsert_markets(self, markets: List[Dict]) -> int:
        inserted = 0
        with self.session_factory() as session:
            for mk in markets:
                try:
                    query = text(
                        """
                        INSERT INTO mansa_quant.event_contracts
                        (contract_id, contract_name, description, source, source_connector,
                         category, resolution_date, status, yes_price, no_price, volume_24h,
                         liquidity_usd, external_data_source, last_synced)
                        VALUES (:cid, :cname, :descr, 'Kalshi', 'kalshi-rest', :cat, :rdate,
                                :status, :yesp, :nop, :vol, :liq, :ext, NOW())
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
                        "cid": mk.get("ticker", ""),
                        "cname": mk.get("title", ""),
                        "descr": mk.get("description", ""),
                        "cat": mk.get("category", "Unknown"),
                        "rdate": mk.get("end_date"),
                        "status": self._map_status(mk.get("status")),
                        "yesp": float(mk.get("yes_price", 0.5)),
                        "nop": float(mk.get("no_price", 0.5)),
                        "vol": float(mk.get("volume_24h", 0)),
                        "liq": float(mk.get("liquidity", 0)),
                        "ext": f"https://kalshi.com/markets/{mk.get('ticker','')}",
                    })
                    inserted += 1
                except Exception as exc:
                    logger.error("Upsert market failed %s: %s", mk.get("ticker"), exc)
            session.commit()
        return inserted

    async def stream_orderbooks(self, contract_ids: List[str], limit: int = 10) -> None:
        if not contract_ids:
            return
        selected = contract_ids[:limit]
        try:
            async with websockets.connect(self.ws_url) as ws:
                await ws.send(json.dumps({"type": "subscribe", "contracts": selected}))
                logger.info("Subscribed to Kalshi WS for %s contracts", len(selected))
                while True:
                    try:
                        msg = await asyncio.wait_for(ws.recv(), timeout=60)
                        data = json.loads(msg)
                        if data.get("type") == "orderbook":
                            await self._store_orderbook(data)
                    except asyncio.TimeoutError:
                        logger.warning("Kalshi WS timeout, reconnecting...")
                        break
        except Exception as exc:
            logger.error("Kalshi WS error: %s", exc)

    async def _store_orderbook(self, data: Dict) -> None:
        contract_id = data.get("contract_id")
        bids = data.get("bids", [])
        asks = data.get("asks", [])
        with self.session_factory() as session:
            for side, orders in (("BID", bids), ("ASK", asks)):
                for order in orders:
                    try:
                        query = text(
                            """
                            INSERT INTO mansa_quant.orderbook_data
                            (contract_id, source, feed_type, side, price, quantity, timestamp, raw_data)
                            VALUES (:cid, 'Kalshi', 'WebSocket', :side, :price, :qty, NOW(), :raw)
                            """
                        )
                        session.execute(query, {
                            "cid": contract_id,
                            "side": side,
                            "price": float(order.get("price", 0)),
                            "qty": float(order.get("size", 0)),
                            "raw": json.dumps(order),
                        })
                    except Exception as exc:
                        logger.error("Kalshi order insert failed %s: %s", contract_id, exc)
            session.commit()

    def _map_status(self, status: str) -> str:
        return {
            "open": "OPEN",
            "closed": "RESOLVED",
            "cancelled": "CANCELLED",
        }.get(status, "OPEN")

    async def run(self) -> None:
        markets = await self.fetch_markets()
        inserted = await self.upsert_markets(markets)
        logger.info("Kalshi markets upserted: %s", inserted)
        contract_ids = [m.get("ticker") for m in markets if m.get("ticker")]
        await self.stream_orderbooks(contract_ids)


def main():
    import os
    api_key = os.getenv("KALSHI_API_KEY", "")
    asyncio.run(KalshiClient(api_key).run())


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
