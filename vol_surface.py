import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime

@st.cache_data(ttl=3600)
def fetch_vol_surface_data(ticker):
    """Fetch options data for volatility surface."""
    try:
        t = yf.Ticker(ticker)
        expirations = t.options
        
        if not expirations: return pd.DataFrame()
        
        # Limit to next 6 expirations for speed
        expirations = expirations[:6]
        
        current_price = t.history(period='1d')['Close'].iloc[-1]
        
        data = []
        
        for exp in expirations:
            chain = t.option_chain(exp)
            calls = chain.calls
            puts = chain.puts
            
            # Combine or just use Calls/Puts? 
            # Ideally OTM Calls and OTM Puts for best IV surface.
            # Or just all strikes implies vol.
            
            # Let's filter near the money to avoid wild IVs deep OTM
            # Strikes +/- 30%
            radius = 0.30
            min_k = current_price * (1 - radius)
            max_k = current_price * (1 + radius)
            
            # Process Calls
            calls = calls[(calls['strike'] >= min_k) & (calls['strike'] <= max_k)]
            for _, row in calls.iterrows():
                try:
                    data.append({
                        "Expiration": exp,
                        "Strike": row['strike'],
                        "Type": "Call",
                        "IV": row['impliedVolatility'],
                        "Days": (datetime.strptime(exp, "%Y-%m-%d") - datetime.now()).days
                    })
                except: pass
                
            # Process Puts
            puts = puts[(puts['strike'] >= min_k) & (puts['strike'] <= max_k)]
            for _, row in puts.iterrows():
                try:
                    data.append({
                        "Expiration": exp,
                        "Strike": row['strike'],
                        "Type": "Put",
                        "IV": row['impliedVolatility'],
                        "Days": (datetime.strptime(exp, "%Y-%m-%d") - datetime.now()).days
                    })
                except: pass
                
        return pd.DataFrame(data)
        
    except Exception as e:
        st.error(f"Error fetching options: {e}")
        return pd.DataFrame()

def render_vol_surface(ticker):
    """Render the Volatility Surface Visualizer tab."""
    st.markdown("### 🏔️ Volatility Surface Visualizer")
    st.caption("3D view of Implied Volatility across Strikes and Expirations.")
    
    if st.button("Generate Surface", key="run_vol_surf"):
        with st.spinner("Fetching Options Data (this may take a moment)..."):
            df = fetch_vol_surface_data(ticker)
            
            if not df.empty:
                # Pivot for Grid
                # X: Days to Expiry, Y: Strike, Z: IV
                # Averaging IV of Calls and Puts for same Strike/Exp?
                # Usually we want OTM IVs. 
                # Let's simple average for visual.
                
                df_avg = df.groupby(['Days', 'Strike'])['IV'].mean().reset_index()
                
                # Create pivot table
                pivot_iv = df_avg.pivot(index='Strike', columns='Days', values='IV')
                
                # Fill missing? Interpolate?
                pivot_iv = pivot_iv.interpolate(method='linear', axis=0) # Interpolate along strikes
                
                # 3D Plot
                fig = go.Figure(data=[go.Surface(
                    z=pivot_iv.values,
                    x=pivot_iv.columns,
                    y=pivot_iv.index,
                    colorscale='Jet',
                    opacity=0.9
                )])
                
                fig.update_layout(
                    title=f"{ticker} Implied Volatility Surface",
                    scene=dict(
                        xaxis_title='Days into Future',
                        yaxis_title='Strike Price',
                        zaxis_title='Implied Volatility',
                    ),
                    width=800, height=600,
                    template="plotly_dark",
                    margin=dict(l=0, r=0, b=0, t=30)
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Skew Analysis
                st.markdown("#### Volatility Skew (Next Expiry)")
                # Get first expiry logic
                min_days = df['Days'].min()
                skew_df = df[df['Days'] == min_days].groupby('Strike')['IV'].mean()
                
                fig_skew = go.Figure(go.Scatter(
                    x=skew_df.index, y=skew_df.values, mode='lines+markers',
                    name='Smile/Skew'
                ))
                fig_skew.update_layout(title="Volatility Smile (Nearest Expiry)", height=300, 
                                       xaxis_title="Strike", yaxis_title="IV", template="plotly_dark")
                st.plotly_chart(fig_skew, use_container_width=True)
                
            else:
                st.error("No options data found or ticker does not have options.")
