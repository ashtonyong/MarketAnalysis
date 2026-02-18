import pandas as pd
import numpy as np
import yfinance as yf
import streamlit as st
import plotly.graph_objects as go

class RegimeBacktester:
    def __init__(self, ticker):
        self.ticker = ticker
        
    def run_backtest(self, initial_capital=100000, trend_threshold=0.3):
        # 1. Fetch Data
        df = yf.download(self.ticker, period="2y", progress=False)
        if df.empty: return None
        
        # 2. Add technicals needed for regime detection (ADX, Volatility)
        # Re-using QuantEngine logic manually here for speed or importing? 
        # Ideally we'd run the detector row-by-row but that's slow.
        # Vectorized approach:
        
        # Simple Regime Logic for Backtest:
        # Volatility Regime: Rolling Std Dev
        # Trend Regime: SMA 50 vs SMA 200
        
        close = df['Close']
        df['SMA50'] = close.rolling(50).mean()
        df['SMA200'] = close.rolling(200).mean()
        df['Returns'] = close.pct_change()
        df['Vol'] = df['Returns'].rolling(20).std() * np.sqrt(252)
        
        # Signals
        # 1 = Long, 0 = Cash, -1 = Short
        df['Signal'] = 0
        
        # STRATEGY:
        # Long only when SMA50 > SMA200 (Trending Up) AND Volatility is NOT Extreme (< 40%)
        # Cash when Trending Down or High Volatility
        
        conditions = (df['SMA50'] > df['SMA200']) & (df['Vol'] < 0.40)
        df.loc[conditions, 'Signal'] = 1
        
        # Calculate Returns
        df['Strategy_Returns'] = df['Signal'].shift(1) * df['Returns']
        df['BuyHold_Returns'] = df['Returns']
        
        # Cumulative Wealth
        df['Strategy_Equity'] = (1 + df['Strategy_Returns']).cumprod() * initial_capital
        df['BuyHold_Equity'] = (1 + df['BuyHold_Returns']).cumprod() * initial_capital
        
        return df.dropna()

def render_regime_backtest(ticker):
    st.markdown("## 🛡️ Regime-Adaptive Backtest")
    st.caption("Compares a static Buy & Hold strategy vs. a Regime-Adaptive strategy.")
    st.info("Adaptive Strategy: Long only when Trend is UP (SMA50 > SMA200) and Volatility is Stable (< 40%).")
    
    bt = RegimeBacktester(ticker)
    
    if st.button("Run Simulation"):
        with st.spinner("Running backtest..."):
            res = bt.run_backtest()
            
        if res is None or res.empty:
            st.error("Backtest failed (insufficient data).")
            return
            
        final_strat = res['Strategy_Equity'].iloc[-1]
        final_bh = res['BuyHold_Equity'].iloc[-1]
        
        strat_ret = (final_strat - 100000) / 100000 * 100
        bh_ret = (final_bh - 100000) / 100000 * 100
        
        # --- Metrics ---
        c1, c2, c3 = st.columns(3)
        c1.metric("Strategy Return", f"{strat_ret:.1f}%", f"${final_strat:,.0f}")
        c2.metric("Buy & Hold Return", f"{bh_ret:.1f}%", f"${final_bh:,.0f}")
        
        outperf = strat_ret - bh_ret
        c3.metric("Outperformance", f"{outperf:+.1f}%", delta_color="normal" if outperf > 0 else "inverse")
        
        st.divider()
        
        # --- Equity Curve ---
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=res.index, y=res['Strategy_Equity'], name='Adaptive Strategy', line=dict(color='cyan', width=2)))
        fig.add_trace(go.Scatter(x=res.index, y=res['BuyHold_Equity'], name='Buy & Hold', line=dict(color='gray', width=2, dash='dot')))
        
        # Shade Regimes
        # Where Signal == 1 (Long) -> Green Background? 
        # Too messy. Let's just show curve.
        
        fig.update_layout(title="Equity Curve Comparison (Start: $100k)", template="plotly_dark", height=400, yaxis_title="Equity ($)")
        st.plotly_chart(fig, use_container_width=True)
