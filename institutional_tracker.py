import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

class InstitutionalTracker:
    def __init__(self, ticker):
        self.ticker = ticker
        
    def fetch_data(self):
        try:
            t = yf.Ticker(self.ticker)
            
            # major_holders: 0=%, 1=Description
            major = t.major_holders
            
            # institutional_holders: Holder, Shares, Date Reported, % Out, Value
            inst = t.institutional_holders
            
            # mutualfund_holders
            mf = t.mutualfund_holders
            
            return {
                "major": major,
                "institutional": inst,
                "mutual_fund": mf
            }
        except Exception as e:
            print(f"Error fetching holdings: {e}")
            return {}

def render_institutional_tracker(ticker: str):
    st.markdown("## ️ Institutional Ownership")
    st.caption("Breakdown of major holders, institutional funds, and mutual funds.")
    
    tracker = InstitutionalTracker(ticker)
    
    with st.spinner("Fetching ownership data..."):
        data = tracker.fetch_data()
        
    if not data or ((data['major'] is None or data['major'].empty) and 
                    (data['institutional'] is None or data['institutional'].empty)):
        st.info("No ownership data available.")
        return
        
    # --- Major Holders (Summary) ---
    major = data.get('major')
    
    if major is not None and not major.empty:
        # yfinance format varies. Sometimes it's a DataFrame with columns [0, 1]
        # 0: Value (e.g. 0.07%), 1: Description (e.g. % of Shares Held by All Insider)
        
        # Let's try to parse it into metrics or a Pie Chart
        try:
            # Rename columns if needed
            if 1 in major.columns:
                major = major.set_index(1)
            
            # Extract common metrics
            pass
        except:
            pass
        
        c1, c2 = st.columns([1, 2])
        
        with c1:
            st.subheader("Ownership Structure")
            st.dataframe(major, use_container_width=True, hide_index=True)
            
        with c2:
            # Try to visualize if we can parse percentages
            # For now, just show the table as it's often text-heavy
            pass
            
    st.divider()
    
    # --- Top Institutions ---
    st.subheader("Top Institutional Holders")
    inst = data.get('institutional')
    if inst is not None and not inst.empty:
        st.dataframe(inst, use_container_width=True, hide_index=True)
    else:
        st.info("No institutional holder data.")
        
    # --- Top Mutual Funds ---
    st.subheader("Top Mutual Funds")
    mf = data.get('mutual_fund')
    if mf is not None and not mf.empty:
        st.dataframe(mf, use_container_width=True, hide_index=True)
    else:
        st.info("No mutual fund data.")
