"""
TradingView Widget Integration
Embed professional TradingView charts in Streamlit (100% FREE)
No API key or paid subscription required.
"""

import streamlit.components.v1 as components


class TradingViewWidget:
    """Embed TradingView charts in Streamlit dashboards."""

    INTERVAL_MAP = {
        '1m': '1', '5m': '5', '15m': '15', '30m': '30',
        '1h': '60', '2h': '120', '4h': '240',
        '1d': 'D', '1w': 'W', '1mo': 'M'
    }

    @classmethod
    def render_chart(cls, symbol: str, interval: str = 'D', height: int = 600,
                     theme: str = 'dark', show_volume_profile: bool = False,
                     allow_symbol_change: bool = True):
        """
        Render a full TradingView advanced chart widget.

        Args:
            symbol: Ticker (SPY, XAUUSD, BTCUSD, EURUSD, etc.)
            interval: Timeframe (1m, 5m, 15m, 1h, 1d, etc.)
            height: Chart height in pixels
            theme: 'dark' or 'light'
            show_volume_profile: Show TradingView's built-in Volume Profile
            allow_symbol_change: Let user change symbol inside the chart
        """
        tv_interval = cls.INTERVAL_MAP.get(interval.lower(), interval)

        studies = ['"Volume@tv-basicstudies"']
        if show_volume_profile:
            studies.append('"VolumeProfile@tv-volumebyprice"')
        studies_str = "[" + ",".join(studies) + "]"

        html = f"""
<div class="tradingview-widget-container" style="height:100%;width:100%">
  <div class="tradingview-widget-container__widget" style="height:calc(100% - 32px);width:100%"></div>
  <script type="text/javascript"
    src="https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js" async>
  {{
    "autosize": true,
    "symbol": "{symbol}",
    "interval": "{tv_interval}",
    "timezone": "America/New_York",
    "theme": "{theme}",
    "style": "1",
    "locale": "en",
    "backgroundColor": "rgba(19, 23, 34, 1)",
    "gridColor": "rgba(42, 46, 57, 0.06)",
    "enable_publishing": false,
    "allow_symbol_change": {str(allow_symbol_change).lower()},
    "details": true,
    "hotlist": true,
    "calendar": false,
    "studies": {studies_str},
    "show_popup_button": true,
    "popup_width": "1000",
    "popup_height": "650",
    "support_host": "https://www.tradingview.com"
  }}
  </script>
</div>
"""
        components.html(html, height=height)

    @classmethod
    def render_symbol_info(cls, symbol: str):
        """Render a compact price ticker widget."""
        html = f"""
<div class="tradingview-widget-container">
  <div class="tradingview-widget-container__widget"></div>
  <script type="text/javascript"
    src="https://s3.tradingview.com/external-embedding/embed-widget-symbol-info.js" async>
  {{
    "symbol": "{symbol}",
    "width": "100%",
    "locale": "en",
    "colorTheme": "dark",
    "isTransparent": false
  }}
  </script>
</div>
"""
        components.html(html, height=120)

    @classmethod
    def render_mini_chart(cls, symbol: str, height: int = 220):
        """Render a mini overview chart."""
        html = f"""
<div class="tradingview-widget-container">
  <div class="tradingview-widget-container__widget"></div>
  <script type="text/javascript"
    src="https://s3.tradingview.com/external-embedding/embed-widget-mini-symbol-overview.js" async>
  {{
    "symbol": "{symbol}",
    "width": "100%",
    "height": "100%",
    "locale": "en",
    "dateRange": "1D",
    "colorTheme": "dark",
    "isTransparent": false,
    "autosize": true
  }}
  </script>
</div>
"""
        components.html(html, height=height)
