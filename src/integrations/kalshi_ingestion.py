"""
Kalshi Data Ingestion Module
Handles WebSocket and FIX feed integration via Airbyte
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass

import websockets
import aiohttp
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)


@dataclass
class KalshiContract:
    """Kalshi contract data model"""
    contract_id: str
    contract_name: str
    description: str
    category: str
    resolution_date: str
    status: str
    yes_price: float
    no_price: float
    volume_24h: float
    liquidity_usd: float


class KalshiRESTConnector:
    """
    Kalshi REST API connector
    Fetches event contract metadata
    """
    
    BASE_URL = "https://api.kalshi.com/v1"
    FEED_TYPE = "REST"
    
    def __init__(self, api_key: str, db_connection_string: str):
        """Initialize Kalshi REST connector"""
        self.api_key = api_key
        self.db_engine = create_engine(db_connection_string)
        self.session_factory = sessionmaker(bind=self.db_engine)
        self.connector_name = "kalshi-rest"
    
    async def fetch_markets(self) -> List[Dict]:
        """
        Fetch active markets from Kalshi REST API
        """
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.BASE_URL}/markets",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"Fetched {len(data.get('markets', []))} markets from Kalshi")
                        return data.get('markets', [])
                    else:
                        logger.error(f"Kalshi API error: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"Kalshi fetch failed: {str(e)}")
            return []
    
    def normalize_market(self, market: Dict) -> KalshiContract:
        """
        Normalize Kalshi market to standard contract format
        """
        return KalshiContract(
            contract_id=market.get('ticker', ''),
            contract_name=market.get('title', ''),
            description=market.get('description', ''),
            category=market.get('category', 'Unknown'),
            resolution_date=market.get('end_date', ''),
            status=self._map_status(market.get('status')),
            yes_price=float(market.get('yes_price', 0.5)),
            no_price=float(market.get('no_price', 0.5)),
            volume_24h=float(market.get('volume_24h', 0)),
            liquidity_usd=float(market.get('liquidity', 0))
        )
    
    def _map_status(self, kalshi_status: str) -> str:
        """Map Kalshi status to standard status"""
        status_map = {
            'open': 'OPEN',
            'closed': 'RESOLVED',
            'cancelled': 'CANCELLED'
        }
        return status_map.get(kalshi_status, 'OPEN')
    
    async def ingest_markets(self) -> tuple:
        """
        Fetch and ingest Kalshi markets into database
        Returns: (records_inserted, records_updated)
        """
        markets = await self.fetch_markets()
        inserted, updated = 0, 0
        
        with self.session_factory() as session:
            for market in markets:
                try:
                    contract = self.normalize_market(market)
                    
                    # Upsert into event_contracts table
                    query = text("""
                        INSERT INTO mansa_quant.event_contracts
                        (contract_id, contract_name, description, source, source_connector,
                         category, resolution_date, status, yes_price, no_price,
                         volume_24h, liquidity_usd, external_data_source, last_synced)
                        VALUES (:contract_id, :contract_name, :description, 'Kalshi',
                                :source_connector, :category, :resolution_date, :status,
                                :yes_price, :no_price, :volume_24h, :liquidity_usd,
                                :external_data_source, NOW())
                        ON DUPLICATE KEY UPDATE
                            contract_name = VALUES(contract_name),
                            yes_price = VALUES(yes_price),
                            no_price = VALUES(no_price),
                            volume_24h = VALUES(volume_24h),
                            liquidity_usd = VALUES(liquidity_usd),
                            status = VALUES(status),
                            last_synced = NOW()
                    """)
                    
                    session.execute(query, {
                        'contract_id': contract.contract_id,
                        'contract_name': contract.contract_name,
                        'description': contract.description,
                        'source_connector': self.connector_name,
                        'category': contract.category,
                        'resolution_date': contract.resolution_date or None,
                        'status': contract.status,
                        'yes_price': contract.yes_price,
                        'no_price': contract.no_price,
                        'volume_24h': contract.volume_24h,
                        'liquidity_usd': contract.liquidity_usd,
                        'external_data_source': f"https://kalshi.com/markets/{contract.contract_id}"
                    })
                    
                    inserted += 1
                    
                except Exception as e:
                    logger.error(f"Failed to ingest market {market.get('ticker')}: {str(e)}")
                    continue
            
            session.commit()
        
        return inserted, updated


class KalshiWebSocketConnector:
    """
    Kalshi WebSocket feed connector
    Real-time orderbook updates via WebSocket
    """
    
    WS_URL = "wss://feeds.kalshi.com/v1/streamer"
    FEED_TYPE = "WebSocket"
    
    def __init__(self, api_key: str, db_connection_string: str):
        """Initialize Kalshi WebSocket connector"""
        self.api_key = api_key
        self.db_engine = create_engine(db_connection_string)
        self.session_factory = sessionmaker(bind=self.db_engine)
        self.connector_name = "kalshi-websocket"
        self.running = False
    
    async def connect_and_stream(self, contract_ids: List[str]):
        """
        Connect to WebSocket and stream orderbook updates
        """
        try:
            async with websockets.connect(self.WS_URL) as websocket:
                # Subscribe to contract feeds
                subscribe_msg = {
                    "type": "subscribe",
                    "contracts": contract_ids
                }
                await websocket.send(json.dumps(subscribe_msg))
                logger.info(f"Subscribed to {len(contract_ids)} contract feeds")
                
                self.running = True
                while self.running:
                    try:
                        message = await asyncio.wait_for(
                            websocket.recv(),
                            timeout=60.0
                        )
                        data = json.loads(message)
                        await self.process_stream_data(data)
                    except asyncio.TimeoutError:
                        logger.warning("WebSocket timeout, reconnecting...")
                        break
                    except Exception as e:
                        logger.error(f"Stream processing error: {str(e)}")
                        break
        
        except Exception as e:
            logger.error(f"WebSocket connection failed: {str(e)}")
    
    async def process_stream_data(self, data: Dict) -> int:
        """
        Process incoming WebSocket data and insert into database
        Returns: number of records inserted
        """
        if data.get('type') != 'orderbook':
            return 0
        
        contract_id = data.get('contract_id')
        bids = data.get('bids', [])
        asks = data.get('asks', [])
        records_inserted = 0
        
        with self.session_factory() as session:
            for side, orders in [('BID', bids), ('ASK', asks)]:
                for order in orders:
                    try:
                        query = text("""
                            INSERT INTO mansa_quant.orderbook_data
                            (contract_id, source, feed_type, side, price, quantity, timestamp, raw_data)
                            VALUES (:contract_id, 'Kalshi', :feed_type, :side, :price, :quantity, NOW(), :raw_data)
                        """)
                        
                        session.execute(query, {
                            'contract_id': contract_id,
                            'feed_type': self.FEED_TYPE,
                            'side': side,
                            'price': float(order.get('price', 0)),
                            'quantity': float(order.get('size', 0)),
                            'raw_data': json.dumps(order)
                        })
                        
                        records_inserted += 1
                    except Exception as e:
                        logger.error(f"Failed to insert order for {contract_id}: {str(e)}")
                        continue
            
            session.commit()
        
        return records_inserted
    
    def stop(self):
        """Stop WebSocket streaming"""
        self.running = False


class KalshiFIXConnector:
    """
    Kalshi FIX (Financial Information Exchange) protocol connector
    For high-frequency trading scenarios
    """
    
    FEED_TYPE = "FIX"
    
    def __init__(self, fix_host: str, fix_port: int, api_key: str, db_connection_string: str):
        """Initialize Kalshi FIX connector"""
        self.fix_host = fix_host
        self.fix_port = fix_port
        self.api_key = api_key
        self.db_engine = create_engine(db_connection_string)
        self.session_factory = sessionmaker(bind=self.db_engine)
        self.connector_name = "kalshi-fix"
    
    async def ingest_fix_message(self, fix_message: Dict) -> int:
        """
        Process FIX protocol message
        Returns: number of records inserted
        """
        try:
            contract_id = fix_message.get('symbol')
            side = fix_message.get('side')  # '1' = BUY, '2' = SELL
            price = float(fix_message.get('price', 0))
            quantity = float(fix_message.get('orderqty', 0))
            
            with self.session_factory() as session:
                query = text("""
                    INSERT INTO mansa_quant.orderbook_data
                    (contract_id, source, feed_type, side, price, quantity, timestamp, raw_data)
                    VALUES (:contract_id, 'Kalshi', :feed_type, :side, :price, :quantity, NOW(), :raw_data)
                """)
                
                session.execute(query, {
                    'contract_id': contract_id,
                    'feed_type': self.FEED_TYPE,
                    'side': 'ASK' if side == '2' else 'BID',
                    'price': price,
                    'quantity': quantity,
                    'raw_data': json.dumps(fix_message)
                })
                
                session.commit()
                return 1
        
        except Exception as e:
            logger.error(f"FIX message processing failed: {str(e)}")
            return 0


async def run_kalshi_sync(api_key: str, db_connection_string: str):
    """
    Main sync function for Kalshi data ingestion
    """
    logger.info("Starting Kalshi ingestion sync...")
    
    # Sync REST API markets
    rest_connector = KalshiRESTConnector(api_key, db_connection_string)
    inserted, updated = await rest_connector.ingest_markets()
    logger.info(f"Kalshi REST: Inserted {inserted}, Updated {updated}")
    
    # Optional: Start WebSocket streaming (non-blocking)
    ws_connector = KalshiWebSocketConnector(api_key, db_connection_string)
    with rest_connector.session_factory() as session:
        active_contracts = session.execute(
            text("SELECT contract_id FROM mansa_quant.event_contracts WHERE source = 'Kalshi' AND status = 'OPEN'")
        ).fetchall()
        
        contract_ids = [c[0] for c in active_contracts]
        if contract_ids:
            asyncio.create_task(ws_connector.connect_and_stream(contract_ids))


if __name__ == "__main__":
    # Example usage
    API_KEY = "your_kalshi_api_key"
    DB_URL = "mysql+pymysql://bentley_user:bentley_password@localhost:3306/Bentley_Bot"
    asyncio.run(run_kalshi_sync(API_KEY, DB_URL))
