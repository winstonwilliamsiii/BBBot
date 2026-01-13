"""
🔍 Streamlit Multi-Page Diagnosis Tool
This script checks why pages aren't appearing in localhost:8501
"""

import os
import sys
from pathlib import Path

def diagnose_streamlit_pages():
    print("=" * 70)
    print("🔍 STREAMLIT MULTI-PAGE DIAGNOSIS")
    print("=" * 70)
    
    # Check current directory
    current_dir = Path.cwd()
    print(f"\n📂 Current Directory: {current_dir}")
    
    # Check for streamlit_app.py
    main_app = current_dir / "streamlit_app.py"
    print(f"\n📄 Main App File: {main_app}")
    print(f"   Exists: {'✅ YES' if main_app.exists() else '❌ NO'}")
    
    # Check for pages directory
    pages_dir = current_dir / "pages"
    print(f"\n📁 Pages Directory: {pages_dir}")
    print(f"   Exists: {'✅ YES' if pages_dir.exists() else '❌ NO'}")
    
    if pages_dir.exists():
        # List all page files
        page_files = sorted(pages_dir.glob("*.py"))
        print(f"   Page Count: {len(page_files)}")
        
        if page_files:
            print("\n   📋 Page Files Found:")
            for i, page in enumerate(page_files, 1):
                file_size = page.stat().st_size
                print(f"      {i}. {page.name} ({file_size:,} bytes)")
                
                # Check file content
                try:
                    content = page.read_text(encoding='utf-8')
                    has_streamlit = 'import streamlit' in content or 'from streamlit' in content
                    has_st_write = 'st.' in content
                    print(f"         - Has Streamlit import: {'✅' if has_streamlit else '❌'}")
                    print(f"         - Uses st commands: {'✅' if has_st_write else '❌'}")
                except Exception as e:
                    print(f"         - Error reading file: {e}")
        else:
            print("   ⚠️ No .py files found in pages directory")
    
    # Check Python version
    print(f"\n🐍 Python Version: {sys.version}")
    
    # Check Streamlit installation
    try:
        import streamlit as st
        print(f"\n📦 Streamlit Version: {st.__version__}")
        print(f"   Location: {st.__file__}")
    except ImportError:
        print("\n❌ Streamlit not installed!")
    
    # Check virtual environment
    venv_path = current_dir / ".venv"
    print(f"\n🔧 Virtual Environment: {venv_path}")
    print(f"   Exists: {'✅ YES' if venv_path.exists() else '❌ NO'}")
    
    # Check if running from correct Python
    print(f"\n🎯 Python Executable: {sys.executable}")
    in_venv = '.venv' in sys.executable
    print(f"   Using venv: {'✅ YES' if in_venv else '⚠️ NO (using system Python)'}")
    
    # Check streamlit config
    streamlit_dir = Path.home() / ".streamlit"
    config_file = streamlit_dir / "config.toml"
    print(f"\n⚙️ Streamlit Config: {config_file}")
    print(f"   Exists: {'✅ YES' if config_file.exists() else '❌ NO (using defaults)'}")
    
    if config_file.exists():
        print("   Content:")
        print("   " + "-" * 50)
        try:
            content = config_file.read_text()
            for line in content.split('\n')[:20]:  # First 20 lines
                if line.strip():
                    print(f"   {line}")
        except Exception as e:
            print(f"   Error reading config: {e}")
    
    # Recommendations
    print("\n" + "=" * 70)
    print("💡 RECOMMENDATIONS")
    print("=" * 70)
    
    if not in_venv:
        print("⚠️ You're not using the virtual environment!")
        print("   Run: .venv\\Scripts\\python.exe diagnose_streamlit.py")
    
    if not pages_dir.exists():
        print("❌ Pages directory missing! Create it:")
        print("   mkdir pages")
    
    if pages_dir.exists() and not list(pages_dir.glob("*.py")):
        print("❌ No .py files in pages directory!")
        print("   Add page files like: 01_Page_Name.py")
    
    print("\n📚 Streamlit Multi-Page Requirements:")
    print("   1. Main file must be named 'streamlit_app.py' or use 'app.py'")
    print("   2. Pages must be in 'pages/' subdirectory")
    print("   3. Page files must be .py files")
    print("   4. Page files should start with numbers for ordering (01_, 02_, etc.)")
    print("   5. Run with: streamlit run streamlit_app.py")
    
    print("\n🔍 Debug Steps:")
    print("   1. Make sure you're in: C:\\Users\\winst\\BentleyBudgetBot")
    print("   2. Stop all Python processes")
    print("   3. Run: .venv\\Scripts\\python.exe -m streamlit run streamlit_app.py")
    print("   4. Check browser at: http://localhost:8501")
    print("   5. Look for pages in the sidebar (hamburger menu)")
    
    print("\n" + "=" * 70)
    print("✅ DIAGNOSIS COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    diagnose_streamlit_pages()
