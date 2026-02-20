import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from datetime import timedelta

@st.cache_data(ttl=3600)
def fetch_earnings_history(ticker):
    """Fetch earnings dates and calculate historical moves."""
    try:
        t = yf.Ticker(ticker)
        # Get earnings dates
        earn_dates = t.earnings_dates
        if earn_dates is None or earn_dates.empty:
            return None, "No earnings dates found."
            
        # Sort by date descending
        earn_dates = earn_dates.sort_index(ascending=False)
        
        # We need historical price data for these dates
        # Let's fetch 2 years of daily data to cover recent earnings
        start_date = earn_dates.index.min() - timedelta(days=10)
        end_date = pd.Timestamp.now() + timedelta(days=5)
        
        hist = t.history(start=start_date, end=end_date)
        
        moves = []
        
        # Iterate through earnings dates
        for date, row in earn_dates.iterrows():
            try:
                # Find comparable dates (Before/After)
                # Earnings date in yfinance is usually the report date
                # We need Close of Day Before and Open of Day After (or Close of Report Day if AMC vs BMO?)
                # Simplified: Close of T-1 vs Open of T+1?
                # Actually simpler: Close of Day Before vs Open of Day of Reaction.
                # If BMO: Reaction is same day. Prev Close is T-1.
                # If AMC: Reaction is next day. Prev Close is T.
                # yfinance doesn't easily give BMO/AMC in this view, assuming standard reaction
                # Let's use: Close of (Date-1) vs Open of (Date) or Open of (Date+1)?
                # Standard practice: Look at the biggest gap around that date.
                
                # Let's try: Close(Date-1 business day) vs Open(Date or Date+1)
                # We will check the price move on the Date and Date+1
                
                # Safe approach: Close of T-1 vs Close of T (Reaction Move)
                # Or Close of T-1 vs Open of T (Gap)
                
                # Let's use Close of T-1 vs Close of T for full day reaction
                idx_loc = hist.index.get_indexer([date], method='nearest')[0]
                
                if idx_loc > 0 and idx_loc < len(hist)-1:
                    prev_close = hist['Close'].iloc[idx_loc-1]
                    # reaction_price = hist['Open'].iloc[idx_loc] # Gap
                    reaction_close = hist['Close'].iloc[idx_loc] # Full day
                    
                    # Logarithmic return or percentage
                    move_pct = abs((reaction_close - prev_close) / prev_close) * 100
                    
                    moves.append({
                        "Date": date,
                        "Move %": move_pct,
                        "EPS Est": row.get('EPS Estimate'),
                        "Reported EPS": row.get('Reported EPS')
                    })
            except Exception:
                continue
                
        if not moves:
            return None, "Could not calculate historical moves."
            
        return pd.DataFrame(moves), None
        
    except Exception as e:
        return None, str(e)

def get_implied_move(ticker):
    """Calculate implied move from nearest expiration straddle."""
    try:
        t = yf.Ticker(ticker)
        options = t.options
        if not options:
            return None, "No options chain."
            
        # Get nearest expiry
        expiry = options[0]
        chain = t.option_chain(expiry)
        
        current_price = t.history(period="1d")['Close'].iloc[-1]
        
        # Find ATM Strike
        calls = chain.calls
        puts = chain.puts
        
        # Find strike closest to current price
        atm_strike = calls.iloc[(calls['strike'] - current_price).abs().argsort()[:1]]['strike'].values[0]
        
        # Get Prices
        atm_call = calls[calls['strike'] == atm_strike]['lastPrice'].values[0]
        atm_put = puts[puts['strike'] == atm_strike]['lastPrice'].values[0]
        
        straddle_cost = atm_call + atm_put
        implied_move_pct = (straddle_cost / current_price) * 100
        
        return implied_move_pct, f"Based on {expiry} expiry, Strike {atm_strike}"
        
    except Exception as e:
        return None, str(e)

def render_earnings_volatility(ticker):
    """Render the Earnings Volatility Predictor tab."""
    st.markdown("###  Earnings Volatility Predictor")
    st.caption("Compare historical post-earnings moves vs current options-implied expected move.")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        if st.button("Analyze Earnings Volatility", key="run_earn_vol"):
            with st.spinner("Analyzing..."):
                df_moves, err = fetch_earnings_history(ticker)
                
                if df_moves is not None:
                    # Stats
                    avg_move = df_moves['Move %'].mean()
                    med_move = df_moves['Move %'].median()
                    max_move = df_moves['Move %'].max()
                    
                    # Implied Move
                    imp_move, imp_note = get_implied_move(ticker)
                    
                    # Verdict
                    verdict = "N/A"
                    color = "gray"
                    if imp_move:
                        if imp_move > avg_move * 1.2:
                            verdict = "Options EXPENSIVE"
                            color = "red"
                        elif imp_move < avg_move * 0.8:
                            verdict = "Options CHEAP"
                            color = "green"
                        else:
                            verdict = "FAIR VALUE"
                            color = "orange"
                    
                    # Metrics
                    st.metric("Verict", verdict)
                    if imp_move:
                        st.metric("Implied Move", f"{imp_move:.2f}%", help=imp_note)
                    st.metric("Avg Hist Move", f"{avg_move:.2f}%")
                    st.metric("Median Hist Move", f"{med_move:.2f}%")
                    
                    st.markdown("---")
                    st.caption(f"Based on last {len(df_moves)} earnings events.")
                    
                else:
                    st.error(err)
                    return

    with col2:
        if 'df_moves' in locals() and df_moves is not None:
            # Chart
            fig = go.Figure()
            
            # Historical Bars
            fig.add_trace(go.Bar(
                x=df_moves['Date'], y=df_moves['Move %'],
                name="Historical Move", marker_color="#3b82f6"
            ))
            
            # Averages lines
            fig.add_hline(y=avg_move, line_dash="dash", line_color="orange", annotation_text="Avg")
            
            if imp_move:
                fig.add_hline(y=imp_move, line_dash="solid", line_color="red", line_width=2, annotation_text="Implied")
            
            fig.update_layout(
                title=f"{ticker} Historical Post-Earnings Moves",
                height=500,
                template="plotly_dark",
                yaxis_title="Move %",
                xaxis_title="Earnings Date"
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Table
            st.dataframe(df_moves.sort_values("Date", ascending=False), use_container_width=True, hide_index=True)
