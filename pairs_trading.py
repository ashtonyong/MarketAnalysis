import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
import statsmodels.api as sm

class PairsTrader:
    def __init__(self, ticker1, ticker2):
        self.t1 = ticker1
        self.t2 = ticker2
        
    def fetch_data(self, period="1y"):
        try:
            # Fetch data for both
            tickers = f"{self.t1} {self.t2}"
            df = yf.download(tickers, period=period, group_by='ticker', progress=False)
            
            # Extract closes
            data = pd.DataFrame()
            data[self.t1] = df[self.t1]['Close']
            data[self.t2] = df[self.t2]['Close']
            
            # Normalize to avoid NaN issues at start/end
            return data.dropna()
        except Exception as e:
            st.error(f"Error fetching pair data: {e}")
            return pd.DataFrame()
            
    def calculate_metrics(self, data):
        if data.empty: return None
        
        # 1. Hedge Ratio (OLS Regression)
        # B = beta * A + alpha
        # We want Spread = B - beta * A
        
        Y = data[self.t1]
        X = data[self.t2]
        X_const = sm.add_constant(X)
        
        try:
            model = sm.OLS(Y, X_const).fit()
            hedge_ratio = model.params[1]
            alpha = model.params[0]
            r_squared = model.rsquared
        except:
            # Fallback if statsmodels fails or singular matrix
            hedge_ratio = 1.0
            alpha = 0.0
            r_squared = 0.0
            
        # 2. Spread
        # Spread = Y - (HedgeRatio * X) - Alpha
        spread = Y - (hedge_ratio * X) - alpha
        
        # 3. Z-Score of Spread
        # Rolling Z-Score (30 day window) usually better for trading than static
        # But for Cointegration check, we often look at static mean
        
        spread_mean = spread.mean()
        spread_std = spread.std()
        
        z_score = (spread - spread_mean) / spread_std
        
        # 4. Correlation
        corr = data[self.t1].corr(data[self.t2])
        
        return {
            "hedge_ratio": hedge_ratio,
            "alpha": alpha,
            "r_squared": r_squared,
            "correlation": corr,
            "spread": spread,
            "z_score": z_score,
            "data": data
        }

def render_pairs_trading(default_ticker):
    st.markdown("## ⚖️ Pairs Trading Scanner")
    st.caption("Analyze the statistical relationship (Cointegration/Correlation) between two assets.")
    
    col1, col2 = st.columns(2)
    with col1:
        ticker1 = st.text_input("Ticker A", value=default_ticker).upper()
    with col2:
        # Suggest a default pair based on Ticker A?
        default_t2 = "QQQ" if default_ticker == "SPY" else "SPY"
        ticker2 = st.text_input("Ticker B", value=default_t2).upper()
        
    if ticker1 == ticker2:
        st.warning("Select two different tickers.")
        return
        
    if st.button("Analyze Pair"):
        pt = PairsTrader(ticker1, ticker2)
        
        with st.spinner(f"Analyzing {ticker1} vs {ticker2}..."):
            data = pt.fetch_data()
            if data.empty:
                st.error("Could not fetch data.")
                return
                
            res = pt.calculate_metrics(data)
            
        if not res:
            st.error("Analysis failed.")
            return
            
        # --- Metrics ---
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Correlation", f"{res['correlation']:.2f}")
        m2.metric("Hedge Ratio", f"{res['hedge_ratio']:.3f}")
        m3.metric("R-Squared", f"{res['r_squared']:.3f}")
        
        last_z = res['z_score'].iloc[-1]
        m4.metric("Current Spread Z-Score", f"{last_z:.2f}", 
                  delta="Extreme" if abs(last_z) > 2 else "Normal",
                  delta_color="inverse")
                  
        st.divider()
        
        # --- Charts ---
        # 1. Normalized Price Comparison
        norm_data = res['data'] / res['data'].iloc[0] * 100
        
        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(x=norm_data.index, y=norm_data[ticker1], name=ticker1))
        fig1.add_trace(go.Scatter(x=norm_data.index, y=norm_data[ticker2], name=ticker2))
        fig1.update_layout(title="Normalized Price Performance (Start=100)", template="plotly_dark", height=350)
        st.plotly_chart(fig1, use_container_width=True)
        
        # 2. Spread Z-Score
        z = res['z_score']
        
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=z.index, y=z, name="Spread Z-Score", line=dict(color='orange')))
        
        # Add bands
        fig2.add_hline(y=2.0, line_dash="dash", line_color="red", annotation_text="Sell Spread (+2)")
        fig2.add_hline(y=-2.0, line_dash="dash", line_color="green", annotation_text="Buy Spread (-2)")
        fig2.add_hline(y=0, line_color="gray")
        
        fig2.update_layout(
            title=f"Spread Z-Score ({ticker1} vs {ticker2})", 
            yaxis_title="Std Dev",
            template="plotly_dark", 
            height=350
        )
        st.plotly_chart(fig2, use_container_width=True)
        
        st.info(f"""
        **Strategy Logic**:
        *   **Buy Spread**: When Z-Score < -2.0 (Spread is too low). Buy {ticker1} / Sell {ticker2}.
        *   **Sell Spread**: When Z-Score > +2.0 (Spread is too high). Sell {ticker1} / Buy {ticker2}.
        *   **Hedge Ratio**: 1 unit of {ticker1} = {res['hedge_ratio']:.2f} units of {ticker2}.
        """)
