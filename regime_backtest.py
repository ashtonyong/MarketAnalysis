import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go

@st.cache_data(ttl=3600)
def fetch_backtest_data(ticker, period="2y"):
    """Fetch daily data for backtesting."""
    try:
        df = yf.download(ticker, period=period, progress=False)
        if df.empty: return pd.DataFrame()
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return pd.DataFrame()

def run_regime_backtest(df, strategy_type, regime_filter):
    """Run backtest with regime filter."""
    data = df.copy()
    data['Returns'] = data['Close'].pct_change()
    
    # 1. Strategy Signal
    if strategy_type == "Identify Trend (SMA 50/200)":
        data['SMA50'] = data['Close'].rolling(50).mean()
        data['SMA200'] = data['Close'].rolling(200).mean()
        data['Signal'] = np.where(data['SMA50'] > data['SMA200'], 1, 0)
    elif strategy_type == "RSI Reversion":
        # RSI 14
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        data['RSI'] = 100 - (100 / (1 + rs))
        # Buy < 30, Sell > 70
        data['Signal'] = 0
        data.loc[data['RSI'] < 30, 'Signal'] = 1
        data.loc[data['RSI'] > 70, 'Signal'] = 0
        data['Signal'] = data['Signal'].ffill().fillna(0) # Hold until sell
    else: # Buy & Hold
        data['Signal'] = 1
        
    # 2. Regime Filter
    data['Regime'] = 1 # Default ON
    
    if regime_filter == "Bull Market Only (Price > SMA200)":
        data['SMA200_R'] = data['Close'].rolling(200).mean()
        data['Regime'] = np.where(data['Close'] > data['SMA200_R'], 1, 0)
    elif regime_filter == "Low Volatility Only":
        # ATR / Vol logic
        data['TrRange'] = np.maximum(
            data['High'] - data['Low'],
            np.maximum(
                abs(data['High'] - data['Close'].shift(1)),
                abs(data['Low'] - data['Close'].shift(1))
            )
        )
        data['ATR'] = data['TrRange'].rolling(14).mean()
        data['ATR_MA'] = data['ATR'].rolling(50).mean()
        data['Regime'] = np.where(data['ATR'] < data['ATR_MA'], 1, 0)
        
    # 3. Combined Signal
    data['Final_Signal'] = data['Signal'] * data['Regime']
    
    # 4. Strategy Returns (Shift signal by 1 to avoid lookahead)
    data['Strat_Ret'] = data['Final_Signal'].shift(1) * data['Returns']
    data['BuyHold_Ret'] = data['Returns']
    
    # 5. Equity Curves
    data['Equity_Strat'] = (1 + data['Strat_Ret'].fillna(0)).cumprod()
    data['Equity_BH'] = (1 + data['BuyHold_Ret'].fillna(0)).cumprod()
    
    return data

def render_regime_backtest(ticker):
    """Render the Regime-Conditional Backtest tab."""
    st.markdown("###  Regime-Conditional Backtest")
    st.caption("Test how strategies perform under specific market conditions.")
    
    c1, c2 = st.columns([1, 3])
    
    with c1:
        st.markdown("**Configuration**")
        strat = st.selectbox("Base Strategy", ["Buy & Hold", "Identify Trend (SMA 50/200)", "RSI Reversion"])
        regime = st.selectbox("Regime Filter", ["None", "Bull Market Only (Price > SMA200)", "Low Volatility Only"])
        
        if st.button("Run Simulation", key="run_regime"):
            st.session_state['regime_run'] = True
            
    with c2:
        if st.session_state.get('run_regime') or st.session_state.get('regime_run'):
            df = fetch_backtest_data(ticker)
            if not df.empty:
                res = run_regime_backtest(df, strat, regime)
                
                # Metrics
                total_ret_strat = (res['Equity_Strat'].iloc[-1] - 1) * 100
                total_ret_bh = (res['Equity_BH'].iloc[-1] - 1) * 100
                
                # MDD
                roll_max = res['Equity_Strat'].cummax()
                drawdown = res['Equity_Strat'] / roll_max - 1
                mdd = drawdown.min() * 100
                
                # Stats Row
                s1, s2, s3 = st.columns(3)
                s1.metric("Strategy Return", f"{total_ret_strat:+.2f}%")
                s2.metric("Buy & Hold Return", f"{total_ret_bh:+.2f}%", delta=f"{total_ret_strat - total_ret_bh:.2f}%")
                s3.metric("Max Drawdown", f"{mdd:.2f}%")
                
                # Chart
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=res.index, y=res['Equity_Strat'],
                    mode='lines', name='Strategy (Filtered)',
                    line=dict(color='cyan', width=2)
                ))
                fig.add_trace(go.Scatter(
                    x=res.index, y=res['Equity_BH'],
                    mode='lines', name='Buy & Hold',
                    line=dict(color='gray', dash='dash')
                ))
                
                # Plot Regime Background?
                # Too heavy for now.
                
                fig.update_layout(
                    title=f"Performance Comparison: {strat} + {regime}",
                    height=500, template="plotly_dark",
                    yaxis_title="Equity (Growth of $1)"
                )
                st.plotly_chart(fig, use_container_width=True)
                
            else:
                st.error("No data found.")
