"""
ML Integration Helper for Bentley Budget Bot Vercel Frontend
Place in your ML/training directory for easy integration

Example usage:
    from vercel_integration import record_metrics, get_metrics
    
    # After training your model
    metrics = {
        'accuracy': 0.92,
        'sharpe_ratio': 1.45,
        'win_rate': 0.70
    }
    
    response = record_metrics(
        user_id='user123',
        bot_id='ml_bot_v1',
        experiment_id='exp_001',
        metrics=metrics
    )
    print(f"Metrics recorded: {response}")
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional

# Configuration
VERCEL_API_BASE = "https://your-vercel-domain.com"  # Update with your domain!
DEFAULT_DATA_SOURCE = "yfinance"

class VercelMetricsClient:
    """Client for communicating with Vercel API routes"""
    
    def __init__(self, base_url: str = VERCEL_API_BASE):
        """
        Initialize the Vercel metrics client
        
        Args:
            base_url: Your Vercel deployment URL (e.g., https://bentley-bot.vercel.app)
        """
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        
    def health_check(self) -> Dict[str, Any]:
        """Check if Vercel API is healthy"""
        try:
            response = self.session.get(f"{self.base_url}/api/health")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"status": "error", "message": str(e)}
    
    def record_metrics(
        self,
        user_id: str,
        bot_id: str,
        metrics: Dict[str, float],
        experiment_id: Optional[str] = None,
        data_source: str = DEFAULT_DATA_SOURCE,
        status: str = "completed",
        notes: str = ""
    ) -> Dict[str, Any]:
        """
        Record bot metrics to Vercel API
        
        Args:
            user_id: Your user ID
            bot_id: Bot/model identifier
            metrics: Dictionary of metrics (e.g., {'accuracy': 0.92, 'sharpe_ratio': 1.5})
            experiment_id: Optional experiment ID (generated if not provided)
            data_source: Data source (yfinance, mysql, appwrite)
            status: Experiment status (completed, failed, in_progress)
            notes: Optional notes about the experiment
            
        Returns:
            Response from API with recorded metrics
        """
        if not experiment_id:
            experiment_id = f"exp_{int(time.time())}"
        
        payload = {
            "user_id": user_id,
            "bot_id": bot_id,
            "experiment_id": experiment_id,
            "metrics": metrics,
            "data_source": data_source,
            "status": status,
            "notes": notes
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/recordBotMetrics",
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {
                "error": "Failed to record metrics",
                "message": str(e),
                "payload": payload
            }
    
    def get_metrics(
        self,
        user_id: str,
        include_stats: bool = True
    ) -> Dict[str, Any]:
        """
        Retrieve recorded metrics for a user
        
        Args:
            user_id: Your user ID
            include_stats: Whether to include aggregated stats
            
        Returns:
            Metrics data from API
        """
        try:
            params = {
                "user_id": user_id,
                "include_stats": "true" if include_stats else "false"
            }
            response = self.session.get(
                f"{self.base_url}/api/getBotMetrics",
                params=params,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {
                "error": "Failed to retrieve metrics",
                "message": str(e)
            }
    
    def create_transaction(
        self,
        user_id: str,
        symbol: str,
        quantity: float,
        price: float,
        transaction_type: str = "buy",
        transaction_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a transaction record
        
        Args:
            user_id: Your user ID
            symbol: Stock symbol (e.g., 'AAPL')
            quantity: Number of shares
            price: Price per share
            transaction_type: 'buy' or 'sell'
            transaction_date: ISO format date (defaults to now)
            
        Returns:
            Transaction response from API
        """
        if not transaction_date:
            transaction_date = datetime.now().isoformat() + 'Z'
        
        payload = {
            "user_id": user_id,
            "symbol": symbol,
            "quantity": quantity,
            "price": price,
            "type": transaction_type,
            "transaction_date": transaction_date
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/createTransaction",
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {
                "error": "Failed to create transaction",
                "message": str(e)
            }
    
    def create_payment(
        self,
        user_id: str,
        amount: float,
        currency: str = "USD",
        payment_method: str = "credit_card",
        description: str = ""
    ) -> Dict[str, Any]:
        """
        Create a payment
        
        Args:
            user_id: Your user ID
            amount: Payment amount
            currency: Currency code (default: USD)
            payment_method: Payment method (credit_card, debit_card, bank_transfer)
            description: Payment description
            
        Returns:
            Payment response from API
        """
        payload = {
            "user_id": user_id,
            "amount": amount,
            "currency": currency,
            "payment_method": payment_method,
            "description": description
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/createPayment",
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {
                "error": "Failed to create payment",
                "message": str(e)
            }


# Convenience functions
def record_metrics(
    user_id: str,
    bot_id: str,
    metrics: Dict[str, float],
    vercel_base: str = VERCEL_API_BASE,
    **kwargs
) -> Dict[str, Any]:
    """
    Quick function to record metrics
    
    Usage:
        record_metrics(
            user_id='user123',
            bot_id='ml_bot_v1',
            metrics={'accuracy': 0.92, 'sharpe_ratio': 1.5}
        )
    """
    client = VercelMetricsClient(vercel_base)
    return client.record_metrics(user_id, bot_id, metrics, **kwargs)


def get_metrics(
    user_id: str,
    vercel_base: str = VERCEL_API_BASE,
    **kwargs
) -> Dict[str, Any]:
    """Quick function to get metrics"""
    client = VercelMetricsClient(vercel_base)
    return client.get_metrics(user_id, **kwargs)


# Example usage (run this file to test)
if __name__ == "__main__":
    # Initialize client
    client = VercelMetricsClient()
    
    print("=" * 60)
    print("Testing Vercel Metrics Integration")
    print("=" * 60)
    
    # Step 1: Health check
    print("\n1. Health Check...")
    health = client.health_check()
    print(f"   Status: {health.get('status', 'unknown')}")
    
    # Step 2: Record sample metrics
    print("\n2. Recording sample metrics...")
    metrics = {
        "accuracy": 0.92,
        "sharpe_ratio": 1.45,
        "max_drawdown": -0.12,
        "total_return": 0.32,
        "win_rate": 0.68,
        "trades_executed": 52
    }
    
    result = client.record_metrics(
        user_id="test_user",
        bot_id="ml_bot_test",
        metrics=metrics,
        data_source="yfinance",
        status="completed",
        notes="Test run - integration verification"
    )
    print(f"   Result: {json.dumps(result, indent=2)}")
    
    # Step 3: Retrieve metrics
    print("\n3. Retrieving metrics...")
    metrics_data = client.get_metrics("test_user", include_stats=True)
    print(f"   Retrieved: {len(metrics_data.get('data', []))} metrics")
    
    print("\n" + "=" * 60)
    print("✅ Integration test complete!")
    print("=" * 60)
