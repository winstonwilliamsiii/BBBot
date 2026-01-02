# Mansa Capital Branding - Color Scheme Reference

## 🎨 Official Color Palette (www.mansacap.com)

### Primary Colors
| Color | HEX Code | Usage | RGB |
|-------|----------|-------|-----|
| **Banner Background** | `#0A0A0A` | Deep black/navy background | rgb(10, 10, 10) |
| **Gradient Overlay** | `#111827` | Dark slate/blue overlay | rgb(17, 24, 39) |
| **Primary Text** | `#FFFFFF` | White text for contrast | rgb(255, 255, 255) |
| **Gold Accent** | `#FACC15` | Metrics/numbers highlight | rgb(250, 204, 21) |
| **Teal Accent** | `#14B8A6` | AI/tech emphasis | rgb(20, 184, 166) |

---

## 📂 Implementation

### Color Scheme File
**Location**: `frontend/styles/colors.py`

```python
COLOR_SCHEME = {
    # Core branding colors
    "background": "#0A0A0A",           # Banner background (deep black/navy)
    "secondary": "#111827",            # Gradient overlay (dark slate/blue)
    "text": "#FFFFFF",                 # Primary text (white for contrast)
    "accent_gold": "#FACC15",          # Gold accent (metrics/numbers)
    "accent_teal": "#14B8A6",          # Teal accent (AI/tech emphasis)
    
    # Legacy/computed colors for compatibility
    "primary": "#14B8A6",              # Using teal as primary
    "primary_foreground": "#0A0A0A",   # Dark background
    "card_background": "#111827",      # Dark slate overlay
}
```

---

## 🎯 Usage Guide

### Backgrounds
```css
/* Full app background */
background: linear-gradient(180deg, #0A0A0A 0%, #111827 100%);

/* Card backgrounds */
background: linear-gradient(135deg, #111827 0%, #0A0A0A 100%);
```

### Text Colors
```css
/* Primary text (headings, body) */
color: #FFFFFF;

/* Secondary text (captions, descriptions) */
color: rgba(255, 255, 255, 0.8);

/* Tertiary text (hints, footnotes) */
color: rgba(255, 255, 255, 0.6);
```

### Accent Highlights

#### Gold Accent (`#FACC15`)
**Use for**:
- Metric values and numbers
- Important statistics
- Price displays
- Performance indicators
- Hover states on interactive elements

**Example**:
```css
.metric-value {
    color: #FACC15;
    font-weight: 700;
}
```

#### Teal Accent (`#14B8A6`)
**Use for**:
- AI/tech related features
- Primary buttons
- Active states
- Links and CTAs
- Status indicators (online/active)

**Example**:
```css
button {
    background: linear-gradient(135deg, #14B8A6 0%, #0D9488 100%);
    border: 2px solid #14B8A6;
}
```

---

## 🖼️ Component Styling

### Status Cards
```html
<div style='background: linear-gradient(135deg, #111827 0%, #0A0A0A 100%); 
            border: 1px solid #14B8A6;'>
    <div class='metric-label' style='color: rgba(255,255,255,0.8);'>Status</div>
    <div class='metric-value' style='color: #14B8A6;'>Active</div>
</div>
```

### Mansa Capital Branding Banner
```html
<div style='background: linear-gradient(135deg, #0A0A0A 0%, #111827 100%); 
            padding: 0.75rem 1.5rem; border-radius: 8px; 
            border: 1px solid #FACC15; 
            box-shadow: 0 2px 8px rgba(250, 204, 21, 0.2);'>
    <p style='color: #FACC15; font-size: 0.85rem; font-weight: 600;'>
        ⚡ Powered by Mansa Capital, LLC
    </p>
</div>
```

### Buttons
```css
/* Primary button (Teal) */
button[kind="primary"] {
    background: linear-gradient(135deg, #14B8A6 0%, #0D9488 100%);
    color: #FFFFFF;
    border: 2px solid #14B8A6;
}

button[kind="primary"]:hover {
    border-color: #FACC15;
    box-shadow: 0 4px 16px rgba(20, 184, 166, 0.5);
}
```

