import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import streamlit as st
import time

@st.cache_data(ttl=600)
def get_peers(ticker: str) -> list:
    try:
        t = yf.Ticker(ticker)
        info = t.info
        sector = info.get("sector", "")
        industry = info.get("industry", "")
        
        PEER_GROUPS = {
            "Semiconductors": ["NVDA","AMD","INTC","QCOM","AVGO","MU","TSM","AMAT"],
            "Internet Content & Information": ["GOOGL","META","SNAP","PINS","TWTR","YELP"],
            "Consumer Electronics": ["AAPL","SONY","SSNLF","HPQ","DELL"],
            "Software—Application": ["MSFT","CRM","ORCL","SAP","ADBE","NOW","WDAY"],
            "Banks—Diversified": ["JPM","BAC","WFC","C","GS","MS"],
            "Drug Manufacturers": ["JNJ","PFE","MRK","ABBV","LLY","BMY"],
            "Oil & Gas E&P": ["XOM","CVX","COP","OXY","PXD","DVN"],
            "Retail—Cyclical": ["AMZN","WMT","TGT","COST","HD","LOW"],
            "Asset Management": ["BLK","SCHW","MS","GS","BAC"],
            "Auto Manufacturers": ["TSLA","F","GM","TM","HMC","RIVN"],
            "Beverages": ["KO","PEP","MNST","KDP","CELH"],
            "Credit": ["V","MA","AXP","DFS","COF"],
            "Entertainment": ["DIS","NFLX","WBD","PARA","CMCSA"]
        }
        
        for key, peers in PEER_GROUPS.items():
            if key.lower() in str(industry).lower():
                return [p for p in peers if p != ticker][:7]
        return []
    except:
        return []

@st.cache_data(ttl=600)
def fetch_peer_metrics(tickers: list) -> pd.DataFrame:
    metrics_data = []
    
    # Define metrics: key (yf), label, is_percent
    METRICS_DEF = [
        ("trailingPE", "P/E", False),
        ("forwardPE", "Fwd P/E", False),
        ("priceToBook", "P/B", False),
        ("enterpriseToEbitda", "EV/EBITDA", False),
        ("priceToSalesTrailing12Months", "P/S", False),
        ("returnOnEquity", "ROE", True),
        ("returnOnAssets", "ROA", True),
        ("profitMargins", "Net Margin", True),
        ("revenueGrowth", "Rev Growth", True),
        ("dividendYield", "Div Yield", True),
        ("debtToEquity", "Debt/Eq", False), # Usually returned as percent by YF, e.g. 150
        ("marketCap", "Market Cap", False)
    ]

    for i, t in enumerate(tickers):
        try:
            info = yf.Ticker(t).info
            row = {"Ticker": t}
            for key, label, is_pct in METRICS_DEF:
                val = info.get(key)
                if val is not None:
                    # Normalize if YF returns raw float for percentage fields
                    # But YF behavior varies. usually decimal for yield, margins.
                    # debtToEquity is usually 0-100+.
                    # marketCap is raw number.
                    pass
                row[label] = val
            metrics_data.append(row)
        except:
            pass
        time.sleep(0.1)
    
    if not metrics_data:
        return pd.DataFrame()
        
    return pd.DataFrame(metrics_data)

