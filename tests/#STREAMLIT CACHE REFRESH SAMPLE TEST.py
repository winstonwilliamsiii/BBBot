#STREAMLIT CACHE REFRESH SAMPLE TEST
# tests/test_cache_refresh.py
import streamlit as st

# Example cached function
@st.cache_data
def get_data():
    return {"portfolio": ["AAPL", "MSFT"]}

def test_cache_refresh(monkeypatch):
    # Call once → cached
    data1 = get_data()
    data2 = get_data()
    assert data1 is data2  # same object, cached

    # Clear cache
    st.cache_data.clear()

    # Call again → fresh object
    data3 = get_data()
    assert data1 is not data3