"""
Broker Interface - Abstract all brokers behind a common API
============================================================

This interface makes Alpaca, MT5, IBKR, and Webull look identical
to your trading strategies. Strategies only use this interface,
never calling broker APIs directly.

Usage:
    # Choose any broker
    broker = AlpacaBrokerClient()  # or MT5BrokerClient()
    
    # All brokers work the same
    equity = broker.get_equity()
    broker.place_order('AAPL', 10, 'buy')
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Position:
    """Standardized position across all brokers"""
    symbol: str
    qty: float
    side: str  # 'long' or 'short'
    entry_price: float
    current_price: float
    unrealized_pnl: float
    broker: str


@dataclass
class Order:
    """Standardized order across all brokers"""
    order_id: str
    symbol: str
    qty: float
    side: str  # 'buy' or 'sell'
    order_type: str  # 'market' or 'limit'
    status: str
    filled_qty: float
    avg_fill_price: Optional[float]


@dataclass
class HistoricalBar:
    """Standardized price bar"""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int


class BrokerClient(ABC):
    """
    Abstract base class that all broker implementations must follow.
    
    Your trading strategies ONLY interact with this interface,
    never directly with Alpaca/MT5/IBKR APIs.
    """
    
    @abstractmethod
    def get_equity(self) -> float:
        """Get current account equity/balance"""
        pass
    
    @abstractmethod
    def get_buying_power(self) -> float:
        """Get available buying power"""
        pass
    
    @abstractmethod
    def get_positions(self) -> List[Position]:
        """Get all open positions"""
        pass
    
    @abstractmethod
    def get_position(self, symbol: str) -> Optional[Position]:
        """Get specific position by symbol"""
        pass
    
    @abstractmethod
    def place_order(
        self,
        symbol: str,
        qty: float,
        side: str,
        order_type: str = "market",
        limit_price: Optional[float] = None
    ) -> Order:
        """Place a new order"""
        pass
    
    @abstractmethod
    def close_position(self, symbol: str) -> Order:
        """Close an existing position"""
        pass
    
    @abstractmethod
    def get_historical_prices(
        self,
        symbol: str,
        timeframe: str = "1D",
        limit: int = 100
    ) -> List[HistoricalBar]:
        """Get historical price data"""
        pass
    
    @abstractmethod
    def get_current_price(self, symbol: str) -> float:
        """Get latest price for a symbol"""
        pass
    
    @abstractmethod
    def cancel_order(self, order_id: str) -> bool:
        """Cancel a pending order"""
        pass
    
    @abstractmethod
    def get_broker_name(self) -> str:
        """Return broker name (e.g., 'alpaca', 'mt5')"""
        pass


# ============================================================
# ALPACA IMPLEMENTATION
# ============================================================

class AlpacaBrokerClient(BrokerClient):
    """Alpaca implementation of BrokerClient interface"""
    
    def __init__(self):
        from frontend.utils.alpaca_connector import AlpacaConnector
        import os
        
        self.connector = AlpacaConnector(
            api_key=os.getenv("ALPACA_API_KEY"),
            secret_key=os.getenv("ALPACA_SECRET_KEY"),
            paper=os.getenv("ALPACA_PAPER", "true").lower() == "true"
        )
    
    def get_equity(self) -> float:
        account = self.connector.get_account()
        return float(account['equity'])
    
    def get_buying_power(self) -> float:
        account = self.connector.get_account()
        return float(account['buying_power'])
    
    def get_positions(self) -> List[Position]:
        positions = self.connector.get_positions()
        return [
            Position(
                symbol=p['symbol'],
                qty=float(p['qty']),
                side='long' if float(p['qty']) > 0 else 'short',
                entry_price=float(p['avg_entry_price']),
                current_price=float(p['current_price']),
                unrealized_pnl=float(p['unrealized_pl']),
                broker='alpaca'
            )
            for p in positions
        ]
    
    def get_position(self, symbol: str) -> Optional[Position]:
        positions = self.get_positions()
        for pos in positions:
            if pos.symbol == symbol:
                return pos
        return None
    
    def place_order(
        self,
        symbol: str,
        qty: float,
        side: str,
        order_type: str = "market",
        limit_price: Optional[float] = None
    ) -> Order:
        result = self.connector.place_order(
            symbol=symbol,
            qty=int(qty),
            side=side,
            order_type=order_type,
            limit_price=limit_price
        )
        
        return Order(
            order_id=result['id'],
            symbol=result['symbol'],
            qty=float(result['qty']),
            side=result['side'],
            order_type=result['type'],
            status=result['status'],
            filled_qty=float(result.get('filled_qty', 0)),
            avg_fill_price=float(result['filled_avg_price']) if result.get('filled_avg_price') else None
        )
    
    def close_position(self, symbol: str) -> Order:
        result = self.connector.close_position(symbol)
        return Order(
            order_id=result['id'],
            symbol=result['symbol'],
            qty=float(result['qty']),
            side=result['side'],
            order_type=result['type'],
            status=result['status'],
            filled_qty=float(result.get('filled_qty', 0)),
            avg_fill_price=None
        )
    
    def get_historical_prices(
        self,
        symbol: str,
        timeframe: str = "1D",
        limit: int = 100
    ) -> List[HistoricalBar]:
        bars = self.connector.get_bars(symbol, timeframe, limit)
        return [
            HistoricalBar(
                timestamp=datetime.fromisoformat(bar['t'].replace('Z', '+00:00')),
                open=float(bar['o']),
                high=float(bar['h']),
                low=float(bar['l']),
                close=float(bar['c']),
                volume=int(bar['v'])
            )
            for bar in bars
        ]
    
    def get_current_price(self, symbol: str) -> float:
        quote = self.connector.get_latest_quote(symbol)
        return float(quote['ap'])  # ask price
    
    def cancel_order(self, order_id: str) -> bool:
        return self.connector.cancel_order(order_id)
    
    def get_broker_name(self) -> str:
        return "alpaca"


# ============================================================
# MT5 IMPLEMENTATION
# ============================================================

class MT5BrokerClient(BrokerClient):
    """MetaTrader 5 implementation of BrokerClient interface"""
    
    def __init__(self):
        from frontend.utils.mt5_connector import MT5Connector
        import os
        
        self.connector = MT5Connector(
            base_url=os.getenv("MT5_API_URL", "http://localhost:8000")
        )
        
        # Auto-connect
        self.connector.connect(
            user=os.getenv("MT5_USER"),
            password=os.getenv("MT5_PASSWORD"),
            host=os.getenv("MT5_HOST"),
            port=int(os.getenv("MT5_PORT", "443"))
        )
    
    def get_equity(self) -> float:
        account = self.connector.get_account_info()
        return float(account['equity'])
    
    def get_buying_power(self) -> float:
        account = self.connector.get_account_info()
        return float(account['free_margin'])
    
    def get_positions(self) -> List[Position]:
        positions = self.connector.get_positions()
        return [
            Position(
                symbol=p.symbol,
                qty=p.volume,
                side='long' if p.type == 'BUY' else 'short',
                entry_price=p.open_price,
                current_price=p.current_price,
                unrealized_pnl=p.profit,
                broker='mt5'
            )
            for p in positions
        ]
    
    def get_position(self, symbol: str) -> Optional[Position]:
        positions = self.get_positions()
        for pos in positions:
            if pos.symbol == symbol:
                return pos
        return None
    
    def place_order(
        self,
        symbol: str,
        qty: float,
        side: str,
        order_type: str = "market",
        limit_price: Optional[float] = None
    ) -> Order:
        result = self.connector.place_trade(
            symbol=symbol,
            order_type=side.upper(),
            volume=qty,
            price=limit_price
        )
        
        return Order(
            order_id=str(result['ticket']),
            symbol=symbol,
            qty=qty,
            side=side,
            order_type=order_type,
            status='filled' if result.get('success') else 'rejected',
            filled_qty=qty if result.get('success') else 0,
            avg_fill_price=limit_price
        )
    
    def close_position(self, symbol: str) -> Order:
        position = self.get_position(symbol)
        if not position:
            raise ValueError(f"No position found for {symbol}")
        
        # Close by placing opposite order
        side = 'sell' if position.side == 'long' else 'buy'
        return self.place_order(symbol, position.qty, side)
    
    def get_historical_prices(
        self,
        symbol: str,
        timeframe: str = "H1",
        limit: int = 100
    ) -> List[HistoricalBar]:
        data = self.connector.get_market_data(symbol, timeframe, limit)
        
        if not data or 'bars' not in data:
            return []
        
        return [
            HistoricalBar(
                timestamp=datetime.fromisoformat(bar['time']),
                open=bar['open'],
                high=bar['high'],
                low=bar['low'],
                close=bar['close'],
                volume=bar['volume']
            )
            for bar in data['bars']
        ]
    
    def get_current_price(self, symbol: str) -> float:
        symbol_info = self.connector.get_symbol_info(symbol)
        return float(symbol_info['bid'])
    
    def cancel_order(self, order_id: str) -> bool:
        # MT5 uses ticket numbers
        return self.connector.close_position(int(order_id))
    
    def get_broker_name(self) -> str:
        return "mt5"


# ============================================================
# BROKER FACTORY
# ============================================================

def create_broker_client(broker_name: str) -> BrokerClient:
    """
    Factory function to create the right broker client
    
    Args:
        broker_name: 'alpaca', 'mt5', 'ibkr', or 'webull'
    
    Returns:
        BrokerClient implementation
    
    Example:
        broker = create_broker_client('alpaca')
        equity = broker.get_equity()
    """
    broker_name = broker_name.lower()
    
    if broker_name == 'alpaca':
        return AlpacaBrokerClient()
    elif broker_name == 'mt5':
        return MT5BrokerClient()
    elif broker_name == 'ibkr':
        # TODO: Implement IBKRBrokerClient
        raise NotImplementedError("IBKR broker client coming soon")
    elif broker_name == 'webull':
        # TODO: Implement WebullBrokerClient
        raise NotImplementedError("Webull broker client coming soon")
    else:
        raise ValueError(f"Unknown broker: {broker_name}")
