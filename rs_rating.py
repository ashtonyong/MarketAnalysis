import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import streamlit as st

class RSRating:
    def __init__(self, ticker, benchmark="SPY"):
        self.ticker = ticker
        self.benchmark = benchmark
        
    def fetch_data(self, period="1y"):
        try:
            tickers = f"{self.ticker} {self.benchmark}"
            df = yf.download(tickers, period=period, group_by='ticker', progress=False)
            
            # Extract Close prices
            # Structure might be MultiIndex (Ticker, OHLCV)
            # We need Close columns for both
            
            data = pd.DataFrame()
            data[self.ticker] = df[self.ticker]['Close']
            data[self.benchmark] = df[self.benchmark]['Close']
            
            return data.dropna()
        except Exception as e:
            print(f"Error fetching RS data: {e}")
            return pd.DataFrame()
            
    def calculate_rating(self):
        """
        Calculate RS Rating based on IBD-style methodology (simplified).
        Weighted average of performance:
        - 3 Month: 40%
        - 6 Month: 20%
        - 9 Month: 20%
        - 12 Month: 20%
        """
        df = self.fetch_data(period="2y") # Fetch enough for calculations
        if df.empty: return 0, df
        
        # Calculate price changes over specific periods
        # We need current price vs price N months ago
        
        current_price = df.iloc[-1]
        
        # Approx trading days: 
        # 3m = 63 days
        # 6m = 126 days
        # 9m = 189 days
        # 12m = 252 days
        
        periods = {
            "3m": 63,
            "6m": 126,
            "9m": 189,
            "12m": 252
        }
        
        scores = {}
        
        for p_name, p_days in periods.items():
            if len(df) > p_days:
                past_price = df.iloc[-(p_days+1)]
                pct_change = (current_price - past_price) / past_price * 100
                scores[p_name] = pct_change[self.ticker]
            else:
                scores[p_name] = 0
                
        # Weighted Score Calculation
        # Weights: 3m (40%), 6m (20%), 9m (20%), 12m (20%)
        # Modified slightly to prioritize recent momentum
        
        weighted_perf = (
            scores["3m"] * 0.4 +
            scores["6m"] * 0.2 +
            scores["9m"] * 0.2 +
            scores["12m"] * 0.2
        )
        
        # To convert this raw performance % into a 1-99 rating, 
        # normally you'd compare against the entire market database.
        # Since we don't have that, we'll use a dynamic scaling based on the Benchmark.
        
        # Benchmark perf for comparison
        bm_perf = 0
        for p_name, p_days in periods.items():
             if len(df) > p_days:
                past_price = df.iloc[-(p_days+1)]
                pct_change = (current_price - past_price) / past_price * 100
                if p_name == "3m": bm_perf += pct_change[self.benchmark] * 0.4
                else: bm_perf += pct_change[self.benchmark] * 0.2
                
        # Relative Performance Ratio
        # If Stock > Benchmark, Rating > 50
        # Scaling factor: assume standard deviation of performance is ~20%
        
        outperformance = weighted_perf - bm_perf
        
        # Sigmoid-like scaling centered at 50
        # +50% outperformance -> ~90
        # -50% underperformance -> ~10
        
        rating = 50 + (outperformance * 1.5)
        rating = max(1, min(99, rating))
        
        # Calculate RS Line (Ratio of Stock / Benchmark)
        df['RS_Line'] = df[self.ticker] / df[self.benchmark]
        # Normalize to start at 100 for better plotting? Or just use raw ratio
        df['RS_Line_Norm'] = df['RS_Line'] / df['RS_Line'].iloc[0] * 100
        
        return int(rating), df, scores

def render_rs_rating(ticker: str):
    st.markdown(f"## 🚀 Relative Strength (RS) Rating: {ticker}")
    st.caption("Technical rating comparing price performance against the S&P 500 (SPY).")
    
    rs = RSRating(ticker)
    
    with st.spinner("Calculating RS Rating..."):
        rating, df, scores = rs.calculate_rating()
        
    if df.empty:
        st.error("Could not fetch data.")
        return
        
    # --- Metrics ---
    c1, c2, c3 = st.columns([1, 1, 2])
    
    color = "green" if rating >= 80 else "blue" if rating >= 50 else "red"
    
    c1.markdown(f"""
    <div style="text-align: center; border: 2px solid {color}; padding: 10px; border-radius: 10px;">
        <h3 style="margin:0; color:gray;">RS Rating</h3>
        <h1 style="margin:0; font-size: 56px; color:{color};">{rating}</h1>
    </div>
    """, unsafe_allow_html=True)
    
    c2.metric("3 Months", f"{scores.get('3m', 0):.2f}%")
    c2.metric("6 Months", f"{scores.get('6m', 0):.2f}%")
    c2.metric("12 Months", f"{scores.get('12m', 0):.2f}%")
    
    with c3:
        st.info("""
        **Interpretation**:
        *   **80-99 (Leading)**: Outperforming significantly. Leaders usually have RS > 80.
        *   **50-79 (Market Perform)**: Performing in-line or slightly better.
        *   **1-49 (Lagging)**: Underperforming the broad market.
        """)
    
    st.divider()
    
    # --- RS Line Chart ---
    # Plot Stock Price vs RS Line
    
    fig = go.Figure()
    
    # Stock Price (Candlestick or Line) - Let's use Normalized Comparison
    # Normalize both to 100 at start
    norm_stock = df[ticker] / df[ticker].iloc[0] * 100
    norm_spy = df['SPY'] / df['SPY'].iloc[0] * 100
    
    fig.add_trace(go.Scatter(
        x=df.index, y=norm_stock,
        name=ticker,
        line=dict(color='cyan', width=2)
    ))
    
    fig.add_trace(go.Scatter(
        x=df.index, y=norm_spy,
        name='S&P 500 (SPY)',
        line=dict(color='gray', width=2, dash='dot')
    ))
    
    # RS Line (Secondary Y?)
    # Actually, showing RS Line is better than comparing price actions sometimes
    # RS Line = Ticker / SPY
    # Let's add RS Line on secondary axis
    
    fig.add_trace(go.Scatter(
        x=df.index, y=df['RS_Line'],
        name='RS Line (Ratio)',
        line=dict(color='magenta', width=2),
        yaxis='y2'
    ))
    
    fig.update_layout(
        title="Relative Strength Line & Performance",
        yaxis=dict(title="Normalized Price (Start=100)"),
        yaxis2=dict(
            title="RS Ratio",
            overlaying='y',
            side='right',
            showgrid=False
        ),
        template='plotly_dark',
        height=500,
        legend=dict(orientation="h", y=1.02, x=0.5, xanchor="center")
    )
    
    st.plotly_chart(fig, use_container_width=True)
