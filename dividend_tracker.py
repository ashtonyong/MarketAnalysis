import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import streamlit as st
import time
from datetime import datetime

@st.cache_data(ttl=300)
def fetch_dividend_data(ticker: str) -> dict:
    try:
        t = yf.Ticker(ticker)
        info = t.info
        dividends = t.dividends  # Historical dividend payments Series
        
        # Helper to safely get info
        def get_i(key, default=None):
            return info.get(key, default)

        # Get financials for safety score
        try:
            financials = t.financials
            if not financials.empty:
                fcf = (financials.loc['Total Cash From Operating Activities'].iloc[0] + 
                       financials.loc['Capital Expenditures'].iloc[0]) if 'Total Cash From Operating Activities' in financials.index and 'Capital Expenditures' in financials.index else None
                revenue_growth = info.get("revenueGrowth", 0)
            else:
                fcf = None
                revenue_growth = None
        except:
            fcf = None
            revenue_growth = None

        # Calculate yield manually to be safe
        div_rate = get_i("dividendRate")
        price = get_i("currentPrice") or get_i("previousClose")
        
        if div_rate and price and price > 0:
            final_yield = (div_rate / price) * 100
        else:
            # Fallback to provided yield
            raw_yield = get_i("dividendYield")
            if raw_yield:
                # If > 1, assume percent. If < 0.1, assume decimal.
                # Between 0.1 and 1 is ambiguous (10% to 100% or 0.1% to 1%?)
                # But yield > 10% is rare for non-REITs. Yield < 1% is common.
                # If we have to guess:
                if raw_yield < 0.2: # Assume decimal (0.05 = 5%)
                    final_yield = raw_yield * 100
                else:
                    final_yield = raw_yield
            else:
                final_yield = None

        data = {
            "yield": final_yield,
            "annual_dividend": get_i("dividendRate", None),
            "payout_ratio": get_i("payoutRatio", None),
            "ex_date": get_i("exDividendDate", None),
            "5yr_avg_yield": get_i("fiveYearAvgDividendYield", None),
            "history": dividends,
            "debt_to_equity": get_i("debtToEquity", 0),
            "fcf": fcf,
            "revenue_growth": revenue_growth
        }
        return data
    except Exception as e:
        return {"error": str(e)}

def calc_dividend_cagr(dividends: pd.Series, years: int = 5) -> float:
    if dividends is None or len(dividends) < 2:
        return None
    # Resample to annual
    try:
        annual = dividends.resample('Y').sum()
        if len(annual) < 2:
            return None
        
        # Get start and end points
        # If we asked for 5 years, looks for -6th element (5 years ago)
        lookback = min(years + 1, len(annual))
        start = annual.iloc[-lookback]
        end = annual.iloc[-1]
        
        n = lookback - 1
        if start <= 0 or n <= 0:
            return None
            
        cagr = ((end / start) ** (1 / n) - 1) * 100
        return cagr
    except:
        return None

def calc_safety_score(payout_ratio, debt_to_equity, fcf, revenue_growth) -> int:
    score = 100
    # Payout ratio penalty (lower is better)
    if payout_ratio:
        if payout_ratio > 0.9: score -= 40
        elif payout_ratio > 0.7: score -= 20
        elif payout_ratio > 0.5: score -= 10
        elif payout_ratio < 0: score -= 50 # Negative payout usually means earnings negative
    
    # Debt penalty
    if debt_to_equity:
        # debtToEquity is usually returned as %, so 100 = 1.0 ratio
        # Let's normalize. If yfinance returns 150 for 1.5, we adjust.
        # Actually yfinance returns ratio? "debtToEquity": 182.251 -> 1.82? 
        # Usually it's a percentage. 100 = 1:1.
        ratio = debt_to_equity / 100
        if ratio > 2.0: score -= 20
        elif ratio > 1.0: score -= 10
    
    # Negative FCF penalty
    if fcf and fcf < 0: score -= 30
    
    # Revenue growth bonus
    if revenue_growth and revenue_growth > 0.05: score += 10
    
    return max(0, min(100, score))

