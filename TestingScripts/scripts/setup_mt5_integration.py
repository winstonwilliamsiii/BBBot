"""
Quick start script for MT5 integration
Sets up environment and runs basic tests
"""

import os
import sys
from pathlib import Path

def check_dependencies():
    """Check if required packages are installed"""
    print("Checking dependencies...")
    
    required_packages = {
        'requests': 'requests',
        'streamlit': 'streamlit',
        'plotly': 'plotly',
        'pandas': 'pandas'
    }
    
    missing = []
    
    for package, pip_name in required_packages.items():
        try:
            __import__(package)
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package} (missing)")
            missing.append(pip_name)
    
    if missing:
        print(f"\n⚠️  Missing packages: {', '.join(missing)}")
        print(f"Install with: pip install {' '.join(missing)}")
        return False
    
    print("✅ All dependencies installed\n")
    return True


def check_env_file():
    """Check if .env file exists"""
    print("Checking environment configuration...")
    
    env_file = Path(".env")
    
    if not env_file.exists():
        print("  ⚠️  .env file not found")
        print("  Creating .env file from example...")
        
        # Create basic .env file
        with open(env_file, 'w') as f:
            f.write("# Bentley Budget Bot - Environment Variables\n\n")
            f.write("# MetaTrader 5 Configuration\n")
            f.write("MT5_API_URL=http://localhost:8000\n")
            f.write("MT5_USER=\n")
            f.write("MT5_PASSWORD=\n")
            f.write("MT5_HOST=\n")
            f.write("MT5_PORT=443\n")
        
        print("  ✅ Created .env file (please fill in your MT5 credentials)\n")
    else:
        print("  ✅ .env file exists\n")
    
    return True


def check_file_structure():
    """Verify all MT5 files are in place"""
    print("Checking file structure...")
    
    required_files = [
        "frontend/utils/mt5_connector.py",
        "frontend/components/mt5_dashboard.py",
        "pages/6_🔌_MT5_Trading.py",
        "examples/mt5_usage_examples.py",
        "docs/MT5_INTEGRATION.md"
    ]
    
    all_present = True
    
    for file_path in required_files:
        path = Path(file_path)
        if path.exists():
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ {file_path} (missing)")
            all_present = False
    
    if all_present:
        print("✅ All MT5 files present\n")
    else:
        print("⚠️  Some files are missing\n")
    
    return all_present


def run_test():
    """Run the test script"""
    print("Running integration tests...")
    print("-" * 60)
    
    # Import and run test
    try:
        import test_mt5_connection
        test_mt5_connection.main()
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    
    return True


def print_next_steps():
    """Print what to do next"""
    print("\n" + "=" * 60)
    print("🚀 NEXT STEPS")
    print("=" * 60)
    
    print("\n1. Configure MT5 credentials in .env file:")
    print("   - Edit .env file")
    print("   - Set MT5_USER, MT5_PASSWORD, MT5_HOST")
    
    print("\n2. Set up MT5 REST API Server:")
    print("   - You need a server implementing MT5 REST API")
    print("   - Or build one using MetaTrader 5 Python package")
    
    print("\n3. Test the connection:")
    print("   python test_mt5_connection.py")
    
    print("\n4. Launch Streamlit app:")
    print("   streamlit run streamlit_app.py")
    print("   Then navigate to: 🔌 MT5 Trading")
    
    print("\n5. Try example scripts:")
    print("   python examples/mt5_usage_examples.py")
    
    print("\n📚 Full documentation: docs/MT5_INTEGRATION.md")
    print("=" * 60 + "\n")


def main():
    """Main setup function"""
    print("\n" + "╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "MT5 INTEGRATION - QUICK START" + " " * 19 + "║")
    print("╚" + "=" * 58 + "╝\n")
    
    # Change to script directory
    os.chdir(Path(__file__).parent)
    
    # Run checks
    checks = [
        ("Dependencies", check_dependencies),
        ("Environment File", check_env_file),
        ("File Structure", check_file_structure),
    ]
    
    all_passed = True
    for check_name, check_func in checks:
        if not check_func():
            all_passed = False
    
    if all_passed:
        print("✅ Setup checks passed!")
        print("\nRunning integration tests...\n")
        run_test()
    else:
        print("⚠️  Some checks failed. Please resolve issues above.")
    
    # Print next steps
    print_next_steps()


if __name__ == "__main__":
    main()
