# Trade Liquidity Ratio System

## Overview

The **Trade Liquidity Ratio** is a risk management system designed to maintain optimal cash reserves ("dry powder") for automatic trading while ensuring portfolio mobility to capitalize on alternative opportunities.

## 🎯 Purpose

Ensures your automated trading system:
- ✅ Always has 20-30% cash available for new opportunities
- ✅ Prevents over-deployment that locks up capital
- ✅ Automatically rebalances when profits reach benchmarks
- ✅ Provides real-time visibility into available "dry powder"

## 📊 Key Metrics

### 1. **Trade Liquidity Ratio**
- **What it is**: Current cash balance as a percentage of total portfolio value
- **Target**: 20-30% (configurable)
- **Formula**: `(Current Cash / Total Portfolio Value) × 100`

### 2. **Available Dry Powder**
- **What it is**: Capital available for immediate deployment on new trades
- **Formula**: `max(0, Current Cash - Target Cash Reserve)`
- **Example**: If you have $26,500 cash and target is $25,000 → **$1,500 available**

### 3. **Profit Benchmark**
- **What it is**: Profit percentage that triggers reallocation to liquidity pool
- **Default**: 15%
- **Purpose**: When positions hit this target, consider taking profits to replenish dry powder

## ⚙️ Configuration

### Default Settings (Configurable in Admin Console)

```python
liquidity_buffer_pct = 25.0      # 25% cash reserve (within 20-30% recommended range)
profit_benchmark_pct = 15.0      # 15% profit triggers liquidity release consideration
auto_rebalance = True            # Automatically maintain liquidity buffer
```

### How to Adjust Settings

#### Via Admin Console UI:
1. Navigate to **Admin Control Center** → **Risk Management** tab
2. Scroll to **Liquidity & Dry Powder Management** section
3. Adjust sliders:
   - **Cash Reserve Buffer**: 20-30% recommended
   - **Profit Benchmark**: Your profit target for rebalancing
   - **Auto-rebalance**: Enable/disable automatic adjustment

#### Via API:
```bash
curl -X POST http://localhost:5000/admin/liquidity \
  -H "Content-Type: application/json" \
  -d '{
    "liquidity_buffer_pct": 25.0,
    "profit_benchmark_pct": 15.0,
    "auto_rebalance": true
  }'
```

## 🔄 How It Works

### Automatic Trading Workflow

1. **Pre-Trade Check**
   - System calculates available dry powder
   - Ensures new position doesn't violate liquidity buffer
   - Calculates max position size: `min(Available Dry Powder, Position Size Limit)`

2. **During Trade Execution**
   - Monitors cash reserves in real-time
   - Tracks liquidity ratio against target
   - Triggers alerts if approaching minimum threshold

3. **Post-Trade Management**
   - Checks position profits against benchmark
   - When profit hits 15%, recommends reallocation
   - Auto-rebalances if enabled to maintain target buffer

### Liquidity Status Levels

| Status | Liquidity Ratio | Action |
|--------|----------------|--------|
| **Healthy** ✅ | ≥ Target (25%) | Normal operations, dry powder available |
| **Warning** ⚠️ | Target - 5% to Target (20-25%) | Reduce new positions, consider closing profitable trades |
| **Critical** 🔴 | < Target - 5% (< 20%) | Immediate rebalancing required, halt new positions |

## 📈 Example Scenarios

### Scenario 1: Healthy Liquidity (26.5% cash)

```
Portfolio Value: $100,000
Current Cash: $26,500 (26.5%)
Target Buffer: $25,000 (25%)
Available Dry Powder: $1,500

Status: ✅ HEALTHY
Action: Can deploy up to $1,500 on new opportunities
```

### Scenario 2: Low Liquidity (22% cash)

```
Portfolio Value: $100,000
Current Cash: $22,000 (22%)
Target Buffer: $25,000 (25%)
Available Dry Powder: $0

Status: ⚠️ WARNING
Action: Need to raise $3,000 → Close profitable positions or reduce exposure
```

### Scenario 3: Critical Liquidity (18% cash)

```
Portfolio Value: $100,000
Current Cash: $18,000 (18%)
Target Buffer: $25,000 (25%)
Deficit: $7,000

Status: 🔴 CRITICAL
Action: Immediately close positions worth $7,000 to restore buffer
Priority: HIGH
```

## 🎮 Usage Guide

### For Automatic Trading Bots

```python
from backend.api.admin.liquidity_manager import LiquidityManager

# Initialize
lm = LiquidityManager(
    liquidity_buffer_pct=25.0,
    profit_benchmark_pct=15.0,
    auto_rebalance=True
)

# Before placing a trade
metrics = lm.calculate_liquidity_metrics(
    total_portfolio_value=100000,
    current_cash=26500,
    open_positions_value=73500
)

# Check available dry powder
available = metrics['available_dry_powder']
print(f"Can deploy: ${available:,.2f}")

# Calculate safe position size
max_position = lm.calculate_max_position_size(metrics)
print(f"Max position size: ${max_position:,.2f}")

# After trade execution, check if rebalancing needed
recommendation = lm.get_rebalance_recommendation(metrics)
if recommendation['action_required']:
    print(f"⚠️ {recommendation['reason']}")
    print(f"Action: {recommendation['action_type']}")
```

### For Manual Position Management

