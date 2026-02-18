import streamlit as st
import streamlit.components.v1 as components

class EventsWidgets:
    
    @staticmethod
    def render_detailed_calendar():
        """Render the wide economic calendar at the top of Home Tab."""
        st.markdown("### 🗓️ Economic Calendar")
        html = """
        <div class="tradingview-widget-container">
          <div class="tradingview-widget-container__widget"></div>
          <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-events.js" async>
          {
          "colorTheme": "dark",
          "isTransparent": true,
          "width": "100%",
          "height": "450",
          "locale": "en",
          "importanceFilter": "0,1",
          "countryFilter": "us,eu,gb,jp,cn"
        }
          </script>
        </div>
        """
        components.html(html, height=470)

    @staticmethod
    def render_market_overview_events():
        """Render the compact events and earnings seen in the second reference image."""
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Top Economic Events")
            html_eco = """
            <div class="tradingview-widget-container">
              <div class="tradingview-widget-container__widget"></div>
              <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-hotlists.js" async>
              {
              "colorTheme": "dark",
              "dateRange": "12M",
              "exchange": "US",
              "showChart": true,
              "locale": "en",
              "width": "100%",
              "height": "400",
              "largeChartUrl": "",
              "isTransparent": true,
              "showSymbolLogo": true,
              "showFloatingTooltip": false,
              "plotLineColorGrowing": "rgba(41, 98, 255, 1)",
              "plotLineColorFalling": "rgba(41, 98, 255, 1)",
              "gridLineColor": "rgba(240, 243, 250, 0)",
              "scaleFontColor": "rgba(106, 109, 120, 1)",
              "belowLineFillColorGrowing": "rgba(41, 98, 255, 0.12)",
              "belowLineFillColorFalling": "rgba(41, 98, 255, 0.12)",
              "belowLineFillColorGrowingBottom": "rgba(41, 98, 255, 0)",
              "belowLineFillColorFallingBottom": "rgba(41, 98, 255, 0)",
              "symbolActiveColor": "rgba(41, 98, 255, 0.12)"
            }
              </script>
            </div>
            """
            # Wait, the second image "Top economic events" look like the 'Economic Calendar' but compact.
            # I'll use the 'Market Overview' themed widget if available, or just the Calendar widget again with different importance filters.
            
            html_eco_compact = """
            <div class="tradingview-widget-container">
              <div class="tradingview-widget-container__widget"></div>
              <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-events.js" async>
              {
              "colorTheme": "dark",
              "isTransparent": true,
              "width": "100%",
              "height": "400",
              "locale": "en",
              "importanceFilter": "1",
              "currencyFilter": "USD"
            }
              </script>
            </div>
            """
            components.html(html_eco_compact, height=420)

        with col2:
            st.markdown("#### Earnings Events")
            st.markdown("#### 📅 Earnings Calendar")
            
            # 1. Get Tickers (Watchlist + Magn. 7)
            watchlist = st.session_state.get('watchlist', ['SPY', 'QQQ', 'IWM'])
            major_tech = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA']
            all_tickers = list(set(watchlist + major_tech))
            
            if st.button("Refresh Earnings Data", key='refresh_earnings'):
                st.cache_data.clear()
                
            try:
                import yfinance as yf
                import pandas as pd
                from datetime import datetime, timedelta
                
                upcoming_earnings = []
                today = datetime.now()
                
                # Fetch data
                progress_text = "Scanning for earnings..."
                my_bar = st.progress(0, text=progress_text)
                
                for i, ticker in enumerate(all_tickers):
                    try:
                        t = yf.Ticker(ticker)
                        cal = t.calendar
                        
                        # Handle different yfinance versions/outputs
                        if cal is not None and not cal.empty:
                            # Calendar keys can vary. Usually 0 is Earnings Date or 'Earnings Date'
                            # Transpose if needed
                            if isinstance(cal, pd.DataFrame):
                                # If columns are integers (old yfinance), transposing might be needed
                                # New yfinance returns a Dictionary or DataFrame with dates
                                
                                # Let's try to find the 'Earnings Date'
                                ern_dates = cal.get('Earnings Date')
                                if ern_dates is None:
                                    # Fallback for some versions
                                    ern_dates = cal.iloc[0] if not cal.empty else None
                                    
                                if ern_dates is not None:
                                    # Get next earnings date
                                    # If list, take first. If series, take values.
                                    next_date = None
                                    if isinstance(ern_dates, list):
                                        next_date = ern_dates[0]
                                    elif isinstance(ern_dates, (pd.Timestamp, datetime)):
                                        next_date = ern_dates
                                    elif hasattr(ern_dates, 'values'): 
                                        next_date = ern_dates.values[0]
                                    
                                    if next_date:
                                        # Normalize to datetime
                                        nd = pd.to_datetime(next_date)
                                        
                                        # Only show future or very recent
                                        days_diff = (nd - today).days
                                        if -5 <= days_diff <= 90: # Show recent past (5 days) and next 3 months
                                            # Estimate logic
                                            est = cal.get('Earnings Average')
                                            if est is None:
                                                est = cal.get('EPS Estimate', [None])[0] if 'EPS Estimate' in cal else "N/A"
                                            
                                            upcoming_earnings.append({
                                                "Ticker": ticker,
                                                "Date": nd.strftime('%Y-%m-%d'),
                                                "Days Left": days_diff,
                                                "Estimate": est
                                            })
                    except Exception:
                        continue
                    
                    # Update progress
                    my_bar.progress((i + 1) / len(all_tickers), text=f"Checking {ticker}...")
                
                my_bar.empty()
                
                if upcoming_earnings:
                    # Sort by Date
                    df_earn = pd.DataFrame(upcoming_earnings)
                    df_earn = df_earn.sort_values('Days Left')
                    
                    st.dataframe(
                        df_earn,
                        column_config={
                            "Ticker": st.column_config.TextColumn("Ticker", width="small"),
                            "Date": st.column_config.DateColumn("Date", format="YYYY-MM-DD"),
                            "Days Left": st.column_config.NumberColumn("Days", format="%d ⏳"),
                            "Estimate": "EPS Est."
                        },
                        hide_index=True,
                        use_container_width=True
                    )
                else:
                    st.info("No upcoming earnings found for your watchlist in the next 90 days.")
                    
            except Exception as e:
                st.error(f"Could not fetch earnings: {e}")
                st.caption("Try refreshing or checking your internet connection.")
