import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import streamlit as st
from datetime import datetime, timedelta
import pytz

# Session Times (UTC)
SESSIONS = {
    "Asian": {"start": "00:00", "end": "08:00", "color": "#FFD700"},  # Gold
    "London": {"start": "07:00", "end": "16:00", "color": "#00BFFF"},  # Deep Sky Blue
    "New York": {"start": "13:00", "end": "22:00", "color": "#FF4500"}  # Orange Red
}

@st.cache_data(ttl=300)
def fetch_intraday_data(ticker):
    """Fetch 5-day intraday data for session analysis."""
    try:
        # 5m interval, 5d period
        df = yf.download(ticker, period="5d", interval="5m", progress=False)
        if df.empty:
            return pd.DataFrame()
        
        # Flatten columns if MultiIndex
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        # Ensure UTC
        if df.index.tz is None:
            df.index = df.index.tz_localize('UTC')
        else:
            df.index = df.index.tz_convert('UTC')
            
        return df
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return pd.DataFrame()

def get_session_ranges(df, session_name):
    """Calculate session high/lows for a specific session."""
    ranges = []
    
    start_time = datetime.strptime(SESSIONS[session_name]["start"], "%H:%M").time()
    end_time = datetime.strptime(SESSIONS[session_name]["end"], "%H:%M").time()
    
    # Group by date
    dates = df.index.normalize().unique()
    
    for date in dates:
        # Create start/end timestamps for this date
        # careful with crossing midnight (Asian session starts 00:00 so ok)
        
        s_ts = pd.Timestamp.combine(date, start_time).tz_localize('UTC')
        e_ts = pd.Timestamp.combine(date, end_time).tz_localize('UTC')
        
        # Filter data
        mask = (df.index >= s_ts) & (df.index < e_ts)
        session_data = df[mask]
        
        if not session_data.empty:
            high = session_data['High'].max()
            low = session_data['Low'].min()
            ranges.append({
                "start": s_ts,
                "end": e_ts,
                "high": high,
                "low": low
            })
            
    return ranges

def render_session_range(ticker):
    """Render the Session Range Tracker tab."""
    st.markdown("###  Session Range Tracker")
    st.caption("Visualizes Asian, London, and New York sessions to identify liquidity pools.")
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        st.markdown("**Session Toggles**")
        show_asian = st.checkbox("Asian Session (00-08 UTC)", value=True)
        show_london = st.checkbox("London Session (07-16 UTC)", value=True)
        show_ny = st.checkbox("New York Session (13-22 UTC)", value=True)
        
        st.info("""
        **Color Key:**
        -  Asian: 00:00 - 08:00 UTC
        -  London: 07:00 - 16:00 UTC
        -  New York: 13:00 - 22:00 UTC
        """)

    with col2:
        df = fetch_intraday_data(ticker)
        
        if df.empty:
            st.warning(f"No intraday data available for {ticker}. Try a crypto pair or major forex pair for best session overlap visibility.")
            return

        # Base Chart
        fig = go.Figure(data=[go.Candlestick(
            x=df.index,
            open=df['Open'], high=df['High'],
            low=df['Low'], close=df['Close'],
            name=ticker
        )])

        # Overlay Sessions
        if show_asian:
            asian_ranges = get_session_ranges(df, "Asian")
            for r in asian_ranges:
                # Draw Rectangle
                fig.add_shape(type="rect",
                    x0=r['start'], y0=r['low'], x1=r['end'], y1=r['high'],
                    line=dict(color=SESSIONS["Asian"]["color"], width=1),
                    fillcolor=SESSIONS["Asian"]["color"], opacity=0.1,
                    layer="below"
                )
                # Add High/Low lines only if desired, or simplified to just box. 
                # Box indicates range nicely.

        if show_london:
            lon_ranges = get_session_ranges(df, "London")
            for r in lon_ranges:
                fig.add_shape(type="rect",
                    x0=r['start'], y0=r['low'], x1=r['end'], y1=r['high'],
                    line=dict(color=SESSIONS["London"]["color"], width=1),
                    fillcolor=SESSIONS["London"]["color"], opacity=0.1,
                     layer="below"
                )

        if show_ny:
            ny_ranges = get_session_ranges(df, "New York")
            for r in ny_ranges:
                 fig.add_shape(type="rect",
                    x0=r['start'], y0=r['low'], x1=r['end'], y1=r['high'],
                    line=dict(color=SESSIONS["New York"]["color"], width=1),
                    fillcolor=SESSIONS["New York"]["color"], opacity=0.1,
                     layer="below"
                )

        fig.update_layout(
            title=f"{ticker} - Session Ranges (UTC)",
            height=600,
            xaxis_rangeslider_visible=False,
            template="plotly_dark",
            paper_bgcolor="#0e1117",
            plot_bgcolor="#0e1117",
            font=dict(color="#ffffff")
        )
        
        st.plotly_chart(fig, use_container_width=True)
