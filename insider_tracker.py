import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.express as px

@st.cache_data(ttl=3600)
def fetch_insider_data(ticker):
    """Fetch insider trading data."""
    try:
        t = yf.Ticker(ticker)
        # Transactions
        trans = t.insider_transactions
        # Roster (Major Holders)
        roster = t.insider_roster_holders
        
        return trans, roster
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return None, None

def render_insider_tracker(ticker):
    """Render the Insider Trading Tracker tab."""
    st.markdown("### 👔 Insider Trading Tracker")
    st.caption("Monitor buying and selling activity by company executives and directors.")
    
    if st.button("Fetch Insider Data", key="run_insider"):
        with st.spinner("Fetching Insider Transactions..."):
            trans, roster = fetch_insider_data(ticker)
            
            if trans is not None and not trans.empty:
                # Process Transactions
                # yfinance returns columns like: Name, Position, Date, Text, Shares, Value, Start Date, Ownership
                # Text usually contains "Sale at price..." or "Purchase at price..."
                
                # Check columns
                # 'Shares' might be total held or traded? 
                # Usually 'Value' is None or formatted string.
                # Let's clean it up.
                
                df = trans.copy()
                
                # Filter recent (last 6 months) if Date column exists
                if 'Start Date' in df.columns:
                    df['Date'] = pd.to_datetime(df['Start Date'])
                    recent_mask = df['Date'] > pd.Timestamp.now() - pd.Timedelta(days=180)
                    df = df[recent_mask]
                
                if df.empty:
                    st.info("No recent insider transactions found (last 6 months).")
                else:
                    # Determine Buy/Sell
                    # Often implicitly in 'Text' column or just 'Shares' sign?
                    # yfinance output for insider_transactions is a bit unstructured.
                    # Usually "Sale" or "Purchase" is in the text description row if available.
                    # Or 'Text' column.
                    
                    # Heuristic:
                    # If 'Text' contains "Sale", it's a Sell.
                    # If "Purchase" or "Buy", it's a Buy.
                    
                    def classify_trans(row):
                        text = str(row.get('Text', '')).lower()
                        if 'sale' in text or 'sell' in text: return 'Sell'
                        if 'purchase' in text or 'buy' in text: return 'Buy'
                        return 'Other'
                        
                    df['Type'] = df.apply(classify_trans, axis=1)
                    
                    # Metrics
                    buys = df[df['Type'] == 'Buy']
                    sells = df[df['Type'] == 'Sell']
                    
                    buy_vol = buys['Shares'].sum() if not buys.empty else 0
                    sell_vol = sells['Shares'].sum() if not sells.empty else 0
                    
                    # Calculate Net Sentiment
                    net_trans = len(buys) - len(sells)
                    sentiment = "Neutral"
                    color = "gray"
                    if net_trans > 0: 
                        sentiment = "Positive (Net Buying)"
                        color = "green"
                    elif net_trans < 0:
                        sentiment = "Negative (Net Selling)"
                        color = "red"
                        
                    # Display Metrics
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Insider Sentiment", sentiment) # No color arg for metric value, handle via markdown?
                    st.markdown(f"**Verdict:** :{color}[{sentiment}]")

                    c2.metric("Total Buys (Shares)", f"{int(buy_vol):,}")
                    c3.metric("Total Sells (Shares)", f"{int(sell_vol):,}")
                    
                    # Chart
                    # Bar chart of Buys vs Sells over time
                    fig = px.bar(
                        df, x='Date', y='Shares', color='Type',
                        color_discrete_map={'Buy': 'green', 'Sell': 'red', 'Other': 'gray'},
                        title="Insider Transaction Volume",
                        template="plotly_dark"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Table
                    st.dataframe(
                        df[['Date', 'Name', 'Position', 'Type', 'Shares', 'Text']],
                        use_container_width=True,
                        hide_index=True
                    )
                    
            else:
                st.warning("No insider transaction data available.")
                
            if roster is not None and not roster.empty:
                with st.expander("Major Holders (Roster)"):
                    st.dataframe(roster, use_container_width=True)
