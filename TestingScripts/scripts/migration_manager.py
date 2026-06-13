#!/usr/bin/env python3
"""
Migration Manager - Handles versioned SQL migrations across multiple environments
Purpose: Deploy SQL migrations in correct order to Demo/Staging/Prod databases
Author: Bentley Bot System
Date: January 27, 2026
"""

import os
import sys
import json
import logging
import mysql.connector
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from enum import Enum
import argparse

# ===================================================================
# Configuration & Logging
# ===================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Environment(Enum):
    """Target deployment environment"""
    DEMO = "demo"
    STAGING = "staging"
    PROD = "prod"


class MigrationStatus(Enum):
    """Status of migration execution"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


# ===================================================================
# Database Configuration by Environment
# ===================================================================

DB_CONFIG = {
    Environment.DEMO: {
        "host": os.getenv("DB_DEMO_HOST", "localhost"),
        "port": int(os.getenv("DB_DEMO_PORT", "3307")),
        "user": os.getenv("DB_DEMO_USER", "root"),
        "password": os.getenv("DB_DEMO_PASSWORD", "root"),
        "databases": ["test_bbbot1", "test_mlflow_db", "test_mansa_quant"],
    },
    Environment.STAGING: {
        "host": os.getenv("DB_STAGING_HOST", "localhost"),
        "port": int(os.getenv("DB_STAGING_PORT", "3307")),
        "user": os.getenv("DB_STAGING_USER", "bentley_bot_staging"),
        "password": os.getenv("DB_STAGING_PASSWORD", ""),
        "databases": ["bbbot1", "mlflow_db", "mansa_quant"],
    },
    Environment.PROD: {
        "host": os.getenv("DB_PROD_HOST", "localhost"),
        "port": int(os.getenv("DB_PROD_PORT", "3306")),
        "user": os.getenv("DB_PROD_USER", "bentley_bot_prod"),
        "password": os.getenv("DB_PROD_PASSWORD", ""),
        "databases": ["bentley_bot", "mlflow_db", "mansa_quant"],
    },
}


# ===================================================================
# Migration File Management
# ===================================================================

class MigrationFile:
    """Represents a SQL migration file"""
    
    def __init__(self, file_path: str, version: str, target_db: str):
        self.file_path = Path(file_path)
        self.version = version  # e.g., "v1.0.0"
        self.target_db = target_db  # e.g., "bbbot1"
        self.name = self.file_path.stem
        
    @property
    def version_tuple(self) -> Tuple[int, int, int]:
        """Convert version string to tuple for comparison"""
        try:
            parts = self.version.replace("v", "").split(".")
            return tuple(int(p) for p in parts)
        except:
            return (0, 0, 0)
    
    def read_content(self) -> str:
        """Read SQL file content"""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to read migration file {self.file_path}: {e}")
            raise
    
    def __repr__(self) -> str:
        return f"Migration({self.version}, {self.target_db})"
    
    def __lt__(self, other):
        """Enable sorting by version"""
        return self.version_tuple < other.version_tuple


class MigrationManager:
    """Manages migration discovery, ordering, and execution"""
    
    def __init__(self, environment: Environment, migration_dir: str = "migrations"):
        self.environment = environment
        self.migration_dir = Path(migration_dir)
        self.db_config = DB_CONFIG[environment]
        self.connection: Optional[mysql.connector.MySQLConnection] = None
        self.migrations: List[MigrationFile] = []
        self.executed_migrations: Dict[str, MigrationStatus] = {}
        
    def discover_migrations(self) -> List[MigrationFile]:
        """Discover all applicable migrations for environment"""
        migrations = []
        
        # 1. Discover base migrations (applies to all environments)
        base_path = self.migration_dir / "base"
        if base_path.exists():
            migrations.extend(self._scan_directory(base_path, "base"))
        
        # 2. Discover environment-specific migrations
        env_path = self.migration_dir / self.environment.value
        if env_path.exists():
            migrations.extend(self._scan_directory(env_path, self.environment.value))
        
        # 3. Sort migrations by version
        migrations.sort()
        
        self.migrations = migrations
        logger.info(f"Discovered {len(migrations)} migrations for {self.environment.value}")
        return migrations
    
    def _scan_directory(self, directory: Path, source: str) -> List[MigrationFile]:
        """Scan directory for SQL migration files"""
        migrations = []
        
        for sql_file in sorted(directory.glob("*.sql")):
            # Extract version from filename (e.g., v1.0.0_init.sql)
            filename = sql_file.stem
            parts = filename.split("_", 1)
            
            if len(parts) >= 1 and parts[0].startswith("v"):
                version = parts[0]
                # Target database is typically mentioned in filename or parent dir
                target_db = self._extract_database(filename)
                
                migration = MigrationFile(str(sql_file), version, target_db)
                migrations.append(migration)
                logger.debug(f"Found migration: {migration}")
        
        return migrations
    
    def _extract_database(self, filename: str) -> str:
        """Extract target database from filename"""
        # Common patterns: init, bbbot1, mlflow, mansa_quant
        if "bbbot1" in filename:
            return "bbbot1"
        elif "mlflow" in filename:
            return "mlflow_db"
        elif "mansa" in filename or "quant" in filename:
            return "mansa_quant"
        elif "bentley" in filename:
            return "bentley_bot"
        else:
            return "bbbot1"  # Default to bbbot1
    
    def connect(self) -> bool:
        """Establish database connection"""
        try:
            self.connection = mysql.connector.connect(
                host=self.db_config["host"],
                port=self.db_config["port"],
                user=self.db_config["user"],
                password=self.db_config["password"],
            )
            logger.info(f"Connected to {self.environment.value} database")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to {self.environment.value} database: {e}")
            return False
    
    def disconnect(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            logger.info(f"Disconnected from {self.environment.value} database")
    
    def ensure_migration_tracking_table(self, database: str):
        """Ensure migration_history table exists"""
        cursor = self.connection.cursor()
        
        try:
            cursor.execute(f"USE {database}")
            
            # Check if migration_history table exists
            cursor.execute("""
                SELECT 1 FROM information_schema.TABLES 
                WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'migration_history'
            """, (database,))
            
            if not cursor.fetchone():
                # Create migration_history table
                cursor.execute(f"""
                    CREATE TABLE {database}.migration_history (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        migration_version VARCHAR(20) NOT NULL,
                        migration_name VARCHAR(255) NOT NULL,
                        executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        status VARCHAR(20) DEFAULT 'success',
                        notes TEXT,
                        INDEX idx_version (migration_version),
                        INDEX idx_executed_at (executed_at)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """)
                logger.info(f"Created migration_history table in {database}")
            
            self.connection.commit()
        except Exception as e:
            logger.error(f"Failed to ensure migration tracking table in {database}: {e}")
            self.connection.rollback()
        finally:
            cursor.close()
    
    def execute_migration(self, migration: MigrationFile) -> bool:
        """Execute a single migration"""
        cursor = self.connection.cursor()
        
        try:
            # Ensure database exists
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {migration.target_db}")
            cursor.execute(f"USE {migration.target_db}")
            
            # Ensure migration tracking table exists
            self.ensure_migration_tracking_table(migration.target_db)
            
            # Check if migration already executed
            cursor.execute(
                f"SELECT 1 FROM {migration.target_db}.migration_history WHERE migration_version = %s",
                (migration.version,)
            )
            
            if cursor.fetchone():
                logger.info(f"Migration {migration.version} already executed, skipping")
                self.executed_migrations[migration.version] = MigrationStatus.PENDING
                return True
            
            # Read and execute migration SQL
            sql_content = migration.read_content()
            
            logger.info(f"Executing migration: {migration.version} on {migration.target_db}")
            
            # Split by semicolon and execute statements
            statements = [s.strip() for s in sql_content.split(";") if s.strip()]
            
            for statement in statements:
                if not statement.startswith("--") and statement.strip():
                    cursor.execute(statement)
            
            self.connection.commit()
            self.executed_migrations[migration.version] = MigrationStatus.SUCCESS
            
            logger.info(f"✓ Successfully executed {migration.version}")
            return True
            
        except Exception as e:
            logger.error(f"✗ Failed to execute {migration.version}: {e}")
            self.executed_migrations[migration.version] = MigrationStatus.FAILED
            self.connection.rollback()
            return False
        finally:
            cursor.close()
    
    def execute_all_migrations(self, dry_run: bool = False) -> bool:
        """Execute all discovered migrations"""
        if not self.migrations:
            logger.warning("No migrations to execute")
            return True
        
        logger.info(f"Executing {len(self.migrations)} migrations for {self.environment.value}")
        
        if dry_run:
            logger.info("DRY RUN MODE - No changes will be made")
            for migration in self.migrations:
                logger.info(f"  Would execute: {migration}")
            return True
        
        success_count = 0
        
        for migration in self.migrations:
            if self.execute_migration(migration):
                success_count += 1
        
        logger.info(f"Migration execution complete: {success_count}/{len(self.migrations)} successful")
        return success_count == len(self.migrations)
    
    def get_status(self) -> Dict:
        """Get migration status summary"""
        return {
            "environment": self.environment.value,
            "total_migrations": len(self.migrations),
            "executed": self.executed_migrations,
            "migrations": [
                {
                    "version": m.version,
                    "database": m.target_db,
                    "name": m.name,
                }
                for m in self.migrations
            ]
        }


# ===================================================================
# CLI Interface
# ===================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Migration Manager - Deploy SQL migrations to specified environment"
    )
    
    parser.add_argument(
        "--env",
        choices=["demo", "staging", "prod"],
        required=True,
        help="Target environment (demo, staging, or prod)"
    )
    
    parser.add_argument(
        "--action",
        choices=["execute", "discover", "status"],
        default="execute",
        help="Action to perform (default: execute)"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run in dry-run mode (no changes)"
    )
    
    parser.add_argument(
        "--migration-dir",
        default="migrations",
        help="Path to migrations directory (default: migrations)"
    )
    
    args = parser.parse_args()
    
    # Convert env to Environment enum
    environment = {
        "demo": Environment.DEMO,
        "staging": Environment.STAGING,
        "prod": Environment.PROD,
    }[args.env]
    
    # Initialize migration manager
    manager = MigrationManager(environment, args.migration_dir)
    
    try:
        # Discover migrations
        manager.discover_migrations()
        
        if args.action == "discover":
            logger.info("Discovered migrations:")
            for migration in manager.migrations:
                logger.info(f"  {migration}")
            return 0
        
        # Connect to database
        if not manager.connect():
            logger.error("Failed to connect to database")
            return 1
        
        if args.action == "execute":
            # Execute migrations
            success = manager.execute_all_migrations(dry_run=args.dry_run)
            
            # Print status
            status = manager.get_status()
            logger.info(json.dumps(status, indent=2))
            
            return 0 if success else 1
        
        elif args.action == "status":
            status = manager.get_status()
            logger.info(json.dumps(status, indent=2))
            return 0
        
    finally:
        manager.disconnect()


if __name__ == "__main__":
    sys.exit(main())
