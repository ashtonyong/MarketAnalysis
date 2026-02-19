import streamlit as st
from streamlit_autorefresh import st_autorefresh
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta
# --- Component Imports ---
from components.sidebar_widgets import SidebarWidgets
from components.events_widgets import EventsWidgets
from components.backtester_ui import render_backtester_tab
from volume_profile_engine import VolumeProfileEngine
from volume_profile_backtester import VolumeProfileBacktester, STRATEGIES
from ai_agent_interface import VolumeProfileAgent
from volume_profile_engine import ProfileComparator, ValueAreaMigrationTracker, POCZoneCalculator
from time_and_sales import TimeAndSalesAnalyzer
from market_profile import MarketProfileEngine
from composite_profile import CompositeProfileBuilder
from volume_nodes import VolumeNodeDetector
from pattern_detector import ProfilePatternDetector
from profile_stats import ProfileStatistics
from scanner import VolumeProfileScanner, WATCHLISTS
from session_analysis import SessionAnalyzer
from risk_manager import RiskManager
from tradingview_widget import TradingViewWidget
from ai_report import AIReportGenerator
from multi_timeframe import MultiTimeframeAnalyzer
from correlation import CorrelationAnalyzer as LegacyCorrelationAnalyzer
from news_feed import NewsFeedAnalyzer
from options_flow import OptionsFlowAnalyzer
from alerts_engine import AlertsEngine, WatchlistManager
from trade_journal import TradeJournal, TickerNotes, UserPreferences
from backtester import BacktestEngine
from quant_engine import MonteCarloSimulator, RegimeDetector, ZScoreCalculator
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
from backtest_engine import render_regime_backtest
from garch_forecaster import render_garch_forecaster
from options_analytics import render_options_analytics
import numpy as np

st.set_page_config(layout="wide", page_title="VP Terminal v2.3")

