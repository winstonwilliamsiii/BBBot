"""
🚀 Quick Fix: Restart Streamlit with Clean State
This script stops all processes and starts Streamlit cleanly
"""

import subprocess
import sys
import time
from pathlib import Path

def run_command(cmd):
    """Run PowerShell command and return output"""
    result = subprocess.run(
        ["powershell", "-Command", cmd],
        capture_output=True,
        text=True
    )
    return result.stdout, result.returncode

def main():
    print("=" * 70)
    print("🚀 STREAMLIT QUICK FIX - CLEAN RESTART")
    print("=" * 70)
    
    # Check we're in the right directory
    current_dir = Path.cwd()
    print(f"\n📂 Current Directory: {current_dir}")
    
    if not (current_dir / "streamlit_app.py").exists():
        print("❌ ERROR: streamlit_app.py not found!")
        print("   Make sure you're in: C:\\Users\\winst\\BentleyBudgetBot")
        return
    
    # Step 1: Stop all Python processes
    print("\n🛑 Step 1: Stopping all Python processes...")
    stdout, code = run_command("Get-Process python* | Stop-Process -Force")
    if code == 0:
        print("   ✅ All Python processes stopped")
    else:
        print("   ⚠️ No Python processes found or already stopped")
    
    time.sleep(2)
    
    # Step 2: Clear Streamlit cache
    print("\n🧹 Step 2: Clearing Streamlit cache...")
    cache_path = Path.home() / ".streamlit" / "cache"
    if cache_path.exists():
        try:
            import shutil
            shutil.rmtree(cache_path)
            print("   ✅ Cache cleared")
        except Exception as e:
            print(f"   ⚠️ Could not clear cache: {e}")
    else:
        print("   ℹ️ No cache to clear")
    
    # Step 3: Verify pages directory
    print("\n📁 Step 3: Verifying pages directory...")
    pages_dir = current_dir / "pages"
    if pages_dir.exists():
        page_files = list(pages_dir.glob("*.py"))
        print(f"   ✅ Found {len(page_files)} page files")
        for page in page_files:
            print(f"      - {page.name}")
    else:
        print("   ❌ Pages directory not found!")
        return
    
    # Step 4: Start Streamlit
    print("\n🚀 Step 4: Starting Streamlit...")
    print("\n" + "=" * 70)
    print("🌐 Streamlit will start in a new window")
    print("=" * 70)
    print("\n📝 IMPORTANT INSTRUCTIONS:")
    print("   1. Browser will open automatically")
    print("   2. Look for HAMBURGER MENU (☰) in TOP LEFT")
    print("   3. Click the menu to see your pages")
    print("   4. Pages appear in SIDEBAR, not main content!")
    print("\n📱 If pages don't appear:")
    print("   - Try: http://127.0.0.1:8501")
    print("   - Try: Incognito mode (Ctrl+Shift+N)")
    print("   - Try: Clear browser cache (Ctrl+Shift+Delete)")
    print("\n⌨️ To stop Streamlit: Press Ctrl+C in terminal")
    print("=" * 70)
    
    input("\n👉 Press ENTER to start Streamlit...")
    
    # Start Streamlit
    venv_python = current_dir / ".venv" / "Scripts" / "python.exe"
    
    if venv_python.exists():
        print(f"\n🐍 Using: {venv_python}")
        cmd = f'& "{venv_python}" -m streamlit run streamlit_app.py --server.port 8501'
    else:
        print("\n⚠️ Virtual environment not found, using system Python")
        cmd = "streamlit run streamlit_app.py --server.port 8501"
    
    print(f"\n🔧 Running: {cmd}\n")
    
    # Start in new PowerShell window
    subprocess.Popen(
        ["powershell", "-NoExit", "-Command", f"cd '{current_dir}'; {cmd}"],
        creationflags=subprocess.CREATE_NEW_CONSOLE
    )
    
    print("\n✅ Streamlit started in new window!")
    print("🌐 Open your browser to: http://localhost:8501")
    print("🔍 Don't forget to check the SIDEBAR (☰ menu) for pages!")

if __name__ == "__main__":
    main()
