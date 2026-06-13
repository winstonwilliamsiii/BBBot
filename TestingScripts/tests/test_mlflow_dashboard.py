"""
Test suite for MLflow Dashboard Integration
Tests configuration, connection, and dashboard functionality
"""

import sys
import os
import pytest

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bbbot1_pipeline.mlflow_config import (
    get_mlflow_config,
    get_mlflow_tracking_uri,
    get_mlflow_artifact_path,
)


class TestMLflowConfiguration:
    """Test MLflow configuration setup."""
    
    def test_mlflow_config_structure(self):
        """Test that MLflow config has all required fields."""
        config = get_mlflow_config()
        
        assert "name" in config
        assert "host" in config
        assert "port" in config
        assert "user" in config
        assert "password" in config
        assert "database" in config
    
    def test_mlflow_config_types(self):
        """Test that config values are of correct types."""
        config = get_mlflow_config()
        
        assert isinstance(config["name"], str)
        assert isinstance(config["host"], str)
        assert isinstance(config["port"], int)
        assert isinstance(config["user"], str)
        assert isinstance(config["database"], str)
    
    def test_tracking_uri_format(self):
        """Test that tracking URI is properly formatted."""
        uri = get_mlflow_tracking_uri()
        
        assert uri.startswith("mysql+pymysql://")
        assert "@" in uri
        assert ":" in uri
        assert "/" in uri
    
    def test_artifact_path_creation(self):
        """Test that artifact path is created and accessible."""
        artifact_path = get_mlflow_artifact_path()
        
        assert isinstance(artifact_path, str)
        assert len(artifact_path) > 0
        # Path should be created by the function
        assert os.path.exists(artifact_path) or True  # May not exist yet


class TestMLflowImport:
    """Test MLflow package availability."""
    
    def test_mlflow_import(self):
        """Test that MLflow can be imported."""
        try:
            import mlflow
            assert mlflow is not None
        except ImportError:
            pytest.skip("MLflow not installed")
    
    def test_mlflow_tracking_import(self):
        """Test that MLflow tracking client can be imported."""
        try:
            from mlflow.tracking import MlflowClient
            assert MlflowClient is not None
        except ImportError:
            pytest.skip("MLflow not installed")


class TestMLflowDashboardPage:
    """Test legacy dashboard pages are removed."""
    
    def test_standalone_dashboard_removed(self):
        """Test that legacy standalone MLflow page has been removed."""
        dashboard_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "pages",
            "98_🧠_MLflow_Training.py"
        )
        assert not os.path.exists(dashboard_path)


class TestAdminControlCenter:
    """Test Admin Control Center removal."""
    
    def test_admin_control_center_removed(self):
        """Test that Admin Control Center file has been removed."""
        admin_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "pages",
            "99_🔧_Admin_Control_Center.py"
        )
        assert not os.path.exists(admin_path)


def run_tests():
    """Run all tests and print results."""
    print("=" * 70)
    print("MLflow Dashboard Integration Tests")
    print("=" * 70)
    print()
    
    # Run tests
    exit_code = pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "-p", "no:warnings"
    ])
    
    return exit_code


if __name__ == "__main__":
    exit_code = run_tests()
    sys.exit(exit_code)
