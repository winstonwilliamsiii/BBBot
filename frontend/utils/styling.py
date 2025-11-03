import streamlit as st
from frontend.styles.colors import COLOR_SCHEME


def apply_custom_styling():
    """Inject custom CSS for the app using COLOR_SCHEME."""
    css = f"""
    <style>
    /* App background */
    .stApp {{
        background: linear-gradient(180deg, {COLOR_SCHEME['background']} 0%, {COLOR_SCHEME['secondary']} 100%);
        color: {COLOR_SCHEME['text']};
    }}

    /* Card style */
    .custom-card {{
        background: {COLOR_SCHEME['card_background']};
        color: {COLOR_SCHEME['text']};
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 4px 14px rgba(2,6,23,0.6);
        margin-bottom: 1rem;
    }}

    .metric-card {{
        background: linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));
        color: {COLOR_SCHEME['text']};
        padding: .75rem 1rem;
        border-radius: 8px;
        text-align: left;
    }}

    .metric-label {{ font-size: 0.9rem; color: rgba(230,238,248,0.9); }}
    .metric-value {{ font-size: 1.6rem; font-weight: 700; margin-top: .25rem; }}
    .metric-delta {{ font-size: 0.9rem; opacity: .9; margin-left: .5rem; }}

    .app-footer {{
        text-align: center;
        padding: 1rem 0.5rem;
        color: rgba(230,238,248,0.7);
        font-size: 0.9rem;
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
    """Render a compact metric card used in small columns."""
    delta_html = f"<span class='metric-delta'>{delta}</span>" if delta else ""
    html = f"""
    <div class='metric-card'>
      <div class='metric-label'>{label}</div>
      <div style='display:flex; align-items:center;'>
        <div class='metric-value'>{value}</div>
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
