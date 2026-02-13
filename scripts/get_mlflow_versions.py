"""
Get available MLFlow migration versions
"""

import os
from pathlib import Path

# Find MLFlow installation directory
import mlflow
mlflow_path = Path(mlflow.__file__).parent

# Check db_migrations directory
migrations_dir = mlflow_path / 'store' / 'db_migrations' / 'versions'

if migrations_dir.exists():
    print(f"MLFlow migrations directory: {migrations_dir}\n")
    
    # List all migration files
    migration_files = sorted(migrations_dir.glob('*.py'))
    
    print("Available migration versions:")
    for f in migration_files[-5:]:  # Show last 5
        print(f"  - {f.name}")
    
    # Extract version hashes from filenames
    versions = []
    for f in migration_files:
        name = f.stem
        if '_' in name:
            version = name.split('_')[0]
            versions.append(version)
    
    if versions:
        print(f"\nLatest version hash: {versions[-1]}")
else:
    print(f"Migrations directory not found: {migrations_dir}")
