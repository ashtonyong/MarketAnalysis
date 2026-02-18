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
            st.markdown("#### Earnings Calendar")
            
            # Use shared data fetcher
            try:
                from components.earnings_data import EarningsData
                
                if st.button("Refresh Data", key='refresh_earnings_main'):
                    st.cache_data.clear()
                
                # Fetch data
                with st.spinner("Scanning market for earnings..."):
                    df = EarningsData.fetch_upcoming_earnings(days_ahead=90)
                
                if df is not None and not df.empty:
                    # Format for Table (Image 1 style: Symbol | DateStr | EPS Est)
                    # We can rename columns to match user request "Symbol | Company | Event | EPS"
                    # We don't have Company Name easily without slow fetch, so we'll sticking to Symbol
                    
                    display_df = df[['Symbol', 'DateStr', 'EPS Est']].copy()
                    display_df.columns = ['Symbol', 'Date', 'EPS Est']
                    
                    st.dataframe(
                        display_df,
                        column_config={
                            "Symbol": st.column_config.TextColumn("Symbol", width="small"),
                            "Date": st.column_config.TextColumn("Date", width="medium"),
                            "EPS Est": st.column_config.TextColumn("EPS Est", width="small"),
                        },
                        hide_index=True,
                        use_container_width=True,
                        height=400
                    )
                else:
                    st.info("No upcoming earnings found in the next 90 days.")
                    
            except Exception as e:
                st.error(f"Could not fetch earnings: {e}")
