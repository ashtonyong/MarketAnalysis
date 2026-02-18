import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px

@st.cache_data(ttl=3600)
def fetch_portfolio_data(tickers, period="1y"):
    """Fetch close prices for portfolio assets."""
    try:
        if not tickers: return pd.DataFrame()
        df = yf.download(tickers, period=period, progress=False)['Close']
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return pd.DataFrame()

def calculate_portfolio_metrics(df, weights):
    """Calculate Return, Volatility, Sharpe, and VaR."""
    returns = df.pct_change().dropna()
    
    # Portfolio Return (Daily)
    port_ret = returns.dot(weights)
    
    # Annualized Stats
    # Assuming 252 trading days
    exp_return = port_ret.mean() * 252
    volatility = port_ret.std() * np.sqrt(252)
    sharpe = exp_return / volatility if volatility > 0 else 0
    
    # Value at Risk (95% Confidence)
    # 5th percentile of daily returns * sqrt(days)? No, historical VaR is just percentile.
    # Parametric VaR: Mean - 1.65 * StdDev
    var_95 = np.percentile(port_ret, 5) # Historical
    
    return {
        "Expected Return": exp_return,
        "Volatility": volatility,
        "Sharpe Ratio": sharpe,
        "Daily VaR (95%)": var_95,
        "Correlation Matrix": returns.corr()
    }

def perform_efficient_frontier(df, num_portfolios=1000):
    """Simulate random portfolios for Efficient Frontier."""
    returns = df.pct_change().dropna()
    mean_daily_ret = returns.mean()
    cov_matrix = returns.cov()
    
    results = np.zeros((3, num_portfolios))
    num_assets = len(df.columns)
    
    for i in range(num_portfolios):
        weights = np.random.random(num_assets)
        weights /= np.sum(weights)
        
        p_ret = np.sum(weights * mean_daily_ret) * 252
        p_vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights))) * np.sqrt(252)
        
        results[0,i] = p_vol
        results[1,i] = p_ret
        results[2,i] = p_ret / p_vol # Sharpe
        
    return results

def render_portfolio_risk(ticker):
    """Render the Portfolio Risk Dashboard tab."""
    st.markdown("### 🛡️ Portfolio Risk Dashboard")
    st.caption("Analyze Volatility, Correlation, and Value at Risk (VaR).")
    
    col_input, col_res = st.columns([1, 2])
    
    with col_input:
        st.markdown("**Portfolio Composition**")
        # Default include the current ticker
        default_tickers = "SPY, TLT, GLD, BTC-USD"
        if ticker not in default_tickers:
            default_tickers = f"{ticker}, {default_tickers}"
            
        tickers_input = st.text_area("Assets (comma separated)", value=default_tickers, height=100)
        
        if st.button("Analyze Risk", key="run_risk"):
            st.session_state['risk_run'] = True
            st.session_state['risk_tickers'] = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]

    with col_res:
        if st.session_state.get('risk_run'):
            tickers = st.session_state['risk_tickers']
            if len(tickers) < 2:
                st.warning("Please enter at least 2 assets.")
                return
                
            df = fetch_portfolio_data(tickers)
            
            if not df.empty:
                # Weights: Equal Weight for simplicity in this demo
                weights = np.array([1/len(tickers)] * len(tickers))
                
                metrics = calculate_portfolio_metrics(df, weights)
                
                # Top Metrics
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Ann. Return", f"{metrics['Expected Return']:.1%}")
                m2.metric("Ann. Volatility", f"{metrics['Volatility']:.1%}")
                m3.metric("Sharpe Ratio", f"{metrics['Sharpe Ratio']:.2f}")
                m4.metric("Daily VaR (95%)", f"{metrics['Daily VaR (95%)']:.2%}", help="Max expected loss on 95% of days")
                
                # Correlation Heatmap
                st.markdown("#### Correlation Matrix")
                corr = metrics['Correlation Matrix']
                fig_corr = px.imshow(corr, text_auto=True, color_continuous_scale='RdBu_r', zmin=-1, zmax=1)
                fig_corr.update_layout(height=400, template='plotly_dark', title="Asset Correlations")
                st.plotly_chart(fig_corr, use_container_width=True)
                
                # Efficient Frontier
                st.markdown("#### Efficient Frontier Simulation")
                st.caption("1000 Random Portfolios (Monte Carlo)")
                sim_res = perform_efficient_frontier(df)
                
                fig_ef = go.Figure(data=go.Scatter(
                    x=sim_res[0,:],
                    y=sim_res[1,:],
                    mode='markers',
                    marker=dict(
                        color=sim_res[2,:],
                        colorscale='Viridis',
                        showscale=True,
                        colorbar=dict(title="Sharpe")
                    ),
                    text=["Random Portfolio"] * 1000
                ))
                
                # Plot Current Equal Weight Point
                fig_ef.add_trace(go.Scatter(
                    x=[metrics['Volatility']], y=[metrics['Expected Return']],
                    mode='markers', marker=dict(color='red', size=12, symbol='star'),
                    name='Current (Equal Wgt)'
                ))
                
                fig_ef.update_layout(
                    title="Efficient Frontier",
                    xaxis_title="Volatility (Risk)",
                    yaxis_title="Return",
                    height=500,
                    template="plotly_dark"
                )
                st.plotly_chart(fig_ef, use_container_width=True)
                
            else:
                st.error("Could not fetch data.")
