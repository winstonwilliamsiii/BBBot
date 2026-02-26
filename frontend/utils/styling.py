import streamlit as st
from frontend.styles.colors import COLOR_SCHEME


def apply_custom_styling():
    """Inject custom CSS for the app using Mansa Capital COLOR_SCHEME."""
    css = f"""
    <style>
    :root {{
        --text-color: {COLOR_SCHEME['text']};
        --secondary-text-color: {COLOR_SCHEME['text']};
    }}

    /* App background with Mansa Capital branding */
    .stApp {{
        background: linear-gradient(180deg, {COLOR_SCHEME['background']} 0%, {COLOR_SCHEME['secondary']} 100%);
        color: {COLOR_SCHEME['text']};
    }}

    .stMarkdown,
    .stMarkdown p,
    .stMarkdown span,
    .stMarkdown li,
    [data-testid="stWidgetLabel"] *,
    [data-testid="stMetricLabel"] *,
    [data-testid="stCaptionContainer"] * {{
        color: {COLOR_SCHEME['text']} !important;
        opacity: 1 !important;
    }}

    /* Card style with Mansa Capital colors */
    .custom-card {{
        background: linear-gradient(135deg, {COLOR_SCHEME['secondary']} 0%, {COLOR_SCHEME['background']} 100%);
        color: {COLOR_SCHEME['text']};
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 4px 14px rgba(20, 184, 166, 0.2);
        border: 1px solid rgba(20, 184, 166, 0.3);
        margin-bottom: 1rem;
    }}

    .metric-card {{
        background: linear-gradient(135deg, {COLOR_SCHEME['secondary']} 0%, {COLOR_SCHEME['background']} 100%);
        color: {COLOR_SCHEME['text']};
        padding: .75rem 1rem;
        border-radius: 8px;
        text-align: left;
        border: 1px solid rgba(20, 184, 166, 0.2);
    }}

    .metric-label {{ font-size: 0.9rem; color: {COLOR_SCHEME['text']}; }}
    .metric-value {{ font-size: 1.6rem; font-weight: 700; margin-top: .25rem; color: {COLOR_SCHEME['accent_gold']}; }}
    .metric-delta {{ font-size: 0.9rem; opacity: .9; margin-left: .5rem; color: {COLOR_SCHEME['accent_teal']}; }}

    .app-footer {{
        text-align: center;
        padding: 1rem 0.5rem;
        color: {COLOR_SCHEME['text']};
        font-size: 0.9rem;
        background: linear-gradient(135deg, {COLOR_SCHEME['background']} 0%, {COLOR_SCHEME['secondary']} 100%);
        border-top: 1px solid rgba(250, 204, 21, 0.2);
    }}

    /* Sidebar styling with Mansa Capital branding */
    [data-testid="stSidebar"] {{
        background: linear-gradient(180deg, {COLOR_SCHEME['background']} 0%, {COLOR_SCHEME['secondary']} 100%) !important;
        border-right: 1px solid rgba(20, 184, 166, 0.2) !important;
    }}

    [data-testid="stSidebar"] * {{
        color: {COLOR_SCHEME['text']} !important;
    }}

    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] .stMarkdown,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span {{
        color: {COLOR_SCHEME['text']} !important;
    }}

    /* Sidebar input labels with gold accent */
    [data-testid="stSidebar"] label {{
        color: {COLOR_SCHEME['text']} !important;
        font-weight: 500 !important;
    }}

    [data-testid="stSidebarNav"] a,
    [data-testid="stSidebarNav"] a span,
    [data-testid="stSidebarNav"] li span {{
        color: {COLOR_SCHEME['text']} !important;
        opacity: 1 !important;
        font-weight: 500 !important;
    }}

    [data-testid="stSidebarNav"] a:hover span {{
        color: {COLOR_SCHEME['accent_gold']} !important;
    }}

    .stTabs [data-baseweb="tab"] {{
        color: {COLOR_SCHEME['text']} !important;
        opacity: 1 !important;
    }}

    .stTabs [data-baseweb="tab"]:hover,
    .stTabs [data-baseweb="tab"][aria-selected="true"] {{
        color: {COLOR_SCHEME['text']} !important;
        opacity: 1 !important;
    }}

    /* Sidebar buttons with teal accent */
    [data-testid="stSidebar"] button {{
        color: {COLOR_SCHEME['text']} !important;
        border: 1px solid {COLOR_SCHEME['accent_teal']} !important;
        background: linear-gradient(135deg, {COLOR_SCHEME['secondary']} 0%, {COLOR_SCHEME['background']} 100%) !important;
    }}
    
    [data-testid="stSidebar"] button:hover {{
        border-color: {COLOR_SCHEME['accent_gold']} !important;
        box-shadow: 0 2px 8px rgba(250, 204, 21, 0.3) !important;
    }}

    /* Sidebar selectbox/input text */
    [data-testid="stSidebar"] input,
    [data-testid="stSidebar"] textarea,
    [data-testid="stSidebar"] [data-baseweb="select"] {{
        color: {COLOR_SCHEME['text']} !important;
    }}

    /* DROPDOWN MENU OPTIONS with Mansa Capital styling */
    [data-baseweb="popover"] {{
        background: linear-gradient(135deg, {COLOR_SCHEME['secondary']} 0%, {COLOR_SCHEME['background']} 100%) !important;
        border: 1px solid rgba(20, 184, 166, 0.3) !important;
    }}
    
    [data-baseweb="menu"] {{
        background: linear-gradient(135deg, {COLOR_SCHEME['secondary']} 0%, {COLOR_SCHEME['background']} 100%) !important;
    }}
    
    [data-baseweb="menu"] li {{
        background-color: {COLOR_SCHEME['secondary']} !important;
        color: {COLOR_SCHEME['text']} !important;
    }}
    
    [data-baseweb="menu"] li:hover {{
        background: linear-gradient(90deg, rgba(20, 184, 166, 0.2) 0%, rgba(250, 204, 21, 0.1) 100%) !important;
        color: {COLOR_SCHEME['accent_gold']} !important;
        border-left: 2px solid {COLOR_SCHEME['accent_teal']} !important;
    }}
    
    [role="option"] {{
        background-color: {COLOR_SCHEME['secondary']} !important;
        color: {COLOR_SCHEME['text']} !important;
    }}
    
    [role="option"]:hover {{
        background: linear-gradient(90deg, rgba(20, 184, 166, 0.2) 0%, rgba(250, 204, 21, 0.1) 100%) !important;
        color: {COLOR_SCHEME['accent_gold']} !important;
    }}
    
    [data-baseweb="select"] > div {{
        background: linear-gradient(135deg, {COLOR_SCHEME['secondary']} 0%, {COLOR_SCHEME['background']} 100%) !important;
        color: {COLOR_SCHEME['text']} !important;
        border: 1px solid rgba(20, 184, 166, 0.3) !important;
    }}
    </style>
    """

    st.markdown(css, unsafe_allow_html=True)


def create_custom_card(title: str, body: str):
    """Render a simple custom card with title and body."""
    html = f"""
    <div class='custom-card'>
      <h3 style='margin:0 0 .5rem 0; color: {COLOR_SCHEME['primary']};'>{title}</h3>
      <div style='color: {COLOR_SCHEME['text']};'>{body}</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def create_metric_card(label: str, value: str, delta: str = None):
    """Render a compact metric card with Mansa Capital branding."""
    delta_html = f"<span class='metric-delta'>{delta}</span>" if delta else ""
    html = f"""
    <div class='metric-card' style='border: 1px solid rgba(20, 184, 166, 0.3);'>
      <div class='metric-label'>{label}</div>
      <div style='display:flex; align-items:center;'>
        <div class='metric-value' style='color: {COLOR_SCHEME['accent_gold']};'>{value}</div>
        {delta_html}
      </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def add_footer():
    st.markdown("""
    <div class='app-footer'>
      <small>Built with ❤️ by the BBBot team — © {year}</small>
    </div>
    """.format(year=__import__('datetime').datetime.now().year), unsafe_allow_html=True)
