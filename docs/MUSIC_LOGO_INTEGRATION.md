# Music & Logo Integration Guide

## 🎵 Adding Music to Streamlit App

### Option 1: Background Music from Local File

**Best for:** Playing audio automatically on page load

```python
import streamlit as st
import base64

def add_bg_music(audio_file_path):
    """Add background music to the Streamlit app"""
    with open(audio_file_path, "rb") as audio_file:
        audio_bytes = audio_file.read()
        audio_base64 = base64.b64encode(audio_bytes).decode()
    
    audio_html = f"""
    <audio autoplay loop>
        <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
    </audio>
    """
    st.markdown(audio_html, unsafe_allow_html=True)

# Usage in streamlit_app.py
add_bg_music("assets/audio/background_music.mp3")
```

### Option 2: Audio Player with Controls

**Best for:** User-controlled music playback

```python
import streamlit as st

# In streamlit_app.py
st.sidebar.markdown("---")
st.sidebar.subheader("🎵 Background Music")

# Local file upload
audio_file = st.sidebar.file_uploader("Upload Music", type=['mp3', 'wav', 'ogg'])
if audio_file:
    st.sidebar.audio(audio_file, format='audio/mp3')

# Or from local file
with open("assets/audio/bentley_theme.mp3", "rb") as audio_file:
    st.sidebar.audio(audio_file.read(), format='audio/mp3')
```

### Option 3: YouTube Music Integration

**Best for:** Streaming music from YouTube

```python
import streamlit as st
from streamlit_player import st_player

# Install: pip install streamlit-player

st.sidebar.markdown("---")
st.sidebar.subheader("🎵 Music Player")

# YouTube video ID
youtube_url = "https://www.youtube.com/watch?v=YOUR_VIDEO_ID"

st_player(youtube_url, height=80)
```

### Option 4: Spotify Web Player

**Best for:** Professional music integration

```python
import streamlit as st

# Spotify embed
spotify_track_id = "YOUR_TRACK_ID"
spotify_html = f"""
<iframe 
    style="border-radius:12px" 
    src="https://open.spotify.com/embed/track/{spotify_track_id}?utm_source=generator" 
    width="100%" 
    height="80" 
    frameBorder="0" 
    allowfullscreen="" 
    allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture">
</iframe>
"""
st.sidebar.markdown(spotify_html, unsafe_allow_html=True)
```

### Recommended Implementation

Add to `streamlit_app.py` after the title:

```python
def main():
    st.set_page_config(...)
    apply_custom_styling()
    
    # Music player in sidebar
    st.sidebar.markdown("---")
    st.sidebar.subheader("🎵 Ambiance")
    
    music_option = st.sidebar.selectbox(
        "Select Music Source",
        ["None", "Upload File", "YouTube", "Spotify"]
    )
    
    if music_option == "Upload File":
        audio_file = st.sidebar.file_uploader("Upload Music", type=['mp3', 'wav'])
        if audio_file:
            st.sidebar.audio(audio_file)
    
    elif music_option == "YouTube":
        youtube_url = st.sidebar.text_input("YouTube URL")
        if youtube_url:
            st.sidebar.video(youtube_url)
    
    elif music_option == "Spotify":
        st.sidebar.info("Enter Spotify track ID")
        # Add Spotify embed
```

### File Structure for Music

```
BentleyBudgetBot/
├── assets/
│   └── audio/
│       ├── background_music.mp3
│       ├── notification.mp3
│       └── success.wav
└── streamlit_app.py
```

---

## 🎨 Adding Logos

### Option 1: Logo in Header

```python
import streamlit as st
from PIL import Image

# Add to streamlit_app.py after page config
col1, col2, col3 = st.columns([1, 2, 1])

with col1:
    try:
        logo = Image.open("assets/images/mansa_capital_logo.png")
        st.image(logo, width=120)
    except:
        st.markdown("**Mansa Capital**")

with col2:
    st.markdown(f"""
    <h1 style='text-align: center; color: {COLOR_SCHEME['text']};'>
    🤖 Bentley Bot Dashboard
    </h1>
    """, unsafe_allow_html=True)

with col3:
    try:
        partner_logo = Image.open("assets/images/partner_logo.png")
        st.image(partner_logo, width=120)
    except:
        pass
```

### Option 2: Logo in Sidebar

```python
# Add to sidebar at the top
st.sidebar.image("assets/images/mansa_capital_logo.png", use_column_width=True)
st.sidebar.markdown("---")
```

### Option 3: Multiple Partner Logos

```python
# Add after Bentley AI Assistant section
st.markdown("---")
st.markdown("<h4 style='text-align: center; color: rgba(230,238,248,0.7);'>Our Partners</h4>", unsafe_allow_html=True)

col1, col2, col3, col4, col5 = st.columns(5)

logos = [
    ("assets/images/webull_logo.png", "WeBull"),
    ("assets/images/ibkr_logo.png", "IBKR"),
    ("assets/images/binance_logo.png", "Binance"),
    ("assets/images/ninjatrader_logo.png", "NinjaTrader"),
    ("assets/images/meta5_logo.png", "Meta5")
]

for col, (logo_path, name) in zip([col1, col2, col3, col4, col5], logos):
    with col:
        try:
            st.image(logo_path, caption=name, use_column_width=True)
        except:
            st.markdown(f"**{name}**")
```

