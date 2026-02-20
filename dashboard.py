import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime
import time

# --- STYLES & CONFIG ---
st.set_page_config(layout="wide", page_title="VP Terminal v2.5 (Fixed)", initial_sidebar_state="expanded")
import styles
import time
# Force reload of CSS by treating it as dynamic injection
st.markdown(styles.get_css(), unsafe_allow_html=True)

# --- IMPORTS (Keep all existing) ---
from components.sidebar_widgets import SidebarWidgets
from components.events_widgets import EventsWidgets
from components.backtester_ui import render_backtester_tab
from volume_profile_engine import VolumeProfileEngine
# from volume_profile_backtester import VolumeProfileBacktester, STRATEGIES # (Unused import in original?)
from ai_agent_interface import VolumeProfileAgent
from market_profile import MarketProfileEngine
from session_analysis import SessionAnalyzer
from risk_manager import RiskManager
from tradingview_widget import TradingViewWidget
from ai_report import AIReportGenerator
from multi_timeframe import MultiTimeframeAnalyzer
from news_feed import NewsFeedAnalyzer
from options_flow import OptionsFlowAnalyzer
from alerts_engine import AlertsEngine, WatchlistManager
from trade_journal import TradeJournal
from backtester import BacktestEngine
from quant_engine import MonteCarloSimulator
from strategies import BaseStrategy
from session_range import render_session_range
from mtf_confluence import render_mtf_confluence
from rolling_beta import render_rolling_beta
from earnings_volatility import render_earnings_volatility
from short_interest import render_short_interest
from fvg_scanner import render_fvg_scanner
from market_structure import render_market_structure
from dcf_engine import render_dcf_engine
from fundamental_screener import render_fundamental_screener
from portfolio_risk import render_portfolio_risk
from regime_backtest import render_regime_backtest
from insider_tracker import render_insider_tracker
from liquidity_heatmap import render_liquidity_heatmap
from vol_surface import render_vol_surface
from factor_model import render_factor_model
from dividend_tracker import render_dividend_tracker
from peer_comparison import render_peer_comparison
from price_targets import render_price_targets
from range_dashboard import render_range_dashboard
from econ_impact_overlay import render_econ_impact_overlay
from setup_scanner import render_setup_scanner
from prepost_tracker import render_prepost_tracker
from sentiment_timeline import render_sentiment_timeline
from rs_rating import render_rs_rating
from analyst_ratings import render_analyst_ratings
from valuation_history import render_valuation_history
from institutional_tracker import render_institutional_tracker
from pairs_trading import render_pairs_trading
from garch_forecaster import render_garch_forecaster
from options_analytics import render_options_analytics
from watchlist_scoring import WatchlistScorer # For Platform-Wide mapped to Screeners

# --- STATE MANAGEMENT ---
if 'nav_category' not in st.session_state: st.session_state['nav_category'] = "Core"
if 'nav_view' not in st.session_state: st.session_state['nav_view'] = "Home"
if 'current_ticker' not in st.session_state: st.session_state['current_ticker'] = "SPY"

# --- HELPER: SET CATEGORY ---
def set_cat(cat):
    st.session_state['nav_category'] = cat
    # Default views for each category
    defaults = {
        "Core": "home", "Technical": "market_structure", "Volume & Order Flow": "volume_profile",
        "Volatility & Risk": "portfolio_risk", "Fundamental": "dcf_engine", "Institutional": "institutional_tracker",
        "Quant & Strategy": "regime_backtest", "Screeners": "setup_scanner", "Research & AI": "backtester"
    }
    st.session_state['nav_view'] = defaults.get(cat, "home")

def set_view(view):
    st.session_state['nav_view'] = view

# --- QUERY PARAM SYNC ---
q_ticker = st.query_params.get("ticker", st.session_state['current_ticker'])
q_view = st.query_params.get("view", st.session_state['nav_view'])
q_cat = st.query_params.get("cat", st.session_state['nav_category'])

if q_ticker != st.session_state['current_ticker']:
    st.session_state['current_ticker'] = q_ticker
    st.rerun()

