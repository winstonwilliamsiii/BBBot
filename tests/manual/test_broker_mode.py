#!/usr/bin/env python
"""Quick test of broker mode config system."""

from config.broker_mode_config import get_config, BOT_BROKER_MAPPING

print("=" * 60)
print("🧪 Broker Mode Config System TEST")
print("=" * 60)

try:
    config = get_config()
    print("\n✅ Broker mode config loaded successfully")
    
    print(f"\n📋 Configuration Status:")
    print(f"   Global mode: {config.get_global_mode()}")
    print(f"   Supported bots: {len(BOT_BROKER_MAPPING)}")
    print(f"   Config file: {config.config_path}")
    print(f"   Config exists: {config.config_path.exists()}")
    
    print(f"\n🤖 First 5 bot-to-broker mappings:")
    for bot, broker in list(BOT_BROKER_MAPPING.items())[:5]:
        mode = config.get_broker_mode(broker)
        print(f"   {bot:12} -> {broker:8} ({mode.upper()})")
    
    print(f"\n🎮 Broker modes:")
    for broker in ["alpaca", "mt5", "axi", "ibkr"]:
        mode = config.get_broker_mode(broker)
        print(f"   {broker:10} -> {mode.upper()}")
    
    print(f"\n✅ All tests passed!")
    print("=" * 60)
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
