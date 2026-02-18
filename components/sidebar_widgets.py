import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import streamlit.components.v1 as components

class SidebarWidgets:
    
    TICKERS = {
        'S&P Futures': 'ES=F',
        'Nasdaq Futures': 'NQ=F',
        'Dow Futures': 'YM=F',
        'Russell 2000': 'RTY=F',
        'VIX': '^VIX',
        'Gold': 'GC=F'
    }

    TRENDING_LIST = ['NVDA', 'TSLA', 'AAPL', 'AMD', 'PLTR', 'COIN', 'MARA', 'SOFI', 'AMZN', 'GOOGL']

    @staticmethod
    @st.cache_data(ttl=60)
    def fetch_indices_data():
        """Fetch data for indices widget."""
        data = {}
        for name, ticker in SidebarWidgets.TICKERS.items():
            try:
                t = yf.Ticker(ticker)
                # Try fast_info
                info = t.fast_info
                price = info.last_price
                prev = info.previous_close
                
                # Fetch history for sparkline
                hist = t.history(period='5d', interval='1h')
                
                if price and prev:
                    change = price - prev
                    pct = (change / prev) * 100
                    
                    data[name] = {
                        'price': price,
                        'change': change,
                        'pct': pct,
                        'history': hist['Close'].tolist() if not hist.empty else []
                    }
            except Exception:
                pass
        return data

    @staticmethod
    @st.cache_data(ttl=60)
    def fetch_trending_data():
        """Fetch data for trending list."""
        data = []
        for ticker in SidebarWidgets.TRENDING_LIST:
            try:
                t = yf.Ticker(ticker)
                info = t.fast_info
                price = info.last_price
                prev = info.previous_close
                if price and prev:
                    pct = (price - prev) / prev * 100
                    data.append({
                        'Ticker': ticker,
                        'Price': price,
                        'Change': pct
                    })
            except:
                pass
        # Sort by absolute change (most active movers)
        return sorted(data, key=lambda x: abs(x['Change']), reverse=True)[:5] 

    @staticmethod
    def render_indices():
        with st.sidebar:
            st.markdown("### Market Overview")
            data = SidebarWidgets.fetch_indices_data()
            
            # Grid layout
            cols = st.columns(2)
            idx_names = list(data.keys())
            
            for i, name in enumerate(idx_names):
                if name in data:
                    d = data[name]
                    col = cols[i % 2]
                    with col:
                        color = "#238636" if d['change'] >= 0 else "#da3633"
                        st.markdown(f"""
                        <div style="background-color: #0e1117; border: 1px solid #30363d; border-radius: 6px; padding: 8px; margin-bottom: 8px;">
                            <div style="font-size: 10px; color: #8b949e; font-weight: 600;">{name}</div>
                            <div style="font-size: 14px; font-weight: bold;">{d['price']:,.2f}</div>
                            <div style="font-size: 11px; color: {color};">
                                 {d['change']:+.2f} ({d['pct']:+.2f}%)
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        if d['history']:
                            fig = go.Figure(go.Scatter(y=d['history'], mode='lines', line=dict(color=color, width=1)))
                            fig.update_layout(
                                height=30, margin=dict(l=0,r=0,t=0,b=0),
                                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                                xaxis=dict(visible=False), yaxis=dict(visible=False)
                            )
                            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                        
            st.markdown("---")

    @staticmethod
    def render_trending():
        with st.sidebar:
            st.markdown("### Trending Tickers")
            data = SidebarWidgets.fetch_trending_data()
            
            for item in data:
                color = "#238636" if item['Change'] >= 0 else "#da3633"
                st.markdown(f"""
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px;">
                    <span style="font-weight: bold; font-size: 13px;">{item['Ticker']}</span>
                    <span style="font-size: 13px;">${item['Price']:.2f}</span>
                    <span style="color: {color}; font-size: 12px; background: rgba({35 if item['Change']>=0 else 218}, {134 if item['Change']>=0 else 54}, {54 if item['Change']>=0 else 51}, 0.2); padding: 2px 4px; border-radius: 4px;">
                        {item['Change']:+.2f}%
                    </span>
                </div>
                """, unsafe_allow_html=True)
                
            st.markdown("---")

    @staticmethod
    def render_compact_events():
        with st.sidebar:
            col_h, col_a = st.columns([6, 1])
            col_h.markdown("### Economic Events")
            if col_a.button(">", key="nav_eco_mini"):
                 st.components.v1.html("""
                    <script>
                    const tabs = window.parent.document.querySelectorAll('button[data-baseweb="tab"]');
                    if (tabs.length > 2) tabs[2].click();
                    </script>
                """, height=0)

            html = """
            <div class="tradingview-widget-container">
              <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-events.js" async>
              {
              "colorTheme": "dark",
              "isTransparent": true,
              "width": "100%",
              "height": "400",
              "locale": "en",
              "importanceFilter": "0,1,2"
            }
              </script>
            </div>
            """
            components.html(html, height=410)
            st.markdown("---")

    @staticmethod
    def render_compact_earnings():
        with st.sidebar:
            col_h, col_a = st.columns([6, 1])
            col_h.markdown("### 📅 Earnings")
            if col_a.button(">", key="nav_earn_mini"):
                 st.components.v1.html("""
                    <script>
                    const tabs = window.parent.document.querySelectorAll('button[data-baseweb="tab"]');
                    if (tabs.length > 2) tabs[2].click();
                    </script>
                """, height=0)

            # 1. Get Tickers (Watchlist + Magn. 7)
            watchlist = st.session_state.get('watchlist', ['SPY', 'QQQ', 'IWM'])
            major_tech = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA']
            all_tickers = list(set(watchlist + major_tech))
            
            try:
                import yfinance as yf
                from datetime import datetime
                
                upcoming_earnings = []
                today = datetime.now()
                
                # Fetch data (simplified for sidebar speed)
                for ticker in all_tickers:
                    try:
                        t = yf.Ticker(ticker)
                        # Quick check on calendar
                        cal = t.calendar
                        if cal is not None and not cal.empty:
                            ern_dates = cal.get('Earnings Date')
                            if ern_dates is None:
                                ern_dates = cal.iloc[0] if not cal.empty else None
                                
                            if ern_dates is not None:
                                next_date = None
                                if isinstance(ern_dates, list): next_date = ern_dates[0]
                                elif hasattr(ern_dates, 'values'): next_date = ern_dates.values[0]
                                else: next_date = ern_dates
                                
                                if next_date:
                                    nd = pd.to_datetime(next_date)
                                    days_diff = (nd - today).days
                                    
                                    if 0 <= days_diff <= 30: # Only next 30 days for sidebar
                                        est = cal.get('Earnings Average')
                                        if est is None: 
                                            est = cal.get('EPS Estimate', [None])[0] if 'EPS Estimate' in cal else None
                                        
                                        upcoming_earnings.append({
                                            "Ticker": ticker,
                                            "Day": nd.strftime('%m-%d'),
                                            "Days": days_diff
                                        })
                    except:
                        continue
                
                if upcoming_earnings:
                    # Sort by soonest
                    upcoming_earnings.sort(key=lambda x: x['Days'])
                    
                    for item in upcoming_earnings[:5]: # Show top 5
                        color = "#e6edf3" if item['Days'] > 3 else "#d29922" # Yellow if within 3 days
                        st.markdown(f"""
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px; font-size: 13px;">
                            <span style="font-weight: 600;">{item['Ticker']}</span>
                            <span style="color: #8b949e;">{item['Day']}</span>
                            <span style="color: {color}; font-size: 11px; background: rgba(56,139,253,0.1); padding: 1px 6px; border-radius: 10px;">
                                {item['Days']}d
                            </span>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.caption("No earnings in next 30 days.")

            except Exception as e:
                st.caption("Earnings data unavailable")
            
            st.markdown("---")