if q_view != st.session_state['nav_view']:
    st.session_state['nav_view'] = q_view
    # Map cat back to display name if needed
    st.session_state['nav_category'] = q_cat.title().replace('_', ' ')
    st.rerun()

# --- CUSTOM SHELL INJECTION ---
def render_shell():
    try:
        with open("vp-terminal.html", "r", encoding="utf-8") as f:
            shell_html = f.read()
        with open("app.js", "r", encoding="utf-8") as f:
            shell_js = f.read()
    except Exception as e:
        # Fallback to simple notice if files missing
        st.warning("Redesign shell assets loading...")
        return

    # Sync state from streamlit to shell
    # Extremely dense, single-line IIFE with strictly matched braces to bypass Streamlit's Markdown parser
    cat_key = st.session_state['nav_category'].lower().replace(' ', '_').replace('&_', '')
    sync_script = (
        f"<script>(function(){{"
        f"if(window.state){{"
        f"window.state.ticker='{st.session_state['current_ticker']}';"
        f"window.state.viewId='{st.session_state['nav_view']}';"
        f"let catKey='{cat_key}';"
        f"if(catKey==='volume_order_flow')catKey='volume';"
        f"if(catKey==='volatility_risk')catKey='volatility';"
        f"if(catKey==='research_ai')catKey='research';"
        f"window.state.category=catKey;"
        f"if(typeof renderRail==='function')renderRail();"
        f"if(typeof renderNav==='function')renderNav();"
        f"if(typeof showView==='function')showView(window.state.viewId,'{st.session_state['nav_view']}');"
        f"const ti=document.getElementById('tickerInput');"
        f"if(ti)ti.value=window.state.ticker;"
        f"}}"
        f"}})();</script>"
    )
    
    # --- CLEAN SHELL INJECTION ---
    # Strip document level tags as Streamlit only allows body/div snippets in st.markdown
    import re
    # 1. Remove HTML comments
    clean_html = re.sub(r'<!--.*?-->', '', shell_html, flags=re.DOTALL)
    
    # 2. Extract only the body content
    clean_html = re.sub(r'<!DOCTYPE.*?>', '', clean_html, flags=re.IGNORECASE | re.DOTALL)
    clean_html = re.sub(r'<html.*?>', '', clean_html, flags=re.IGNORECASE | re.DOTALL)
    clean_html = re.sub(r'</html>', '', clean_html, flags=re.IGNORECASE | re.DOTALL)
    clean_html = re.sub(r'<head.*?>.*?</head>', '', clean_html, flags=re.IGNORECASE | re.DOTALL)
    clean_html = re.sub(r'<body.*?>', '', clean_html, flags=re.IGNORECASE | re.DOTALL)
    clean_html = re.sub(r'</body>', '', clean_html, flags=re.IGNORECASE | re.DOTALL)

    # 3. Compile the exact Javascript payload
    combined_js = shell_js + "\n" + sync_script.replace('<script>', '').replace('</script>', '')
    
    # 4. Integrate JS into the HTML Shell directly
    script_pattern = r'<script\s+src=["\']app\.js["\']\s*></script>'
    full_html = re.sub(script_pattern, f"<script>{combined_js}</script>", clean_html, flags=re.IGNORECASE)
    
    # 5. Base64 Encode the ENTIRE payload to protect it
    import base64
    b64_payload = base64.b64encode(full_html.encode('utf-8')).decode('utf-8')
    
    # 6. Inject via a tiny hidden Component Iframe that manipulates the Parent DOM
    import streamlit.components.v1 as components
    injector_js = f"""
    <script>
        // Use a slight delay to ensure Streamlit's initial render is stable
        setTimeout(() => {{
            if (!window.parent.document.getElementById('vp-terminal-root')) {{
                const b64Data = "{b64_payload}";
                // Decode base64 to Unicode string safely
                const rawHtml = decodeURIComponent(escape(window.atob(b64Data)));
                
                const root = window.parent.document.createElement('div');
                root.id = 'vp-terminal-root';
                root.innerHTML = rawHtml;
                
                // Note: innerHTML does not execute scripts. We must extract and run them manually.
                window.parent.document.body.appendChild(root);
                
                const scripts = root.getElementsByTagName('script');
                for (let i = 0; i < scripts.length; i++) {{
                    const newScript = window.parent.document.createElement('script');
                    newScript.textContent = scripts[i].textContent;
                    window.parent.document.body.appendChild(newScript);
                }}
            }}
        }}, 100);
    </script>
    """
    components.html(injector_js, height=0, width=0)