```python
# Check if a position should be closed for liquidity
should_release, message = lm.check_profit_benchmark(
    position_profit_pct=18.5
)

if should_release:
    print(f"✅ Position reached 15% profit benchmark")
    print(f"Consider closing to replenish dry powder")
```

## 🌐 API Endpoints

### GET /admin/liquidity

Get current liquidity metrics.

**Query Parameters:**
- `total_value` (optional): Total portfolio value
- `current_cash` (optional): Current cash balance
- `positions_value` (optional): Value of open positions

**Response:**
```json
{
  "status": "success",
  "metrics": {
    "total_portfolio_value": 100000,
    "current_cash": 26500,
    "current_liquidity_ratio": 26.5,
    "target_cash_reserve": 25000,
    "available_dry_powder": 1500,
    "liquidity_status": "healthy"
  },
  "recommendation": {
    "action_required": false,
    "reason": "Liquidity within healthy range"
  },
  "max_position_size": 1500
}
```

### POST /admin/liquidity

Update liquidity settings.

**Request Body:**
```json
{
  "liquidity_buffer_pct": 25.0,
  "profit_benchmark_pct": 15.0,
  "auto_rebalance": true
}
```

### POST /admin/liquidity/check-profit

Check if position profit has reached benchmark.

**Request Body:**
```json
{
  "position_profit_pct": 18.5
}
```

**Response:**
```json
{
  "status": "success",
  "should_release": true,
  "message": "Position profit (18.50%) has reached benchmark (15.00%)",
  "current_profit": 18.5,
  "benchmark": 15.0
}
```

## 🧪 Testing

Run the test script to see the system in action:

```bash
python tests/manual/test_liquidity_ratio.py
```

This demonstrates:
- ✅ Healthy liquidity calculations
- ⚠️ Warning state handling
- 🔴 Critical liquidity response
- 📊 Profit benchmark checks
- 🔄 Rebalancing recommendations

## 📱 Admin Console Integration

Access the Trade Liquidity Ratio dashboard at:

**Admin Control Center → Risk Management Tab → Liquidity & Dry Powder Management**

Features:
- 📊 Real-time liquidity ratio display
- 💰 Available dry powder calculation
- ⚙️ Configurable buffer and benchmark settings
- 📈 Visual health indicators
- 🔔 Automatic rebalancing recommendations

## 🎯 Best Practices

### For Automatic Trading

1. **Set Conservative Buffers**
   - Use 25-30% for volatile markets
   - Use 20-25% for stable markets
   - Never go below 20%

2. **Adjust Profit Benchmarks**
   - Higher benchmarks (20-25%) for momentum strategies
   - Lower benchmarks (10-15%) for mean reversion
   - Match to your trading style

3. **Monitor Daily**
   - Check liquidity status each morning
   - Review dry powder before market open
   - Ensure buffer is maintained

4. **Rebalance Proactively**
   - Don't wait for critical warnings
   - Close profitable positions when warned
   - Maintain discipline on buffer targets

### For Portfolio Management

1. **Opportunistic Deployment**
   - Keep dry powder ready for market dips
   - Size positions based on available liquidity
   - Don't force trades when buffer is low

2. **Profit Taking**
   - Use 15% benchmark as minimum
   - Scale out of winners to replenish reserves
   - Reinvest only when liquidity is healthy

3. **Risk Management**
   - Link liquidity to overall risk limits
   - Reduce exposure if buffer drops
   - Use auto-rebalance for peace of mind

## 🔗 Integration Points

### With Existing Systems

- **Alpaca/Schwab/MT5**: Check liquidity before order placement
- **Risk Engine**: Incorporate into pre-trade checks
- **Monitoring**: Alert on liquidity violations
- **Reporting**: Include in daily portfolio summaries

### With MLflow

Track liquidity metrics alongside model performance:
```python
import mlflow

mlflow.log_metric("liquidity_ratio", metrics['current_liquidity_ratio'])
mlflow.log_metric("dry_powder", metrics['available_dry_powder'])
mlflow.log_metric("buffer_deviation", metrics['buffer_deviation'])
```

## 📚 Related Documentation

- [Risk Management Guide](trades/TRADING_PARAMETERS.md)
- [Admin Console Guide](docs/CONTROL_CENTER_ADMIN_UI_GUIDE.md)
- [Trading Parameters](trades/TRADING_PARAMETERS.md)

## 🆘 Troubleshooting

### Issue: Liquidity always shows as critical

**Solution**: Check if target buffer is too high for your trading style. Consider:
- Reducing `liquidity_buffer_pct` to 20%
- Closing some positions to raise cash
- Depositing additional capital

### Issue: No dry powder available

**Solution**: 
- Review open positions and close profitable ones
- Wait for profit benchmark to be reached
- Enable auto-rebalance to maintain buffer automatically

### Issue: API returns errors

**Solution**:
- Ensure the FastAPI control center is running: `powershell -ExecutionPolicy Bypass -File .\start_control_center_api.ps1`
- Check the backend health endpoint: `http://localhost:5001/health`
- Verify portfolio values are positive numbers

## 📞 Support

For questions or issues with the Trade Liquidity Ratio system:
1. Check this documentation
2. Run `tests/manual/test_liquidity_ratio.py` to verify functionality
3. Review Admin Console Risk Management tab
4. Check API endpoints with `curl http://localhost:5000/admin/liquidity`

---

**Last Updated**: February 16, 2026  
**Version**: 1.0.0  
**Status**: ✅ Production Ready
