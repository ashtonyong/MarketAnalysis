import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots

@st.cache_data(ttl=3600)
def fetch_benchmark_data(ticker, benchmark, period="1y"):
    """Fetch daily close data for ticker and benchmark."""
    try:
        data = yf.download([ticker, benchmark], period=period, progress=False)['Close']
        # If multi-index (common in new yfinance), flatten
        # If only 2 columns, it might be flat already if different tickers
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
            
        returns = data.pct_change().dropna()
        return returns
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return pd.DataFrame()

def calculate_rolling_stats(returns, ticker, benchmark, window):
    """Calculate rolling beta and correlation."""
    if ticker not in returns.columns or benchmark not in returns.columns:
        return None, None
        
    asset_ret = returns[ticker]
    bench_ret = returns[benchmark]
    
    # Rolling Covariance and Variance
    rolling_cov = asset_ret.rolling(window=window).cov(bench_ret)
    rolling_var = bench_ret.rolling(window=window).var()
    
    rolling_beta = rolling_cov / rolling_var
    rolling_corr = asset_ret.rolling(window=window).corr(bench_ret)
    
    return rolling_beta, rolling_corr

def render_rolling_beta(ticker):
    """Render the Rolling Beta & Correlation tab."""
    st.markdown("### 📈 Rolling Beta & Correlation")
    st.caption("Analyze how the asset moves relative to a benchmark over time.")
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        st.markdown("**Settings**")
        benchmark = st.selectbox("Benchmark", ["SPY", "QQQ", "IWM", "DIA", "BTC-USD"], index=0)
        window = st.slider("Rolling Window (Days)", min_value=10, max_value=90, value=30, step=5)
        period = st.selectbox("Lookback Period", ["6mo", "1y", "2y", "5y"], index=1)
        
        if ticker == benchmark:
            st.warning("Ticker cannot be the same as benchmark.")
            return

    with col2:
        if st.button("Calculate", key="run_beta"):
            with st.spinner("Calculating Rolling Statistics..."):
                returns = fetch_benchmark_data(ticker, benchmark, period)
                
                if returns.empty or len(returns.columns) < 2:
                    st.error("Insufficient data fetched.")
                    return
                    
                beta, corr = calculate_rolling_stats(returns, ticker, benchmark, window)
                
                if beta is not None:
                    # Current Metrics
                    cur_beta = beta.iloc[-1]
                    cur_corr = corr.iloc[-1]
                    avg_beta = beta.mean()
                    
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Current Beta", f"{cur_beta:.2f}")
                    m2.metric("Current Correlation", f"{cur_corr:.2f}")
                    m3.metric(f"Avg Beta ({period})", f"{avg_beta:.2f}")
                    
                    # Dual Axis Chart
                    fig = make_subplots(specs=[[{"secondary_y": True}]])
                    
                    # Beta Line (Left Y)
                    fig.add_trace(go.Scatter(
                        x=beta.index, y=beta, name="Rolling Beta",
                        line=dict(color="#00BFFF", width=2)
                    ), secondary_y=False)
                    
                    # Correlation Line (Right Y)
                    fig.add_trace(go.Scatter(
                        x=corr.index, y=corr, name="Rolling Correlation",
                        line=dict(color="#FFD700", width=2, dash="dot")
                    ), secondary_y=True)
                    
                    # Reference Lines
                    fig.add_hline(y=1, line_dash="dash", line_color="gray", opacity=0.5, secondary_y=False)
                    fig.add_hline(y=1, line_dash="dash", line_color="gray", opacity=0.5, secondary_y=True)
                    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.3, secondary_y=True)
                    
                    fig.update_layout(
                        title=f"{ticker} vs {benchmark} (Rolling {window}-day)",
                        height=500,
                        template="plotly_dark",
                        xaxis_title="Date",
                        yaxis_title="Beta",
                        yaxis2_title="Correlation",
                        legend=dict(orientation="h", y=1.1)
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Interpretation
                    st.info(f"""
                    **Interpretation:**
                    - **Beta > 1.0**: {ticker} is more volatile than {benchmark}.
                    - **Beta < 1.0**: {ticker} is less volatile than {benchmark}.
                    - **Correlation > 0.8**: Moves effectively in lockstep.
                    - **Correlation < 0**: Moving inversely to the market.
                    """)
                else:
                    st.error("Could not calculate stats.")