### Greeting/Info Boxes
```html
<div style='background: linear-gradient(135deg, #111827 0%, #0A0A0A 100%); 
            border-left: 4px solid #14B8A6; 
            box-shadow: 0 4px 12px rgba(20, 184, 166, 0.2);'>
    <p style='color: #FFFFFF;'>
        👋 <strong style='color: #FACC15;'>Hi, I'm Bentley</strong>
    </p>
    <p style='color: rgba(255,255,255,0.85);'>
        Your AI financial assistant
    </p>
</div>
```

---

## 🎨 Gradient Combinations

### Background Gradients
```css
/* Top to bottom (full page) */
background: linear-gradient(180deg, #0A0A0A 0%, #111827 100%);

/* Diagonal (cards, buttons) */
background: linear-gradient(135deg, #111827 0%, #0A0A0A 100%);

/* Left to right (hover states) */
background: linear-gradient(90deg, rgba(20, 184, 166, 0.2) 0%, rgba(250, 204, 21, 0.1) 100%);
```

### Text Gradients
```css
/* Teal to Gold (brand identity) */
background: linear-gradient(135deg, #14B8A6 0%, #FACC15 100%);
-webkit-background-clip: text;
-webkit-text-fill-color: transparent;
background-clip: text;
```

---

## 🔍 Opacity Guidelines

### Text Transparency
```css
/* Full opacity (primary text) */
color: #FFFFFF;  /* 100% */

/* High opacity (secondary text) */
color: rgba(255, 255, 255, 0.9);  /* 90% */

/* Medium opacity (labels, captions) */
color: rgba(255, 255, 255, 0.8);  /* 80% */

/* Low opacity (hints, disabled) */
color: rgba(255, 255, 255, 0.6);  /* 60% */

/* Very low (backgrounds, subtle) */
color: rgba(255, 255, 255, 0.1);  /* 10% */
```

### Border Transparency
```css
/* Visible borders */
border: 1px solid rgba(20, 184, 166, 0.3);  /* Teal 30% */
border: 1px solid rgba(250, 204, 21, 0.2);  /* Gold 20% */

/* Subtle dividers */
border: 1px solid rgba(255, 255, 255, 0.1);  /* White 10% */
```

---

## ✅ Applied Throughout

### Main Dashboard
- ✅ Title gradient (Teal → Gold)
- ✅ Subtitle white text
- ✅ Background (#0A0A0A → #111827)

### Bentley AI Assistant
- ✅ Status cards (Teal borders, Gold values)
- ✅ Mansa Capital banner (Gold border/text)
- ✅ Buttons (Teal primary, Gold hover)
- ✅ Greeting box (Teal left border, Gold name)

### Metrics & Cards
- ✅ Card backgrounds (gradient)
- ✅ Values in Gold (#FACC15)
- ✅ Delta changes in Teal (#14B8A6)

### Sidebar
- ✅ Background gradient
- ✅ Teal border right
- ✅ Button teal borders
- ✅ Gold hover states

### Dropdowns & Menus
- ✅ Dark slate background
- ✅ Teal left border on hover
- ✅ Gold text on hover

---

## 🚀 Testing

To see the new branding:
```bash
streamlit run streamlit_app.py
```

**What to look for**:
- Dark black/slate background
- White text throughout
- Gold numbers and metrics
- Teal accents on AI features
- "Powered by Mansa Capital, LLC" banner with gold border

---

## 📊 Color Psychology

### Why These Colors?

**Black/Navy (#0A0A0A, #111827)**
- Professional, sophisticated
- Premium financial service feel
- Reduces eye strain for data-heavy interfaces

**Gold (#FACC15)**
- Wealth, success, prosperity
- High-value metrics and achievements
- Attention-drawing for important numbers

**Teal (#14B8A6)**
- Technology, innovation
- Trust and reliability
- Modern fintech aesthetic

**White (#FFFFFF)**
- Clarity and transparency
- Maximum readability
- Clean, premium interface

---

## 🎨 Brand Consistency Checklist

- [x] Background matches Mansa Capital website
- [x] Gold used for financial metrics
- [x] Teal used for AI/tech features
- [x] White text for all content
- [x] Mansa Capital branding banner present
- [x] Gradient combinations consistent
- [x] Hover states use accent colors
- [x] All components follow color scheme

---

**Last Updated**: December 9, 2025  
**Brand Guidelines**: www.mansacap.com  
**Implementation**: Complete ✅
