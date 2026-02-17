import streamlit as st
from streamlit_autorefresh import st_autorefresh
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
import pandas as pd
from datetime import datetime
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
from correlation import CorrelationAnalyzer
from news_feed import NewsFeedAnalyzer
from options_flow import OptionsFlowAnalyzer
from alerts_engine import AlertsEngine, WatchlistManager
from trade_journal import TradeJournal, TickerNotes, UserPreferences
import numpy as np

st.set_page_config(layout="wide", page_title="Volume Profile Terminal")

# --- Minimal Dark Theme CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }
    .main .block-container { padding: 1.2rem 2rem; max-width: 100%; }

    /* Sidebar */
    [data-testid="stSidebar"] { background: #0d1117; border-right: 1px solid #21262d; }
    [data-testid="stSidebar"][aria-expanded="true"] { min-width: 260px; }
    [data-testid="stSidebar"][aria-expanded="false"] { min-width: 0px; max-width: 0px; }
    section[data-testid="stSidebar"] > div { padding-top: 1rem; }

    /* Tab bar */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0; border-bottom: 1px solid #21262d;
        background: transparent; overflow-x: auto;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 18px; font-size: 13px; font-weight: 500;
        color: #7d8590; border-bottom: 2px solid transparent;
        white-space: nowrap;
    }
    .stTabs [data-baseweb="tab"]:hover { color: #e6edf3; }
    .stTabs [aria-selected="true"] {
        color: #e6edf3 !important; font-weight: 600;
        border-bottom: 2px solid #e6edf3 !important;
        background: transparent !important;
    }

    /* Metric cards */
    [data-testid="stMetric"] {
        background: #161b22; border: 1px solid #21262d;
        border-radius: 6px; padding: 12px 16px;
    }
    [data-testid="stMetricLabel"] { font-size: 11px !important; color: #7d8590 !important; text-transform: uppercase; letter-spacing: 0.5px; }
    [data-testid="stMetricValue"] { font-size: 20px !important; font-weight: 600 !important; }

    /* Buttons */
    .stButton > button {
        background: #21262d !important; color: #e6edf3 !important;
        border: 1px solid #30363d !important; border-radius: 6px;
        font-weight: 500; font-size: 13px; padding: 6px 16px;
    }
    .stButton > button:hover { background: #30363d !important; border-color: #8b949e !important; }

    /* Headers */
    h1, h2, h3 { font-weight: 600 !important; }
    h2 { font-size: 18px !important; }
    h3 { font-size: 15px !important; color: #c9d1d9 !important; }

    /* Dividers */
    hr { border-color: #21262d !important; }

    /* Download buttons */
    .stDownloadButton > button { background: transparent !important; border: 1px solid #30363d !important; }

    /* Expanders */
    .streamlit-expanderHeader { font-size: 13px !important; }

    /* Responsive */
    @media (max-width: 768px) {
        .main .block-container { padding: 0.5rem; }
        [data-testid="stSidebar"][aria-expanded="true"] { min-width: 100%; max-width: 100%; }
        .stTabs [data-baseweb="tab"] { padding: 8px 12px; font-size: 11px; }
    }
</style>
""", unsafe_allow_html=True)

# --- Ticker symbol mapping ---
# TradingView accepts symbols like XAUUSD, but Yahoo Finance uses different formats.
# This mapping converts common TradingView symbols to Yahoo Finance equivalents.
YAHOO_TICKER_MAP = {
    # Commodities
    'XAUUSD': 'GC=F',   'GOLD': 'GC=F',
    'XAGUSD': 'SI=F',   'SILVER': 'SI=F',
    'CRUDEOIL': 'CL=F', 'OIL': 'CL=F',   'USOIL': 'CL=F',
    'NGAS': 'NG=F',     'NATGAS': 'NG=F',
    # Futures
    'NQ': 'NQ=F',       'NQ1!': 'NQ=F',
    'ES': 'ES=F',       'ES1!': 'ES=F',
    'YM': 'YM=F',       'YM1!': 'YM=F',
    'RTY': 'RTY=F',     'RTY1!': 'RTY=F',
    # Forex
    'EURUSD': 'EURUSD=X',
    'GBPUSD': 'GBPUSD=X',
    'USDJPY': 'USDJPY=X',
    'AUDUSD': 'AUDUSD=X',
    'USDCAD': 'USDCAD=X',
    'USDCHF': 'USDCHF=X',
    'NZDUSD': 'NZDUSD=X',
    'EURJPY': 'EURJPY=X',
    'GBPJPY': 'GBPJPY=X',
    # Crypto
    'BTCUSD': 'BTC-USD',  'BITCOIN': 'BTC-USD', 'BTC': 'BTC-USD',
    'ETHUSD': 'ETH-USD',  'ETHEREUM': 'ETH-USD', 'ETH': 'ETH-USD',
    'SOLUSD': 'SOL-USD',  'SOL': 'SOL-USD',
    'XRPUSD': 'XRP-USD',  'XRP': 'XRP-USD',
    'DOGEUSD': 'DOGE-USD', 'DOGE': 'DOGE-USD',
    'LTCUSD': 'LTC-USD',  'LTC': 'LTC-USD',
}

# Reverse mapping: Yahoo Finance format -> TradingView format
# Handles cases where user types "GC=F" directly
TV_TICKER_MAP = {
    'GC=F': 'XAUUSD', 'SI=F': 'XAGUSD', 'CL=F': 'USOIL',
    'NG=F': 'NGAS',
    'NQ=F': 'NQ1!', 'ES=F': 'ES1!', 'YM=F': 'YM1!', 'RTY=F': 'RTY1!',
    'EURUSD=X': 'EURUSD', 'GBPUSD=X': 'GBPUSD', 'USDJPY=X': 'USDJPY',
    'AUDUSD=X': 'AUDUSD', 'USDCAD=X': 'USDCAD', 'USDCHF=X': 'USDCHF',
    'NZDUSD=X': 'NZDUSD', 'EURJPY=X': 'EURJPY', 'GBPJPY=X': 'GBPJPY',
    'BTC-USD': 'BTCUSD', 'ETH-USD': 'ETHUSD', 'SOL-USD': 'SOLUSD',
    'XRP-USD': 'XRPUSD', 'DOGE-USD': 'DOGEUSD', 'LTC-USD': 'LTCUSD',
}

# --- Sidebar Branding & Navigation ---
st.sidebar.markdown("""
<div style='display: flex; align-items: center; gap: 10px; margin-bottom: 20px;'>
    <h1 style='margin: 0; font-size: 22px;'>📊 VP Terminal</h1>
</div>
""", unsafe_allow_html=True)

# --- MARKET SELECTION SECTION ---
st.sidebar.subheader("Market Selection")

# Use st.selectbox with a text_input fallback for better UX
popular_tickers = ["SPY", "QQQ", "IWM", "AAPL", "TSLA", "NVDA", "AMD", "MSFT", "GOOGL", "AMZN", 
                   "BTCUSD", "ETHUSD", "XAUUSD", "CL=F", "EURUSD", "USDJPY"]

# Session Persistence for Ticker
if 'current_ticker' not in st.session_state:
    st.session_state['current_ticker'] = "SPY"

# Searchable dropdown with custom option
selected_ticker = st.sidebar.selectbox(
    "Ticker", options=popular_tickers + ["Custom"], 
    index=popular_tickers.index(st.session_state['current_ticker']) if st.session_state['current_ticker'] in popular_tickers else len(popular_tickers),
    key='ticker_select'
)

if selected_ticker == "Custom":
    raw_ticker = st.sidebar.text_input("Enter Ticker", value=st.session_state.get('last_custom', "SPY")).upper().strip()
    st.session_state['last_custom'] = raw_ticker
else:
    raw_ticker = selected_ticker

st.session_state['current_ticker'] = raw_ticker

# Translate for Yahoo Finance
yahoo_ticker = YAHOO_TICKER_MAP.get(raw_ticker, raw_ticker)

# Translate for TradingView (handle if user typed Yahoo format like GC=F)
tv_ticker = TV_TICKER_MAP.get(raw_ticker, raw_ticker)

# Show mapping info if translated
if yahoo_ticker != raw_ticker:
    st.sidebar.caption(f"Yahoo Finance: {yahoo_ticker}")

# Helper for callbacks
def set_ticker(t):
    st.session_state['current_ticker'] = t
    st.session_state['ticker_select'] = t if t in popular_tickers else "Custom"
    if t not in popular_tickers:
        st.session_state['last_custom'] = t
    # Update recent tickers logic here too if needed, but it depends on raw_ticker which is set later.
    # Actually, recent tickers update happens on the NEXT run when raw_ticker is read.
    # But if we click "Recent", we are selecting it.
    
# Quick Select Categories (Updates session state via callback)
with st.sidebar.expander("Quick Select", expanded=False):
    st.markdown("**Indices**")
    idx_cols = st.columns(3)
    for btn, col in [("SPY", idx_cols[0]), ("QQQ", idx_cols[1]), ("IWM", idx_cols[2])]:
        col.button(btn, key=f"q_{btn}", use_container_width=True, 
                   on_click=set_ticker, args=(btn,))
    
    st.markdown("**Tech**")
    tech_cols = st.columns(3)
    for btn, col in [("AAPL", tech_cols[0]), ("TSLA", tech_cols[1]), ("NVDA", tech_cols[2])]:
        col.button(btn, key=f"q_{btn}", use_container_width=True, 
                   on_click=set_ticker, args=(btn,))

    st.markdown("**Macro / Crypto**")
    macro_cols = st.columns(3)
    for btn, lbl, col in [("XAUUSD", "GOLD", macro_cols[0]), ("BTCUSD", "BTC", macro_cols[1]), ("ETHUSD", "ETH", macro_cols[2])]:
        col.button(lbl, key=f"q_{lbl}", use_container_width=True, 
                   on_click=set_ticker, args=(btn,))

# Recent Tickers
if 'recent_tickers' not in st.session_state:
    st.session_state['recent_tickers'] = []

if raw_ticker and raw_ticker not in st.session_state['recent_tickers']:
    st.session_state['recent_tickers'] = [raw_ticker] + st.session_state['recent_tickers'][:4]

if st.session_state['recent_tickers']:
    st.sidebar.caption("Recent:")
    rec_cols = st.sidebar.columns(len(st.session_state['recent_tickers']))
    for i, t in enumerate(st.session_state['recent_tickers']):
        rec_cols[i].button(t, key=f"rec_{t}", use_container_width=True, 
                           on_click=set_ticker, args=(t,))

st.sidebar.divider()
st.sidebar.subheader("Analysis Settings")

ticker = yahoo_ticker

# Full Persistence for Period/Interval
if 'period' not in st.session_state: st.session_state['period'] = "1mo"
if 'interval' not in st.session_state: st.session_state['interval'] = "15m"

period = st.sidebar.selectbox("Period", ["1d", "5d", "1mo", "3mo", "6mo", "1y"], 
                              index=["1d", "5d", "1mo", "3mo", "6mo", "1y"].index(st.session_state['period']),
                              key='sb_period')
interval = st.sidebar.selectbox("Interval", ["1m", "5m", "15m", "1h", "1d"], 
                                index=["1m", "5m", "15m", "1h", "1d"].index(st.session_state['interval']),
                                key='sb_interval')

# Update session state on change
if period != st.session_state['period']: st.session_state['period'] = period
if interval != st.session_state['interval']: st.session_state['interval'] = interval

# --- PRICE STRIP ---
@st.cache_data(ttl=5)
def get_quick_quote(t):
    try:
        info = yf.Ticker(t).fast_info
        price = info['last_price']
        prev = info['previous_close']
        change = (price - prev) / prev * 100
        return price, change
    except:
        return None, None

price_q, change_q = get_quick_quote(ticker if 'ticker' in dir() else raw_ticker)
if price_q is not None:
    clr = "#238636" if change_q >= 0 else "#da3633"
    st.sidebar.markdown(f"""
    <div style='background:#161b22;border:1px solid #21262d;border-radius:6px;padding:10px;margin:8px 0;'>
        <div style='font-size:11px;color:#8b949e;text-transform:uppercase;letter-spacing:.5px;'>Last Price</div>
        <div style='font-size:20px;font-weight:600;'>${price_q:.2f}
            <span style='font-size:13px;color:{clr};'>{change_q:+.2f}%</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- DASHBOARD ACTIONS ---
st.sidebar.divider()
st.sidebar.subheader("Actions")

# Detailed Status Indicator
import time
last_upd = time.strftime("%H:%M:%S")
st.sidebar.markdown(f"""
<div style='display:flex;align-items:center;justify-content:space-between;background:#0d1117;padding:5px 10px;border-radius:4px;border:1px solid #30363d;margin-bottom:10px;'>
    <span style='font-size:11px;color:#8b949e;'>DATA STATUS</span>
    <span style='font-size:11px;color:#238636;font-weight:600;'>● LIVE ({last_upd})</span>
</div>
""", unsafe_allow_html=True)

auto_refresh = st.sidebar.checkbox("Live Refresh (10s)", value=False)
if auto_refresh:
    st_autorefresh(interval=10000, limit=None, key="live_refresh")

# Keyboard Shortcuts (JS Injection)
st.components.v1.html("""
<script>
const doc = window.parent.document;
doc.addEventListener('keydown', function(e) {
    if (e.target.tagName !== 'INPUT' && e.target.tagName !== 'TEXTAREA') {
        if (e.key === '/') {
            e.preventDefault();
            const input = doc.querySelector('input[aria-label="Ticker"]') || doc.querySelector('input[aria-label="Enter Ticker"]');
            if (input) {
                input.focus();
                input.select();
            }
        }
    }
});
</script>
""", height=0)

# Initialize managers (used by My Dashboard tab)
alert_engine = AlertsEngine()
wl_mgr = WatchlistManager()

# Global Engine Instance
@st.cache_data(ttl=10)
def load_data(ticker, period, interval):
    engine = VolumeProfileEngine(ticker, period, interval)
    engine.fetch_data()
    engine.calculate_volume_profile()
    return engine

if st.sidebar.button("Run Analysis", use_container_width=True, type="primary"):
    st.session_state['run'] = True

# --- SIDEBAR FOOTER ---
st.sidebar.markdown("---")
_now = datetime.now()
_hr = _now.hour
_market = "Open" if 9 <= _hr < 16 else "Closed"
st.sidebar.caption(f"{_now.strftime('%H:%M')} · Market {_market}")
st.sidebar.markdown("<div style='font-size:10px;color:#484f58;'>VP Terminal v2.1 • Fixed</div>", unsafe_allow_html=True)

# --- TABS ---
(tab_my, tab_tv, tab1, tab2, tab_analytics, tab_tools, tab_news, tab_research) = st.tabs([
    "Home", "Chart", "Analysis", "Order Flow",
    "Analytics", "Tools", "News", "Research"
])

# --- TAB: HOME ---
with tab_my:

    journal = TradeJournal()
    notes_mgr = TickerNotes()
    user_prefs = UserPreferences()

    my_tabs = st.tabs(["Overview", "Watchlists", "Alerts", "Trade Journal",
                        "Ticker Notes", "Export", "Preferences"])

    # ---- OVERVIEW (Command Center) ----
    with my_tabs[0]:
        # Summary Cards Row
        active_alerts = alert_engine.get_active_alerts()
        triggered_alerts = alert_engine.get_triggered_alerts()
        journal_stats = journal.get_stats()

        ov1, ov2, ov3, ov4 = st.columns(4)
        ov1.metric("Active Alerts", len(active_alerts) if active_alerts else 0)
        ov2.metric("Triggered Today", len(triggered_alerts) if triggered_alerts else 0)
        ov3.metric("Win Rate", f"{journal_stats.get('win_rate', 0)}%")
        ov4.metric("Total Trades", journal_stats.get('total_trades', 0))

        st.markdown("---")

        # Watchlist Sparklines
        st.markdown("### Watchlist Overview")
        wl_names_ov = wl_mgr.get_names()
        if wl_names_ov:
            selected_wl = st.selectbox("Watchlist", wl_names_ov, key="ov_wl_select")
            wl_tickers_ov = wl_mgr.get_tickers(selected_wl)

            if wl_tickers_ov:
                spark_cols = st.columns(min(len(wl_tickers_ov), 4))
                for i, wt in enumerate(wl_tickers_ov[:8]):
                    col_idx = i % min(len(wl_tickers_ov), 4)
                    with spark_cols[col_idx]:
                        try:
                            yf_t = YAHOO_TICKER_MAP.get(wt.upper(), wt.upper())
                            spark_data = yf.download(yf_t, period="5d", interval="1h", progress=False)
                            if not spark_data.empty:
                                close = spark_data['Close']
                                if hasattr(close, 'columns'):
                                    close = close.iloc[:, 0]
                                last_p = float(close.iloc[-1])
                                first_p = float(close.iloc[0])
                                chg = (last_p - first_p) / first_p * 100
                                clr_s = "#238636" if chg >= 0 else "#da3633"

                                fig_spark = go.Figure(go.Scatter(
                                    y=close.values, mode='lines',
                                    line=dict(color=clr_s, width=1.5),
                                    fill='tozeroy',
                                    fillcolor=f"rgba({'35,134,54' if chg >= 0 else '218,54,51'},0.1)"
                                ))
                                fig_spark.update_layout(
                                    height=80, margin=dict(l=0,r=0,t=0,b=0),
                                    xaxis=dict(visible=False), yaxis=dict(visible=False),
                                    template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)',
                                    plot_bgcolor='rgba(0,0,0,0)'
                                )
                                st.markdown(f"**{wt}** · ${last_p:.2f} <span style='color:{clr_s};font-size:12px;'>{chg:+.1f}%</span>", unsafe_allow_html=True)
                                st.plotly_chart(fig_spark, use_container_width=True, key=f"spark_{wt}")
                            else:
                                st.caption(f"{wt}: No data")
                        except Exception:
                            st.caption(f"{wt}: Error")
                            st.caption(f"{wt}: Error")
        else:
            st.info("No watchlists yet. Create one in the Watchlists tab.")

        st.markdown("---")
        st.markdown("### Portfolio Heatmap")
        
        @st.cache_data(ttl=60)
        def get_heatmap_data_v2(tickers):
            data = []
            for t in tickers:
                try:
                    yf_t = YAHOO_TICKER_MAP.get(t.upper(), t.upper())
                    info = yf.Ticker(yf_t).fast_info
                    
                    # 1. Get Market Cap / Size (Handle ETFs)
                    mcap = info.get('market_cap')
                    if mcap is None:
                        mcap = info.get('totalAssets')
                    if mcap is None:
                        mcap = 1e9  # Default to 1B
                    
                    # 2. Get Price Change
                    price = info.get('last_price')
                    prev = info.get('previous_close')
                    
                    if price and prev:
                        change = (price - prev) / prev * 100
                        data.append({
                            'Ticker': t,
                            'Change': change,
                            'Market Cap': mcap,
                            'Abs Change': abs(change),
                            'Color': 'Green' if change >= 0 else 'Red'
                        })
                except Exception as e:
                    # st.write(f"Error fetching {t}: {e}") # Debug
                    pass
            return pd.DataFrame(data)

        if wl_names_ov and wl_tickers_ov:
            with st.spinner("Generating heatmap..."):
                hm_df = get_heatmap_data_v2(wl_tickers_ov)
                if not hm_df.empty:
                    fig_hm = px.treemap(
                        hm_df, path=['Ticker'], values='Market Cap',
                        color='Change', color_continuous_scale='RdYlGn',
                        color_continuous_midpoint=0,
                        hover_data=['Change', 'Market Cap'],
                        title=f"Market Performance ({selected_wl})"
                    )
                    fig_hm.update_layout(height=400, template='plotly_dark')
                    fig_hm.data[0].textinfo = 'label+text+value'
                    fig_hm.data[0].texttemplate = "%{label}<br>%{customdata[0]:.2f}%"
                    st.plotly_chart(fig_hm, use_container_width=True)
                else:
                    st.info("Insufficient data for heatmap. Check internet or ticker symbols.")

    # ---- WATCHLIST MANAGER ----
    with my_tabs[1]:
        st.markdown("### Watchlist Manager")
        wl_names_my = wl_mgr.get_names()

        wl_col1, wl_col2 = st.columns([1, 2])
        with wl_col1:
            st.markdown("**Your Watchlists**")
            for name in wl_names_my:
                tickers_list = wl_mgr.get_tickers(name)
                with st.expander(f"{name} ({len(tickers_list)})"):
                    st.write(", ".join(tickers_list))
                    remove_t = st.text_input(f"Remove ticker from {name}", key=f"rm_{name}")
                    if st.button("Remove", key=f"rmbtn_{name}"):
                        if remove_t:
                            wl_mgr.remove_ticker(name, remove_t)
                            st.rerun()
                    if st.button(f"Delete '{name}'", key=f"del_{name}"):
                        wl_mgr.delete(name)
                        st.rerun()

        with wl_col2:
            st.markdown("**Create / Edit Watchlist**")
            wl_new_name = st.text_input("Watchlist Name", key='my_wl_name')
            wl_new_tickers = st.text_area("Tickers (one per line or comma-separated)",
                                           key='my_wl_tickers', height=100)
            if st.button("Save Watchlist", key='my_wl_save'):
                if wl_new_name and wl_new_tickers:
                    t_list = [t.strip() for t in wl_new_tickers.replace('\n', ',').split(',') if t.strip()]
                    wl_mgr.create(wl_new_name, t_list)
                    st.success(f"Saved '{wl_new_name}' with {len(t_list)} tickers")
                    st.rerun()

    # ---- ALERTS MANAGER ----
    with my_tabs[2]:
        st.markdown("### Alerts Manager")

        al_col1, al_col2 = st.columns(2)
        with al_col1:
            st.markdown("**Add New Alert**")
            al_ticker = st.text_input("Ticker", value=raw_ticker, key='my_al_tick')
            al_type = st.selectbox("Alert Type",
                ['PRICE_ABOVE', 'PRICE_BELOW', 'VAH_BREAK', 'VAL_BREAK', 'POC_TOUCH'],
                key='my_al_type')
            al_price = st.number_input("Price Level", value=0.0, step=0.01, key='my_al_price')
            al_note = st.text_input("Note (optional)", key='my_al_note')
            if st.button("Create Alert", key='my_al_create'):
                if al_price > 0:
                    alert_engine.add_alert(al_ticker, al_type,
                        f"{al_ticker} {al_type} {al_price}", al_price, al_note)
                    st.success(f"Alert created: {al_ticker} {al_type} at ${al_price:.2f}")

        with al_col2:
            st.markdown("**Active Alerts**")
            active_alerts = alert_engine.get_active_alerts()
            if active_alerts:
                for a in active_alerts:
                    c1, c2 = st.columns([4, 1])
                    c1.caption(f"#{a['id']} {a['ticker']} | {a['type']} | ${a['price']:.2f} | {a.get('note', '')}")
                    if c2.button("X", key=f"del_al_{a['id']}"):
                        alert_engine.delete_alert(a['id'])
                        st.rerun()
            else:
                st.info("No active alerts.")

            st.markdown("**Triggered Alerts (History)**")
            triggered = alert_engine.get_triggered_alerts()
            if triggered:
                for t in triggered:
                    st.caption(f"#{t['id']} {t['ticker']} {t['type']} ${t['price']:.2f} — triggered {t.get('triggered_at', '')}")
                if st.button("Clear History", key='clear_triggered'):
                    alert_engine.clear_triggered()
                    st.rerun()
            else:
                st.caption("No triggered alerts yet.")

    # ---- TRADE JOURNAL ----
    with my_tabs[3]:
        st.markdown("### Trade Journal")

        # Performance stats
        stats = journal.get_stats()
        if stats['total_trades'] > 0:
            s1, s2, s3, s4, s5, s6 = st.columns(6)
            s1.metric("Total Trades", stats['total_trades'])
            s2.metric("Win Rate", f"{stats['win_rate']}%")
            s3.metric("Total P&L", f"${stats['total_pnl']:,.2f}")
            s4.metric("Avg P&L", f"${stats['avg_pnl']:,.2f}")
            s5.metric("Profit Factor", f"{stats['profit_factor']:.2f}")
            s6.metric("Best / Worst", f"${stats['best_trade']:,.2f} / ${stats['worst_trade']:,.2f}")

            # Equity curve
            if stats['equity_curve']:
                eq_df = pd.DataFrame(stats['equity_curve'])
                fig_eq = go.Figure(go.Scatter(
                    x=eq_df['date'], y=eq_df['equity'],
                    mode='lines+markers', line=dict(color='cyan', width=2),
                    fill='tozeroy', fillcolor='rgba(0,255,255,0.1)'
                ))
                fig_eq.update_layout(
                    height=300, template='plotly_dark',
                    title='Equity Curve', yaxis_title='Cumulative P&L ($)',
                    margin=dict(l=40, r=20, t=40, b=30)
                )
                st.plotly_chart(fig_eq, use_container_width=True)

            # Trade table
            if journal.get_all_trades():
                st.markdown("---")
                trades_df = pd.DataFrame(journal.get_all_trades())
                display_cols = ['id', 'ticker', 'direction', 'entry_price', 'exit_price',
                               'size', 'pnl', 'pnl_pct', 'result', 'strategy', 'exit_date']
                display_cols = [c for c in display_cols if c in trades_df.columns]
                st.dataframe(trades_df[display_cols], use_container_width=True,
                    column_config={
                        'entry_price': st.column_config.NumberColumn('Entry', format='$%.2f'),
                        'exit_price': st.column_config.NumberColumn('Exit', format='$%.2f'),
                        'pnl': st.column_config.NumberColumn('P&L', format='$%.2f'),
                        'pnl_pct': st.column_config.NumberColumn('P&L %', format='%.2f%%'),
                    }
                )
        else:
            st.info("No trades logged yet. Add your first trade below.")

        # Add trade form
        st.markdown("---")
        st.markdown("**Log a Trade**")
        tc1, tc2, tc3, tc4 = st.columns(4)
        j_ticker = tc1.text_input("Ticker", value=raw_ticker, key='j_ticker')
        j_dir = tc2.selectbox("Direction", ['LONG', 'SHORT'], key='j_dir')
        j_entry = tc3.number_input("Entry Price", value=0.0, step=0.01, key='j_entry')
        j_exit = tc4.number_input("Exit Price", value=0.0, step=0.01, key='j_exit')

        tc5, tc6, tc7, tc8 = st.columns(4)
        j_size = tc5.number_input("Size (shares/contracts)", value=1.0, step=1.0, key='j_size')
        j_strat = tc6.text_input("Strategy", key='j_strat')
        j_edate = tc7.text_input("Entry Date (YYYY-MM-DD)", key='j_edate')
        j_xdate = tc8.text_input("Exit Date (YYYY-MM-DD)", key='j_xdate')

        j_notes = st.text_area("Trade Notes", key='j_notes', height=60)

        if st.button("Log Trade", key='j_log'):
            if j_entry > 0 and j_exit > 0:
                journal.add_trade(j_ticker, j_dir, j_entry, j_exit, j_size,
                                  j_edate, j_xdate, j_strat, j_notes)
                st.success(f"Trade logged!")
                st.rerun()
            else:
                st.warning("Enter valid entry and exit prices.")

        if stats['total_trades'] > 0:
            if st.button("Clear All Trades", key='j_clear'):
                journal.clear_all()
                st.rerun()

    # ---- TICKER NOTES ----
    with my_tabs[4]:
        st.markdown("### Ticker Notes")
        st.caption("Save personal analysis notes for any ticker. These persist across sessions.")

        note_ticker = st.text_input("Ticker", value=raw_ticker, key='note_ticker')
        existing_note = notes_mgr.get_note(note_ticker)
        note_text = st.text_area("Your Notes", value=existing_note, height=200, key='note_text')

        nc1, nc2 = st.columns(2)
        if nc1.button("Save Note", key='note_save'):
            notes_mgr.save_note(note_ticker, note_text)
            st.success(f"Note saved for {note_ticker}")

        if nc2.button("Delete Note", key='note_del'):
            notes_mgr.delete_note(note_ticker)
            st.success(f"Note deleted for {note_ticker}")
            st.rerun()

        # Show all notes
        all_notes = notes_mgr.get_all()
        if all_notes:
            st.markdown("---")
            st.markdown("**All Saved Notes**")
            for tk, nt in all_notes.items():
                with st.expander(tk):
                    st.write(nt)

    # ---- EXPORT CENTER ----
    with my_tabs[5]:
        st.markdown("### Export Center")
        st.caption("Download your data as CSV files.")

        ex_col1, ex_col2 = st.columns(2)
        with ex_col1:
            st.markdown("**Trade Journal Export**")
            csv_data = journal.export_csv()
            st.download_button(
                "Download Trade Journal (CSV)",
                csv_data,
                file_name=f"trade_journal_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                key='exp_journal'
            )

        with ex_col2:
            st.markdown("**VP Levels Export**")
            try:
                if data_loaded and metrics:
                    levels_csv = f"Metric,Value\nPOC,{metrics['poc']:.2f}\nVAH,{metrics['vah']:.2f}\nVAL,{metrics['val']:.2f}\nCurrent Price,{metrics['current_price']:.2f}\nPosition,{metrics['position']}"
                    st.download_button(
                        "Download VP Levels (CSV)",
                        levels_csv,
                        file_name=f"{ticker}_levels_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv",
                        key='exp_levels'
                    )
                else:
                    st.caption("Run analysis first to export VP levels.")
            except NameError:
                st.caption("Run analysis first to export VP levels.")

    # ---- PREFERENCES ----
    with my_tabs[6]:
        st.markdown("### User Preferences")
        st.caption("Set your defaults. These are saved locally and persist across sessions.")

        current_prefs = user_prefs.get_all()

        pf_col1, pf_col2 = st.columns(2)
        with pf_col1:
            pf_ticker = st.text_input("Default Ticker", value=current_prefs.get('default_ticker', 'SPY'), key='pf_ticker')
            pf_period = st.selectbox("Default Period", ["1d", "5d", "1mo", "3mo", "6mo", "1y"],
                                      index=["1d", "5d", "1mo", "3mo", "6mo", "1y"].index(current_prefs.get('default_period', '1mo')),
                                      key='pf_period')
            pf_interval = st.selectbox("Default Interval", ["1m", "5m", "15m", "1h", "1d"],
                                        index=["1m", "5m", "15m", "1h", "1d"].index(current_prefs.get('default_interval', '15m')),
                                        key='pf_interval')

        with pf_col2:
            pf_refresh = st.checkbox("Auto-Refresh by Default", value=current_prefs.get('auto_refresh', False), key='pf_refresh')
            pf_rate = st.number_input("Refresh Rate (seconds)", value=current_prefs.get('refresh_rate', 10),
                                       min_value=5, max_value=60, key='pf_rate')

        if st.button("Save Preferences", key='pf_save'):
            user_prefs.save_all({
                'default_ticker': pf_ticker,
                'default_period': pf_period,
                'default_interval': pf_interval,
                'auto_refresh': pf_refresh,
                'refresh_rate': pf_rate,
            })
            st.success("Preferences saved! They will apply on next page load.")

# --- TAB TV: TRADINGVIEW PROFESSIONAL CHART ---
with tab_tv:
    tv_col1, tv_col2 = st.columns([3, 1])
    with tv_col1:
        st.caption("Use drawing tools & indicators from the chart toolbar. Click symbol name to search.")
    with tv_col2:
        tv_interval = st.selectbox(
            "Timeframe",
            options=['1m', '5m', '15m', '30m', '1h', '4h', '1d', '1w'],
            index=2,
            key='tv_timeframe'
        )

    TradingViewWidget.render_chart(
        symbol=tv_ticker,
        interval=tv_interval,
        height=800,
        theme='dark',
        show_volume_profile=False,
        allow_symbol_change=True
    )

data_loaded = False
if 'run' in st.session_state:
    try:
        with st.spinner(f"Analyzing {ticker}..."):
            engine = load_data(ticker, period, interval)
            if engine.data is None or engine.data.empty:
                raise ValueError(f"No data returned for '{ticker}'. Check the ticker symbol.")
            metrics = engine.get_all_metrics()
            df = engine.data
            profile = engine.volume_profile
            data_loaded = True

            # Phase 5: Advanced Analytics
            daily_profiles = engine.get_daily_profiles(days=5)
            if len(daily_profiles) >= 2:
                comp = ProfileComparator(ticker).compare_yesterday_today()
            else:
                comp = {}

            tracker = ValueAreaMigrationTracker(ticker, lookback_days=10).track_migration()

            # Volume Anomalies
            vol_mean = df['Volume'].mean()
            vol_std = df['Volume'].std()

    except Exception as e:
        st.warning(f"Data loading failed for '{ticker}': {e}. Chart tab still works.")
        data_loaded = False

# --- TAB 1: MARKET ANALYSIS ---
with tab1:
    if not data_loaded:
        st.info("Open sidebar, enter a ticker, and click Run Analysis.")
    else:
        # 1. Metrics Row
        col1, col2, col3, col4 = st.columns(4)
    
        pos_color = "green" if "ABOVE" in metrics['position'] else "red" if "BELOW" in metrics['position'] else "orange"
    
        col1.metric("Current Price", f"${metrics['current_price']:.2f}", 
                    delta=f"{metrics['distance_from_poc_pct']:.2f}% from POC")
    
        # Phase 7: Comparator
        comp_delta = f"{comp['shift']['poc_shift_pct']:.2f}%" if 'shift' in comp else "N/A"
        col2.metric("POC Profile Shift", f"${metrics['poc']:.2f}", delta=comp_delta, delta_color="normal",
                    help=comp.get('shift', {}).get('interpretation', 'No data'))
    
        # Phase 7: Migration Tracker
        if 'trend' in tracker:
            trend_color = "green" if tracker['trend'] == "UPTREND" else "red" if tracker['trend'] == "DOWNTREND" else "gray"
            col3.markdown(f"**Migration:** :{trend_color}[{tracker['trend']}]")
            st.caption(f"Str: {tracker.get('strength')}% | Vel: {tracker.get('velocity')}%")
        else:
            col3.metric("Migration", "N/A")
    
        col4.markdown(f"**Position:** :{pos_color}[{metrics['position']}]")

        # Level Export
        with st.expander("Key Levels", expanded=False):
            lev_cols = st.columns(3)
            lev_cols[0].metric("POC", f"${metrics['poc']:.2f}")
            lev_cols[1].metric("VAH", f"${metrics['vah']:.2f}")
            lev_cols[2].metric("VAL", f"${metrics['val']:.2f}")
            levels_txt = f"POC: {metrics['poc']:.2f} | VAH: {metrics['vah']:.2f} | VAL: {metrics['val']:.2f}"
            st.code(levels_txt, language=None)

        # Comparison Mode
        if st.checkbox("Compare with...", key='comp_mode'):
            st.markdown("#### Comparison Analysis")
            c_col1, c_col2, c_col3 = st.columns(3)
            c_ticker = c_col1.text_input("Comp Ticker", value=ticker, key='c_ticker').upper()
            c_period = c_col2.selectbox("Comp Period", ["1d", "5d", "1mo", "3mo", "6mo"], index=2, key='c_period')
            c_interval = c_col3.selectbox("Comp Interval", ["5m", "15m", "1h", "1d"], index=2, key='c_interval')

            if st.button("Run Comparison"):
                with st.spinner(f"Comparing with {c_ticker}..."):
                    try:
                        # Use a separate engine for comparison
                        c_engine = VolumeProfileEngine(c_ticker, c_period, c_interval)
                        c_engine.fetch_data()
                        c_engine.calculate_volume_profile()
                        c_metrics = c_engine.get_all_metrics()
                        
                        # Comparison Table
                        st.markdown(f"**VS {c_ticker} ({c_period})**")
                        comp_data = {
                            "Metric": ["Price", "POC", "VA Width", "Total Vol"],
                            f"Current ({ticker})": [
                                f"${metrics['current_price']:.2f}",
                                f"${metrics['poc']:.2f}",
                                f"{metrics['va_width_pct']:.2f}%",
                                f"{metrics['total_volume']:,}"
                            ],
                            f"Comp ({c_ticker})": [
                                f"${c_metrics['current_price']:.2f}",
                                f"${c_metrics['poc']:.2f}",
                                f"{c_metrics['va_width_pct']:.2f}%",
                                f"{c_metrics['total_volume']:,}"
                            ],
                            "Delta": [
                                f"{(metrics['current_price'] - c_metrics['current_price']):.2f}",
                                f"{(metrics['poc'] - c_metrics['poc']):.2f}",
                                f"{(metrics['va_width_pct'] - c_metrics['va_width_pct']):.2f}%",
                                f"{(metrics['total_volume'] - c_metrics['total_volume']):,}"
                            ]
                        }
                        st.dataframe(pd.DataFrame(comp_data), hide_index=True, use_container_width=True)

                    except Exception as e:
                        st.error(f"Comparison failed: {e}")

        # Toast notification
        st.toast(f"Analysis complete for {ticker}", icon="✅")

        # 2. Charts
        # Create subplots: Price on top, Volume on bottom
        fig = make_subplots(rows=2, cols=2, shared_xaxes=True, 
                            vertical_spacing=0.05, 
                            row_heights=[0.7, 0.3],
                            column_widths=[0.8, 0.2],
                            horizontal_spacing=0.02,
                            specs=[[{}, {"rowspan": 2}],
                                   [{}, None]]) # Profile on right sidebar spanning both rows

        # Candlestick
        fig.add_trace(go.Candlestick(x=df.index,
                                     open=df['Open'], high=df['High'],
                                     low=df['Low'], close=df['Close'],
                                     name='Price'), row=1, col=1)

        # Key Levels Lines
        # Phase 5: POC Zone (Not just a line)
        fig.add_hrect(y0=metrics['poc']*0.998, y1=metrics['poc']*1.002, 
                      line_width=0, fillcolor="orange", opacity=0.2, annotation_text="POC Zone", row=1, col=1)
    
        fig.add_hline(y=metrics['vah'], line_dash="dash", line_color="green", annotation_text="VAH", row=1, col=1)
        fig.add_hline(y=metrics['val'], line_dash="dash", line_color="red", annotation_text="VAL", row=1, col=1)
    
        # Phase 5: Previous Day's Levels (Comparison)
        if len(daily_profiles) >= 2:
            yest = daily_profiles[-2] # Last one is today, -2 is yesterday
            fig.add_hline(y=yest['poc'], line_dash="dot", line_color="gray", opacity=0.5, annotation_text="Y-POC", row=1, col=1)
            fig.add_hline(y=yest['vah'], line_dash="dot", line_color="gray", opacity=0.5, annotation_text="Y-VAH", row=1, col=1)
            fig.add_hline(y=yest['val'], line_dash="dot", line_color="gray", opacity=0.5, annotation_text="Y-VAL", row=1, col=1)

        # Volume Bars (Phase 5: Anomaly Detection)
        # Color bar yellow if volume > 2 std dev
        colors = []
        for i, r in df.iterrows():
            if r['Volume'] > (vol_mean + 2 * vol_std):
                colors.append('yellow') # Anomaly
            elif r['Close'] > r['Open']:
                colors.append('green')
            else:
                colors.append('red')

        fig.add_trace(go.Bar(x=df.index, y=df['Volume'], marker_color=colors, name='Volume'), row=2, col=1)

        # Volume Profile (Horizontal Histogram)
        # Volume Profile (Horizontal Histogram)
        # Highlight Value Area
        colors_vp = ['green' if metrics['val'] <= p <= metrics['vah'] else 'gray' for p in profile['price']]
        fig.add_trace(go.Bar(x=profile['volume'], y=profile['price'], orientation='h', 
                             marker_color=colors_vp, name='Profile', opacity=0.6), row=1, col=2)

        fig.update_layout(height=900, xaxis_rangeslider_visible=False, title=f"{ticker} Volume Profile Analysis")
        st.plotly_chart(fig, use_container_width=True)

        # --- AI ANALYSIS REPORT ---
        st.markdown("---")
        st.subheader("AI Analysis Report")
        try:
            report_gen = AIReportGenerator(metrics, ticker)

            # Try to get patterns if available
            try:
                from pattern_detector import ProfilePatternDetector
                pat_det = ProfilePatternDetector(profile, df)
                patterns = pat_det.detect_all_patterns()
            except Exception:
                patterns = None

            report_text = report_gen.generate(patterns=patterns)
            st.markdown(report_text)

            # Download button
            download_text = report_gen.generate_downloadable(patterns=patterns)
            st.download_button(
                "Download Report (.txt)",
                download_text,
                file_name=f"{ticker}_analysis_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                mime="text/plain"
            )
        except Exception as e:
            st.warning(f"Could not generate AI report: {e}")


# --- TAB 2: ORDER FLOW ---
with tab2:
    if not data_loaded:
        st.info("Run Analysis to view Order Flow data.")
    else:
        st.subheader("Order Flow Analysis")

        of_period = st.selectbox("Order Flow Period", ['1d', '5d', '1mo'], index=1, key='of_period')

        if st.button("Analyze Order Flow"):
            with st.spinner("Running order flow analysis..."):
                try:
                    from order_flow import OrderFlowEngine

                    of_engine = OrderFlowEngine(ticker, period=of_period, interval='15m')
                    of_engine.fetch_data()
                    of_result = of_engine.analyze()
                    s = of_result.summary

                    # --- Summary Metrics ---
                    st.markdown("### Flow Summary")
                    sm1, sm2, sm3, sm4 = st.columns(4)
                    control_color = "green" if s['overall_control'] == 'BUYERS' else "red"
                    sm1.metric("Overall Control", s['overall_control'])
                    sm2.metric("Buy %", f"{s['buy_pct']}%")
                    sm3.metric("VWAP", f"${s['vwap']:.2f}")
                    sm4.metric("Position", s['vwap_position'])

                    sm5, sm6, sm7, sm8 = st.columns(4)
                    sm5.metric("Net Delta", f"{s['net_delta']:,}")
                    sm6.metric("Recent Control", s['recent_control'])
                    sm7.metric("CVD Trend", s['cvd_trend'])
                    sm8.metric("Divergence", s['divergence_type'])

                    # --- 1. VWAP + SD Chart ---
                    st.markdown("---")
                    st.markdown("### VWAP + Standard Deviation Bands")
                    st.caption("VWAP = institutional fair value. Price above VWAP = bullish, below = bearish. SD bands act as support/resistance.")

                    delta_df = of_result.delta
                    fig_vwap = go.Figure()
                    fig_vwap.add_trace(go.Candlestick(
                        x=delta_df.index, open=delta_df['Open'], high=delta_df['High'],
                        low=delta_df['Low'], close=delta_df['Close'], name='Price'
                    ))
                    fig_vwap.add_trace(go.Scatter(
                        x=delta_df.index, y=delta_df['VWAP'],
                        line=dict(color='yellow', width=2), name='VWAP'
                    ))
                    fig_vwap.add_trace(go.Scatter(
                        x=delta_df.index, y=delta_df['VWAP_1SD_Upper'],
                        line=dict(color='rgba(0,200,255,0.4)', width=1, dash='dash'), name='+1 SD'
                    ))
                    fig_vwap.add_trace(go.Scatter(
                        x=delta_df.index, y=delta_df['VWAP_1SD_Lower'],
                        line=dict(color='rgba(0,200,255,0.4)', width=1, dash='dash'), name='-1 SD',
                        fill='tonexty', fillcolor='rgba(0,200,255,0.05)'
                    ))
                    fig_vwap.add_trace(go.Scatter(
                        x=delta_df.index, y=delta_df['VWAP_2SD_Upper'],
                        line=dict(color='rgba(255,100,100,0.4)', width=1, dash='dot'), name='+2 SD'
                    ))
                    fig_vwap.add_trace(go.Scatter(
                        x=delta_df.index, y=delta_df['VWAP_2SD_Lower'],
                        line=dict(color='rgba(255,100,100,0.4)', width=1, dash='dot'), name='-2 SD',
                        fill='tonexty', fillcolor='rgba(255,100,100,0.03)'
                    ))
                    fig_vwap.update_layout(
                        height=500, xaxis_rangeslider_visible=False,
                        template='plotly_dark', title=f'{ticker} VWAP + SD Bands'
                    )
                    st.plotly_chart(fig_vwap, use_container_width=True)

                    # --- 2. Delta + CVD Chart ---
                    st.markdown("---")
                    st.markdown("### Delta Analysis + Cumulative Volume Delta")
                    st.caption("Delta = buy volume minus sell volume per bar. CVD = running total. Rising CVD = buyer dominance.")

                    fig_delta = make_subplots(
                        rows=2, cols=1, shared_xaxes=True,
                        row_heights=[0.5, 0.5],
                        subplot_titles=['Bar Delta (Buy - Sell Volume)', 'Cumulative Volume Delta (CVD)']
                    )

                    delta_colors = ['green' if d >= 0 else 'red' for d in delta_df['Delta']]
                    fig_delta.add_trace(go.Bar(
                        x=delta_df.index, y=delta_df['Delta'],
                        marker_color=delta_colors, name='Delta', opacity=0.8
                    ), row=1, col=1)

                    fig_delta.add_trace(go.Scatter(
                        x=delta_df.index, y=delta_df['CVD'],
                        line=dict(color='cyan', width=2), name='CVD',
                        fill='tozeroy', fillcolor='rgba(0,255,255,0.1)'
                    ), row=2, col=1)

                    fig_delta.update_layout(height=600, template='plotly_dark')
                    st.plotly_chart(fig_delta, use_container_width=True)

                    # --- 3. Buy/Sell by Price Level ---
                    st.markdown("---")
                    st.markdown("### Buy/Sell Volume by Price Level")
                    st.caption("Shows who controls each price level. Green = buyer control, red = seller control.")

                    bs_data = of_engine.get_buy_sell_by_price(25)
                    if not bs_data.empty:
                        fig_bs = go.Figure()
                        fig_bs.add_trace(go.Bar(
                            y=bs_data['price'], x=bs_data['buy_volume'],
                            orientation='h', name='Buy Volume',
                            marker_color='rgba(0,200,100,0.7)'
                        ))
                        fig_bs.add_trace(go.Bar(
                            y=bs_data['price'], x=-bs_data['sell_volume'],
                            orientation='h', name='Sell Volume',
                            marker_color='rgba(255,80,80,0.7)'
                        ))
                        fig_bs.update_layout(
                            height=500, template='plotly_dark', barmode='overlay',
                            title='Buy vs Sell Volume at Each Price',
                            xaxis_title='Volume (Buy positive, Sell negative)',
                            yaxis_title='Price'
                        )
                        st.plotly_chart(fig_bs, use_container_width=True)

                    # --- 4. Large Blocks ---
                    st.markdown("---")
                    st.markdown("### Large Block Detection (Institutional Footprint)")
                    st.caption("Bars with volume > 2x standard deviations above average. EXTREME = 3x+ SD.")

                    if not of_result.large_blocks.empty:
                        lb = of_result.large_blocks.copy()
                        lb.index = lb.index.strftime('%Y-%m-%d %H:%M') if hasattr(lb.index, 'strftime') else lb.index
                        st.dataframe(
                            lb, use_container_width=True,
                            column_config={
                                'Close': st.column_config.NumberColumn('Price', format='$%.2f'),
                                'Volume': st.column_config.NumberColumn('Volume', format='%d'),
                                'Vol_Multiple': st.column_config.NumberColumn('x Avg', format='%.1fx'),
                                'Price_Impact': st.column_config.NumberColumn('Impact %', format='%.3f%%'),
                                'Delta': st.column_config.NumberColumn('Delta', format='%d'),
                            }
                        )
                    else:
                        st.info("No large blocks detected in this period.")

                    # --- 5. Absorption Events ---
                    st.markdown("---")
                    st.markdown("### Absorption Detection")
                    st.caption("High volume + no price movement = hidden buying/selling. Strong reversal signal.")

                    if not of_result.absorption.empty:
                        ab = of_result.absorption.copy()
                        ab.index = ab.index.strftime('%Y-%m-%d %H:%M') if hasattr(ab.index, 'strftime') else ab.index
                        st.dataframe(
                            ab, use_container_width=True,
                            column_config={
                                'Close': st.column_config.NumberColumn('Price', format='$%.2f'),
                                'Volume': st.column_config.NumberColumn('Volume', format='%d'),
                                'Vol_Multiple': st.column_config.NumberColumn('x Avg', format='%.1fx'),
                                'Range': st.column_config.NumberColumn('Range', format='$%.4f'),
                                'Range_Ratio': st.column_config.NumberColumn('Range Ratio', format='%.2fx'),
                                'Delta': st.column_config.NumberColumn('Delta', format='%d'),
                            }
                        )
                    else:
                        st.info("No absorption events detected in this period.")

                except Exception as e:
                    st.error(f"Order Flow Error: {e}")

# --- TAB: ANALYTICS (Advanced + Multi-TF + Correlation + Watchlist) ---
with tab_analytics:
    if not data_loaded:
        st.info("Run Analysis to view Analytics data.")
    else:
        analytics_sub = st.tabs(["Advanced", "Multi-TF", "Correlation", "Watchlist"])
        with analytics_sub[0]:
            st.subheader("Advanced Volume & Market Profile Analytics")
            adv_tabs = st.tabs(["Market Profile (TPO)", "Composite Profiles", "Volume Nodes", "Patterns & Stats"])
    
            # 1. Market Profile (TPO)
            with adv_tabs[0]:
                st.markdown("### Market Profile (TPO)")
                try:
                    mp_engine = MarketProfileEngine(ticker)
                    tpo_data = mp_engine.calculate_tpo_profile()
            
                    if tpo_data:
                        # Top Metrics
                        m1, m2, m3 = st.columns(3)
                        m1.metric("Day Type", tpo_data['day_type'])
                        m2.metric("IB Range", f"{tpo_data['initial_balance']['low']:.2f} - {tpo_data['initial_balance']['high']:.2f}")
                        m3.metric("Profile Shape", tpo_data['shape']['shape'], help=tpo_data['shape']['description'])
                
                        # TPO Chart (Text-based approximation)
                        st.write("#### TPO Structure")
                        tpo_container = st.container(height=600)
                        with tpo_container:
                            # Create a dataframe for display
                            tpo_df = pd.DataFrame(tpo_data['profile'])
                            if not tpo_df.empty:
                                # Format for display: Price | Letters
                                tpo_df['Price'] = tpo_df['price'].apply(lambda x: f"{x:.2f}")
                                tpo_df['Structure'] = tpo_df['letter_string']
                                st.dataframe(
                                    tpo_df[['Price', 'Structure', 'tpo_count']], 
                                    use_container_width=True,
                                    height=550,
                                    hide_index=True
                                )
                    else:
                        st.warning("No TPO data available.")
                except Exception as e:
                    st.error(f"Error loading TPO: {e}")

            # 2. Composite Profiles
            with adv_tabs[1]:
                st.markdown("### Composite Profiles (Multi-Day Value)")
        
                col_comp_set, col_comp_viz = st.columns([1, 3])
        
                with col_comp_set:
                    comp_days = st.select_slider("Composite Period (Days)", options=[5, 10, 20, 30, 60], value=10)
                    comp_weight = st.selectbox("Weighting", ["equal", "linear", "exponential"], index=2)
            
                    if st.button("Build Composite"):
                        st.session_state['run_composite'] = True
                
                if st.session_state.get('run_composite', False):
                    try:
                        comp_builder = CompositeProfileBuilder(ticker)
                        comp = comp_builder.build_composite(days=comp_days, weighting=comp_weight)
                
                        if comp:
                            # Metrics
                            c1, c2, c3 = st.columns(3)
                            c1.metric("Composite POC", f"${comp['poc']:.2f}")
                            c2.metric("Composite VAH", f"${comp['vah']:.2f}")
                            c3.metric("Composite VAL", f"${comp['val']:.2f}")
                    
                            # Chart
                            comp_df = pd.DataFrame(comp['profile'])
                            fig_comp = px.bar(
                                comp_df, y='Price', x='Volume', orientation='h',
                                title=f"{comp_days}-Day Composite Profile ({comp_weight})",
                                height=600
                            )
                            # Add VA lines
                            fig_comp.add_hline(y=comp['poc'], line_dash="dash", line_color="red", annotation_text="POC")
                            fig_comp.add_hline(y=comp['vah'], line_dash="dash", line_color="green", annotation_text="VAH")
                            fig_comp.add_hline(y=comp['val'], line_dash="dash", line_color="green", annotation_text="VAL")
                            st.plotly_chart(fig_comp, use_container_width=True)
                    
                            # Confluence Check
                            st.markdown("#### Confluence Check")
                            conf = comp_builder.compare_composites([5, 10, 20])
                            if conf['confluence']:
                                for c in conf['confluence']:
                                    st.success(f"Confluence Zone at ${c['price']:.2f} (Matches: {c['timeframes']})")
                            else:
                                st.info("No strong confluence detected across timeframes.")
                    except Exception as e:
                        st.error(f"Composite Error: {e}")

            # 3. Volume Nodes
            with adv_tabs[2]:
                st.markdown("### Volume Nodes & Breakout Zones")
                try:
                    # Use data from main engine or fetch fresh
                    vn_engine = VolumeProfileEngine(ticker, period="1mo")
                    vn_engine.calculate_volume_profile()
            
                    detector = VolumeNodeDetector(vn_engine.volume_profile)
                    nodes = detector.find_all_nodes()
                    breakouts = detector.identify_breakout_zones()
            
                    c_hvn, c_lvn = st.columns(2)
            
                    with c_hvn:
                        st.markdown("#### High Volume Nodes (Support/Resistance)")
                        if nodes['hvn_clusters']:
                            for hvn in nodes['hvn_clusters'][:5]: # Top 5
                                st.success(f"**${hvn['price_center']:.2f}** (Vol: {int(hvn['total_volume'] / 1000)}k)")
                                st.progress(min(hvn['strength']/100, 1.0))
                        else:
                            st.info("No significant HVNs")
                    
                    with c_lvn:
                        st.markdown("#### Breakout Zones (LVN Gaps)")
                        if breakouts:
                            for bo in breakouts:
                                st.warning(f"**Breakout Zone**: ${bo['support']:.2f} - ${bo['resistance']:.2f}")
                                st.caption(f"Width: ${bo['width']:.2f}")
                        else:
                            st.info("No clear breakout zones")
                    
                except Exception as e:
                    st.error(f"Node Detection Error: {e}")

            # 4. Patterns & Stats
            with adv_tabs[3]:
                st.markdown("### Pattern Recognition & Deep Stats")
        
                try:
                    # Re-use engine data
                    stats_engine = VolumeProfileEngine(ticker, period="1mo")
                    stats_metrics = stats_engine.get_all_metrics()
            
                    # Patterns
                    pat_det = ProfilePatternDetector(stats_engine.volume_profile, stats_engine.data)
                    patterns = pat_det.detect_all_patterns()
            
                    st.markdown("#### Detected Patterns")
                    # Poor High/Low
                    p_cols = st.columns(2)
                    if patterns['poor_highs_lows']['poor_high']['detected']:
                        p_cols[0].error(f"Poor High at ${patterns['poor_highs_lows']['poor_high']['price']:.2f}")
                    else:
                        p_cols[0].success("Clean High")
                
                    if patterns['poor_highs_lows']['poor_low']['detected']:
                        p_cols[1].error(f"Poor Low at ${patterns['poor_highs_lows']['poor_low']['price']:.2f}")
                    else:
                        p_cols[1].success("Clean Low")
                
                    # Excess
                    if patterns['excess']:
                        for ex in patterns['excess']:
                            st.info(f"tail: {ex['type']} at ${ex['price']:.2f} ({ex['interpretation']})")
            
                    # VA Status
                    st.markdown("#### Value Area Status")
                    va_stat = patterns['value_area_status']
                    st.metric("Status", va_stat['status'], va_stat['interpretation'])
            
                    st.markdown("---")
            
                    # Statistics
                    st.markdown("#### Deep Statistics")
                    prof_stats = ProfileStatistics(
                        stats_engine.volume_profile, stats_engine.data, 
                        stats_metrics['poc'], stats_metrics['vah'], stats_metrics['val']
                    )
                    full_stats = prof_stats.calculate_all_statistics()
            
                    row1 = st.columns(3)
                    row1[0].metric("Profile Efficiency", f"{full_stats['profile_efficiency']['efficiency_pct']:.1f}%")
                    row1[1].metric("Review Bias", full_stats['volume_distribution']['bias'])
                    row1[2].metric("Volatility", full_stats['profile_width']['volatility'])
            
                    st.caption(f"Time in VA: {full_stats['time_in_va'].get('pct_inside_va', 0):.1f}%")
            
                except Exception as e:
                    st.error(f"Stats Error: {e}")


        with analytics_sub[1]:
            st.subheader("Multi-Timeframe Volume Profile")
            st.caption("Find confluent POC/VAH/VAL levels across timeframes. Aligned levels are strong S/R.")

            mtf_tfs = st.multiselect("Timeframes", ['15m', '1h', '4h', '1d', '1w'],
                                      default=['15m', '1h', '1d'], key='mtf_tfs')
            if st.button("Run Multi-TF Analysis", key='mtf_run'):
                with st.spinner("Analyzing across timeframes..."):
                    try:
                        mtf = MultiTimeframeAnalyzer(ticker, mtf_tfs)
                        mtf_result = mtf.analyze()

                        # Show each timeframe's levels
                        st.markdown("### Levels by Timeframe")
                        cols = st.columns(len(mtf_tfs))
                        for i, tf in enumerate(mtf_tfs):
                            with cols[i]:
                                data = mtf_result['timeframes'].get(tf, {})
                                label = data.get('label', tf)
                                st.markdown(f"**{label}**")
                                if 'error' not in data:
                                    st.metric("POC", f"${data['poc']:.2f}")
                                    st.metric("VAH", f"${data['vah']:.2f}")
                                    st.metric("VAL", f"${data['val']:.2f}")
                                else:
                                    st.warning(data['error'])

                        # Confluence levels
                        confluences = mtf_result['confluences']
                        if confluences:
                            st.markdown("---")
                            st.markdown("### Confluence Levels (Strongest S/R)")
                            for c in confluences:
                                strength_bar = "+" * c['strength']
                                st.markdown(f"**${c['price']:.2f}** [{strength_bar}] -- {c['description']}")

                        # Strongest levels table
                        strongest = mtf_result['strongest_levels']
                        if strongest:
                            st.markdown("---")
                            st.markdown("### Ranked Levels")
                            st.dataframe(pd.DataFrame(strongest), use_container_width=True)

                    except Exception as e:
                        st.error(f"MTF Error: {e}")

        with analytics_sub[2]:
            st.subheader("Correlation Heatmap")
            st.caption("Find correlated and inversely correlated assets. Useful for hedging and divergence trading.")

            corr_preset = st.selectbox("Preset", list(CorrelationAnalyzer.DEFAULT_PAIRS.keys()) + ['Custom'],
                                        key='corr_preset')
            if corr_preset == 'Custom':
                corr_tickers_str = st.text_input("Tickers (comma-separated)", "SPY,QQQ,GC=F,TLT", key='corr_custom')
                corr_tickers = [t.strip() for t in corr_tickers_str.split(',')]
            else:
                corr_tickers = CorrelationAnalyzer.DEFAULT_PAIRS[corr_preset]

            corr_period = st.selectbox("Period", ['1mo', '3mo', '6mo', '1y'], index=1, key='corr_period')

            if st.button("Compute Correlation", key='corr_run'):
                with st.spinner("Computing correlations..."):
                    try:
                        ca = CorrelationAnalyzer(corr_tickers, period=corr_period)
                        summary = ca.get_summary()
                        corr_matrix = summary['correlation_matrix']

                        # Heatmap
                        fig_corr = go.Figure(data=go.Heatmap(
                            z=corr_matrix.values,
                            x=corr_matrix.columns.tolist(),
                            y=corr_matrix.index.tolist(),
                            colorscale='RdBu_r',
                            zmid=0, zmin=-1, zmax=1,
                            text=corr_matrix.values.round(2),
                            texttemplate='%{text}',
                            textfont={"size": 14},
                        ))
                        fig_corr.update_layout(
                            height=500, template='plotly_dark',
                            title='Correlation Matrix (Daily Returns)'
                        )
                        st.plotly_chart(fig_corr, use_container_width=True)

                        # Summary
                        c1, c2 = st.columns(2)
                        with c1:
                            st.markdown("**Strongest Positive Correlations**")
                            for p in summary['strongest_positive'][:5]:
                                st.caption(f"{p['pair']}: {p['correlation']:.3f}")
                        with c2:
                            st.markdown("**Strongest Negative Correlations**")
                            for p in summary['strongest_negative'][:5]:
                                st.caption(f"{p['pair']}: {p['correlation']:.3f}")

                    except Exception as e:
                        st.error(f"Correlation Error: {e}")

        with analytics_sub[3]:
            st.subheader("Watchlist Dashboard")

            wl_names = wl_mgr.get_names()
            wl_choice = st.selectbox("Select Watchlist", wl_names, key='wl_dash_select') if wl_names else None

            if wl_choice and st.button("Load Watchlist", key='wl_load'):
                wl_tickers = wl_mgr.get_tickers(wl_choice)
                with st.spinner(f"Loading {len(wl_tickers)} tickers..."):
                    cols = st.columns(min(4, len(wl_tickers)))
                    for i, wt in enumerate(wl_tickers):
                        col = cols[i % 4]
                        with col:
                            try:
                                wt_data = yf.download(wt, period='5d', interval='1d',
                                                      progress=False, auto_adjust=True)
                                if wt_data is not None and not wt_data.empty:
                                    if isinstance(wt_data.columns, pd.MultiIndex):
                                        wt_data.columns = wt_data.columns.get_level_values(0)
                                    price = float(wt_data['Close'].iloc[-1])
                                    prev = float(wt_data['Close'].iloc[-2]) if len(wt_data) > 1 else price
                                    change_pct = (price - prev) / prev * 100

                                    st.metric(
                                        wt, f"${price:.2f}",
                                        delta=f"{change_pct:+.2f}%"
                                    )

                                    # Mini sparkline
                                    fig_mini = go.Figure(go.Scatter(
                                        y=wt_data['Close'].tolist(), mode='lines',
                                        line=dict(color='cyan' if change_pct >= 0 else 'red', width=1.5)
                                    ))
                                    fig_mini.update_layout(
                                        height=80, margin=dict(l=0, r=0, t=0, b=0),
                                        xaxis=dict(visible=False), yaxis=dict(visible=False),
                                        template='plotly_dark', plot_bgcolor='rgba(0,0,0,0)',
                                        paper_bgcolor='rgba(0,0,0,0)'
                                    )
                                    st.plotly_chart(fig_mini, use_container_width=True)
                                else:
                                    st.caption(f"{wt}: No data")
                            except Exception:
                                st.caption(f"{wt}: Error")

        # --- TAB: NEWS (News + Calendar) ---
# --- TAB: TOOLS (Scanner + Sessions + Risk) ---
with tab_tools:
    if not data_loaded:
        st.info("Run Analysis to view Tools data.")
    else:
        tools_sub = st.tabs(["Scanner", "Sessions", "Risk Calculator"])
        with tools_sub[0]:
            st.subheader("Multi-Asset Scanner")

            scan_col1, scan_col2 = st.columns([2, 1])
            with scan_col1:
                watchlist_name = st.selectbox(
                    "Watchlist",
                    list(WATCHLISTS.keys()),
                    format_func=lambda x: f"{x} ({len(WATCHLISTS[x])} tickers)"
                )
            with scan_col2:
                custom_tickers = st.text_input(
                    "Or enter custom tickers (comma-separated)",
                    placeholder="AAPL, MSFT, TSLA"
                )

            if st.button("Run Scanner"):
                tickers_to_scan = (
                    [t.strip().upper() for t in custom_tickers.split(',') if t.strip()]
                    if custom_tickers
                    else WATCHLISTS[watchlist_name]
                )

                with st.spinner(f"Scanning {len(tickers_to_scan)} tickers..."):
                    scanner = VolumeProfileScanner(tickers_to_scan)
                    results = scanner.scan_all()

                    if results:
                        st.success(f"Scanned {len(results)} tickers successfully!")

                        # Top metrics
                        top = results[0]
                        s1, s2, s3 = st.columns(3)
                        s1.metric("Best Opportunity", top['ticker'], f"Score: {top['opportunity_score']}/100")
                        s2.metric("Price", f"${top['current_price']:.2f}")
                        s3.metric("Position", top['position'])

                        # Results table
                        scan_df = scanner.to_dataframe()
                        display_cols = ['ticker', 'opportunity_score', 'current_price',
                                        'poc', 'vah', 'val', 'position', 'distance_from_poc_pct', 'signal']
                        display_cols = [c for c in display_cols if c in scan_df.columns]
                        st.dataframe(
                            scan_df[display_cols],
                            use_container_width=True,
                            hide_index=True,
                            column_config={
                                'opportunity_score': st.column_config.ProgressColumn(
                                    'Score', min_value=0, max_value=100, format='%d'
                                ),
                                'current_price': st.column_config.NumberColumn('Price', format='$%.2f'),
                                'poc': st.column_config.NumberColumn('POC', format='$%.2f'),
                                'vah': st.column_config.NumberColumn('VAH', format='$%.2f'),
                                'val': st.column_config.NumberColumn('VAL', format='$%.2f'),
                            }
                        )

                        # Export
                        csv = scan_df.to_csv(index=False)
                        st.download_button("Export CSV", csv, "scan_results.csv", "text/csv")

                    if scanner.errors:
                        with st.expander(f"{len(scanner.errors)} errors"):
                            for err in scanner.errors:
                                st.caption(f"{err['ticker']}: {err['error']}")

        with tools_sub[1]:
            st.subheader("Session Analysis (Asia / London / NY)")

            if st.button("Analyze Sessions"):
                with st.spinner(f"Analyzing sessions for {ticker}..."):
                    try:
                        sess_analyzer = SessionAnalyzer(ticker)
                        sessions = sess_analyzer.analyze_sessions()
                        comparison = sess_analyzer.get_session_comparison()

                        # Session cards
                        sc1, sc2, sc3 = st.columns(3)
                        session_cols = {'Asia': sc1, 'London': sc2, 'NY': sc3}
                        session_colors = {'Asia': 'ASIA', 'London': 'LDN', 'NY': 'US'}

                        for name, col in session_cols.items():
                            data = sessions.get(name, {})
                            with col:
                                st.markdown(f"### {session_colors[name]} {name}")
                                if data.get('status') == 'OK':
                                    st.metric("POC", f"${data['poc']:.2f}")
                                    st.metric("Volume", f"{data['volume']:,}")
                                    st.metric("Range", f"${data['range']:.2f}")
                                    st.caption(f"High: ${data['high']:.2f} | Low: ${data['low']:.2f}")
                                else:
                                    st.info("No data for this session")

                        # Comparison
                        st.markdown("---")
                        st.markdown("### Session Comparison")
                        cc1, cc2, cc3 = st.columns(3)
                        cc1.metric("Dominant Session", comparison.get('dominant_session', 'N/A'))
                        cc2.metric("POC Direction", comparison.get('poc_direction', 'N/A'),
                                   delta=f"{comparison.get('poc_shift_pct', 0):.3f}%")
                        cc3.metric("Overnight Gap", comparison.get('gap_type', 'N/A'),
                                   delta=f"${comparison.get('overnight_gap', 0):.2f}")

                        # Volume breakdown
                        vol_breakdown = comparison.get('volume_breakdown', {})
                        if vol_breakdown:
                            st.markdown("#### Volume Distribution")
                            vol_data = pd.DataFrame([
                                {'Session': k, 'Volume': v['volume'], 'Pct': v['pct']}
                                for k, v in vol_breakdown.items()
                            ])
                            fig_vol = px.pie(vol_data, values='Volume', names='Session',
                                             title='Volume by Session', hole=0.4)
                            st.plotly_chart(fig_vol, use_container_width=True)

                    except Exception as e:
                        st.error(f"Session Analysis Error: {e}")

        with tools_sub[2]:
            st.subheader("Risk Calculator")

            # Settings
            risk_col1, risk_col2 = st.columns(2)
            with risk_col1:
                acct_size = st.number_input("Account Size ($)", value=10000, min_value=100, step=1000)
                risk_pct = st.slider("Risk Per Trade (%)", 0.1, 5.0, 1.0, 0.1)
            with risk_col2:
                entry_price = st.number_input("Entry Price ($)", value=float(metrics.get('poc', 100)), min_value=0.01, step=0.5)
                stop_price = st.number_input("Stop Loss ($)", value=float(metrics.get('val', 98)), min_value=0.01, step=0.5)

            rm = RiskManager(acct_size, risk_pct)

            if st.button("Calculate Position"):
                pos = rm.calculate_position_size(entry_price, stop_price)

                if 'error' in pos:
                    st.error(pos['error'])
                else:
                    # Position size
                    st.markdown("### Position Size")
                    p1, p2, p3, p4 = st.columns(4)
                    p1.metric("Shares", pos['shares'])
                    p2.metric("Position Value", f"${pos['position_value']:,.2f}")
                    p3.metric("Risk ($)", f"${pos['total_risk_dollars']:,.2f}")
                    p4.metric("Risk (%)", f"{pos['total_risk_pct']}%")

                    # Multi-target plan
                    st.markdown("### Profit Targets")
                    va_range = metrics.get('vah', entry_price) - metrics.get('val', stop_price)
                    if va_range <= 0:
                        va_range = abs(entry_price - stop_price)

                    if pos['direction'] == 'LONG':
                        targets = [
                            round(entry_price + va_range, 2),
                            round(entry_price + 2 * va_range, 2),
                            round(entry_price + 3 * va_range, 2),
                        ]
                    else:
                        targets = [
                            round(entry_price - va_range, 2),
                            round(entry_price - 2 * va_range, 2),
                            round(entry_price - 3 * va_range, 2),
                        ]

                    plan = rm.multi_target_plan(entry_price, stop_price, targets)

                    if 'targets' in plan:
                        for t in plan['targets']:
                            tc1, tc2, tc3, tc4 = st.columns(4)
                            tc1.metric(f"Target {t['target_num']}", f"${t['price']:.2f}")
                            tc2.metric("R:R", t['rr_ratio'])
                            tc3.metric("Reward", f"${t['reward_dollars']:,.2f}")
                            tc4.metric("Quality", t['quality'])

                    # Account heat info
                    st.markdown("### Account Utilization")
                    util_pct = pos['account_utilization_pct']
                    if util_pct <= 100:
                        st.progress(util_pct / 100, text=f"Account usage: {util_pct:.1f}%")
                    else:
                        st.warning(f"Position requires margin: {util_pct:.1f}% of account")

        # --- TAB: RESEARCH (Backtester + AI + Options) ---
with tab_research:
    if not data_loaded:
        st.info("Run Analysis to view Research data.")
    else:
        research_sub = st.tabs(["Backtester", "AI Insights", "Options Flow"])
        with research_sub[0]:
            st.subheader("Strategy Backtester")
    
            col_strat, col_cap, col_btn = st.columns([2, 1, 1])
            strategy_name = col_strat.selectbox("Select Strategy", list(STRATEGIES.keys()))
            capital = col_cap.number_input("Initial Capital", value=10000)
    
            if col_btn.button("Run Simulation"):
                with st.spinner("Running backtest..."):
                    bt = VolumeProfileBacktester(ticker, initial_capital=capital)
                    strategy = STRATEGIES[strategy_name]
                    results = bt.run_strategy(strategy)
            
                    if "error" in results:
                        st.error(results['error'])
                    else:
                        # Metrics
                        m1, m2, m3, m4 = st.columns(4)
                        m1.metric("Win Rate", f"{results['win_rate']}%")
                        m2.metric("Total Return", f"{results['total_return']}%")
                        m3.metric("Final Capital", f"${results['final_capital']:,.2f}")
                        m4.metric("Total Trades", results['total_trades'])
                
                        # Equity Curve
                        st.line_chart(bt.equity_curve)
                
                        # Trades Table
                        if bt.trades:
                            st.dataframe(pd.DataFrame(bt.trades))

        with research_sub[1]:
            st.subheader("AI Agent Insights")

            if st.button("Generate Trading Plan"):
                with st.spinner("Agent is thinking..."):
                    plan_res = VolumeProfileAgent.get_trading_plan(ticker, period)

                    if plan_res['status'] == 'success':
                        p = plan_res['plan']
                        st.success(f"Strategy: {p['strategy']}")

                        c1, c2 = st.columns(2)
                        with c1:
                            st.write("**Setup:**")
                            st.write(f"- Bias: {p['bias']}")
                            st.write(f"- Entry Zone: ${p['entry_zone']['min']:.2f} - ${p['entry_zone']['max']:.2f}")

                        with c2:
                            st.write("**Risk Management:**")
                            sl = f"${p['stop_loss']:.2f}" if p['stop_loss'] is not None else "N/A"
                            t1 = f"${p['target_1']:.2f}" if p['target_1'] is not None else "N/A"
                            t2 = f"${p['target_2']:.2f}" if p['target_2'] is not None else "N/A"

                            st.write(f"- Stop Loss: {sl}")
                            st.write(f"- Target 1: {t1}")
                            st.write(f"- Target 2: {t2}")
                    else:
                        st.error(plan_res.get('error', 'Unknown error'))

        with research_sub[2]:
            st.subheader("Options Flow Analysis")

            if st.button("Load Options", key='opt_load'):
                with st.spinner("Loading options chain..."):
                    try:
                        ofa = OptionsFlowAnalyzer(ticker)
                        expirations = ofa.get_expirations()

                        if not expirations:
                            st.warning("No options data available for this ticker.")
                        else:
                            exp_choice = st.selectbox("Expiration", expirations, key='opt_exp')
                            opt_result = ofa.analyze(exp_choice)

                            if 'error' in opt_result:
                                st.error(opt_result['error'])
                            else:
                                oc1, oc2, oc3, oc4 = st.columns(4)
                                oc1.metric("Put/Call Ratio", f"{opt_result['pc_ratio']:.2f}")
                                oc2.metric("Max Pain", f"${opt_result['max_pain']:.2f}")
                                oc3.metric("Sentiment", opt_result['sentiment'])
                                oc4.metric("Current Price", f"${opt_result['current_price']:.2f}")

                                oc5, oc6, oc7, oc8 = st.columns(4)
                                oc5.metric("Call Volume", f"{opt_result['call_volume']:,}")
                                oc6.metric("Put Volume", f"{opt_result['put_volume']:,}")
                                oc7.metric("Call IV", f"{opt_result['call_iv']}%")
                                oc8.metric("Put IV", f"{opt_result['put_iv']}%")

                                st.markdown("---")
                                st.markdown("### Open Interest by Strike")
                                calls = opt_result['calls']
                                puts = opt_result['puts']

                                fig_oi = go.Figure()
                                if not calls.empty and 'openInterest' in calls.columns:
                                    fig_oi.add_trace(go.Bar(
                                        x=calls['strike'], y=calls['openInterest'],
                                        name='Call OI', marker_color='rgba(0,200,100,0.7)'
                                    ))
                                if not puts.empty and 'openInterest' in puts.columns:
                                    fig_oi.add_trace(go.Bar(
                                        x=puts['strike'], y=puts['openInterest'],
                                        name='Put OI', marker_color='rgba(255,80,80,0.7)'
                                    ))
                                fig_oi.add_vline(x=opt_result['max_pain'], line_dash="dash", line_color="yellow", annotation_text="Max Pain")
                                fig_oi.add_vline(x=opt_result['current_price'], line_dash="solid", line_color="white", annotation_text="Price")
                                fig_oi.update_layout(height=400, template='plotly_dark', barmode='group', title='Open Interest Distribution')
                                st.plotly_chart(fig_oi, use_container_width=True)

                                unusual = opt_result['unusual_activity']
                                if not unusual.empty:
                                    st.markdown("---")
                                    st.markdown("### Unusual Options Activity")
                                    st.caption("Options with volume significantly above average.")
                                    st.dataframe(unusual, use_container_width=True)
                                else:
                                    st.info("No unusual options activity detected.")

                    except Exception as e:
                        st.error(f"Options Error: {e}")

with tab_news:
    news_sub = st.tabs(["News Feed", "Economic Calendar"])
    with news_sub[0]:
        st.subheader("News & Sentiment")
        st.caption("Live news from Google News (Reuters, Bloomberg, CNBC, etc.) with sentiment scoring.")

        if st.button("Load News", key='news_load'):
            with st.spinner("Fetching news..."):
                try:
                    nf = NewsFeedAnalyzer(ticker)
                    result = nf.get_sentiment_summary()

                    # Summary metrics
                    nc1, nc2, nc3, nc4, nc5 = st.columns(5)
                    nc1.metric("Overall Sentiment", result['overall_sentiment'])
                    nc2.metric("Score", f"{result['avg_score']:+.2f}")
                    nc3.metric("Positive", result['positive_count'])
                    nc4.metric("Negative", result['negative_count'])
                    nc5.metric("Neutral", result['neutral_count'])

                    # Articles
                    st.markdown("---")
                    for article in result['articles']:
                        sent = article['sentiment']
                        sent_emoji = "🟢" if sent == 'Positive' else "🔴" if sent == 'Negative' else "⚪"
                        st.markdown(
                            f"{sent_emoji} **{article['title']}**  \n"
                            f"*{article['publisher']}* · {article['age']}  "
                            f"[Read →]({article['link']})"
                        )
                        st.markdown("---")

                    if not result['articles']:
                        st.info("No news articles found. Try a different ticker.")

                except Exception as e:
                    st.error(f"News Error: {e}")


    with news_sub[1]:
        st.subheader("Economic Calendar")
        st.caption("Upcoming high-impact economic events that affect markets.")

        import streamlit.components.v1 as components_cal
        cal_html = """
        <div style="height:600px;overflow:auto;">
        <!-- TradingView Widget BEGIN -->
        <div class="tradingview-widget-container">
          <div class="tradingview-widget-container__widget"></div>
          <script type="text/javascript"
            src="https://s3.tradingview.com/external-embedding/embed-widget-events.js" async>
            {
              "colorTheme": "dark",
              "isTransparent": true,
              "width": "100%",
              "height": "580",
              "locale": "en",
              "importanceFilter": "0,1",
              "countryFilter": "us,eu,gb,jp,cn"
            }
          </script>
        </div>
        <!-- TradingView Widget END -->
        </div>
        """
        components_cal.html(cal_html, height=620)

