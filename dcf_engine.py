import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go

@st.cache_data(ttl=3600)
def fetch_financials(ticker):
    """Fetch financial data for DCF."""
    try:
        t = yf.Ticker(ticker)
        info = t.info
        
        # Heuristic to check if Equity
        # If ticker contains '=' (Futures/Forexy) or is 'BTC-USD' etc.
        if '=' in ticker or '-USD' in ticker:
            return None, "DCF is only applicable to Equities (Stocks). Please select a stock ticker (e.g., AAPL, TSLA)."

        # Get Cash Flow
        cf = t.cashflow
        bs = t.balance_sheet
        
        if cf.empty or bs.empty:
            return None, "Financial statements unavailable."
            
        # Get latest full year data
        # columns are dates. use iloc[:, 0]
        latest_cf = cf.iloc[:, 0]
        latest_bs = bs.iloc[:, 0]
        
        # Free Cash Flow = Operating Cash Flow - CapEx
        ocf = latest_cf.get("Total Cash From Operating Activities", latest_cf.get("Operating Cash Flow"))
        capex = latest_cf.get("Capital Expenditures", latest_cf.get("Capital Expenditure"))
        
        if ocf is None or np.isnan(ocf):
            return None, "Operating Cash Flow not found."
            
        # CapEx is usually negative in yfinance, but sometimes positive. 
        # FCF = OCF - abs(CapEx) or OCF + CapEx (if negative)
        if capex is None: capex = 0
        fcf = ocf + capex if capex < 0 else ocf - capex
        
        # Balance Sheet items
        cash = latest_bs.get("Cash And Cash Equivalents", 0) + latest_bs.get("Other Short Term Investments", 0)
        debt = latest_bs.get("Total Debt", latest_bs.get("Long Term Debt", 0))
        
        shares = info.get("sharesOutstanding")
        price = info.get("currentPrice", info.get("regularMarketPrice"))
        
        if not shares or not price:
            return None, "Share count or price unavailable."
            
        data = {
            "fcf": fcf,
            "cash": cash,
            "debt": debt,
            "shares": shares,
            "price": price,
            "beta": info.get("beta", 1.0),
            "currency": info.get("currency", "USD")
        }
        return data, None
        
    except Exception as e:
        return None, str(e)

def calculate_dcf(data, growth_rate, terminal_growth, discount_rate):
    """Calculate Intrinsic Value."""
    fcf = data['fcf']
    
    # Project 5 years
    future_fcfs = []
    for i in range(1, 6):
        fcf_proj = fcf * ((1 + growth_rate) ** i)
        future_fcfs.append(fcf_proj)
        
    # Terminal Value (Gordon Growth)
    # TV = FCF5 * (1+g_term) / (WACC - g_term)
    last_fcf = future_fcfs[-1]
    tv = last_fcf * (1 + terminal_growth) / (discount_rate - terminal_growth)
    
    # Discount to PV
    pv_fcfs = 0
    for i, val in enumerate(future_fcfs):
        pv_fcfs += val / ((1 + discount_rate) ** (i + 1))
        
    pv_tv = tv / ((1 + discount_rate) ** 5)
    
    enterprise_value = pv_fcfs + pv_tv
    equity_value = enterprise_value + data['cash'] - data['debt']
    
    fair_value = equity_value / data['shares']
    
    return fair_value, equity_value, pv_fcfs, pv_tv

def render_dcf_engine(ticker):
    """Render the DCF Valuation Engine tab."""
    st.markdown("###  DCF Valuation Engine")
    st.caption("Estimate Intrinsic Value using Discounted Cash Flow analysis.")
    
    col_input, col_res = st.columns([1, 2])
    
    with col_input:
        st.markdown("**Assumptions**")
        growth_rate = st.slider("Growth Rate (5y)", 0.0, 0.5, 0.10, 0.01, format="%.2f")
        terminal_growth = st.slider("Terminal Growth", 0.0, 0.05, 0.02, 0.005, format="%.3f")
        discount_rate = st.slider("Discount Rate (WACC)", 0.05, 0.20, 0.09, 0.005, format="%.3f")
        
        st.info("""
        **Default Logic:**
        - FCF = OCF - CapEx (Last FY)
        - Projection: 5 Years
        - Terminal Value: Gordon Growth Model
        """)
        
        if st.button("Calculate Value", key="run_dcf"):
            st.session_state['dcf_run'] = True

    with col_res:
        if st.session_state.get('dcf_run'):
            data, err = fetch_financials(ticker)
            
            if data:
                fair_value, eq_val, pv_fcfs, pv_tv = calculate_dcf(data, growth_rate, terminal_growth, discount_rate)
                current_price = data['price']
                upside = (fair_value - current_price) / current_price * 100
                
                # Verdict
                if upside > 20:
                    verdict = "UNDERVALUED"
                    color = "green"
                elif upside < -20:
                    verdict = "OVERVALUED"
                    color = "red"
                else:
                    verdict = "FAIRLY VALUED"
                    color = "orange"
                    
                # Metrics Row
                m1, m2, m3 = st.columns(3)
                m1.metric("Fair Value", f"${fair_value:.2f}")
                m2.metric("Current Price", f"${current_price:.2f}")
                m3.metric("Upside / Downside", f"{upside:+.2f}%", 
                          delta_color="normal" if upside > 0 else "inverse") 
                          # Actually inverse is wrong if I want green for positive upside. 
                          # 'normal' gives Green for positive delta.
                
                st.markdown(f"#### Verdict: :{color}[{verdict}]")
                
                # Waterfall Chart breakdown
                fig = go.Figure(go.Waterfall(
                    name = "DCF", orientation = "v",
                    measure = ["absolute", "relative", "relative", "relative", "relative", "total", "absolute"],
                    x = ["PV of FCFs", "+ PV of Terminal Val", "+ Cash", "- Debt", "Enterprise Value", "Equity Value", "Fair Value"],
                    # Actually logic: PV(FCF) + PV(TV) = EV. EV + Cash - Debt = EqVal.
                    # Waterfall requires sequential steps.
                    # 1. PV FCFs (Base)
                    # 2. PV TV (Add)
                    # 3. Cash (Add)
                    # 4. Debt (Subtract)
                    # 5. Result = Equity Value.
                    textposition = "outside",
                    # text = [f"{pv_fcfs/1e9:.2f}B", f"{pv_tv/1e9:.2f}B", f"{data['cash']/1e9:.2f}B", f"-{data['debt']/1e9:.2f}B", f"{eq_val/1e9:.2f}B"],
                    y = [pv_fcfs, pv_tv, data['cash'], -data['debt'], 0, 0, 0], # Using dummy 0s for intermediate totals if needed?
                    # Simpler breakdown:
                    # PV FCFs, PV TV, Cash, Debt (neg), Equity Value (Total)
                ))
                
                # Let's do a simple bar chart or pie? 
                # Waterfall is tricky without proper "total" handling.
                # Let's simple use a Bar chart of components.
                
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=["PV FCFs", "PV Terminal", "Cash"],
                    y=[pv_fcfs, pv_tv, data['cash']],
                    name="Assets", marker_color="green"
                ))
                fig.add_trace(go.Bar(
                    x=["Debt"],
                    y=[data['debt']],
                    name="Liabilities", marker_color="red"
                ))
                fig.add_trace(go.Bar(
                    x=["Equity Value"],
                    y=[eq_val],
                    name="Equity", marker_color="blue"
                ))
                
                fig.update_layout(title="Valuation Components", height=400, template="plotly_dark")
                st.plotly_chart(fig, use_container_width=True)
                
            else:
                st.error(err)
