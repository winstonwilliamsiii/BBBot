"""
Environment Configuration Manager
Handles loading environment-specific configuration with proper precedence
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv, find_dotenv

# Critical environment variables that MUST be present
CRITICAL_VARS = [
    'MYSQL_HOST',
    'MYSQL_PORT',
    'MYSQL_USER',
    'MYSQL_PASSWORD',
    'MYSQL_DATABASE',
]

# Important variables that should be present but can be optional
IMPORTANT_VARS = [
    'PLAID_CLIENT_ID',
    'ALPACA_API_KEY',
    'MLFLOW_TRACKING_URI',
    'APPWRITE_ENDPOINT',
]

class EnvironmentConfig:
    """Manages environment-specific configuration loading"""
    
    def __init__(self):
        """Initialize configuration with proper precedence"""
        self.env_type = os.getenv('ENVIRONMENT', 'development')
        self._load_env_files()
        self._validate_critical_vars()
    
    def _load_env_files(self):
        """
        Load environment files in precedence order:
        1. .env.local (machine-specific, gitignored) - HIGHEST PRIORITY
        2. .env.{ENVIRONMENT} (environment-specific)
        3. .env (default fallback)
        """
        # Use the directory where config_env.py is located, not parent
        project_root = Path(__file__).parent
        
        # Define environment files in reverse precedence order
        env_files = [
            project_root / '.env',  # Base fallback
            project_root / f'.env.{self.env_type}',  # Environment-specific
            project_root / '.env.local',  # Machine-specific (highest priority)
        ]
        
        # Load each file, with later files overriding earlier ones
        loaded_any = False
        for env_file in env_files:
            if env_file.exists():
                load_dotenv(env_file, override=True)
                print(f"✓ Loaded config: {env_file.name}")
                loaded_any = True
        
        if not loaded_any:
            print(f"⚠️ No .env files found in {project_root}", file=sys.stderr)
            print(f"   Looking for: .env, .env.{self.env_type}, or .env.local", file=sys.stderr)

        # Backfill MYSQL_* from DB_* if present (dev compatibility)
        db_to_mysql = {
            'DB_HOST': 'MYSQL_HOST',
            'DB_PORT': 'MYSQL_PORT',
            'DB_USER': 'MYSQL_USER',
            'DB_PASSWORD': 'MYSQL_PASSWORD',
            'DB_NAME': 'MYSQL_DATABASE',
        }
        for db_key, mysql_key in db_to_mysql.items():
            if not os.getenv(mysql_key) and os.getenv(db_key):
                os.environ[mysql_key] = os.getenv(db_key)
    
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
    
    def _validate_critical_vars(self):
        """
        Validate that critical environment variables are set
        Fails fast if critical variables are missing
        """
        missing_critical = []
        missing_important = []
        
        # Check critical variables
        for var in CRITICAL_VARS:
            if not os.getenv(var):
                missing_critical.append(var)
        
        # Check important variables (warnings only)
        for var in IMPORTANT_VARS:
            if not os.getenv(var):
                missing_important.append(var)
        
        # Fail if critical variables are missing
        if missing_critical:
            error_msg = f"""
╔════════════════════════════════════════════════════════════════╗
║  ❌ CRITICAL CONFIGURATION ERROR                               ║
╠════════════════════════════════════════════════════════════════╣
║  Missing required environment variables:                       ║
║  {', '.join(missing_critical):<58} ║
║                                                                ║
║  These variables MUST be set in your .env file                 ║
║                                                                ║
║  Quick Fix:                                                    ║
║  1. Copy .env.example to .env                                  ║
║     Copy-Item .env.example .env                                ║
║  2. Fill in your actual values in .env                         ║
║  3. Restart the application                                    ║
╚════════════════════════════════════════════════════════════════╝
"""
            if self.is_production():
                print(error_msg, file=sys.stderr)
                sys.exit(1)
            else:
                # In development, warn but allow the app to start
                print(error_msg, file=sys.stderr)
                print("⚠️  Development mode: continuing without required vars.", file=sys.stderr)
        
        # Warn about missing important variables
        if missing_important:
            warning_msg = f"""
⚠️  WARNING: Missing optional but important environment variables:
   {', '.join(missing_important)}
   
   Some features may not work correctly without these variables.
   Check .env.example for reference.
"""
            print(warning_msg, file=sys.stderr)


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
