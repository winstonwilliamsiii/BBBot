#streamlit_investment_pg_integration
# pages/investment.py
import streamlit as st
import pandas as pd
from sqlalchemy import create_engine

engine = create_engine("mysql+pymysql://user:pass@localhost:3306/bbbot1")

def get_tickers():
    return pd.read_sql("SELECT ticker, name FROM companies ORDER BY ticker", con=engine)

def get_ratios(tickers):
    q = """
    SELECT d.ticker, d.report_date, d.pe_ratio, d.pb_ratio, d.ev_ebit, d.ev_ebitda, d.roa, d.roi, d.noi
    FROM fundamentals_derived d
    WHERE d.ticker IN ({})
    ORDER BY d.report_date DESC
    """.format(",".join(["%s"]*len(tickers)))
    return pd.read_sql(q, con=engine, params=tickers)

def login_required():
    # integrate with your existing login/session system
    return True

def main():
    if not login_required():
        st.error("Please log in to view the Investment page.")
        st.stop()

    st.title("Investment Analytics")
    tickers_df = get_tickers()
    selected = st.multiselect("Select tickers", tickers_df["ticker"].tolist(), default=tickers_df["ticker"].tolist()[:5])

    if selected:
        ratios = get_ratios(selected)
        st.dataframe(ratios)

        # Comparison charts
        st.subheader("P/E comparison (latest)")
        latest = ratios.sort_values(["ticker","report_date"]).groupby("ticker").head(1)
        st.bar_chart(latest.set_index("ticker")["pe_ratio"])

        st.subheader("EV/EBITDA comparison (latest)")
        st.bar_chart(latest.set_index("ticker")["ev_ebitda"])

        st.subheader("ROA vs ROI (latest)")
        st.scatter_chart(latest[["roa","roi"]], use_container_width=True)

if __name__ == "__main__":
    main()

