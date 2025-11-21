"""
Bentley Budget Bot - Environment Configuration Helper
Loads environment variables from .env file and validates required credentials
"""

import os
from pathlib import Path
from typing import Dict, List, Optional
from dotenv import load_dotenv


class EnvironmentConfig:
    """Manages environment variables and validates required credentials"""
    
    REQUIRED_VARS = [
        'TIINGO_API_KEY',
        'MYSQL_PASSWORD',
        'MYSQL_USER',
        'MYSQL_DATABASE',
    ]
    
    OPTIONAL_VARS = [
        'YAHOO_FINANCE_API_KEY',
        'BARCHART_API_KEY',
        'POLYGON_API_KEY',
        'NEWS_API_KEY',
        'BANKING_API_KEY',
        'MLFLOW_TRACKING_URI',
        'AIRBYTE_API_URL',
    ]
    
    def __init__(self, env_file: Optional[str] = None):
        """
        Initialize environment configuration
        
        Args:
            env_file: Path to .env file. If None, searches for .env in project root
        """
        if env_file:
            self.env_path = Path(env_file)
        else:
            # Search for .env in current directory and parent directories
            self.env_path = self._find_env_file()
        
        self.load_environment()
    
    def _find_env_file(self) -> Optional[Path]:
        """Find .env file in current or parent directories"""
        current = Path.cwd()
        
        # Check current directory and up to 3 parent directories
        for _ in range(4):
            env_file = current / '.env'
            if env_file.exists():
                return env_file
            current = current.parent
        
        return None
    
    def load_environment(self) -> bool:
        """
        Load environment variables from .env file
        
        Returns:
            bool: True if .env file was found and loaded
        """
        if self.env_path and self.env_path.exists():
            load_dotenv(self.env_path)
            print(f"✅ Loaded environment from: {self.env_path}")
            return True
        else:
            print("⚠️  No .env file found. Please create one from .env.example")
            print("   Run: cp .env.example .env")
            return False
    
    def validate_required(self) -> tuple[bool, List[str]]:
        """
        Validate that all required environment variables are set
        
        Returns:
            tuple: (is_valid, missing_vars)
        """
        missing = []
        
        for var in self.REQUIRED_VARS:
            value = os.getenv(var)
            if not value or value.startswith('your_'):
                missing.append(var)
        
        is_valid = len(missing) == 0
        return is_valid, missing
    
    def get_config(self) -> Dict[str, str]:
        """
        Get all configuration values
        
        Returns:
            dict: Dictionary of all environment variables
        """
        config = {}
        
        for var in self.REQUIRED_VARS + self.OPTIONAL_VARS:
            value = os.getenv(var)
            config[var] = value if value else None
        
        return config
    
    def print_status(self):
        """Print status of all environment variables"""
        print("\n" + "="*60)
        print("🔐 Bentley Budget Bot - Environment Configuration Status")
        print("="*60)
        
        is_valid, missing = self.validate_required()
        
        if is_valid:
            print("\n✅ All required environment variables are set!")
        else:
            print(f"\n❌ Missing {len(missing)} required environment variable(s):")
            for var in missing:
                print(f"   - {var}")
        
        print("\n📋 Required Variables:")
        for var in self.REQUIRED_VARS:
            value = os.getenv(var)
            status = "✅" if value and not value.startswith('your_') else "❌"
            masked = self._mask_value(value) if value else "Not set"
            print(f"   {status} {var}: {masked}")
        
        print("\n📋 Optional Variables:")
        for var in self.OPTIONAL_VARS:
            value = os.getenv(var)
            status = "✅" if value and not value.startswith('your_') else "⚪"
            masked = self._mask_value(value) if value else "Not set"
            print(f"   {status} {var}: {masked}")
        
        print("\n" + "="*60)
        
        if not is_valid:
            print("\n⚠️  Please update your .env file with the missing values")
            print("   See SECURITY.md for detailed setup instructions")
        
        print()
    
    @staticmethod
    def _mask_value(value: Optional[str]) -> str:
        """Mask sensitive values for display"""
        if not value:
            return "Not set"
        if value.startswith('your_'):
            return "⚠️  Template value (needs update)"
        if len(value) > 8:
            return f"{value[:4]}...{value[-4:]}"
        return "****"
    
    def get_database_url(self, database: str = None) -> str:
        """
        Get MySQL database connection URL
        
        Args:
            database: Database name (overrides MYSQL_DATABASE)
        
        Returns:
            str: MySQL connection URL
        """
        host = os.getenv('MYSQL_HOST', 'localhost')
        port = os.getenv('MYSQL_PORT', '3306')
        user = os.getenv('MYSQL_USER', 'airflow')
        password = os.getenv('MYSQL_PASSWORD', '')
        db = database or os.getenv('MYSQL_DATABASE', 'airflow')
        
        if not password:
            raise ValueError("MYSQL_PASSWORD not set in environment")
        
        return f"mysql+pymysql://{user}:{password}@{host}:{port}/{db}"
    
    def get_mlflow_uri(self) -> str:
        """Get MLflow tracking URI"""
        return os.getenv('MLFLOW_TRACKING_URI', 'http://localhost:5000')
    
    def get_airbyte_url(self) -> str:
        """Get Airbyte API URL"""
        return os.getenv('AIRBYTE_API_URL', 'http://localhost:8001')


# Singleton instance
_config_instance = None


def get_config() -> EnvironmentConfig:
    """
    Get or create singleton EnvironmentConfig instance
    
    Returns:
        EnvironmentConfig: Configuration instance
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = EnvironmentConfig()
    return _config_instance


def require_env_var(var_name: str) -> str:
    """
    Get environment variable or raise error if not set
    
    Args:
        var_name: Name of environment variable
    
    Returns:
        str: Value of environment variable
    
    Raises:
        ValueError: If environment variable is not set
    """
    value = os.getenv(var_name)
    if not value or value.startswith('your_'):
        raise ValueError(
            f"{var_name} environment variable not set. "
            f"Please add it to your .env file. See SECURITY.md for details."
        )
    return value


if __name__ == '__main__':
    # Test the configuration when run directly
    config = EnvironmentConfig()
    config.print_status()
    
    # Test database URL generation if credentials are valid
    is_valid, missing = config.validate_required()
    if is_valid:
        print("\n🔗 Connection URLs:")
        try:
            print(f"   Database: {config.get_database_url()}")
            print(f"   MLflow: {config.get_mlflow_uri()}")
            print(f"   Airbyte: {config.get_airbyte_url()}")
        except ValueError as e:
            print(f"   ❌ Error: {e}")
