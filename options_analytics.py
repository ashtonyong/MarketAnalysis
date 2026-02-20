import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import streamlit as st
from datetime import datetime

class OptionsAnalytics:
    def __init__(self, ticker):
        self.ticker = ticker
        self.tk = yf.Ticker(ticker)
        
    def get_expirations(self):
        try:
            return self.tk.options
        except:
            return []
            
    def get_chain(self, expiration):
        try:
            opt = self.tk.option_chain(expiration)
            calls = opt.calls
            puts = opt.puts
            calls['Type'] = 'Call'
            puts['Type'] = 'Put'
            return calls, puts
        except Exception as e:
            print(f"Error fetching chain: {e}")
            return pd.DataFrame(), pd.DataFrame()
            
    def calculate_max_pain(self, calls, puts):
        # Max Pain: Strike price where option writers lose the least money
        # (Where total value of options expiring ITM is lowest)
        
        # Combine strikes
        strikes = sorted(list(set(calls['strike'].unique()) | set(puts['strike'].unique())))
        
        pain_values = []
        for s in strikes:
            # Value of Calls expiring ITM at strike s (Stock Price = s)
            # If Stock = s, Call Value = max(0, s - K) * OI
            # Wait, Max Pain is about settlement.
            # If Stock settles at S, 
            # Call(K) is worth max(0, S - K)
            # Put(K) is worth max(0, K - S)
            
            call_loss = calls.apply(lambda row: max(0, s - row['strike']) * row['openInterest'], axis=1).sum()
            put_loss = puts.apply(lambda row: max(0, row['strike'] - s) * row['openInterest'], axis=1).sum()
            
            pain_values.append(call_loss + put_loss)
            
        # Find strike with min pain
        if not pain_values: return 0
        min_pain_idx = np.argmin(pain_values)
        return strikes[min_pain_idx]

def render_options_analytics(ticker):
    st.markdown("## ️ Options Chain Analytics")
    st.caption("Open Interest distribution and 'Max Pain' levels.")
    
    oa = OptionsAnalytics(ticker)
    exps = oa.get_expirations()
    
    if not exps:
        st.info("No options data found.")
        return
        
    # Select Expiration
    selected_exp = st.selectbox("Select Expiration Date", exps)
    
    with st.spinner(f"Fetching chain for {selected_exp}..."):
        calls, puts = oa.get_chain(selected_exp)
        
    if calls.empty and puts.empty:
        st.error("Failed to fetch option chain.")
        return
        
    # --- Max Pain ---
    max_pain = oa.calculate_max_pain(calls, puts)
    
    # Current Price (Approx from chain or fetch?)
    # Call(0).lastPrice + Strike? No.
    # Just use last underlying price if available or infer.
    # Let's rely on ticker passed in st context usually having a price, but here we are isolated.
    # We can imply price from ITM/OTM border but let's just display Max Pain.
    
    # Put/Call Ratio
    total_call_oi = calls['openInterest'].sum()
    total_put_oi = puts['openInterest'].sum()
    pc_ratio = total_put_oi / total_call_oi if total_call_oi > 0 else 0
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Max Pain Strike", f"${max_pain}")
    c2.metric("Put/Call Ratio (OI)", f"{pc_ratio:.2f}")
    c3.metric("Total Open Interest", f"{int(total_call_oi + total_put_oi):,}")
    
    st.divider()
    
    # --- Visualization ---
    # Open Interest by Strike
    
    fig = go.Figure()
    
    # Filter for reasonable range near Max Pain to avoid cluttered chart?
    # Or just show all? SPY has many strikes.
    # Let's show all for now, plotly handles zoom.
    
    fig.add_trace(go.Bar(
        x=calls['strike'], y=calls['openInterest'],
        name='Call OI',
        marker_color='green',
        opacity=0.6
    ))
    
    fig.add_trace(go.Bar(
        x=puts['strike'], y=puts['openInterest'],
        name='Put OI',
        marker_color='red',
        opacity=0.6
    ))
    
    fig.add_vline(x=max_pain, line_=dict(color='yellow', dash='dash'), annotation_text="Max Pain")
    
    fig.update_layout(
        title=f"Open Interest Distribution ({selected_exp})",
        xaxis_title="Strike Price",
        yaxis_title="Open Interest",
        barmode='overlay', # Overlay or Stack? 
        # Usually stacked isn't right because K is x-axis. Group or Overlay.
        # Overlay lets us see both at same Strike.
        template="plotly_dark",
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Volume?
    if st.checkbox("Show Volume Distribution"):
        fig_vol = go.Figure()
        fig_vol.add_trace(go.Bar(x=calls['strike'], y=calls['volume'], name='Call Vol', marker_color='cyan'))
        fig_vol.add_trace(go.Bar(x=puts['strike'], y=puts['volume'], name='Put Vol', marker_color='magenta'))
        fig_vol.update_layout(title="Volume Distribution", template="plotly_dark", height=350, barmode='group')
        st.plotly_chart(fig_vol, use_container_width=True)