def render_dividend_tracker(ticker: str):
    st.markdown("##  Dividend Tracker")
    st.caption("Comprehensive analysis of dividend yield, growth, and safety.")

    with st.spinner("Fetching dividend data..."):
        data = fetch_dividend_data(ticker)
        time.sleep(0.3) # API politeness

    if "error" in data:
        st.error(f"Error fetching data: {data['error']}")
        return

    # Check if pays dividend
    div_yield = data.get("yield")
    if div_yield is None or (data["history"].empty and div_yield == 0):
        st.info(f"ℹ️ **{ticker}** does not appear to pay a dividend.")
        return

    # Metrics
    cagr_5yr = calc_dividend_cagr(data["history"], 5)
    safety_score = calc_safety_score(
        data["payout_ratio"], 
        data.get("debt_to_equity"), 
        data.get("fcf"), 
        data.get("revenue_growth")
    )
    
    # Safety Color
    if safety_score >= 70: s_color = "green"
    elif safety_score >= 40: s_color = "orange"
    else: s_color = "red"

    # Layout
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Dividend Yield", f"{div_yield:.2f}%")
    m2.metric("Annual Payout", f"${data['annual_dividend']:.2f}" if data['annual_dividend'] else "N/A")
    m3.metric("Payout Ratio", f"{data['payout_ratio']*100:.1f}%" if data['payout_ratio'] else "N/A")
    m4.metric("5yr Avg Yield", f"{data['5yr_avg_yield']:.2f}%" if data['5yr_avg_yield'] else "N/A")

    st.markdown("---")

    c1, c2, c3 = st.columns(3)
    
    # Ex-Div Date
    ex_ts = data.get("ex_date")
    if ex_ts:
        ex_date_str = pd.Timestamp(ex_ts, unit='s').strftime('%b %d, %Y')
    else:
        ex_date_str = "N/A"
    
    c1.metric("Ex-Dividend Date", ex_date_str)
    c2.metric("5yr Dividend CAGR", f"{cagr_5yr:.1f}%" if cagr_5yr is not None else "N/A")
    c3.markdown(f"**Safety Score**: :{s_color}[{safety_score}/100]")
    
    st.progress(safety_score / 100)

    # Charts
    tab_hist, tab_yield = st.tabs(["Dividend History", "Yield History"])
    
    with tab_hist:
        df_div = data["history"]
        if not df_div.empty:
            # Resample to annual for bar chart
            annual_pay = df_div.resample('Y').sum()
            annual_pay.index = annual_pay.index.strftime('%Y')
            
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=annual_pay.index,
                y=annual_pay.values,
                name="Annual Dividend",
                marker_color="#00C9FF"
            ))
            
            # Trend line
            # Simple linear fit just for visual or use Plotly trendline
            
            fig.update_layout(
                title="Annual Dividend Payments (USD)",
                yaxis_title="Dividend Per Share",
                template="plotly_dark",
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Dividend Calendar logic (Estimation)
            st.subheader(" Estimated Dividend Calendar")
            last_payment = df_div.index[-1]
            # Detect frequency
            if len(df_div) > 4:
                diffs = df_div.index.to_series().diff().dropna().dt.days
                avg_diff = diffs.mean()
                if 25 <= avg_diff <= 35: freq = "Monthly"; days=30
                elif 80 <= avg_diff <= 100: freq = "Quarterly"; days=91
                elif 170 <= avg_diff <= 190: freq = "Semi-Annual"; days=182
                else: freq = "Annual"; days=365
            else:
                freq = "Unknown"; days = 91 # Default quarterly
                
            est_dates = []
            next_date = last_payment
            for i in range(4):
                next_date = next_date + pd.Timedelta(days=days)
                est_dates.append(next_date.strftime('%b %d, %Y'))
            
            st.info(f"Based on historical **{freq}** frequency, next estimated ex-dates:")
            cols = st.columns(4)
            for i, d in enumerate(est_dates):
                cols[i].markdown(f"**{d}**")
                
        else:
            st.warning("No dividend history details found.")

    with tab_yield:
        # Need price history to calc yield history
        # Yield = Div(TTM) / Price
        # This is expensive to calc correctly rolling TTM
        # Approximation: Get 5y history, get 5y dividends.
        st.caption("Yield history requires processing extensive price data. (Simplified view)")
        # Just fetching 1y yield from yfinance if available or skip for speed?
        # User guide asked for "Line chart of trailing dividend yield over last 5 years"
        # We can try to approximate it or fetch it.
        # Let's do a simple calculation if possible.
        try:
            hist_price = yf.download(ticker, period="5y", interval="1wk", progress=False)['Close']
            if not hist_price.empty and not df_div.empty:
                # Align to weekly
                # Rolling 12m sum of dividends
                div_w = df_div.resample('W').sum().reindex(hist_price.index, fill_value=0)
                rolling_div = div_w.rolling(52).sum()
                
                yield_hist = (rolling_div / hist_price) * 100
                
                fig_y = go.Figure()
                fig_y.add_trace(go.Scatter(
                    x=yield_hist.index, y=yield_hist,
                    mode='lines', name='Trailing Yield %',
                    line=dict(color='yellow')
                ))
                fig_y.update_layout(title="Trailing 12-Month Dividend Yield", template="plotly_dark", height=400)
                st.plotly_chart(fig_y, use_container_width=True)
            else:
                st.warning("Insufficient data for yield chart.")
        except Exception as e:
            st.error(f"Could not load yield chart: {e}")
