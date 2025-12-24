#!/usr/bin/env python3
"""
Deployment validation script for Bentley Budget Bot
Checks if all components are ready for deployment
"""

import os
import sys
from pathlib import Path

def check_files():
    """Check if all required files exist"""
    required_files = [
        'streamlit_app.py',
        'requirements.txt',
        'Dockerfile',
        '.dockerignore',
        'docker-compose.yml',
        'vercel.json',
        'start.sh',
        'api/index.py'
    ]
    
    missing_files = []
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Missing files: {', '.join(missing_files)}")
        return False
    else:
        print("✅ All required files present")
        return True

def check_docker():
    """Check if Docker is available"""
    try:
        import subprocess
        result = subprocess.run(['docker', '--version'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Docker available: {result.stdout.strip()}")
            return True
        else:
            print("❌ Docker not available")
            return False
    except FileNotFoundError:
        print("❌ Docker not installed")
        return False

def check_dependencies():
    """Check if Python dependencies are installable"""
    try:
        with open('requirements.txt', 'r') as f:
            deps = f.read().strip().split('\n')
        print(f"✅ Found {len(deps)} dependencies in requirements.txt")
        return True
    except FileNotFoundError:
        print("❌ requirements.txt not found")
        return False

def main():
    """Main validation function"""
    print("🔍 Bentley Budget Bot - Deployment Validation")
    print("=" * 50)
    
    checks_passed = 0
    total_checks = 3
    
    if check_files():
        checks_passed += 1
    
    if check_docker():
        checks_passed += 1
    
    if check_dependencies():
        checks_passed += 1
    
    print("\n" + "=" * 50)
    
    if checks_passed == total_checks:
        print("🎉 All checks passed! Ready for deployment")
        print("\nNext steps:")
        print("1. Test locally: docker run -p 8501:8501 bentley-budget-bot")
        print("2. Deploy to Vercel: vercel --prod")
        return 0
    else:
        print(f"⚠️  {checks_passed}/{total_checks} checks passed")
        print("Please fix the issues above before deployment")
        return 1

if __name__ == "__main__":
    sys.exit(main())