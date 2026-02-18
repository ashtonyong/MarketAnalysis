import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from arch import arch_model

@st.cache_data(ttl=3600)
def fetch_vol_data(ticker, period="2y"):
    """Fetch daily data for volatility modeling."""
    try:
        df = yf.download(ticker, period=period, progress=False)
        if df.empty: return pd.DataFrame()
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df[['Close', 'Adj Close']]
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return pd.DataFrame()

def run_garch_model(df):
    """Fit GARCH(1,1) and forecast."""
    # Calculate log returns * 100 (for arch stability)
    returns = 100 * df['Close'].pct_change().dropna()
    
    # Fit GARCH(1,1)
    # vol='Garch', p=1, q=1
    am = arch_model(returns, vol='Garch', p=1, o=0, q=1, dist='Normal')
    res = am.fit(update_freq=0, disp='off')
    
    # Conditional Volatility (Historical)
    cond_vol = res.conditional_volatility
    
    # Forecast 5 days ahead
    forecasts = res.forecast(horizon=5, reindex=False)
    # Variance forecast
    var_forecast = forecasts.variance.iloc[-1]
    # Volatility forecast (sqrt)
    vol_forecast = np.sqrt(var_forecast)
    
    return returns, cond_vol, vol_forecast, res.summary().as_text()

def render_garch_forecaster(ticker):
    """Render the GARCH Volatility Forecaster tab."""
    st.markdown("### 🌋 GARCH Volatility Forecaster")
    st.caption("Forecast future volatility using Generalized Autoregressive Conditional Heteroskedasticity.")
    
    if st.button("Run GARCH Model", key="run_garch"):
        with st.spinner("Fitting GARCH(1,1) Model..."):
            df = fetch_vol_data(ticker)
            if not df.empty:
                try:
                    returns, cond_vol, vol_forecast, summary = run_garch_model(df)
                    
                    # Annualize Volatility
                    # Daily Vol * sqrt(252)
                    ann_vol_hist = cond_vol * np.sqrt(252)
                    
                    # Forecast
                    # vol_forecast is daily % sigma.
                    # Convert to annualized %
                    ann_forecast = vol_forecast * np.sqrt(252)
                    
                    # Metrics
                    curr_vol = ann_vol_hist.iloc[-1]
                    mean_vol = ann_vol_hist.mean()
                    
                    # 5-day forecast average
                    forecast_5d = ann_forecast.mean()
                    
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Current Ann. Vol", f"{curr_vol:.2f}%")
                    c2.metric("5-Day Forecast Vol", f"{forecast_5d:.2f}%", 
                              delta=f"{forecast_5d - curr_vol:.2f}%", delta_color="inverse")
                    c3.metric("Long-Run Mean Vol", f"{mean_vol:.2f}%")
                    
                    # Plots
                    fig = go.Figure()
                    
                    # Historical Volatility
                    fig.add_trace(go.Scatter(
                        x=ann_vol_hist.index, y=ann_vol_hist,
                        mode='lines', name='Historical Vol (GARCH)',
                        line=dict(color='orange', width=1.5)
                    ))
                    
                    # Forecast Points (Future)
                    # Create future dates
                    last_date = ann_vol_hist.index[-1]
                    future_dates = [last_date + pd.Timedelta(days=i) for i in range(1, 6)]
                    
                    fig.add_trace(go.Scatter(
                        x=future_dates, y=ann_forecast.values,
                        mode='lines+markers', name='Forecast Vol',
                        line=dict(color='cyan', width=2, dash='dot')
                    ))
                    
                    fig.update_layout(
                        title=f"{ticker} Conditional Volatility (Annualized)",
                        height=500, template="plotly_dark",
                        yaxis_title="Volatility %"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                    with st.expander("Model Summary"):
                        st.text(summary)
                        
                except Exception as e:
                    st.error(f"GARCH Model Failed: {e}")
                    st.info("Ensure you have 'arch' installed and sufficient data history.")
            else:
                st.error("No data found.")
