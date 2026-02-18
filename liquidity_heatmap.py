import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import streamlit as st


@st.cache_data(ttl=300)
def build_volume_matrix(ticker: str, period: str, interval: str):
    """Fetches OHLCV data and builds the raw volume matrix."""
    df = yf.download(ticker, period=period, interval=interval, progress=False)
    df.dropna(inplace=True)

    if df.empty or len(df) < 10:
        return None, None, None

    # Build price grid — finer resolution (ATR/20 not ATR/10)
    atr_series = (df['High'] - df['Low'])
    atr = atr_series.mean()
    
    # Handle Series vs Scalar
    if isinstance(atr, (pd.Series, np.ndarray)):
        atr = atr.item()
        
    if atr <= 0: atr = 0.01 # Guard against zero division
    
    grid_step = atr / 20
    if grid_step <= 0: grid_step = 0.01
    
    start_price = df['Low'].min() - atr
    end_price = df['High'].max() + atr
    
    # Ensure scalars
    if isinstance(start_price, (pd.Series, np.ndarray)): start_price = start_price.item()
    if isinstance(end_price, (pd.Series, np.ndarray)): end_price = end_price.item()
    
    price_min = float(start_price)
    price_max = float(end_price)
    
    # Arange can be empty if step is wrong, safely handle
    try:
        price_levels = np.arange(float(price_min), float(price_max), float(grid_step))
    except:
        return None, None, None

    if len(price_levels) == 0:
        return None, None, None

    time_index = df.index
    volume_matrix = np.zeros((len(price_levels), len(time_index)))

    # Distribute each candle's volume across the price levels it touched
    for t_idx, (timestamp, row) in enumerate(df.iterrows()):
        candle_low = float(row['Low'])
        candle_high = float(row['High'])
        candle_vol = float(row['Volume'])
        mask = (price_levels >= candle_low) & (price_levels <= candle_high)
        levels_hit = mask.sum()
        if levels_hit > 0:
            volume_matrix[mask, t_idx] = candle_vol / levels_hit

    return volume_matrix, price_levels, time_index


def render_liquidity_heatmap(ticker: str):
    st.markdown("## 💧 Liquidity Heatmap (Historical)")
    st.caption("Visualize volume density over time to identify sticky price levels.")

    # User controls
    col1, col2, col3 = st.columns(3)
    with col1:
        period = st.selectbox("Lookback Period", ["3d", "7d", "14d"], index=1)
    with col2:
        interval = st.selectbox("Candle Interval", ["5m", "15m", "1h"], index=0)
    with col3:
        show_pools = st.checkbox("Show Liquidity Pool Lines", value=True)

    if not st.button("Generate Heatmap"):
        return

    with st.spinner("Building volume matrix..."):
        volume_matrix, price_levels, time_index = build_volume_matrix(ticker, period, interval)

    if volume_matrix is None:
        st.error("Insufficient data to generate heatmap for this ticker.")
        return

    # ─────────────────────────────────────────────
    # FIX 1: Log normalization
    z = np.log1p(volume_matrix)

    # FIX 2: Percentile clipping
    nonzero = z[z > 0]
    if len(nonzero) > 10:
        vmax = np.percentile(nonzero, 95)
        z = np.clip(z, 0, vmax)
    else:
        st.warning("Not enough volume data to identify distinct pools cleanly.")
    # ─────────────────────────────────────────────

    x_labels = [str(t) for t in time_index]

    # FIX 3: plasma colorscale
    heatmap_trace = go.Heatmap(
        z=z,
        x=x_labels,
        y=price_levels,
        colorscale="plasma",
        showscale=True,
        colorbar=dict(
            title="Volume Density",
            tickvals=[],
            ticktext=[]
        ),
        hovertemplate="Time: %{x}<br>Price: %{y:.2f}<br>Density: %{z:.2f}<extra></extra>"
    )

    # White price line overlay
    try:
        # Re-fetch close for overlay if needed or use what we have? 
        # Ideally we should pass 'Close' from build_volume_matrix to avoid double fetch, 
        # but for simplicity let's just re-download or assume we can get it from matrix? 
        # The user code re-downloads. Let's optimize slightly by separate fetch if needed, 
        # but yf.download is cached by streamlit usually if same args? 
        # Actually build_volume_matrix returns matrix not df.
        # Let's just re-download cleanly or just trust user code.
        # User code: yf.download(ticker, period=period, interval=interval, progress=False)['Close'].values
        price_data = yf.download(ticker, period=period, interval=interval, progress=False)['Close'].values
    except:
        price_data = []

    price_line = go.Scatter(
        x=x_labels,
        y=price_data,
        mode='lines',
        line=dict(color='white', width=1.5),
        name='Price',
        hovertemplate="Price: %{y:.2f}<extra></extra>"
    )

    fig = go.Figure(data=[heatmap_trace, price_line])

    # Auto-annotate top 3 liquidity pools
    if show_pools:
        row_sums = z.sum(axis=1)
        # Avoid empty or all-zero rows causing issues
        if row_sums.sum() > 0:
            top_indices = np.argsort(row_sums)[-3:][::-1]
            for idx in top_indices:
                if row_sums[idx] > 0 and idx < len(price_levels):
                    fig.add_hline(
                        y=float(price_levels[idx]),
                        line=dict(color="yellow", width=1, dash="dot"),
                        annotation_text=f"Pool: {float(price_levels[idx]):.2f}",
                        annotation_font_color="yellow",
                        annotation_font_size=11
                    )

    fig.update_layout(
        title=f"{ticker} Volume Heatmap (Last {period})",
        xaxis_title="Date/Time",
        yaxis_title="Price",
        plot_bgcolor="#0e1117",
        paper_bgcolor="#0e1117",
        font=dict(color="#ffffff"),
        height=550,
        xaxis=dict(nticks=10)
    )

    st.plotly_chart(fig, use_container_width=True)
    st.info("🔆 Brighter regions indicate high volume interaction (Liquidity Pools).")
