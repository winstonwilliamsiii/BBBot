# Discord Trade Notifications

**Status**: ⚠️ **NOT YET INTEGRATED** - Code exists but not active in production  
**Priority**: HIGH - Recommended for real-time trade monitoring  
**Last Updated**: February 15, 2026

---

## 📋 Current Status

### What Exists
✅ Discord notification function is implemented in:
- **File**: [`frontend/utils/discord_alpaca.py`](../frontend/utils/discord_alpaca.py)
- **Function**: `send_discord_trade_notification()`
- **Testing**: Works in [`tests/test_alpaca_connection.py`](../tests/test_alpaca_connection.py)

### What's Missing
❌ **Not integrated** into production trading scripts:
- `place_turb_supx_orders.py` - TURB/SUPX order placement
- `fix_supx_protection.py` - SUPX protection orders
- Any other live trading scripts

---

## 🔧 Setup Instructions

### 1. Get Discord Webhook URL

1. Go to your Discord server
2. Navigate to **Server Settings** > **Integrations** > **Webhooks**
3. Click **New Webhook** or use existing one
4. Copy the webhook URL
5. Add to your `.env` file:

```bash
DISCORD_ALPACA_WEBHOOK=https://discord.com/api/webhooks/YOUR_WEBHOOK_URL_HERE
```

### 2. Test Discord Integration

```bash
# Test with test script (already has Discord integration)
python tests/test_alpaca_connection.py
```

### 3. Expected Notification Format

When working, Discord will receive:

**Trade Executed**
```
🟢 Alpaca Trade: BUY TURB
Order Type: limit
Qty: 2000
Limit Price: $0.6881
Status: new
```

**Sell Notifications**
```
🔴 Alpaca Trade: SELL SUPX
Order Type: stop
Qty: 167
Limit Price: $17.69
Status: filled
```

---

## 🚀 Integration Guide

### Adding Discord to `place_turb_supx_orders.py`

After each successful order placement, add:

```python
# After TURB order placement
if turb_order:
    print(f"\n✅ TURB order placed successfully!")
    # ... existing code ...
    
    # ADD THIS: Send Discord notification
    try:
        from frontend.utils.discord_alpaca import send_discord_trade_notification
        sent = send_discord_trade_notification(
            symbol=turb_symbol,
            side="buy",
            qty=turb_qty,
            order_type=order_type,
            limit_price=turb_entry,
            status=turb_order.get('status')
        )
        if sent:
            print("   📱 Discord notification sent")
    except Exception as e:
        print(f"   ⚠️  Discord notification failed: {e}")
```

### For SUPX Stop Loss Orders

```python
if stop_order:
    print(f"   ✅ Stop loss order placed: ${supx_stop_loss:.2f}")
    
    # ADD THIS: Send Discord notification
    try:
        from frontend.utils.discord_alpaca import send_discord_trade_notification
        send_discord_trade_notification(
            symbol="SUPX",
            side="sell",
            qty=supx_qty,
            order_type="stop",
            limit_price=supx_stop_loss,
            status=stop_order.get('status')
        )
        print("   📱 Discord notification sent")
    except Exception as e:
        print(f"   ⚠️  Discord notification failed: {e}")
```

### For SUPX Take Profit Orders

```python
if profit_order:
    print(f"   ✅ Take profit order placed: ${supx_take_profit:.2f}")
    
    # ADD THIS: Send Discord notification
    try:
        from frontend.utils.discord_alpaca import send_discord_trade_notification
        send_discord_trade_notification(
            symbol="SUPX",
            side="sell",
            qty=supx_qty,
            order_type="limit",
            limit_price=supx_take_profit,
            status=profit_order.get('status')
        )
        print("   📱 Discord notification sent")
    except Exception as e:
        print(f"   ⚠️  Discord notification failed: {e}")
```

---

## 🎯 When Notifications Trigger

With proper integration, you'll receive Discord notifications for:

### TURB Trade
1. ✅ **Order Placed** - When limit order is submitted
2. ✅ **Order Filled** - When TURB buy executes at $0.6881
3. ✅ **Stop Loss Triggered** - If price drops to stop level
4. ✅ **Take Profit Triggered** - If price reaches profit target

### SUPX Trade
1. ✅ **Protection Orders Placed** - Stop loss and take profit orders submitted
2. ✅ **Stop Loss Triggered** - If SUPX drops 10%
3. ✅ **Take Profit Triggered** - If SUPX rises 20%

---

## 🔍 Troubleshooting

### Notifications Not Received

**Check 1: Webhook URL configured**
```bash
# In PowerShell
$env:DISCORD_ALPACA_WEBHOOK
```

**Check 2: Test the webhook directly**
```python
import requests
import os
from dotenv import load_dotenv

load_dotenv()
webhook = os.getenv('DISCORD_ALPACA_WEBHOOK')

if webhook:
    payload = {"content": "Test notification from Bentley Bot"}
    response = requests.post(webhook, json=payload)
    print(f"Status: {response.status_code}")
else:
    print("❌ DISCORD_ALPACA_WEBHOOK not found in .env")
```

**Check 3: Discord server permissions**
- Ensure the webhook hasn't been deleted
- Verify you have permission to post in that channel

---

## 📊 Benefits of Discord Integration

1. **Real-Time Alerts** - Get instant notifications on your phone/desktop
2. **Trade Confirmation** - Verify orders executed as expected
3. **Stop Loss Monitoring** - Immediate notification if protective stops trigger
4. **Historical Record** - Discord messages create a searchable trade log
5. **Multi-Device Access** - View notifications on any device with Discord

---

## 🔒 Security Considerations

⚠️ **IMPORTANT**: Keep your webhook URL private!

- ✅ Store in `.env` file (not committed to git)
- ❌ Never share webhook URL publicly
- ✅ Use separate webhooks for paper vs. live trading
- ✅ Regenerate webhook if accidentally exposed

---

## 📝 Next Steps

To fully implement Discord notifications:

1. ✅ Add `DISCORD_ALPACA_WEBHOOK` to `.env` file
2. ⚠️ Update `place_turb_supx_orders.py` with notification calls (see Integration Guide above)
3. ⚠️ Update any other trading scripts that place orders
4. ✅ Test with paper trading orders first
5. ✅ Verify notifications appear in Discord

---

## 💡 Future Enhancements

Consider adding:
- Order cancellation notifications
- Position update summaries  
- Daily P&L reports
- Error alerts for failed orders
- Webhook for paper vs. live trading (separate channels)

---

## 📚 Related Files

- [`frontend/utils/discord_alpaca.py`](../frontend/utils/discord_alpaca.py) - Discord notification function
- [`tests/test_alpaca_connection.py`](../tests/test_alpaca_connection.py) - Example implementation
- [`place_turb_supx_orders.py`](place_turb_supx_orders.py) - Needs integration
- [`.env.example`](../.env.example) - Environment variable template
