import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import statsmodels.api as sm
import plotly.graph_objects as go

@st.cache_data(ttl=3600)
def fetch_factor_data(ticker, period="2y"):
    """Fetch return data for ticker and factor proxies."""
    try:
        # Proxies
        # Mkt: SPY
        # SMB: IWM (Small Cap) - SPY (Large Cap) ? Or just IWM as Small factor?
        # A common proxy approach:
        # Mkt = SPY
        # SMB = IWM (Small) - SPY (Large) is rough. 
        # Better: use IWM and SPY returns as regressors?
        # Standard FF uses long-short portfolio returns.
        # Let's simple use: SPY, IWM, VTV (Value), VUG (Growth)
        # SMB Proxy = IWM - SPY
        # HML Proxy = VTV - VUG
        
        tickers = [ticker, 'SPY', 'IWM', 'VTV', 'VUG']
        df = yf.download(tickers, period=period, progress=False)['Close']
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        returns = df.pct_change().dropna()
        return returns
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return pd.DataFrame()

def run_factor_model(returns, ticker):
    """Run 3-Factor Regression."""
    # Construct Factors
    # Excess Returns (assume RF=0 for simplicity, or 0.04/252)
    rf = 0.04 / 252
    
    # Target
    y = returns[ticker] - rf
    
    # Factors
    mkt = returns['SPY'] - rf
    smb = returns['IWM'] - returns['SPY'] # Small minus Big Proxy
    hml = returns['VTV'] - returns['VUG'] # Value minus Growth Proxy
    
    X = pd.DataFrame({'Mkt-RF': mkt, 'SMB': smb, 'HML': hml})
    X = sm.add_constant(X)
    
    model = sm.OLS(y, X).fit()
    return model

def render_factor_model(ticker):
    """Render the Fama-French Factor Model tab."""
    st.markdown("### 📚 Fama-French 3-Factor Model (Proxy)")
    st.caption("Decompose returns into Market, Size, and Value risks using ETF proxies.")
    
    if st.button("Run Regression", key="run_ff"):
        with st.spinner("Fetching data and calculating..."):
            returns = fetch_factor_data(ticker)
            
            if not returns.empty and ticker in returns.columns:
                try:
                    model = run_factor_model(returns, ticker)
                    
                    # Metrics
                    alpha = model.params['const'] * 252 # Annualized
                    beta_mkt = model.params['Mkt-RF']
                    beta_smb = model.params['SMB']
                    beta_hml = model.params['HML']
                    r2 = model.rsquared
                    
                    c1, c2, c3, c4, c5 = st.columns(5)
                    c1.metric("Alpha (Ann.)", f"{alpha:.2%}", delta_color="normal")
                    c2.metric("Market Beta", f"{beta_mkt:.2f}")
                    c3.metric("Size Beta (SMB)", f"{beta_smb:.2f}")
                    c4.metric("Value Beta (HML)", f"{beta_hml:.2f}")
                    c5.metric("R-Squared", f"{r2:.2f}")
                    
                    st.markdown("---")
                    
                    # Interpretation
                    st.markdown("#### Factor Loadings Interpretation")
                    
                    direction_smb = "Small Cap Tilt" if beta_smb > 0 else "Large Cap Tilt"
                    direction_hml = "Value Tilt" if beta_hml > 0 else "Growth Tilt"
                    
                    st.info(f"""
                    - **Market**: Sensitivity to broad market moves.
                    - **SMB ({beta_smb:.2f})**: Uses {direction_smb}.
                    - **HML ({beta_hml:.2f})**: Uses {direction_hml}.
                    - **Alpha**: Excess return not explained by these factors.
                    """)
                    
                    # Chart: Rolling Alpha or Residuals?
                    # Let's plot Predicted vs Actual?
                    # Or just coefficient bar chart.
                    
                    coefs = model.params.drop('const')
                    fig = go.Figure(go.Bar(
                        x=coefs.index, y=coefs.values,
                        marker_color=['blue', 'orange', 'green']
                    ))
                    fig.update_layout(title="Factor Betas", height=300, template="plotly_dark")
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Show summary stats
                    with st.expander("Regression Summary"):
                        st.text(model.summary().as_text())
                        
                except Exception as e:
                    st.error(f"Modeling Error: {e}")
            else:
                st.error("Insufficient data.")
