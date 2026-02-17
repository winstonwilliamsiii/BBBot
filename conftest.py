"""
Pytest configuration file
Ensures src/ directory is in sys.path for all tests
"""
import sys
from pathlib import Path

# Add project root and src directory to sys.path
project_root = Path(__file__).parent
src_dir = project_root / "src"

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

print(f"✓ Added to sys.path: {project_root}")
print(f"✓ Added to sys.path: {src_dir}")