render_shell()

# --- NAVIGATION SYNC BRIDGE ---
# We read the state directly from the URL. Our Javascript shell updates the URL
# via history.pushState and then clicks a hidden button to force Streamlit to resync.

_need_rerun = False
if "ticker" in st.query_params and st.query_params["ticker"].upper() != st.session_state.get('current_ticker'):
    st.session_state['current_ticker'] = st.query_params["ticker"].upper()
    _need_rerun = True

if "view" in st.query_params and st.query_params["view"].lower() != st.session_state.get('nav_view'):
    st.session_state['nav_view'] = st.query_params["view"].lower()
    _need_rerun = True

if "cat" in st.query_params and st.query_params["cat"].lower() != st.session_state.get('nav_category'):
    st.session_state['nav_category'] = st.query_params["cat"].lower()
    _need_rerun = True

# If the URL had values different from session state, we update session state.
# We don't necessarily have to rerun here because we are reading the params *before* rendering the views,
# so the views below will automatically use the updated session state!

with st.sidebar:
    # This button is completely invisible due to styles.py (sidebar width=0, visibility=hidden)
    # Javascript calls .click() on it to silently force a backend rerun.
    st.button("V2_SyncState", key="sync_btn")

# --- SIDEBAR NAVIGATION (Hidden) ---
def set_view(view, cat=None):
    st.session_state['nav_view'] = view
    if cat: st.session_state['nav_category'] = cat
    st.query_params["view"] = view
    if cat: st.query_params["cat"] = cat
    st.rerun()

# --- VIEW ROUTER & RENDERING ---
ticker = st.session_state['current_ticker']
# Force lowercase to fix legacy session state mismatch (e.g. "Home" -> "home")
st.session_state['nav_view'] = st.session_state['nav_view'].lower()
nav_view = st.session_state['nav_view']

# DEBUG: Show current view state to verify rendering
# st.error(f"DEBUG: Current View = '{nav_view}' | hidden_view = '{st.session_state.get('hidden_view', 'NONE')}' | new_view = '{st.session_state.get('nav_view')}'")

