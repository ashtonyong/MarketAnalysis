import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go

@st.cache_data(ttl=300)
def fetch_fvg_data(ticker, interval="1h", period="60d"):
    """Fetch OHLC data for FVG scanning."""
    try:
        df = yf.download(ticker, period=period, interval=interval, progress=False)
        if df.empty: return pd.DataFrame()
        # Flatten columns if MultiIndex
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return pd.DataFrame()

def scan_fvgs(df):
    """Scan for Bullish and Bearish Fair Value Gaps."""
    fvgs = []
    
    # Need at least 3 candles
    if len(df) < 3: return []
    
    # Loop from index 1 to len-2 (need i-1 and i+1)
    # Actually, FVG is formed by candle i-1, i, i+1.
    # Pattern:
    # Bullish: Low(i+1) > High(i-1)  (Gap is between High[i-1] and Low[i+1])
    # Bearish: High(i+1) < Low(i-1) (Gap is between Low[i-1] and High[i+1])
    
    for i in range(1, len(df) - 1):
        # Bullish FVG
        # Gap between Candle i-1 High and Candle i+1 Low
        high_prev = df['High'].iloc[i-1]
        low_next = df['Low'].iloc[i+1]
        
        if low_next > high_prev:
            # Found Bullish FVG
            top = low_next
            bottom = high_prev
            
            # Check if filled
            # Check all candles AFTER i+1
            filled = False
            for j in range(i+2, len(df)):
                # If any candle Low goes below Top? 
                # Strictly, filled means price traded through it.
                # Partial fill is common. Complete fill means Price < Bottom (for Bullish).
                # Let's say "Mitigated" if price touches it. "Filled" if crossed?
                # Prompt: "filled" if any subsequent candle's range OVERLAPS the gap zone.
                # Overlap means Low[j] < Top.
                c_low = df['Low'].iloc[j]
                c_high = df['High'].iloc[j]
                
                # Check overlap
                if c_low < top:
                    filled = True
                    break
            
            fvgs.append({
                "type": "Bullish",
                "top": top,
                "bottom": bottom,
                "start_idx": df.index[i], # Visual anchor
                "end_idx": df.index[-1], # Extend to valid end
                "filled": filled,
                "created_at": df.index[i]
            })
            
        # Bearish FVG
        # Gap between Candle i-1 Low and Candle i+1 High
        low_prev = df['Low'].iloc[i-1]
        high_next = df['High'].iloc[i+1]
        
        if high_next < low_prev:
            # Found Bearish FVG
            top = low_prev
            bottom = high_next
            
            # Check if filled (Price > Bottom)
            filled = False
            for j in range(i+2, len(df)):
                c_high = df['High'].iloc[j]
                if c_high > bottom:
                    filled = True
                    break
            
            fvgs.append({
                "type": "Bearish",
                "top": top,
                "bottom": bottom,
                "start_idx": df.index[i],
                "end_idx": df.index[-1],
                "filled": filled,
                "created_at": df.index[i]
            })
            
    return fvgs

def render_fvg_scanner(ticker):
    """Render the FVG Scanner tab."""
    st.markdown("###  Fair Value Gap (FVG) Scanner")
    st.caption("Identify unfilled price imbalances (magnets for price action).")
    
    col1, col2 = st.columns([1, 4])
    
    with col1:
        st.markdown("**Settings**")
        interval = st.selectbox("Timeframe", ["1h", "4h", "1d"], index=0)
        show_filled = st.checkbox("Show Filled FVGs", value=False)
        
        period_map = {"1h": "60d", "4h": "1y", "1d": "2y"}
        period = period_map.get(interval, "60d")

    with col2:
        df = fetch_fvg_data(ticker, interval, period)
        if df.empty:
            st.warning("No data found.")
            return

        fvgs = scan_fvgs(df)
        
        # Filter
        active_fvgs = [f for f in fvgs if not f['filled']]
        display_fvgs = fvgs if show_filled else active_fvgs
        
        # Chart
        fig = go.Figure(data=[go.Candlestick(
            x=df.index,
            open=df['Open'], high=df['High'],
            low=df['Low'], close=df['Close'],
            name=ticker
        )])
        
        # Draw FVGs
        for f in display_fvgs:
            color = "rgba(0, 255, 0, 0.15)" if f['type'] == "Bullish" else "rgba(255, 0, 0, 0.15)"
            line_color = "green" if f['type'] == "Bullish" else "red"
            
            # Add Rectangle
            # We can use add_shape (layout) or add_trace(scatter)
            # Shapes are easiest for boxes
            # x0 is creation time, x1 is current time (end of chart)
            
            fig.add_shape(type="rect",
                x0=f['created_at'], y0=f['bottom'],
                x1=df.index[-1], y1=f['top'], # Extend to right edge
                line=dict(color=line_color, width=0),
                fillcolor=color, opacity=0.5,
                layer="below"
            )
            
        fig.update_layout(
            title=f"{ticker} - Fair Value Gaps ({interval})",
            height=600,
            xaxis_rangeslider_visible=False,
            template="plotly_dark"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Table
        if active_fvgs:
            st.markdown("#### Active Unfilled FVGs")
            
            # Current Price
            curr = df['Close'].iloc[-1]
            
            table_data = []
            for f in active_fvgs:
                # Dist %
                mid = (f['top'] + f['bottom']) / 2
                dist_pct = (curr - mid) / mid * 100
                
                table_data.append({
                    "Date": f['created_at'].strftime('%Y-%m-%d %H:%M'),
                    "Type": f['type'],
                    "Top": f"${f['top']:.2f}",
                    "Bottom": f"${f['bottom']:.2f}",
                    "Distance %": f"{dist_pct:+.2f}%"
                })
                
            st.dataframe(pd.DataFrame(table_data), use_container_width=True, hide_index=True)
        else:
            st.info("No active unfilled FVGs detected.")
