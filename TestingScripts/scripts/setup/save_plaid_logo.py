"""
Plaid Logo Converter
Converts and saves Plaid logo for use in Streamlit app
"""

from PIL import Image
import io
import base64

def save_plaid_logo_from_base64(base64_string, output_path):
    """Save Plaid logo from base64 string"""
    try:
        # Decode base64
        image_data = base64.b64decode(base64_string)
        
        # Open and save image
        img = Image.open(io.BytesIO(image_data))
        img.save(output_path, 'PNG')
        
        print(f"✅ Plaid logo saved to: {output_path}")
        return True
    except Exception as e:
        print(f"❌ Error saving logo: {e}")
        return False


def download_plaid_logo(output_path):
    """Download Plaid logo from official source"""
    import requests
    
    # Try official Plaid logo URL
    urls = [
        'https://plaid.com/assets/img/plaid-logo.png',
        'https://cdn.plaid.com/logo/plaid-logo-600x200.png',
    ]
    
    for url in urls:
        try:
            print(f"📥 Downloading from: {url}")
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                img = Image.open(io.BytesIO(response.content))
                img.save(output_path, 'PNG')
                print(f"✅ Logo downloaded and saved to: {output_path}")
                return True
        except Exception as e:
            print(f"⚠️  Failed: {e}")
            continue
    
    return False


if __name__ == '__main__':
    import sys
    from pathlib import Path
    
    output_path = Path(__file__).parent.parent.parent / "resources" / "images" / "plaid_logo.png"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print("🎨 Plaid Logo Setup")
    print("=" * 60)
    print()
    
    # Check if logo already exists
    if output_path.exists():
        print(f"ℹ️  Logo already exists at: {output_path}")
        print()
        overwrite = input("Do you want to replace it? (y/N): ").strip().lower()
        if overwrite != 'y':
            print("Keeping existing logo.")
            sys.exit(0)
    
    # Try to download
    print("Attempting to download Plaid logo...")
    print()
    
    if download_plaid_logo(str(output_path)):
        print()
        print("=" * 60)
        print("✅ Success! Logo is ready to use.")
        print()
        print("🚀 Next steps:")
        print("   1. Restart Streamlit: streamlit run streamlit_app.py")
        print("   2. Go to Personal Budget page")
        print("   3. You should see the Plaid logo")
    else:
        print()
        print("=" * 60)
        print("⚠️  Automatic download failed.")
        print()
        print("📋 Manual steps:")
        print("   1. Download Plaid logo from: https://plaid.com/company/brand/")
        print(f"   2. Save PNG file to: {output_path}")
        print("   3. Restart Streamlit app")
        print()
        print("💡 Or save your Plaid logo PNG file to:")
        print(f"   {output_path}")
