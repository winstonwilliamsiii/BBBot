"""
Environment Configuration Manager
Handles loading environment-specific configuration with proper precedence
"""
import os
from pathlib import Path
from dotenv import load_dotenv, find_dotenv

class EnvironmentConfig:
    """Manages environment-specific configuration loading"""
    
    def __init__(self):
        """Initialize configuration with proper precedence"""
        self.env_type = os.getenv('ENVIRONMENT', 'development')
        self._load_env_files()
    
    def _load_env_files(self):
        """
        Load environment files in precedence order:
        1. .env.local (machine-specific, gitignored) - HIGHEST PRIORITY
        2. .env.{ENVIRONMENT} (environment-specific)
        3. .env (default fallback)
        """
        project_root = Path(__file__).parent.parent
        
        # Define environment files in reverse precedence order
        env_files = [
            project_root / '.env',  # Base fallback
            project_root / f'.env.{self.env_type}',  # Environment-specific
            project_root / '.env.local',  # Machine-specific (highest priority)
        ]
        
        # Load each file, with later files overriding earlier ones
        for env_file in env_files:
            if env_file.exists():
                load_dotenv(env_file, override=True)
                print(f"✓ Loaded config: {env_file.name}")
    
    @staticmethod
    def get(key: str, default=None):
        """Get configuration value"""
        return os.getenv(key, default)
    
    @staticmethod
    def get_bool(key: str, default=False) -> bool:
        """Get boolean configuration value"""
        value = os.getenv(key, str(default)).lower()
        return value in ('true', '1', 'yes', 'on')
    
    @staticmethod
    def get_int(key: str, default=0) -> int:
        """Get integer configuration value"""
        try:
            return int(os.getenv(key, default))
        except (ValueError, TypeError):
            return default
    
    @staticmethod
    def is_production() -> bool:
        """Check if running in production"""
        return os.getenv('ENVIRONMENT', 'development').lower() == 'production'
    
    @staticmethod
    def is_development() -> bool:
        """Check if running in development"""
        return os.getenv('ENVIRONMENT', 'development').lower() == 'development'


def reload_env():
    """
    Reload environment configuration
    Useful for Streamlit apps during development
    """
    # Clear current environment variables (except system vars)
    project_root = Path(__file__).parent.parent
    env_files = [
        project_root / '.env',
        project_root / f'.env.{os.getenv("ENVIRONMENT", "development")}',
        project_root / '.env.local',
    ]
    
    for env_file in env_files:
        if env_file.exists():
            load_dotenv(env_file, override=True)
    
    return EnvironmentConfig()


# Initialize on module import
config = EnvironmentConfig()

if __name__ == '__main__':
    # Print current configuration
    print(f"Environment: {config.get('ENVIRONMENT')}")
    print(f"Is Production: {config.is_production()}")
    print(f"Is Development: {config.is_development()}")
    print(f"Database Host: {config.get('DB_HOST')}")
    print(f"Alpaca Environment: {config.get('ALPACA_ENVIRONMENT')}")
