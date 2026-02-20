import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import streamlit as st
from datetime import timedelta

# Try to import arch, else fallback
try:
    from arch import arch_model
    HAS_ARCH = True
except ImportError:
    HAS_ARCH = False

class GarchForecaster:
    def __init__(self, ticker):
        self.ticker = ticker
        
    def fetch_returns(self):
        try:
            df = yf.download(self.ticker, period="2y", progress=False)
            if df.empty: return pd.Series()
            
            # Log returns are better for GARCH
            closes = df['Close']
            returns = 100 * np.log(closes / closes.shift(1)).dropna()
            return returns
        except:
            return pd.Series()
            
    def forecast_vol(self):
        returns = self.fetch_returns()
        if returns.empty: return None
        
        # 1. GARCH(1,1)
        if HAS_ARCH:
            try:
                model = arch_model(returns, vol='Garch', p=1, q=1)
                res = model.fit(disp='off')
                forecast = res.forecast(horizon=5)
                # Annualized Vol Forecast
                vol_forecast_annual = np.sqrt(forecast.variance.iloc[-1]) * np.sqrt(252)
                
                # Historic Vol (for plotting)
                conditional_vol = res.conditional_volatility * np.sqrt(252)
                
                return {
                    "method": "GARCH(1,1)",
                    "current_vol": vol_forecast_annual.iloc[0],
                    "conditional_vol": conditional_vol,
                    "returns": returns,
                    "model_summary": res.summary()
                }
            except Exception as e:
                # Fallback if fit fails
                print(f"GARCH fit failed: {e}")
                pass
                
        # 2. Fallback: EWMA
        # Lambda = 0.94 (RiskMetrics standard)
        decay = 0.94
        squared_returns = returns ** 2
        ewma_var = squared_returns.ewm(alpha=1-decay).mean()
        ewma_vol = np.sqrt(ewma_var) * np.sqrt(252)
        
        return {
            "method": "EWMA (RiskMetrics)",
            "current_vol": ewma_vol.iloc[-1],
            "conditional_vol": ewma_vol,
            "returns": returns,
            "model_summary": "EWMA Fallback (No ARCH package or fit failed)"
        }

def render_garch_forecaster(ticker):
    st.markdown("##  Volatility Forecaster (GARCH)")
    st.caption("Forecasts future volatility using GARCH(1,1) or EWMA. Used to estimate risk and option pricing.")
    
    forecaster = GarchForecaster(ticker)
    
    with st.spinner("Forecasting volatility..."):
        res = forecaster.forecast_vol()
        
    if not res:
        st.error("Could not forecast volatility.")
        return
        
    curr_vol = res['current_vol']
    method = res['method']
    
    # --- Metrics ---
    c1, c2, c3 = st.columns(3)
    c1.metric("Forecasted Vol (Annual)", f"{curr_vol:.2f}%")
    c2.metric("Method", method)
    
    # Implied Move (1 Day)
    # Vol / 16 (Rule of 16) approx or Vol / sqrt(252)
    daily_vol = curr_vol / np.sqrt(252)
    # Assuming price from last return calc? We don't have price here easily unless we fetch again or pass it.
    # Just show % move
    c3.metric("Implied Daily Move", f"±{daily_vol:.2f}%")
    
    st.divider()
    
    if method == "GARCH(1,1)":
        with st.expander("Model Summary"):
            st.text(res['model_summary'])
    
    # --- Visualization ---
    # Plot Conditional Volatility over time
    cond_vol = res['conditional_vol']
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=cond_vol.index, 
        y=cond_vol, 
        name="Conditional Volatility",
        line=dict(color='orange')
    ))
    
    # Add simple realized vol for comparison? 
    # Rolling 20d std dev
    realized = res['returns'].rolling(window=20).std() * np.sqrt(252)
    fig.add_trace(go.Scatter(
        x=realized.index,
        y=realized,
        name="Realized Vol (20d)",
        line=dict(color='gray', width=1, dash='dot')
    ))
    
    fig.update_layout(
        title="Historical Volatility Regimes",
        yaxis_title="Annualized Volatility (%)",
        template="plotly_dark",
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
