"""
DCF Analysis Widget for Bentley Bot Dashboard
==============================================
Streamlit UI component for equity DCF valuation.
"""

import streamlit as st
import pandas as pd
from typing import Optional, Dict

try:
    from frontend.components.dcf_analysis import run_equity_dcf, MYSQL_AVAILABLE
    DCF_AVAILABLE = True
except ImportError:
    DCF_AVAILABLE = False


def render_dcf_widget():
    """
    Render the DCF analysis widget on the dashboard.
    Allows users to input a ticker and view fundamental valuation.
    Supports both manual ticker entry and CSV upload for batch analysis.
    """
    if not DCF_AVAILABLE:
        st.warning("📊 DCF Analysis requires MySQL database configuration")
        return
    
    st.markdown("### 📈 Fundamental Analysis - DCF Valuation")
    
    # Analysis mode selector
    analysis_mode = st.radio(
        "Analysis Mode",
        options=["Single Ticker", "CSV Upload (Batch)"],
        horizontal=True,
        help="Choose single ticker or upload CSV for batch DCF analysis",
        key="dcf_mode"
    )
    
    with st.expander("ℹ️ About DCF Analysis", expanded=False):
        st.markdown("""
        **Discounted Cash Flow (DCF)** analysis estimates a stock's intrinsic value by:
        
        1. 📊 Analyzing historical free cash flow
        2. 📈 Projecting future cash flows (5-10 years)
        3. 💰 Discounting to present value
        4. ✅ Comparing to current market price
        
        **Classification:**
        - 🟢 **Undervalued**: Market price significantly below intrinsic value
        - 🔵 **Fairly Valued**: Market price near intrinsic value
        - 🔴 **Overvalued**: Market price significantly above intrinsic value
        
        **CSV Upload Format:**
        For batch analysis, upload a CSV with column: `Ticker` (or `ticker`, `Symbol`, `symbol`)
        Example: AAPL, MSFT, GOOGL (one per row)
        """)
    
    # Handle CSV Upload Mode
    if analysis_mode == "CSV Upload (Batch)":
        render_dcf_csv_upload()
        return
    
    # Single Ticker Mode - Input form
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        ticker = st.text_input(
            "Stock Ticker",
            value="",
            placeholder="e.g., AAPL",
            help="Enter stock ticker symbol (must exist in database)",
            key="dcf_ticker"
        ).upper()
    
    with col2:
        discount_rate = st.number_input(
            "Discount Rate (%)",
            min_value=1.0,
            max_value=30.0,
            value=10.0,
            step=0.5,
            help="Expected rate of return (WACC)",
            key="dcf_discount"
        ) / 100
    
    with col3:
        term_years = st.selectbox(
            "Projection Years",
            options=[5, 7, 10],
            index=2,
            help="Forecast horizon",
            key="dcf_years"
        )
    
    # Advanced settings
    with st.expander("⚙️ Advanced Settings", expanded=False):
        col_adv1, col_adv2 = st.columns(2)
        
        with col_adv1:
            perp_growth = st.number_input(
                "Terminal Growth Rate (%)",
                min_value=0.0,
                max_value=5.0,
                value=2.0,
                step=0.1,
                help="Perpetual growth rate for terminal value",
                key="dcf_perp"
            ) / 100
        
        with col_adv2:
            margin_of_safety = st.number_input(
                "Margin of Safety (%)",
                min_value=0.0,
                max_value=50.0,
                value=15.0,
                step=5.0,
                help="Buffer for valuation classification",
                key="dcf_mos"
            ) / 100
    
    # Run analysis button
    if st.button("🔬 Run DCF Analysis", type="primary", key="run_dcf"):
        if not ticker:
            st.warning("⚠️ Please enter a ticker symbol")
            return
        
        try:
            with st.spinner(f"Analyzing {ticker}..."):
                result = run_equity_dcf(
                    ticker=ticker,
                    discount_rate=discount_rate,
                    term_years=term_years,
                    perp_growth=perp_growth,
                    margin_of_safety=margin_of_safety,
                )
            
            # Display results
            display_dcf_results(result)
            
        except ValueError as e:
            st.error(f"❌ Data Error: {str(e)}")
            st.info("💡 Make sure the ticker exists in the database with at least 5 years of historical fundamentals.")
        except Exception as e:
            st.error(f"❌ Analysis Failed: {str(e)}")
            st.info("💾 Ensure MySQL database is configured correctly with environment variables.")


