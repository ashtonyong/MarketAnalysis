import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import streamlit as st
import time

@st.cache_data(ttl=3600)
def fetch_price_targets(ticker: str) -> dict:
    try:
        t = yf.Ticker(ticker)
        info = t.info
        
        # Get current price safely
        current_price = info.get("currentPrice") or info.get("regularMarketPrice") or info.get("previousClose")
        
        # Get targets
        targets = {
            "current_price": current_price,
            "target_mean": info.get("targetMeanPrice"),
            "target_high": info.get("targetHighPrice"),
            "target_low": info.get("targetLowPrice"),
            "target_median": info.get("targetMedianPrice"),
            "analyst_count": info.get("numberOfAnalystOpinions"),
            "recommendation": info.get("recommendationKey", "N/A").upper().replace("_", " "),
            "recommendation_mean": info.get("recommendationMean"), # 1=Strong Buy, 5=Sell
        }
        return targets
    except Exception as e:
        return {"error": str(e)}

def render_price_targets(ticker: str):
    st.markdown("##  Analysis Consensus & Price Targets")
    st.caption(f"Wall Street analyst price targets and recommendations for **{ticker}**.")

    with st.spinner("Fetching analyst data..."):
        data = fetch_price_targets(ticker)
        time.sleep(0.1)

    if "error" in data:
        st.error(f"Error fetching targets: {data['error']}")
        return

    curr = data.get("current_price")
    mean = data.get("target_mean")
    high = data.get("target_high")
    low = data.get("target_low")
    count = data.get("analyst_count")
    rec = data.get("recommendation")
    
    if not mean or not curr:
        st.info("No analyst coverage or price target data available for this ticker.")
        return

    # Helper for Upside
    upside = (mean - curr) / curr * 100
    
    # --- Row 1: Key Metrics ---
    c1, c2, c3, c4 = st.columns(4)
    
    # Upside Card
    u_color = "green" if upside > 0 else "red"
    c1.metric("Implied Upside", f"{upside:+.2f}%", delta_color="normal" if upside > 0 else "inverse")
    
    # Recommendation Badge
    # Color logic
    if "BUY" in rec: r_color = "green"
    elif "SELL" in rec: r_color = "red"
    else: r_color = "orange"
    
    c2.markdown(f"**Consensus**")
    c2.markdown(f":{r_color}-background[{rec}]")
    
    c3.metric("Analysts", count if count else "N/A")
    c4.metric("Mean Target", f"${mean:.2f}")

    st.markdown("---")

    # --- Row 2: Visual Target Range ---
    # We want a horizontal chart showing Low -> Current -> Mean -> High
    
    fig = go.Figure()

    # 1. Range Bar (Low to High)
    if low and high:
        fig.add_trace(go.Scatter(
            x=[low, high], y=["Targets", "Targets"],
            mode='lines',
            line=dict(color='#30363d', width=12),
            showlegend=False,
            hoverinfo='skip'
        ))
        
        # Add endpoints
        fig.add_trace(go.Scatter(
            x=[low, high], y=["Targets", "Targets"],
            mode='markers',
            marker=dict(color='#30363d', size=12),
            showlegend=False,
            hoverinfo='skip'
        ))
        
        # Annotate Low and High
        fig.add_annotation(x=low, y="Targets", text=f"Low: ${low}", showarrow=True, arrowhead=0, ay=25)
        fig.add_annotation(x=high, y="Targets", text=f"High: ${high}", showarrow=True, arrowhead=0, ay=25)

    # 2. Mean Target Marker (Green)
    fig.add_trace(go.Scatter(
        x=[mean], y=["Targets"],
        mode='markers',
        marker=dict(color='#00ff88', size=18, symbol='diamond'),
        name='Mean Target',
        hovertemplate=f"Mean: ${mean}<extra></extra>"
    ))
    
    # 3. Current Price Marker (White/Blue)
    fig.add_trace(go.Scatter(
        x=[curr], y=["Targets"],
        mode='markers',
        marker=dict(color='white', size=14, symbol='line-ns-open', line=dict(color='white', width=3)),
        name='Current Price',
        hovertemplate=f"Current: ${curr}<extra></extra>"
    ))
    
    # Add annotation for current and mean
    fig.add_annotation(x=mean, y="Targets", text=f"Mean: ${mean}", showarrow=True, arrowhead=0, ay=-30, font=dict(color="#00ff88"))
    fig.add_annotation(x=curr, y="Targets", text=f"Curr: ${curr}", showarrow=True, arrowhead=0, ay=30, font=dict(color="white"))

    # Layout
    # Determine range padding
    min_x = min(low, curr) * 0.9 if low else curr * 0.9
    max_x = max(high, curr) * 1.1 if high else curr * 1.1
    
    fig.update_layout(
        height=200,
        xaxis=dict(title="Price (USD)", range=[min_x, max_x], showgrid=False),
        yaxis=dict(showgrid=False, showticklabels=False),
        template="plotly_dark",
        margin=dict(l=20, r=20, t=10, b=10),
        legend=dict(orientation="h", y=1.1)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # --- Row 3: Recommendation Distribution (Donut) ---
    # yfinance 'recommendations' is a DataFrame usually?
    # t.recommendations gives history.
    # Info sometimes defines 'recommendationMean'.
    # For distribution, we might check 'recommendations' property if recent.
    # But often unreliable or messy.
    # Let's check 'recommendationKey' again. Nothing more granular in standard .info usually.
    # We will skip the donut chart if data is missing, or mock it if we had 'numberOfAnalystOpinions' breakdown (Buy/Hold/Sell count), 
    # but yfinance API doesn't always provide the counts easily in .info.
    # We can try t.recommendations_summary if available (newer yf?)
    
    try:
        t = yf.Ticker(ticker)
        # Check for recommendations summary (newer endpoint)
        # rec_sum = t.get_recommendations_summary() # Not standard.
        # Check standard recommendations
        recs = t.recommendations
        if recs is not None and not recs.empty:
            # recs is historical. 
            # Columns: period, strongBuy, buy, hold, sell, strongSell
            # We want the latest period (0m or current row).
            # Usually indexed by 0, 1, 2, 3 (periods: 0m, -1m, -2m, -3m).
            # Let's try to get row 0.
            if 'To Grade' in recs.columns:
                 # Old format: Date, Firm, To Grade, From Grade, Action
                 # We can count distinct "To Grade" in last 90 days?
                 pass
            else:
                 # New format might exist.
                 # Actually standard yf usually returns historical upgrades/downgrades df.
                 pass
            # If we simply rely on 'recommendationMean' (1-5), we can visualize that on a scale.
    except:
        pass

    # Recommendation Scale Bar (1-5)
    rec_mean = data.get("recommendation_mean") # 1 = Strong Buy, 5 = Strong Sell
    if rec_mean:
        st.markdown("### Analyst Sentiment Score")
        st.caption("Lower score is better (1.0 = Strong Buy, 5.0 = Sell)")
        
        # Custom progress bar logic
        # 1.0 -> 100% (Green). 5.0 -> 0% (Red).
        # Invert: score 1 => value 1.0. score 5 => value 0.
        # Formula: (5 - score) / 4
        # Range 1 to 5. Length 4.
        # 5 - 1 = 4 / 4 = 1.0
        # 5 - 5 = 0 / 4 = 0.0
        # 5 - 3 = 2 / 4 = 0.5
        norm_score = max(0, min(1, (5 - rec_mean) / 4))
        
        st.progress(norm_score)
        c01, c02, c03 = st.columns([1, 8, 1])
        c01.markdown("Sell")
        c03.markdown("Buy")
        c02.markdown(f"<div style='text-align:center'><b>{rec_mean:.1f}</b></div>", unsafe_allow_html=True)

