import streamlit as st

# Set the current color format for the Streamlit app
st.set_page_config(page_title="Streamlit React App", page_icon=":sparkles:", layout="wide")

# Title of the app
st.title("Welcome to the Streamlit React App")

# Example color format usage
st.markdown(
    """
    <style>
    .main {
        background-color: #f0f2f5;  /* Light gray background */
        color: #333;  /* Dark text color */
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Main content of the app
st.write("This is a simple Streamlit app integrated with React.")