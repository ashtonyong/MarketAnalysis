import streamlit as st
import pandas as pd
import numpy as np
import time
from quant_engine import ZScoreCalculator, RegimeDetector, SetupScorer
from volume_profile_engine import VolumeProfileEngine

class SetupScanner:
    def __init__(self, tickers: list):
        self.tickers = tickers
        self.z_calc = ZScoreCalculator()
        self.regime_det = RegimeDetector()
        self.scorer = SetupScorer()
        
    def scan(self, progress_bar=None) -> pd.DataFrame:
        results = []
        
        total = len(self.tickers)
        for i, ticker in enumerate(self.tickers):
            if progress_bar:
                progress_bar.progress((i + 1) / total, text=f"Scanning {ticker}...")
            
            try:
                # 1. Fetch Data (1 Month, 1 Hour)
                engine = VolumeProfileEngine(ticker, period="1mo", interval="1h")
                df = engine.fetch_data()
                
                if df.empty or len(df) < 50:
                    continue
                    
                # 2. Calculate Profile & Levels
                vp = engine.calculate_volume_profile()
                poc = engine.find_poc(vp)
                vah, val = engine.find_value_area(vp)
                
                current_price = df['Close'].iloc[-1]
                
                # 3. Calculate Derivatives
                # pct from poc
                if poc > 0:
                    dist_poc_pct = (current_price - poc) / poc * 100
                else:
                    dist_poc_pct = 999
                    
                # Position
                if current_price > vah:
                    pos = "ABOVE VA"
                elif current_price < val:
                    pos = "BELOW VA"
                else:
                    pos = "INSIDE VA"
                    
                # Volume Ratio
                avg_vol = df['Volume'].rolling(20).mean().iloc[-1]
                curr_vol = df['Volume'].iloc[-1]
                vol_ratio = curr_vol / avg_vol if avg_vol > 0 else 0
                
                # 4. Quant Metrics
                z_res = self.z_calc.calculate(df, poc)
                reg_res = self.regime_det.detect(df)
                
                # 5. Score
                ticker_data = {
                    'distance_from_poc_pct': dist_poc_pct,
                    'position': pos,
                    'volume_ratio': vol_ratio,
                    'z_score': z_res.get('current_z_score', 0),
                    'regime': reg_res.get('regime', 'UNKNOWN'),
                    'patterns': {} # Placeholder for now
                }
                
                score_res = self.scorer.score_setup(ticker_data)
                
                results.append({
                    "Ticker": ticker,
                    "Score": score_res['total_score'],
                    "Grade": score_res['grade'],
                    "Action": score_res['action'],
                    "Price": current_price,
                    "Regime": reg_res.get('regime', 'N/A'),
                    "Position": pos,
                    "Z-Score": z_res.get('current_z_score', 0),
                    "POC Dist %": round(dist_poc_pct, 2),
                    "Upside": score_res['recommendation']
                })
                
            except Exception as e:
                print(f"Error scanning {ticker}: {e}")
                continue
                
        return pd.DataFrame(results).sort_values("Score", ascending=False)

def render_setup_scanner(default_tickers: list):
    st.markdown("## ️ Multi-Ticker Setup Scanner")
    st.caption("Scans watchlists for high-probability setups using the Quant Engine scoring model.")
    
    # Input
    with st.expander("Scanner Settings", expanded=True):
        raw_input = st.text_area("Tickers to Scan (comma separated)", 
                                 value=", ".join(default_tickers),
                                 height=70)
        
        col1, col2 = st.columns([1, 4])
        scan_btn = col1.button("Run Scanner", type="primary", use_container_width=True)
    
    if scan_btn:
        tickers = [t.strip().upper() for t in raw_input.split(",") if t.strip()]
        
        scanner = SetupScanner(tickers)
        prog_bar = st.progress(0, text="Initializing scanner...")
        
        results_df = scanner.scan(prog_bar)
        prog_bar.empty()
        
        if results_df.empty:
            st.warning("No results found. Please checked the tickers or try again.")
            return
            
        # Display Best Setups (Score >= 70)
        best = results_df[results_df['Score'] >= 70]
        if not best.empty:
            st.success(f"Found {len(best)} High-Quality Setups!")
            st.dataframe(best, use_container_width=True, hide_index=True)
        else:
            st.info("No 'A' Grade setups found right now.")
            
        st.markdown("### Full Results")
        
        # Color styling for Score
        # We can use Pandas Styler or just display raw
        # Using st.dataframe column config for bars
        st.dataframe(
            results_df,
            column_config={
                "Score": st.column_config.ProgressColumn(
                    "Score",
                    help="Quant Score (0-100)",
                    format="%d",
                    min_value=0,
                    max_value=100,
                ),
                "Price": st.column_config.NumberColumn(format="$%.2f"),
                "Z-Score": st.column_config.NumberColumn(format="%.2f"),
                "POC Dist %": st.column_config.NumberColumn(format="%.2f%%"),
            },
            use_container_width=True,
            hide_index=True
        )