# --- Minimal Dark Theme CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }
    .main .block-container { padding: 1.2rem 2rem; max-width: 100%; }
    
    /* Sidebar */
    [data-testid="stSidebar"] { background: #0d1117; border-right: 1px solid #21262d; }
    
    /* Buttons */
    .stButton > button {
        background: #21262d !important; color: #e6edf3 !important;
        border: 1px solid #30363d !important; border-radius: 6px;
    }
    .stButton > button:hover { background: #30363d !important; border-color: #8b949e !important; }

    /* Metrics */
    [data-testid="stMetric"] { background: #161b22; border: 1px solid #21262d; border-radius: 6px; padding: 12px; }
    
    /* Radio Buttons (Navigation) */
    .stRadio > div { background: transparent; }
    .stRadio label { font-size: 14px; font-weight: 500; padding: 4px 0; }
</style>
""", unsafe_allow_html=True)

# --- Ticker Mapping ---
YAHOO_TICKER_MAP = {
    'XAUUSD': 'GC=F', 'GOLD': 'GC=F', 'CRUDEOIL': 'CL=F', 'OIL': 'CL=F',
    'BTCUSD': 'BTC-USD', 'ETHUSD': 'ETH-USD', 'SOLUSD': 'SOL-USD',
    'EURUSD': 'EURUSD=X', 'USDJPY': 'USDJPY=X', 'GBPUSD': 'GBPUSD=X',
    'NQ': 'NQ=F', 'ES': 'ES=F'
}

# --- Sidebar Header ---
st.sidebar.markdown("### 📊 VP Terminal")

# --- GLOBAL TICKER SELECTION ---
if 'current_ticker' not in st.session_state: st.session_state['current_ticker'] = "SPY"
popular_tickers = ["SPY", "QQQ", "IWM", "AAPL", "MSFT", "NVDA", "TSLA", "AMD", "BTCUSD", "ETHUSD", "XAUUSD", "CL=F"]

selected_ticker = st.sidebar.selectbox("Ticker", options=popular_tickers + ["Custom"], 
    index=popular_tickers.index(st.session_state['current_ticker']) if st.session_state['current_ticker'] in popular_tickers else len(popular_tickers))

if selected_ticker == "Custom":
    raw_ticker = st.sidebar.text_input("Symbol", value="SPY").upper().strip()
else:
    raw_ticker = selected_ticker

st.session_state['current_ticker'] = raw_ticker
ticker = YAHOO_TICKER_MAP.get(raw_ticker, raw_ticker)

# --- Global Settings ---
c1, c2 = st.sidebar.columns(2)
period = c1.selectbox("Period", ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y"], index=2)
interval = c2.selectbox("Interval", ["1m", "5m", "15m", "30m", "1h", "1d", "1wk"], index=5)

# --- MARKET STATUS ---
import time
_now = datetime.now()
_market_status = "OPEN" if 9 <= _now.hour < 16 and _now.weekday() < 5 else "CLOSED"
_color = "#238636" if _market_status == "OPEN" else "#da3633"

st.sidebar.markdown(f"""
<div style='display: flex; align-items: center; justify-content: space-between; background: #161b22; padding: 8px 12px; border-radius: 6px; border: 1px solid #30363d; margin: 10px 0;'>
    <div>
        <span style='font-size: 10px; color: #8b949e; font-weight: 600;'>MARKET</span>
        <div style='font-size: 12px; font-weight: bold; color: {_color};'>{_market_status}</div>
    </div>
    <div style='text-align: right;'>
        <span style='font-size: 10px; color: #8b949e; font-weight: 600;'>LIVE</span>
        <div style='font-size: 12px; font-weight: bold; color: #e6edf3;'>{_now.strftime('%H:%M:%S')}</div>
    </div>
</div>
""", unsafe_allow_html=True)

if st.sidebar.button("🔄 Refresh Analysis", use_container_width=True):
    st.rerun()

st.sidebar.markdown("---")

# --- WIDGETS ---
with st.sidebar.expander("Market Overview", expanded=True) as c:
    SidebarWidgets.render_indices(c)
    
with st.sidebar.expander("Trending Tickers", expanded=False) as c:
    SidebarWidgets.render_trending(c)

with st.sidebar.expander("Upcoming Events", expanded=False) as c:
    SidebarWidgets.render_compact_events(c)
    
with st.sidebar.expander("Earnings This Week", expanded=False) as c:
    SidebarWidgets.render_compact_earnings(c)

# --- NAVIGATION SYSTEM (LAZY LOADING FIX) ---
st.sidebar.markdown("---")
st.sidebar.subheader("Navigation")

nav_category = st.sidebar.radio(
    "Category",
    ["Core", "Technical", "Volume & Order Flow", "Volatility & Risk", 
     "Fundamental", "Institutional", "Quant & Strategy", "Screeners", "Research"],
    index=0
)

# Dynamic Sub-Navigation
if nav_category == "Core":
    nav_view = st.sidebar.radio("View", ["Home", "Chart", "News", "Events"])
    
elif nav_category == "Technical":
    nav_view = st.sidebar.radio("View", 
        ["Market Structure", "FVG Scanner", "MTF Confluence", "Session Ranges", "Pre/Post Tracker", "Targets", "Range Analysis"])

elif nav_category == "Volume & Order Flow":
    nav_view = st.sidebar.radio("Analysis", 
        ["Volume Profile (Legacy)", "Order Flow", "Liquidity Heatmap", "Session Analysis"])

elif nav_category == "Volatility & Risk":
    nav_view = st.sidebar.radio("Tools", 
        ["Portfolio Risk", "Earnings Volatility", "GARCH Forecast", "Vol Surface", "Options Flow", "Options Chain"])

elif nav_category == "Fundamental":
    nav_view = st.sidebar.radio("Metrics", 
        ["Valuation (DCF)", "Valuation History", "Analyst Ratings", "Peers", "Dividends"])

elif nav_category == "Institutional":
    nav_view = st.sidebar.radio("Tracking", 
        ["Institutional Ownership", "Insider Trading", "Short Interest", "Sentiment Timeline"])

elif nav_category == "Quant & Strategy":
    nav_view = st.sidebar.radio("Models", 
        ["Regime Backtest", "Pairs Trading", "Rolling Beta", "Factor Model", "Correlation"])

elif nav_category == "Screeners":
    nav_view = st.sidebar.radio("Scanner", 
        ["Setup Scanner", "Fundamental Screener", "RS Rating"])

elif nav_category == "Research":
    nav_view = st.sidebar.radio("Lab", 
        ["Backtester", "AI Insights", "Tools"])

# --- MAIN CONTENT RENDERING ---

# 1. CORE VIEWS
if nav_category == "Core":
    if nav_view == "Home":
        st.subheader("🏠 Home")
        
        # Initialize Managers
        journal = TradeJournal()
        wl_mgr = WatchlistManager()
        alert_engine = AlertsEngine()
        
        home_tabs = st.tabs(["Overview", "Journal", "Watchlists", "Alerts"])
        
        # --- OVERVIEW ---
        with home_tabs[0]:
            # Summary Cards
            active_alerts = alert_engine.get_active_alerts()
            triggered_alerts = alert_engine.get_triggered_alerts()
            journal_stats = journal.get_stats()
            
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Active Alerts", len(active_alerts) if active_alerts else 0)
            c2.metric("Triggered Today", len(triggered_alerts) if triggered_alerts else 0)
            c3.metric("Win Rate", f"{journal_stats.get('win_rate', 0)}%")
            c4.metric("Total Trades", journal_stats.get('total_trades', 0))
            
            st.divider()
            st.markdown("### Watchlist Overview")
            wl_names = wl_mgr.get_names()
            if wl_names:
                sel_wl = st.selectbox("Select Watchlist", wl_names)
                tickers = wl_mgr.get_tickers(sel_wl)
                if tickers:
                    st.write(f"**{sel_wl}**: {', '.join(tickers)}")
            else:
                st.info("No watchlists created.")

        # --- JOURNAL ---
        with home_tabs[1]:
            st.subheader("Trade Journal")
            # Simple form to add trade
            with st.expander("Log New Trade"):
                with st.form("trade_log"):
                    t_ticker = st.text_input("Ticker", value=ticker)
                    t_action = st.selectbox("Action", ["Buy", "Sell"])
                    t_price = st.number_input("Price", min_value=0.0)
                    t_shares = st.number_input("Shares", min_value=1)
                    t_notes = st.text_area("Notes")
                    if st.form_submit_button("Log Trade"):
                        journal.log_trade(t_ticker, t_action, t_price, t_shares, t_notes)
                        st.success("Trade Logged!")
            
            # Show Recent
            trades = journal.get_recent_trades()
            if not trades.empty:
                st.dataframe(trades, use_container_width=True)

        # --- WATCHLISTS ---
        with home_tabs[2]:
            st.subheader("Manage Watchlists")
            new_wl = st.text_input("New Watchlist Name")
            if st.button("Create Watchlist") and new_wl:
                wl_mgr.create_watchlist(new_wl)
                st.success(f"Created {new_wl}")

        # --- ALERTS ---
        with home_tabs[3]:
            st.subheader("Active Alerts")
            if active_alerts:
                st.dataframe(active_alerts, use_container_width=True)
            else:
                st.info("No active alerts.")
            
    elif nav_view == "Chart":
        st.subheader(f"📈 Chart: {ticker}")
        TradingViewWidget.render(ticker)
        
    elif nav_view == "News":
        render_sentiment_timeline(ticker)
        
    elif nav_view == "Events":
        render_econ_impact_overlay(ticker)

# 2. TECHNICAL ANALYSIS
elif nav_category == "Technical":
    if nav_view == "Market Structure": render_market_structure(ticker)
    elif nav_view == "FVG Scanner": render_fvg_scanner(ticker)
    elif nav_view == "MTF Confluence": render_mtf_confluence(ticker)
    elif nav_view == "Session Ranges": render_session_range(ticker)
    elif nav_view == "Pre/Post Tracker": render_prepost_tracker(popular_tickers)
    elif nav_view == "Targets": render_price_targets(ticker)
    elif nav_view == "Range Analysis": render_range_dashboard(ticker)

# 3. VOLUME & ORDER FLOW
elif nav_category == "Volume & Order Flow":
    if nav_view == "Volume Profile (Legacy)":
        # Simplified VP rendering
        engine = VolumeProfileEngine(ticker, period, interval)
        engine.fetch_data()
        engine.calculate_volume_profile()
        st.write("Volume Profile Logic Here (Simplified for Lazy Load)")
        # In real app, paste full logic or modularize 'render_volume_profile'
        
    elif nav_view == "Order Flow":
        st.subheader("Order Flow & TPO")
        st.info("Market Profile Engine Loading...")
        try:
            mp = MarketProfileEngine(ticker)
            tpo = mp.calculate_tpo_profile()
            if tpo:
                st.write(f"Day Type: {tpo['day_type']}")
            else:
                st.warning("No TPO data")
        except Exception as e:
            st.error(f"Error: {e}")
            
    elif nav_view == "Liquidity Heatmap": render_liquidity_heatmap(ticker)
    elif nav_view == "Session Analysis": 
        sess = SessionAnalyzer(ticker)
        st.write("Session Analysis Placeholder")

# 4. VOLATILITY & RISK
elif nav_category == "Volatility & Risk":
    if nav_view == "Portfolio Risk": render_portfolio_risk(ticker)
    elif nav_view == "Earnings Volatility": render_earnings_volatility(ticker)
    elif nav_view == "GARCH Forecast": render_garch_forecaster(ticker)
    elif nav_view == "Vol Surface": render_vol_surface(ticker)
    elif nav_view == "Options Chain": render_options_analytics(ticker)
    elif nav_view == "Options Flow": 
        st.subheader("Options Flow")
        try:
            ofa = OptionsFlowAnalyzer(ticker)
            exps = ofa.get_expirations()
            if exps:
                sel = st.selectbox("Expiration", exps)
                if st.button("Load Flow"):
                    res = ofa.analyze(sel)
                    st.write(res)
        except: st.error("Options Error")

# 5. FUNDAMENTAL
elif nav_category == "Fundamental":
    if nav_view == "Valuation (DCF)": render_dcf_engine(ticker)
    elif nav_view == "Valuation History": render_valuation_history(ticker)
    elif nav_view == "Analyst Ratings": render_analyst_ratings(ticker)
    elif nav_view == "Peers": render_peer_comparison(ticker)
    elif nav_view == "Dividends": render_dividend_tracker(ticker)

# 6. INSTITUTIONAL
elif nav_category == "Institutional":
    if nav_view == "Institutional Ownership": render_institutional_tracker(ticker)
    elif nav_view == "Insider Trading": render_insider_tracker(ticker)
    elif nav_view == "Short Interest": render_short_interest(ticker)
    elif nav_view == "Sentiment Timeline": render_sentiment_timeline(ticker)

# 7. QUANT & STRATEGY
elif nav_category == "Quant & Strategy":
    if nav_view == "Regime Backtest": render_regime_backtest(ticker)
    elif nav_view == "Pairs Trading": render_pairs_trading(ticker)
    elif nav_view == "Rolling Beta": render_rolling_beta(ticker)
    elif nav_view == "Factor Model": render_factor_model(ticker)
    elif nav_view == "Correlation": 
        st.subheader("Correlation Matrix")
        # Legacy/Simple Correlation placeholder
        st.info("Correlation Matrix Placeholder")

# 8. SCREENERS
elif nav_category == "Screeners":
    if nav_view == "Setup Scanner": render_setup_scanner(popular_tickers)
    elif nav_view == "Fundamental Screener": render_fundamental_screener(ticker)
    elif nav_view == "RS Rating": render_rs_rating(ticker)

# 9. RESEARCH
elif nav_category == "Research":
    if nav_view == "Backtester": render_backtester_tab(ticker, period)
    elif nav_view == "AI Insights":
        if st.button("Generate AI Plan"):
            st.info("AI Agent Thinking...")
            plan = VolumeProfileAgent.get_trading_plan(ticker, period)
            st.write(plan)
    elif nav_view == "Tools":
        st.write("Calculators & Tools")
st.sidebar.markdown("<div style='font-size:10px;color:#484f58;'>VP Terminal v2.3</div>", unsafe_allow_html=True)
