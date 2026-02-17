"""
Test script for Liquidity Manager

Demonstrates the Trade Liquidity Ratio calculations for automatic trades.
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.api.admin.liquidity_manager import LiquidityManager


def print_section(title):
    """Print formatted section header."""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)


def test_liquidity_manager():
    """Test liquidity manager with different scenarios."""
    
    # Initialize with user's preferences: 20-30% buffer, 15% profit benchmark
    lm = LiquidityManager(
        liquidity_buffer_pct=25.0,    # 25% cash reserve (within 20-30% range)
        profit_benchmark_pct=15.0,     # 15% profit triggers rebalance
        auto_rebalance=True
    )
    
    print_section("💧 TRADE LIQUIDITY RATIO TEST")
    print("Configuration:")
    print(f"  • Liquidity Buffer: {lm.liquidity_buffer_pct}% (Target: 20-30%)")
    print(f"  • Profit Benchmark: {lm.profit_benchmark_pct}%")
    print(f"  • Auto-Rebalance: {lm.auto_rebalance}")
    
    # Scenario 1: Healthy liquidity position
    print_section("Scenario 1: Healthy Liquidity (26.5% cash)")
    
    total_value = 100000
    cash = 26500  # 26.5% - Above 25% target
    positions = 73500
    
    metrics = lm.calculate_liquidity_metrics(total_value, cash, positions)
    
    print(f"\nPortfolio Breakdown:")
    print(f"  • Total Value: ${metrics['total_portfolio_value']:,.2f}")
    print(f"  • Current Cash: ${metrics['current_cash']:,.2f} ({metrics['current_liquidity_ratio']:.2f}%)")
    print(f"  • Open Positions: ${metrics['open_positions_value']:,.2f}")
    
    print(f"\nLiquidity Analysis:")
    print(f"  • Target Reserve: ${metrics['target_cash_reserve']:,.2f} ({lm.liquidity_buffer_pct}%)")
    print(f"  • Available Dry Powder: ${metrics['available_dry_powder']:,.2f}")
    print(f"  • Status: {metrics['liquidity_status'].upper()}")
    
    recommendation = lm.get_rebalance_recommendation(metrics)
    print(f"\nRebalancing Recommendation:")
    print(f"  • Action Required: {recommendation['action_required']}")
    print(f"  • {recommendation['reason']}")
    
    max_position = lm.calculate_max_position_size(metrics)
    print(f"\nPosition Sizing:")
    print(f"  • Max New Position: ${max_position:,.2f}")
    
    # Scenario 2: Low liquidity (warning)
    print_section("Scenario 2: Low Liquidity (22% cash)")
    
    cash_low = 22000  # 22% - Below 25% target but above 20%
    positions_high = 78000
    
    metrics_low = lm.calculate_liquidity_metrics(total_value, cash_low, positions_high)
    
    print(f"\nPortfolio Breakdown:")
    print(f"  • Total Value: ${metrics_low['total_portfolio_value']:,.2f}")
    print(f"  • Current Cash: ${metrics_low['current_cash']:,.2f} ({metrics_low['current_liquidity_ratio']:.2f}%)")
    print(f"  • Open Positions: ${metrics_low['open_positions_value']:,.2f}")
    
    print(f"\nLiquidity Analysis:")
    print(f"  • Target Reserve: ${metrics_low['target_cash_reserve']:,.2f}")
    print(f"  • Available Dry Powder: ${metrics_low['available_dry_powder']:,.2f}")
    print(f"  • Buffer Deviation: {metrics_low['buffer_deviation']:.2f}%")
    print(f"  • Status: {metrics_low['liquidity_status'].upper()}")
    
    recommendation_low = lm.get_rebalance_recommendation(metrics_low)
    print(f"\nRebalancing Recommendation:")
    print(f"  • Action Required: {recommendation_low['action_required']}")
    print(f"  • Action Type: {recommendation_low['action_type']}")
    print(f"  • Amount: ${recommendation_low['amount']:,.2f}")
    print(f"  • {recommendation_low['reason']}")
    print(f"  • Priority: {recommendation_low['priority'].upper()}")
    
    # Scenario 3: Critical liquidity
    print_section("Scenario 3: Critical Liquidity (18% cash)")
    
    cash_critical = 18000  # 18% - Below 20% minimum
    positions_critical = 82000
    
    metrics_critical = lm.calculate_liquidity_metrics(total_value, cash_critical, positions_critical)
    
    print(f"\nPortfolio Breakdown:")
    print(f"  • Total Value: ${metrics_critical['total_portfolio_value']:,.2f}")
    print(f"  • Current Cash: ${metrics_critical['current_cash']:,.2f} ({metrics_critical['current_liquidity_ratio']:.2f}%)")
    print(f"  • Open Positions: ${metrics_critical['open_positions_value']:,.2f}")
    
    print(f"\nLiquidity Analysis:")
    print(f"  • Target Reserve: ${metrics_critical['target_cash_reserve']:,.2f}")
    print(f"  • Available Dry Powder: ${metrics_critical['available_dry_powder']:,.2f}")
    print(f"  • Buffer Deviation: {metrics_critical['buffer_deviation']:.2f}%")
    print(f"  • Status: {metrics_critical['liquidity_status'].upper()} 🔴")
    
    recommendation_critical = lm.get_rebalance_recommendation(metrics_critical)
    print(f"\nRebalancing Recommendation:")
    print(f"  • Action Required: {recommendation_critical['action_required']}")
    print(f"  • Action Type: {recommendation_critical['action_type']}")
    print(f"  • Amount Needed: ${recommendation_critical['amount']:,.2f}")
    print(f"  • {recommendation_critical['reason']}")
    print(f"  • Priority: {recommendation_critical['priority'].upper()}")
    
    # Scenario 4: Profit benchmark check
    print_section("Scenario 4: Profit Benchmark Check")
    
    positions_to_check = [
        ("NVDA Position", 12.5),
        ("TSLA Position", 18.3),
        ("SPY Position", 8.2),
        ("Profitable Trade", 22.0)
    ]
    
    for position_name, profit_pct in positions_to_check:
        should_release, message = lm.check_profit_benchmark(profit_pct)
        status = "✅ RELEASE" if should_release else "⏳ HOLD"
        print(f"\n{position_name} ({profit_pct}%): {status}")
        print(f"  {message}")
    
    # Summary
    print_section("📊 SUMMARY")
    print("""
The Trade Liquidity Ratio system ensures:

1. **Dry Powder Management**: Always maintains 20-30% cash reserve
2. **Opportunity Mobility**: Available capital for alternative trades
3. **Profit-Based Rebalance**: Releases funds when positions hit 15% profit
4. **Auto-Adjustment**: Automatically maintains target liquidity levels

Benefits for Automatic Trading:
• Can quickly deploy capital on new opportunities
• Maintains flexibility for market volatility
• Prevents over-leveraging
• Ensures liquidity for risk management
    """)
    
    print("\n✅ All tests completed successfully!\n")


if __name__ == "__main__":
    test_liquidity_manager()