def display_dcf_results(result: Dict):
    """Display DCF analysis results in a formatted layout."""
    
    ticker = result['ticker']
    current_price = result['current_price']
    intrinsic_value = result['intrinsic_value_per_share']
    valuation = result['valuation_label']
    upside = result['upside_percent']
    
    # Valuation badge color
    if valuation == "Undervalued":
        val_color = "#10b981"  # green
        val_emoji = "🟢"
    elif valuation == "Overvalued":
        val_color = "#ef4444"  # red
        val_emoji = "🔴"
    else:
        val_color = "#3b82f6"  # blue
        val_emoji = "🔵"
    
    # Header
    st.markdown(f"""
    <div style='background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); 
                padding: 2rem; border-radius: 12px; margin: 1rem 0;
                border: 2px solid {val_color};'>
        <h2 style='color: white; margin: 0; text-align: center;'>
            {val_emoji} {ticker} - {valuation}
        </h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Key metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Current Price",
            f"${current_price:.2f}",
            help="Latest market price"
        )
    
    with col2:
        st.metric(
            "Intrinsic Value",
            f"${intrinsic_value:.2f}",
            f"{upside:+.1f}%",
            help="DCF-calculated fair value per share"
        )
    
    with col3:
        delta_color = "normal" if upside > 0 else "inverse"
        st.metric(
            "Upside/Downside",
            f"{upside:+.1f}%",
            delta_color=delta_color,
            help="Percentage difference from intrinsic value"
        )
    
    # Detailed analysis
    st.markdown("---")
    st.markdown("#### 📊 Analysis Details")
    
    col_det1, col_det2 = st.columns(2)
    
    with col_det1:
        st.markdown(f"""
        **Financial Metrics:**
        - Total Equity Value: ${result['equity_value_total']:,.0f}
        - Growth Rate Used: {result['growth_rate_used']:.2%}
        - Projection Period: {result['term_years']} years
        """)
    
    with col_det2:
        st.markdown(f"""
        **Model Parameters:**
        - Discount Rate (WACC): {result['discount_rate']:.2%}
        - Terminal Growth: {result['perp_growth']:.2%}
        - Margin of Safety: {result['margin_of_safety']:.2%}
        """)
    
    # Investment recommendation
    st.markdown("---")
    st.markdown("#### 💡 Investment Perspective")
    
    if valuation == "Undervalued":
        st.success(f"""
        **{ticker}** appears **undervalued** at current prices.
        
        - Market Price: **${current_price:.2f}**
        - Fair Value: **${intrinsic_value:.2f}**
        - Potential Upside: **{upside:.1f}%**
        
        ⚠️ **Note:** This is a quantitative assessment based on DCF fundamentals. 
        Always consider qualitative factors, market conditions, and consult a financial advisor.
        """)
    elif valuation == "Overvalued":
        st.warning(f"""
        **{ticker}** appears **overvalued** at current prices.
        
        - Market Price: **${current_price:.2f}**
        - Fair Value: **${intrinsic_value:.2f}**
        - Potential Downside: **{upside:.1f}%**
        
        ⚠️ **Note:** Overvaluation doesn't mean immediate decline. Growth expectations, 
        market sentiment, and other factors may justify premium pricing.
        """)
    else:
        st.info(f"""
        **{ticker}** appears **fairly valued** at current prices.
        
        - Market Price: **${current_price:.2f}**
        - Fair Value: **${intrinsic_value:.2f}**
        - Difference: **{upside:.1f}%**
        
        💡 Current market price is within {result['margin_of_safety']:.0%} of calculated intrinsic value.
        """)
    
    # Timestamp
    st.caption(f"Analysis completed at: {result['timestamp']}")


def render_dcf_csv_upload():
    """
    Handle CSV upload for batch DCF analysis.
    Allows users to upload a CSV file with ticker symbols for bulk analysis.
    """
    st.markdown("#### 📁 Upload Stock Portfolio CSV")
    
    # CSV format helper
    with st.expander("📋 CSV Format Requirements", expanded=False):
        st.markdown("""
        **Required Column:**
        - `Ticker` (or `ticker`, `Symbol`, `symbol`) - Stock ticker symbols
        
        **Example CSV:**
        ```
        Ticker
        AAPL
        MSFT
        GOOGL
        AMZN
        ```
        
        **Optional:** You can include other columns - they will be displayed but not used for DCF.
        """)
        
        # Download template button
        template_df = pd.DataFrame({
            'Ticker': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
        })
        csv_template = template_df.to_csv(index=False)
        st.download_button(
            label="📥 Download CSV Template",
            data=csv_template,
            file_name="dcf_analysis_template.csv",
            mime="text/csv",
            key="dcf_csv_template"
        )
    
    # File uploader
    uploaded_file = st.file_uploader(
        "Choose a CSV file",
        type=['csv'],
        help="Upload CSV with stock tickers for DCF analysis",
        key="dcf_csv_upload"
    )
    
    # Analysis parameters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        discount_rate = st.number_input(
            "Discount Rate (%)",
            min_value=1.0,
            max_value=30.0,
            value=10.0,
            step=0.5,
            key="dcf_csv_discount"
        ) / 100
    
    with col2:
        term_years = st.selectbox(
            "Projection Years",
            options=[5, 7, 10],
            index=2,
            key="dcf_csv_years"
        )
    
    with col3:
        perp_growth = st.number_input(
            "Terminal Growth (%)",
            min_value=0.0,
            max_value=5.0,
            value=2.0,
            step=0.1,
            key="dcf_csv_perp"
        ) / 100
    
    if uploaded_file is not None:
        try:
            # Read CSV
            df_upload = pd.read_csv(uploaded_file)
            
            # Identify ticker column (flexible naming)
            ticker_col = None
            for possible_name in ['Ticker', 'ticker', 'Symbol', 'symbol', 'TICKER', 'SYMBOL']:
                if possible_name in df_upload.columns:
                    ticker_col = possible_name
                    break
            
            if ticker_col is None:
                st.error("❌ CSV must contain a 'Ticker' or 'Symbol' column")
                return
            
            # Extract tickers and clean
            tickers = df_upload[ticker_col].dropna().str.strip().str.upper().unique().tolist()
            
            st.success(f"✅ Loaded {len(tickers)} unique tickers from CSV")
            st.dataframe(df_upload.head(10), use_container_width=True)
            
            # Analyze button
            if st.button("🔬 Run Batch DCF Analysis", type="primary", key="run_batch_dcf"):
                results_list = []
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for i, ticker in enumerate(tickers):
                    status_text.text(f"Analyzing {ticker} ({i+1}/{len(tickers)})...")
                    
                    try:
                        result = run_equity_dcf(
                            ticker=ticker,
                            discount_rate=discount_rate,
                            term_years=term_years,
                            perp_growth=perp_growth,
                            margin_of_safety=0.15  # Default 15%
                        )
                        
                        results_list.append({
                            'Ticker': ticker,
                            'Current Price': f"${result['current_price']:.2f}",
                            'Intrinsic Value': f"${result['intrinsic_value_per_share']:.2f}",
                            'Upside/Downside': f"{result['upside_percent']:+.1f}%",
                            'Valuation': result['valuation_label'],
                            'Status': '✅'
                        })
                    except Exception as e:
                        results_list.append({
                            'Ticker': ticker,
                            'Current Price': 'N/A',
                            'Intrinsic Value': 'N/A',
                            'Upside/Downside': 'N/A',
                            'Valuation': 'Error',
                            'Status': f'❌ {str(e)[:50]}'
                        })
                    
                    progress_bar.progress((i + 1) / len(tickers))
                
                status_text.text("Analysis complete!")
                
                # Display results
                st.markdown("---")
                st.markdown("### 📊 Batch DCF Results")
                
                results_df = pd.DataFrame(results_list)
                
                # Count valuations
                undervalued = len(results_df[results_df['Valuation'] == 'Undervalued'])
                overvalued = len(results_df[results_df['Valuation'] == 'Overvalued'])
                fair = len(results_df[results_df['Valuation'] == 'Fairly Valued'])
                errors = len(results_df[results_df['Valuation'] == 'Error'])
                
                # Summary metrics
                col_sum1, col_sum2, col_sum3, col_sum4 = st.columns(4)
                
                with col_sum1:
                    st.metric("🟢 Undervalued", undervalued)
                with col_sum2:
                    st.metric("🔴 Overvalued", overvalued)
                with col_sum3:
                    st.metric("🔵 Fair", fair)
                with col_sum4:
                    st.metric("❌ Errors", errors)
                
                # Display full results table
                # Color code the Valuation column
                def highlight_valuation(row):
                    if row['Valuation'] == 'Undervalued':
                        return ['background-color: #10b98133'] * len(row)
                    elif row['Valuation'] == 'Overvalued':
                        return ['background-color: #ef444433'] * len(row)
                    elif row['Valuation'] == 'Fairly Valued':
                        return ['background-color: #3b82f633'] * len(row)
                    else:
                        return ['background-color: #71717133'] * len(row)
                
                styled_df = results_df.style.apply(highlight_valuation, axis=1)
                st.dataframe(styled_df, use_container_width=True)
                
                # Download results
                csv_results = results_df.to_csv(index=False)
                st.download_button(
                    label="📥 Download DCF Results CSV",
                    data=csv_results,
                    file_name=f"dcf_batch_results_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    key="download_batch_results"
                )
                
        except Exception as e:
            st.error(f"❌ Error reading CSV file: {str(e)}")
            st.info("Please ensure your CSV is properly formatted with a 'Ticker' or 'Symbol' column.")


def render_dcf_mini_widget():
    """
    Compact version of DCF widget for dashboard overview.
    Shows quick ticker lookup only.
    """
    if not DCF_AVAILABLE:
        return
    
    st.markdown("#### 📈 Quick DCF Check")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        ticker = st.text_input(
            "Ticker",
            value="",
            placeholder="e.g., AAPL",
            label_visibility="collapsed",
            key="dcf_mini_ticker"
        ).upper()
    
    with col2:
        analyze_btn = st.button("Analyze", key="dcf_mini_btn")
    
    if analyze_btn and ticker:
        try:
            with st.spinner("..."):
                result = run_equity_dcf(ticker=ticker)
            
            val = result['valuation_label']
            upside = result['upside_percent']
            
            if val == "Undervalued":
                st.success(f"🟢 {ticker}: Undervalued ({upside:+.1f}%)")
            elif val == "Overvalued":
                st.error(f"🔴 {ticker}: Overvalued ({upside:+.1f}%)")
            else:
                st.info(f"🔵 {ticker}: Fair ({upside:+.1f}%)")
                
        except Exception as e:
            st.error(f"❌ {str(e)}")
