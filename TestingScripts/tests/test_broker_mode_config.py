"""
Tests for Broker Mode Configuration and Live/Paper Mode Switching

Tests cover:
1. Config file creation and persistence
2. Global mode changes
3. Per-broker mode overrides
4. Environment variable overrides
5. Bot status tracking
6. Mode resolver integration
7. Secrets helper integration
"""

import pytest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.broker_mode_config import (
    BrokerModeConfig,
    get_config,
    BOT_BROKER_MAPPING,
    SUPPORTED_BROKERS,
)
from frontend.utils.broker_mode_resolver import (
    get_effective_mode,
    resolve_mt5_credentials,
)


class TestBrokerModeConfig:
    """Test broker mode configuration system."""

    def test_config_creation(self):
        """Test that config file is created with defaults."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "broker_modes.json"
            config = BrokerModeConfig(config_path)

            # Verify file was created
            assert config_path.exists()

            # Verify default structure
            assert config.get_global_mode() == "paper"
            assert config.config["broker_modes"]["alpaca"] == "paper"
            assert config.config["broker_modes"]["mt5"] == "paper"

    def test_global_mode_change(self):
        """Test changing global mode."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "broker_modes.json"
            config = BrokerModeConfig(config_path)

            # Change global mode
            config.set_global_mode("live")
            assert config.get_global_mode() == "live"

            # Verify persistence
            with open(config_path, "r") as f:
                saved = json.load(f)
                assert saved["global_mode"] == "live"

    def test_broker_mode_override(self):
        """Test per-broker mode override."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "broker_modes.json"
            config = BrokerModeConfig(config_path)

            # Set global to paper, Alpaca to live
            config.set_global_mode("paper")
            config.set_broker_mode("alpaca", "live")

            assert config.get_global_mode() == "paper"
            assert config.get_broker_mode("alpaca") == "live"
            assert config.get_broker_mode("mt5") == "paper"  # Inherits global

    def test_env_var_override(self):
        """Test that environment variables override config file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "broker_modes.json"
            config = BrokerModeConfig(config_path)

            # Set config to paper
            config.set_broker_mode("alpaca", "paper")

            # Set env var to live
            with patch.dict(os.environ, {"ALPACA_MODE": "live"}):
                # Env var should take precedence
                assert config.get_broker_mode("alpaca") == "live"

    def test_bot_status_tracking(self):
        """Test bot activation/deactivation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "broker_modes.json"
            config = BrokerModeConfig(config_path)

            # All bots should start inactive
            for bot in BOT_BROKER_MAPPING.keys():
                assert config.is_bot_active(bot) == False

            # Activate Titan
            config.set_bot_active("Titan", True)
            assert config.is_bot_active("Titan") == True
            assert config.is_bot_active("Vega") == False

    def test_get_bot_mode(self):
        """Test getting effective mode for a bot."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "broker_modes.json"
            config = BrokerModeConfig(config_path)

            # Titan uses Alpaca
            assert BOT_BROKER_MAPPING["Titan"] == "alpaca"

            # Set Alpaca to live
            config.set_broker_mode("alpaca", "live")

            # Titan should report live mode
            assert config.get_bot_mode("Titan") == "live"

    def test_all_bots_status(self):
        """Test getting status of all bots."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "broker_modes.json"
            config = BrokerModeConfig(config_path)

            # Set some bots active
            config.set_bot_active("Titan", True)
            config.set_bot_active("Rigel", True)

            status = config.get_all_bots_status()

            assert len(status) == len(BOT_BROKER_MAPPING)
            assert status["Titan"]["active"] == True
            assert status["Titan"]["broker"] == "alpaca"
            assert status["Titan"]["mode"] == "paper"  # Default
            assert status["Vega"]["active"] == False

    def test_invalid_mode(self):
        """Test that invalid modes are rejected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "broker_modes.json"
            config = BrokerModeConfig(config_path)

            with pytest.raises(ValueError):
                config.set_global_mode("invalid")

            with pytest.raises(ValueError):
                config.set_broker_mode("alpaca", "invalid")

    def test_invalid_broker(self):
        """Test that invalid brokers are rejected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "broker_modes.json"
            config = BrokerModeConfig(config_path)

            with pytest.raises(ValueError):
                config.set_broker_mode("invalid_broker", "paper")

    def test_invalid_bot(self):
        """Test that invalid bots are rejected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "broker_modes.json"
            config = BrokerModeConfig(config_path)

            with pytest.raises(ValueError):
                config.set_bot_active("InvalidBot", True)


