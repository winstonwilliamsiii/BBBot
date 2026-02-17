"""
Root-level Environment Configuration
Provides simple environment detection for CI/CD workflows
Full configuration available in src/config_env.py
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv


class EnvironmentConfig:
    """Simple configuration for CI/CD environment detection"""
    
    def __init__(self):
        """Initialize configuration by loading environment files"""
        self._load_env_files()
        self.environment = os.getenv('ENVIRONMENT', 'development').lower()
    
    def _load_env_files(self):
        """Load environment files in precedence order"""
        project_root = Path(__file__).parent
        
        # Load in reverse precedence order (later files override earlier)
        env_files = [
            project_root / '.env',
            project_root / f'.env.{os.getenv("ENVIRONMENT", "development")}',
            project_root / '.env.local',
        ]
        
        for env_file in env_files:
            if env_file.exists():
                load_dotenv(env_file, override=True)
    
    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get environment variable value"""
        return os.getenv(key, default)
    
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.environment == 'production'
    
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.environment in ('development', 'dev')
    
    def is_staging(self) -> bool:
        """Check if running in staging environment"""
        return self.environment == 'staging'
    
    def is_ci(self) -> bool:
        """Check if running in CI/CD environment"""
        return os.getenv('CI', '').lower() == 'true' or os.getenv('GITHUB_ACTIONS', '').lower() == 'true'
    
    def get_environment(self) -> str:
        """Get current environment name"""
        return self.environment


# Create module-level config instance
config = EnvironmentConfig()


# Export commonly used functions
def is_production() -> bool:
    """Check if running in production"""
    return config.is_production()


def is_development() -> bool:
    """Check if running in development"""
    return config.is_development()


def is_staging() -> bool:
    """Check if running in staging"""
    return config.is_staging()


def is_ci() -> bool:
    """Check if running in CI/CD"""
    return config.is_ci()


if __name__ == '__main__':
    print(f"Environment: {config.get_environment()}")
    print(f"Is Production: {config.is_production()}")
    print(f"Is Development: {config.is_development()}")
    print(f"Is Staging: {config.is_staging()}")
    print(f"Is CI: {config.is_ci()}")
