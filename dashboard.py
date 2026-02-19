import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime
import time

# --- STYLES & CONFIG ---
st.set_page_config(layout="wide", page_title="VP Terminal v2.3 Pro", initial_sidebar_state="expanded")
import styles
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
        "Core": "Home", "Technical": "Market Structure", "Volume & Order Flow": "Volume Profile (Legacy)",
        "Volatility & Risk": "Portfolio Risk", "Fundamental": "Valuation (DCF)", "Institutional": "Institutional Ownership",
        "Quant & Strategy": "Regime Backtest", "Screeners": "Setup Scanner", "Research & AI": "Backtester"
    }
    st.session_state['nav_view'] = defaults.get(cat, "Home")

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
    # This ensures shell reflects Streamlit's initial or updated state
    sync_script = f"""
    <script>
    window.addEventListener('load', () => {{
        if (window.state) {{
            window.state.ticker = "{st.session_state['current_ticker']}";
            window.state.viewId = "{st.session_state['nav_view']}";
            let catKey = "{st.session_state['nav_category'].lower().replace(' ', '_').replace('&_', '')}";
            // Handle special mapping for categories
            if (catKey === "volume_order_flow") catKey = "volume";
            if (catKey === "volatility_risk") catKey = "volatility";
            if (catKey === "research_ai") catKey = "research";
            
            window.state.category = catKey;
            
            if (typeof renderRail === 'function') renderRail();
            if (typeof renderNav === 'function') renderNav();
            if (typeof showView === 'function') showView(window.state.viewId, "{st.session_state['nav_view']}");
            
            // Update ticker input
            const ti = document.getElementById('tickerInput');
            if (ti) ti.value = window.state.ticker;
        }}
    }});
    </script>
    """
    
    # --- CLEAN SHELL INJECTION ---
    # Strip document level tags as Streamlit only allows body/div snippets in st.markdown
    import re
    # 1. Remove comments
    clean_html = re.sub(r'<!--.*?-->', '', shell_html, flags=re.DOTALL)
    
    # 2. Extract only the #app content (including the div itself)
    # We look for <div id="app"> ... </div> but regex for matching balanced tags is hard.
    # Instead, let's just strip the known preamble.
    clean_html = re.sub(r'<!DOCTYPE.*?>', '', clean_html, flags=re.IGNORECASE | re.DOTALL)
    clean_html = re.sub(r'<html.*?>', '', clean_html, flags=re.IGNORECASE | re.DOTALL)
    clean_html = re.sub(r'</html>', '', clean_html, flags=re.IGNORECASE | re.DOTALL)
    clean_html = re.sub(r'<head.*?>.*?</head>', '', clean_html, flags=re.IGNORECASE | re.DOTALL)
    clean_html = re.sub(r'<body.*?>', '', clean_html, flags=re.IGNORECASE | re.DOTALL)
    clean_html = re.sub(r'</body>', '', clean_html, flags=re.IGNORECASE | re.DOTALL)
    
    # 3. Aggressive whitespace cleanup:
    # Remove leading spaces on every line to avoid code block detection
    lines = [line.strip() for line in clean_html.split('\n') if line.strip()]
    clean_html = "".join(lines) # Join without newlines to be safe
    
    # 4. Inject JS
    # We simply replace the script tag. Since we removed newlines, we must match carefully or just append.
    # The file has <script src="app.js"></script>.
    # If we joined lines, it might be <script src="app.js"></script> directly.
    full_html = clean_html.replace('<script src="app.js"></script>', f'<script>{shell_js}</script>{sync_script}')
    
    # 5. Final Safety: Wrap in a div if not already (it should be)
    st.markdown(full_html, unsafe_allow_html=True)

render_shell()

# --- TOPBAR CONTROLS SYNC (Hidden) ---
# We keep these for state persistence and to allow Streamlit-side updates
with st.container():
    # Only show if not fully hidden by CSS, but styles.py hides this container
    new_ticker = st.text_input("Ticker", st.session_state['current_ticker'], key="hidden_ticker", label_visibility="collapsed")
    if new_ticker != st.session_state['current_ticker']:
        st.session_state['current_ticker'] = new_ticker.upper()
        # Update query param manually to trigger JS shell update on next load
        st.query_params["ticker"] = st.session_state['current_ticker']
        st.rerun()

# --- SIDEBAR NAVIGATION (Hidden) ---
def set_view(view, cat=None):
    st.session_state['nav_view'] = view
    if cat: st.session_state['nav_category'] = cat
    st.rerun()

# --- VIEW ROUTER & RENDERING ---
ticker = st.session_state['current_ticker']
nav_view = st.session_state['nav_view']

# 1. CORE
if nav_view == "Home":
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

elif nav_view == "Chart":
    st.subheader(f"Chart: {ticker}")
    TradingViewWidget.render(ticker)

elif nav_view == "News": render_sentiment_timeline(ticker)
elif nav_view == "Events": render_econ_impact_overlay(ticker)

# 2. TECHNICAL
elif nav_view == "Market Structure": render_market_structure(ticker)
elif nav_view == "FVG Scanner": render_fvg_scanner(ticker)
# ...
elif nav_view == "Watchlist Scoring":
    st.subheader("Watchlist Scoring")
    # ...

elif nav_view == "AI Report Generator":
    st.subheader("AI Report Generator")
    gen = AIReportGenerator()
    if st.button(f"Generate Report for {ticker}"):
        path = gen.generate_report(ticker, {})
        st.success(f"Report Generated: {path}")
