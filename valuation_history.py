import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from datetime import datetime, timedelta

class ValuationHistory:
    def __init__(self, ticker):
        self.ticker = ticker
        
    def fetch_data(self):
        try:
            t = yf.Ticker(self.ticker)
            
            # 1. Price History (5Y)
            prices = t.history(period="5y")
            if prices.empty: return pd.DataFrame()
            
            # Remove timezone from prices index to match financials
            prices.index = prices.index.tz_localize(None)
            
            # 2. Financials (Quarterly)
            # We need TTM EPS and TTM Revenue
            # financials/quarterly_financials
            
            # TTM Calculation: standard approach is sum of last 4 quarters
            
            q_fin = t.quarterly_financials
            if q_fin.empty:
                # Fallback to annual if quarterly not available?
                return pd.DataFrame()
                
            # Transpose so dates are index
            q_fin = q_fin.T
            q_fin.index = pd.to_datetime(q_fin.index)
            q_fin = q_fin.sort_index()
            
            # Identify columns
            # EPS: 'Basic EPS' or 'Diluted EPS'
            # Rev: 'Total Revenue'
            
            eps_col = next((c for c in q_fin.columns if 'Diluted EPS' in c or 'Basic EPS' in c), None)
            rev_col = next((c for c in q_fin.columns if 'Total Revenue' in c), None)
            shares_col = next((c for c in q_fin.columns if 'Diluted Average Shares' in c or 'Basic Average Shares' in c), None)
            
            if not eps_col or not rev_col:
                return pd.DataFrame()
                
            # Calculate TTM
            # Rolling sum of last 4 quarters
            q_fin['EPS_TTM'] = q_fin[eps_col].rolling(4).sum()
            q_fin['Rev_TTM'] = q_fin[rev_col].rolling(4).sum()
            
            # Calculate Revenue Per Share TTM
            # If we don't have shares count, we can't do P/S accurately per share, 
            # but we can do Market Cap / Total Revenue.
            # Let's stick to P/E first.
            
            # Merge with Price
            # We need to forward fill the financials to the daily price dates
            
            combined = pd.DataFrame(index=prices.index)
            combined['Close'] = prices['Close']
            
            # Reindex financials to match price index, forward fill
            # This applies the earnings of a quarter to all subsequent days until next report
            fin_reindexed = q_fin[['EPS_TTM', 'Rev_TTM']].reindex(combined.index, method='ffill')
            
            combined = combined.join(fin_reindexed)
            
            # Calculate Ratios
            combined['PE_Ratio'] = combined['Close'] / combined['EPS_TTM']
            
            # Handle negative P/E or outliers
            # combined['PE_Ratio'] = combined['PE_Ratio'].where(combined['EPS_TTM'] > 0)
            
            return combined.dropna()
            
        except Exception as e:
            print(f"Error valuation: {e}")
            return pd.DataFrame()

def render_valuation_history(ticker: str):
    st.markdown("## 📊 Valuation History (P/E Ratio)")
    st.caption("Historical Price-to-Earnings Ratio derived from 5-year price and quarterly earnings data.")
    
    vh = ValuationHistory(ticker)
    
    with st.spinner("Calculating historical valuation..."):
        df = vh.fetch_data()
        
    if df.empty:
        st.info("Insufficient financial data to calculate historical valuation.")
        return
        
    # --- Statistics ---
    current_pe = df['PE_Ratio'].iloc[-1]
    avg_pe_5y = df['PE_Ratio'].mean()
    min_pe_5y = df['PE_Ratio'].min()
    max_pe_5y = df['PE_Ratio'].max()
    
    # Deviation
    dev = (current_pe - avg_pe_5y) / avg_pe_5y * 100
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Current P/E", f"{current_pe:.2f}")
    c2.metric("5Y Average", f"{avg_pe_5y:.2f}")
    c3.metric("Premium/Discount", f"{dev:+.2f}%", 
             delta="Expensive" if dev > 20 else "Cheap" if dev < -20 else "Fair",
             delta_color="inverse")
    c4.metric("Range (Low-High)", f"{min_pe_5y:.1f} - {max_pe_5y:.1f}")
    
    st.divider()
    
    # --- Charts ---
    
    tab1, tab2 = st.tabs(["P/E History", "Price vs Fair Value"])
    
    with tab1:
        # Plot P/E over time
        fig_pe = go.Figure()
        fig_pe.add_trace(go.Scatter(
            x=df.index, y=df['PE_Ratio'],
            name='P/E Ratio',
            line=dict(color='cyan', width=2)
        ))
        
        # Add Average Line
        fig_pe.add_hline(y=avg_pe_5y, line_dash="dash", line_color="white", annotation_text="5Y Avg")
        
        fig_pe.update_layout(
            title="Historical P/E Ratio (TTM)",
            yaxis_title="P/E",
            template="plotly_dark",
            height=400
        )
        st.plotly_chart(fig_pe, use_container_width=True)
        
    with tab2:
        # Plot Price vs "Fair Value" (Price implied by 5Y Avg P/E)
        # Fair Value = EPS_TTM * Avg_PE
        
        df['Fair_Value'] = df['EPS_TTM'] * avg_pe_5y
        
        fig_fv = go.Figure()
        
        fig_fv.add_trace(go.Scatter(
            x=df.index, y=df['Close'],
            name='Actual Price',
            line=dict(color='white', width=2)
        ))
        
        fig_fv.add_trace(go.Scatter(
            x=df.index, y=df['Fair_Value'],
            name=f'Implied Price (@ {avg_pe_5y:.1f}x P/E)',
            line=dict(color='orange', width=2, dash='dot')
        ))
        
        fig_fv.update_layout(
            title="Price vs. Mean Valuation",
            yaxis_title="Price ($)",
            template="plotly_dark",
            height=400
        )
        st.plotly_chart(fig_fv, use_container_width=True)