# 1. CORE
if nav_view == "home":
    st.subheader("Home Dashboard")
    
    # Initialize Managers
    journal = TradeJournal()
    wl_mgr = WatchlistManager()
    alert_engine = AlertsEngine()
    
    home_tabs = st.tabs(["Overview", "Journal", "Watchlists", "Alerts"])
    
    # --- OVERVIEW ---
    with home_tabs[0]:
        active_alerts = alert_engine.get_active_alerts()
        triggered_alerts = alert_engine.get_triggered_alerts()
        journal_stats = journal.get_stats()
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Active Alerts", len(active_alerts) if active_alerts else 0)
        c2.metric("Triggered Today", len(triggered_alerts) if triggered_alerts else 0)
        c3.metric("Win Rate", f"{journal_stats.get('win_rate', 0)}%")
        c4.metric("Total Trades", journal_stats.get('total_trades', 0))
        
        st.markdown("---")
        
        # Split Layout
        col_main, col_side = st.columns([2, 1])
        
        with col_main:
            st.markdown("### Watchlist & Heatmap")
            wl_names = wl_mgr.get_names()
            if wl_names:
                sel_wl = st.selectbox("Select Watchlist", wl_names)
                tickers = wl_mgr.get_tickers(sel_wl)
                if tickers:
                    st.caption(f"**{sel_wl}**: {', '.join(tickers)}")
                    
                    # HEATMAP
                    with st.spinner("Loading heatmap..."):
                        try:
                            df = yf.download(tickers, period="2d", progress=False)
                            data = []
                            # (Heatmap Data Logic)
                            if len(tickers) == 1:
                                close = df['Close']
                                change = (close.iloc[-1] - close.iloc[0]) / close.iloc[0] * 100
                                data.append({'Ticker': tickers[0], 'Change': change, 'Price': close.iloc[-1], 'Size': 1})
                            else:
                                close = df['Close']
                                for t in tickers:
                                    if t in close.columns:
                                        s = close[t].dropna()
                                        if len(s) >= 2:
                                            chg = (s.iloc[-1] - s.iloc[-2]) / s.iloc[-2] * 100
                                            data.append({'Ticker': t, 'Change': chg, 'Price': s.iloc[-1], 'Size': 1})
                            
                            if data:
                                df_map = pd.DataFrame(data)
                                # Custom Color Scale for "Green=Pos, Red=Neg"
                                fig = px.treemap(
                                    df_map, path=['Ticker'], values='Size', color='Change',
                                    color_continuous_scale=[(0, "#ef4444"), (0.5, "#161b22"), (1, "#10b981")],
                                    range_color=[-3, 3],
                                    custom_data=['Change', 'Price']
                                )
                                fig.update_traces(
                                    textposition="middle center",
                                    texttemplate="%{label}<br>%{customdata[0]:.2f}%<br>$%{customdata[1]:.2f}",
                                    hovertemplate="%{label}<br>$%{customdata[1]:.2f}<br>%{customdata[0]:.2f}%"
                                )
                                fig.update_layout(margin=dict(t=0,l=0,r=0,b=0), height=350, paper_bgcolor='rgba(0,0,0,0)')
                                st.plotly_chart(fig, use_container_width=True)
                        except Exception as e: st.error(f"Heatmap: {e}")
        
    # --- JOURNAL ---
    with home_tabs[1]:
        # ... (Journal Logic) ...
        pass

elif nav_view == "chart":
    st.subheader(f"Chart: {ticker}")
    TradingViewWidget.render_chart(ticker)

elif nav_view == "news": render_sentiment_timeline(ticker)
elif nav_view == "events": render_econ_impact_overlay(ticker)

# 2. TECHNICAL
elif nav_view == "market_structure": render_market_structure(ticker)
elif nav_view == "fvg_scanner": render_fvg_scanner(ticker)
# ...
elif nav_view == "setup_scanner":
    st.subheader("Watchlist Scoring")
    # ...

elif nav_view == "ai_report":
    st.subheader("AI Report Generator")
    gen = AIReportGenerator()
    if st.button(f"Generate Report for {ticker}"):
        path = gen.generate_report(ticker, {})
        st.success(f"Report Generated: {path}")

# --- 3. MISSING VIEW HANDLERS (Mapped to Imports) ---
elif nav_view == "mtf_confluence": render_mtf_confluence(ticker)
elif nav_view == "session_range": render_session_range(ticker)
elif nav_view == "liquidity_heatmap": render_liquidity_heatmap(ticker)
elif nav_view == "portfolio_risk": render_portfolio_risk(ticker)
elif nav_view == "earnings_volatility": render_earnings_volatility(ticker)
elif nav_view == "vol_surface": render_vol_surface(ticker)
elif nav_view == "dcf_engine": render_dcf_engine(ticker)
elif nav_view == "peer_comparison": render_peer_comparison(ticker)
elif nav_view == "dividend_tracker": render_dividend_tracker(ticker)
elif nav_view == "insider_tracker": render_insider_tracker(ticker)
elif nav_view == "short_interest": render_short_interest(ticker)
elif nav_view == "sentiment_timeline": render_sentiment_timeline(ticker)
elif nav_view == "regime_backtest": render_regime_backtest(ticker)
elif nav_view == "rolling_beta": render_rolling_beta(ticker)
elif nav_view == "factor_model": render_factor_model(ticker)
elif nav_view == "fundamental_screener": render_fundamental_screener(ticker)
elif nav_view == "backtester": render_backtester_tab()

# --- 4. CATCH-ALL FOR UNIMPLEMENTED FEATURES ---
else:
    st.container().empty() # spacer
    st.info(f"🚧 **{nav_view.replace('_', ' ').title()}** is currently under construction.")
    st.caption("This feature is part of the roadmap and will be available in the next update.")
