import yfinance as yf
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from datetime import datetime, timedelta

class AnalystRatings:
    def __init__(self, ticker):
        self.ticker = ticker
        
    def fetch_upgrades_downgrades(self):
        try:
            t = yf.Ticker(self.ticker)
            # This returns a DataFrame with columns: GradeDate, Firm, ToGrade, FromGrade, Action
            ud = t.upgrades_downgrades
            
            if ud is None or ud.empty:
                return pd.DataFrame()
                
            # Filter for last 12 months
            one_year_ago = datetime.now() - timedelta(days=365)
            ud = ud[ud.index > one_year_ago]
            
            return ud.sort_index(ascending=False)
        except Exception as e:
            print(f"Error fetching upgrades: {e}")
            return pd.DataFrame()
            
    def get_summary_stats(self, df):
        if df.empty: return {}
        
        # Actions: 'up', 'down', 'main', 'init', 'reit'
        actions = df['Action'].value_counts()
        
        firms = df['Firm'].nunique()
        
        latest = df.iloc[0]
        
        return {
            "Total Actions (1Y)": len(df),
            "Upgrades": actions.get('up', 0),
            "Downgrades": actions.get('down', 0),
            "Initiations": actions.get('init', 0),
            "Firms Tracking": firms,
            "Latest Action": f"{latest['Firm']}: {latest['ToGrade']} ({latest['Action']})"
        }

def render_analyst_ratings(ticker: str):
    st.markdown("##  Analyst Upgrades & Downgrades")
    st.caption("Detailed history of analyst recommendations and rating changes over the last year.")
    
    ar = AnalystRatings(ticker)
    
    with st.spinner("Fetching analyst data..."):
        df = ar.fetch_upgrades_downgrades()
        
    if df.empty:
        st.info("No recent analyst activity found.")
        return
        
    stats = ar.get_summary_stats(df)
    
    # --- Metrics ---
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Analyst Firms", stats.get("Firms Tracking", 0))
    c2.metric("Upgrades (1Y)", stats.get("Upgrades", 0), delta=int(stats.get("Upgrades", 0)), delta_color="normal")
    c3.metric("Downgrades (1Y)", stats.get("Downgrades", 0), delta=-int(stats.get("Downgrades", 0)), delta_color="inverse")
    c4.metric("Total Actions", stats.get("Total Actions (1Y)", 0))
    
    st.divider()
    
    # --- Visual Timeline of Actions ---
    # We can plot price and marker the upgrades/downgrades
    # Fetch price history for context
    price_df = yf.Ticker(ticker).history(period="1y")
    
    fig = go.Figure()
    
    # Price Line
    fig.add_trace(go.Scatter(
        x=price_df.index, y=price_df['Close'],
        name='Price',
        line=dict(color='gray', width=1)
    ))
    
    # Overlay Upgrades/Downgrades
    # Match dates
    
    # Upgrades
    ups = df[df['Action'] == 'up']
    if not ups.empty:
        fig.add_trace(go.Scatter(
            x=ups.index, 
            y=[price_df.loc[d.date()]['Close'] if d.date() in price_df.index else price_df.iloc[-1]['Close'] for d in ups.index], # Approx price
            mode='markers',
            marker=dict(symbol='triangle-up', size=12, color='green'),
            name='Upgrade',
            text=ups['Firm'] + ": " + ups['ToGrade'],
            hovertemplate="%{text}<br>Date: %{x}<extra></extra>"
        ))
        
    # Downgrades
    downs = df[df['Action'] == 'down']
    if not downs.empty:
        fig.add_trace(go.Scatter(
            x=downs.index, 
            y=[price_df.loc[d.date()]['Close'] if d.date() in price_df.index else price_df.iloc[-1]['Close'] for d in downs.index],
            mode='markers',
            marker=dict(symbol='triangle-down', size=12, color='red'),
            name='Downgrade',
            text=downs['Firm'] + ": " + downs['ToGrade'],
            hovertemplate="%{text}<br>Date: %{x}<extra></extra>"
        ))
        
    fig.update_layout(
        title="Rating Changes vs Price",
        template="plotly_dark",
        height=400,
        xaxis_title="Date",
        yaxis_title="Price"
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # --- Data Table ---
    st.subheader("Detailed Logs")
    
    # Clean up DF for display
    display_df = df[['Firm', 'ToGrade', 'FromGrade', 'Action']].copy()
    st.dataframe(display_df, use_container_width=True)
