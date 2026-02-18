import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import streamlit as st
import time

@st.cache_data(ttl=300)
def fetch_range_data(ticker: str) -> dict:
    try:
        t = yf.Ticker(ticker)
        # Get 1 year history for SMAs and charts
        hist = t.history(period="2y") # Need > 1y for 200 SMA at start of 1y chart if possible, or just period='2y'
        
        if hist.empty:
            return {"error": "No price history found."}
        
        # Calculate SMAs
        hist['SMA_50'] = hist['Close'].rolling(window=50).mean()
        hist['SMA_200'] = hist['Close'].rolling(window=200).mean()
        
        current_close = hist['Close'].iloc[-1]
        current_price = current_close # FIX: Define current_price
        high_52 = hist['High'].tail(252).max()
        low_52 = hist['Low'].tail(252).min()
        
        # ATH (All time high) - approximates from max of fetched history (2y is too short for ATH)
        # We can try t.info['allTimeHigh']? usually not there. 'fiftyTwoWeekHigh' is there.
        # Let's rely on info for official 52w.
        info = t.info
        i_high_52 = info.get("fiftyTwoWeekHigh", high_52)
        i_low_52 = info.get("fiftyTwoWeekLow", low_52)
        
        # Current Metrics
        sma_50 = hist['SMA_50'].iloc[-1]
        sma_200 = hist['SMA_200'].iloc[-1]
        
        return {
            "history": hist,
            "current_price": current_price,
            "high_52": i_high_52,
            "low_52": i_low_52,
            "sma_50": sma_50,
            "sma_200": sma_200,
            "pct_from_high": (current_price - i_high_52) / i_high_52 * 100,
            "pct_from_low": (current_price - i_low_52) / i_low_52 * 100,
            "position": (current_price - i_low_52) / (i_high_52 - i_low_52) if (i_high_52 - i_low_52) > 0 else 0.5
        }
    except Exception as e:
        return {"error": str(e)}

def render_range_dashboard(ticker: str):
    st.markdown("## 📏 52-Week Range & Trend Dashboard")
    st.caption(f"Price position relative to yearly range and key moving averages for **{ticker}**.")

    with st.spinner("Analyzing trend data..."):
        data = fetch_range_data(ticker)
    
    if "error" in data:
        st.error(f"Error: {data['error']}")
        return

    curr = data['current_price']
    high = data['high_52']
    low = data['low_52']
    pos = data['position'] # 0 to 1
    
    # --- Metric Row ---
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("52-Week High", f"${high:,.2f}")
    m2.metric("52-Week Low", f"${low:,.2f}")
    m3.metric("% Below High", f"{data['pct_from_high']:.2f}%", delta_color="normal" if data['pct_from_high'] > -5 else "inverse") # Inverse? -20% is red? usually "Below High" is negative. Closer to 0 is good (Green).
    m4.metric("% Above Low", f"{data['pct_from_low']:.2f}%")

    st.markdown("### Range Position")
    # Custom Progress Bar
    # We want a bar with Low on left, High on right, and Arrow at Position.
    
    # Validating inputs
    if high <= low: high = low + 0.01

    range_pct = max(0.0, min(1.0, pos))
    
    bar_html = f"""
    <div style="position: relative; width: 100%; height: 30px; background-color: #30363d; border-radius: 5px; margin-bottom: 20px;">
        <div style="position: absolute; top: 0; left: 0; height: 100%; width: {range_pct*100}%; background: linear-gradient(90deg, #da3633, #e3b341, #238636); border-radius: 5px;"></div>
        <div style="position: absolute; top: -5px; left: {range_pct*100}%; transform: translateX(-50%);">
            <div style="width: 4px; height: 40px; background-color: white; border: 1px solid black;"></div>
            <div style="font-size: 12px; color: white; background: #000; padding: 2px 4px; border-radius: 3px; margin-top: 5px; white-space: nowrap;">
                ${curr:.2f}
            </div>
        </div>
    </div>
    <div style="display: flex; justify-content: space-between; font-size: 12px; color: #8b949e;">
        <span>Low: ${low:.2f}</span>
        <span>High: ${high:.2f}</span>
    </div>
    """
    st.markdown(bar_html, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # --- Moving Averages & Chart ---
    hist = data['history']
    
    # Last Values
    sma50 = data['sma_50']
    sma200 = data['sma_200']
    
    # Crossover Logic
    # Check proper cross in last few days or current state
    trend = "Neutral"
    if sma50 > sma200:
        trend = "Bullish (Golden Cross Region)"
        t_color = "green"
    else:
        trend = "Bearish (Death Cross Region)"
        t_color = "red"
        
    k1, k2, k3 = st.columns(3)
    k1.metric("SMA 50", f"${sma50:.2f}" if not pd.isna(sma50) else "N/A")
    k2.metric("SMA 200", f"${sma200:.2f}" if not pd.isna(sma200) else "N/A")
    k3.markdown(f"**Trend State**: :{t_color}[{trend}]")
    
    # Chart
    st.subheader("Price vs SMAs (1 Year)")
    
    # Filter last 252 days for display
    display_hist = hist.tail(252).copy()
    
    fig = go.Figure()
    
    # Candlestick
    fig.add_trace(go.Candlestick(
        x=display_hist.index,
        open=display_hist['Open'], high=display_hist['High'],
        low=display_hist['Low'], close=display_hist['Close'],
        name='Price'
    ))
    
    # SMA 50
    if not display_hist['SMA_50'].isna().all():
        fig.add_trace(go.Scatter(
            x=display_hist.index, y=display_hist['SMA_50'],
            mode='lines', name='SMA 50',
            line=dict(color='orange', width=1.5)
        ))

    # SMA 200
    if not display_hist['SMA_200'].isna().all():
        fig.add_trace(go.Scatter(
            x=display_hist.index, y=display_hist['SMA_200'],
            mode='lines', name='SMA 200',
            line=dict(color='white', width=1.5, dash='dash')
        ))
        
    fig.update_layout(
        template="plotly_dark",
        xaxis_rangeslider_visible=False,
        height=500,
        title=f"{ticker} Daily Chart",
        hovermode="x unified"
    )
    st.plotly_chart(fig, use_container_width=True)