### Option 4: Logo with URL in Chatbot Header

Update `bentley_chatbot.py`:

```python
st.markdown("""
<div style='text-align: center; margin-bottom: 1rem;'>
    <img src='assets/images/mansa_capital_logo.png' width='100' style='margin-bottom: 0.5rem;'>
    <h2 style='color: #e6eef8; font-size: 2rem;'>
        🤖 Bentley AI Assistant
    </h2>
    <p style='color: rgba(230,238,248,0.5); font-size: 0.7rem;'>
        Powered by <a href='https://mansacapital.com' target='_blank' style='color: #20B2AA;'>Mansa Capital, LLC</a>
    </p>
</div>
""", unsafe_allow_html=True)
```

### Option 5: Base64 Embedded Logo (No File Needed)

```python
import base64

def get_base64_logo(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

logo_base64 = get_base64_logo("assets/images/logo.png")

st.markdown(f"""
<img src='data:image/png;base64,{logo_base64}' width='150'>
""", unsafe_allow_html=True)
```

### Recommended File Structure

```
BentleyBudgetBot/
├── assets/
│   ├── images/
│   │   ├── mansa_capital_logo.png
│   │   ├── bentley_icon.png
│   │   ├── webull_logo.png
│   │   ├── ibkr_logo.png
│   │   ├── binance_logo.png
│   │   ├── ninjatrader_logo.png
│   │   └── meta5_logo.png
│   └── audio/
│       ├── background_music.mp3
│       └── notification.mp3
└── streamlit_app.py
```

---

## 🎯 Quick Implementation Guide

### Step 1: Create Assets Directory

```bash
mkdir -p assets/images assets/audio
```

### Step 2: Add Logo to Chatbot

Update `frontend/components/bentley_chatbot.py`:

```python
# After line with "Powered by Mansa Capital, LLC"
# Add logo option
logo_html = ""
import os
if os.path.exists("assets/images/mansa_capital_logo.png"):
    import base64
    with open("assets/images/mansa_capital_logo.png", "rb") as f:
        logo_base64 = base64.b64encode(f.read()).decode()
    logo_html = f"<img src='data:image/png;base64,{logo_base64}' width='80' style='margin-bottom: 0.5rem;'>"

st.markdown(f"""
<div style='text-align: center; margin-bottom: 1rem;'>
    {logo_html}
    <h2 style='color: #e6eef8; font-size: 2rem;'>
        🤖 Bentley AI Assistant
    </h2>
    ...
""", unsafe_allow_html=True)
```

### Step 3: Add Music Player to Sidebar

Add to `streamlit_app.py` sidebar section:

```python
# After "Portfolio Data Upload" section
st.sidebar.markdown("---")
st.sidebar.subheader("🎵 Music")

# Simple audio player
if os.path.exists("assets/audio/background_music.mp3"):
    with open("assets/audio/background_music.mp3", "rb") as audio_file:
        st.sidebar.audio(audio_file.read())
else:
    audio_upload = st.sidebar.file_uploader("Upload Music", type=['mp3', 'wav'])
    if audio_upload:
        st.sidebar.audio(audio_upload)
```

---

## 📋 Music Sources

### Free Music Sources:
1. **YouTube Audio Library** - https://www.youtube.com/audiolibrary
2. **Free Music Archive** - https://freemusicarchive.org/
3. **Bensound** - https://www.bensound.com/
4. **Incompetech** - https://incompetech.com/
5. **ccMixter** - http://ccmixter.org/

### Commercial Sources:
1. **Epidemic Sound** - https://www.epidemicsound.com/
2. **Artlist** - https://artlist.io/
3. **AudioJungle** - https://audiojungle.net/

### Recommended for Financial Apps:
- Ambient/Lo-fi beats
- Classical piano
- Smooth jazz
- Corporate/Professional tracks

---

## 🖼️ Logo Sources

### Free Logo Design:
1. **Canva** - https://www.canva.com/
2. **LogoMakr** - https://logomakr.com/
3. **Hatchful** - https://www.shopify.com/tools/logo-maker

### Broker Logos:
Download from official press kits:
- WeBull: https://www.webull.com/press
- Interactive Brokers: https://www.interactivebrokers.com/
- Binance: https://www.binance.com/en/official-brand-assets
- NinjaTrader: https://ninjatrader.com/
- MetaTrader: https://www.metatrader5.com/

### Image Formats:
- **PNG** - Best for logos with transparency
- **SVG** - Best for scalable logos
- **JPG** - Best for photos

### Recommended Sizes:
- Header logo: 150x50 pixels
- Sidebar logo: 200x80 pixels
- Partner logos: 100x40 pixels
- Favicon: 32x32 pixels

---

## ⚠️ Important Notes

### Music Considerations:
- **Autoplay** may be blocked by browsers
- Keep volume low by default
- Provide mute/volume controls
- Use compressed audio (MP3, 128kbps)
- Keep files under 5MB for fast loading

### Logo Considerations:
- Use transparent PNG for overlays
- Optimize images (compress to <100KB)
- Use CDN for faster loading
- Provide alt text for accessibility
- Test on different screen sizes

### Legal:
- ✅ Use royalty-free music
- ✅ Get permission for broker logos
- ✅ Credit artists when required
- ❌ Don't use copyrighted music
- ❌ Don't modify official brand logos

---

Need help implementing? Let me know which option you'd like to use!
