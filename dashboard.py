import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
import pandas as pd
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

st.set_page_config(layout="wide", page_title="Volume Profile Dashboard")

# --- Sidebar Controls ---
st.sidebar.title("Configuration")
ticker = st.sidebar.text_input("Ticker", value="SPY").upper()
period = st.sidebar.selectbox("Period", ["1d", "5d", "1mo", "3mo", "6mo", "1y"], index=2)
interval = st.sidebar.selectbox("Interval", ["1m", "5m", "15m", "1h", "1d"], index=2)

# Global Engine Instance
@st.cache_data(ttl=60) # Cache data for 1 minute
def load_data(ticker, period, interval):
    engine = VolumeProfileEngine(ticker, period, interval)
    engine.fetch_data()
    engine.calculate_volume_profile()
    return engine

if st.sidebar.button("Run Analysis"):
    st.session_state['run'] = True

if 'run' not in st.session_state:
    st.info("Enter a ticker and click 'Run Analysis' to start.")
    st.stop()

# --- tabs ---
# Define tabs early to prevent resetting on interaction
tab1, tab2, tab5, tab6, tab7, tab8, tab3, tab4 = st.tabs([
    "Market Analysis", "Order Flow (T&S)", "Advanced Analytics",
    "📡 Scanner", "🕐 Sessions", "⚖️ Risk Calculator",
    "Backtester", "AI Insights"
])

try:
    with st.spinner(f"Analyzing {ticker}..."):
        engine = load_data(ticker, period, interval)
        metrics = engine.get_all_metrics()
        df = engine.data
        profile = engine.volume_profile
        
        # Phase 5: Advanced Analytics
        daily_profiles = engine.get_daily_profiles(days=5)
        # Phase 6: Use new classes
        if len(daily_profiles) >= 2:
            comp = ProfileComparator(ticker).compare_yesterday_today()
        else:
            comp = {}
            
        tracker = ValueAreaMigrationTracker(ticker, lookback_days=10).track_migration()
        
        # Volume Anomalies
        vol_mean = df['Volume'].mean()
        vol_std = df['Volume'].std()
        
except Exception as e:
    st.error(f"Error: {e}")
    st.stop()

# --- tabs ---
# Tabs defined above

# --- TAB 1: MARKET ANALYSIS ---
with tab1:
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


# --- TAB 2: ORDER FLOW (T&S) ---
with tab2:
    st.subheader("Time & Sales Analysis (Volume Proxy)")
    
    ts_btn = st.button("Analyze Order Flow")
    
    if ts_btn:
        with st.spinner("Analyzing Tick Data..."):
            # Use 1m data for granular analysis
            # We need POC/VAH/VAL for this
            ts_res = VolumeProfileAgent.get_time_and_sales(ticker, metrics['poc'], metrics['vah'], metrics['val'])
            
            if ts_res['status'] == 'success':
                data = ts_res['data']
                lp = data.get('large_prints', [])
                levels = data.get('key_levels', {})
                
                # Top Section: Activity at Key Levels
                st.markdown("### Activity at Key Levels")
                c1, c2, c3 = st.columns(3)
                
                # Mapping friendly names to keys
                level_map = {'POC': 'poc', 'VAH': 'vah', 'VAL': 'val'}
                
                for i, (label, key) in enumerate(level_map.items()):
                    lvl_data = levels.get(key, {})
                    col = [c1, c2, c3][i]
                    
                    with col:
                        status = lvl_data.get('status', 'NO_DATA')
                        price = lvl_data.get('level', 0)
                        
                        st.markdown(f"**{label}** (${price:.2f})")
                        
                        if status == 'ACTIVE':
                            bias = lvl_data.get('bias', 'NEUTRAL')
                            b_color = "green" if bias == "BULLISH" else "red" if bias == "BEARISH" else "gray"
                            st.markdown(f"Bias: :{b_color}[{bias}]")
                            st.caption(lvl_data.get('interpretation', ''))
                            
                            # Vol Bars
                            buy_r = lvl_data.get('buy_ratio', 0)
                            sell_r = lvl_data.get('sell_ratio', 0)
                            st.progress(buy_r, text=f"Buy {int(buy_r*100)}% vs Sell {int(sell_r*100)}%")
                        else:
                            st.caption("No significant activity detected")
                
                # Bottom Section: Large Prints
                st.markdown("### Large Prints (Aggressive Tape)")
                if lp:
                    lp_df = pd.DataFrame(lp)
                    # Color table based on Aggressive Side
                    # Columns: time, price, size, aggressive, interpretation
                    st.dataframe(
                        lp_df[['time', 'price', 'size', 'aggressive', 'interpretation']],
                        use_container_width=True,
                        column_config={
                            "price": st.column_config.NumberColumn(format="$%.2f"),
                            "size": st.column_config.NumberColumn(format="%d"),
                        }
                    )
                else:
                    st.info("No aggressive large prints detected on tape.")
            else:
                st.error(ts_res.get('error'))

# --- TAB 5: ADVANCED ANALYTICS (Phase 8) ---
with tab5:
    st.subheader("Advanced Volume & Market Profile Analytics")
    
    # Create tabs for sub-features
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
                            st.success(f"🎯 Confluence Zone at ${c['price']:.2f} (Matches: {c['timeframes']})")
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
                        st.warning(f"⚡ **Breakout Zone**: ${bo['support']:.2f} - ${bo['resistance']:.2f}")
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
            
            st.markdown("#### 🔍 Detected Patterns")
            # Poor High/Low
            p_cols = st.columns(2)
            if patterns['poor_highs_lows']['poor_high']['detected']:
                p_cols[0].error(f"⚠️ Poor High at ${patterns['poor_highs_lows']['poor_high']['price']:.2f}")
            else:
                p_cols[0].success("✅ Clean High")
                
            if patterns['poor_highs_lows']['poor_low']['detected']:
                p_cols[1].error(f"⚠️ Poor Low at ${patterns['poor_highs_lows']['poor_low']['price']:.2f}")
            else:
                p_cols[1].success("✅ Clean Low")
                
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
            st.markdown("#### 📊 Deep Statistics")
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

# --- TAB 6: MULTI-ASSET SCANNER ---
with tab6:
    st.subheader("📡 Multi-Asset Scanner")

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

    if st.button("🔍 Run Scanner"):
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
                st.download_button("📥 Export CSV", csv, "scan_results.csv", "text/csv")

            if scanner.errors:
                with st.expander(f"⚠️ {len(scanner.errors)} errors"):
                    for err in scanner.errors:
                        st.caption(f"{err['ticker']}: {err['error']}")

# --- TAB 7: SESSION ANALYSIS ---
with tab7:
    st.subheader("🕐 Session Analysis (Asia / London / NY)")

    if st.button("Analyze Sessions"):
        with st.spinner(f"Analyzing sessions for {ticker}..."):
            try:
                sess_analyzer = SessionAnalyzer(ticker)
                sessions = sess_analyzer.analyze_sessions()
                comparison = sess_analyzer.get_session_comparison()

                # Session cards
                sc1, sc2, sc3 = st.columns(3)
                session_cols = {'Asia': sc1, 'London': sc2, 'NY': sc3}
                session_colors = {'Asia': '🌏', 'London': '🇬🇧', 'NY': '🇺🇸'}

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

# --- TAB 8: RISK CALCULATOR ---
with tab8:
    st.subheader("⚖️ Risk Calculator")

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
                st.warning(f"⚠️ Position requires margin: {util_pct:.1f}% of account")

# --- TAB 3: BACKTESTER ---
with tab3:
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

# --- TAB 4: AI AGENT ---
with tab4:
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
