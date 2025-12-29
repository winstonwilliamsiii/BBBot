#!/usr/bin/env python3
"""
Database Migration Runner
=========================
Automatically applies SQL migrations to multiple databases in order.

Features:
- Reads .sql files from migrations/ folder
- Tracks applied migrations in schema_migrations table
- Applies to both local and Railway databases
- Transaction support for rollback on error
- Detailed logging and progress reporting

Usage:
    python migrations/run_migrations.py
    python migrations/run_migrations.py --database mydb
    python migrations/run_migrations.py --dry-run
"""

import os
import sys
import re
import pymysql
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple, Optional
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

load_dotenv()

# ============================================================================
# DATABASE CONFIGURATIONS
# ============================================================================

DATABASES = {
    "mydb": {
        "name": "mydb (Local Budget DB)",
        "host": os.getenv("BUDGET_MYSQL_HOST", "127.0.0.1"),
        "port": int(os.getenv("BUDGET_MYSQL_PORT", "3306")),
        "user": os.getenv("BUDGET_MYSQL_USER", "root"),
        "password": os.getenv("BUDGET_MYSQL_PASSWORD", "root"),
        "database": os.getenv("BUDGET_MYSQL_DATABASE", "mydb")
    },
    "mansa_bot": {
        "name": "mansa_bot (Local Trading DB)",
        "host": os.getenv("MYSQL_HOST", "127.0.0.1"),
        "port": int(os.getenv("MYSQL_PORT", "3307")),
        "user": os.getenv("MYSQL_USER", "root"),
        "password": os.getenv("MYSQL_PASSWORD", "root"),
        "database": os.getenv("MYSQL_DATABASE", "mansa_bot")
    },
    "railway": {
        "name": "Railway (Production)",
        "host": os.getenv("RAILWAY_MYSQL_HOST", ""),
        "port": int(os.getenv("RAILWAY_MYSQL_PORT", "3306")) if os.getenv("RAILWAY_MYSQL_PORT") else 3306,
        "user": os.getenv("RAILWAY_MYSQL_USER", ""),
        "password": os.getenv("RAILWAY_MYSQL_PASSWORD", ""),
        "database": os.getenv("RAILWAY_MYSQL_DATABASE", "railway")
    }
}

MIGRATIONS_DIR = project_root / "migrations"

# ============================================================================
# SCHEMA MIGRATIONS TABLE
# ============================================================================

CREATE_MIGRATIONS_TABLE = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    version VARCHAR(50) NOT NULL UNIQUE,
    filename VARCHAR(255) NOT NULL,
    description TEXT,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    execution_time_ms INT,
    checksum VARCHAR(64),
    INDEX idx_version (version),
    INDEX idx_applied_at (applied_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
"""

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_connection(db_config: Dict) -> Optional[pymysql.connections.Connection]:
    """Create database connection"""
    try:
        if not db_config.get("password"):
            return None
        
        conn = pymysql.connect(
            host=db_config["host"],
            port=db_config["port"],
            user=db_config["user"],
            password=db_config["password"],
            database=db_config["database"],
            autocommit=False  # Use transactions
        )
        return conn
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        return None


def ensure_migrations_table(conn: pymysql.connections.Connection) -> bool:
    """Create schema_migrations table if it doesn't exist"""
    try:
        cursor = conn.cursor()
        cursor.execute(CREATE_MIGRATIONS_TABLE)
        conn.commit()
        cursor.close()
        return True
    except Exception as e:
        print(f"   ❌ Failed to create migrations table: {e}")
        return False


def get_applied_migrations(conn: pymysql.connections.Connection) -> List[str]:
    """Get list of already applied migration versions"""
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT version FROM schema_migrations ORDER BY version")
        applied = [row[0] for row in cursor.fetchall()]
        cursor.close()
        return applied
    except Exception as e:
        print(f"   ⚠️  Could not read migration history: {e}")
        return []


def get_migration_files() -> List[Tuple[str, Path]]:
    """Get all .sql files from migrations folder in order"""
    migration_files = []
    
    for file in sorted(MIGRATIONS_DIR.glob("*.sql")):
        # Extract version number from filename (e.g., "001" from "001_init.sql")
        match = re.match(r"^(\d+)_.*\.sql$", file.name)
        if match:
            version = match.group(1)
            migration_files.append((version, file))
    
    return migration_files


def parse_migration_file(file_path: Path) -> Dict:
    """Parse migration file to extract metadata"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract description from header comment
    description_match = re.search(r'-- Migration \d+: (.+)', content)
    description = description_match.group(1) if description_match else file_path.stem
    
    # Calculate checksum
    import hashlib
    checksum = hashlib.sha256(content.encode()).hexdigest()
    
    return {
        "content": content,
        "description": description,
        "checksum": checksum
    }


def apply_migration(
    conn: pymysql.connections.Connection,
    version: str,
    file_path: Path,
    dry_run: bool = False
) -> Tuple[bool, Optional[str], int]:
    """
    Apply a single migration file to database
    
    Returns:
        Tuple of (success, error_message, execution_time_ms)
    """
    try:
        migration_data = parse_migration_file(file_path)
        
        if dry_run:
            print(f"      [DRY RUN] Would execute: {file_path.name}")
            return True, None, 0
        
        start_time = datetime.now()
        cursor = conn.cursor()
        
        # Split SQL into individual statements (handle multi-statement files)
        statements = [s.strip() for s in migration_data["content"].split(';') if s.strip()]
        
        for statement in statements:
            if statement:
                cursor.execute(statement)
        
        # Record migration in schema_migrations table
        cursor.execute(
            """
            INSERT INTO schema_migrations (version, filename, description, checksum, execution_time_ms)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                version,
                file_path.name,
                migration_data["description"],
                migration_data["checksum"],
                int((datetime.now() - start_time).total_seconds() * 1000)
            )
        )
        
        conn.commit()
        cursor.close()
        
        execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
        return True, None, execution_time
        
    except Exception as e:
        conn.rollback()
        return False, str(e), 0


