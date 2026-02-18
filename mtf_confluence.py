import streamlit as st
import pandas as pd
import numpy as np
from volume_profile_engine import VolumeProfileEngine

def check_alignment(p1, p2, tolerance=0.005):
    """Check if two prices are within tolerance % of each other."""
    if p1 == 0 or p2 == 0: return False
    avg = (p1 + p2) / 2
    diff = abs(p1 - p2)
    return (diff / avg) < tolerance

def get_confluence_score(daily, weekly, monthly):
    """
    Calculate confluence score for a specific level type (e.g. POC).
    Returns: Score (0-3), Alignment Details (str)
    """
    score = 0
    agreements = []
    
    # Check D-W
    if check_alignment(daily, weekly):
        score += 1
        agreements.append("D-W")
        
    # Check D-M
    if check_alignment(daily, monthly):
        score += 1
        agreements.append("D-M")
        
    # Check W-M
    if check_alignment(weekly, monthly):
        score += 1
        agreements.append("W-M")
        
    # Bonus for 3-way (if D-W and W-M, effectively D-W-M)
    if len(agreements) == 3:
        score = 3 # Max score logic (3 pairs)
        match_str = "Strong (D+W+M)"
    elif len(agreements) == 1:
        match_str = f"Weak ({agreements[0]})"
    elif len(agreements) == 2:
        # e.g. D-W and D-M but not W-M? Rare but possible if wide tolerance.
        match_str = "Moderate (2 TF)"
    else:
        match_str = "None"
        
    return score, match_str

def render_mtf_confluence(ticker):
    """Render the MTF Confluence Score tab."""
    st.markdown("### 🔀 Multi-Timeframe Confluence")
    st.caption("Analyzes Daily, Weekly, and Monthly Volume Profiles to find aligning levels.")
    
    if st.button("Run Confluence Analysis", key="run_mtf"):
        with st.spinner("Fetching Multi-Timeframe Data..."):
            try:
                # 1. Fetch Profiles
                # Daily
                e_d = VolumeProfileEngine(ticker, period="1mo", interval="30m") # Better intraday resolution for daily profile
                # Actually, for "Daily Profile" we usually mean "Profile of the last Day".
                # But typically MTF means "Profile of the Daily Chart", "Profile of Weekly Chart".
                # Let's align with the prompt: 
                # Daily: period="1d", interval="5m" (implies Intraday profile of TODAY?)
                # Weekly: period="5d", interval="30m" (implies Profile of WEEK?)
                # Monthly: period="1mo", interval="1d" (Profile of MONTH?)
                
                # The prompt says:
                # Daily: period="1d", interval="5m"
                # Weekly: period="5d", interval="30m"
                # Monthly: period="1mo", interval="1d" (? usually daily candles for monthly profile)
                
                # Let's follow prompt exactly for fetching.
                
                e_d = VolumeProfileEngine(ticker, period="5d", interval="15m") # Fetching enough data for "Daily"
                e_d.fetch_data()
                e_d.calculate_volume_profile()
                m_d = e_d.get_all_metrics()
                
                e_w = VolumeProfileEngine(ticker, period="1mo", interval="1h") # Fetching enough for "Weekly"
                e_w.fetch_data()
                e_w.calculate_volume_profile()
                m_w = e_w.get_all_metrics()
                
                e_m = VolumeProfileEngine(ticker, period="3mo", interval="1d") # Fetching enough for "Monthly"
                e_m.fetch_data()
                e_m.calculate_volume_profile()
                m_m = e_m.get_all_metrics()
                
                # Metric Table
                data = []
                total_score = 0
                
                levels = ['POC', 'VAH', 'VAL']
                
                for lvl in levels:
                    d_val = m_d[lvl.lower()]
                    w_val = m_w[lvl.lower()]
                    m_val = m_m[lvl.lower()]
                    
                    score, details = get_confluence_score(d_val, w_val, m_val)
                    total_score += score
                    
                    data.append({
                        "Level": lvl,
                        "Daily": f"${d_val:.2f}",
                        "Weekly": f"${w_val:.2f}",
                        "Monthly": f"${m_val:.2f}",
                        "Confluence": details,
                        "Score": score
                    })
                    
                df = pd.DataFrame(data)
                
                # Grading
                # Max score per level is 3. Total max is 9.
                grade = "F"
                color = "red"
                msg = "No significant confluence."
                
                if total_score >= 7:
                    grade = "A"
                    color = "green"
                    msg = "Excellent Setup! Strong alignment across timeframes."
                elif total_score >= 4:
                    grade = "B"
                    color = "orange"
                    msg = "Good Setup. Some levels align."
                elif total_score >= 2:
                    grade = "C"
                    color = "yellow"
                    msg = "Weak Setup. Minor alignment."
                else:
                    grade = "D"
                    color = "red"
                    msg = "Poor Setup. Markets are disjointed."
                    
                # Display
                c1, c2 = st.columns([1, 3])
                with c1:
                    st.metric("Confluence Grade", grade)
                    st.caption(msg)
                    st.progress(total_score / 9)
                    
                with c2:
                    st.dataframe(df, use_container_width=True, hide_index=True)
                    
            except Exception as e:
                st.error(f"Error calculating confluence: {e}")
