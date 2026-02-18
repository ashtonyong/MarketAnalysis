import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import streamlit as st
from datetime import datetime, timedelta

class EconomicCalendar:
    def __init__(self):
        # Simulated "Major" events for demonstration since real-time API is paid
        # In a real app, fetch from an API like investing.com or FXStreet
        # Simulated "Major" events for 2025-2026 (User time is Feb 2026)
        self.events = [
            # FOMC (Approx every 6 weeks)
            {"date": "2025-01-29", "event": "FOMC Meeting", "impact": "High"},
            {"date": "2025-03-19", "event": "FOMC Meeting", "impact": "High"},
            {"date": "2025-04-30", "event": "FOMC Meeting", "impact": "High"},
            {"date": "2025-06-11", "event": "FOMC Meeting", "impact": "High"},
            {"date": "2025-07-30", "event": "FOMC Meeting", "impact": "High"},
            {"date": "2025-09-17", "event": "FOMC Meeting", "impact": "High"},
            {"date": "2025-10-29", "event": "FOMC Meeting", "impact": "High"},
            {"date": "2025-12-10", "event": "FOMC Meeting", "impact": "High"},
            {"date": "2026-01-28", "event": "FOMC Meeting", "impact": "High"},
            {"date": "2026-03-18", "event": "FOMC Meeting", "impact": "High"},
            
            # CPI (Mid-month)
            {"date": "2025-01-14", "event": "CPI Release", "impact": "High"},
            {"date": "2025-02-13", "event": "CPI Release", "impact": "High"},
            {"date": "2025-03-13", "event": "CPI Release", "impact": "High"},
            {"date": "2025-04-10", "event": "CPI Release", "impact": "High"},
            {"date": "2025-05-14", "event": "CPI Release", "impact": "High"},
            {"date": "2025-06-12", "event": "CPI Release", "impact": "High"},
            {"date": "2025-07-11", "event": "CPI Release", "impact": "High"},
            {"date": "2025-08-14", "event": "CPI Release", "impact": "High"},
            {"date": "2025-09-11", "event": "CPI Release", "impact": "High"},
            {"date": "2025-10-15", "event": "CPI Release", "impact": "High"},
            {"date": "2025-11-13", "event": "CPI Release", "impact": "High"},
            {"date": "2025-12-11", "event": "CPI Release", "impact": "High"},
            {"date": "2026-01-14", "event": "CPI Release", "impact": "High"},
            {"date": "2026-02-12", "event": "CPI Release", "impact": "High"},

            # NFP (First Friday)
            {"date": "2025-01-03", "event": "Non-Farm Payrolls", "impact": "High"},
            {"date": "2025-02-07", "event": "Non-Farm Payrolls", "impact": "High"},
            {"date": "2025-03-07", "event": "Non-Farm Payrolls", "impact": "High"},
            {"date": "2025-04-04", "event": "Non-Farm Payrolls", "impact": "High"},
            {"date": "2025-05-02", "event": "Non-Farm Payrolls", "impact": "High"},
            {"date": "2025-06-06", "event": "Non-Farm Payrolls", "impact": "High"},
            {"date": "2025-07-04", "event": "Non-Farm Payrolls", "impact": "High"},
            {"date": "2025-08-01", "event": "Non-Farm Payrolls", "impact": "High"},
            {"date": "2025-09-05", "event": "Non-Farm Payrolls", "impact": "High"},
            {"date": "2025-10-03", "event": "Non-Farm Payrolls", "impact": "High"},
            {"date": "2025-11-07", "event": "Non-Farm Payrolls", "impact": "High"},
            {"date": "2025-12-05", "event": "Non-Farm Payrolls", "impact": "High"},
            {"date": "2026-01-09", "event": "Non-Farm Payrolls", "impact": "High"},
            {"date": "2026-02-06", "event": "Non-Farm Payrolls", "impact": "High"},
        ]

    def get_events(self, start_date, end_date):
        # Filter events within range
        res = []
        for e in self.events:
            # Simple string comparison works for iso format
            if start_date <= e['date'] <= end_date:
                res.append(e)
        return res

@st.cache_data(ttl=600)
def fetch_price_history(ticker):
    try:
        # Fetch 1y data
        df = yf.download(ticker, period="1y", interval="1d", progress=False)
        return df
    except:
        return pd.DataFrame()

def render_econ_impact_overlay(ticker: str):
    st.markdown("## 📅 Economic Impact Overlay")
    st.caption(f"Visualizing price action around major economic events for **{ticker}**.")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        with st.spinner("Fetching price data..."):
            df = fetch_price_history(ticker)
        
        if df.empty:
            st.error("No price data found.")
            return
            
        # Initialize calendar
        calendar = EconomicCalendar()
        
        # Determine range of data
        start_dt = df.index[0].strftime('%Y-%m-%d')
        end_dt = df.index[-1].strftime('%Y-%m-%d')
        
        events = calendar.get_events(start_dt, end_dt)
        
        # Plot
        fig = go.Figure()
        
        # Candlestick
        fig.add_trace(go.Candlestick(
            x=df.index,
            open=df['Open'], high=df['High'],
            low=df['Low'], close=df['Close'],
            name='Price'
        ))
        
        # Add Events as Vertical Lines
        for e in events:
            date_str = e['date']
            # Find closest trading day?
            # Vertical line at date
            
            # Color coding
            color = "red" if "FOMC" in e['event'] else "orange" if "CPI" in e['event'] else "blue"
            
            # Use add_shape and add_annotation manually to avoid known Plotly add_vline TypeError with dates
            fig.add_shape(
                type="line",
                x0=date_str, x1=date_str,
                y0=0, y1=1,
                yref="paper",
                line=dict(color=color, width=1, dash="dash")
            )
            fig.add_annotation(
                x=date_str,
                y=1,
                yref="paper",
                text=e['event'],
                showarrow=False,
                font=dict(color=color, size=10),
                xanchor="left",
                yanchor="top"
            )
            
        fig.update_layout(
            title=f"{ticker} Price Action vs Macro Events",
            template="plotly_dark",
            xaxis_rangeslider_visible=False,
            height=500,
            hovermode="x unified"
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("### 📋 Event List")
        if not events:
            st.info("No major events in this period.")
        else:
            # Sort by date desc
            events_sorted = sorted(events, key=lambda x: x['date'], reverse=True)
            for e in events_sorted:
                color = "red" if "FOMC" in e['event'] else "orange" if "CPI" in e['event'] else "blue"
                st.markdown(f"""
                <div style='padding: 8px; border-left: 3px solid {color}; background: #161b22; margin-bottom: 8px; border-radius: 4px;'>
                    <div style='font-size: 11px; color: #8b949e;'>{e['date']}</div>
                    <div style='font-weight: 500; font-size: 13px;'>{e['event']}</div>
                    <div style='font-size: 10px; color: {color};'>{e['impact']} Impact</div>
                </div>
                """, unsafe_allow_html=True)