def run_migrations_for_database(
    db_key: str,
    db_config: Dict,
    target_version: Optional[str] = None,
    dry_run: bool = False
) -> Tuple[int, int]:
    """
    Run all pending migrations for a single database
    
    Returns:
        Tuple of (applied_count, failed_count)
    """
    print(f"\n{'='*80}")
    print(f"Database: {db_config['name']}")
    print(f"{'='*80}")
    
    # Check if database is accessible
    if not db_config.get("password"):
        print(f"⏭️  Skipping {db_key} (no credentials)")
        return 0, 0
    
    conn = get_connection(db_config)
    if not conn:
        print(f"❌ Could not connect to {db_key}")
        return 0, 0
    
    print(f"✅ Connected to {db_config['host']}:{db_config['port']}/{db_config['database']}")
    
    # Ensure migrations table exists
    if not ensure_migrations_table(conn):
        conn.close()
        return 0, 0
    
    # Get applied migrations
    applied_migrations = get_applied_migrations(conn)
    print(f"📊 Applied migrations: {len(applied_migrations)}")
    
    # Get all migration files
    migration_files = get_migration_files()
    print(f"📁 Total migration files: {len(migration_files)}")
    
    # Find pending migrations
    pending = []
    for version, file_path in migration_files:
        if version not in applied_migrations:
            if target_version and version > target_version:
                break
            pending.append((version, file_path))
    
    if not pending:
        print("✅ All migrations are up to date!")
        conn.close()
        return 0, 0
    
    print(f"\n🔄 Pending migrations: {len(pending)}")
    
    # Apply each pending migration
    applied_count = 0
    failed_count = 0
    
    for version, file_path in pending:
        print(f"\n   📝 Applying {file_path.name}...")
        
        success, error, exec_time = apply_migration(conn, version, file_path, dry_run)
        
        if success:
            print(f"      ✅ Applied successfully ({exec_time}ms)")
            applied_count += 1
        else:
            print(f"      ❌ Failed: {error}")
            failed_count += 1
            break  # Stop on first failure
    
    conn.close()
    
    # Summary
    print(f"\n{'─'*80}")
    print(f"Summary: {applied_count} applied, {failed_count} failed")
    print(f"{'─'*80}")
    
    return applied_count, failed_count


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Run database migrations for Bentley Budget Bot"
    )
    parser.add_argument(
        "--database",
        choices=["mydb", "mansa_bot", "railway", "all"],
        default="all",
        help="Which database to migrate (default: all)"
    )
    parser.add_argument(
        "--target",
        help="Target migration version (e.g., 002)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without applying migrations"
    )
    parser.add_argument(
        "--skip-railway",
        action="store_true",
        help="Skip Railway database (useful for local testing)"
    )
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("DATABASE MIGRATION RUNNER")
    print("=" * 80)
    print(f"Migrations directory: {MIGRATIONS_DIR}")
    print(f"Target version: {args.target or 'latest'}")
    print(f"Dry run: {args.dry_run}")
    print("=" * 80)
    
    # Determine which databases to migrate
    databases_to_run = []
    
    if args.database == "all":
        databases_to_run = [("mydb", DATABASES["mydb"]), ("mansa_bot", DATABASES["mansa_bot"])]
        if not args.skip_railway:
            databases_to_run.append(("railway", DATABASES["railway"]))
    else:
        databases_to_run = [(args.database, DATABASES[args.database])]
    
    # Run migrations for each database
    total_applied = 0
    total_failed = 0
    
    for db_key, db_config in databases_to_run:
        applied, failed = run_migrations_for_database(
            db_key,
            db_config,
            target_version=args.target,
            dry_run=args.dry_run
        )
        total_applied += applied
        total_failed += failed
    
    # Final summary
    print("\n" + "=" * 80)
    print("FINAL SUMMARY")
    print("=" * 80)
    print(f"Total applied: {total_applied}")
    print(f"Total failed: {total_failed}")
    
    if total_failed > 0:
        print("\n❌ Some migrations failed! Review errors above.")
        sys.exit(1)
    elif total_applied > 0:
        print("\n✅ All migrations applied successfully!")
        sys.exit(0)
    else:
        print("\n✅ All databases are up to date!")
        sys.exit(0)


if __name__ == "__main__":
    main()