class TestBrokerModeResolver:
    """Test broker mode resolver utilities."""

    def test_get_effective_mode_default(self):
        """Test getting effective mode with default config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "broker_modes.json"

            with patch("config.broker_mode_config.CONFIG_FILE", config_path):
                BrokerModeConfig(config_path)  # Create default config

                # Should default to paper
                with patch(
                    "frontend.utils.broker_mode_resolver.get_config",
                    return_value=BrokerModeConfig(config_path),
                ):
                    assert get_effective_mode("alpaca") == "paper"

    def test_get_effective_mode_with_env_override(self):
        """Test that env vars override config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "broker_modes.json"
            config = BrokerModeConfig(config_path)

            with patch(
                "frontend.utils.broker_mode_resolver.get_config",
                return_value=config,
            ):
                with patch.dict(os.environ, {"ALPACA_MODE": "live"}):
                    assert get_effective_mode("alpaca") == "live"

    def test_resolve_mt5_credentials(self):
        """Test MT5 credentials resolution."""
        with patch(
            "frontend.utils.broker_mode_resolver.get_secret"
        ) as mock_get_secret:

            def mock_secret(key, default=None, **kwargs):
                secrets = {
                    "MT5_USER": "123456",
                    "MT5_PASSWORD": "mypassword",
                    "MT5_SERVER": "Axi-US51-Live",
                    "MT5_PORT": "443",
                }
                return secrets.get(key, default)

            mock_get_secret.side_effect = mock_secret

            with tempfile.TemporaryDirectory() as tmpdir:
                config_path = Path(tmpdir) / "broker_modes.json"
                config = BrokerModeConfig(config_path)

                with patch(
                    "frontend.utils.broker_mode_resolver.get_config",
                    return_value=config,
                ):
                    creds = resolve_mt5_credentials()

                    assert creds["user"] == "123456"
                    assert creds["password"] == "mypassword"
                    assert creds["server"] == "Axi-US51-Live"
                    assert creds["port"] == 443
                    assert creds["mode"] == "paper"


class TestModePersistence:
    """Test that mode settings persist across app reloads."""

    def test_mode_persists_after_reload(self):
        """Test that mode survives config reload."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "broker_modes.json"

            # Create and modify config
            config1 = BrokerModeConfig(config_path)
            config1.set_global_mode("live")
            config1.set_bot_active("Titan", True)

            # Reload config
            config2 = BrokerModeConfig(config_path)

            # Verifying persistence
            assert config2.get_global_mode() == "live"
            assert config2.is_bot_active("Titan") == True

    def test_mode_override_persists(self):
        """Test that broker-specific overrides persist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "broker_modes.json"

            config1 = BrokerModeConfig(config_path)
            config1.set_global_mode("paper")
            config1.set_broker_mode("alpaca", "live")

            # Reload
            config2 = BrokerModeConfig(config_path)

            # Verify both settings persist
            assert config2.get_global_mode() == "paper"
            assert config2.get_broker_mode("alpaca") == "live"


# ============================================================================
# INTEGRATION TESTS - Test full workflow
# ============================================================================


class TestPaperLiveSwitchingWorkflow:
    """Test complete workflow of switching between paper and live modes."""

    def test_ml_experiment_setup(self):
        """
        Test ML experiment setup:
        - Rigel and Dogon run on PAPER (for ML experiments)
        - Titan runs on LIVE (for real trading)
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "broker_modes.json"
            config = BrokerModeConfig(config_path)

            # Initial: all paper
            config.set_global_mode("paper")

            # Activate research bots on paper
            config.set_bot_active("Rigel", True)
            config.set_bot_active("Dogon", True)

            # Activate trading bot on live
            config.set_bot_active("Titan", True)
            config.set_broker_mode("alpaca", "live")

            # Verify setup
            assert config.get_bot_mode("Rigel") == "paper"  # MT5 is paper
            assert config.get_bot_mode("Dogon") == "paper"
            assert config.get_bot_mode("Titan") == "live"  # Alpaca is live

            status = config.get_all_bots_status()
            assert status["Rigel"]["active"] == True
            assert status["Rigel"]["mode"] == "paper"
            assert status["Titan"]["active"] == True
            assert status["Titan"]["mode"] == "live"

    def test_multi_broker_setup(self):
        """
        Test multi-broker setup:
        - Alpaca bots on PAPER (testing)
        - MT5 bots on LIVE (prop trading)
        - IBKR on PAPER (default)
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "broker_modes.json"
            config = BrokerModeConfig(config_path)

            # Mixed mode setup
            config.set_broker_mode("alpaca", "paper")
            config.set_broker_mode("mt5", "live")
            config.set_broker_mode("ibkr", "paper")

            # Activate bots
            config.set_bot_active("Titan", True)  # Alpaca bot
            config.set_bot_active("Rigel", True)  # MT5 bot
            config.set_bot_active("Vega", True)   # IBKR bot

            # Verify mixed setup
            assert config.get_bot_mode("Titan") == "paper"
            assert config.get_bot_mode("Rigel") == "live"
            assert config.get_bot_mode("Vega") == "paper"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
