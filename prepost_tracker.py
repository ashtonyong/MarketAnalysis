import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import streamlit as st
from datetime import datetime, time as dt_time

class PrePostTracker:
    def __init__(self, tickers):
        self.tickers = tickers
        
    def fetch_data(self) -> pd.DataFrame:
        results = []
        
        for ticker in self.tickers:
            try:
                # Get today's data with prepost
                # 1m interval, 1d period, prepost=True
                # Note: yfinance might return empty if market is closed or no pre-market yet.
                df = yf.download(ticker, period="1d", interval="1m", prepost=True, progress=False)
                
                if df.empty:
                    continue
                    
                # Identify session
                # 09:30 - 16:00 ET is RTH
                # Before 09:30 is Pre-Market
                # After 16:00 is Post-Market
                
                # Convert index to ET (US/Eastern) if possible, but yf usually returns local/UTC?
                # yf usually returns timezone aware timestamps (America/New_York)
                
                if df.index.tz is None:
                    # Assume UTC if none, but usually it is localized
                    pass
                else:
                    # Convert to Eastern Time just in case
                    df = df.tz_convert("America/New_York")
                
                # Filter for Pre/Post
                # Pre: < 09:30
                # Post: > 16:00
                
                # Ensure scalar
                last_close = float(df['Close'].iloc[-1])
                
                # Previous day close (regular session)
                info = yf.Ticker(ticker).fast_info
                prev_close = float(info.previous_close)
                
                change_pct = (last_close - prev_close) / prev_close * 100
                
                # Check if currently in pre/post/open
                now = datetime.now()
                # Determine "Gap"
                
                # Store
                results.append({
                    "Ticker": ticker,
                    "Price": last_close,
                    "Change %": change_pct,
                    "Volume": df['Volume'].sum(),
                    "Prev Close": prev_close,
                    "Time": df.index[-1].strftime("%H:%M:%S")
                })
                
            except Exception as e:
                print(f"Error {ticker}: {e}")
                
        if not results:
            return pd.DataFrame()
            
        return pd.DataFrame(results).sort_values("Change %", ascending=False)

def render_prepost_tracker(tickers: list):
    st.markdown("## 🌙 Pre/Post Market Tracker")
    st.caption("Monitor price action in extended trading hours.")
    
    if st.button("Refresh Data", key="refresh_prepost"):
        st.cache_data.clear()
        
    tracker = PrePostTracker(tickers)
    
    with st.spinner("Fetching pre/post market data..."):
        df = tracker.fetch_data()
        
    if df.empty:
        st.info("No data available. Market might be closed or pre-market hasn't started.")
        return
        
    # Top Movers
    st.subheader("Top Movers")
    
    # Styling
    st.dataframe(
        df,
        column_config={
            "Change %": st.column_config.NumberColumn(
                "Change %",
                format="%.2f%%",
                help="Percentage change from previous close",
            ),
            "Price": st.column_config.NumberColumn(format="$%.2f"),
        },
        use_container_width=True,
        hide_index=True
    )
    
    # Visual
    st.subheader("Relative Performance")
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df['Ticker'],
        y=df['Change %'],
        marker_color=np.where(df['Change %'] >= 0, 'green', 'red'),
    ))
    fig.update_layout(
        title="Extended Hours Performance",
        yaxis_title="Change %",
        template="plotly_dark",
        height=300
    )
    st.plotly_chart(fig, use_container_width=True)
