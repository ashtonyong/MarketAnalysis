import streamlit as st
import pandas as pd
import yfinance as yf

# Use a universe of ~50 major stocks for performance
TICKER_UNIVERSE = [
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'NFLX',
    'AMD', 'INTC', 'QCOM', 'AVGO', 'TXN', 'CSCO', 'CRM', 'ADBE',
    'JPM', 'BAC', 'WFC', 'C', 'GS', 'MS', 'AXP', 'V', 'MA',
    'JNJ', 'PFE', 'MRK', 'ABBV', 'LLY', 'UNH', 'CVS',
    'PG', 'KO', 'PEP', 'COST', 'WMT', 'TGT', 'HD', 'LOW',
    'XOM', 'CVX', 'COP', 'SLB', 'EOG',
    'BA', 'CAT', 'HON', 'GE', 'MMM', 'DE', 'LMT', 'RTX',
    'DIS', 'CMCSA', 'TMUS', 'VZ', 'T'
]

@st.cache_data(ttl=3600)
def fetch_screener_data(tickers):
    """Fetch fundamental data for the universe."""
    data = []
    
    # Batch fetching might be tricky with info, yfinance doesn't fully support batch info well.
    # We iterate. Limit universe to avoid timeouts.
    
    progress = st.progress(0)
    total = len(tickers)
    
    for i, t in enumerate(tickers):
        try:
            ticker = yf.Ticker(t)
            info = ticker.fast_info # Fast info is limited. We need full info for PE/PEG.
            # Fast access for price/mcap works.
            # For fundamentals, we need 'info' property which triggers API call per ticker.
            info_full = ticker.info
            
            data.append({
                "Ticker": t,
                "Sector": info_full.get("sector", "N/A"),
                "Price": info_full.get("currentPrice", 0),
                "Market Cap": info_full.get("marketCap", 0),
                "P/E": info_full.get("trailingPE", None),
                "Forward P/E": info_full.get("forwardPE", None),
                "PEG": info_full.get("pegRatio", None),
                "P/S": info_full.get("priceToSalesTrailing12Months", None),
                "ROE": info_full.get("returnOnEquity", None),
                "Profit Margin": info_full.get("profitMargins", None),
                "Debt/Eq": info_full.get("debtToEquity", None),
                "Div Potential": info_full.get("dividendYield", 0)
            })
        except Exception:
            pass
            
        progress.progress((i + 1) / total)
        
    progress.empty()
    return pd.DataFrame(data)

def render_fundamental_screener(ticker):
    """Render the Fundamental Screener tab."""
    st.markdown("###  Fundamental Screener")
    st.caption(f"Screening Universe: {len(TICKER_UNIVERSE)} Major US Stocks")
    
    col_filter, col_res = st.columns([1, 4])
    
    with col_filter:
        st.markdown("**Filters**")
        
        min_pe = st.number_input("Max P/E Ratio", value=50.0, step=5.0)
        max_peg = st.number_input("Max PEG Ratio", value=2.0, step=0.1)
        min_roe = st.number_input("Min ROE %", value=10.0, step=5.0)
        min_margin = st.number_input("Min Profit Margin %", value=10.0, step=5.0)
        
        sector = st.selectbox("Sector", ["All", "Technology", "Financial Services", "Healthcare", "Consumer Cyclical", "Energy", "Industrials"])
        
        if st.button("Run Screener", key="run_screen"):
            st.session_state['screen_run'] = True
            
    with col_res:
        if st.session_state.get('screen_run'):
            df = fetch_screener_data(TICKER_UNIVERSE)
            
            if not df.empty:
                # Apply Filters
                # Convert ROE/Margin to percentage (info returns decimal 0.15 for 15%)
                if 'ROE' in df.columns:
                    mask = (
                        ((df['P/E'] <= min_pe) | (df['P/E'].isna())) & # Handle NaN usually means negative earnings or missing
                        ((df['PEG'] <= max_peg) | (df['PEG'].isna())) &
                        ((df['ROE'] * 100 >= min_roe) | (df['ROE'].isna())) &
                        ((df['Profit Margin'] * 100 >= min_margin) | (df['Profit Margin'].isna()))
                    )
                    
                    if sector != "All":
                        mask = mask & (df['Sector'] == sector)
                        
                    results = df[mask].copy()
                    
                    # Formatting for display
                    # Sort by Market Cap desc
                    results = results.sort_values("Market Cap", ascending=False)
                    
                    # Display Table
                    st.markdown(f"**Found {len(results)} matches**")
                    
                    st.dataframe(
                        results,
                        column_config={
                            "Market Cap": st.column_config.NumberColumn("Mkt Cap", format="$%.2e"),
                            "Price": st.column_config.NumberColumn("Price", format="$%.2f"),
                            "P/E": st.column_config.NumberColumn("P/E", format="%.1f"),
                            "PEG": st.column_config.NumberColumn("PEG", format="%.2f"),
                            "ROE": st.column_config.NumberColumn("ROE", format="%.1%"),
                            "Profit Margin": st.column_config.NumberColumn("Margin", format="%.1%")
                        },
                        use_container_width=True,
                        hide_index=True
                    )
                    
                    # Top Picks Card
                    if not results.empty:
                        best = results.iloc[0]
                        st.success(f" **Top Pick:** {best['Ticker']} ({best['Sector']}) - P/E: {best['P/E']:.1f}, PEG: {best['PEG']}")
                else:
                    st.error("Data processing error.")
            else:
                st.error("Failed to fetch data.")
