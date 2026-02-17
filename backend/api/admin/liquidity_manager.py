"""
Liquidity Manager for Automatic Trade Deployment

Manages portfolio liquidity, dry powder calculations, and profit-based
rebalancing to maintain optimal cash reserves for opportunity capture.
"""

from typing import Dict, Tuple, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class LiquidityManager:
    """
    Manages trade liquidity ratios and dry powder calculations.
    
    Features:
    - Cash reserve buffer management (default 20-30%)
    - Profit benchmark tracking for liquidity release
    - Available dry powder calculation
    - Auto-rebalance recommendations
    """
    
    def __init__(
        self,
        liquidity_buffer_pct: float = 25.0,
        profit_benchmark_pct: float = 15.0,
        auto_rebalance: bool = True
    ):
        """
        Initialize liquidity manager.
        
        Args:
            liquidity_buffer_pct: Target cash reserve % (default 25%)
            profit_benchmark_pct: Profit % to trigger liquidity release (default 15%)
            auto_rebalance: Enable automatic rebalancing
        """
        self.liquidity_buffer_pct = liquidity_buffer_pct
        self.profit_benchmark_pct = profit_benchmark_pct
        self.auto_rebalance = auto_rebalance
        
        # Recommended range for liquidity buffer
        self.min_recommended_buffer = 20.0
        self.max_recommended_buffer = 30.0
    
    def calculate_liquidity_metrics(
        self,
        total_portfolio_value: float,
        current_cash: float,
        open_positions_value: float
    ) -> Dict[str, float]:
        """
        Calculate comprehensive liquidity metrics.
        
        Args:
            total_portfolio_value: Total portfolio value in USD
            current_cash: Current cash balance in USD
            open_positions_value: Total value of open positions in USD
        
        Returns:
            Dictionary with liquidity metrics
        """
        # Calculate current liquidity ratio
        current_liquidity_ratio = (current_cash / total_portfolio_value * 100) if total_portfolio_value > 0 else 0
        
        # Calculate target cash reserve
        target_cash_reserve = total_portfolio_value * (self.liquidity_buffer_pct / 100)
        
        # Calculate available dry powder
        available_dry_powder = max(0, current_cash - target_cash_reserve)
        
        # Calculate utilization rate
        utilization_rate = (open_positions_value / total_portfolio_value * 100) if total_portfolio_value > 0 else 0
        
        # Calculate buffer deviation
        buffer_deviation = current_liquidity_ratio - self.liquidity_buffer_pct
        
        metrics = {
            "total_portfolio_value": total_portfolio_value,
            "current_cash": current_cash,
            "current_liquidity_ratio": current_liquidity_ratio,
            "target_liquidity_buffer": self.liquidity_buffer_pct,
            "target_cash_reserve": target_cash_reserve,
            "available_dry_powder": available_dry_powder,
            "open_positions_value": open_positions_value,
            "utilization_rate": utilization_rate,
            "buffer_deviation": buffer_deviation,
            "liquidity_status": self._get_liquidity_status(buffer_deviation),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return metrics
    
    def _get_liquidity_status(self, buffer_deviation: float) -> str:
        """
        Determine liquidity health status.
        
        Args:
            buffer_deviation: Difference between current and target liquidity ratio
        
        Returns:
            Status string: 'healthy', 'warning', or 'critical'
        """
        if buffer_deviation >= 0:
            return "healthy"
        elif buffer_deviation >= -5:
            return "warning"
        else:
            return "critical"
    
    def check_profit_benchmark(
        self,
        position_profit_pct: float
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if position profit has reached benchmark for liquidity release.
        
        Args:
            position_profit_pct: Current profit percentage of position
        
        Returns:
            Tuple of (should_release, recommendation_message)
        """
        if position_profit_pct >= self.profit_benchmark_pct:
            message = (
                f"✅ Position profit ({position_profit_pct:.2f}%) has reached benchmark "
                f"({self.profit_benchmark_pct:.2f}%). Consider reallocating to liquidity pool."
            )
            return True, message
        else:
            remaining = self.profit_benchmark_pct - position_profit_pct
            message = (
                f"Position profit ({position_profit_pct:.2f}%) is {remaining:.2f}% "
                f"below benchmark ({self.profit_benchmark_pct:.2f}%)."
            )
            return False, message
    
    def get_rebalance_recommendation(
        self,
        metrics: Dict[str, float]
    ) -> Dict[str, any]:
        """
        Generate rebalancing recommendations based on liquidity metrics.
        
        Args:
            metrics: Liquidity metrics from calculate_liquidity_metrics()
        
        Returns:
            Dictionary with rebalancing recommendations
        """
        buffer_deviation = metrics["buffer_deviation"]
        available_dry_powder = metrics["available_dry_powder"]
        current_cash = metrics["current_cash"]
        target_cash_reserve = metrics["target_cash_reserve"]
        
        recommendation = {
            "action_required": False,
            "action_type": None,
            "amount": 0,
            "reason": "",
            "priority": "low"
        }
        
        # Scenario 1: Below minimum buffer (critical)
        if buffer_deviation < -5:
            deficit = target_cash_reserve - current_cash
            recommendation.update({
                "action_required": True,
                "action_type": "CLOSE_POSITIONS",
                "amount": deficit,
                "reason": f"Liquidity critically low. Need ${deficit:,.2f} to reach minimum buffer.",
                "priority": "high"
            })
        
        # Scenario 2: Below target buffer (warning)
        elif buffer_deviation < 0:
            deficit = target_cash_reserve - current_cash
            recommendation.update({
                "action_required": True if self.auto_rebalance else False,
                "action_type": "REDUCE_POSITIONS",
                "amount": deficit,
                "reason": f"Approaching liquidity minimum. Consider raising ${deficit:,.2f}.",
                "priority": "medium"
            })
        
        # Scenario 3: Excess liquidity (opportunity to deploy)
        elif available_dry_powder > (target_cash_reserve * 0.2):  # >20% excess
            recommendation.update({
                "action_required": False,
                "action_type": "DEPLOY_CAPITAL",
                "amount": available_dry_powder * 0.5,  # Deploy 50% of excess
                "reason": f"Excess liquidity detected. ${available_dry_powder:,.2f} available for deployment.",
                "priority": "low"
            })
        
        # Scenario 4: Healthy range
        else:
            recommendation.update({
                "reason": "Liquidity within healthy range. No action needed.",
                "priority": "low"
            })
        
        return recommendation
    
    def calculate_max_position_size(
        self,
        metrics: Dict[str, float],
        max_position_pct: float = 10.0
    ) -> float:
        """
        Calculate maximum position size while maintaining liquidity buffer.
        
        Args:
            metrics: Liquidity metrics from calculate_liquidity_metrics()
            max_position_pct: Maximum position size as % of portfolio (default 10%)
        
        Returns:
            Maximum position size in USD
        """
        total_value = metrics["total_portfolio_value"]
        available_dry_powder = metrics["available_dry_powder"]
        
        # Can't exceed available dry powder
        max_from_liquidity = available_dry_powder
        
        # Can't exceed position size limit
        max_from_position_limit = total_value * (max_position_pct / 100)
        
        # Return the smaller of the two constraints
        max_position = min(max_from_liquidity, max_from_position_limit)
        
        logger.info(
            f"Max position size: ${max_position:,.2f} "
            f"(Liquidity: ${max_from_liquidity:,.2f}, Limit: ${max_from_position_limit:,.2f})"
        )
        
        return max_position
    
    def get_liquidity_summary(
        self,
        metrics: Dict[str, float]
    ) -> str:
        """
        Generate human-readable liquidity summary.
        
        Args:
            metrics: Liquidity metrics from calculate_liquidity_metrics()
        
        Returns:
            Formatted summary string
        """
        status_emoji = {
            "healthy": "✅",
            "warning": "⚠️",
            "critical": "🔴"
        }
        
        status = metrics["liquidity_status"]
        emoji = status_emoji.get(status, "❓")
        
        summary = f"""
{emoji} Liquidity Status: {status.upper()}

Portfolio Overview:
- Total Value: ${metrics['total_portfolio_value']:,.2f}
- Current Cash: ${metrics['current_cash']:,.2f} ({metrics['current_liquidity_ratio']:.2f}%)
- Target Buffer: {self.liquidity_buffer_pct}% (${metrics['target_cash_reserve']:,.2f})

Dry Powder:
- Available for Deployment: ${metrics['available_dry_powder']:,.2f}
- Open Positions: ${metrics['open_positions_value']:,.2f} ({metrics['utilization_rate']:.2f}%)

Configuration:
- Liquidity Buffer: {self.liquidity_buffer_pct}%
- Profit Benchmark: {self.profit_benchmark_pct}%
- Auto-Rebalance: {'Enabled' if self.auto_rebalance else 'Disabled'}
        """
        
        return summary.strip()


# Example usage
if __name__ == "__main__":
    # Initialize liquidity manager with default settings
    lm = LiquidityManager(
        liquidity_buffer_pct=25.0,    # 25% cash reserve
        profit_benchmark_pct=15.0,     # 15% profit triggers rebalance
        auto_rebalance=True
    )
    
    # Example portfolio
    total_value = 100000
    cash = 26500
    positions = 73500
    
    # Calculate metrics
    metrics = lm.calculate_liquidity_metrics(total_value, cash, positions)
    
    # Print summary
    print(lm.get_liquidity_summary(metrics))
    
    # Get rebalancing recommendation
    recommendation = lm.get_rebalance_recommendation(metrics)
    print(f"\nRecommendation: {recommendation['reason']}")
    
    # Calculate max position size
    max_position = lm.calculate_max_position_size(metrics)
    print(f"\nMax Position Size: ${max_position:,.2f}")
    
    # Check profit benchmark for a position
    should_release, message = lm.check_profit_benchmark(18.5)
    print(f"\nProfit Check: {message}")
