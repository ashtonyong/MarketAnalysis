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

# --- TOPBAR ---
with st.container():
    # Grid: Logo/Title | Ticker/Controls | Status/Clock
    c_logo, c_controls, c_status = st.columns([2, 5, 3])
    
    with c_logo:
        st.markdown("""
        <div style="display:flex; align-items:center; gap:10px;">
            <div style="width:28px; height:28px; background:linear-gradient(135deg, #3b82f6, #8b5cf6); border-radius:6px; color:white; display:flex; align-items:center; justify-content:center; font-weight:800; font-size:14px;">VP</div>
            <div style="line-height:1.1;">
                <div style="font-weight:700; font-size:15px; color:#e2e8f0;">Terminal</div>
                <div style="font-size:10px; color:#64748b;">v2.3 Pro</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    with c_controls:
        cc1, cc2, cc3, cc4 = st.columns([2, 0.2, 1, 1])
        with cc1:
            raw_ticker = st.text_input("Ticker", value=st.session_state['current_ticker'], label_visibility="collapsed", placeholder="Search Ticker...")
            st.session_state['current_ticker'] = raw_ticker.upper().strip()
            
        with cc3:
            period = st.selectbox("Period", ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y"], index=2, label_visibility="collapsed")
        with cc4:
            interval = st.selectbox("Interval", ["1m", "5m", "15m", "30m", "1h", "1d", "1wk"], index=5, label_visibility="collapsed")
            
    with c_status:
        _now = datetime.now()
        _market = "OPEN" if 9 <= _now.hour < 16 and _now.weekday() < 5 else "CLOSED"
        _color = "#10b981" if _market == "OPEN" else "#ef4444"
        
        st.markdown(f"""
        <div style="display:flex; justify-content:flex-end; align-items:center; gap:16px;">
            <div style="display:flex; align-items:center; gap:6px; background:rgba(16,185,129,0.12); padding:4px 8px; border-radius:100px; color:{_color}; font-size:10px; font-weight:600;">
                <div style="width:6px; height:6px; background:currentColor; border-radius:50%;"></div> MARKET {_market}
            </div>
            <div style="text-align:right;">
                <div style="font-family:'JetBrains Mono'; font-size:14px; font-weight:600; color:#e2e8f0;">{_now.strftime('%H:%M:%S')}</div>
                <div style="font-size:9px; color:#64748b;">{_now.strftime('%b %d')}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

st.divider()

# --- SIDEBAR NAVIGATION (Rail + Panel) ---
with st.sidebar:
    # Custom 2-col sidebar
    c_rail, c_nav = st.columns([1, 4])
    
    # RAIL
    with c_rail:
        # Text-based Rail for Professional Look (No Emojis)
        if st.button("CORE", key="nav_core", help="Core Dashboard"): set_cat("Core")
        if st.button("TECH", key="nav_tech", help="Technical Analysis"): set_cat("Technical")
        if st.button("VOL", key="nav_vol", help="Volume & Order Flow"): set_cat("Volume & Order Flow")
        if st.button("RISK", key="nav_risk", help="Volatility & Risk"): set_cat("Volatility & Risk")
        if st.button("FUND", key="nav_fund", help="Fundamental Analysis"): set_cat("Fundamental")
        if st.button("INST", key="nav_inst", help="Institutional Tracking"): set_cat("Institutional")
        if st.button("QNT", key="nav_quant", help="Quant & Strategy"): set_cat("Quant & Strategy")
        if st.button("SCAN", key="nav_screen", help="Screeners"): set_cat("Screeners")
        if st.button("R&D", key="nav_res", help="Research & AI"): set_cat("Research & AI")
        
        st.markdown("---")
        if st.button("RFR", key="refresh", help="Refresh Data"): st.rerun()

    # PANEL
    with c_nav:
        cat = st.session_state['nav_category']
        st.markdown(f"**{cat}**")
        
        # CATEGORY VIEW LISTS
        if cat == "Core":
            for v in ["Home", "Chart", "News", "Events"]:
                if st.button(v, key=f"v_{v}", type="primary" if st.session_state['nav_view'] == v else "secondary"): set_view(v)
        
        elif cat == "Technical":
            for v in ["Market Structure", "FVG Scanner", "MTF Confluence", "Session Ranges", "Pre/Post Tracker", "Targets", "Range Analysis"]:
                if st.button(v, key=f"v_{v}", type="primary" if st.session_state['nav_view'] == v else "secondary"): set_view(v)
                
        elif cat == "Volume & Order Flow":
            for v in ["Volume Profile (Legacy)", "Order Flow", "Liquidity Heatmap", "Session Analysis"]:
                if st.button(v, key=f"v_{v}", type="primary" if st.session_state['nav_view'] == v else "secondary"): set_view(v)

        elif cat == "Volatility & Risk":
            for v in ["Portfolio Risk", "Earnings Volatility", "GARCH Forecast", "Vol Surface", "Options Flow", "Options Chain"]:
                if st.button(v, key=f"v_{v}", type="primary" if st.session_state['nav_view'] == v else "secondary"): set_view(v)

        elif cat == "Fundamental":
            for v in ["Valuation (DCF)", "Valuation History", "Analyst Ratings", "Peers", "Dividends"]:
                if st.button(v, key=f"v_{v}", type="primary" if st.session_state['nav_view'] == v else "secondary"): set_view(v)

        elif cat == "Institutional":
            for v in ["Institutional Ownership", "Insider Trading", "Short Interest", "Sentiment Timeline"]:
                if st.button(v, key=f"v_{v}", type="primary" if st.session_state['nav_view'] == v else "secondary"): set_view(v)

        elif cat == "Quant & Strategy":
            for v in ["Regime Backtest", "Pairs Trading", "Rolling Beta", "Factor Model", "Correlation"]:
                if st.button(v, key=f"v_{v}", type="primary" if st.session_state['nav_view'] == v else "secondary"): set_view(v)

        elif cat == "Screeners":
            for v in ["Setup Scanner", "Fundamental Screener", "RS Rating", "Watchlist Scoring"]:
                if st.button(v, key=f"v_{v}", type="primary" if st.session_state['nav_view'] == v else "secondary"): set_view(v)
        
        elif cat == "Research & AI":
            for v in ["Backtester", "AI Insights", "AI Report Generator"]:
                if st.button(v, key=f"v_{v}", type="primary" if st.session_state['nav_view'] == v else "secondary"): set_view(v)

# --- VIEW ROUTER & RENDERING ---
ticker = st.session_state['current_ticker']
nav_view = st.session_state['nav_view']

# 1. CORE
if nav_view == "Home":
    st.subheader("🏠 Home Dashboard")
    
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
        
        # Split Layout: Heatmap + Watchlist | Widgets
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
                                fig = px.treemap(
                                    df_map, path=['Ticker'], values='Size', color='Change',
                                    color_continuous_scale='RdBu_r', range_color=[-3, 3],
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
        
        with col_side:
            with st.expander("Sidebar Widgets", expanded=True):
                 SidebarWidgets.render_indices()
                 st.markdown("---")
                 SidebarWidgets.render_trending()

    # --- JOURNAL ---
    with home_tabs[1]:
        with st.form("trade_log"):
            c1, c2 = st.columns(2)
            t_ticker = c1.text_input("Ticker", value=ticker)
            t_action = c2.selectbox("Action", ["Buy", "Sell"])
            c3, c4 = st.columns(2)
            t_price = c3.number_input("Price", min_value=0.0)
            t_shares = c4.number_input("Shares", min_value=1)
            t_notes = st.text_area("Notes")
            if st.form_submit_button("Log Trade"):
                journal.log_trade(t_ticker, t_action, t_price, t_shares, t_notes)
                st.success("Logged!")
        st.dataframe(journal.get_recent_trades(), use_container_width=True)

    # --- WATCHLISTS ---
    with home_tabs[2]:
        new_wl = st.text_input("New Watchlist Name")
        if st.button("Create Watchlist") and new_wl:
            wl_mgr.create_watchlist(new_wl)
            st.success(f"Created {new_wl}")

    # --- ALERTS ---
    with home_tabs[3]:
        st.dataframe(alert_engine.get_active_alerts(), use_container_width=True)

elif nav_view == "Chart":
    st.subheader(f"📈 Chart: {ticker}")
    TradingViewWidget.render(ticker)

elif nav_view == "News": render_sentiment_timeline(ticker)
elif nav_view == "Events": render_econ_impact_overlay(ticker)

# 2. TECHNICAL
elif nav_view == "Market Structure": render_market_structure(ticker)
elif nav_view == "FVG Scanner": render_fvg_scanner(ticker)
elif nav_view == "MTF Confluence": render_mtf_confluence(ticker)
elif nav_view == "Session Ranges": render_session_range(ticker)
elif nav_view == "Pre/Post Tracker": render_prepost_tracker(popular_tickers)
elif nav_view == "Targets": render_price_targets(ticker)
elif nav_view == "Range Analysis": render_range_dashboard(ticker)

# 3. VOLUME
elif nav_view == "Volume Profile (Legacy)":
    engine = VolumeProfileEngine(ticker, period, interval)
    engine.fetch_data(); engine.calculate_volume_profile()
    st.info("Legacy VP Engine Loaded.")
elif nav_view == "Order Flow":
    st.subheader("Order Flow TPO")
    try:
        mp = MarketProfileEngine(ticker)
        tpo = mp.calculate_tpo_profile()
        st.write(f"Day Type: {tpo['day_type']}" if tpo else "No Data")
    except: st.warning("TPO Calc Failed")
elif nav_view == "Liquidity Heatmap": render_liquidity_heatmap(ticker)
elif nav_view == "Session Analysis": st.write("Session Analysis Placeholder")

# 4. RISK
elif nav_view == "Portfolio Risk": render_portfolio_risk(ticker)
elif nav_view == "Earnings Volatility": render_earnings_volatility(ticker)
elif nav_view == "GARCH Forecast": render_garch_forecaster(ticker)
elif nav_view == "Vol Surface": render_vol_surface(ticker)
elif nav_view == "Options Chain": render_options_analytics(ticker)
elif nav_view == "Options Flow": st.info("Options Flow Placeholder")

# 5. FUNDAMENTAL
elif nav_view == "Valuation (DCF)": render_dcf_engine(ticker)
elif nav_view == "Valuation History": render_valuation_history(ticker)
elif nav_view == "Analyst Ratings": render_analyst_ratings(ticker)
elif nav_view == "Peers": render_peer_comparison(ticker)
elif nav_view == "Dividends": render_dividend_tracker(ticker)

# 6. INSTITUTIONAL
elif nav_view == "Institutional Ownership": render_institutional_tracker(ticker)
elif nav_view == "Insider Trading": render_insider_tracker(ticker)
elif nav_view == "Short Interest": render_short_interest(ticker)
elif nav_view == "Sentiment Timeline": render_sentiment_timeline(ticker)

# 7. QUANT
elif nav_view == "Regime Backtest": render_regime_backtest(ticker)
elif nav_view == "Pairs Trading": render_pairs_trading(ticker)
elif nav_view == "Rolling Beta": render_rolling_beta(ticker)
elif nav_view == "Factor Model": render_factor_model(ticker)
elif nav_view == "Correlation": st.info("Correlation Matrix Placeholder")

# 8. SCREENERS
elif nav_view == "Setup Scanner": render_setup_scanner(ticker)
elif nav_view == "Fundamental Screener": render_fundamental_screener()
elif nav_view == "RS Rating": render_rs_rating(ticker)
elif nav_view == "Watchlist Scoring":
    st.subheader("🏆 Watchlist Scoring")
    scorer = WatchlistScorer()
    default_tickers = ["NVDA", "AMD", "TSLA", "AAPL", "MSFT"]
    t_in = st.text_area("Tickers", value=", ".join(default_tickers))
    tickers = [t.strip().upper() for t in t_in.split(",") if t.strip()]
    if st.button("Run Scoring"):
        data = scorer.fetch_data(tickers)
        scores = scorer.calculate_scores(data)
        st.dataframe(scores, use_container_width=True)

# 9. RESEARCH
elif nav_view == "Backtester":
    # Simple placeholder or load legacy
    st.subheader("Backtester")
    st.info("Legacy Backtester UI")
elif nav_view == "AI Insights": st.info("AI Insights Placeholder")
elif nav_view == "AI Report Generator":
    st.subheader("📄 AI Report Generator")
    gen = AIReportGenerator()
    if st.button(f"Generate Report for {ticker}"):
        path = gen.generate_report(ticker, {})
        st.success(f"Report Generated: {path}")