def render_peer_comparison(ticker: str):
    st.markdown("##  Peer Comparison Engine")
    
    # 1. Get Peers
    auto_peers = get_peers(ticker)
    
    with st.expander("️ Comparison Settings", expanded=not auto_peers):
        val = ",".join(auto_peers) if auto_peers else ""
        peers_input = st.text_input("Peer Tickers (comma separated)", value=val)
        if st.button("Apply Peers"):
            st.session_state['custom_peers'] = [x.strip().upper() for x in peers_input.split(",") if x.strip()]

    # Resolve list
    peers_to_use = st.session_state.get('custom_peers', auto_peers)
    if not peers_to_use:
        # Tried to check session but might be empty.
        peers_to_use = [x.strip().upper() for x in peers_input.split(",") if x.strip()]
    
    final_list = [ticker] + [p for p in peers_to_use if p != ticker]
    final_list = list(dict.fromkeys(final_list))[:8]

    if len(final_list) < 2:
        st.info("Add peers to compare.")
        return

    # 2. Fetch Data
    with st.spinner("Fetching peer metrics..."):
        df = fetch_peer_metrics(final_list)
    
    if df.empty:
        st.error("No data available.")
        return

    # 3. Process Data for Display
    df = df.set_index("Ticker")
    
    # Separate formatting logic from calculation logic
    # We want a heatmap. Lower is better for Valuation. Higher is better for Profit.
    
    val_cols = ["P/E", "Fwd P/E", "P/B", "EV/EBITDA", "P/S", "Debt/Eq"]
    prof_cols = ["ROE", "ROA", "Net Margin", "Rev Growth", "Div Yield"]
    
    # Transpose so Columns=Tickers, Rows=Metrics
    df_T = df.T
    
    def color_scale(row):
        # row is a Series of values for one metric across all tickers
        # Return list of 'background-color: ...'
        
        styles = []
        is_val = row.name in val_cols
        is_prof = row.name in prof_cols
        
        if not is_val and not is_prof:
            return ['' for _ in row]
            
        # Convert to float
        nums = pd.to_numeric(row, errors='coerce')
        if nums.dropna().empty:
            return ['' for _ in row]
            
        # Rank: 0=worst, 1=best
        if is_val:
            # Lower is better. Rank ascending (min=1)
            # We want best to be Green. 
            # If we map 0->Red, 1->Green.
            # Ascending rank: min val gets rank 1. Max val gets rank N.
            # We want Min to be Green.
            ranks = nums.rank(ascending=False) 
            # Smallest value -> Rank N (Highest rank) -> Green?
            # No. Rank(ascending=True): Smallest -> 1. Largest -> N.
            # We want Smallest -> Green (1). Largest -> Red (0).
            # So normalize rank such that Smallest is 1.0, Largest is 0.0?
            
            # Let's use percentile rank.
            # pct=True results in [0..1].
            # ascending=False: Largest is 1.0, Smallest is 0.0.
            # We want Smallest to be Green.
            # So use ascending=False (Smallest is 0.0?) No.
            # ascending=False: Smallest is 0 (approx). Largest is 1.
            # We want Smallest=Green, Largest=Red.
            pcts = nums.rank(ascending=False, pct=True) 
            # Smallest P/E gets rank ~1.0? 
            # NO. asc=False means Large numbers get Low rank (1), Small numbers get High rank (N).
            # wait. rank(ascending=False):
            # [10, 20, 30]. asc=False -> [3, 2, 1].
            # 10 is Rank 3. 30 is Rank 1.
            # We want 10 (Smallest) to be Green.
            # So higher rank number = Green.
            # So yes, ascending=False works.
            
        else: # Profitability
            # Higher is better.
            # We want Largest to be Green.
            # [10, 20, 30]. We want 30 to be Green (High rank).
            # rank(ascending=True) -> [1, 2, 3]. 30 is Rank 3.
            pcts = nums.rank(ascending=True, pct=True)
            
        # Map pct (0..1) to Color
        # 0 = Red (hsl 0), 1 = Green (hsl 120)
        for val, pct in zip(row, pcts):
            if pd.isna(val):
                styles.append('')
            else:
                # pct is between 0 and 1 (roughly)
                hue = int(pct * 120)
                styles.append(f'background-color: hsla({hue}, 60%, 20%, 0.8); color: white')
                
        return styles

    # Format numbers for display
    def format_row(x):
        try:
            val = float(x)
            if pd.isna(val): return "-"
            if abs(val) > 1e9: return f"{val/1e9:.1f}B" # For market cap
            if abs(val) > 1e6 and abs(val) < 1e9: return f"{val/1e6:.1f}M"
           
            # Identify row by context? Hard in 'applymap'.
            # Just do generic formatting
            if abs(val) < 1 and abs(val) > 0.0001: 
                # Likely percentage (except Beta etc)
                # But P/E can be < 1? No.
                # Yield, Margins are < 1.
                # Let's assume passed data is raw.
                return f"{val:.2f}"
            return f"{val:.1f}"
        except:
            return x

    # 4. Render Table
    st.markdown("###  Valuation & Profitability Matrix")
    st.dataframe(df_T.style.apply(color_scale, axis=1).format("{:.2f}"), use_container_width=True)
    
    # 5. Radar Chart
    st.markdown("### ️ Relative Strength Radar")
    
    # Normalize metrics 0-1 for radar
    # Must inverse valuation metrics
    radar_metrics = ["P/E", "P/B", "ROE", "Net Margin", "Rev Growth", "Div Yield"]
    
    # Filter rows that exist
    rows_to_use = [m for m in radar_metrics if m in df_T.index]
    
    if rows_to_use:
        subset = df_T.loc[rows_to_use].apply(pd.to_numeric, errors='coerce')
        
        # Rank percentile (0-1)
        # For P/E, P/B: Lower is better -> Invert rank
        # For indices in [P/E, P/B]:
        #   rank(ascending=False, pct=True) -> Smallest gets 1.0 (Best)
        # For others:
        #   rank(ascending=True, pct=True) -> Largest gets 1.0 (Best)
        
        radar_data = subset.copy()
        
        for m in radar_data.index:
            if m in ["P/E", "P/B"]:
                radar_data.loc[m] = subset.loc[m].rank(ascending=False, pct=True)
            else:
                radar_data.loc[m] = subset.loc[m].rank(ascending=True, pct=True)
                
        # Fill NA with 0.5
        radar_data = radar_data.fillna(0.5)
        
        fig = go.Figure()
        
        # Main Ticker
        if ticker in radar_data.columns:
            fig.add_trace(go.Scatterpolar(
                r=radar_data[ticker].values,
                theta=radar_data.index,
                fill='toself',
                name=ticker,
                line_color='#00ff88'
            ))
            
        # Median of peers
        peers = [c for c in radar_data.columns if c != ticker]
        if peers:
            median_vals = radar_data[peers].median(axis=1)
            fig.add_trace(go.Scatterpolar(
                r=median_vals.values,
                theta=radar_data.index,
                fill='toself',
                name='Peer Median',
                line_color='rgba(150, 150, 150, 0.5)',
                line_dash='dash'
            ))
            
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
            showlegend=True,
            template="plotly_dark",
            height=400,
            title="Relative Percentile Rank (Outer = Best)"
        )
        st.plotly_chart(fig, use_container_width=True)
