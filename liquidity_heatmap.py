import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go

@st.cache_data(ttl=3600)
def fetch_heatmap_data(ticker, days=7):
    """Fetch intraday data for heatmap."""
    try:
        # 1m data limited to 7 days by yfinance
        df = yf.download(ticker, period=f"{days}d", interval="1m", progress=False)
        if df.empty:
            # Fallback to 5m for longer if needed, but 7d is period limit for 1m
            df = yf.download(ticker, period="5d", interval="5m", progress=False)
            
        if df.empty: return pd.DataFrame()
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return pd.DataFrame()

def generate_heatmap_matrix(df, buckets=100):
    """Convert price data into a Time x Price volume matrix."""
    # We want to see how volume clusters at prices OVER TIME.
    # X-axis: Time (e.g. hourly or 30m blocks)
    # Y-axis: Price
    # Z-axis: Volume
    
    # Resample to 30m blocks
    df['TimeBlock'] = df.index.floor('30min') 
    
    # Price Bucketing
    min_p = df['Low'].min()
    max_p = df['High'].max()
    price_range = max_p - min_p
    bucket_size = price_range / buckets
    
    # Assign each row to a price bucket
    # Use 'Close' price for volume attribution or spread volume across High-Low?
    # Simple: Attribution to Close price bucket. A bit imprecise but fast.
    # Better: Attribution to (High+Low)/2
    
    df['PriceBucket'] = ((df['Close'] - min_p) / bucket_size).astype(int)
    
    # Clip to max bucket
    df['PriceBucket'] = df['PriceBucket'].clip(0, buckets-1)
    
    # Group by TimeBlock and PriceBucket
    grouped = df.groupby(['TimeBlock', 'PriceBucket'])['Volume'].sum().reset_index()
    
    # Pivot
    heatmap_data = grouped.pivot(index='PriceBucket', columns='TimeBlock', values='Volume').fillna(0)
    
    # Convert PriceBucket index back to Price Levels
    price_levels = [min_p + i * bucket_size for i in heatmap_data.index]
    
    return heatmap_data, price_levels

def render_liquidity_heatmap(ticker):
    """Render the Liquidity Heatmap tab."""
    st.markdown("### 🗺️ Liquidity Heatmap (Historical)")
    st.caption("Visualize volume density over time to identify sticky price levels.")
    
    if st.button("Generate Heatmap", key="run_heatmap"):
        with st.spinner("Processing High-Freq Data..."):
            df = fetch_heatmap_data(ticker)
            
            if not df.empty:
                heatmap_matrix, price_levels = generate_heatmap_matrix(df)
                
                # Plot
                fig = go.Figure(data=go.Heatmap(
                    z=heatmap_matrix.values,
                    x=heatmap_matrix.columns,
                    y=price_levels,
                    colorscale='Viridis', # or 'Hot', 'Inferno'
                    colorbar=dict(title='Volume')
                ))
                
                # Overlay Price Line?
                # Resample price to match columns
                price_line = df['Close'].resample('30min').last().dropna()
                # Align X axis
                common_idx = heatmap_matrix.columns.intersection(price_line.index)
                
                fig.add_trace(go.Scatter(
                    x=common_idx,
                    y=price_line[common_idx],
                    mode='lines',
                    line=dict(color='white', width=1),
                    name='Price'
                ))
                
                fig.update_layout(
                    title=f"{ticker} Volume Heatmap (Last 7 Days)",
                    height=600,
                    template="plotly_dark",
                    xaxis_title="Date/Time",
                    yaxis_title="Price"
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                st.info("Brighter regions indicate high volume interaction (Liquidity Pools).")
                
            else:
                st.error("No intraday data found.")
