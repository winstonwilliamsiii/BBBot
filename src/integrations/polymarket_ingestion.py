"""
Polymarket Data Ingestion Module
Handles GAMMA and CLOB feed integration via Airbyte
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

import aiohttp
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)


@dataclass
class PolymarketContract:
    """Polymarket contract data model"""
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


class PolymarketGammaConnector:
    """
    Polymarket GAMMA feed connector
    Pulls real-time event contract data
    """
    
    BASE_URL = "https://api.polymarket.com/events"
    FEED_TYPE = "GAMMA"
    
    def __init__(self, db_connection_string: str):
        """Initialize Polymarket GAMMA connector"""
        self.db_engine = create_engine(db_connection_string)
        self.session_factory = sessionmaker(bind=self.db_engine)
        self.connector_name = "polymarket-gamma"
        
    async def fetch_events(self) -> List[Dict]:
        """
        Fetch active events from Polymarket GAMMA
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.BASE_URL,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"Fetched {len(data)} events from Polymarket GAMMA")
                        return data
                    else:
                        logger.error(f"Polymarket API error: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"Polymarket fetch failed: {str(e)}")
            return []
    
    def normalize_contract(self, event: Dict) -> PolymarketContract:
        """
        Normalize Polymarket event to standard contract format
        Maps Polymarket fields to event_contracts table schema
        """
        return PolymarketContract(
            contract_id=event.get('id', ''),
            contract_name=event.get('title', ''),
            description=event.get('description', ''),
            category=event.get('category', 'Unknown'),
            resolution_date=event.get('resolvedAt', ''),
            status=self._map_status(event.get('status')),
            yes_price=float(event.get('price', 0)),
            no_price=1.0 - float(event.get('price', 0)),
            volume_24h=float(event.get('volume24h', 0)),
            liquidity_usd=float(event.get('liquidityUSD', 0))
        )
    
    def _map_status(self, polymarket_status: str) -> str:
        """Map Polymarket status to standard status"""
        status_map = {
            'active': 'OPEN',
            'resolved': 'RESOLVED',
            'cancelled': 'CANCELLED'
        }
        return status_map.get(polymarket_status, 'OPEN')
    
    async def ingest_contracts(self) -> Tuple[int, int]:
        """
        Fetch and ingest Polymarket contracts into database
        Returns: (records_inserted, records_updated)
        """
        events = await self.fetch_events()
        inserted, updated = 0, 0
        
        with self.session_factory() as session:
            for event in events:
                try:
                    contract = self.normalize_contract(event)
                    
                    # Upsert into event_contracts table
                    query = text("""
                        INSERT INTO mansa_quant.event_contracts 
                        (contract_id, contract_name, description, source, source_connector,
                         category, resolution_date, status, yes_price, no_price, 
                         volume_24h, liquidity_usd, last_synced)
                        VALUES (:contract_id, :contract_name, :description, 'Polymarket', 
                                :source_connector, :category, :resolution_date, :status, 
                                :yes_price, :no_price, :volume_24h, :liquidity_usd, NOW())
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
                        'liquidity_usd': contract.liquidity_usd
                    })
                    
                    # Track inserts vs updates (simplified)
                    inserted += 1
                    
                except Exception as e:
                    logger.error(f"Failed to ingest contract {event.get('id')}: {str(e)}")
                    continue
            
            session.commit()
        
        return inserted, updated


class PolymarketCLOBConnector:
    """
    Polymarket CLOB (Central Limit Order Book) feed connector
    Pulls real-time orderbook data
    """
    
    BASE_URL = "https://clob.polymarket.com"
    FEED_TYPE = "CLOB"
    
    def __init__(self, db_connection_string: str):
        """Initialize Polymarket CLOB connector"""
        self.db_engine = create_engine(db_connection_string)
        self.session_factory = sessionmaker(bind=self.db_engine)
        self.connector_name = "polymarket-clob"
    
    async def fetch_orderbook(self, contract_id: str) -> Dict:
        """
        Fetch orderbook snapshot for contract
        """
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.BASE_URL}/orderbook/{contract_id}"
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"CLOB API error: {response.status} for {contract_id}")
                        return {}
        except Exception as e:
            logger.error(f"CLOB fetch failed for {contract_id}: {str(e)}")
            return {}
    
    async def ingest_orderbook(self, contract_id: str, feed_data: Dict) -> int:
        """
        Ingest orderbook data into database
        Returns: number of records inserted
        """
        bids = feed_data.get('bids', [])
        asks = feed_data.get('asks', [])
        records_inserted = 0
        
        with self.session_factory() as session:
            for side, orders in [('BID', bids), ('ASK', asks)]:
                for order in orders:
                    try:
                        query = text("""
                            INSERT INTO mansa_quant.orderbook_data
                            (contract_id, source, feed_type, side, price, quantity, timestamp, raw_data)
                            VALUES (:contract_id, 'Polymarket', :feed_type, :side, :price, :quantity, NOW(), :raw_data)
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
                        logger.error(f"Failed to ingest order for {contract_id}: {str(e)}")
                        continue
            
            session.commit()
        
        return records_inserted


async def run_polymarket_sync(db_connection_string: str):
    """
    Main sync function for Polymarket data ingestion
    """
    logger.info("Starting Polymarket ingestion sync...")
    
    # Sync GAMMA contracts
    gamma_connector = PolymarketGammaConnector(db_connection_string)
    inserted, updated = await gamma_connector.ingest_contracts()
    logger.info(f"GAMMA: Inserted {inserted}, Updated {updated}")
    
    # Sync CLOB orderbooks for active contracts
    clob_connector = PolymarketCLOBConnector(db_connection_string)
    with gamma_connector.session_factory() as session:
        active_contracts = session.execute(
            text("SELECT contract_id FROM mansa_quant.event_contracts WHERE status = 'OPEN' LIMIT 10")
        ).fetchall()
        
        for (contract_id,) in active_contracts:
            orderbook = await clob_connector.fetch_orderbook(contract_id)
            if orderbook:
                records = await clob_connector.ingest_orderbook(contract_id, orderbook)
                logger.info(f"CLOB {contract_id}: Ingested {records} orderbook records")


if __name__ == "__main__":
    # Example usage
    DB_URL = "mysql+pymysql://bentley_user:bentley_password@localhost:3306/Bentley_Bot"
    asyncio.run(run_polymarket_sync(DB_URL))
